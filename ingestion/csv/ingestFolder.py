import datetime
import re
import shutil
import uuid
from pathlib import Path
import pandas as pd
from sqlalchemy import Date, create_engine, text

# --- Configuration & Paths ---
INPUT_DIR = Path("/Users/jonathankee/Data-Science-Projects/ingestion/sources_unprocessed")
PROCESSED_DIR = Path("/Users/jonathankee/Data-Science-Projects/ingestion/sources_processed")

DB_URL = "postgresql://postgres:abc123@localhost:5432/prosperous_universe"
SCHEMA = "raw"

# Primary key mapping defining the behavior of each table:
# This dictionary dictates how the UPSERT (Insert or Update) logic will behave. 
# If a row with these keys already exists, it gets updated. Otherwise, it's inserted.
PRIMARY_KEY_MAP = {
    # HISTORICAL TIMESERIES: Uses filename date component (file_date) + entity keys
    # Subsequent runs on a new day insert new rows, preserving historical data over time.
    "prices": ["ticker", "file_date"],
    
    # LATEST STATE: Overwrites existing records per snapshot based on unique entity IDs
    "inventory": ["ticker", "storage_type"],
    "workforce": ["planet_natural_id", "material_ticker"]
}

def clean_snake_case(name: str) -> str:
    """Converts string headers to clean snake_case."""
    # Step 1: Insert an underscore between lowercase/number and uppercase letters 
    # (e.g., 'MaterialTicker' becomes 'Material_Ticker')
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name.strip())
    # Step 2: Replace any non-alphanumeric characters with underscores, 
    # convert to lowercase, and strip trailing/leading underscores
    return re.sub(r"[^\w]+", "_", s).lower().strip("_")

def load_to_postgres(df: pd.DataFrame, target_table: str, pks: list, engine):
    """Loads a DataFrame into Postgres idempotently with schema evolution and deduplication."""
    with engine.begin() as conn:
        # Ensure the target schema (folder for tables) exists
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA};"))

        # ==========================================
        # 1. SCHEMA EVOLUTION (Dynamic Column Addition)
        # ==========================================
        # Check if the target table already exists in the database
        table_exists = conn.execute(text(f"""
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = :schema AND table_name = :table_name;
        """), {"schema": SCHEMA, "table_name": target_table}).scalar()

        if table_exists:
            # If the table exists, get a list of its current columns
            cols_result = conn.execute(text(f"""
                SELECT column_name FROM information_schema.columns 
                WHERE table_schema = :schema AND table_name = :table_name;
            """), {"schema": SCHEMA, "table_name": target_table})
            
            existing_cols = [row[0] for row in cols_result]

            # Map pandas data types to PostgreSQL data types
            type_map = {
                "object": "TEXT",
                "int64": "BIGINT",
                "int32": "INTEGER",
                "float64": "DOUBLE PRECISION",
                "float32": "REAL",
                "bool": "BOOLEAN",
            }

            # Loop through the incoming dataframe columns. 
            # If the database is missing a column that exists in the CSV, alter the table to add it.
            for col in df.columns:
                if col not in existing_cols:
                    dtype_str = str(df[col].dtype)
                    
                    # Handle specific date/time types accurately
                    if "datetime" in dtype_str:
                        sql_type = "TIMESTAMPTZ" if ("UTC" in dtype_str or (hasattr(df[col], 'dt') and df[col].dt.tz is not None)) else "TIMESTAMP"
                    elif col == "file_date":
                        sql_type = "DATE"
                    else:
                        # Fallback to mapped type, default to TEXT if unknown
                        sql_type = type_map.get(dtype_str, "TEXT")
                    
                    # Dynamically execute the ALTER TABLE statement
                    conn.execute(text(f'ALTER TABLE "{SCHEMA}"."{target_table}" ADD COLUMN "{col}" {sql_type};'))

        # ==========================================
        # 2. STAGING (Temporary Data Dump)
        # ==========================================
        # Use a unique staging table name per run to prevent collision/leftover issues if jobs run concurrently
        stg_table = f"_stg_{target_table}_{uuid.uuid4().hex[:8]}"
        
        # Write current batch to a temporary staging table using pandas native to_sql
        # We explicitly cast 'file_date' to a Date object so Postgres recognizes it properly
        df.to_sql(
            stg_table, 
            conn, 
            schema=SCHEMA, 
            if_exists="replace", 
            index=False,
            dtype={"file_date": Date()}
        )

        # ==========================================
        # 3. TARGET TABLE CREATION (If new)
        # ==========================================
        # If the target table didn't exist in Step 1, create it now by cloning the staging table's structure
        conn.execute(
            text(f'CREATE TABLE IF NOT EXISTS "{SCHEMA}"."{target_table}" (LIKE "{SCHEMA}"."{stg_table}");')
        )

        # ==========================================
        # 4. UPSERT & PRIMARY KEY MANAGEMENT
        # ==========================================
        if len(pks) > 0:
            # Check the database to see what Primary Keys currently exist on the target table
            current_pk_result = conn.execute(text("""
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                WHERE tc.table_schema = :schema 
                  AND tc.table_name = :target_table 
                  AND tc.constraint_type = 'PRIMARY KEY';
            """), {"schema": SCHEMA, "target_table": target_table})
            
            current_pks = [row[0] for row in current_pk_result]
            
            # If the database PKs don't match our PRIMARY_KEY_MAP, we need to update them
            if current_pks != pks:
                # If there are existing PKs, find the constraint name and drop it
                if len(current_pks) > 0:
                    constraint_name_result = conn.execute(text("""
                        SELECT tc.constraint_name
                        FROM information_schema.table_constraints tc
                        WHERE tc.table_schema = :schema 
                          AND tc.table_name = :target_table 
                          AND tc.constraint_type = 'PRIMARY KEY';
                    """), {"schema": SCHEMA, "target_table": target_table}).scalar()
                    
                    if constraint_name_result:
                        conn.execute(text(f'ALTER TABLE "{SCHEMA}"."{target_table}" DROP CONSTRAINT "{constraint_name_result}";'))
                
                # Apply the new Primary Keys from our map
                pk_quoted = [f'"{pk}"' for pk in pks]
                pk_str_def = ", ".join(pk_quoted)
                conn.execute(text(f'ALTER TABLE "{SCHEMA}"."{target_table}" ADD PRIMARY KEY ({pk_str_def});'))

            # Format columns for SQL queries (wrapping in double quotes to handle case-sensitivity)
            columns_quoted = [f'"{col}"' for col in df.columns]
            col_str = ", ".join(columns_quoted)
            
            # Build the "DO UPDATE SET" clause for our Upsert
            # This ensures that if a row already exists, non-key columns get overwritten with the new data
            update_clauses = []
            for col in df.columns:
                if col not in pks:
                    # e.g., "price" = EXCLUDED."price" (EXCLUDED is Postgres syntax for the incoming staging row)
                    update_clauses.append(f'"{col}" = EXCLUDED."{col}"')
            
            pk_quoted = [f'"{pk}"' for pk in pks]
            pk_str = ", ".join(pk_quoted)

            # If there are columns to update, execute an UPSERT, otherwise just DO NOTHING on conflict
            if len(update_clauses) > 0:
                set_clause = ", ".join(update_clauses)
                conflict_action = f"DO UPDATE SET {set_clause}"
            else:
                conflict_action = "DO NOTHING"

            # Execute the final MERGE/UPSERT statement moving data from Staging -> Target
            merge_sql = f"""
                INSERT INTO "{SCHEMA}"."{target_table}" ({col_str})
                SELECT {col_str} FROM "{SCHEMA}"."{stg_table}"
                ON CONFLICT ({pk_str})
                {conflict_action};
            """
            conn.execute(text(merge_sql))
            
        else:
            # If no Primary Keys are defined, do a standard, blind INSERT (Append-only mode)
            columns_quoted = [f'"{col}"' for col in df.columns]
            col_str = ", ".join(columns_quoted)
            
            insert_sql = f"""
                INSERT INTO "{SCHEMA}"."{target_table}" ({col_str})
                SELECT {col_str} FROM "{SCHEMA}"."{stg_table}";
            """
            conn.execute(text(insert_sql))

        # ==========================================
        # 5. CLEANUP
        # ==========================================
        # Drop the temporary staging table so it doesn't bloat the database
        conn.execute(text(f'DROP TABLE IF EXISTS "{SCHEMA}"."{stg_table}";'))

def process_file(file_path: Path, engine):
    """Reads, normalizes, and loads a single CSV file."""
    
    # --- File Parsing ---
    # Extract the base name without extensions or URL parameters
    raw_stem = file_path.stem.split("?")[0]
    # Split from the right on the underscore to separate prefix (table name) and suffix (date)
    # e.g., "prices_17082026" -> ["prices", "17082026"]
    parts = raw_stem.rsplit("_", 1)
    # Clean the prefix to serve as the base table name
    prefix = re.sub(r"[^\w]+", "", parts[0]).lower()
    
    # Extract 8-digit date from filename (e.g., 17082026 -> DDMMYYYY)
    file_date_str = None
    if len(parts) > 1 and re.match(r"^\d{8}$", parts[1]):
        date_str = parts[1]
        day = date_str[0:2]
        month = date_str[2:4]
        year = date_str[4:8]
        try:
            file_date_str = f"{year}-{month}-{day}"
        except ValueError:
            pass
            
    # Fallback to current date if filename doesn't contain a valid date pattern
    if not file_date_str:
        file_date_str = pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%d")

    target_table = f"{prefix}_raw"

    # --- Data Transformations ---
    df = pd.read_csv(file_path)

    # Standardize column headers using the regex helper
    clean_cols = [clean_snake_case(c) for c in df.columns]
    df.columns = clean_cols

    # Prepare audit timestamps
    current_time = pd.Timestamp.now(tz="UTC")
    file_date_val = pd.to_datetime(file_date_str).date()

    # Inject metadata columns at the front of the dataframe
    # This helps track data lineage (where it came from, what day it represents, when it was loaded)
    df.insert(0, "source_file", file_path.name)
    df.insert(0, "file_date", file_date_val)
    df.insert(0, "load_time", current_time)

    # --- Data Cleaning & Deduplication ---
    pks = PRIMARY_KEY_MAP.get(prefix, [])
    if len(pks) > 0:
        # Check if all expected primary keys actually exist in the CSV headers
        all_pks_present = all(k in df.columns for k in pks)
                
        if all_pks_present:
            for k in pks:
                if df[k].dtype == "object":
                    # For string-based primary keys, remove whitespace. 
                    # If the key is entirely blank spaces, convert it to a true NULL (pd.NA)
                    df[k] = df[k].astype(str).str.strip().replace(r"^\s*$", pd.NA, regex=True)
            
            # 1. Drop rows where Primary Keys are missing (Cannot upsert without them)
            df = df.dropna(subset=pks)
            # 2. In-batch deduplication: if the CSV has duplicate rows for the same PK, keep the last one.
            # This prevents the Postgres UPSERT from throwing a cardinal violation.
            df = df.drop_duplicates(subset=pks, keep="last")

    # Pass the clean dataframe to the loading function
    load_to_postgres(df, target_table, pks, engine)

def main():
    # Gather all CSVs in the input directory
    csv_files = list(INPUT_DIR.glob("*.csv"))
        
    if len(csv_files) == 0:
        print("No CSV files found.")
        return

    # Initialize DB connection and ensure output directory exists
    engine = create_engine(DB_URL)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    processed_count = 0
    # Process files sequentially
    for file_path in csv_files:
        try:
            process_file(file_path, engine)
            # If successful, move the file to the 'processed' folder to avoid double-processing later
            shutil.move(str(file_path), str(PROCESSED_DIR / file_path.name))
            processed_count += 1
            print(f"Loaded and moved: {file_path.name}")
        except Exception as e:
            # Catch and log individual file failures so one bad file doesn't crash the whole batch
            print(f"Failed to process {file_path.name}: {e}")

    print(f"Successfully processed and moved {processed_count} file(s).")

if __name__ == "__main__":
    main()
import datetime
import re
import shutil
import uuid
from pathlib import Path
import pandas as pd
from sqlalchemy import Date, create_engine, text

INPUT_DIR = Path("/Users/jonathankee/Data-Science-Projects/ingestion/sources_unprocessed")
PROCESSED_DIR = Path("/Users/jonathankee/Data-Science-Projects/ingestion/sources_processed")

DB_URL = "postgresql://postgres:abc123@localhost:5432/prosperous_universe"
SCHEMA = "raw"

# Primary key mapping defining the behavior of each table:
PRIMARY_KEY_MAP = {
    # HISTORICAL TIMESERIES: Uses filename date component (file_date) + entity keys
    # Subsequent runs on a new day insert new rows, preserving historical data over time.
    "prices": ["ticker", "file_date"],
    
    # LATEST STATE: Overwrites existing records per snapshot
    "inventory": ["ticker", "storage_type"],

    # LATEST STATE: Overwrites existing records per snapshot
    "workforce": ["planet_natural_id", "material_ticker"]
}

def clean_snake_case(name: str) -> str:
    """Converts string headers to clean snake_case."""
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name.strip())
    return re.sub(r"[^\w]+", "_", s).lower().strip("_")

def load_to_postgres(df: pd.DataFrame, target_table: str, pks: list, engine):
    """Loads a DataFrame into Postgres idempotently with schema evolution and deduplication."""
    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA};"))

        # 1. Check if target table exists and dynamically add any missing columns (schema evolution)
        table_exists = conn.execute(text(f"""
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = :schema AND table_name = :table_name;
        """), {"schema": SCHEMA, "table_name": target_table}).scalar()

        if table_exists:
            cols_result = conn.execute(text(f"""
                SELECT column_name FROM information_schema.columns 
                WHERE table_schema = :schema AND table_name = :table_name;
            """), {"schema": SCHEMA, "table_name": target_table})
            
            existing_cols = []
            for row in cols_result:
                existing_cols.append(row[0])

            type_map = {
                "object": "TEXT",
                "int64": "BIGINT",
                "int32": "INTEGER",
                "float64": "DOUBLE PRECISION",
                "float32": "REAL",
                "bool": "BOOLEAN",
            }

            for col in df.columns:
                if col not in existing_cols:
                    dtype_str = str(df[col].dtype)
                    if "datetime" in dtype_str:
                        sql_type = "TIMESTAMPTZ" if ("UTC" in dtype_str or (hasattr(df[col], 'dt') and df[col].dt.tz is not None)) else "TIMESTAMP"
                    elif col == "file_date":
                        sql_type = "DATE"
                    else:
                        sql_type = type_map.get(dtype_str, "TEXT")
                    
                    conn.execute(text(f'ALTER TABLE "{SCHEMA}"."{target_table}" ADD COLUMN "{col}" {sql_type};'))

        # Use a unique staging table name per run to prevent collision/leftover issues
        stg_table = f"_stg_{target_table}_{uuid.uuid4().hex[:8]}"
        
        # 2. Write current batch to temporary staging table with explicit Date type mapping
        df.to_sql(
            stg_table, 
            conn, 
            schema=SCHEMA, 
            if_exists="replace", 
            index=False,
            dtype={"file_date": Date()}
        )

        # 3. Ensure target table exists (clones structure from staging if missing)
        conn.execute(
            text(f'CREATE TABLE IF NOT EXISTS "{SCHEMA}"."{target_table}" (LIKE "{SCHEMA}"."{stg_table}");')
        )

        # 4. Upsert Data & Sync Primary Key Constraints Dynamically
        if len(pks) > 0:
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
            
            current_pks = []
            for row in current_pk_result:
                current_pks.append(row[0])
            
            if current_pks != pks:
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
                
                pk_quoted = []
                for pk in pks:
                    pk_quoted.append(f'"{pk}"')
                pk_str_def = ", ".join(pk_quoted)
                conn.execute(text(f'ALTER TABLE "{SCHEMA}"."{target_table}" ADD PRIMARY KEY ({pk_str_def});'))

            # Gather columns
            columns_quoted = []
            for col in df.columns:
                columns_quoted.append(f'"{col}"')
            col_str = ", ".join(columns_quoted)
            
            # FIX: Updated to include 'load_time' and 'file_date' during UPSERTs so snapshots refresh timestamps
            update_clauses = []
            for col in df.columns:
                if col not in pks:
                    update_clauses.append(f'"{col}" = EXCLUDED."{col}"')
            
            pk_quoted = []
            for pk in pks:
                pk_quoted.append(f'"{pk}"')
            pk_str = ", ".join(pk_quoted)

            if len(update_clauses) > 0:
                set_clause = ", ".join(update_clauses)
                conflict_action = f"DO UPDATE SET {set_clause}"
            else:
                conflict_action = "DO NOTHING"

            merge_sql = f"""
                INSERT INTO "{SCHEMA}"."{target_table}" ({col_str})
                SELECT {col_str} FROM "{SCHEMA}"."{stg_table}"
                ON CONFLICT ({pk_str})
                {conflict_action};
            """
            conn.execute(text(merge_sql))
            
        else:
            columns_quoted = []
            for col in df.columns:
                columns_quoted.append(f'"{col}"')
            col_str = ", ".join(columns_quoted)
            
            insert_sql = f"""
                INSERT INTO "{SCHEMA}"."{target_table}" ({col_str})
                SELECT {col_str} FROM "{SCHEMA}"."{stg_table}";
            """
            conn.execute(text(insert_sql))

        # 5. Clean up staging table
        conn.execute(text(f'DROP TABLE IF EXISTS "{SCHEMA}"."{stg_table}";'))

def process_file(file_path: Path, engine):
    """Reads, normalizes, and loads a single CSV file."""
    raw_stem = file_path.stem.split("?")[0]
    parts = raw_stem.rsplit("_", 1)
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

    df = pd.read_csv(file_path)
    
    clean_cols = []
    for c in df.columns:
        clean_cols.append(clean_snake_case(c))
    df.columns = clean_cols

    current_time = pd.Timestamp.now(tz="UTC")
    file_date_val = pd.to_datetime(file_date_str).date()

    # Add metadata columns using the extracted filename date
    df.insert(0, "source_file", file_path.name)
    df.insert(0, "file_date", file_date_val)
    df.insert(0, "load_time", current_time)

    # Primary key matching, NULL cleaning, and batch deduplication
    pks = PRIMARY_KEY_MAP.get(prefix, [])
    if len(pks) > 0:
        all_pks_present = True
        for k in pks:
            if k not in df.columns:
                all_pks_present = False
                break
                
        if all_pks_present:
            for k in pks:
                if df[k].dtype == "object":
                    df[k] = df[k].astype(str).str.strip().replace(r"^\s*$", pd.NA, regex=True)
            df = df.dropna(subset=pks)
            df = df.drop_duplicates(subset=pks, keep="last")

    load_to_postgres(df, target_table, pks, engine)

def main():
    csv_files = []
    for f in INPUT_DIR.glob("*.csv"):
        csv_files.append(f)
        
    if len(csv_files) == 0:
        print("No CSV files found.")
        return

    engine = create_engine(DB_URL)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    processed_count = 0
    for file_path in csv_files:
        try:
            process_file(file_path, engine)
            shutil.move(str(file_path), str(PROCESSED_DIR / file_path.name))
            processed_count += 1
            print(f"Loaded and moved: {file_path.name}")
        except Exception as e:
            print(f"Failed to process {file_path.name}: {e}")

    print(f"Successfully processed and moved {processed_count} file(s).")

if __name__ == "__main__":
    main()
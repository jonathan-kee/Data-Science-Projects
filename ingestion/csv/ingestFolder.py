import datetime
import re
import shutil
import uuid
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text

INPUT_DIR = Path("/Users/jonathankee/Data-Science-Projects/ingestion/sources_unprocessed")
PROCESSED_DIR = Path("/Users/jonathankee/Data-Science-Projects/ingestion/sources_processed")

DB_URL = "postgresql://postgres:abc123@localhost:5432/prosperous_universe"
SCHEMA = "raw"

PRIMARY_KEY_MAP = {
    "prices": ["ticker"],
    "inventory": ["ticker", "storage_type"],
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
            existing_cols = {row[0] for row in cols_result}

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
                    else:
                        sql_type = type_map.get(dtype_str, "TEXT")
                    
                    conn.execute(text(f'ALTER TABLE "{SCHEMA}"."{target_table}" ADD COLUMN "{col}" {sql_type};'))

        # Use a unique staging table name per run to prevent collision/leftover issues
        stg_table = f"_stg_{target_table}_{uuid.uuid4().hex[:8]}"
        
        # 2. Write current batch to temporary staging table
        df.to_sql(stg_table, conn, schema=SCHEMA, if_exists="replace", index=False)

        # 3. Ensure target table exists (clones structure from staging if missing)
        conn.execute(
            text(f'CREATE TABLE IF NOT EXISTS "{SCHEMA}"."{target_table}" (LIKE "{SCHEMA}"."{stg_table}");')
        )

        # 4. Enforce Idempotency (Delete existing matching records before insert)
        if pks:
            # Delete records matching business primary keys
            pk_match = " AND ".join(
                [f'"{SCHEMA}"."{target_table}"."{pk}" = "{SCHEMA}"."{stg_table}"."{pk}"' for pk in pks]
            )
            delete_sql = f"""
                DELETE FROM "{SCHEMA}"."{target_table}"
                WHERE EXISTS (
                    SELECT 1 FROM "{SCHEMA}"."{stg_table}"
                    WHERE {pk_match}
                );
            """
            conn.execute(text(delete_sql))
        else:
            # For tables without primary keys, clear out old records from the same source file 
            # to make re-runs fully idempotent and repeatable without duplicating rows.
            source_file_val = df["source_file"].iloc[0] if not df.empty and "source_file" in df.columns else None
            if source_file_val:
                conn.execute(
                    text(f'DELETE FROM "{SCHEMA}"."{target_table}" WHERE "source_file" = :source_file;'),
                    {"source_file": source_file_val}
                )

        # 5. Insert new records from staging into target
        cols = ", ".join([f'"{col}"' for col in df.columns])
        insert_sql = f"""
            INSERT INTO "{SCHEMA}"."{target_table}" ({cols})
            SELECT {cols} FROM "{SCHEMA}"."{stg_table}";
        """
        conn.execute(text(insert_sql))

        # 6. Clean up staging table
        conn.execute(text(f'DROP TABLE IF EXISTS "{SCHEMA}"."{stg_table}";'))

def process_file(file_path: Path, engine):
    """Reads, normalizes, and loads a single CSV file."""
    raw_stem = file_path.stem.split("?")[0]
    prefix = re.sub(r"[^\w]+", "", raw_stem.rsplit("_", 1)[0] if "_" in raw_stem else raw_stem).lower()
    target_table = f"{prefix}_raw"

    df = pd.read_csv(file_path)
    df.columns = [clean_snake_case(c) for c in df.columns]

    # Add metadata columns
    df.insert(0, "source_file", file_path.name)
    df.insert(0, "load_time", pd.Timestamp.now(tz="UTC"))

    # Primary key matching, NULL cleaning, and batch deduplication
    pks = PRIMARY_KEY_MAP.get(prefix, [])
    if pks and all(k in df.columns for k in pks):
        for k in pks:
            if df[k].dtype == "object":
                df[k] = df[k].astype(str).str.strip().replace(r"^\s*$", pd.NA, regex=True)
        df = df.dropna(subset=pks)
        df = df.drop_duplicates(subset=pks, keep="last")

    load_to_postgres(df, target_table, pks, engine)

def main():
    csv_files = list(INPUT_DIR.glob("*.csv"))
    if not csv_files:
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
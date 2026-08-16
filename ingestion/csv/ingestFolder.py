import datetime
import re
import shutil
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
}

def clean_snake_case(name: str) -> str:
    """Converts string headers to clean snake_case."""
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name.strip())
    return re.sub(r"[^\w]+", "_", s).lower().strip("_")

def load_to_postgres(df: pd.DataFrame, target_table: str, pks: list, engine):
    """Loads a DataFrame into Postgres using append or upsert (merge) strategy."""
    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA};"))

        if pks:
            stg_table = f"_stg_{target_table}"
            # 1. Write current batch to temporary staging table
            df.to_sql(stg_table, conn, schema=SCHEMA, if_exists="replace", index=False)

            # 2. Ensure target table exists (clones structure from staging if missing)
            conn.execute(
                text(f'CREATE TABLE IF NOT EXISTS "{SCHEMA}"."{target_table}" (LIKE "{SCHEMA}"."{stg_table}");')
            )

            # 3. Delete existing records in target matching primary keys in staging
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

            # 4. Insert new records from staging into target
            cols = ", ".join([f'"{col}"' for col in df.columns])
            insert_sql = f"""
                INSERT INTO "{SCHEMA}"."{target_table}" ({cols})
                SELECT {cols} FROM "{SCHEMA}"."{stg_table}";
            """
            conn.execute(text(insert_sql))

            # 5. Clean up staging table
            conn.execute(text(f'DROP TABLE IF EXISTS "{SCHEMA}"."{stg_table}";'))
        else:
            # Simple append if no primary keys are mapped
            df.to_sql(target_table, conn, schema=SCHEMA, if_exists="append", index=False)

def process_file(file_path: Path, engine):
    """Reads, normalizes, and loads a single CSV file."""
    raw_stem = file_path.stem.split("?")[0]
    prefix = re.sub(r"[^\w]+", "", raw_stem.rsplit("_", 1)[0] if "_" in raw_stem else raw_stem).lower()
    target_table = f"{prefix}_raw"

    df = pd.read_csv(file_path)
    df.columns = [clean_snake_case(c) for c in df.columns]

    # Add metadata columns (using pd.Timestamp to ensure native TIMESTAMPTZ database type)
    df.insert(0, "source_file", file_path.name)
    df.insert(0, "load_time", pd.Timestamp.now(tz="UTC"))

    # Primary key matching and NULL cleaning
    pks = PRIMARY_KEY_MAP.get(prefix, [])
    if pks and all(k in df.columns for k in pks):
        for k in pks:
            if df[k].dtype == "object":
                df[k] = df[k].astype(str).str.strip().replace(r"^\s*$", pd.NA, regex=True)
        df = df.dropna(subset=pks)

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
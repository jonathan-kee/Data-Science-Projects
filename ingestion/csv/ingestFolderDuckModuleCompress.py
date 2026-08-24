import datetime
import re
import sys
from pathlib import Path

# Add project root directory to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.utils import clean_snake_case, parse_filename_date
from ingestion.db import init_connections, perform_upsert
from ingestion.archive import process_and_archive_batch

# --- Configuration & Paths ---
INPUT_DIR = Path("/Users/jonathankee/Data-Science-Projects/ingestion/sources_unprocessed")
PROCESSED_DIR = Path("/Users/jonathankee/Data-Science-Projects/ingestion/sources_processed")
DB_URL = "postgresql://postgres:abc123@localhost:5432/prosperous_universe"
SCHEMA = "raw"

PRIMARY_KEY_MAP = {
    "prices": ["ticker", "file_date"],
    "inventory": ["ticker", "storage_type"],
    "workforce": ["planet_natural_id", "material_ticker"]
}

# Initialize DB connection and DuckDB attachment
engine, duck_con = init_connections(DB_URL, schema=SCHEMA)


def process_file(file_path: Path):
    raw_stem = file_path.stem.split("?")[0]
    parts = raw_stem.rsplit("_", 1)
    prefix = re.sub(r"[^\w]+", "", parts[0]).lower()
    
    file_date_str = parse_filename_date(file_path, date_format="DDMMYYYY")
    load_time_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    target_table = f"{prefix}_raw"
    staging_table = f"{target_table}_staging"
    pks = PRIMARY_KEY_MAP.get(prefix, [])

    # Fetch CSV Headers dynamically using DuckDB
    headers_df = duck_con.query(f"SELECT * FROM read_csv_auto('{file_path}') LIMIT 0").df()
    clean_cols = [clean_snake_case(c) for c in headers_df.columns]
    
    select_clause = ", ".join([
        f'"{raw}" AS {clean}' for raw, clean in zip(headers_df.columns, clean_cols)
    ])

    final_columns = ['source_file', 'file_date', 'load_time'] + clean_cols

    # Build Deduplication Clause
    dedup_clause = ""
    if pks:
        pk_partition = ", ".join(pks)
        dedup_clause = f"""
            QUALIFY ROW_NUMBER() OVER (PARTITION BY {pk_partition} ORDER BY load_time DESC) = 1
        """

    # Stream data from CSV -> DuckDB -> Postgres Staging Table
    duck_con.execute(f"DROP TABLE IF EXISTS pg.{SCHEMA}.{staging_table}")
    duck_con.execute(f"""
        CREATE TABLE pg.{SCHEMA}.{staging_table} AS 
        SELECT 
            '{file_path.name}' AS source_file,
            CAST('{file_date_str}' AS DATE) AS file_date,
            CAST('{load_time_str}' AS TIMESTAMP) AS load_time,
            *
        FROM (
            SELECT {select_clause} FROM read_csv_auto('{file_path}')
        )
        {dedup_clause};
    """)

    # Merge Staging into Target Table natively in Postgres
    perform_upsert(
        engine, 
        target_table, 
        staging_table, 
        pks, 
        final_columns, 
        schema=SCHEMA
    )


def main():
    if not INPUT_DIR.exists():
        print(f"Input directory does not exist: {INPUT_DIR}")
        return

    csv_files = list(INPUT_DIR.glob("*.csv"))
    if not csv_files:
        print("No CSV files found.")
        return

    process_and_archive_batch(csv_files, process_file, PROCESSED_DIR, "csv")


if __name__ == "__main__":
    main()
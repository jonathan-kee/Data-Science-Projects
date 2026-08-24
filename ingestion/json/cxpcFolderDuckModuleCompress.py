import re
import sys  # 1. Added missing import
from pathlib import Path

# 2. Add the directory containing the 'ingestion' package (e.g., Data-Science-Projects) to sys.path
# If script is in ingestion/scripts/cxpc_ingest.py, use .parent.parent.parent
# If script is in ingestion/cxpc_ingest.py, use .parent.parent
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.utils import clean_snake_case, parse_filename_date
from ingestion.db import init_connections, perform_upsert
from ingestion.archive import process_and_archive_batch

INPUT_DIR = Path("/Users/jonathankee/Data-Science-Projects/ingestion/sources_unprocessed")
PROCESSED_DIR = Path("/Users/jonathankee/Data-Science-Projects/ingestion/sources_processed")
DB_URL = "postgresql://postgres:abc123@localhost:5432/prosperous_universe"

engine, duck_con = init_connections(DB_URL, schema="raw")

def process_file(file_path: Path):
    parts = file_path.stem.split("_")
    file_prefix = parts[0]
    formatted_date = parse_filename_date(file_path, date_format="DDMMYYYY")

    table_name = f"cxpc_{file_prefix.replace('.', '_')}_raw".lower()
    staging_table = f"{table_name}_staging"
    primary_keys = ["interval", "date_epoch_ms"]

    headers_df = duck_con.query(f"SELECT * FROM read_json_auto('{file_path}') LIMIT 0").df()
    clean_cols = [clean_snake_case(c) for c in headers_df.columns]
    final_columns = ['file_date'] + clean_cols

    pk_partition = ", ".join([clean_snake_case(pk) for pk in primary_keys])
    select_clause = ", ".join([f'"{raw}" AS {clean}' for raw, clean in zip(headers_df.columns, clean_cols)])

    duck_con.execute(f"DROP TABLE IF EXISTS pg.raw.{staging_table}")
    duck_con.execute(f"""
        CREATE TABLE pg.raw.{staging_table} AS 
        SELECT CAST('{formatted_date}' AS DATE) AS file_date, *
        FROM (SELECT {select_clause} FROM read_json_auto('{file_path}'))
        QUALIFY ROW_NUMBER() OVER (PARTITION BY {pk_partition}) = 1;
    """)

    perform_upsert(engine, table_name, staging_table, [clean_snake_case(pk) for pk in primary_keys], final_columns)

def main():
    pattern = re.compile(r"^.*AI1_\d{8}\.json$")
    target_files = [f for f in INPUT_DIR.iterdir() if pattern.match(f.name)]
    if target_files:
        process_and_archive_batch(target_files, process_file, PROCESSED_DIR, "cxpc")
    else:
        print("No eligible files found.")

if __name__ == "__main__":
    main()
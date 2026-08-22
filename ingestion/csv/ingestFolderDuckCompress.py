import datetime
import re
import tarfile
from pathlib import Path

import duckdb
from sqlalchemy import create_engine, text

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

def clean_snake_case(name: str) -> str:
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name.strip())
    return re.sub(r"[^\w]+", "_", s).lower().strip("_")

def perform_upsert(engine, target_table: str, staging_table: str, pks: list, columns: list):
    """Merges the staging table into the target table using native Postgres UPSERT."""
    col_names = ", ".join(columns)
    
    with engine.begin() as conn:
        # 1. If target table doesn't exist, create it from staging directly
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {SCHEMA}.{target_table} 
            AS SELECT * FROM {SCHEMA}.{staging_table} WHERE 1=0;
        """))
        
        # 2. Safely check for and add Primary Keys
        if pks:
            pk_str = ", ".join(pks)
            
            # Query Postgres system catalogs to see if a PK already exists
            check_pk_query = text("""
                SELECT 1
                FROM pg_constraint
                JOIN pg_class ON pg_constraint.conrelid = pg_class.oid
                JOIN pg_namespace ON pg_class.relnamespace = pg_namespace.oid
                WHERE pg_namespace.nspname = :schema
                  AND pg_class.relname = :table
                  AND pg_constraint.contype = 'p';
            """)
            
            has_pk = conn.execute(check_pk_query, {"schema": SCHEMA, "table": target_table}).scalar()
            
            if not has_pk:
                conn.execute(text(f"""
                    ALTER TABLE {SCHEMA}.{target_table} 
                    ADD PRIMARY KEY ({pk_str});
                """))
        
        # 3. Perform the Upsert or Append
        if pks:
            pk_str = ", ".join(pks)
            updates = ", ".join([f"{col} = EXCLUDED.{col}" for col in columns if col not in pks])
            
            do_update = f"DO UPDATE SET {updates}" if updates else "DO NOTHING"
            
            upsert_query = f"""
                INSERT INTO {SCHEMA}.{target_table} ({col_names})
                SELECT {col_names} FROM {SCHEMA}.{staging_table}
                ON CONFLICT ({pk_str}) {do_update};
            """
            conn.execute(text(upsert_query))
        else:
            append_query = f"""
                INSERT INTO {SCHEMA}.{target_table} ({col_names})
                SELECT {col_names} FROM {SCHEMA}.{staging_table};
            """
            conn.execute(text(append_query))
            
        # 4. Clean up staging
        conn.execute(text(f"DROP TABLE {SCHEMA}.{staging_table};"))


def process_file(file_path: Path, duck_con, engine):
    raw_stem = file_path.stem.split("?")[0]
    parts = raw_stem.rsplit("_", 1)
    prefix = re.sub(r"[^\w]+", "", parts[0]).lower()
    
    # Parse file date
    file_date_str = None
    if len(parts) > 1 and re.match(r"^\d{8}$", parts[1]):
        date_str = parts[1]
        try:
            file_date_str = f"{date_str[4:8]}-{date_str[2:4]}-{date_str[0:2]}"
        except ValueError:
            pass
    if not file_date_str:
        file_date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        
    load_time_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    target_table = f"{prefix}_raw"
    staging_table = f"{target_table}_staging"
    pks = PRIMARY_KEY_MAP.get(prefix, [])

    # 1. Fetch CSV Headers using DuckDB to dynamically rename them
    headers_df = duck_con.query(f"SELECT * FROM read_csv_auto('{file_path}') LIMIT 0").df()
    clean_cols = [clean_snake_case(c) for c in headers_df.columns]
    
    # Map raw headers to clean headers for the DuckDB query
    select_clause = ", ".join([
        f'"{raw}" AS {clean}' for raw, clean in zip(headers_df.columns, clean_cols)
    ])

    # Add metadata columns to our list of known columns
    final_columns = ['source_file', 'file_date', 'load_time'] + clean_cols

    # 2. Build Deduplication Logic in DuckDB SQL
    dedup_clause = ""
    if pks:
        pk_partition = ", ".join(pks)
        # Deduplicates based on reading order (keeping the last) via ROW_NUMBER
        dedup_clause = f"""
            QUALIFY ROW_NUMBER() OVER (PARTITION BY {pk_partition} ORDER BY load_time DESC) = 1
        """

    # 3. Stream data from CSV -> DuckDB -> Postgres Staging Table
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

    # 4. Merge Staging into Target Table natively in Postgres
    perform_upsert(engine, target_table, staging_table, pks, final_columns)


def main():
    csv_files = list(INPUT_DIR.glob("*.csv"))
    if not csv_files:
        print("No CSV files found.")
        return

    # Initialize SQLAlchemy for native Postgres DDL (Upserts)
    engine = create_engine(DB_URL)
    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA};"))
        
    # Initialize DuckDB for the heavy data lifting
    duck_con = duckdb.connect()
    duck_con.execute("INSTALL postgres; LOAD postgres;")
    duck_con.execute(f"ATTACH '{DB_URL}' AS pg (TYPE postgres);")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    run_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_tar_name = f"processed_batch_csv_{run_timestamp}.tar.gz"
    batch_tar_path = PROCESSED_DIR / batch_tar_name

    processed_count = 0
    with tarfile.open(batch_tar_path, "w:gz") as tar:
        for file_path in csv_files:
            try:
                process_file(file_path, duck_con, engine)
                tar.add(file_path, arcname=file_path.name)
                file_path.unlink()
                processed_count += 1
                print(f"Loaded and archived: {file_path.name}")
            except Exception as e:
                print(f"Failed to process {file_path.name}: {e}")
                
    if processed_count == 0:
        batch_tar_path.unlink(missing_ok=True)
        print("No files were processed successfully.")
    else:
        print(f"Successfully processed and bundled {processed_count} file(s) into {batch_tar_name}.")

if __name__ == "__main__":
    main()
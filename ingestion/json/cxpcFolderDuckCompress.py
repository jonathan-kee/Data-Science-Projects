import datetime
import os
import re
import tarfile
import time
from pathlib import Path

import duckdb
from sqlalchemy import create_engine, text

def clean_snake_case(name: str) -> str:
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name.strip())
    return re.sub(r"[^\w]+", "_", s).lower().strip("_")

def perform_upsert(engine, target_table: str, staging_table: str, pks: list, columns: list):
    """Merges the staging table into the target table using native Postgres UPSERT with robust PK enforcement."""
    col_names = ", ".join([f'"{col}"' for col in columns])
    
    with engine.begin() as conn:
        # 1. If target table doesn't exist, create it from staging directly
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS raw.{target_table} 
            AS SELECT * FROM raw.{staging_table} WHERE 1=0;
        """))
        
        # 2. Auto-add any missing columns from staging to target table (Schema Evolution)
        staging_cols = conn.execute(text(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'raw' AND table_name = '{staging_table}';
        """)).fetchall()
        
        target_cols = {row[0] for row in conn.execute(text(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'raw' AND table_name = '{target_table}';
        """)).fetchall()}
        
        for col_name, data_type in staging_cols:
            if col_name not in target_cols:
                conn.execute(text(f'ALTER TABLE raw.{target_table} ADD COLUMN "{col_name}" {data_type};'))

        # 3. Robustly ensure the Primary Key constraint exists
        if pks:
            pk_str = ", ".join([f'"{pk}"' for pk in pks])
            
            has_pk = conn.execute(text("""
                SELECT 1
                FROM pg_constraint
                JOIN pg_class ON pg_constraint.conrelid = pg_class.oid
                JOIN pg_namespace ON pg_class.relnamespace = pg_namespace.oid
                WHERE pg_namespace.nspname = 'raw'
                  AND pg_class.relname = :table
                  AND pg_constraint.contype = 'p';
            """), {"table": target_table}).scalar()
            
            if not has_pk:
                try:
                    conn.execute(text(f'ALTER TABLE raw.{target_table} ADD PRIMARY KEY ({pk_str});'))
                except Exception as e:
                    print(f"Warning: Could not add PRIMARY KEY to raw.{target_table}. Details: {e}")
        
        # 4. Perform the Upsert
        updates = ", ".join([f'"{col}" = EXCLUDED."{col}"' for col in columns if col not in pks])
        do_update = f"DO UPDATE SET {updates}" if updates else "DO NOTHING"
        
        if pks:
            pk_str = ", ".join([f'"{pk}"' for pk in pks])
            upsert_query = f"""
                INSERT INTO raw.{target_table} ({col_names})
                SELECT {col_names} FROM raw.{staging_table}
                ON CONFLICT ({pk_str}) {do_update};
            """
            conn.execute(text(upsert_query))
        else:
            append_query = f"""
                INSERT INTO raw.{target_table} ({col_names})
                SELECT {col_names} FROM raw.{staging_table};
            """
            conn.execute(text(append_query))
            
        # 5. Clean up staging
        conn.execute(text(f"DROP TABLE raw.{staging_table};"))

def process_files():
    start_time = time.perf_counter()

    input_folder = Path(
        os.getenv(
            "INPUT_FOLDER",
            "/Users/jonathankee/Data-Science-Projects/ingestion/sources_unprocessed",
        )
    )
    processed_folder = Path(
        "/Users/jonathankee/Data-Science-Projects/ingestion/sources_processed"
    )

    if not input_folder.exists():
        print(f"Input directory does not exist: {input_folder}")
        return

    pattern = re.compile(r"^.*AI1_\d{8}\.json$")
    target_files = [f for f in input_folder.iterdir() if pattern.match(f.name)]

    if not target_files:
        print("No files matching the pattern *AI1_DDMMYYYY.json found in the directory.")
        return

    DB_URL = "postgresql://postgres:abc123@localhost:5432/prosperous_universe"
    engine = create_engine(DB_URL)

    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw;"))

    duck_con = duckdb.connect()
    duck_con.execute("INSTALL postgres; LOAD postgres;")
    duck_con.execute(f"ATTACH '{DB_URL}' AS pg (TYPE postgres);")

    processed_folder.mkdir(parents=True, exist_ok=True)
    run_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_tar_name = f"processed_batch_cxpc_{run_timestamp}.tar.gz"
    batch_tar_path = processed_folder / batch_tar_name

    processed_count = 0

    with tarfile.open(batch_tar_path, "w:gz") as tar:
        for file_path in target_files:
            file_name_generic = file_path.stem
            parts = file_name_generic.split("_")

            if len(parts) < 2:
                print(f"Skipping malformed filename: {file_path.name}")
                continue

            file_prefix = parts[0]
            file_date_str = parts[1]

            table_name = f"cxpc_{file_prefix.replace('.', '_')}_raw".lower()
            staging_table = f"{table_name}_staging"
            primary_keys = ["interval", "date_epoch_ms"]

            try:
                day = file_date_str[0:2]
                month = file_date_str[2:4]
                year = file_date_str[4:8]
                formatted_date = f"{year}-{month}-{day}"
            except IndexError:
                print(f"Invalid date format in filename: {file_path.name}")
                continue

            try:
                # 1. Fetch JSON headers dynamically via DuckDB to map keys to snake_case
                headers_df = duck_con.query(f"SELECT * FROM read_json_auto('{file_path}') LIMIT 0").df()
                clean_cols = [clean_snake_case(c) for c in headers_df.columns]

                final_columns = ['file_date'] + clean_cols

                # 2. Build deduplication clause using DuckDB window functions
                pk_partition = ", ".join([clean_snake_case(pk) for pk in primary_keys])
                dedup_clause = f"""
                    QUALIFY ROW_NUMBER() OVER (PARTITION BY {pk_partition}) = 1
                """

                # Build explicit column select string for DuckDB staging creation
                select_clause = ", ".join([
                    f'"{raw}" AS {clean}' for raw, clean in zip(headers_df.columns, clean_cols)
                ])

                # 3. Stream from JSON -> DuckDB -> Postgres Staging Table
                duck_con.execute(f"DROP TABLE IF EXISTS pg.raw.{staging_table}")
                
                duck_con.execute(f"""
                    CREATE TABLE pg.raw.{staging_table} AS 
                    SELECT 
                        CAST('{formatted_date}' AS DATE) AS file_date,
                        *
                    FROM (
                        SELECT {select_clause} FROM read_json_auto('{file_path}')
                    )
                    {dedup_clause};
                """)

                # 4. Perform native Postgres Upsert with automatic schema and PK enforcement
                perform_upsert(engine, table_name, staging_table, [clean_snake_case(pk) for pk in primary_keys], final_columns)

                # 5. Compress and cleanup
                tar.add(file_path, arcname=file_path.name)
                file_path.unlink()
                processed_count += 1
                
                print(f"Successfully processed and merged {file_path.name} into raw.{table_name}")

            except Exception as e:
                print(f"Failed to process JSON file {file_path.name}: {e}\n")

    if processed_count == 0:
        batch_tar_path.unlink(missing_ok=True)
        print("No files were processed successfully.")
    else:
        print(f"Successfully processed and bundled {processed_count} JSON file(s) into {batch_tar_name}.")

    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(f"\nPipeline finished in {elapsed_time:.4f} seconds.")

if __name__ == "__main__":
    process_files()
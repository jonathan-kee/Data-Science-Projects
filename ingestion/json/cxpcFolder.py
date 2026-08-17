import json
import os
import re
from pathlib import Path
import shutil

import pandas as pd
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.dialects.postgresql import insert


def create_upsert_method(primary_keys):
    """
    Returns a custom upsert method for pandas to_sql to perform Postgres 
    INSERT ... ON CONFLICT DO UPDATE.
    """
    def postgres_upsert(table, conn, keys, data_iter):
        data = [dict(zip(keys, row)) for row in data_iter]
        stmt = insert(table.table).values(data)
        
        # Define columns to update (all columns except the primary keys)
        update_dict = {
            c.name: c 
            for c in stmt.excluded 
            if c.name not in primary_keys
        }
        
        if update_dict:
            upsert_stmt = stmt.on_conflict_do_update(
                index_elements=primary_keys,
                set_=update_dict
            )
        else:
            upsert_stmt = stmt.on_conflict_do_nothing(
                index_elements=primary_keys
            )
            
        conn.execute(upsert_stmt)
    return postgres_upsert


def process_files():
    # Define directories
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

    # Regex pattern matching *AI1_DDMMYYYY.json
    pattern = re.compile(r"^.*AI1_\d{8}\.json$")
    target_files = [f for f in input_folder.iterdir() if pattern.match(f.name)]

    if not target_files:
        print("No files matching the pattern *AI1_DDMMYYYY.json found in the directory.")
        return

    # Initialize SQLAlchemy Engine
    engine = create_engine("postgresql://postgres:abc123@localhost:5432/prosperous_universe")

    # Ensure the target schema exists
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw;"))

    for file_path in target_files:
        file_name_generic = file_path.stem  # Filename without extension
        parts = file_name_generic.split("_")

        if len(parts) < 2:
            print(f"Skipping malformed filename: {file_path.name}")
            continue

        file_prefix = parts[0]
        file_date_str = parts[1]

        # 1. Transform table name: cxpc_afr_ai1_raw
        table_name = f"cxpc_{file_prefix.replace('.', '_')}_raw".lower()

        # 2. Convert DDMMYYYY (e.g. 16082026) to SQL Date format YYYY-MM-DD (2026-08-16)
        try:
            day = file_date_str[0:2]
            month = file_date_str[2:4]
            year = file_date_str[4:8]
            formatted_date = f"{year}-{month}-{day}"
        except IndexError:
            print(f"Invalid date format in filename: {file_path.name}")
            continue

        # Read JSON file on disk
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                print(f"The JSON file {file_path.name} does not contain a top-level array.")
                continue

            print(f"Loaded {len(data)} items successfully from {file_path.name}!")
        except Exception as e:
            print(f"Failed to read or parse JSON file {file_path.name}: {e}")
            continue

        # Load into Pandas DataFrame
        df = pd.DataFrame(data)

        # Push metadata and deduplicate (prevents within-batch upsert errors)
        df["file_date"] = formatted_date
        
        # We must drop exact duplicate primary keys within the same file to prevent Postgres errors
        df = df.drop_duplicates(subset=["Interval", "DateEpochMs"], keep="last")

        try:
            # Check if dynamic table already exists
            inspector = inspect(engine)
            table_exists = inspector.has_table(table_name, schema="raw")
            
            if not table_exists:
                # If table doesn't exist, create it with 0 rows, then explicitly add Primary Keys
                df.head(0).to_sql(table_name, engine, schema="raw", if_exists="fail", index=False)
                with engine.begin() as conn:
                    # Note: We quote the column names because PostgreSQL forces lowercase unquoted identifiers
                    conn.execute(text(
                        f'ALTER TABLE raw.{table_name} ADD PRIMARY KEY ("Interval", "DateEpochMs");'
                    ))

            # Execute the Upsert
            df.to_sql(
                name=table_name,
                con=engine,
                schema="raw",
                if_exists="append",
                index=False,
                method=create_upsert_method(primary_keys=["Interval", "DateEpochMs"])
            )
            
            print(f"Successfully upserted data into table raw.{table_name}!")

            # Move processed file to processed folder
            processed_folder.mkdir(parents=True, exist_ok=True)
            processed_file_path = processed_folder / file_path.name
            shutil.move(str(file_path), str(processed_file_path))
            print(f"Successfully moved JSON file to: {processed_file_path}\n")

        except Exception as e:
            print(f"Error during database ingestion or file moving for {file_path.name}: {e}\n")


if __name__ == "__main__":
    process_files()
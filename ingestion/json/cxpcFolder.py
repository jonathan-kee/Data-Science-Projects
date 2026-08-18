import json
import os
import re
from pathlib import Path
import shutil

import pandas as pd
from sqlalchemy import create_engine, text, inspect

# This code implements a latest state pattern.
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
    
    # Find target files (No list comprehension)
    target_files = []
    for f in input_folder.iterdir():
        if pattern.match(f.name):
            target_files.append(f)

    if len(target_files) == 0:
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
        staging_table = f"{table_name}_stg"
        primary_keys = ["Interval", "DateEpochMs"]

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
        
        # Drop exact duplicate primary keys within the same file to prevent Postgres errors
        df = df.drop_duplicates(subset=primary_keys, keep="last")

        try:
            # Check if dynamic table already exists
            inspector = inspect(engine)
            table_exists = inspector.has_table(table_name, schema="raw")
            
            # Step 1: If target table doesn't exist, create an empty one and set the primary keys
            if not table_exists:
                df.head(0).to_sql(table_name, engine, schema="raw", if_exists="fail", index=False)
                with engine.begin() as conn:
                    # Note: We quote the column names because PostgreSQL forces lowercase unquoted identifiers
                    conn.execute(text(
                        f'ALTER TABLE raw.{table_name} ADD PRIMARY KEY ("Interval", "DateEpochMs");'
                    ))

            # Step 2: Push data to a staging table
            # We use a single connection for the staging table write and merge execution
            with engine.begin() as conn:
                df.to_sql(
                    name=staging_table,
                    con=conn,
                    schema="raw",
                    if_exists="replace", # Replaces the staging table for every batch
                    index=False
                )

                # Step 3: Construct the Merge/Upsert SQL Query
                
                # Gather column names with quotes (No list comprehension)
                columns_quoted = []
                for col in df.columns:
                    columns_quoted.append(f'"{col}"')
                col_str = ", ".join(columns_quoted)
                
                # Gather update conditions (No list comprehension)
                update_clauses = []
                for col in df.columns:
                    if col not in primary_keys:
                        update_clauses.append(f'"{col}" = EXCLUDED."{col}"')
                
                # Gather primary keys with quotes
                pk_quoted = []
                for pk in primary_keys:
                    pk_quoted.append(f'"{pk}"')
                pk_str = ", ".join(pk_quoted)

                if len(update_clauses) > 0:
                    set_clause = ", ".join(update_clauses)
                    conflict_action = f"DO UPDATE SET {set_clause}"
                else:
                    conflict_action = "DO NOTHING"

                # Standard SQL Merge Pattern via INSERT ... ON CONFLICT
                merge_sql = f"""
                    INSERT INTO raw.{table_name} ({col_str})
                    SELECT {col_str} FROM raw.{staging_table}
                    ON CONFLICT ({pk_str})
                    {conflict_action};
                """
                
                # Step 4: Execute the merge and drop the staging table
                conn.execute(text(merge_sql))
                conn.execute(text(f"DROP TABLE raw.{staging_table};"))
            
            print(f"Successfully merged/upserted data into table raw.{table_name}!")

            # Move processed file to processed folder
            processed_folder.mkdir(parents=True, exist_ok=True)
            processed_file_path = processed_folder / file_path.name
            shutil.move(str(file_path), str(processed_file_path))
            print(f"Successfully moved JSON file to: {processed_file_path}\n")

        except Exception as e:
            print(f"Error during database ingestion or file moving for {file_path.name}: {e}\n")


if __name__ == "__main__":
    process_files()
import datetime
import json
import os
import re
import tarfile
import time
from pathlib import Path

import pandas as pd
from pangres import upsert
from sqlalchemy import create_engine, text

# This code implements a latest state pattern.
def process_files():
    start_time = time.perf_counter()

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
    
    # Find target files
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

    # Prepare batch archive with the updated naming convention
    processed_folder.mkdir(parents=True, exist_ok=True)
    run_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_tar_name = f"processed_batch_cxpc_{run_timestamp}.tar.gz"
    batch_tar_path = processed_folder / batch_tar_name

    processed_count = 0

    # Open the master tar archive once for the entire run
    with tarfile.open(batch_tar_path, "w:gz") as tar:
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
            primary_keys = ["Interval", "DateEpochMs"]

            # 2. Convert DDMMYYYY (e.g. 16082026) to SQL Date format YYYY-MM-DD
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
            df = df.drop_duplicates(subset=primary_keys, keep="last")

            try:
                # pangres requires the primary keys to be set as the DataFrame index
                df = df.set_index(primary_keys)

                # Upsert using pangres: handles table creation, primary keys, and schema evolution automatically
                upsert(
                    con=engine,
                    df=df,
                    table_name=table_name,
                    schema="raw",
                    if_row_exists="update",
                    add_new_columns=True
                )
                
                print(f"Successfully merged/upserted data into table raw.{table_name}!")

                # --- BATCH COMPRESSION LOGIC ---
                tar.add(file_path, arcname=file_path.name)
                file_path.unlink() # Delete the original JSON
                processed_count += 1
                
                print(f"Successfully compressed and removed JSON file: {file_path.name}\n")

            except Exception as e:
                print(f"Error during database ingestion or archiving for {file_path.name}: {e}\n")

    # Clean up empty tar file if the script ran but all files failed
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
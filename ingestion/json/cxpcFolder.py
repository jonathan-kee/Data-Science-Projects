from datetime import datetime
import json
import os
import re
from pathlib import Path
import shutil
import dlt
from dlt.destinations import postgres


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
    print(
        "No files matching the pattern *AI1_DDMMYYYY.json found in the"
        " directory."
    )
    return

  # Initialize dlt pipeline with your PostgreSQL credentials
  pipeline = dlt.pipeline(
      pipeline_name="json_file_ingestion",
      destination=postgres(
          credentials="postgresql://postgres:abc123@localhost:5432/prosperous_universe"
      ),
      dataset_name="raw",
  )

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
        print(
            f"The JSON file {file_path.name} does not contain a top-level"
            " array."
        )
        continue

      print(f"Loaded {len(data)} items successfully from {file_path.name}!")
    except Exception as e:
      print(f"Failed to read or parse JSON file {file_path.name}: {e}")
      continue

    # Push file_date metadata entry into each record
    for item in data:
      item["file_date"] = formatted_date

    # Define dlt resource with merge write disposition and primary keys for idempotency / upsert
    @dlt.resource(
        name=table_name,
        write_disposition="merge",
        primary_key=("Interval", "DateEpochMs"),
    )
    def json_resource():
      yield data

    # Run the pipeline
    try:
      load_info = pipeline.run(json_resource())
      print(f"Successfully loaded data into table raw.{table_name}!")
      print(load_info)

      # Move processed file to processed folder
      processed_folder.mkdir(parents=True, exist_ok=True)
      processed_file_path = processed_folder / file_path.name
      shutil.move(str(file_path), str(processed_file_path))
      print(f"Successfully moved JSON file to: {processed_file_path}")

    except Exception as e:
      print(
          f"Error during pipeline execution or file moving for"
          f" {file_path.name}: {e}"
      )


if __name__ == "__main__":
  process_files()
import datetime
import os
from pathlib import Path
import re
import shutil
import dlt
from dlt.destinations import postgres
import pandas as pd

# Explicit primary key mappings (using standard snake_case column names)
PRIMARY_KEY_MAP = {
    "prices": ["ticker"],
    "inventory": ["ticker", "storage_type"],
    "recipeinputs": ["key"],
}


def sanitize_prefix(raw_prefix: str) -> str:
  """Strips query parameters and non-alphanumeric characters (except underscores)."""
  clean = raw_prefix.split("?")[0]
  return "".join(c for c in clean if c.isalnum() or c == "_")


def to_snake_case(name: str) -> str:
  """Converts PascalCase, camelCase, or spaced strings to snake_case."""
  s = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name.strip())
  s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
  return s.lower().replace(" ", "_").replace("__", "_")


def main():
  input_folder = Path(
      "/Users/jonathankee/Data-Science-Projects/ingestion/sources_unprocessed"
  )
  processed_folder = Path(
      "/Users/jonathankee/Data-Science-Projects/ingestion/sources_processed"
  )

  csv_files = list(input_folder.glob("*.csv"))

  if not csv_files:
    print(f"No .csv files found in {input_folder}")
    return

  print(f"Found {len(csv_files)} CSV file(s) to process.")

  # dev_mode=True forces dlt to recreate tables and schemas on each run during development
  pipeline = dlt.pipeline(
      pipeline_name="csv_folder_ingestion",
      destination=postgres(
          credentials="postgresql://postgres:abc123@localhost:5432/prosperous_universe"
      ),
      dataset_name="raw",
      dev_mode=True,
  )

  resources = []

  for file_path in csv_files:
    filename = file_path.name
    name_without_ext = file_path.stem

    parts = name_without_ext.rsplit("_", 1)
    if len(parts) == 2 and len(parts[1]) == 8 and parts[1].isdigit():
      raw_prefix, date_str = parts[0], parts[1]
      formatted_date = f"{date_str[:2]}/{date_str[2:4]}/{date_str[4:]}"
    else:
      raw_prefix = name_without_ext
      formatted_date = datetime.datetime.now().strftime("%d/%m/%Y")

    prefix = sanitize_prefix(raw_prefix).lower()
    target_table = f"{prefix}_raw"

    try:
      df = pd.read_csv(file_path, sep=",", header="infer")
    except Exception as e:
      print(f"Error reading {filename}: {e}")
      continue

    # Standardize headers to snake_case (e.g., StorageType -> storage_type)
    df.columns = [to_snake_case(col) for col in df.columns]

    current_time = datetime.datetime.now().strftime("%H:%M:%S")
    load_time_str = f"{formatted_date} {current_time}"

    df.insert(0, "source_file", filename)
    df.insert(0, "load_time", load_time_str)

    configured_keys = PRIMARY_KEY_MAP.get(prefix)
    if isinstance(configured_keys, str):
      configured_keys = [configured_keys]

    if configured_keys and all(k in df.columns for k in configured_keys):
      primary_key = configured_keys
      write_disp = "merge"
    else:
      primary_key = None
      write_disp = "append"
      if configured_keys:
        print(
            f"Warning: Primary key columns {configured_keys} not found in"
            f" {filename}. Available columns: {list(df.columns)}. Falling back"
            " to APPEND."
        )

    print(
        f"Preparing {len(df)} rows from '{filename}' for '{target_table}'"
        f" ({write_disp.upper()}"
        + (f" on {primary_key}" if primary_key else "")
        + ")"
    )

    res = dlt.resource(
        df,
        name=target_table,
        write_disposition=write_disp,
        primary_key=primary_key,
    )
    resources.append(res)

  if not resources:
    print("No valid CSV files to ingest.")
    return

  try:
    load_info = pipeline.run(resources)
    print("\n--- dlt Pipeline Load Summary ---")
    print(load_info)

    processed_folder.mkdir(parents=True, exist_ok=True)
    for file_path in csv_files:
      destination = processed_folder / file_path.name
      if destination.exists():
        destination.unlink()
      shutil.move(str(file_path), str(destination))
      print(f"Archived {file_path.name} to {destination}")

  except Exception as e:
    print(f"Error during dlt pipeline execution: {e}")


if __name__ == "__main__":
  main()
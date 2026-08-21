import datetime
import re
import tarfile
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from pangres import upsert  

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

def load_to_postgres(df: pd.DataFrame, target_table: str, pks: list, engine):
    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA};"))

    if pks:
        df = df.set_index(pks)
        upsert(
            con=engine, 
            df=df, 
            table_name=target_table, 
            schema=SCHEMA,
            if_row_exists='update',
            add_new_columns=True
        )
    else:
        df.to_sql(
            name=target_table, 
            con=engine, 
            schema=SCHEMA, 
            if_exists='append', 
            index=False
        )

def process_file(file_path: Path, engine):
    raw_stem = file_path.stem.split("?")[0]
    parts = raw_stem.rsplit("_", 1)
    prefix = re.sub(r"[^\w]+", "", parts[0]).lower()
    
    file_date_str = None
    if len(parts) > 1 and re.match(r"^\d{8}$", parts[1]):
        date_str = parts[1]
        try:
            file_date_str = f"{date_str[4:8]}-{date_str[2:4]}-{date_str[0:2]}"
        except ValueError:
            pass
            
    if not file_date_str:
        file_date_str = pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%d")

    target_table = f"{prefix}_raw"

    df = pd.read_csv(file_path)
    df.columns = [clean_snake_case(c) for c in df.columns]

    df.insert(0, "source_file", file_path.name)
    df.insert(0, "file_date", pd.to_datetime(file_date_str).date())
    df.insert(0, "load_time", pd.Timestamp.now(tz="UTC"))

    pks = PRIMARY_KEY_MAP.get(prefix, [])
    if pks and all(k in df.columns for k in pks):
        for k in pks:
            if df[k].dtype == "object":
                df[k] = df[k].astype(str).str.strip().replace(r"^\s*$", pd.NA, regex=True)
        
        df = df.dropna(subset=pks)
        df = df.drop_duplicates(subset=pks, keep="last")

    load_to_postgres(df, target_table, pks, engine)

def main():
    csv_files = list(INPUT_DIR.glob("*.csv"))
        
    if not csv_files:
        print("No CSV files found.")
        return

    engine = create_engine(DB_URL)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Generate a unique batch name with the explicit csv label using the current timestamp
    run_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_tar_name = f"processed_batch_csv_{run_timestamp}.tar.gz"
    batch_tar_path = PROCESSED_DIR / batch_tar_name

    processed_count = 0
    
    # Open the master tar archive once for the entire run
    with tarfile.open(batch_tar_path, "w:gz") as tar:
        for file_path in csv_files:
            try:
                # 1. Process and load to DB
                process_file(file_path, engine)
                
                # 2. Add to the batch archive
                tar.add(file_path, arcname=file_path.name)
                
                # 3. Delete the original CSV
                file_path.unlink()
                
                processed_count += 1
                print(f"Loaded and archived: {file_path.name}")
            except Exception as e:
                print(f"Failed to process {file_path.name}: {e}")

    # Clean up empty tar file if the script ran but all files failed
    if processed_count == 0:
        batch_tar_path.unlink(missing_ok=True)
        print("No files were processed successfully.")
    else:
        print(f"Successfully processed and bundled {processed_count} file(s) into {batch_tar_name}.")

if __name__ == "__main__":
    main()
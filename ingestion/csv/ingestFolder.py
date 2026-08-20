import datetime
import re
import shutil
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from pangres import upsert  # Import the library

# --- Configuration & Paths ---
INPUT_DIR = Path("/Users/jonathankee/Data-Science-Projects/ingestion/sources_unprocessed")
PROCESSED_DIR = Path("/Users/jonathankee/Data-Science-Projects/ingestion/sources_processed")

DB_URL = "postgresql://postgres:abc123@localhost:5432/prosperous_universe"
SCHEMA = "raw"

# Primary key mapping defining the UPSERT behavior
PRIMARY_KEY_MAP = {
    "prices": ["ticker", "file_date"],
    "inventory": ["ticker", "storage_type"],
    "workforce": ["planet_natural_id", "material_ticker"]
}

def clean_snake_case(name: str) -> str:
    """Converts string headers to clean snake_case."""
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name.strip())
    return re.sub(r"[^\w]+", "_", s).lower().strip("_")

def load_to_postgres(df: pd.DataFrame, target_table: str, pks: list, engine):
    """Loads a DataFrame into Postgres utilizing pangres for schema evolution and upserts."""
    
    # 1. Ensure the schema exists (pangres handles table creation, but not schema creation)
    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA};"))

    # 2. Database Loading
    if pks:
        # pangres requires the primary key(s) to be set as the DataFrame index
        df = df.set_index(pks)
        
        # This single line handles:
        # - Creating the table if it doesn't exist
        # - Adding new columns to the database if the CSV has them
        # - Staging the data and generating the "ON CONFLICT DO UPDATE" logic safely
        upsert(
            con=engine, 
            df=df, 
            table_name=target_table, 
            schema=SCHEMA,
            if_row_exists='update',
            add_new_columns=True
        )
    else:
        # Fallback for append-only tables that have no primary keys
        df.to_sql(
            name=target_table, 
            con=engine, 
            schema=SCHEMA, 
            if_exists='append', 
            index=False
        )

def process_file(file_path: Path, engine):
    """Reads, normalizes, cleans, and loads a single CSV file."""
    
    # --- File Parsing ---
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

    # --- Data Transformations ---
    df = pd.read_csv(file_path)
    df.columns = [clean_snake_case(c) for c in df.columns]

    # Inject metadata columns
    df.insert(0, "source_file", file_path.name)
    df.insert(0, "file_date", pd.to_datetime(file_date_str).date())
    df.insert(0, "load_time", pd.Timestamp.now(tz="UTC"))

    # --- Data Cleaning & Deduplication ---
    pks = PRIMARY_KEY_MAP.get(prefix, [])
    if pks and all(k in df.columns for k in pks):
        
        # Clean string-based primary keys
        for k in pks:
            if df[k].dtype == "object":
                df[k] = df[k].astype(str).str.strip().replace(r"^\s*$", pd.NA, regex=True)
        
        # Clean the data so pangres doesn't fail on index constraint violations
        df = df.dropna(subset=pks)
        df = df.drop_duplicates(subset=pks, keep="last")

    # Pass the clean dataframe to our simplified database function
    load_to_postgres(df, target_table, pks, engine)

def main():
    csv_files = list(INPUT_DIR.glob("*.csv"))
        
    if not csv_files:
        print("No CSV files found.")
        return

    engine = create_engine(DB_URL)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    processed_count = 0
    for file_path in csv_files:
        try:
            process_file(file_path, engine)
            shutil.move(str(file_path), str(PROCESSED_DIR / file_path.name))
            processed_count += 1
            print(f"Loaded and moved: {file_path.name}")
        except Exception as e:
            print(f"Failed to process {file_path.name}: {e}")

    print(f"Successfully processed and moved {processed_count} file(s).")

if __name__ == "__main__":
    main()
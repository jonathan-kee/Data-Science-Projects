import json
import sys
from pathlib import Path
import pandas as pd

# Add project root directory to sys.path to allow absolute imports from local packages
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.utils import parse_filename_date
from ingestion.db import init_connections, perform_upsert
from ingestion.archive import process_and_archive_batch

# --- Configuration & Paths ---
INPUT_DIR = Path("/Users/jonathankee/Data-Science-Projects/ingestion/sources_unprocessed")
PROCESSED_DIR = Path("/Users/jonathankee/Data-Science-Projects/ingestion/sources_processed")
DB_URL = "postgresql://postgres:abc123@localhost:5432/prosperous_universe"
SCHEMA = "raw"

# Define primary keys used for table upserts (deduplication/conflict resolution)
PRIMARY_KEY_MAP = {
    "buildings": ["id"],
    "building_costs": ["building_id", "commodity_ticker"]
}

# Initialize PostgreSQL SQLAlchemy engine and DuckDB connection (with PostgreSQL extension attached)
engine, duck_con = init_connections(DB_URL, schema=SCHEMA)


def process_file(file_path: Path):
    """
    Parses a single JSON building file, stages the extracted data using DuckDB, 
    and upserts it into the PostgreSQL database.
    """
    # 1. Extract file date from the filename based on the specified format
    file_date_str = parse_filename_date(file_path, date_format="DDMMYYYY")

    # 2. Load the raw JSON payload
    with open(file_path, "r", encoding="utf-8") as f:
        data_payload = json.load(f)

    # 3. Validate that a BuildingId exists; skip the file if it's missing
    building_id = data_payload.get("BuildingId")
    if not building_id:
        print(f'-> Missing "BuildingId" in JSON payload for file {file_path.name}. Skipping.')
        return

    # 4. Extract building-level attributes into a structured list
    buildings_data = [{
        "id": building_id,
        "ticker": data_payload.get("Ticker"),
        "name": data_payload.get("Name"),
        "area_cost": data_payload.get("AreaCost"),
        "user_name_submitted": data_payload.get("UserNameSubmitted"),
        "file_date": file_date_str,
    }]

    # 5. Extract itemized building cost attributes into a list of dictionaries
    building_costs_data = []
    for cost in data_payload.get("BuildingCosts", []):
        building_costs_data.append({
            "building_id": building_id,
            "commodity_name": cost.get("CommodityName"),
            "commodity_ticker": cost.get("CommodityTicker"),
            "weight": cost.get("Weight"),
            "volume": cost.get("Volume"),
            "amount": cost.get("Amount"),
        })

    # 6. Convert lists to Pandas DataFrames and drop duplicate records (keeping the last entry)
    df_buildings = pd.DataFrame(buildings_data).drop_duplicates(subset=["id"], keep="last")
    df_costs = pd.DataFrame(building_costs_data)
    if not df_costs.empty:
        df_costs = df_costs.drop_duplicates(subset=["building_id", "commodity_ticker"], keep="last")

    # 7. Stage buildings data using DuckDB's replacement scan feature (reads local df_buildings directly)
    duck_con.execute(f"DROP TABLE IF EXISTS pg.{SCHEMA}.buildings_raw_staging")
    duck_con.execute(f"""
        CREATE TABLE pg.{SCHEMA}.buildings_raw_staging AS 
        SELECT * FROM df_buildings;
    """)

    # Perform upsert from staging to the main PostgreSQL buildings raw table
    buildings_cols = ["id", "ticker", "name", "area_cost", "user_name_submitted", "file_date"]
    perform_upsert(
        engine, 
        "buildings_raw", 
        "buildings_raw_staging", 
        PRIMARY_KEY_MAP["buildings"], 
        buildings_cols, 
        schema=SCHEMA
    )

    # 8. Stage and upsert building costs raw table (only if costs data is present)
    if not df_costs.empty:
        duck_con.execute(f"DROP TABLE IF EXISTS pg.{SCHEMA}.building_costs_raw_staging")
        duck_con.execute(f"""
            CREATE TABLE pg.{SCHEMA}.building_costs_raw_staging AS 
            SELECT * FROM df_costs;
        """)
        
        costs_cols = ["building_id", "commodity_name", "commodity_ticker", "weight", "volume", "amount"]
        perform_upsert(
            engine, 
            "building_costs_raw", 
            "building_costs_raw_staging", 
            PRIMARY_KEY_MAP["building_costs"], 
            costs_cols, 
            schema=SCHEMA
        )


def main():
    """
    Locates unprocessed JSON files, filters out files containing 'AI1', 
    and triggers batch processing and archiving.
    """
    if not INPUT_DIR.exists():
        print(f"Input directory does not exist: {INPUT_DIR}")
        return

    # Filter for valid JSON files while excluding any files with "AI1" in their name
    target_files = [
        f for f in INPUT_DIR.iterdir() 
        if f.is_file() and f.name.endswith(".json") and "AI1" not in f.name
    ]

    if not target_files:
        print('No eligible files (without "AI1") found in the directory.')
        return

    # Process the batch of filtered files and move them to the processed directory
    process_and_archive_batch(target_files, process_file, PROCESSED_DIR, "buildings")


if __name__ == "__main__":
    main()
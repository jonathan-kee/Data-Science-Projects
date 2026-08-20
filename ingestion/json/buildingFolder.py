from datetime import date
import json
import os
from pathlib import Path
import shutil

import pandas as pd
from pangres import upsert
from sqlalchemy import create_engine, text

def main():
    # Define directories matching your local paths
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

    # Filter files: must end with '.json' and NOT contain 'AI1'
    target_files = []
    for f in input_folder.iterdir():
        if f.is_file() and f.name.endswith(".json") and "AI1" not in f.name:
            target_files.append(f)

    if len(target_files) == 0:
        print('No eligible files (without "AI1") found in the directory.')
        return

    buildings_data = []
    building_costs_data = []
    current_date = date.today().isoformat()

    # Parse JSON files
    for file_path in target_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data_payload = json.load(f)
            print(f"Loaded JSON successfully from {file_path.name}!")
        except Exception as e:
            print(f"Failed to read or parse JSON file {file_path.name}: {e}")
            continue

        building_id = data_payload.get("BuildingId")
        if not building_id:
            print(f'Missing "BuildingId" in JSON payload for file {file_path.name}.')
            continue

        buildings_data.append({
            "id": building_id,
            "ticker": data_payload.get("Ticker"),
            "name": data_payload.get("Name"),
            "area_cost": data_payload.get("AreaCost"),
            "user_name_submitted": data_payload.get("UserNameSubmitted"),
            "file_date": current_date,
        })

        for cost in data_payload.get("BuildingCosts", []):
            building_costs_data.append({
                "building_id": building_id,
                "commodity_name": cost.get("CommodityName"),
                "commodity_ticker": cost.get("CommodityTicker"),
                "weight": cost.get("Weight"),
                "volume": cost.get("Volume"),
                "amount": cost.get("Amount"),
            })

    if len(buildings_data) == 0:
        print("No valid building data found to process.")
        return

    # Convert to Pandas DataFrames and deduplicate to ensure within-batch idempotency
    df_buildings = pd.DataFrame(buildings_data).drop_duplicates(subset=["id"], keep="last")
    df_costs = pd.DataFrame(building_costs_data).drop_duplicates(subset=["building_id", "commodity_ticker"], keep="last")

    # pangres requires primary keys to be set as the DataFrame index
    df_buildings = df_buildings.set_index("id")
    df_costs = df_costs.set_index(["building_id", "commodity_ticker"])

    # Database connection using SQLAlchemy
    engine = create_engine("postgresql://postgres:abc123@localhost:5432/prosperous_universe")

    try:
        with engine.begin() as conn:
            # Ensure schema exists
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw;"))

        # ---------------------------------------------------------
        # Upsert for 'buildings' Table via pangres
        # ---------------------------------------------------------
        upsert(
            con=engine,
            df=df_buildings,
            table_name="buildings",
            schema="raw",
            if_row_exists="update",
            add_new_columns=True
        )

        # ---------------------------------------------------------
        # Upsert for 'building_costs' Table via pangres
        # ---------------------------------------------------------
        if not df_costs.empty:
            upsert(
                con=engine,
                df=df_costs,
                table_name="building_costs",
                schema="raw",
                if_row_exists="update",
                add_new_columns=True
            )

        print('\nSUCCESS: Pipeline execution completed with pangres Upserts in schema "raw".\n')

        # Safe check for database results
        try:
            query = """
                SELECT id, name, ticker, area_cost, user_name_submitted, file_date 
                FROM raw.buildings
            """
            with engine.connect() as conn:
                summary_df = pd.read_sql(text(query), conn)
                
            print('--- Queried Database Summary (from schema "raw") ---')
            for row in summary_df.to_dict(orient="records"):
                print(row)
        except Exception as query_err:
            print(f"Note: Could not run summary print query automatically: {query_err}")

        # Move processed files to the processed folder
        processed_folder.mkdir(parents=True, exist_ok=True)
        for file_path in target_files:
            processed_file_path = processed_folder / file_path.name
            shutil.move(str(file_path), str(processed_file_path))
            print(f"Successfully moved JSON file to: {processed_file_path}")

    except Exception as e:
        print(f"Error during pipeline execution: {e}\n")


if __name__ == "__main__":
    main()
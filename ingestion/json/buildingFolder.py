from datetime import date
import json
import os
from pathlib import Path
import shutil

import pandas as pd
from sqlalchemy import create_engine, text

# This code implements a latest state pattern.
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

    # Filter files: must end with '.json' and NOT contain 'AI1' (No list comprehension)
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

    # Database connection using SQLAlchemy
    engine = create_engine("postgresql://postgres:abc123@localhost:5432/prosperous_universe")

    try:
        with engine.begin() as conn:
            # Pre-create Schema and Tables WITH Primary Keys explicitly
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw;"))
            
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS raw.buildings (
                    id TEXT PRIMARY KEY,
                    ticker TEXT,
                    name TEXT,
                    area_cost DOUBLE PRECISION,
                    user_name_submitted TEXT,
                    file_date TEXT
                );
            """))
            
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS raw.building_costs (
                    building_id TEXT,
                    commodity_name TEXT,
                    commodity_ticker TEXT,
                    weight DOUBLE PRECISION,
                    volume DOUBLE PRECISION,
                    amount DOUBLE PRECISION,
                    PRIMARY KEY (building_id, commodity_ticker),
                    CONSTRAINT fk_building FOREIGN KEY (building_id) REFERENCES raw.buildings(id) ON DELETE CASCADE
                );
            """))

            # ---------------------------------------------------------
            # Merge / Upsert for 'buildings' Table via Staging
            # ---------------------------------------------------------
            pk_buildings = ["id"]
            staging_buildings = "buildings_stg"
            
            df_buildings.to_sql(
                name=staging_buildings,
                con=conn,
                schema="raw",
                if_exists="replace",
                index=False
            )
            
            # Gather column names with quotes (No list comprehension)
            b_cols_quoted = []
            for col in df_buildings.columns:
                b_cols_quoted.append(f'"{col}"')
            b_col_str = ", ".join(b_cols_quoted)
            
            # Gather update conditions (No list comprehension)
            b_update_clauses = []
            for col in df_buildings.columns:
                if col not in pk_buildings:
                    b_update_clauses.append(f'"{col}" = EXCLUDED."{col}"')
            
            # Gather primary keys with quotes
            b_pk_quoted = []
            for pk in pk_buildings:
                b_pk_quoted.append(f'"{pk}"')
            b_pk_str = ", ".join(b_pk_quoted)
            
            if len(b_update_clauses) > 0:
                b_set_clause = ", ".join(b_update_clauses)
                b_conflict_action = f"DO UPDATE SET {b_set_clause}"
            else:
                b_conflict_action = "DO NOTHING"

            merge_buildings_sql = f"""
                INSERT INTO raw.buildings ({b_col_str})
                SELECT {b_col_str} FROM raw.{staging_buildings}
                ON CONFLICT ({b_pk_str})
                {b_conflict_action};
            """
            
            conn.execute(text(merge_buildings_sql))
            conn.execute(text(f"DROP TABLE raw.{staging_buildings};"))


            # ---------------------------------------------------------
            # Merge / Upsert for 'building_costs' Table via Staging
            # ---------------------------------------------------------
            if not df_costs.empty:
                pk_costs = ["building_id", "commodity_ticker"]
                staging_costs = "building_costs_stg"
                
                df_costs.to_sql(
                    name=staging_costs,
                    con=conn,
                    schema="raw",
                    if_exists="replace",
                    index=False
                )
                
                # Gather column names with quotes
                c_cols_quoted = []
                for col in df_costs.columns:
                    c_cols_quoted.append(f'"{col}"')
                c_col_str = ", ".join(c_cols_quoted)
                
                # Gather update conditions
                c_update_clauses = []
                for col in df_costs.columns:
                    if col not in pk_costs:
                        c_update_clauses.append(f'"{col}" = EXCLUDED."{col}"')
                
                # Gather primary keys with quotes
                c_pk_quoted = []
                for pk in pk_costs:
                    c_pk_quoted.append(f'"{pk}"')
                c_pk_str = ", ".join(c_pk_quoted)
                
                if len(c_update_clauses) > 0:
                    c_set_clause = ", ".join(c_update_clauses)
                    c_conflict_action = f"DO UPDATE SET {c_set_clause}"
                else:
                    c_conflict_action = "DO NOTHING"

                merge_costs_sql = f"""
                    INSERT INTO raw.building_costs ({c_col_str})
                    SELECT {c_col_str} FROM raw.{staging_costs}
                    ON CONFLICT ({c_pk_str})
                    {c_conflict_action};
                """
                
                conn.execute(text(merge_costs_sql))
                conn.execute(text(f"DROP TABLE raw.{staging_costs};"))

        print('\nSUCCESS: Pipeline execution completed with Upserts in schema "raw".\n')

        # Safe check for database results
        try:
            query = """
                SELECT id, name, ticker, area_cost, user_name_submitted, file_date 
                FROM raw.buildings
            """
            with engine.connect() as conn:
                summary_df = pd.read_sql(text(query), conn)
                
            print('--- Queried Database Summary (from schema "raw") ---')
            # Iterate through rows without list/dictionary comprehensions
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
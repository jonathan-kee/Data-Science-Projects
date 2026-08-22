import datetime
import json
import os
import re
import tarfile
import time
from pathlib import Path

import duckdb
import pandas as pd
from sqlalchemy import create_engine, text

# --- Configuration & Paths ---
INPUT_DIR = Path("/Users/jonathankee/Data-Science-Projects/ingestion/sources_unprocessed")
PROCESSED_DIR = Path("/Users/jonathankee/Data-Science-Projects/ingestion/sources_processed")

DB_URL = "postgresql://postgres:abc123@localhost:5432/prosperous_universe"
SCHEMA = "raw"

# Define primary keys mapping to follow the {prefix}_raw convention
PRIMARY_KEY_MAP = {
    "buildings": ["id"],
    "building_costs": ["building_id", "commodity_ticker"]
}

def clean_snake_case(name: str) -> str:
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name.strip())
    return re.sub(r"[^\w]+", "_", s).lower().strip("_")

def perform_upsert(engine, target_table: str, staging_table: str, pks: list, columns: list):
    """Merges the staging table into the target table using native Postgres UPSERT with schema evolution & PK enforcement."""
    col_names = ", ".join([f'"{col}"' for col in columns])
    
    with engine.begin() as conn:
        # 1. If target table doesn't exist, create it from staging directly
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {SCHEMA}.{target_table} 
            AS SELECT * FROM {SCHEMA}.{staging_table} WHERE 1=0;
        """))
        
        # 2. Auto-add any missing columns from staging to target table (Schema Evolution)
        staging_cols = conn.execute(text(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = '{SCHEMA}' AND table_name = '{staging_table}';
        """)).fetchall()
        
        target_cols = {row[0] for row in conn.execute(text(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = '{SCHEMA}' AND table_name = '{target_table}';
        """)).fetchall()}
        
        for col_name, data_type in staging_cols:
            if col_name not in target_cols:
                conn.execute(text(f'ALTER TABLE {SCHEMA}.{target_table} ADD COLUMN "{col_name}" {data_type};'))

        # 3. Robustly ensure the Primary Key constraint exists
        if pks:
            pk_str = ", ".join([f'"{pk}"' for pk in pks])
            
            has_pk = conn.execute(text("""
                SELECT 1
                FROM pg_constraint
                JOIN pg_class ON pg_constraint.conrelid = pg_class.oid
                JOIN pg_namespace ON pg_class.relnamespace = pg_namespace.oid
                WHERE pg_namespace.nspname = :schema
                  AND pg_class.relname = :table
                  AND pg_constraint.contype = 'p';
            """), {"schema": SCHEMA, "table": target_table}).scalar()
            
            if not has_pk:
                try:
                    conn.execute(text(f'ALTER TABLE {SCHEMA}.{target_table} ADD PRIMARY KEY ({pk_str});'))
                except Exception as e:
                    print(f"Warning: Could not add PRIMARY KEY to {SCHEMA}.{target_table}. Details: {e}")
        
        # 4. Perform the Upsert
        updates = ", ".join([f'"{col}" = EXCLUDED."{col}"' for col in columns if col not in pks])
        do_update = f"DO UPDATE SET {updates}" if updates else "DO NOTHING"
        
        if pks:
            pk_str = ", ".join([f'"{pk}"' for pk in pks])
            upsert_query = f"""
                INSERT INTO {SCHEMA}.{target_table} ({col_names})
                SELECT {col_names} FROM {SCHEMA}.{staging_table}
                ON CONFLICT ({pk_str}) {do_update};
            """
            conn.execute(text(upsert_query))
        else:
            append_query = f"""
                INSERT INTO {SCHEMA}.{target_table} ({col_names})
                SELECT {col_names} FROM {SCHEMA}.{staging_table};
            """
            conn.execute(text(append_query))
            
        # 5. Clean up staging
        conn.execute(text(f"DROP TABLE {SCHEMA}.{staging_table};"))

def process_file(file_path: Path, duck_con, engine):
    # Parse file date from filename if applicable (e.g., buildings_22082026.json)
    raw_stem = file_path.stem.split("?")[0]
    parts = raw_stem.rsplit("_", 1)
    
    file_date_str = None
    if len(parts) > 1 and re.match(r"^\d{8}$", parts[1]):
        date_str = parts[1]
        try:
            file_date_str = f"{date_str[4:8]}-{date_str[2:4]}-{date_str[0:2]}"
        except ValueError:
            pass
    if not file_date_str:
        file_date_str = datetime.date.today().isoformat()

    # 1. Parse JSON safely using Python json.load
    with open(file_path, "r", encoding="utf-8") as f:
        data_payload = json.load(f)

    building_id = data_payload.get("BuildingId")
    if not building_id:
        print(f'-> Missing "BuildingId" in JSON payload for file {file_path.name}. Skipping.')
        return

    buildings_data = [{
        "id": building_id,
        "ticker": data_payload.get("Ticker"),
        "name": data_payload.get("Name"),
        "area_cost": data_payload.get("AreaCost"),
        "user_name_submitted": data_payload.get("UserNameSubmitted"),
        "file_date": file_date_str,
    }]

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

    # 2. Convert to Pandas DataFrames and deduplicate
    df_buildings = pd.DataFrame(buildings_data).drop_duplicates(subset=["id"], keep="last")
    df_costs = pd.DataFrame(building_costs_data)
    if not df_costs.empty:
        df_costs = df_costs.drop_duplicates(subset=["building_id", "commodity_ticker"], keep="last")

    # 3. Push to Postgres via DuckDB Staging Tables following the {prefix}_raw pattern
    duck_con.execute(f"DROP TABLE IF EXISTS pg.{SCHEMA}.buildings_raw_staging")
    duck_con.execute("""
        CREATE TABLE pg.raw.buildings_raw_staging AS 
        SELECT * FROM df_buildings;
    """)

    buildings_cols = ["id", "ticker", "name", "area_cost", "user_name_submitted", "file_date"]
    perform_upsert(engine, "buildings_raw", "buildings_raw_staging", PRIMARY_KEY_MAP["buildings"], buildings_cols)

    if not df_costs.empty:
        duck_con.execute(f"DROP TABLE IF EXISTS pg.{SCHEMA}.building_costs_raw_staging")
        duck_con.execute("""
            CREATE TABLE pg.raw.building_costs_raw_staging AS 
            SELECT * FROM df_costs;
        """)
        costs_cols = ["building_id", "commodity_name", "commodity_ticker", "weight", "volume", "amount"]
        perform_upsert(engine, "building_costs_raw", "building_costs_raw_staging", PRIMARY_KEY_MAP["building_costs"], costs_cols)

def main():
    start_time = time.perf_counter()

    if not INPUT_DIR.exists():
        print(f"Input directory does not exist: {INPUT_DIR}")
        return

    target_files = [f for f in INPUT_DIR.iterdir() if f.is_file() and f.name.endswith(".json") and "AI1" not in f.name]

    if len(target_files) == 0:
        print('No eligible files (without "AI1") found in the directory.')
        return

    engine = create_engine(DB_URL)
    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA};"))

    duck_con = duckdb.connect()
    duck_con.execute("INSTALL postgres; LOAD postgres;")
    duck_con.execute(f"ATTACH '{DB_URL}' AS pg (TYPE postgres);")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    run_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_tar_name = f"processed_batch_buildings_{run_timestamp}.tar.gz"
    batch_tar_path = PROCESSED_DIR / batch_tar_name

    processed_count = 0
    with tarfile.open(batch_tar_path, "w:gz") as tar:
        for file_path in target_files:
            print(f"Processing {file_path.name}...")
            try:
                process_file(file_path, duck_con, engine)
                tar.add(file_path, arcname=file_path.name)
                file_path.unlink()
                processed_count += 1
                print(f"-> Successfully processed and archived: {file_path.name}")
            except Exception as e:
                print(f"-> Failed to process {file_path.name}: {e}")

    duck_con.close()

    if processed_count == 0:
        batch_tar_path.unlink(missing_ok=True)
        print("No building files were processed successfully.")
    else:
        print(f"\nSUCCESS: Successfully processed and bundled {processed_count} JSON file(s) into {batch_tar_name}.")

    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(f"\nPipeline finished in {elapsed_time:.4f} seconds.")

if __name__ == "__main__":
    main()
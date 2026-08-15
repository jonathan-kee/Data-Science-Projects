import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from dagster import asset, AssetExecutionContext, PipesSubprocessClient, DailyPartitionsDefinition
from dagster_dbt import dbt_assets, DbtCliResource, DbtProject

# Base directory setup
WORKING_DIR = Path("/Users/jonathankee/Data-Science-Projects")
DBT_PROJECT_DIR = WORKING_DIR / "dbtproject"
PROFILES_DIR = Path.home() / ".dbt"

# ------------------------------------------------------------------
# dbt Configuration & Project Initialization
# ------------------------------------------------------------------
dbt_project = DbtProject(
    project_dir=DBT_PROJECT_DIR,
    profiles_dir=PROFILES_DIR,
)

dbt_project.prepare_if_dev()

# 1. Define Daily Partitions (Includes today's ongoing date)
daily_partitions_def = DailyPartitionsDefinition(
    start_date="2026-01-01", 
    end_offset=1  
)

@dbt_assets(
    manifest=dbt_project.manifest_path, 
    partitions_def=daily_partitions_def
)
def dbtproject_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    """Generates partitioned dbt assets with a built-in date picker."""
    target_date = context.partition_key
    context.log.info(f"Running dbt with date_part: {target_date}")
    
    dbt_args = [
        "run",
        "--vars",
        json.dumps({"date_part": target_date})
    ]
    yield from dbt.cli(dbt_args, context=context).stream()


# ------------------------------------------------------------------
# Ingestion Setup 
# ------------------------------------------------------------------
SMELTOR_TICKERS = [
    "AL.AI1", "AU.AI1", "CF.AI1", "CU.AI1", "FE.AI1", 
    "LI.AI1", "S.AI1", "STL.AI1", "TI.AI1", "SI.AI1", "RE.AI1"
]

METALIST_TICKERS = [
    "SEQ.AI1", "BGO.AI1", "MFK.AI1", "BRO.AI1", "BFR.AI1", "RGO.AI1", 
    "UTS.AI1", "BCO.AI1", "AFR.AI1", "SFK.AI1", "HCC.AI1", "BGC.AI1", "FLO.AI1"
]

OTHER_TICKERS = ["ALO.AI1"]
ALL_TICKERS = SMELTOR_TICKERS + METALIST_TICKERS + OTHER_TICKERS

def create_ticker_asset(ticker: str):
    sanitized_name = ticker.replace(".", "_")
    asset_name = f"ticker_{sanitized_name}"

    # 2. Add partitions_def so this asset aligns with the calendar UI
    @asset(name=asset_name, group_name="exchange_ingestion", partitions_def=daily_partitions_def)
    def _asset(context: AssetExecutionContext, pipes_subprocess_client: PipesSubprocessClient):

        today = datetime.now().strftime("%d%m%Y")

        bash_script = f"""
        set -e
        tsc && node ./build/ingestion/json/cxpc.js "https://rest.fnar.net/exchange/cxpc/{ticker}"
        docker exec -i -e PGPASSWORD=abc123 postgres-container psql \\
            --dbname=prosperous_universe --username=postgres \\
            < ingestion/sql/cxpc_{sanitized_name}_{today}.sql
        """

        return pipes_subprocess_client.run(
            command=["bash", "-c", bash_script],
            context=context,
            cwd=str(WORKING_DIR),
        ).get_results()

    return _asset


ticker_assets = [create_ticker_asset(t) for t in ALL_TICKERS]


# Add partitions_def to all remaining assets
@asset(group_name="building_ingestion", partitions_def=daily_partitions_def)
def building_costs_hb2(context: AssetExecutionContext, pipes_subprocess_client: PipesSubprocessClient):
    bash_script = 'tsc && node ./build/ingestion/json/building.js "https://rest.fnar.net/building/HB2"'
    return pipes_subprocess_client.run(command=["bash", "-c", bash_script], context=context, cwd=str(WORKING_DIR)).get_results()


@asset(group_name="building_ingestion", partitions_def=daily_partitions_def)
def building_costs_fs(context: AssetExecutionContext, pipes_subprocess_client: PipesSubprocessClient):
    bash_script = 'tsc && node ./build/ingestion/json/building.js "https://rest.fnar.net/building/FS"'
    return pipes_subprocess_client.run(command=["bash", "-c", bash_script], context=context, cwd=str(WORKING_DIR)).get_results()


@asset(group_name="csv_ingestion", partitions_def=daily_partitions_def)
def prices_csv(context: AssetExecutionContext, pipes_subprocess_client: PipesSubprocessClient):
    bash_script = 'python ingestion/csv/ingest.py "https://rest.fnar.net/csv/prices"'
    return pipes_subprocess_client.run(command=["bash", "-c", bash_script], context=context, cwd=str(WORKING_DIR)).get_results()


@asset(group_name="csv_ingestion", partitions_def=daily_partitions_def)
def inventory_csv(context: AssetExecutionContext, pipes_subprocess_client: PipesSubprocessClient):
    url = "https://rest.fnar.net/csv/inventory?apikey=0f11ac24-ef14-428f-8213-4438576837f4&username=jonathan_kee"
    bash_script = f'python ingestion/csv/ingest.py "{url}"'
    return pipes_subprocess_client.run(command=["bash", "-c", bash_script], context=context, cwd=str(WORKING_DIR)).get_results()


# Combine all asset objects including dbt into a single exported list
all_pipeline_assets: List = [
    *ticker_assets,
    building_costs_hb2,
    building_costs_fs,
    prices_csv,
    inventory_csv,
    dbtproject_dbt_assets,
]
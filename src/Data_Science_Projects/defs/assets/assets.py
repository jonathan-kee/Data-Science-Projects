import json
from datetime import datetime
from pathlib import Path
from typing import List
from dagster import (
    asset, 
    multi_asset, 
    AssetOut, 
    AssetKey, 
    AssetExecutionContext, 
    PipesSubprocessClient, 
    DailyPartitionsDefinition,
    Output
)
from dagster_dbt import (
    dbt_assets, 
    DbtCliResource, 
    DbtProject
)

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

# Define Daily Partitions (Includes today's ongoing date)
daily_partitions_def = DailyPartitionsDefinition(
    start_date="2026-01-01", 
    end_offset=1  
)

# ------------------------------------------------------------------
# Ingestion Setup & Ticker Definitions
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

@asset(group_name="kotlin_ingestion", partitions_def=daily_partitions_def)
def kotlin_cli_ingest(context: AssetExecutionContext, pipes_subprocess_client: PipesSubprocessClient):
    """Step 1: Runs the Kotlin CLI jar to fetch all exchange and building payloads."""
    urls = [f"https://rest.fnar.net/exchange/cxpc/{t}" for t in ALL_TICKERS] + [
        "https://rest.fnar.net/building/HB2",
        "https://rest.fnar.net/building/FS"
    ]
    url_args = " ".join([f'"{u}"' for u in urls])
    
    bash_script = f"""
    cd ingestion
    java -jar KotlinCLI-1.0-SNAPSHOT-all.jar {url_args}
    """
    
    return pipes_subprocess_client.run(
        command=["bash", "-c", bash_script],
        context=context,
        cwd=str(WORKING_DIR),
    ).get_results()


@asset(group_name="typescript_build", partitions_def=daily_partitions_def, deps=[kotlin_cli_ingest])
def typescript_build(context: AssetExecutionContext, pipes_subprocess_client: PipesSubprocessClient):
    """Step 2: Cleans and builds the TypeScript project after Kotlin ingestion."""
    bash_script = """
    set -e
    tsc --build --clean
    tsc --build
    """
    return pipes_subprocess_client.run(
        command=["bash", "-c", bash_script],
        context=context,
        cwd=str(WORKING_DIR),
    ).get_results()


# Step 3: Exchange Ingestion Multi-Asset matching dbt's source key format [source_name, table_name]
CXPC_TABLE_NAMES = [f"cxpc_{t.lower().replace('.', '_')}_raw" for t in ALL_TICKERS]

@multi_asset(
    outs={
        name: AssetOut(key=AssetKey(["prosperous_universe_sources", name]))
        for name in CXPC_TABLE_NAMES
    },
    group_name="exchange_ingestion",
    partitions_def=daily_partitions_def,
    deps=[typescript_build]
)
def cxpc_folder_ingest(context: AssetExecutionContext, pipes_subprocess_client: PipesSubprocessClient):
    """Processes folder-based exchange JSON files and executes SQL into PostgreSQL."""
    bash_script = "node ./build/ingestion/json/cxpcFolder.js"
    result = pipes_subprocess_client.run(
        command=["bash", "-c", bash_script],
        context=context,
        cwd=str(WORKING_DIR),
    ).get_results()
    
    # Format partition key (YYYY-MM-DD) into DDMMYYYY for SQL filenames
    dt = datetime.strptime(context.partition_key, "%Y-%m-%d")
    today_str = dt.strftime("%d%m%Y")
    
    output_to_ticker = {
        f"cxpc_{t.lower().replace('.', '_')}_raw": t.replace('.', '_')
        for t in ALL_TICKERS
    }
    
    for output_name in context.selected_output_names:
        ticker_token = output_to_ticker[output_name]
        sql_filename = f"ingestion/sql/cxpc_{ticker_token}_{today_str}.sql"
        
        sql_command = f"""
        docker exec -i -e PGPASSWORD=abc123 postgres-container psql --dbname=prosperous_universe --username=postgres < {sql_filename}
        """
        
        context.log.info(f"Executing SQL file for {output_name}: {sql_filename}")
        pipes_subprocess_client.run(
            command=["bash", "-c", sql_command.strip()],
            context=context,
            cwd=str(WORKING_DIR),
        )
        
        yield Output(result, output_name=output_name)


# Step 4: Building Ingestion Multi-Asset matching dbt source format, independent of exchange ingestion
BUILDING_TABLE_NAMES = ["recipe_inputs_raw", "recipe_inputs_time_raw"]

@multi_asset(
    outs={
        name: AssetOut(key=AssetKey(["prosperous_universe_sources", name]))
        for name in BUILDING_TABLE_NAMES
    },
    group_name="building_ingestion",
    partitions_def=daily_partitions_def,
    deps=[typescript_build]
)
def building_folder_ingest(context: AssetExecutionContext, pipes_subprocess_client: PipesSubprocessClient):
    """Processes folder-based building JSON files independently after typescript build."""
    bash_script = "node ./build/ingestion/json/buildingFolder.js"
    result = pipes_subprocess_client.run(
        command=["bash", "-c", bash_script],
        context=context,
        cwd=str(WORKING_DIR),
    ).get_results()
    
    for output_name in context.selected_output_names:
        yield Output(result, output_name=output_name)


@asset(group_name="csv_ingestion", partitions_def=daily_partitions_def)
def prices_csv(context: AssetExecutionContext, pipes_subprocess_client: PipesSubprocessClient):
    bash_script = 'python ingestion/csv/ingest.py "https://rest.fnar.net/csv/prices"'
    return pipes_subprocess_client.run(command=["bash", "-c", bash_script], context=context, cwd=str(WORKING_DIR)).get_results()


@asset(group_name="csv_ingestion", partitions_def=daily_partitions_def)
def inventory_csv(context: AssetExecutionContext, pipes_subprocess_client: PipesSubprocessClient):
    url = "https://rest.fnar.net/csv/inventory?apikey=0f11ac24-ef14-428f-8213-4438576837f4&username=jonathan_kee"
    bash_script = f'python ingestion/csv/ingest.py "{url}"'
    return pipes_subprocess_client.run(command=["bash", "-c", bash_script], context=context, cwd=str(WORKING_DIR)).get_results()


@asset(group_name="csv_ingestion", partitions_def=daily_partitions_def)
def workforce_csv(context: AssetExecutionContext, pipes_subprocess_client: PipesSubprocessClient):
    url = "https://rest.fnar.net/csv/workforce?apikey=0f11ac24-ef14-428f-8213-4438576837f4&username=jonathan_kee"
    bash_script = f'python ingestion/csv/ingest.py "{url}"'
    return pipes_subprocess_client.run(command=["bash", "-c", bash_script], context=context, cwd=str(WORKING_DIR)).get_results()


# ------------------------------------------------------------------
# Step 5: dbt Assets Integration (Downstream of ingestion sources)
# ------------------------------------------------------------------
@dbt_assets(
    manifest=dbt_project.manifest_path, 
    partitions_def=daily_partitions_def
)
def dbtproject_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    """Generates partitioned individual dbt model assets downstream of all ingestion sources."""
    target_date = context.partition_key
    context.log.info(f"Running dbt with date_part: {target_date}")
    
    dbt_args = [
        "run",
        "--vars",
        json.dumps({"date_part": target_date})
    ]
    yield from dbt.cli(dbt_args, context=context).stream()


# Combine all asset objects into a single exported list
all_pipeline_assets: List = [
    kotlin_cli_ingest,
    typescript_build,
    cxpc_folder_ingest,
    building_folder_ingest,
    prices_csv,
    inventory_csv,
    workforce_csv,
    dbtproject_dbt_assets,
]
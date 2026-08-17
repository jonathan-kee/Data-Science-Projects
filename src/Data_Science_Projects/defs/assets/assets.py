import json
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any

from dagster import (
    AssetExecutionContext,
    AssetKey,
    AssetOut,
    DailyPartitionsDefinition,
    Output,
    PipesExecutionResult,
    PipesSubprocessClient,
    asset,
    multi_asset,
)
from dagster_dbt import (
    DagsterDbtTranslator,
    DbtCliResource,
    DbtProject,
    dbt_assets,
)

# Base directory setup
WORKING_DIR: Path = Path("/Users/jonathankee/Data-Science-Projects")
DBT_PROJECT_DIR: Path = WORKING_DIR / "dbtproject"
PROFILES_DIR: Path = Path.home() / ".dbt"

# ------------------------------------------------------------------
# dbt Configuration & Project Initialization
# ------------------------------------------------------------------
dbt_project: DbtProject = DbtProject(
    project_dir=DBT_PROJECT_DIR,
    profiles_dir=PROFILES_DIR,
)

dbt_project.prepare_if_dev()

# Define Daily Partitions (Includes today's ongoing date)
daily_partitions_def: DailyPartitionsDefinition = DailyPartitionsDefinition(
    start_date="2026-01-01", 
    end_offset=1,
    timezone="Asia/Kuala_Lumpur",  # Replace with your local IANA timezone string
)

# ------------------------------------------------------------------
# Custom Translator to Disconnect dbt Assets from Upstream Ingestion
# ------------------------------------------------------------------
class CustomDagsterDbtTranslator(DagsterDbtTranslator):
    def get_group_name(self, dbt_resource_props: dict[str, Any]) -> str:
        return "DBT"

    def get_asset_key(self, dbt_resource_props: dict[str, Any]) -> AssetKey:
        # Renames dbt source keys so they no longer match the "prosperous_universe_sources" 
        # keys emitted by ingestion multi-assets, severing upstream dependency edges.
        if dbt_resource_props.get("resource_type") == "source":
            return AssetKey(["dbt_raw_sources", dbt_resource_props["name"]])
        
        return super().get_asset_key(dbt_resource_props)

# ------------------------------------------------------------------
# Helper Function for Multi-Asset Outputs
# ------------------------------------------------------------------
def build_asset_outs(table_names: list[str]) -> dict[str, AssetOut]:
    """Helper to build AssetOut mappings without dict comprehensions."""
    outs: dict[str, AssetOut] = {}
    for name in table_names:
        outs[name] = AssetOut(key=AssetKey(["prosperous_universe_sources", name]))
    return outs

# ------------------------------------------------------------------
# Ingestion Setup & Ticker Definitions
# ------------------------------------------------------------------
SMELTOR_TICKERS: list[str] = [
    "AL.AI1", "AU.AI1", "CF.AI1", "CU.AI1", "FE.AI1", 
    "LI.AI1", "S.AI1", "STL.AI1", "TI.AI1", "SI.AI1", "RE.AI1"
]

METALIST_TICKERS: list[str] = [
    "SEQ.AI1", "BGO.AI1", "MFK.AI1", "BRO.AI1", "BFR.AI1", "RGO.AI1", 
    "UTS.AI1", "BCO.AI1", "AFR.AI1", "SFK.AI1", "HCC.AI1", "BGC.AI1", "FLO.AI1"
]

OTHER_TICKERS: list[str] = ["ALO.AI1"]
ALL_TICKERS: list[str] = SMELTOR_TICKERS + METALIST_TICKERS + OTHER_TICKERS

@asset(group_name="kotlin_ingestion", partitions_def=daily_partitions_def)
def kotlin_cli_ingest(
    context: AssetExecutionContext, 
    pipes_subprocess_client: PipesSubprocessClient
) -> Any:
    """Step 1: Runs the Kotlin CLI jar to fetch all exchange, building, and CSV payloads."""
    urls: list[str] = []
    for t in ALL_TICKERS:
        urls.append(f"https://rest.fnar.net/exchange/cxpc/{t}")
    
    urls.extend([
        "https://rest.fnar.net/building/HB2",
        "https://rest.fnar.net/building/FS",
        "https://rest.fnar.net/csv/prices",
        "https://rest.fnar.net/csv/inventory?apikey=0f11ac24-ef14-428f-8213-4438576837f4&username=jonathan_kee",
        "https://rest.fnar.net/csv/recipeinputs",
        "https://rest.fnar.net/csv/workforce?apikey=0f11ac24-ef14-428f-8213-4438576837f4&username=jonathan_kee"
    ])
    
    quoted_urls: list[str] = []
    for u in urls:
        quoted_urls.append(f'"{u}"')
    url_args: str = " ".join(quoted_urls)
    
    bash_script: str = f"""
    cd ingestion
    java -jar KotlinCLI-1.0-SNAPSHOT-all.jar {url_args}
    """
    
    return pipes_subprocess_client.run(
        command=["bash", "-c", bash_script],
        context=context,
        cwd=str(WORKING_DIR),
    ).get_results()


# ------------------------------------------------------------------
# Step 2: Exchange Ingestion Multi-Asset
# ------------------------------------------------------------------
CXPC_TABLE_NAMES: list[str] = []
for t in ALL_TICKERS:
    CXPC_TABLE_NAMES.append(f"cxpc_{t.lower().replace('.', '_')}_raw")

@multi_asset(
    outs=build_asset_outs(CXPC_TABLE_NAMES),
    group_name="exchange_ingestion",
    partitions_def=daily_partitions_def,
    deps=[kotlin_cli_ingest]
)
def cxpc_folder_ingest(
    context: AssetExecutionContext, 
    pipes_subprocess_client: PipesSubprocessClient
) -> Iterator[Output]:
    """Processes folder-based exchange JSON files and executes SQL into PostgreSQL."""
    bash_script: str = "python ingestion/json/cxpcFolder.py"
    result = pipes_subprocess_client.run(
        command=["bash", "-c", bash_script],
        context=context,
        cwd=str(WORKING_DIR),
    ).get_results()
    
    dt: datetime = datetime.strptime(context.partition_key, "%Y-%m-%d")
    today_str: str = dt.strftime("%d%m%Y")
    
    output_to_ticker: dict[str, str] = {}
    for t in ALL_TICKERS:
        key: str = f"cxpc_{t.lower().replace('.', '_')}_raw"
        output_to_ticker[key] = t.replace('.', '_')
    
    for output_name in context.selected_output_names:
        ticker_token: str = output_to_ticker[output_name]
        sql_filename: str = f"ingestion/sql/cxpc_{ticker_token}_{today_str}.sql"
        
        sql_command: str = f"""
        docker exec -i -e PGPASSWORD=abc123 postgres-container psql --dbname=prosperous_universe --username=postgres < {sql_filename}
        """
        
        context.log.info(f"Executing SQL file for {output_name}: {sql_filename}")
        pipes_subprocess_client.run(
            command=["bash", "-c", sql_command.strip()],
            context=context,
            cwd=str(WORKING_DIR),
        )
        
        yield Output(result, output_name=output_name)


# ------------------------------------------------------------------
# Step 3: Building Ingestion Multi-Asset
# ------------------------------------------------------------------
BUILDING_TABLE_NAMES: list[str] = ["recipe_inputs_raw", "recipe_inputs_time_raw"]

@multi_asset(
    outs=build_asset_outs(BUILDING_TABLE_NAMES),
    group_name="building_ingestion",
    partitions_def=daily_partitions_def,
    deps=[kotlin_cli_ingest]
)
def building_folder_ingest(
    context: AssetExecutionContext, 
    pipes_subprocess_client: PipesSubprocessClient
) -> Iterator[Output]:
    """Processes folder-based building JSON files independently."""
    bash_script: str = "python ingestion/json/buildingFolder.py"
    result = pipes_subprocess_client.run(
        command=["bash", "-c", bash_script],
        context=context,
        cwd=str(WORKING_DIR),
    ).get_results()
    
    for output_name in context.selected_output_names:
        yield Output(result, output_name=output_name)


# ------------------------------------------------------------------
# Step 4: CSV Ingestion Multi-Asset (Direct Python PostgreSQL Load)
# ------------------------------------------------------------------
CSV_TABLE_NAMES: list[str] = ["prices_raw", "inventory_raw", "recipe_inputs_raw_csv", "workforce_raw"]

@multi_asset(
    outs=build_asset_outs(CSV_TABLE_NAMES),
    group_name="csv_ingestion",
    partitions_def=daily_partitions_def,
    deps=[kotlin_cli_ingest]
)
def csv_folder_ingest(
    context: AssetExecutionContext, 
    pipes_subprocess_client: PipesSubprocessClient
) -> Iterator[Output]:
    """Processes folder-based CSV files and loads them directly into PostgreSQL via Python."""
    bash_script: str = "python ingestion/csv/ingestFolder.py"
    result = pipes_subprocess_client.run(
        command=["bash", "-c", bash_script], 
        context=context, 
        cwd=str(WORKING_DIR)
    ).get_results()
    
    for output_name in context.selected_output_names:
        yield Output(result, output_name=output_name)


# ------------------------------------------------------------------
# Step 5: Standalone dbt Assets Integration
# ------------------------------------------------------------------
@dbt_assets(
    manifest=dbt_project.manifest_path, 
    partitions_def=daily_partitions_def,
    dagster_dbt_translator=CustomDagsterDbtTranslator()
)
def dbtproject_dbt_assets(
    context: AssetExecutionContext, 
    dbt: DbtCliResource
) -> Iterator[Any]:
    """Generates all dbt model assets as an independent pipeline graph."""
    target_date: str = context.partition_key
    context.log.info(f"Running dbt with date_part: {target_date}")
    
    dbt_args: list[str] = [
        "run",
        "--vars",
        json.dumps({"date_part": target_date})
    ]
    yield from dbt.cli(dbt_args, context=context).stream()


# Combine all asset objects into a single exported list
all_pipeline_assets: list[Any] = [
    kotlin_cli_ingest,
    cxpc_folder_ingest,
    building_folder_ingest,
    csv_folder_ingest,
    dbtproject_dbt_assets,
]
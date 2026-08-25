import functools
import inspect
import json
import logging
import socket
from collections.abc import Iterator
from datetime import datetime
from logging.handlers import SysLogHandler
from pathlib import Path
from typing import Any

from dagster import (
    AssetExecutionContext,
    AssetKey,
    AssetOut,
    BackfillPolicy,
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

# ------------------------------------------------------------------
# Direct SysLog Handler Setup (UDP Port 10514)
# ------------------------------------------------------------------
syslog_logger = logging.getLogger("dagster_syslog")
syslog_logger.setLevel(logging.INFO)

if not syslog_logger.handlers:
    handler = SysLogHandler(address=("127.0.0.1", 10514), socktype=socket.SOCK_DGRAM)
    handler.setFormatter(
        logging.Formatter("dagster[%(process)d]: %(levelname)s - %(message)s\n")
    )
    syslog_logger.addHandler(handler)

# ------------------------------------------------------------------
# Lineage-Safe Lifecycle Decorator
# ------------------------------------------------------------------
def log_rsyslog_lifecycle(fn):
    if inspect.isgeneratorfunction(fn):
        @functools.wraps(fn)
        def gen_wrapper(*args, **kwargs):
            context = kwargs.get("context")
            if not context:
                for arg in args:
                    if hasattr(arg, "run_id"):
                        context = arg
                        break

            run_id = context.run_id if context else "unknown_run"
            asset_name = fn.__name__

            syslog_logger.info(f"Asset STARTED | Asset: {asset_name} | Run ID: {run_id}")

            try:
                for item in fn(*args, **kwargs):
                    yield item
                syslog_logger.info(f"Asset SUCCESS | Asset: {asset_name} | Run ID: {run_id}")
            except Exception as e:
                syslog_logger.error(
                    f"Asset FAILURE | Asset: {asset_name} | Run ID: {run_id} | Error: {str(e)}"
                )
                raise
        return gen_wrapper
    else:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            context = kwargs.get("context")
            if not context:
                for arg in args:
                    if hasattr(arg, "run_id"):
                        context = arg
                        break

            run_id = context.run_id if context else "unknown_run"
            asset_name = fn.__name__

            syslog_logger.info(f"Asset STARTED | Asset: {asset_name} | Run ID: {run_id}")

            try:
                result = fn(*args, **kwargs)
                syslog_logger.info(f"Asset SUCCESS | Asset: {asset_name} | Run ID: {run_id}")
                return result
            except Exception as e:
                syslog_logger.error(
                    f"Asset FAILURE | Asset: {asset_name} | Run ID: {run_id} | Error: {str(e)}"
                )
                raise
        return wrapper

# ------------------------------------------------------------------
# Base Directories & Config
# ------------------------------------------------------------------
WORKING_DIR: Path = Path("/Users/jonathankee/Data-Science-Projects")
DBT_PROJECT_DIR: Path = WORKING_DIR / "dbtproject"
PROFILES_DIR: Path = Path.home() / ".dbt"

dbt_project: DbtProject = DbtProject(
    project_dir=DBT_PROJECT_DIR,
    profiles_dir=PROFILES_DIR,
)

daily_partitions_def: DailyPartitionsDefinition = DailyPartitionsDefinition(
    start_date="2026-01-01", 
    end_offset=1,
    timezone="Asia/Kuala_Lumpur",
)

# ------------------------------------------------------------------
# Custom Translator & Output Builder
# ------------------------------------------------------------------
class CustomDagsterDbtTranslator(DagsterDbtTranslator):
    def get_group_name(self, dbt_resource_props: dict[str, Any]) -> str:
        return "DBT"

    def get_asset_key(self, dbt_resource_props: dict[str, Any]) -> AssetKey:
        if dbt_resource_props.get("resource_type") == "source":
            return AssetKey(["dbt_raw_sources", dbt_resource_props["name"]])
        return super().get_asset_key(dbt_resource_props)

def build_asset_outs(table_names: list[str]) -> dict[str, AssetOut]:
    outs: dict[str, AssetOut] = {}
    for name in table_names:
        outs[name] = AssetOut(key=AssetKey(["prosperous_universe_sources", name]))
    return outs

# ------------------------------------------------------------------
# Tickers Configuration
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

# ------------------------------------------------------------------
# Pipeline Assets
# ------------------------------------------------------------------

@asset(group_name="kotlin_ingestion", partitions_def=daily_partitions_def)
@log_rsyslog_lifecycle
def kotlin_cli_ingest(
    context: AssetExecutionContext, 
    pipes_subprocess_client: PipesSubprocessClient
) -> Any:
    urls: list[str] = [f"https://rest.fnar.net/exchange/cxpc/{t}" for t in ALL_TICKERS]
    urls.extend([
        "https://rest.fnar.net/building/HB2",
        "https://rest.fnar.net/building/FS",
        "https://rest.fnar.net/csv/prices",
        "https://rest.fnar.net/csv/inventory?apikey=0f11ac24-ef14-428f-8213-4438576837f4&username=jonathan_kee",
        "https://rest.fnar.net/csv/recipeinputs",
        "https://rest.fnar.net/csv/workforce?apikey=0f11ac24-ef14-428f-8213-4438576837f4&username=jonathan_kee"
    ])
    
    quoted_urls: list[str] = [f'"{u}"' for u in urls]
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


CXPC_TABLE_NAMES: list[str] = [f"cxpc_{t.lower().replace('.', '_')}_raw" for t in ALL_TICKERS]

@multi_asset(
    outs=build_asset_outs(CXPC_TABLE_NAMES),
    group_name="exchange_ingestion",
    partitions_def=daily_partitions_def,
    deps=[kotlin_cli_ingest]
)
@log_rsyslog_lifecycle
def cxpc_folder_ingest(
    context: AssetExecutionContext, 
    pipes_subprocess_client: PipesSubprocessClient
) -> Iterator[Output]:
    bash_script: str = "python ingestion/json/cxpcFolderDuckModuleCompress.py"
    result = pipes_subprocess_client.run(
        command=["bash", "-c", bash_script],
        context=context,
        cwd=str(WORKING_DIR),
    ).get_results()
    
    for output_name in context.selected_output_names:
        syslog_logger.info(f"Materialized asset prosperous_universe_sources/{output_name}")
        yield Output(result, output_name=output_name)


BUILDING_TABLE_NAMES: list[str] = ["recipe_inputs_raw", "recipe_inputs_time_raw"]

@multi_asset(
    outs=build_asset_outs(BUILDING_TABLE_NAMES),
    group_name="building_ingestion",
    partitions_def=daily_partitions_def,
    deps=[kotlin_cli_ingest]
)
@log_rsyslog_lifecycle
def building_folder_ingest(
    context: AssetExecutionContext, 
    pipes_subprocess_client: PipesSubprocessClient
) -> Iterator[Output]:
    bash_script: str = "python ingestion/json/buildingFolderDuckModuleCompress.py"
    result = pipes_subprocess_client.run(
        command=["bash", "-c", bash_script],
        context=context,
        cwd=str(WORKING_DIR),
    ).get_results()
    
    for output_name in context.selected_output_names:
        syslog_logger.info(f"Materialized asset prosperous_universe_sources/{output_name}")
        yield Output(result, output_name=output_name)


CSV_TABLE_NAMES: list[str] = ["prices_raw", "inventory_raw", "recipe_inputs_raw_csv", "workforce_raw"]

@multi_asset(
    outs=build_asset_outs(CSV_TABLE_NAMES),
    group_name="csv_ingestion",
    partitions_def=daily_partitions_def,
    deps=[kotlin_cli_ingest]
)
@log_rsyslog_lifecycle
def csv_folder_ingest(
    context: AssetExecutionContext, 
    pipes_subprocess_client: PipesSubprocessClient
) -> Iterator[Output]:
    bash_script: str = "python ingestion/csv/ingestFolderDuckModuleCompress.py"
    result = pipes_subprocess_client.run(
        command=["bash", "-c", bash_script], 
        context=context, 
        cwd=str(WORKING_DIR)
    ).get_results()
    
    for output_name in context.selected_output_names:
        syslog_logger.info(f"Materialized asset prosperous_universe_sources/{output_name}")
        yield Output(result, output_name=output_name)


@dbt_assets(
    manifest=dbt_project.manifest_path, 
    partitions_def=daily_partitions_def,
    dagster_dbt_translator=CustomDagsterDbtTranslator(),
    backfill_policy=BackfillPolicy.multi_run(),
    pool="dbt_execution_pool"
)
@log_rsyslog_lifecycle
def dbtproject_dbt_assets(
    context: AssetExecutionContext, 
    dbt: DbtCliResource
) -> Iterator[Any]:
    if context.has_partition_key:
        start_date = end_date = date_part = context.partition_key
    else:
        partition_range = context.partition_key_range
        start_date, end_date = partition_range.start, partition_range.end
        date_part = start_date

    dbt_args: list[str] = [
        "run",
        "--vars",
        json.dumps({
            "production_amount": 6,
            "start_date": start_date,
            "end_date": end_date,
            "date_part": date_part
        })
    ]
    
    yield from dbt.cli(dbt_args, context=context).stream()


all_pipeline_assets: list[Any] = [
    kotlin_cli_ingest,
    cxpc_folder_ingest,
    building_folder_ingest,
    csv_folder_ingest,
    dbtproject_dbt_assets,
]
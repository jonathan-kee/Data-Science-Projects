from pathlib import Path
from dagster import Definitions, PipesSubprocessClient
from dagster_dbt import DbtCliResource

from Data_Science_Projects.defs.assets.assets import (
    all_pipeline_assets,
    DBT_PROJECT_DIR,
    PROFILES_DIR,
)

defs = Definitions(
    assets=all_pipeline_assets,
    resources={
        "dbt": DbtCliResource(
            project_dir=DBT_PROJECT_DIR,
            profiles_dir=PROFILES_DIR,
        ),
        "pipes_subprocess_client": PipesSubprocessClient(),
    },
)
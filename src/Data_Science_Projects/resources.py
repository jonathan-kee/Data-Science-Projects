import os
from pathlib import Path
from dagster import Definitions, definitions, PipesSubprocessClient
from dagster_dbt import DbtCliResource

WORKING_DIR = Path("/Users/jonathankee/Data-Science-Projects")
DBT_PROJECT_DIR = WORKING_DIR / "dbtproject"

@definitions
def resource_defs():
    return Definitions(
        resources={
            "dbt": DbtCliResource(project_dir=os.fspath(DBT_PROJECT_DIR)),
            "pipes_subprocess_client": PipesSubprocessClient(),
        }
    )
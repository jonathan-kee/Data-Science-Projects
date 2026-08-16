import json
import os
from pathlib import Path
import shutil
import dlt
from dlt.destinations import postgres


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
  target_files = [
      f
      for f in input_folder.iterdir()
      if f.is_file() and f.name.endswith(".json") and "AI1" not in f.name
  ]

  if not target_files:
    print('No eligible files (without "AI1") found in the directory.')
    return

  # Initialize dlt pipeline targeting PostgreSQL and schema 'raw'
  pipeline = dlt.pipeline(
      pipeline_name="building_ingestion",
      destination=postgres(
          credentials="postgresql://postgres:abc123@localhost:5432/prosperous_universe"
      ),
      dataset_name="raw",
  )

  # Use "replace" for the initial table creation. Change to "merge" on subsequent runs after tables exist.
  @dlt.resource(name="buildings", write_disposition="merge", primary_key="id")
  def building_resource():
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

      # Yield transformed payload data for dlt normalization
      yield {
          "id": building_id,
          "ticker": data_payload.get("Ticker"),
          "name": data_payload.get("Name"),
          "area_cost": data_payload.get("AreaCost"),
          "user_name_submitted": data_payload.get("UserNameSubmitted"),
          "building_costs": [
              {
                  "commodity_name": cost.get("CommodityName"),
                  "commodity_ticker": cost.get("CommodityTicker"),
                  "weight": cost.get("Weight"),
                  "volume": cost.get("Volume"),
                  "amount": cost.get("Amount"),
              }
              for cost in data_payload.get("BuildingCosts", [])
          ],
      }

  try:
    # Run pipeline execution once for all files
    load_info = pipeline.run(building_resource())
    print(
        "\nSUCCESS: Pipeline execution completed and tables created in schema"
        ' "raw".\n'
    )

    # Safe check for database results now that tables exist
    try:
      with pipeline.sql_client() as client:
        with client.execute_query(
            "SELECT id, name, ticker, area_cost, user_name_submitted FROM"
            " buildings"
        ) as cursor:
          if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            print('--- Queried Database Summary (from schema "raw") ---')
            for row in rows:
              print(dict(zip(columns, row)))
    except Exception as query_err:
      print(
          f"Note: Could not run summary print query automatically: {query_err}"
      )

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
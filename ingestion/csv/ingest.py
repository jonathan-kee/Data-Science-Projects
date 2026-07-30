import os
import datetime
import shutil
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine
import requests

def load_csv_to_postgres(path: Path, engine, target_dir: Path ) -> None:
    """
    Reads a CSV file, prepends a timestamp column, and writes the data 
    into a PostgreSQL table named after the CSV file prefix.
    """
    path_obj = Path(path)
    
    # Parse filename information
    filename = os.path.basename(path)  # 'prices_24072026.csv'
    name_without_ext = os.path.splitext(filename)[0]  # 'prices_24072026'
    prefix, date_str = name_without_ext.split("_")  # 'prices', '24072026'

    # Read data
    df = pd.read_csv(path, sep=',', header='infer')

    # Format date_str ('24072026') into 'DD/MM/YYYY'
    formatted_date = f"{date_str[:2]}/{date_str[2:4]}/{date_str[4:]}"
    
    # Get current time (HH:MM:SS)
    current_time = datetime.datetime.now().strftime("%H:%M:%S")
    
    # Combine formatted date with current time
    load_time_str = f"{formatted_date} {current_time}"
    
    df.insert(0, "load time", load_time_str)

    print(df)

    # Write to database
    target_schema = "raw"
    with engine.begin() as connection:
        df.to_sql(
            name=prefix + "_raw",          # Table name derived from filename prefix
            con=connection, 
            schema=target_schema, 
            if_exists="append", # Append is still good because I got load time column from Python
            index=False
        )

    print(f"Successfully written to {target_schema}.{prefix}!")

    # Move file after successful write
    if target_dir:
        target_dir = Path(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)  # Create destination folder if it doesn't exist
        
        destination = target_dir / filename
        shutil.move(str(path_obj), str(destination))
        print(f"Moved {filename} to {destination}")


def readFile(fileName:str):
    folder = Path("/Users/jonathankee/Data-Science-Projects/ingestion/sources_unprocessed")
    archive_folder =  Path("/Users/jonathankee/Data-Science-Projects/ingestion/sources_processed")  # Destination directory

    # Find all CSV files starting with fileName inside the directory
    price_paths = [str(p) for p in folder.glob(fileName+"*.csv")]

    print(price_paths)

    db_engine = create_engine("postgresql+psycopg2://postgres:abc123@localhost/prosperous_universe", echo=True)

    for path in price_paths:
        print(f"Processing path: {path}")
        load_csv_to_postgres(path, db_engine, target_dir=archive_folder)

def downloadFile(url_string:str):
    # Extract base name ("prices") and format today's date ("30072026")
    base_name = Path(url_string).name
    date_str = datetime.datetime.now().strftime("%d%m%Y")
    filename = f"{base_name}_{date_str}.csv"  # -> "prices_30072026.csv"

    # Target directory
    folder = Path(
        "/Users/jonathankee/Data-Science-Projects/ingestion/sources_unprocessed"
    )
    folder.mkdir(parents=True, exist_ok=True)

    file_path = folder / filename

    try:
        response = requests.get(
            url_string,
            headers={"accept": "text/csv, application/csv"},
            timeout=15,  # 5 seconds
        )
        response.raise_for_status()

        # Write CSV text to file
        file_path.write_text(response.text, encoding="utf-8")

        print(f"Successfully saved CSV to {file_path}")

    except requests.exceptions.RequestException as e:
        print(f"HTTP Request failed for {url_string}")
        raise

# Example usage:
if __name__ == "__main__":
    url_string = "https://rest.fnar.net/csv/prices"
    # Extract 'prices' from the URL end and attach extension
    filename = f"{Path(url_string).name}.csv"  # Gives "prices.csv"
    filenameWithoutExtension = f"{Path(url_string).name}" # # Gives "prices"
    downloadFile(url_string)
    readFile(filenameWithoutExtension)
    
import os
import datetime
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine

def load_csv_to_postgres(path: str, engine) -> None:
    """
    Reads a CSV file, prepends a timestamp column, and writes the data 
    into a PostgreSQL table named after the CSV file prefix.
    """
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
            if_exists="append",
            index=False
        )

    print(f"Successfully written to {target_schema}.{prefix}!")


# Example usage:
if __name__ == "__main__":
    folder = Path("/Users/jonathankee/Data-Science-Projects/csv")

    # Find all CSV files starting with "prices" inside the directory
    price_paths = [str(p) for p in folder.glob("prices*.csv")]

    print(price_paths)

    db_engine = create_engine("postgresql+psycopg2://postgres:abc123@localhost/prosperous_universe", echo=True)

    for path in price_paths:
        print(f"Processing path: {path}")
        load_csv_to_postgres(path, db_engine)
    
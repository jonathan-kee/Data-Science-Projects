import os
import datetime
import pandas as pd 
from sqlalchemy import create_engine

path = "/Users/jonathankee/Data-Science-Projects/csv/prices_24072026.csv"

filename = os.path.basename(path)  # 'prices_24072026.csv'
name_without_ext = os.path.splitext(filename)[0]  # 'prices_24072026'
prefix, date_str = name_without_ext.split("_")  # 'prices', '24072026'

df = pd.read_csv(path, sep=',', header='infer')

# 1. Format the current time (DD/MM/YYYY HH:MM:SS)
load_time_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

# 2. Insert at index position 0 (the front)
# df.insert(location, column_name, value)
df.insert(0, "load time", load_time_str)

print(df)

# Create sql alchemy engine object
engine = create_engine("postgresql+psycopg2://postgres:abc123@localhost/prosperous_universe", echo=True)

# Write to the 'raw' schema
with engine.begin() as connection:
    df.to_sql(
        name=prefix, # Name of table: prices
        con=connection, 
        schema="raw",         # <--- Specify your target schema here
        if_exists="replace", 
        index=False
    )

print("Successfully written to raw.testing!")
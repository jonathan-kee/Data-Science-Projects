import pandas as pd 
from sqlalchemy import create_engine

df = pd.read_csv("/Users/jonathankee/Data-Science-Projects/csv/prices_24072026.csv", sep=',', header='infer')

print(df)

# Create sql alchemy engine object
engine = create_engine("postgresql+psycopg2://postgres:abc123@localhost/prosperous_universe", echo=True)

# Write to the 'raw' schema
with engine.begin() as connection:
    df.to_sql(
        name="testing", 
        con=connection, 
        schema="raw",         # <--- Specify your target schema here
        if_exists="replace", 
        index=False
    )

print("Successfully written to raw.testing!")
# Download CSV from api /csv/prices
curl -s -X GET "https://api.fnar.net/csv/prices?include_header=true" -H "accept: text/csv" -o prices.csv

# Transfer csv over to postgres container
docker cp \
    ./csv/prices.csv \
    postgres-container:/tmp/prices.csvs

echo "Ingest finish"


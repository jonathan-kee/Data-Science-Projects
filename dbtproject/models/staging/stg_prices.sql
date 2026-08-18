SELECT
    "file_date" AS date_part,
    CAST(CAST("load_time" AS TIMESTAMP) AS TIME) AS time_part,
    *
FROM {{ source('prosperous_universe_sources', 'prices_raw') }}
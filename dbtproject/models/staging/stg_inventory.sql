SELECT
    CAST(CAST("load_time" AS TIMESTAMP) AS DATE) AS date_part,
    CAST(CAST("load_time" AS TIMESTAMP) AS TIME) AS time_part,
    *
FROM {{ source('prosperous_universe_sources', 'inventory_raw') }}
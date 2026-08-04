SELECT
    CAST(TO_TIMESTAMP("load time", 'DD/MM/YYYY HH24:MI:SS') AS DATE) AS date_part,
    CAST(TO_TIMESTAMP("load time", 'DD/MM/YYYY HH24:MI:SS') AS TIME) AS time_part,
    *
FROM {{ source('prosperous_universe_sources', 'inventory_raw') }}
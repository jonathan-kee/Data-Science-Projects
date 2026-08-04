WITH source_data AS (
    SELECT * 
    FROM {{ ref('stg_prices') }}
)

SELECT
    source_data.*
FROM source_data
WHERE "Ticker" IS NOT NULL
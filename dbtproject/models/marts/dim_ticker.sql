WITH source_data AS (
    SELECT DISTINCT
        "Ticker" AS "Ticker"
    FROM {{ ref('stg_prices') }}
    WHERE "Ticker" IS NOT NULL
)

SELECT
    -- Natural Primary Key for the Dimension
    "Ticker",
    
    -- Metadata / Placeholder attributes (e.g., sector, company_name)
    CURRENT_TIMESTAMP AS created_at

FROM source_data
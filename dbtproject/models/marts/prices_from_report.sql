SELECT
    raw.stg_prices.date_part,
    raw.stg_prices."Ticker",
    raw.stg_prices."AI1-AskPrice",
    CASE
        WHEN raw.recipe_report."input_materials_AI1_AskPrice_per_unit" IS NOT NULL
        THEN raw.recipe_report."input_materials_AI1_AskPrice_per_unit"
        ELSE raw.stg_prices."AI1-BidPrice"
    END AS "AI1-BidPrice"
FROM {{ ref("stg_prices") }}
LEFT JOIN raw.recipe_report
    ON raw.recipe_report."Output Material" = raw.stg_prices."Ticker"
WHERE raw.stg_prices.date_part = (
    SELECT MAX(raw.stg_prices.date_part)
    FROM raw.stg_prices
)
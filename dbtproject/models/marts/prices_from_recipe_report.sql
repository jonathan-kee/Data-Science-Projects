with
    all_tables as (
SELECT
    raw.stg_prices.date_part,
    raw.stg_prices."Ticker",
    raw.stg_prices."AI1-BidPrice",
    raw.stg_prices."AI1-AskPrice" as "Original AI1-AskPrice",
    raw.recipe_report."input_materials_AI1_AskPrice_per_unit" as "Changed AI1-AskPrice",
    CASE
        WHEN raw.recipe_report."input_materials_AI1_AskPrice_per_unit" IS NOT NULL
        THEN raw.recipe_report."input_materials_AI1_AskPrice_per_unit"
        ELSE raw.stg_prices."AI1-AskPrice"
    END AS "AI1-AskPrice"
FROM {{ ref("stg_prices") }}
LEFT JOIN raw.recipe_report
    ON raw.recipe_report."Output Material" = raw.stg_prices."Ticker"
WHERE raw.stg_prices.date_part = (
    SELECT MAX(raw.stg_prices.date_part)
    FROM raw.stg_prices
)
),
toFilter as (
    select *
    from all_tables 
    -- Did filter below to make sure there's only one row to not cause issue
    -- Not sure why TI has two 1887
    where "AI1-AskPrice" NOT IN (459.3333333333333, 761.3333333333334, 1887,1870, 4304.5)
) select * from toFilter
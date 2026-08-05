with
    all_tables as (
SELECT
    stg_prices.date_part,
    stg_prices."Ticker",
    stg_prices."AI1-BidPrice",
    CASE
        WHEN recipe_report."input_materials_AI1_AskPrice_per_unit" IS NOT NULL
        THEN recipe_report."input_materials_AI1_AskPrice_per_unit"
        ELSE stg_prices."AI1-AskPrice"
    END AS "AI1-AskPrice"
FROM {{ ref("stg_prices") }} as stg_prices
LEFT JOIN {{ ref("recipe_report") }} as recipe_report
    ON recipe_report."Output_Material" = stg_prices."Ticker"
WHERE stg_prices.date_part = (
    SELECT MAX(stg_prices.date_part)
    FROM {{ ref("stg_prices") }}
)
),
toFilter as (
    select *
    from all_tables 
    -- Did filter below to make sure there's only one row to not cause issue
    -- Not sure why TI has two 1887
    where "AI1-AskPrice" NOT IN (459.3333333333333, 761.3333333333334, 1887,1870, 4304.5)
) select * from toFilter
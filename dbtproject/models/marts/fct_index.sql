WITH pivoted_prices AS (
    -- Step 1: Pivot rows into Gold and Aluminium columns per timestamp
    SELECT
        date_part,
        MAX(CASE WHEN ticker = 'au' THEN "Open" END) AS gold_price,
        MAX(CASE WHEN ticker = 'al' THEN "Open" END) AS aluminium_price
    FROM {{ ref("fct_cxpc") }}
    WHERE ticker IN ('au', 'al') 
      AND "Interval" = 'DAY_ONE'
    GROUP BY date_part
    -- Filter out dates where either asset is missing to prevent NULL base prices
    HAVING MAX(CASE WHEN ticker = 'au' THEN "Open" END) IS NOT NULL
       AND MAX(CASE WHEN ticker = 'al' THEN "Open" END) IS NOT NULL
),
indexed_base AS (
    -- Step 2: Extract base prices dynamically from the first complete trading day
    SELECT
        date_part,
        gold_price,
        aluminium_price,
        FIRST_VALUE(gold_price) OVER (ORDER BY date_part ASC) AS base_gold,
        FIRST_VALUE(aluminium_price) OVER (ORDER BY date_part ASC) AS base_aluminium
    FROM pivoted_prices
)
-- Step 3: Compute the weighted index
SELECT
    date_part,
    gold_price,
    aluminium_price,
    ROUND(
        100.0 * (
            0.5 * (gold_price::NUMERIC / NULLIF(base_gold, 0)) +
            0.5 * (aluminium_price::NUMERIC / NULLIF(base_aluminium, 0))
        ), 2
    ) AS metals_index
FROM indexed_base
ORDER BY date_part ASC
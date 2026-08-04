-- Fixed dbt model
-- Original is still in Analysis.sql, search (The shorter the time span, the more urgent you want to sell) --
WITH base AS (
    SELECT 
        "date_part"::date AS date_part,
        "Low" AS low
    FROM {{ ref("stg_cxpc_al_ai1") }}
    WHERE "Interval" = 'DAY_ONE'
),

begining_month_minimum_low AS (
    SELECT 
        MIN(low) AS min_low,
        DATE_TRUNC('month', '2026-07-26'::date)::date AS start_date,
        '2026-07-26'::date AS end_date
    FROM base
    WHERE date_part BETWEEN DATE_TRUNC('month', '2026-07-26'::date)::date AND '2026-07-26'::date
),

three_month_minimum_low AS (
    SELECT 
        MIN(low) AS min_low,
        (DATE_TRUNC('month', '2026-07-26'::date) - INTERVAL '2 months')::date AS start_date,
        '2026-07-26'::date AS end_date
    FROM base
    WHERE date_part BETWEEN (DATE_TRUNC('month', '2026-07-26'::date) - INTERVAL '2 months')::date AND '2026-07-26'::date
),

six_month_minimum_low AS (
    SELECT 
        MIN(low) AS min_low,
        (DATE_TRUNC('month', '2026-07-26'::date) - INTERVAL '5 months')::date AS start_date,
        '2026-07-26'::date AS end_date
    FROM base
    WHERE date_part BETWEEN (DATE_TRUNC('month', '2026-07-26'::date) - INTERVAL '5 months')::date AND '2026-07-26'::date
),

nine_month_minimum_low AS (
    SELECT 
        MIN(low) AS min_low,
        (DATE_TRUNC('month', '2026-07-26'::date) - INTERVAL '8 months')::date AS start_date,
        '2026-07-26'::date AS end_date
    FROM base
    WHERE date_part BETWEEN (DATE_TRUNC('month', '2026-07-26'::date) - INTERVAL '8 months')::date AND '2026-07-26'::date
),

twelve_month_minimum_low AS (
    SELECT 
        MIN(low) AS min_low,
        (DATE_TRUNC('month', '2026-07-26'::date) - INTERVAL '11 months')::date AS start_date,
        '2026-07-26'::date AS end_date
    FROM base
    WHERE date_part BETWEEN (DATE_TRUNC('month', '2026-07-26'::date) - INTERVAL '11 months')::date AND '2026-07-26'::date
),

entire_period_minimum_low AS (
    SELECT 
        MIN(low) AS min_low,
        MIN(date_part) AS start_date,
        MAX(date_part) AS end_date
    FROM base
)

SELECT 'today period' AS period, low AS min_low, '2026-07-26'::date AS start_date, '2026-07-26'::date AS end_date
FROM base
WHERE date_part = '2026-07-26'::date

UNION ALL
SELECT '1st month period' AS period, min_low, start_date, end_date FROM begining_month_minimum_low
UNION ALL
SELECT '3rd month period' AS period, min_low, start_date, end_date FROM three_month_minimum_low
UNION ALL
SELECT '6th month period' AS period, min_low, start_date, end_date FROM six_month_minimum_low
UNION ALL
SELECT '9th month period' AS period, min_low, start_date, end_date FROM nine_month_minimum_low
UNION ALL
SELECT '12th month period' AS period, min_low, start_date, end_date FROM twelve_month_minimum_low
UNION ALL
SELECT 'entire period' AS period, min_low, start_date, end_date FROM entire_period_minimum_low
-- Fixed dbt model
-- Original is still in Analysis.sql, search (The shorter the time span, the more urgent you want to sell) --
WITH base AS (
    SELECT 
        "date_part"::date AS date_part,
        "High" AS high
    FROM {{ ref("stg_cxpc_al_ai1") }}
    WHERE "Interval" = 'DAY_ONE'
),

begining_month_maximum_high AS (
    SELECT 
        MAX(high) AS max_high,
        DATE_TRUNC('month', '2026-07-26'::date)::date AS start_date,
        '2026-07-26'::date AS end_date
    FROM base
    WHERE date_part BETWEEN DATE_TRUNC('month', '2026-07-26'::date)::date AND '2026-07-26'::date
),

three_month_maximum_high AS (
    SELECT 
        MAX(high) AS max_high,
        (DATE_TRUNC('month', '2026-07-26'::date) - INTERVAL '2 months')::date AS start_date,
        '2026-07-26'::date AS end_date
    FROM base
    WHERE date_part BETWEEN (DATE_TRUNC('month', '2026-07-26'::date) - INTERVAL '2 months')::date AND '2026-07-26'::date
),

six_month_maximum_high AS (
    SELECT 
        MAX(high) AS max_high,
        (DATE_TRUNC('month', '2026-07-26'::date) - INTERVAL '5 months')::date AS start_date,
        '2026-07-26'::date AS end_date
    FROM base
    WHERE date_part BETWEEN (DATE_TRUNC('month', '2026-07-26'::date) - INTERVAL '5 months')::date AND '2026-07-26'::date
),

nine_month_maximum_high AS (
    SELECT 
        MAX(high) AS max_high,
        (DATE_TRUNC('month', '2026-07-26'::date) - INTERVAL '8 months')::date AS start_date,
        '2026-07-26'::date AS end_date
    FROM base
    WHERE date_part BETWEEN (DATE_TRUNC('month', '2026-07-26'::date) - INTERVAL '8 months')::date AND '2026-07-26'::date
),

twelve_month_maximum_high AS (
    SELECT 
        MAX(high) AS max_high,
        (DATE_TRUNC('month', '2026-07-26'::date) - INTERVAL '11 months')::date AS start_date,
        '2026-07-26'::date AS end_date
    FROM base
    WHERE date_part BETWEEN (DATE_TRUNC('month', '2026-07-26'::date) - INTERVAL '11 months')::date AND '2026-07-26'::date
),

entire_period_maximum_high AS (
    SELECT 
        MAX(high) AS max_high,
        MIN(date_part) AS start_date,
        MAX(date_part) AS end_date
    FROM base
)

SELECT 'today period' AS period, high AS max_high, '2026-07-26'::date AS start_date, '2026-07-26'::date AS end_date
FROM base
WHERE date_part = '2026-07-26'::date

UNION ALL
SELECT '1st month period' AS period, max_high, start_date, end_date FROM begining_month_maximum_high
UNION ALL
SELECT '3rd month period' AS period, max_high, start_date, end_date FROM three_month_maximum_high
UNION ALL
SELECT '6th month period' AS period, max_high, start_date, end_date FROM six_month_maximum_high
UNION ALL
SELECT '9th month period' AS period, max_high, start_date, end_date FROM nine_month_maximum_high
UNION ALL
SELECT '12th month period' AS period, max_high, start_date, end_date FROM twelve_month_maximum_high
UNION ALL
SELECT 'entire period' AS period, max_high, start_date, end_date FROM entire_period_maximum_high
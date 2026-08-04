-- Fixed dbt model
-- Original is still in Analysis.sql, search (The shorter the time span, the more urgent you want to sell) --
WITH base AS (
    SELECT 
        "date_part"::date AS date_part,
        "High" AS high
    FROM {{ ref("stg_cxpc_al_ai1") }}
    WHERE "Interval" = 'DAY_ONE'
),
max_date AS (
    SELECT MAX("date_part"::date) as max_date_part
    from {{ ref("stg_cxpc_al_ai1") }}
),
begining_month_maximum_high AS (
    SELECT 
        MAX(high) AS max_high,
        DATE_TRUNC('month', MAX(max_date.max_date_part::date))::date AS start_date,
        MAX(max_date.max_date_part::date) AS end_date
    FROM base inner join max_date on 1=1
    WHERE date_part BETWEEN DATE_TRUNC('month', max_date.max_date_part::date)::date AND max_date.max_date_part::date
),

three_month_maximum_high AS (
    SELECT 
        MAX(high) AS max_high,
        (DATE_TRUNC('month', MAX(max_date.max_date_part::date)) - INTERVAL '2 months')::date AS start_date,
        MAX(max_date.max_date_part::date) AS end_date
    FROM base inner join max_date on 1=1
    WHERE date_part BETWEEN (DATE_TRUNC('month', max_date.max_date_part::date) - INTERVAL '2 months')::date AND max_date.max_date_part::date
),

six_month_maximum_high AS (
    SELECT 
        MAX(high) AS max_high,
        (DATE_TRUNC('month', MAX(max_date.max_date_part::date)) - INTERVAL '5 months')::date AS start_date,
        MAX(max_date.max_date_part::date) AS end_date
    FROM base inner join max_date on 1=1
    WHERE date_part BETWEEN (DATE_TRUNC('month', max_date.max_date_part::date) - INTERVAL '5 months')::date AND max_date.max_date_part::date
),

nine_month_maximum_high AS (
    SELECT 
        MAX(high) AS max_high,
        (DATE_TRUNC('month', MAX(max_date.max_date_part::date)) - INTERVAL '8 months')::date AS start_date,
        MAX(max_date.max_date_part::date) AS end_date
    FROM base inner join max_date on 1=1
    WHERE date_part BETWEEN (DATE_TRUNC('month', max_date.max_date_part::date) - INTERVAL '8 months')::date AND max_date.max_date_part::date
),

twelve_month_maximum_high AS (
    SELECT 
        MAX(high) AS max_high,
        (DATE_TRUNC('month', MAX(max_date.max_date_part::date)) - INTERVAL '11 months')::date AS start_date,
        MAX(max_date.max_date_part::date) AS end_date
    FROM base inner join max_date on 1=1
    WHERE date_part BETWEEN (DATE_TRUNC('month', max_date.max_date_part::date) - INTERVAL '11 months')::date AND max_date.max_date_part::date
),

entire_period_maximum_high AS (
    SELECT 
        MAX(high) AS max_high,
        MIN(date_part) AS start_date,
        MAX(date_part) AS end_date
    FROM base
),

OnlyOneRow as (
    SELECT 'today period' AS period, high AS max_high, max_date.max_date_part::date AS start_date, max_date.max_date_part::date AS end_date
    FROM base inner join max_date on 1=1
    WHERE date_part = max_date.max_date_part::date
)

SELECT period AS period, max_high AS max_high, start_date AS start_date, end_date AS end_date
FROM OnlyOneRow
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
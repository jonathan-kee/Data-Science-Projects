-- Fixed dbt model
-- Original is still in Analysis.sql, search (The shorter the time span, the more
-- urgent you want to sell) --
with
    base as (
        select "date_part"::date as date_part, "Low" as low
        from {{ ref("stg_cxpc_al_ai1") }}
        where "Interval" = 'DAY_ONE'
    ),

    begining_month_minimum_low as (
        select
            min(low) as min_low,
            date_trunc('month', '2026-07-26'::date)::date as start_date,
            '2026-07-26'::date as end_date
        from base
        where
            date_part
            between date_trunc('month', '2026-07-26'::date)::date and '2026-07-26'::date
    ),

    three_month_minimum_low as (
        select
            min(low) as min_low,
            (date_trunc('month', '2026-07-26'::date) - interval '2 months')::date
            as start_date,
            '2026-07-26'::date as end_date
        from base
        where
            date_part between (
                date_trunc('month', '2026-07-26'::date) - interval '2 months'
            )::date and '2026-07-26'::date
    ),

    six_month_minimum_low as (
        select
            min(low) as min_low,
            (date_trunc('month', '2026-07-26'::date) - interval '5 months')::date
            as start_date,
            '2026-07-26'::date as end_date
        from base
        where
            date_part between (
                date_trunc('month', '2026-07-26'::date) - interval '5 months'
            )::date and '2026-07-26'::date
    ),

    nine_month_minimum_low as (
        select
            min(low) as min_low,
            (date_trunc('month', '2026-07-26'::date) - interval '8 months')::date
            as start_date,
            '2026-07-26'::date as end_date
        from base
        where
            date_part between (
                date_trunc('month', '2026-07-26'::date) - interval '8 months'
            )::date and '2026-07-26'::date
    ),

    twelve_month_minimum_low as (
        select
            min(low) as min_low,
            (date_trunc('month', '2026-07-26'::date) - interval '11 months')::date
            as start_date,
            '2026-07-26'::date as end_date
        from base
        where
            date_part between (
                date_trunc('month', '2026-07-26'::date) - interval '11 months'
            )::date and '2026-07-26'::date
    ),

    entire_period_minimum_low as (
        select
            min(low) as min_low,
            min(date_part) as start_date,
            max(date_part) as end_date
        from base
    )

select
    'today period' as period,
    low as min_low,
    '2026-07-26'::date as start_date,
    '2026-07-26'::date as end_date
from base
where date_part = '2026-07-26'::date

union all
select '1st month period' as period, min_low, start_date, end_date
from begining_month_minimum_low
union all
select '3rd month period' as period, min_low, start_date, end_date
from three_month_minimum_low
union all
select '6th month period' as period, min_low, start_date, end_date
from six_month_minimum_low
union all
select '9th month period' as period, min_low, start_date, end_date
from nine_month_minimum_low
union all
select '12th month period' as period, min_low, start_date, end_date
from twelve_month_minimum_low
union all
select 'entire period' as period, min_low, start_date, end_date
from entire_period_minimum_low

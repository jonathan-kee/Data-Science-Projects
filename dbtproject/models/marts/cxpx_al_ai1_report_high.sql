-- Fixed dbt model
-- Original is still in Analysis.sql, search (The shorter the time span, the more
-- urgent you want to sell) --
with
    base as (
        select "date_part"::date as date_part, "high" as high
        from {{ ref("stg_cxpc_al_ai1") }}
        where "interval" = 'DAY_ONE'
    ),
    max_date as (
        select max("date_part"::date) as max_date_part from {{ ref("stg_cxpc_al_ai1") }}
    ),
    begining_month_maximum_high as (
        select
            max(high) as max_high,
            date_trunc('month', max(max_date.max_date_part::date))::date as start_date,
            max(max_date.max_date_part::date) as end_date
        from base
        inner join max_date on 1 = 1
        where
            date_part
            between date_trunc('month', max_date.max_date_part::date)::date
            and max_date.max_date_part::date
    ),

    three_month_maximum_high as (
        select
            max(high) as max_high,
            (
                date_trunc('month', max(max_date.max_date_part::date))
                - interval '2 months'
            )::date as start_date,
            max(max_date.max_date_part::date) as end_date
        from base
        inner join max_date on 1 = 1
        where
            date_part between (
                date_trunc('month', max_date.max_date_part::date) - interval '2 months'
            )::date and max_date.max_date_part::date
    ),

    six_month_maximum_high as (
        select
            max(high) as max_high,
            (
                date_trunc('month', max(max_date.max_date_part::date))
                - interval '5 months'
            )::date as start_date,
            max(max_date.max_date_part::date) as end_date
        from base
        inner join max_date on 1 = 1
        where
            date_part between (
                date_trunc('month', max_date.max_date_part::date) - interval '5 months'
            )::date and max_date.max_date_part::date
    ),

    nine_month_maximum_high as (
        select
            max(high) as max_high,
            (
                date_trunc('month', max(max_date.max_date_part::date))
                - interval '8 months'
            )::date as start_date,
            max(max_date.max_date_part::date) as end_date
        from base
        inner join max_date on 1 = 1
        where
            date_part between (
                date_trunc('month', max_date.max_date_part::date) - interval '8 months'
            )::date and max_date.max_date_part::date
    ),

    twelve_month_maximum_high as (
        select
            max(high) as max_high,
            (
                date_trunc('month', max(max_date.max_date_part::date))
                - interval '11 months'
            )::date as start_date,
            max(max_date.max_date_part::date) as end_date
        from base
        inner join max_date on 1 = 1
        where
            date_part between (
                date_trunc('month', max_date.max_date_part::date) - interval '11 months'
            )::date and max_date.max_date_part::date
    ),

    entire_period_maximum_high as (
        select
            max(high) as max_high,
            min(date_part) as start_date,
            max(date_part) as end_date
        from base
    ),

    onlyonerow as (
        select
            'today period' as period,
            high as max_high,
            max_date.max_date_part::date as start_date,
            max_date.max_date_part::date as end_date
        from base
        inner join max_date on 1 = 1
        where date_part = max_date.max_date_part::date
    )

select
    period as period,
    max_high as max_high,
    start_date as start_date,
    end_date as end_date
from onlyonerow
union all
select '1st month period' as period, max_high, start_date, end_date
from begining_month_maximum_high
union all
select '3rd month period' as period, max_high, start_date, end_date
from three_month_maximum_high
union all
select '6th month period' as period, max_high, start_date, end_date
from six_month_maximum_high
union all
select '9th month period' as period, max_high, start_date, end_date
from nine_month_maximum_high
union all
select '12th month period' as period, max_high, start_date, end_date
from twelve_month_maximum_high
union all
select 'entire period' as period, max_high, start_date, end_date
from entire_period_maximum_high

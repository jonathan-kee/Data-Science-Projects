-- Get Single --
with aggregates as (
    select
        Sum(raw.dim_report.material_input_total_cost) as "material_input_total_cost",
        max(raw.dim_report.material_output_total_sell_price) as "material_output_total_sell_price",
        max(raw.dim_report.total_order_per_day) as "total_order_per_day"
    from raw.dim_report
    where materialoutput = 'AL' and materialoutputquantity = 4
    -- and materialinput <> 'ALO' -- Comment Out to remove ALO because base already produce ALO
),
RoiPerDay as (
    select
        (aggregates."material_output_total_sell_price" - aggregates."material_input_total_cost") * aggregates."total_order_per_day" as RoiPerDay
    from aggregates
)
select * from RoiPerDay


-- Group By Aggregate --
-- If I group by common data like prefix and materialoutputquantity, materialoutput, I can squish the data
-- I get a single row
with aggregates as (select prefix,
                           materialoutputquantity,
                           materialoutput,
                           Sum(raw.dim_report.material_input_total_cost)        as "material_input_total_cost",
                           max(raw.dim_report.material_output_total_sell_price) as "material_output_total_sell_price",
                           max(raw.dim_report.total_order_per_day)              as "total_order_per_day"
                    from raw.dim_report
                    group by prefix, materialoutputquantity, materialoutput),
RoiPerDay as (
    select
        prefix,
        materialoutputquantity,
        materialoutput,
        (aggregates."material_output_total_sell_price" - aggregates."material_input_total_cost") * aggregates."total_order_per_day" as RoiPerDay
    from aggregates
)
select * from RoiPerDay

-- 'AL' is ticker for aluminium
-- Ask Price is seller, You buy from them
-- Bid Price is buyer, You sell to them
select "AI1-AskPrice" , "AI1-BidPrice"
from raw.stg_market_depth
where "Ticker" = 'AL'

-- Group By Aggregate for SME (Smelter) --
-- PrunPlanner  4xAL    6568.92
-- Mine         4xAL    6115.54
-- If I group by common data like prefix and materialoutputquantity, materialoutput, I can squish the data
with aggregates as (select prefix,
                           materialoutputquantity,
                           materialoutput,
                           Sum(raw.dim_report.material_input_total_cost)        as "material_input_total_cost",
                           max(raw.dim_report.material_output_total_sell_price) as "material_output_total_sell_price",
                           max(raw.dim_report.total_order_per_day)              as "total_order_per_day"
                    from raw.dim_report
                    where prefix = 'SME'
                    and materialinput <> 'ALO'
                    group by prefix, materialoutputquantity, materialoutput),
RoiPerDay as (
    select
        prefix,
        materialoutputquantity,
        materialoutput,
        (aggregates."material_output_total_sell_price" - aggregates."material_input_total_cost") * aggregates."total_order_per_day" as RoiPerDay
    from aggregates
)
select * from RoiPerDay order by RoiPerDay desc


-- (Need to convert to date for more accurate comparison)
-- The longer the time span, the less urgent you want to sell --
WITH entire_period as (
    select raw.stg_cxpc_al_ai1."date_part" ,raw.stg_cxpc_al_ai1."High"
    from raw.stg_cxpc_al_ai1
    WHERE "Interval" = 'DAY_ONE' and
    "date_part" between (
        select min("date_part") as "start_date"
                   from raw.stg_cxpc_al_ai1
                   WHERE "Interval" = 'DAY_ONE'
        ) and (
            select max("date_part") as "end_date"
                   from raw.stg_cxpc_al_ai1
                   WHERE "Interval" = 'DAY_ONE'
        )
    order by 1 desc
),
maximum_high as (
    select max("High"),
           (select min("date_part") as "start_date"
                   from raw.stg_cxpc_al_ai1
                   WHERE "Interval" = 'DAY_ONE') as "start_date",
    (select max("date_part") as "end_date"
                   from raw.stg_cxpc_al_ai1
                   WHERE "Interval" = 'DAY_ONE') as "end_date"
    from entire_period
    )
select * from maximum_high;

-- The shorter the time span, the more urgent you want to sell --
WITH begining_month as (
    select raw.stg_cxpc_al_ai1."date_part"::date ,raw.stg_cxpc_al_ai1."High"
    from raw.stg_cxpc_al_ai1
    WHERE "Interval" = 'DAY_ONE' and
    "date_part"::date between date_trunc('month', '2026-07-26'::date)::date and '2026-07-26'::date
    order by 1 desc
),
maximum_high as (
    select max("High"),
        date_trunc('month', '2026-07-26'::date)::date as "start_date",
        '2026-07-26'::date as "end_date"
    from begining_month
    )
select * from maximum_high;

WITH three_month as (
    select raw.stg_cxpc_al_ai1."date_part"::date ,raw.stg_cxpc_al_ai1."High"
    from raw.stg_cxpc_al_ai1
    WHERE "Interval" = 'DAY_ONE' and
    "date_part"::date between (date_trunc('month', '2026-07-26'::date) - INTERVAL '2 months')::date and '2026-07-26'::date
    order by 1 desc
),
maximum_high as (
    select max("High"),
        (date_trunc('month', '2026-07-26'::date) - INTERVAL '2 months')::date as "start_date",
        '2026-07-26'::date as "end_date"
    from three_month
    )
select * from maximum_high;

WITH six_month as (
    select raw.stg_cxpc_al_ai1."date_part"::date ,raw.stg_cxpc_al_ai1."High"
    from raw.stg_cxpc_al_ai1
    WHERE "Interval" = 'DAY_ONE' and
    "date_part"::date between (date_trunc('month', '2026-07-26'::date) - INTERVAL '5 months')::date and '2026-07-26'::date
    order by 1 desc
),
maximum_high as (
    select max("High"),
        (date_trunc('month', '2026-07-26'::date) - INTERVAL '5 months')::date as "start_date",
        '2026-07-26'::date as "end_date"
    from six_month
    )
select * from maximum_high;

WITH nine_month as (
    select raw.stg_cxpc_al_ai1."date_part"::date ,raw.stg_cxpc_al_ai1."High"
    from raw.stg_cxpc_al_ai1
    WHERE "Interval" = 'DAY_ONE' and
    "date_part"::date between (date_trunc('month', '2026-07-26'::date) - INTERVAL '8 months')::date and '2026-07-26'::date
    order by 1 desc
),
maximum_high as (
    select max("High"),
        (date_trunc('month', '2026-07-26'::date) - INTERVAL '8 months')::date as "start_date",
        '2026-07-26'::date as "end_date"
    from nine_month
    )
select * from maximum_high;

WITH twelve_month as (
    select raw.stg_cxpc_al_ai1."date_part"::date ,raw.stg_cxpc_al_ai1."High"
    from raw.stg_cxpc_al_ai1
    WHERE "Interval" = 'DAY_ONE' and
    "date_part"::date between (date_trunc('month', '2026-07-26'::date) - INTERVAL '11 months')::date and '2026-07-26'::date
    order by 1 desc
),
maximum_high as (
    select max("High"),
        (date_trunc('month', '2026-07-26'::date) - INTERVAL '11 months')::date as "start_date",
        '2026-07-26'::date as "end_date"
    from twelve_month
    )
select * from maximum_high;

-- The shorter the time span, the more urgent you want to sell --
WITH begining_month as (select raw.stg_cxpc_al_ai1."date_part"::date, raw.stg_cxpc_al_ai1."High"
                        from raw.stg_cxpc_al_ai1
                        WHERE "Interval" = 'DAY_ONE'
                          and "date_part"::date between date_trunc('month', '2026-07-26'::date)::date and '2026-07-26'::date
                        order by 1 desc),
     begining_month_maximum_high as (select max("High"),
                             date_trunc('month', '2026-07-26'::date)::date as "start_date",
                             '2026-07-26'::date                            as "end_date"
                      from begining_month)
,
three_month as (select raw.stg_cxpc_al_ai1."date_part"::date, raw.stg_cxpc_al_ai1."High"
                     from raw.stg_cxpc_al_ai1
                     WHERE "Interval" = 'DAY_ONE'
                       and "date_part"::date between (date_trunc('month', '2026-07-26'::date) - INTERVAL '2 months')::date and '2026-07-26'::date
                     order by 1 desc),
     three_month_maximum_high as (select max("High"),
                             (date_trunc('month', '2026-07-26'::date) - INTERVAL '2 months')::date as "start_date",
                             '2026-07-26'::date                                                    as "end_date"
                      from three_month)
,
six_month as (select raw.stg_cxpc_al_ai1."date_part"::date, raw.stg_cxpc_al_ai1."High"
                   from raw.stg_cxpc_al_ai1
                   WHERE "Interval" = 'DAY_ONE'
                     and "date_part"::date between (date_trunc('month', '2026-07-26'::date) - INTERVAL '5 months')::date and '2026-07-26'::date
                   order by 1 desc),
     six_month_maximum_high as (select max("High"),
                             (date_trunc('month', '2026-07-26'::date) - INTERVAL '5 months')::date as "start_date",
                             '2026-07-26'::date                                                    as "end_date"
                      from six_month)
,
nine_month as (select raw.stg_cxpc_al_ai1."date_part"::date, raw.stg_cxpc_al_ai1."High"
                    from raw.stg_cxpc_al_ai1
                    WHERE "Interval" = 'DAY_ONE'
                      and "date_part"::date between (date_trunc('month', '2026-07-26'::date) - INTERVAL '8 months')::date and '2026-07-26'::date
                    order by 1 desc),
     nine_month_maximum_high as (select max("High"),
                             (date_trunc('month', '2026-07-26'::date) - INTERVAL '8 months')::date as "start_date",
                             '2026-07-26'::date                                                    as "end_date"
                      from nine_month)
,
twelve_month as (select raw.stg_cxpc_al_ai1."date_part"::date, raw.stg_cxpc_al_ai1."High"
                      from raw.stg_cxpc_al_ai1
                      WHERE "Interval" = 'DAY_ONE'
                        and "date_part"::date between (date_trunc('month', '2026-07-26'::date) - INTERVAL '11 months')::date and '2026-07-26'::date
                      order by 1 desc),
     twelve_month_maximum_high as (select max("High"),
                             (date_trunc('month', '2026-07-26'::date) - INTERVAL '11 months')::date as "start_date",
                             '2026-07-26'::date                                                     as "end_date"
                      from twelve_month)

-- (Need to convert to date for more accurate comparison)
-- The longer the time span, the less urgent you want to sell --
,
entire_period as (select raw.stg_cxpc_al_ai1."date_part", raw.stg_cxpc_al_ai1."High"
                       from raw.stg_cxpc_al_ai1
                       WHERE "Interval" = 'DAY_ONE'
                         and "date_part"::date between (select min("date_part")::date as "start_date"
                                                        from raw.stg_cxpc_al_ai1
                                                        WHERE "Interval" = 'DAY_ONE') and (select max("date_part")::date as "end_date"
                                                                                           from raw.stg_cxpc_al_ai1
                                                                                           WHERE "Interval" = 'DAY_ONE')
                       order by 1 desc),
     entire_period_maximum_high as (select max("High"),
                             (select min("date_part")::date as "start_date"
                              from raw.stg_cxpc_al_ai1
                              WHERE "Interval" = 'DAY_ONE') as "start_date",
                             (select max("date_part")::date as "end_date"
                              from raw.stg_cxpc_al_ai1
                              WHERE "Interval" = 'DAY_ONE') as "end_date"
                      from entire_period)
SELECT '1st month period' as "period", * FROM begining_month_maximum_high
UNION ALL
SELECT '2nd month period' as "period",* FROM three_month_maximum_high
UNION ALL
SELECT '6th month period' as "period",* FROM six_month_maximum_high
UNION ALL
SELECT '9th month period' as "period",* FROM nine_month_maximum_high
UNION ALL
SELECT '12th month period' as "period",* FROM twelve_month_maximum_high
UNION ALL
SELECT 'entire period' as "period",* FROM entire_period_maximum_high;


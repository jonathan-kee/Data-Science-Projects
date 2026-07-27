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
    order by 1
),
maximum_high as (
    select max("High")
    from entire_period
    )
select * from maximum_high;

-- The shorter the time span, the more urgent you want to sell --
WITH one_month as (
    select raw.stg_cxpc_al_ai1."date_part" ,raw.stg_cxpc_al_ai1."High"
    from raw.stg_cxpc_al_ai1
    WHERE "Interval" = 'DAY_ONE' and
    "date_part" between '2026-07-01' and '2026-07-26'
    order by 1 desc
),
maximum_high as (
    select max("High")
    from one_month
    )
select * from maximum_high;
with aggregates as (
    select
        Sum(material_input_total_cost) as "material_input_total_cost",
        max(material_output_total_sell_price) as "material_output_total_sell_price",
        max("total_order_per_day") as "total_order_per_day"
    from raw.dim_report
    where materialoutput = 'AL' and materialoutputquantity = 3
),
RoiPerDay as (
    select
        ("material_input_total_cost" - "material_input_total_cost") * "total_order_per_day" as RoiPerDay
    from aggregates
)
select * from RoiPerDay

-- 'AL' is ticker for aluminium
-- Ask Price is seller, You buy from them
-- Bid Price is buyer, You sell to them
select "AI1-AskPrice" , "AI1-BidPrice"
from raw.stg_market_depth
where "Ticker" = 'AL'
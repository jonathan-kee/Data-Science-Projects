with aggregates as (
    select
        Sum(raw.dim_report.material_input_total_cost) as "material_input_total_cost",
        max(raw.dim_report.material_output_total_sell_price) as "material_output_total_sell_price",
        max(raw.dim_report.total_order_per_day) as "total_order_per_day"
    from raw.dim_report
    where materialoutput = 'AL' and materialoutputquantity = 3
    -- and materialinput <> 'ALO' -- Comment Out to remove ALO because base already produce ALO
),
RoiPerDay as (
    select
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
CREATE TABLE raw.recipe_input_totals AS
with 
    joining_table as (
        select raw.stg_recipe_inputs_time.*, 
        -- Ask Price is seller, You buy from them --
        "AI1-AskPrice", 
        -- Bid Price is buyer, You sell to them -- 
        "AI1-BidPrice", 
        stg_recipe_inputs_time."time_ms" / 60000.0 AS "minutes"
        from raw.stg_recipe_inputs_time
        -- Because you only join on "materialinput", you cannot count the profit of output
        inner join
            raw.stg_prices
            on raw.stg_recipe_inputs_time."materialinput" = raw.stg_prices."Ticker"
        where
            -- maximum date --
            raw.stg_prices.date_part = (select max("date_part") from raw.stg_prices)
            order by 1
    ),
    group_by_total as (
        select
            joining_table."original_query",
            joining_table."prefix",
            max("minutes") as "minutes per order",
            CONCAT(
        CAST(MAX(minutes) AS INT) / 60, ' hours ', 
        CAST(MAX(minutes) AS INT) % 60, ' mins'
        ) AS "hour and minutes" ,
            max("minutes") / max("materialoutputquantity") as "minutes per unit",
            CONCAT(
        CAST(max("minutes") / max("materialoutputquantity") AS INT) / 60, ' hours ', 
        CAST(max("minutes") / max("materialoutputquantity") AS INT) % 60, ' mins'
        ) AS "hour and minutes" ,
            sum("AI1-AskPrice") / max("materialinputquantity") as "input_materials_AI1_askprice_per_unit"
        from joining_table 
        group by
            joining_table."original_query",
            joining_table."prefix"
        order by 1
    )
select *
from group_by_total
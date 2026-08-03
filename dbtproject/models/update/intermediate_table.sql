CREATE TABLE raw.recipe_input_totals AS
with 
    joining_table as (
        select raw.stg_recipe_inputs_time.*, "AI1-AskPrice", stg_recipe_inputs_time."time_ms" / 60000.0 AS "minutes"
        from raw.stg_recipe_inputs_time
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
            joining_table."materialinput",
            joining_table."materialinputquantity",
            -- Ask Price is seller, You buy from them --
            joining_table."AI1-AskPrice",
            sum("AI1-AskPrice") / max("materialinputquantity") as "total_a1_askprice",
            max("minutes") as "minutes per order",
            CONCAT(
        CAST(MAX(minutes) AS INT) / 60, ' hours ', 
        CAST(MAX(minutes) AS INT) % 60, ' mins'
        ) AS "hour and minutes" 
        from joining_table 
        group by
            joining_table."original_query",
            joining_table."prefix",
            joining_table."materialinput",
            joining_table."materialinputquantity",
            joining_table."AI1-AskPrice"
        order by 1
    )
select *
from group_by_total
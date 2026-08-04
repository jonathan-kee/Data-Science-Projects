with 
joining_table as (
    select raw.stg_recipe_inputs_time.*,
    -- Ask Price is seller, You buy from them --
    "AI1-AskPrice",
    -- Bid Price is buyer, You sell to them --
    "AI1-BidPrice",
    stg_recipe_inputs_time."time_ms" / 60000.0 AS "minutes"
    from {{ ref("stg_recipe_inputs_time") }}
    -- Joining on "materialinput" to get prices for each ingredient
    inner join
        raw.stg_prices
        on raw.stg_recipe_inputs_time."materialinput" = raw.stg_prices."Ticker"
    where
        -- maximum date --
        raw.stg_prices.date_part = (select max("date_part") from raw.stg_prices)
        -- filter by SME
        and prefix = 'SME' and materialinput <> 'ALO'
),
group_by_total_input as (
    select
        joining_table."original_query",
        joining_table."prefix",
        max("minutes") as "minutes per order",
        CONCAT(
            CAST(MAX(minutes) AS INT) / 60, ' hours ',
            CAST(MAX(minutes) AS INT) % 60, ' mins'
        ) AS "hour and minutes",
        max("minutes") / max("materialoutputquantity") as "minutes per unit",
        CONCAT(
            CAST(max("minutes") / max("materialoutputquantity") AS INT) / 60, ' hours ',
            CAST(max("minutes") / max("materialoutputquantity") AS INT) % 60, ' mins'
        ) AS "hour and minutes per unit",

        -- MULTIPLY EACH INGREDIENT PRICE BY ITS INPUT QUANTITY --
        sum("AI1-AskPrice" * "materialinputquantity") as "total input_materials_AI1_AskPrice",

        -- TOTAL INPUT COST DIVIDED BY OUTPUT QUANTITY FOR PER-UNIT COST --
        sum("AI1-AskPrice" * "materialinputquantity") / max("materialoutputquantity") as "input_materials_AI1_AskPrice_per_unit"

    from joining_table
    group by
        joining_table."original_query",
        joining_table."prefix"
)
select *
from group_by_total_input
order by 1
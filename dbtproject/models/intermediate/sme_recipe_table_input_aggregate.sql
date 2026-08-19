with
    joining_table as (
        select
            stg_recipe_inputs_time.*,
            -- Ask Price is seller, You buy from them --
            stg_prices."ai1_ask_price",
            -- Bid Price is buyer, You sell to them --
            stg_prices."ai1_bid_price",
            stg_recipe_inputs_time."time_ms" / 60000.0 as "minutes"
        -- PARENT TABLE: Acting as the base table holding the master list of prices
        from {{ ref("stg_prices_partition_date") }} as stg_prices
        -- CHILD TABLE: Joining the many recipe inputs that use these ingredients
        inner join
            {{ ref("stg_recipe_inputs_time") }} as stg_recipe_inputs_time
            on stg_prices."ticker" = stg_recipe_inputs_time."materialinput"
        where
            -- filter by SME and exclude ALO
            stg_recipe_inputs_time.prefix = 'SME'
            and stg_recipe_inputs_time.materialinput <> 'ALO'
    ),
    group_by_total_input as (
        select
            joining_table."original_query",
            joining_table."prefix",
            max("minutes") as "minutes per order",
            concat(
                cast(max(minutes) as int) / 60,
                ' hours ',
                cast(max(minutes) as int) % 60,
                ' mins'
            ) as "hour and minutes",
            max("minutes") / max("materialoutputquantity") as "minutes per unit",
            concat(
                cast(max("minutes") / max("materialoutputquantity") as int) / 60,
                ' hours ',
                cast(max("minutes") / max("materialoutputquantity") as int) % 60,
                ' mins'
            ) as "hour and minutes per unit",

            -- MULTIPLY EACH INGREDIENT PRICE BY ITS INPUT QUANTITY --
            sum(
                "ai1_ask_price" * "materialinputquantity"
            ) as "total input_materials_AI1_AskPrice",

            -- TOTAL INPUT COST DIVIDED BY OUTPUT QUANTITY FOR PER-UNIT COST --
            sum("ai1_ask_price" * "materialinputquantity")
            / max("materialoutputquantity") as "input_materials_AI1_AskPrice_per_unit"

        from joining_table
        group by joining_table."original_query", joining_table."prefix"
    )
select *
from group_by_total_input
order by 1

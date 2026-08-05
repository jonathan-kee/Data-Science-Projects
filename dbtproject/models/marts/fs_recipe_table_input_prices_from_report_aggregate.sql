with
    joining_table as (
        select
            stg_recipe_inputs_time.*,
            -- Ask Price is seller, You buy from them --
            "AI1-AskPrice",
            -- Bid Price is buyer, You sell to them --
            "AI1-BidPrice",
            stg_recipe_inputs_time."time_ms" / 60000.0 as "minutes"
        from {{ ref("stg_recipe_inputs_time") }} as stg_recipe_inputs_time
        -- Joining on "materialinput" to get prices for each ingredient
        inner join
            {{ ref("prices_from_recipe_report") }} as prices_from_recipe_report
            on stg_recipe_inputs_time."materialinput"
            = prices_from_recipe_report."Ticker"
        where
            -- maximum date --
            prices_from_recipe_report."date_part"
            = (select max("date_part") from {{ ref("prices_from_recipe_report") }})
            -- filter by SME
            and prefix = 'FS'
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
                "AI1-AskPrice" * "materialinputquantity"
            ) as "total input_materials_AI1_AskPrice",

            -- TOTAL INPUT COST DIVIDED BY OUTPUT QUANTITY FOR PER-UNIT COST --
            sum("AI1-AskPrice" * "materialinputquantity")
            / max("materialoutputquantity") as "input_materials_AI1_AskPrice_per_unit"

        from joining_table
        group by joining_table."original_query", joining_table."prefix"
    )
select *
from group_by_total_input
order by 1

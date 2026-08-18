with
    -- Looks correct
    joining_table as (
        select
            stg_recipe_inputs_time.*,
            -- Ask Price is seller, You buy from them --
            "ai1_ask_price",
            -- Bid Price is buyer, You sell to them --
            "ai1_bid_price",
            stg_recipe_inputs_time."time_ms" / 60000.0 as "minutes"
        from {{ ref("stg_recipe_inputs_time") }} as stg_recipe_inputs_time
        -- Joining on "materialinput" to get prices for each ingredient
        inner join
            {{ ref("prices_from_recipe_report_v2") }} as prices_from_recipe_report
            on stg_recipe_inputs_time."materialinput"
            = prices_from_recipe_report."ticker"
        where
            {% if var("date_part", none) is not none %}
                prices_from_recipe_report."date_part" = '{{ var("date_part") }}'
            {% else %}
                prices_from_recipe_report."date_part" = (select max("date_part") from {{ ref("prices_from_recipe_report_v2") }})
            {% endif %}
            -- filter by SME
            and prefix = 'FS'
    ),
    group_by_total_input as (
        select
            joining_table."original_query",
            joining_table."prefix",
            max("minutes") as "minutes_per_order",
            concat(
                cast(max(minutes) as int) / 60,
                ' hours ',
                cast(max(minutes) as int) % 60,
                ' mins'
            ) as "hour_and_minutes",
            max("minutes") / max("materialoutputquantity") as "minutes_per_unit",
            concat(
                cast(max("minutes") / max("materialoutputquantity") as int) / 60,
                ' hours ',
                cast(max("minutes") / max("materialoutputquantity") as int) % 60,
                ' mins'
            ) as "hour_and_minutes_per_unit",

            -- MULTIPLY EACH INGREDIENT PRICE BY ITS INPUT QUANTITY --
            sum(
                "ai1_ask_price" * "materialinputquantity"
            ) as "total_input_materials_AI1_AskPrice",

            -- TOTAL INPUT COST DIVIDED BY OUTPUT QUANTITY FOR PER-UNIT COST --
            sum("ai1_ask_price" * "materialinputquantity")
            / max("materialoutputquantity") as "input_materials_AI1_AskPrice_per_unit"

        from joining_table
        group by joining_table."original_query", joining_table."prefix"
    )
select *
from group_by_total_input
order by 1
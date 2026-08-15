with
    joining_table as (
        select
            stg_recipe_inputs_time.*,
            -- Ask Price is seller, You buy from them --
            stg_prices."AI1-AskPrice",
            -- Bid Price is buyer, You sell to them --
            stg_prices."AI1-BidPrice",
            stg_recipe_inputs_time."time_ms" / 60000.0 as "minutes"
        from {{ ref("stg_recipe_inputs_time") }} as stg_recipe_inputs_time
        inner join
            {{ ref("stg_prices") }} as stg_prices
            on stg_recipe_inputs_time."materialoutput" = stg_prices."Ticker"
        where
            {% if var("date_part", none) is not none %}
                stg_prices.date_part = '{{ var("date_part") }}'
            {% else %}
                stg_prices.date_part = (select max("date_part") from {{ ref("stg_prices") }})
            {% endif %}
            and prefix = 'SME'
    ),
    group_by_total_output as (
        select
            joining_table."original_query",
            joining_table."prefix",
            joining_table."materialoutputquantity",
            joining_table."materialoutput",
            max("minutes") as "minutes per order",
            concat(
                cast(max(minutes) as int) / 60,
                ' hours ',
                cast(max(minutes) as int) % 60,
                ' mins'
            ) as "hour and minutes",

            -- Multiply Unit Price (1940) by Quantity (e.g. 2) to get Total (3880) --
            (sum("AI1-BidPrice") / count(*))
            * max("materialoutputquantity") as "total output_materials_AI1_BidPrice",

            -- Unit price remains 1940 --
            sum("AI1-BidPrice") / count(*) as "output_materials_AI1_BidPrice_per_unit"

        from joining_table
        group by
            joining_table."original_query",
            joining_table."prefix",
            joining_table."materialoutputquantity",
            joining_table."materialoutput"
    )
select *
from group_by_total_output
order by 1
with
    joining_table as (
        select
            stg_recipe_inputs_time.*,
            -- Ask Price is seller, You buy from them --
            "ai1_ask_price",
            -- Bid Price is buyer, You sell to them --
            "ai1_bid_price",
            stg_recipe_inputs_time."time_ms" / 60000.0 as "minutes"
        from {{ ref("stg_recipe_inputs_time") }} as stg_recipe_inputs_time
        inner join
            {{ ref("stg_prices") }} as stg_prices
            on stg_recipe_inputs_time."materialoutput" = stg_prices."ticker"
        where
            {% if var("date_part", none) is not none %}
                stg_prices.date_part = '{{ var("date_part") }}'
            {% else %}
                stg_prices.date_part = (select max("date_part") from {{ ref("stg_prices") }})
            {% endif %}
            and prefix = 'FS'
    ),
    
    -- FS:1xZR-1xAL=>1xAFR = 22000 "AI1-BidPrice"
    -- FS:4xAU-1xFE=>5xBGO = 3010 * 5 = 15050
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
            (sum("ai1_bid_price") / count(*))
            * max("materialoutputquantity") as "total_output_materials_AI1_BidPrice",

            -- Unit price remains 1940 --
            sum("ai1_bid_price") / count(*) as "output_materials_AI1_BidPrice_per_unit"

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
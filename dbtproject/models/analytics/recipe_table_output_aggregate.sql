with 
joining_table as (
    select 
        stg_recipe_inputs_time.*,
        raw.stg_prices."AI1-AskPrice",
        raw.stg_prices."AI1-BidPrice",
        stg_recipe_inputs_time."time_ms" / 60000.0 AS "minutes"
    from {{ ref("stg_recipe_inputs_time") }}
    inner join raw.stg_prices
        on raw.stg_recipe_inputs_time."materialoutput" = raw.stg_prices."Ticker"
    where
        raw.stg_prices.date_part = (select max("date_part") from raw.stg_prices)
        and prefix = 'SME'
),
group_by_total_output as (
    select
        joining_table."original_query",
        joining_table."prefix",
        joining_table."materialoutputquantity",
        joining_table."materialoutput",
        max("minutes") as "minutes per order",
        CONCAT(
            CAST(MAX(minutes) AS INT) / 60, ' hours ',
            CAST(MAX(minutes) AS INT) % 60, ' mins'
        ) AS "hour and minutes",
        
        -- Multiply Unit Price (1940) by Quantity (e.g. 2) to get Total (3880) --
        (sum("AI1-BidPrice") / count(*)) * max("materialoutputquantity") as "total output_materials_AI1_BidPrice",
        
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
order by 1;
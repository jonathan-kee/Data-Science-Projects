with
    stg_prices as (
        select *
        from {{ ref("stg_prices") }}
        where
            -- raw.stg_prices.date_part = '2026-07-30'
            -- maximum date --
            raw.stg_prices.date_part
            = (select max("date_part") from {{ ref("stg_prices") }})
    ),

    stg_recipe_inputs as (select * from {{ ref("stg_recipe_inputs") }}),
    stg_recipe_inputs_time as (select * from {{ ref("stg_recipe_inputs_time") }}),
    material_input_total_cost_cte as (
        select
            stg_recipe_inputs.original_query,
            stg_recipe_inputs.prefix,
            stg_recipe_inputs.materialinputquantity,
            stg_recipe_inputs.materialinput,
            -- Ask Price is seller, You buy from them --
            stg_prices."AI1-AskPrice",
            stg_recipe_inputs.materialinputquantity
            * stg_prices."AI1-AskPrice" as "material_input_total_cost",
            stg_recipe_inputs.materialoutputquantity,
            stg_recipe_inputs.materialoutput
        from stg_prices
        left join
            stg_recipe_inputs on stg_recipe_inputs.materialinput = stg_prices."Ticker"
    ),
    material_output_total_cost as (
        select
            material_input_total_cost_cte.original_query,
            material_input_total_cost_cte.prefix,
            material_input_total_cost_cte.materialinputquantity,
            material_input_total_cost_cte.materialinput,
            material_input_total_cost_cte."AI1-AskPrice" as "material_input_buy_price",
            material_input_total_cost_cte."material_input_total_cost",
            material_input_total_cost_cte.materialoutputquantity,
            material_input_total_cost_cte.materialoutput,
            -- Bid Price is buyer, You sell to them -- 
            stg_prices."AI1-BidPrice" as "material_output_sell_price",
            material_input_total_cost_cte.materialoutputquantity
            * stg_prices."AI1-BidPrice" as "material_output_total_sell_price",
            (
                stg_recipe_inputs_time.time_ms / 60000
            ) as "time_taken_per_order_in_minutes",
            cast(
                (24 * 60) / cast(
                    (stg_recipe_inputs_time.time_ms / 60000) as decimal(10, 2)
                ) as decimal(10, 2)
            ) as "total_order_per_day"
        from stg_prices
        left join
            material_input_total_cost_cte
            on material_input_total_cost_cte.materialoutput = stg_prices."Ticker"
        left join
            stg_recipe_inputs_time
            on stg_recipe_inputs_time.prefix = material_input_total_cost_cte.prefix
            and stg_recipe_inputs_time.materialinputquantity
            = material_input_total_cost_cte.materialinputquantity
            and stg_recipe_inputs_time.materialinput
            = material_input_total_cost_cte.materialinput
            and stg_recipe_inputs_time.materialoutputquantity
            = material_input_total_cost_cte.materialoutputquantity
            and stg_recipe_inputs_time.materialoutput
            = material_input_total_cost_cte.materialoutput
    -- The problem with the above query is that I can only accurately get one of the
    -- total cost,
    -- need to split the data
    )
select *
from material_output_total_cost

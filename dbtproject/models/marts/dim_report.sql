with
    stg_market_depth as (select * from {{ ref("stg_market_depth") }}),

    stg_recipe_inputs as (select * from {{ ref("stg_recipe_inputs") }}),
    stg_recipe_inputs_time as (select * from {{ ref("stg_recipe_inputs_time") }}),
    material_input_total_cost as (
        select
            stg_recipe_inputs.original_query,
            stg_recipe_inputs.prefix,
            stg_recipe_inputs.materialinputquantity,
            stg_recipe_inputs.materialinput,
            -- Ask Price is seller, You buy from them --
            stg_market_depth."AI1-AskPrice",
            stg_recipe_inputs.materialinputquantity
            * stg_market_depth."AI1-AskPrice" as "material_input_total_cost",
            stg_recipe_inputs.materialoutputquantity,
            stg_recipe_inputs.materialoutput
        from stg_market_depth
        left join
            stg_recipe_inputs
            on stg_recipe_inputs.materialinput = stg_market_depth."Ticker"
    ),
    material_output_total_cost as (
        select
            material_input_total_cost.original_query,
            material_input_total_cost.prefix,
            material_input_total_cost.materialinputquantity,
            material_input_total_cost.materialinput,
            material_input_total_cost."AI1-Average" as "material input's AI1-Average",
            material_input_total_cost."total cost" as "material input's total cost",
            material_input_total_cost.materialoutputquantity,
            material_input_total_cost.materialoutput,
            stg_market_depth."AI1-Average" as "material output's AI1-Average",
            material_input_total_cost.materialoutputquantity
            * stg_market_depth."AI1-Average" as "material output's total price",
            (material_input_total_cost.materialoutputquantity * stg_market_depth."AI1-Average")
            - material_input_total_cost."total cost" as profit,
            (
                stg_recipe_inputs_time.time_ms / 60000
            ) as "time taken per order in minutes",
            (24 * 60)
            / (stg_recipe_inputs_time.time_ms / 60000) as "total_order_per_day"
        from stg_market_depth
        left join material_input_total_cost on material_input_total_cost.materialoutput = stg_market_depth."Ticker"
        left join
            stg_recipe_inputs_time
            on stg_recipe_inputs_time.prefix = material_input_total_cost.prefix
            and stg_recipe_inputs_time.materialinputquantity
            = material_input_total_cost.materialinputquantity
            and stg_recipe_inputs_time.materialinput = material_input_total_cost.materialinput
            and stg_recipe_inputs_time.materialoutputquantity
            = material_input_total_cost.materialoutputquantity
            and stg_recipe_inputs_time.materialoutput = material_input_total_cost.materialoutput
    -- The problem with the above query is that I can only accurately get one of the
    -- total cost,
    -- need to split the data
    )
select *
from material_output_total_cost

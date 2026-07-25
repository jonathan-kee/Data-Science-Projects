with stg_market_depth as (
    select * from {{ref("stg_market_depth")}}
),

stg_recipe_inputs as (
    select * from {{ref("stg_recipe_inputs")}}
),
stg_recipe_inputs_time as (
    select * from {{ref("stg_recipe_inputs_time")}}
),
material_input_total_cost AS (select stg_recipe_inputs.original_query,
                      stg_recipe_inputs.prefix,
                      stg_recipe_inputs.materialInputQuantity,
                      stg_recipe_inputs.materialInput,
                      -- Ask Price is seller, You buy from them --
                      stg_market_depth."AI1-AskPrice",
                      stg_recipe_inputs.materialInputQuantity * stg_market_depth."AI1-AskPrice" as "material_input_total_cost",
                      stg_recipe_inputs.materialOutputQuantity,
                      stg_recipe_inputs.materialOutput
               from stg_market_depth
                        left join stg_recipe_inputs on stg_recipe_inputs.materialInput = stg_market_depth."Ticker"
),
final as (
  select totalCost.original_query,
       totalCost.prefix,
totalCost.materialInputQuantity,
totalCost.materialInput,
totalCost."AI1-Average" as "material input's AI1-Average",
totalCost."total cost" as "material input's total cost",
totalCost.materialOutputQuantity,
totalCost.materialOutput,
stg_market_depth."AI1-Average" as "material output's AI1-Average",
totalCost.materialOutputQuantity * stg_market_depth."AI1-Average" as "material output's total price",
(totalCost.materialOutputQuantity * stg_market_depth."AI1-Average") - totalCost."total cost" as profit,
(stg_recipe_inputs_time.time_ms / 60000) as "time taken per order in minutes",
(24* 60) / (stg_recipe_inputs_time.time_ms / 60000) as "total_order_per_day"
from stg_market_depth 
left join totalCost on totalCost.materialOutput = stg_market_depth."Ticker"
left join stg_recipe_inputs_time on stg_recipe_inputs_time.prefix = totalCost.prefix 
and stg_recipe_inputs_time.materialInputQuantity = totalCost.materialInputQuantity
and stg_recipe_inputs_time.materialInput = totalCost.materialInput
and stg_recipe_inputs_time.materialOutputQuantity = totalCost.materialOutputQuantity
and stg_recipe_inputs_time.materialOutput = totalCost.materialOutput
-- The problem with the above query is that I can only accurately get one of the total cost,
-- need to split the data
)

select * from final
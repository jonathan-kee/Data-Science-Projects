with stg_market_depth as (
    select * from {{ref("stg_market_depth")}}
),

stg_recipe_inputs as (
    select * from {{ref("stg_recipe_inputs")}}
),
totalCost AS (select stg_recipe_inputs.original_query,
                      stg_recipe_inputs.prefix,
                      stg_recipe_inputs.materialInputQuantity,
                      stg_recipe_inputs.materialInput,
                      stg_market_depth."AI1-Average",
                      stg_recipe_inputs.materialInputQuantity * stg_market_depth."AI1-Average" as "total cost",
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
(totalCost.materialOutputQuantity * stg_market_depth."AI1-Average") - totalCost."total cost" as profit
from stg_market_depth left join totalCost on totalCost.materialOutput = stg_market_depth."Ticker"
-- The problem with the above query is that I can only accurately get one of the total cost,
-- need to split the data
)

select * from final
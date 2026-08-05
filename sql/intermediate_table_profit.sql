select distinct recipe.original_query,"total output_materials_AI1_BidPrice" - "total input_materials_AI1_AskPrice" as "profit"
from (
    select distinct original_query, prefix
    from raw.stg_recipe_inputs_time
     ) as recipe
    join raw.recipe_input_aggregates
    on recipe.original_query = raw.recipe_input_aggregates.original_query
    join raw.recipe_output_aggregates
    on recipe.original_query = raw.recipe_input_aggregates.original_query
where  recipe.prefix = 'SME'
order by 2 desc;
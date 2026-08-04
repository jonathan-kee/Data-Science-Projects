select raw.recipe_table_input_aggregate.original_query,
       RIGHT(raw.recipe_table_input_aggregate.original_query, 2) as "Output Material",
       "total input_materials_AI1_AskPrice" / "input_materials_AI1_AskPrice_per_unit" as "volume",
       "input_materials_AI1_AskPrice_per_unit",
       "total input_materials_AI1_AskPrice",
       "total output_materials_AI1_BidPrice",
       "total output_materials_AI1_BidPrice" - "total input_materials_AI1_AskPrice" as "profit"
from {{ ref("recipe_table_input_aggregate") }} join raw.recipe_table_output_aggregate
    on raw.recipe_table_input_aggregate.original_query = raw.recipe_table_output_aggregate.original_query
where raw.recipe_table_input_aggregate.prefix = 'SME'
ORDER BY "profit" desc
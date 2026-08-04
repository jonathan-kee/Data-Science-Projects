select raw.recipe_table_input_aggregate.original_query,
        raw.recipe_table_input_aggregate.prefix,
       SPLIT_PART(raw.recipe_table_input_aggregate.original_query, 'x', -1) as "Output Material",
       "total input_materials_AI1_AskPrice" / "input_materials_AI1_AskPrice_per_unit" as "volume",
       "input_materials_AI1_AskPrice_per_unit",
       "total input_materials_AI1_AskPrice",
       "total output_materials_AI1_BidPrice",
       "total output_materials_AI1_BidPrice" - "total input_materials_AI1_AskPrice" as "profit"
from {{ ref("fs_recipe_table_input_prices_from_report_aggregate") }} join raw.fs_recipe_table_output_aggregate
    on raw.recipe_table_input_aggregate.original_query = raw.recipe_table_output_aggregate.original_query
where raw.recipe_table_input_aggregate.prefix = 'SME'
ORDER BY "profit" desc
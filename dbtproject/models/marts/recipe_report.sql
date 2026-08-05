select
    recipe_table_input_aggregate.original_query,
    recipe_table_input_aggregate.prefix,
    split_part(
        recipe_table_input_aggregate.original_query, 'x', -1
    ) as "Output_Material",
    "total input_materials_AI1_AskPrice"
    / "input_materials_AI1_AskPrice_per_unit" as "volume",
    "input_materials_AI1_AskPrice_per_unit",
    "total input_materials_AI1_AskPrice",
    "total output_materials_AI1_BidPrice",
    "total output_materials_AI1_BidPrice"
    - "total input_materials_AI1_AskPrice" as "profit of buy minus sell",
    (1440 / recipe_table_input_aggregate."minutes per order") * (
        "total output_materials_AI1_BidPrice" - "total input_materials_AI1_AskPrice"
    ) as "profit per day"
from {{ ref("recipe_table_input_aggregate") }} as recipe_table_input_aggregate
join
    {{ ref("recipe_table_output_aggregate") }} as recipe_table_output_aggregate
    on recipe_table_input_aggregate.original_query
    = recipe_table_output_aggregate.original_query
where recipe_table_input_aggregate.prefix = 'SME'
order by "profit per day" desc

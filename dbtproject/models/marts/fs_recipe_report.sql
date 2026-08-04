select fs_recipe_table_input_prices_from_report_aggregate.original_query,
        fs_recipe_table_input_prices_from_report_aggregate.prefix,
       SPLIT_PART(fs_recipe_table_input_prices_from_report_aggregate.original_query, 'x', -1) as "Output Material",
       "total input_materials_AI1_AskPrice" / "input_materials_AI1_AskPrice_per_unit" as "volume",
       "input_materials_AI1_AskPrice_per_unit",
       "total input_materials_AI1_AskPrice",
       "total output_materials_AI1_BidPrice",
       "total output_materials_AI1_BidPrice" - "total input_materials_AI1_AskPrice" as "profit",
       (1440 / fs_recipe_table_input_prices_from_report_aggregate."minutes per order") * ("total output_materials_AI1_BidPrice" - "total input_materials_AI1_AskPrice") as "profit per day"
from {{ ref("fs_recipe_table_input_prices_from_report_aggregate") }} as fs_recipe_table_input_prices_from_report_aggregate
join {{ ref("fs_recipe_table_output_aggregate") }} as fs_recipe_table_output_aggregate
    on fs_recipe_table_input_prices_from_report_aggregate.original_query = fs_recipe_table_output_aggregate.original_query
where fs_recipe_table_input_prices_from_report_aggregate.prefix = 'FS'
ORDER BY "profit per day" desc
select
    input.original_query,
    input.prefix,
    split_part(
        input.original_query, 'x', -1
    ) as "Output Material",
    "total input_materials_AI1_AskPrice"
    / "input_materials_AI1_AskPrice_per_unit" as "volume",
    "input_materials_AI1_AskPrice_per_unit",
    "total input_materials_AI1_AskPrice" / "input_materials_AI1_AskPrice_per_unit" as "Quantity",
    "total input_materials_AI1_AskPrice",
    "total output_materials_AI1_BidPrice",
    -- Should not be total minus total, should be individual --
    "total output_materials_AI1_BidPrice" - "total input_materials_AI1_AskPrice" as "profit",
    (1440 / input."minutes per order") * (
        "total output_materials_AI1_BidPrice" - "total input_materials_AI1_AskPrice"
    ) as "profit per day"
from
    {{ ref("fs_recipe_table_input_prices_from_report_aggregate") }}
    as input
join
    {{ ref("fs_recipe_table_output_aggregate") }} as output
    on input.original_query
    = output.original_query
where input.prefix = 'FS'
order by "profit per day" desc

-- fs_recipe_report
-- FS:1xFE=>16xSFK
-- total input_materials_AI1_AskPrice
-- 5771.666666666666

-- recipe_report
-- price of 1 FE 1318.5
-- total input material cost 5274
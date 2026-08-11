select
    input.original_query,
    input.prefix,
    split_part(
        input.original_query, 'x', -1
    ) as "Output Material",
    input."input_materials_AI1_AskPrice_per_unit",
    input."total input_materials_AI1_AskPrice",
    output."total output_materials_AI1_BidPrice",
    -- Should not be total minus total, should be individual --
    output."total output_materials_AI1_BidPrice" - input."total input_materials_AI1_AskPrice" as "profit_per_total",
    (1440 / input."minutes per order") * (output."total output_materials_AI1_BidPrice" - input."total input_materials_AI1_AskPrice") as "profit_per_day"
from
    {{ ref("fs_recipe_table_input_prices_from_report_aggregate") }}
    as input
join
    {{ ref("fs_recipe_table_output_aggregate") }} as output
    on input.original_query
    = output.original_query
where input.prefix = 'FS'
order by "profit_per_total" desc

-- fs_recipe_report
-- FS:1xFE=>16xSFK
-- total input_materials_AI1_AskPrice
-- 5771.666666666666

-- recipe_report
-- price of 1 FE 1318.5
-- total input material cost 5274
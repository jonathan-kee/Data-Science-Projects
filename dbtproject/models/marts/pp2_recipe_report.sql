{{
    config(
        materialized="incremental",
        unique_key=["report_date", "original_query"],
        incremental_strategy="delete+insert",
    )
}}

select
    -- 1. Add a daily date identifier to stamp each snapshot
    cast(
        '{{ var("date_part", run_started_at.strftime("%Y-%m-%d")) }}' as date
    ) as report_date,
    input.original_query,
    input.prefix,
    split_part(input.original_query, 'x', -1) as "Output Material",
    input."input_materials_AI1_AskPrice_per_unit",
    input."total_input_materials_AI1_AskPrice",
    output."total_output_materials_AI1_BidPrice",
    -- Should not be total minus total, should be individual --
    output."total_output_materials_AI1_BidPrice"
    - input."total_input_materials_AI1_AskPrice" as "profit_per_total",
    (1440 / input."minutes_per_order") * (
        output."total_output_materials_AI1_BidPrice"
        - input."total_input_materials_AI1_AskPrice"
    ) as "profit_per_day"
from {{ ref("pp2_recipe_table_input_prices_from_report_aggregate") }} as input
join
    {{ ref("pp2_recipe_table_output_aggregate") }} as output
    on input.original_query = output.original_query
where input.prefix = 'PP2'
order by
    "profit_per_total" desc

    -- fs_recipe_report
    -- FS:1xFE=>16xSFK
    -- total input_materials_AI1_AskPrice
    -- 5771.666666666666
    -- recipe_report
    -- price of 1 FE 1318.5
    -- total input material cost 5274

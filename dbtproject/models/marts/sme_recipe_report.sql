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
    - "total input_materials_AI1_AskPrice" as "profit_of_buy_minus_sell",
    (1440 / recipe_table_input_aggregate."minutes per order") as "order_per_day",
    -- 1.0 - 0.1248 is based on expert calculation --
    ((1440 / recipe_table_input_aggregate."minutes per order") * (1.0 - 0.1248)) as "expert_order_per_day",
    ((1440 / recipe_table_input_aggregate."minutes per order") * (1.0 - 0.1248)) 
    * 25.00 as "production_fee_per_day",
    ((1440 / recipe_table_input_aggregate."minutes per order") * (1.0 - 0.1248)) 
    * ("total output_materials_AI1_BidPrice") as "revenue_per_day",
    ((1440 / recipe_table_input_aggregate."minutes per order") * (1.0 - 0.1248))  * ("total output_materials_AI1_BidPrice" - "total input_materials_AI1_AskPrice")
    - ((1440 / recipe_table_input_aggregate."minutes per order") * (1.0 - 0.1248))  * 25.00 as "profit_per_day",
    sme_traded_report."traded_rank" as "traded_rank"
from {{ ref("sme_recipe_table_input_aggregate") }} as recipe_table_input_aggregate
join
    {{ ref("sme_recipe_table_output_aggregate") }} as recipe_table_output_aggregate
    on recipe_table_input_aggregate.original_query
    = recipe_table_output_aggregate.original_query
left join
    {{ ref("sme_traded_report") }} as sme_traded_report
    on split_part(recipe_table_input_aggregate.original_query, 'x', -1)
    = upper(sme_traded_report."ticker")
where recipe_table_input_aggregate.prefix = 'SME'
order by "profit_per_day" desc

with 
joining_table_recipe_report as (
    select *
    from {{ ref("recipe_report") }}
),
joining_table as (
    select raw.stg_recipe_inputs_time.*, "input_materials_AI1_AskPrice_per_unit"
    from {{ ref("stg_recipe_inputs_time") }}
    -- Joining on "materialinput" to get prices for each ingredient
    left join 
    {{ ref("recipe_report") }} as recipe_report
         ON raw.stg_recipe_inputs_time."materialinput" = recipe_report."Output Material"
),
group_by_total_input as (
    select
        joining_table."original_query",
        joining_table."prefix",
        max("minutes") as "minutes per order",
        CONCAT(
            CAST(MAX(minutes) AS INT) / 60, ' hours ',
            CAST(MAX(minutes) AS INT) % 60, ' mins'
        ) AS "hour and minutes",
        max("minutes") / max("materialoutputquantity") as "minutes per unit",
        CONCAT(
            CAST(max("minutes") / max("materialoutputquantity") AS INT) / 60, ' hours ',
            CAST(max("minutes") / max("materialoutputquantity") AS INT) % 60, ' mins'
        ) AS "hour and minutes per unit",

        -- MULTIPLY EACH INGREDIENT PRICE BY ITS INPUT QUANTITY --
        sum("AI1-AskPrice" * "materialinputquantity") as "total input_materials_AI1_AskPrice",

        -- TOTAL INPUT COST DIVIDED BY OUTPUT QUANTITY FOR PER-UNIT COST --
        sum("AI1-AskPrice" * "materialinputquantity") / max("materialoutputquantity") as "input_materials_AI1_AskPrice_per_unit"

    from joining_table
    group by
        joining_table."original_query",
        joining_table."prefix"
)
select *
from group_by_total_input
order by 1
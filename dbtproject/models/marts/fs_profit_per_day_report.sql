with
    material_input_time as (
        select max("minutes per order") as "minutes per order"
        from raw.recipe_table_input_aggregate
        where original_query in ('SME:1xC-3xAUO=>2xAU', 'SME:6xFEO-1xC-1xO-1xFLX=>4xFE')
    ),
    material_output_time as (
        select "minutes per order"
        from raw.fs_recipe_table_output_aggregate
        where original_query = 'FS:4xAU-1xFE=>5xBGO'
    ),
    profit_per_day as (
        select
            (
                1440 / (
                    material_input_time."minutes per order"
                    + material_output_time."minutes per order"
                )
            )
            * "profit_per_total" as "profit_per_day"
        from raw.fs_recipe_report
        join material_input_time on 1 = 1
        join material_output_time on 1 = 1
        where original_query = 'FS:4xAU-1xFE=>5xBGO'
    ),
    material_input_time_2 as (
        select max("minutes per order") as "minutes per order"
        from raw.recipe_table_input_aggregate
        where original_query in ('SME:5xCUO-10xO-1xSIO=>3xCU')
    ),
    material_output_time_2 as (
        select "minutes per order"
        from raw.fs_recipe_table_output_aggregate
        where original_query = 'FS:1xCU-300xPE=>10xBCO'
    ),
    profit_per_day_2 as (
        select
            (
                1440 / (
                    material_input_time."minutes per order"
                    + material_output_time."minutes per order"
                )
            )
            * "profit_per_total" as "profit_per_day"
        from raw.fs_recipe_report
        join material_input_time on 1 = 1
        join material_output_time on 1 = 1
        where original_query = 'FS:1xCU-300xPE=>10xBCO'
    ),material_input_time_3 as (
        select max("minutes per order") as "minutes per order"
        from raw.recipe_table_input_aggregate
        where original_query in ('SME:6xALO-1xO-1xC-1xFLX=>4xAL', 'SME:5xCUO-10xO-1xSIO=>3xCU')
    ),
    material_output_time_3 as (
        select "minutes per order"
        from raw.fs_recipe_table_output_aggregate
        where original_query = 'FS:1xAL-2xCU=>3xBRO'
    ),
    profit_per_day_3 as (
        select
            (
                1440 / (
                    material_input_time_3."minutes per order"
                    + material_output_time_3."minutes per order"
                )
            )
            * "profit_per_total" as "profit_per_day"
        from raw.fs_recipe_report
        join material_input_time_3 on 1 = 1
        join material_output_time_3 on 1 = 1
        where original_query = 'FS:1xAL-2xCU=>3xBRO'
    )
select *
from profit_per_day
union all
select *
from profit_per_day_2
union all
select *
from profit_per_day_3
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
            * "profit" as "profit_per_day"
        from raw.fs_recipe_report
        join material_input_time on 1 = 1
        join material_output_time on 1 = 1
        where original_query = 'FS:4xAU-1xFE=>5xBGO'
    )
select *
from profit_per_day

with
    report1 as (
        select 'days_to_support_recipe_recipe_report' as "report", "materialinput" ,"total_days_left_per_building" as "days_left"
        from {{ ref("days_to_support_recipe_report") }}

    ),
    report2 as (
        select 'workforce_consumable_report' as "report","material_ticker", "days_left"
        from {{ ref("workforce_consumable_report") }}
    )
select *
from report1
union all
select *
from report2
order by "days_left" asc

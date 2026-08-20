with
    report1 as (
        select "materialinput", "days_left"
        from {{ ref("days_to_support_recipe_report") }}

    ),
    report2 as (
        select "material_ticker", "days_left"
        from {{ ref("workforce_consumable_report") }}
    )
select *
from report1
union all
select *
from report2
order by "days_left" asc

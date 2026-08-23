select
    report_date,
    (
        select days_left
        from {{ ref("days_to_support_base_report") }}
        where materialinput = 'O'
    ) as "days_left",
    revenue_per_day,
    (
        select total_selling_price
        from {{ ref("inventory_price_report_v2") }}
        where
            report_date = (select max(report_date) from {{ ref("inventory_price_report_v2") }})
            and material_ticker = 'AL'
    ) as "inventory_revenue",
    (
        revenue_per_day * (
            select days_left
            from {{ ref("days_to_support_base_report") }}
            where materialinput = 'O'
        )
    ) + (
        select total_selling_price
        from {{ ref("inventory_price_report_v2") }}
        where
            report_date = (select max(report_date) from {{ ref("inventory_price_report_v2") }})
            and material_ticker = 'AL'
    ) as "total_revenue_before_exchange"
from {{ ref("revenue_per_day_report") }}
order by report_date asc

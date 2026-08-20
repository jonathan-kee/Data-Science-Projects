select
    report_date,
    (
        select days_left
        from raw.days_to_support_base_report
        where materialinput = 'RAT'
    ) as "days_left",
    revenue_per_day,
    (
        select total_selling_price
        from raw.inventory_price_report_v2
        where
            report_date = (select max(report_date) from raw.inventory_price_report_v2)
            and material_ticker = 'AL'
    ) as "inventory_revenue",
    (
        revenue_per_day * (
            select days_left
            from raw.days_to_support_base_report
            where materialinput = 'RAT'
        )
    ) + (
        select total_selling_price
        from raw.inventory_price_report_v2
        where
            report_date = (select max(report_date) from raw.inventory_price_report_v2)
            and material_ticker = 'AL'
    ) as "total_revenue_before_exchange"
from raw.revenue_per_day_report

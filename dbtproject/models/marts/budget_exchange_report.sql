with
    calculation as (
        select
            revenue_before_exchange_report.report_date,
            revenue_before_exchange_report.total_revenue_before_exchange
            / total_cost_per_day as "number_of_days_to_support_for_budget"
        from
            {{ ref("revenue_before_exchange_report") }}
            as revenue_before_exchange_report
        join
            {{ ref("cost_per_day_report") }} as cost_per_day_report
            on revenue_before_exchange_report.report_date
            = cost_per_day_report.report_date
        order by revenue_before_exchange_report.report_date
    )
select *
from calculation

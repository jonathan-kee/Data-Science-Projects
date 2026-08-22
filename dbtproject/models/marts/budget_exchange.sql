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
    ),
    future_revenue_before_exchange as (
            {# select sme_recipe_report.report_date, number_of_days_to_support_for_budget, (revenue_per_day * 4) * number_of_days_to_support_for_budget as "total__future_revenue"
            from {{ ref("sme_recipe_report") }} as sme_recipe_report
            join calculation on sme_recipe_report.report_date = calculation.report_date
            where original_query = 'SME:6xALO-1xO-1xC-1xFLX=>4xAL'
            and sme_recipe_report.report_date = (select max(report_date)from {{ ref("sme_recipe_report") }} )  #}

        select revenue_per_day_report.report_date, "total_revenue_per_day" * number_of_days_to_support_for_budget as "total_future_revenue"
        from {{ ref("revenue_per_day_report") }} as revenue_per_day_report
        join calculation on revenue_per_day_report.report_date = calculation.report_date
    ),
    future_calculation as (
        select
            future_revenue_before_exchange.report_date,
            future_revenue_before_exchange.total_future_revenue
            / total_cost_per_day as "number_of_days_to_support_for_budget"
        from future_revenue_before_exchange as future_revenue_before_exchange
        join
            {{ ref("cost_per_day_report") }} as cost_per_day_report
            on future_revenue_before_exchange.report_date = cost_per_day_report.report_date
        order by future_revenue_before_exchange.report_date
    )
select *
from future_calculation;

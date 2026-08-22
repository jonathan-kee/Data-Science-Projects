with
    profit as (
        select
            report_date,  -- ADDED: Need this here so we can join it to 'cost' later
            "revenue_per_day"
        from {{ ref("sme_recipe_report") }}
        where
            original_query = 'SME:6xALO-1xO-1xC-1xFLX=>4xAL'

            -- UPDATED: Support ranges first
            {% if var("start_date", none) is not none and var(
                "end_date", none
            ) is not none %}
                and report_date
                between '{{ var("start_date") }}' and '{{ var("end_date") }}'

            -- Fallback to your old single-day logic
            {% elif var("date_part", none) is not none %}
                and report_date = '{{ var("date_part") }}'

            -- Default when no vars are passed
            {% else %}
                and report_date
                = (select max(report_date) from {{ ref("sme_recipe_report") }})
            {% endif %}
    )
select
    revenue_before_exchange_report.report_date,
    revenue_before_exchange_report.total_revenue_before_exchange
    / total_cost_per_day as "number_of_days_to_support_for_budget",
    (revenue_before_exchange_report.total_revenue_before_exchange / total_cost_per_day)
    * "revenue_per_day" as "future_revenue",
    (
        (
            revenue_before_exchange_report.total_revenue_before_exchange
            / total_cost_per_day
        )
        * "revenue_per_day"
    )
    / total_cost_per_day as "future_number_of_days_to_support_for_budget"
from {{ ref("revenue_before_exchange_report") }} as revenue_before_exchange_report
join
    {{ ref("cost_per_day_report") }} as cost_per_day_report
    on revenue_before_exchange_report.report_date = cost_per_day_report.report_date
order by revenue_before_exchange_report.report_date

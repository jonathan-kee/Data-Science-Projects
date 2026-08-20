{{
    config(
        materialized="incremental",
        unique_key=["report_date"],
        incremental_strategy="delete+insert",
    )
}}

with
    profit as (
        select "profit_per_day"
        from {{ ref("sme_recipe_report") }}
        where
            original_query = 'SME:6xALO-1xO-1xC-1xFLX=>4xAL'
            {% if var("date_part", none) is not none %}
                and report_date = '{{ var("date_part") }}'
            {% else %}
                and report_date
                = (select max(report_date) from {{ ref("sme_recipe_report") }})
            {% endif %}
    ),

    cost as (
        select
            report_date,
            "smeltor_cost_per_day",
            "workforce_cost_per_day",
            "total_cost_per_day"
        from {{ ref("cost_per_day_report") }}
        where
            {% if var("date_part", none) is not none %}
                report_date = '{{ var("date_part") }}'
            {% else %}
                report_date
                = (select max(report_date) from {{ ref("cost_per_day_report") }})
            {% endif %}
    )

-- ("profit per day" * 3) because I have 3 production of AL --
select
    cost.report_date,
    profit."profit_per_day",
    3 as "production_amount",
    cost."workforce_cost_per_day",
    -- The reason I did not include smeltor_cost_per_day was because profit per day
    -- already take into account
    (profit."profit_per_day" * 3) - cost."workforce_cost_per_day" as "total_profit_per_day"
from profit
cross join cost

{{
    config(
        materialized="incremental",
        unique_key=["report_date"],
        incremental_strategy="delete+insert",
    )
}}

with
    profit as (
        select "profit per day"
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
        select report_date, sum("Cost Per Day") as "cost_per_day"
        from {{ ref("workforce_price_report") }}
        where
            {% if var("date_part", none) is not none %}
                report_date = '{{ var("date_part") }}'
            {% else %}
                report_date
                = (select max(report_date) from {{ ref("workforce_price_report") }})
            {% endif %}
        group by report_date
    )

-- ("profit per day" * 3) because I have 3 production of AL --
select
    cost.report_date,
    "profit per day",
    3 as "production_amount",
    "cost_per_day",
    ("profit per day" * 3) - "cost_per_day" as "profit_per_day"
from profit
cross join cost

{{
    config(
        materialized='incremental',
        unique_key=['report_date'],
        incremental_strategy='delete+insert'
    )
}}

with
    sme_cost as (
        select "cost per day"
        from {{ ref("sme_cost_report") }}
        where
            original_query = 'SME:6xALO-1xO-1xC-1xFLX=>4xAL'
            {% if var("date_part", none) is not none %}
                and report_date = '{{ var("date_part") }}'
            {% else %}
                and report_date = (select max(report_date) from {{ ref("sme_cost_report") }})
            {% endif %}
    ),

    cost as (   
        select 
            report_date, 
            sum("Cost Per Day") as "cost_per_day"
        from {{ ref("workforce_price_report") }}
        where
            {% if var("date_part", none) is not none %}
                report_date = '{{ var("date_part") }}'
            {% else %}
                report_date = (select max(report_date) from {{ ref("workforce_price_report") }})
            {% endif %}
        group by report_date
    )

-- ("profit per day" * 3) because I have 3 production of AL --
select 
    cost.report_date, 
    sme_cost."cost per day" as "smeltor_cost_per_day",
    cost."cost_per_day" as "workforce_cost_per_day",
    sme_cost."cost per day" + cost."cost_per_day" as "total_cost_per_day"
from sme_cost
cross join cost
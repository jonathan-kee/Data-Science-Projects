{{
    config(
        materialized="incremental",
        unique_key=["report_date"],
        incremental_strategy="delete+insert",
    )
}}

with
    sme_cost as (
        select 
            report_date, -- ADDED: Need this here so we can join it to 'cost' later
            "cost per day"
        from {{ ref("sme_cost_report") }}
        where
            original_query = 'SME:6xALO-1xO-1xC-1xFLX=>4xAL'
            
            -- UPDATED: Support ranges first
            {% if var("start_date", none) is not none and var("end_date", none) is not none %}
                and report_date between '{{ var("start_date") }}' and '{{ var("end_date") }}'
            
            -- Fallback to your old single-day logic
            {% elif var("date_part", none) is not none %}
                and report_date = '{{ var("date_part") }}'
            
            -- Default when no vars are passed
            {% else %}
                and report_date = (select max(report_date) from {{ ref("sme_cost_report") }})
            {% endif %}
    ),

    cost as (
        select 
            report_date, 
            sum("cost_per_day_ask_price") as "cost_per_day"
        from {{ ref("workforce_price_report") }}
        where
            -- UPDATED: Support ranges first
            {% if var("start_date", none) is not none and var("end_date", none) is not none %}
                report_date between '{{ var("start_date") }}' and '{{ var("end_date") }}'
            
            -- Fallback to your old single-day logic
            {% elif var("date_part", none) is not none %}
                report_date = '{{ var("date_part") }}'
            
            -- Default when no vars are passed
            {% else %}
                report_date = (select max(report_date) from {{ ref("workforce_price_report") }})
            {% endif %}
        group by report_date
    )

-- ("profit per day" * 3) because I have 3 production of AL --
select
    cost.report_date,
    41.67 as "production_fee_per_day",
    sme_cost."cost per day" as "smeltor_cost_per_day",
    cost."cost_per_day" as "workforce_cost_per_day",
    sme_cost."cost per day" + cost."cost_per_day" + 41.67 as "total_cost_per_day"
from sme_cost
-- UPDATED: Replaced CROSS JOIN with an INNER JOIN to prevent row duplication on ranges
join cost 
    on sme_cost.report_date = cost.report_date
{{
    config(
        materialized="incremental",
        unique_key=["report_date"],
        incremental_strategy="delete+insert",
    )
}}

with
    profit as (
        select 
            report_date, -- ADDED: Need this here so we can join it to 'cost' later
            "revenue_per_day"
        from {{ ref("sme_recipe_report") }}
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
                and report_date = (select max(report_date) from {{ ref("sme_recipe_report") }})
            {% endif %}
    )

-- ("profit per day" * 3) because I have 3 production of AL --
select
    profit.report_date,
    profit."revenue_per_day",
    3 as "production_amount",
    profit."revenue_per_day" * 3 as "total_revenue_per_day"
from profit
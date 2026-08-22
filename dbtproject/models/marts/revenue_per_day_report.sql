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
            report_date,
            "revenue_per_day"
        from {{ ref("sme_recipe_report") }}
        where
            original_query = 'SME:6xALO-1xO-1xC-1xFLX=>4xAL'
            
            -- Support ranges first
            {% if var("start_date", none) is not none and var("end_date", none) is not none %}
                and report_date between '{{ var("start_date") }}' and '{{ var("end_date") }}'
            
            -- Fallback to your single-day logic
            {% elif var("date_part", none) is not none %}
                and report_date = '{{ var("date_part") }}'
            
            -- Default when no vars are passed
            {% else %}
                and report_date = (select max(report_date) from {{ ref("sme_recipe_report") }})
            {% endif %}
    )

select
    profit.report_date,
    profit."revenue_per_day",
    {{ var("production_amount") }} as "production_amount",
    profit."revenue_per_day" * {{ var("production_amount") }} as "total_revenue_per_day"
from profit
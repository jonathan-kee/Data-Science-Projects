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
            "profit_per_day"
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
    ),

    cost as (
        select
            report_date,
            "smeltor_cost_per_day",
            "workforce_cost_per_day",
            "total_cost_per_day"
        from {{ ref("cost_per_day_report") }}
        where
            -- UPDATED: Support ranges first
            {% if var("start_date", none) is not none and var("end_date", none) is not none %}
                report_date between '{{ var("start_date") }}' and '{{ var("end_date") }}'
            
            -- Fallback to your old single-day logic
            {% elif var("date_part", none) is not none %}
                report_date = '{{ var("date_part") }}'
            
            -- Default when no vars are passed
            {% else %}
                report_date = (select max(report_date) from {{ ref("cost_per_day_report") }})
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
-- UPDATED: Replaced CROSS JOIN with an INNER JOIN to prevent row duplication on ranges
join cost 
    on profit.report_date = cost.report_date
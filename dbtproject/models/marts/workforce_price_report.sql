{{
    config(
        materialized='incremental',
        unique_key=['report_date', 'material_ticker'],
        incremental_strategy='delete+insert'
    )
}}

select distinct 
    -- 1. Add a daily date identifier to stamp each snapshot
    cast('{{ var("date_part", run_started_at.strftime("%Y-%m-%d")) }}' as date) as report_date,
    stg_workforce."MaterialTicker" as material_ticker, 
    stg_workforce."DailyAmount" * stg_prices."AI1-AskPrice" as "Cost Per Day"
from {{ref("stg_workforce")}} as stg_workforce
join {{ref("stg_prices")}} as stg_prices
    on stg_workforce."MaterialTicker" = stg_prices."Ticker"
where 
{% if var("date_part", none) is not none %}
    stg_prices.date_part = '{{ var("date_part") }}'
{% else %}
    stg_prices.date_part = (select max("date_part") from {{ ref("stg_prices") }})
{% endif %}
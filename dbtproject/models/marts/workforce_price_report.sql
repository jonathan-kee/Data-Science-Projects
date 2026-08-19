{{
    config(
        materialized="incremental",
        unique_key=["report_date", "material_ticker"],
        incremental_strategy="delete+insert",
    )
}}

select distinct
    -- 1. Add a daily date identifier to stamp each snapshot
    cast(
        '{{ var("date_part", run_started_at.strftime("%Y-%m-%d")) }}' as date
    ) as report_date,
    stg_workforce."material_ticker" as material_ticker,
    stg_prices."ai1_ask_price" as "material_ask_price",
    stg_prices."ai1_bid_price" as "material_bid_price",
    stg_prices."ai1_ask_price" - stg_prices."ai1_bid_price" as "material_price_spead",
    stg_workforce."daily_amount" * stg_prices."ai1_ask_price" as "cost_per_day_ask_price",
    stg_workforce."daily_amount" * stg_prices."ai1_bid_price" as "cost_per_day_bid_price",
    (stg_workforce."daily_amount" * stg_prices."ai1_ask_price") - ( stg_workforce."daily_amount" * stg_prices."ai1_bid_price" ) as "cost_per_day_spread"
from {{ ref("stg_workforce") }} as stg_workforce
join
    {{ ref("stg_prices") }} as stg_prices
    on stg_workforce."material_ticker" = stg_prices."ticker"
where
    {% if var("date_part", none) is not none %}
        stg_prices.date_part = '{{ var("date_part") }}'
    {% else %}
        stg_prices.date_part = (select max("date_part") from {{ ref("stg_prices") }})
    {% endif %}

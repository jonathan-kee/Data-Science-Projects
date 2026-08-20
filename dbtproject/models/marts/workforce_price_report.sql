{{
    config(
        materialized="incremental",
        unique_key=["report_date", "material_ticker"],
        incremental_strategy="delete+insert",
    )
}}

select distinct
    -- UPDATED: Pull the date directly from the table rather than the variable 
    -- so that date ranges map correctly to their respective days.
    cast(stg_prices.date_part as date) as report_date,
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
    -- UPDATED: Support ranges first
    {% if var("start_date", none) is not none and var("end_date", none) is not none %}
        stg_prices.date_part between '{{ var("start_date") }}' and '{{ var("end_date") }}'
        
    -- Fallback to your old single-day logic
    {% elif var("date_part", none) is not none %}
        stg_prices.date_part = '{{ var("date_part") }}'
        
    -- Default when no vars are passed
    {% else %}
        stg_prices.date_part = (select max("date_part") from {{ ref("stg_prices") }})
    {% endif %}
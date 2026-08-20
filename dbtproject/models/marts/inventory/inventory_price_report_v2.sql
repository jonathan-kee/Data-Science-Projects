{{
    config(
        materialized="incremental",
        unique_key=["report_date", "material_ticker"],
        incremental_strategy="delete+insert",
    )
}}

with
    -- Inventory is a snapshot, so we always isolate its latest available date
    filter_stg_inventory as (
        select 
            "ticker", 
            "amount"
        from {{ ref("stg_inventory") }}
        where "storage_type" = 'STORE'
          and "date_part" = (select max("date_part") from {{ ref("stg_inventory") }})
    ),
    
    -- Prices support your date range or single-day variables
    filter_stg_prices as (
        select 
            "date_part", 
            "ticker", 
            "ai1_bid_price"
        from {{ ref("stg_prices") }}
        where
            {% if var("start_date", none) is not none and var("end_date", none) is not none %}
                "date_part" between '{{ var("start_date") }}' and '{{ var("end_date") }}'
            {% elif var("date_part", none) is not none %}
                "date_part" = '{{ var("date_part") }}'
            {% else %}
                -- Simplified: Uses stg_prices directly to avoid unnecessary upstream ref complexity
                "date_part" = (select max("date_part") from {{ ref("stg_prices") }})
            {% endif %}
    )

select distinct
    -- Stamp the report date using each day from the price range
    cast(filter_stg_prices."date_part" as date) as report_date,
    filter_stg_inventory."ticker" as material_ticker,
    filter_stg_inventory."amount",
    filter_stg_prices."ai1_bid_price",
    filter_stg_inventory."amount" * filter_stg_prices."ai1_bid_price" as "total_selling_price"
from filter_stg_prices
inner join
    filter_stg_inventory
    on filter_stg_prices."ticker" = filter_stg_inventory."ticker"
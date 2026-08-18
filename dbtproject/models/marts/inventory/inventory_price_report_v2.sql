with
    max_date_stg_inventory as (
        select max(date_part) as max_date_part from {{ ref("stg_inventory") }}
    ),
    max_date_stg_prices as (
        select max(dim_d.date_part) as max_date_part
        from {{ ref("fact_ticker_quotes") }} fct
        -- Skip joining dim_ticker --
        inner join
            {{ ref("dim_date_time") }} dim_d on fct.date_time_id = dim_d.date_time_id
    ),
    filter_stg_inventory_max_date as (
        select *
        from {{ ref("stg_inventory") }} as stg_inventory
        inner join max_date_stg_inventory on 1 = 1
        where
            stg_inventory."date_part" = max_date_stg_inventory."max_date_part"
            and stg_inventory."storage_type" = 'STORE'
    ),
    filter_stg_prices_max_date as (
        select *
        from {{ ref("stg_prices") }} as stg_prices
        inner join max_date_stg_prices on 1 = 1
        -- Cast the date to text to match stg_prices.date_part data type --
        where stg_prices."date_part" = max_date_stg_prices."max_date_part"::text
    ),
    total_selling_price_max_date as (
        select distinct
            filter_stg_inventory_max_date."ticker" as "Inventory Ticker",
            filter_stg_inventory_max_date."amount",
            filter_stg_inventory_max_date."amount"
            * filter_stg_prices_max_date."ai1_bid_price" as "total_selling_price"
        from filter_stg_inventory_max_date
        inner join
            filter_stg_prices_max_date
            on filter_stg_prices_max_date."ticker"
            = filter_stg_inventory_max_date."ticker"
        order by "total_selling_price" desc
    )
select *
from total_selling_price_max_date

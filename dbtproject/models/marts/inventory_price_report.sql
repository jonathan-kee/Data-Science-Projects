with
    max_date_stg_inventory as (
        select max(date_part) as max_date_part from {{ ref("stg_inventory") }}
    ),
    max_date_stg_prices as (
        select max(date_part) as max_date_part from {{ ref("stg_prices") }}
    ),
    filter_stg_inventory_max_date as (
        select *
        from {{ ref("stg_inventory") }} as stg_inventory
        inner join max_date_stg_inventory on 1 = 1
        where
            stg_inventory."date_part" = max_date_stg_inventory."max_date_part"
            and stg_inventory."StorageType" = 'STORE'
    ),
    filter_stg_prices_max_date as (
        select *
        from {{ ref("stg_prices") }} as stg_prices
        inner join max_date_stg_prices on 1 = 1
        where stg_prices."date_part" = max_date_stg_prices."max_date_part"
    ),
    total_selling_price_max_date as (
        select distinct
            filter_stg_inventory_max_date."Ticker" as "Inventory Ticker",
            filter_stg_inventory_max_date."Amount",
            filter_stg_inventory_max_date."Amount"
            * filter_stg_prices_max_date."AI1-BidPrice" as "total_selling_price"
        from filter_stg_inventory_max_date
        inner join
            filter_stg_prices_max_date
            on filter_stg_prices_max_date."Ticker"
            = filter_stg_inventory_max_date."Ticker"
        order by "total_selling_price" desc
    )
select *
from total_selling_price_max_date

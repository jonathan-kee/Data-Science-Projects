select
    stg_inventory."Ticker" as "Inventory Ticker",
    stg_inventory."Amount",
    stg_inventory."Amount" * stg_prices."AI1-BidPrice" as "total_selling_price"
from {{ ref("stg_inventory") }} as stg_inventory
inner join
    {{ ref("stg_prices") }} as stg_prices
    on stg_prices."Ticker" = stg_inventory."Ticker"
where stg_inventory."StorageType" = 'STORE'
order by "total_selling_price" desc

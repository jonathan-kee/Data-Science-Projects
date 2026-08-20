select
    workforce.material_ticker, inventory.amount / workforce.daily_amount as "days_left"
from {{ ref("stg_workforce") }} as workforce
join {{ ref("stg_inventory") }} as inventory on material_ticker = ticker

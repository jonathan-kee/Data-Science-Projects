with source_data as (select * from {{ ref("stg_prices") }})

select source_data.*
from source_data
where "Ticker" is not null

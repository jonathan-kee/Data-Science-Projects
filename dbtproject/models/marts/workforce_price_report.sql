select distinct stg_workforce."MaterialTicker", stg_workforce."DailyAmount" * stg_prices."AI1-AskPrice" as "Cost Per Day"
from {{ref("stg_workforce")}} as stg_workforce
join {{ref("stg_prices")}} as stg_prices
on stg_workforce."MaterialTicker" = stg_prices."Ticker"
where stg_prices.date_part = (select max("date_part") from {{ ref("stg_prices") }})
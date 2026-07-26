select "load time" as "Date", "AI1-BidPrice" as "Close"
from {{ ref("stg_prices") }}
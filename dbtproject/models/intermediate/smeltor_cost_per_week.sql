select sum(cost) as smeltor_cost_per_week
from
(
    select ai1_ask_price * ROUND(((10 * 1.67) * 7), 0) as cost
    from {{ ref("stg_prices_partition_date") }}
    where ticker in ('O')
    union all
    select ai1_ask_price *  ROUND(((10 * 1.67) * 7), 0)  as cost
    from {{ ref("stg_prices_partition_date") }}
    where ticker in ('C')
    union all
    select ai1_ask_price *  ROUND(((10 * 1.67) * 7), 0)  as cost
    from {{ ref("stg_prices_partition_date") }}
    where ticker in ('FLX')
 ) as materialCosts

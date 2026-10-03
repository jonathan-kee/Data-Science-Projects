select sum(cost) as workforce_cost_per_week
from
(
    select ai1_ask_price * ROUND(4.0 * 7, 0) as cost
    from {{ ref("stg_prices_partition_date") }}
    where ticker in ('COF')
    union all
    select ai1_ask_price * ROUND(31.6 * 7, 0) as cost
    from {{ ref("stg_prices_partition_date") }}
    where ticker in ('DW')
    union all
    select ai1_ask_price * ROUND(31.6 * 7, 0) as cost
    from {{ ref("stg_prices_partition_date") }}
    where ticker in ('RAT')
    union all
    select ai1_ask_price * ROUND(4 * 7, 0) as cost
    from {{ ref("stg_prices_partition_date") }}
    where ticker in ('OVE')
    union all
    select ai1_ask_price * ROUND(1.6 * 7, 0) as cost
    from {{ ref("stg_prices_partition_date") }}
    where ticker in ('PWO')
 ) as workforceCosts

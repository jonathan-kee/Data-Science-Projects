select *
from {{ ref("stg_prices") }} as stg_prices
where
    {% if var("date_part", none) is not none %}
        stg_prices.date_part = '{{ var("date_part") }}'
    {% else %}
        stg_prices.date_part = (select max(date_part) from {{ ref("stg_prices") }})
    {% endif %}

select
    -- Descriptive columns from Dimension tables
    dim_t."ticker",
    dim_d."date_part",
    dim_d."time_part",
    dim_d."timezone",
    dim_i."interval_name",

    -- Metrics from the Fact table
    fct."open",
    fct."close",
    fct."high",
    fct."low",
    fct."volume",
    fct."traded"
from {{ ref("fact_fs_market_data") }} as fct
-- Join the Asset Dimension
join {{ ref("dim_ticker") }} as dim_t on fct."ticker" = dim_t."ticker"
-- Join the Datetime Dimension
join {{ ref("dim_fs_datetime") }} as dim_d on fct."date_epoch_ms" = dim_d."date_epoch_ms"
-- Join the Interval Dimension
join
    {{ ref("dim_fs_interval") }} as dim_i on fct."interval_name" = dim_i."interval_name"

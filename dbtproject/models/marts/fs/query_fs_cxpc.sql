select
    -- Descriptive columns from Dimension tables
    dim_t."ticker",
    dim_d."date_part",
    dim_d."time_part",
    dim_d."timezone",
    dim_i."interval_name",

    -- Metrics from the Fact table
    fct."Open",
    fct."Close",
    fct."High",
    fct."Low",
    fct."Volume",
    fct."Traded"
from {{ ref("fact_fs_market_data") }} as fct
-- Join the Asset Dimension
join {{ ref("dim_ticker") }} as dim_t on fct."ticker" = dim_t."ticker"
-- Join the Datetime Dimension
join {{ ref("dim_fs_datetime") }} as dim_d on fct."DateEpochMs" = dim_d."DateEpochMs"
-- Join the Interval Dimension
join
    {{ ref("dim_fs_interval") }} as dim_i on fct."interval_name" = dim_i."interval_name"

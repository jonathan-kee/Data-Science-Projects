SELECT 
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
    fct."Volume"
FROM {{ ref('fact_market_data') }} AS fct
-- Join the Asset Dimension
JOIN {{ ref('dim_ticker') }}  AS dim_t 
    ON fct."ticker" = dim_t."ticker"
-- Join the Datetime Dimension
JOIN {{ ref('dim_datetime') }}  AS dim_d 
    ON fct."DateEpochMs" = dim_d."DateEpochMs"
-- Join the Interval Dimension
JOIN {{ ref('dim_interval') }} AS dim_i 
    ON fct."interval_name" = dim_i."interval_name"
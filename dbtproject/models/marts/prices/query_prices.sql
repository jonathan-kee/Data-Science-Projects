select
    -- Dimension attributes (Human-readable metadata)
    dim_t.ticker,
    dim_d.date_part,
    dim_d.time_part,
    dim_d.load_timestamp,
    fct.provider_code,
    
    -- Fact measures (Quantitative financial metrics)
    fct.mmbuy,
    fct.mmsell,
    fct.average_price,
    fct.ask_amt,
    fct.ask_price,
    fct.ask_avail,
    fct.bid_amt,
    fct.bid_price,
    fct.bid_avail

from {{ ref('fact_ticker_quotes') }} fct
inner join {{ ref('dim_ticker') }} dim_t
    on fct.ticker_id = dim_t.ticker_id
inner join {{ ref('dim_date_time') }} dim_d 
    on fct.date_time_id = dim_d.date_time_id
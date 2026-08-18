select
    -- Dimension attributes (Human-readable metadata)
    t.ticker,
    dt.quote_date,
    dt.time_part,
    dt.load_timestamp,
    f.provider_code,
    
    -- Fact measures (Quantitative financial metrics)
    f.mmbuy,
    f.mmsell,
    f.average_price,
    f.ask_amt,
    f.ask_price,
    f.ask_avail,
    f.bid_amt,
    f.bid_price,
    f.bid_avail

from {{ ref('fact_ticker_quotes') }} f
inner join {{ ref('dim_ticker') }} t 
    on f.ticker_id = t.ticker_id
inner join {{ ref('dim_date_time') }} dt 
    on f.date_time_id = dt.date_time_id
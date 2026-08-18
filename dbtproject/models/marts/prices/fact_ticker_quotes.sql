{{
    config(
        materialized='incremental',
        unique_key=['ticker_id', 'date_time_id', 'provider_code']
    )
}}

with stg as (
    select * from {{ ref('stg_prices') }}
    
    {% if is_incremental() %}
    where load_time::timestamp > (
        select max(dt.load_timestamp) 
        from {{ this }} f
        inner join {{ ref('dim_date_time') }} dt 
            on f.date_time_id = dt.date_time_id
    )
    {% endif %}
),

tickers as (
    select * from {{ ref('dim_ticker') }}
),

date_times as (
    select * from {{ ref('dim_date_time') }}
),

unpivoted as (
    -- AI1 Provider
    select 
        ticker, date_part, time_part, load_time, mmbuy, mmsell,
        'ai1' as provider_code, 
        ai1_average as average_price, ai1_ask_amt as ask_amt, ai1_ask_price as ask_price, 
        ai1_ask_avail as ask_avail, ai1_bid_amt as bid_amt, ai1_bid_price as bid_price, ai1_bid_avail as bid_avail 
    from stg
    
    union all
    
    -- CI1 Provider
    select 
        ticker, date_part, time_part, load_time, mmbuy, mmsell,
        'ci1' as provider_code, 
        ci1_average as average_price, ci1_ask_amt as ask_amt, ci1_ask_price as ask_price, 
        ci1_ask_avail as ask_avail, ci1_bid_amt as bid_amt, ci1_bid_price as bid_price, ci1_bid_avail as bid_avail 
    from stg
    
    union all
    
    -- CI2 Provider
    select 
        ticker, date_part, time_part, load_time, mmbuy, mmsell,
        'ci2' as provider_code, 
        ci2_average as average_price, ci2_ask_amt as ask_amt, ci2_ask_price as ask_price, 
        ci2_ask_avail as ask_avail, ci2_bid_amt as bid_amt, ci2_bid_price as bid_price, ci2_bid_avail as bid_avail 
    from stg
    
    union all
    
    -- NC1 Provider
    select 
        ticker, date_part, time_part, load_time, mmbuy, mmsell,
        'nc1' as provider_code, 
        nc1_average as average_price, nc1_ask_amt as ask_amt, nc1_ask_price as ask_price, 
        nc1_ask_avail as ask_avail, nc1_bid_amt as bid_amt, nc1_bid_price as bid_price, nc1_bid_avail as bid_avail 
    from stg
    
    union all
    
    -- NC2 Provider
    select 
        ticker, date_part, time_part, load_time, mmbuy, mmsell,
        'nc2' as provider_code, 
        nc2_average as average_price, nc2_ask_amt as ask_amt, nc2_ask_price as ask_price, 
        nc2_ask_avail as ask_avail, nc2_bid_amt as bid_amt, nc2_bid_price as bid_price, nc2_bid_avail as bid_avail 
    from stg
    
    union all
    
    -- IC1 Provider
    select 
        ticker, date_part, time_part, load_time, mmbuy, mmsell,
        'ic1' as provider_code, 
        ic1_average as average_price, ic1_ask_amt as ask_amt, ic1_ask_price as ask_price, 
        ic1_ask_avail as ask_avail, ic1_bid_amt as bid_amt, ic1_bid_price as bid_price, ic1_bid_avail as bid_avail 
    from stg
)

select
    t.ticker_id,
    dt.date_time_id,
    u.provider_code,
    u.mmbuy,
    u.mmsell,
    u.average_price,
    u.ask_amt,
    u.ask_price,
    u.ask_avail,
    u.bid_amt,
    u.bid_price,
    u.bid_avail
from unpivoted u
inner join tickers t 
    on u.ticker = t.ticker
inner join date_times dt 
    on u.date_part::date = dt.quote_date
    and u.time_part = dt.time_part 
    and u.load_time::timestamp = dt.load_timestamp
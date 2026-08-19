{{ config(materialized="table") }}

with
    distinct_tickers as (
        select distinct ticker from {{ ref("stg_prices") }} where ticker is not null
    )

select {{ dbt_utils.generate_surrogate_key(["ticker"]) }} as ticker_id, ticker
from distinct_tickers

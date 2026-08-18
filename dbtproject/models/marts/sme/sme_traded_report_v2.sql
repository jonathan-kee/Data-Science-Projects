with
    rank_all_sources as (
        select
            dim_t."ticker",
            sum(fct."Traded") as "total_traded",
            dense_rank() over (order by sum(fct."Traded") desc) as "traded_rank"
        from {{ ref("fact_sme_market_data") }} as fct
        -- Join the Asset Dimension
        join {{ ref("dim_ticker") }} as dim_t on fct."ticker" = dim_t."ticker"
        -- Join the Datetime Dimension
        join
            {{ ref("dim_sme_datetime") }} as dim_d
            on fct."DateEpochMs" = dim_d."DateEpochMs"
        -- Join the Interval Dimension
        join
            {{ ref("dim_sme_interval") }} as dim_i
            on fct."interval_name" = dim_i."interval_name"
        group by dim_t."ticker"
    )
select *
from rank_all_sources
order by "traded_rank" asc

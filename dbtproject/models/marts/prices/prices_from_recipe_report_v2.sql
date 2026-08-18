{{
    config(
        materialized='incremental',
        unique_key=['date_part', 'ticker'],
        incremental_strategy='delete+insert'
    )
}}

with
    all_tables as (
        select
            stg_prices.date_part,
            stg_prices."ticker",
            -- Bid Price is buyer, You sell to them --
            stg_prices."bid_price" as "ai1_bid_price",
            -- Ask Price is seller, You buy from them --
            case
                when recipe_report."input_materials_AI1_AskPrice_per_unit" is not null
                then recipe_report."input_materials_AI1_AskPrice_per_unit"
                else stg_prices."ask_price"
            end as "ai1_ask_price"
        from
            (
                select
                    -- Dimension attributes (Human-readable metadata)
                    dim_t.ticker,
                    dim_d.date_part,
                    fct.bid_price,
                    -- Fact measures (Quantitative financial metrics)
                    fct.ask_price
                from {{ ref('fact_ticker_quotes') }} fct
                inner join
                    {{ ref('dim_ticker') }} dim_t on fct.ticker_id = dim_t.ticker_id
                inner join
                    {{ ref('dim_date_time') }} dim_d
                    on fct.date_time_id = dim_d.date_time_id
                where fct.provider_code = 'ai1'
            ) as stg_prices
        inner join
            {{ ref("sme_recipe_report") }} as recipe_report
            on recipe_report."Output_Material" = stg_prices."ticker"
        where
            {% if var("date_part", none) is not none %}
                stg_prices.date_part = '{{ var("date_part") }}'
                and recipe_report.report_date = '{{ var("date_part") }}'
            {% else %}
                stg_prices.date_part = (
                    select max(dim_d.date_part) 
                    from {{ ref('fact_ticker_quotes') }} fct
                    inner join {{ ref('dim_date_time') }} dim_d on fct.date_time_id = dim_d.date_time_id
                )
                and recipe_report.report_date = (
                    select max(dim_d.date_part) 
                    from {{ ref('fact_ticker_quotes') }} fct
                    inner join {{ ref('dim_date_time') }} dim_d on fct.date_time_id = dim_d.date_time_id
                )
            {% endif %}
    ),
    tofilter as (
        select
            date_part,
            "ticker",
            max("ai1_bid_price") as "ai1_bid_price",
            min("ai1_ask_price") as "ai1_ask_price"
        from all_tables
        group by date_part, "ticker"
    )
select *
from tofilter
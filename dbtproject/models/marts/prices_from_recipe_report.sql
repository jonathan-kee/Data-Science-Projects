with
    all_tables as (
        select
            stg_prices.date_part,
            stg_prices."ticker",
            -- Bid Price is buyer, You sell to them --
            stg_prices."ai1_bid_price",
            -- Ask Price is seller, You buy from them --
            case
                when recipe_report."input_materials_AI1_AskPrice_per_unit" is not null
                then recipe_report."input_materials_AI1_AskPrice_per_unit"
                else stg_prices."ai1_ask_price"
            end as "ai1_ask_price"
        from {{ ref("stg_prices") }} as stg_prices
        inner join
            {{ ref("recipe_report") }} as recipe_report
            on recipe_report."Output_Material" = stg_prices."ticker"
        where
            stg_prices.date_part
            = (select max(stg_prices.date_part) from {{ ref("stg_prices") }})
    ),
    tofilter as (
        select date_part, "ticker", MAX("ai1_bid_price") AS "ai1_bid_price", MIN("ai1_ask_price") AS "ai1_ask_price"
        from all_tables
        group by date_part, "ticker"
    )
select *
from tofilter

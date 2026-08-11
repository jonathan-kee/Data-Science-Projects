with
    all_tables as (
        select
            stg_prices.date_part,
            stg_prices."Ticker",
            -- Bid Price is buyer, You sell to them --
            stg_prices."AI1-BidPrice",
            -- Ask Price is seller, You buy from them --
            case
                when recipe_report."input_materials_AI1_AskPrice_per_unit" is not null
                then recipe_report."input_materials_AI1_AskPrice_per_unit"
                else stg_prices."AI1-AskPrice"
            end as "AI1-AskPrice"
        from {{ ref("stg_prices") }} as stg_prices
        left join
            {{ ref("recipe_report") }} as recipe_report
            on recipe_report."Output_Material" = stg_prices."Ticker"
        where
            stg_prices.date_part
            = (select max(stg_prices.date_part) from {{ ref("stg_prices") }})
    ),
    tofilter as (
        select date_part, "Ticker", MAX("AI1-BidPrice") AS "AI1-BidPrice", MIN("AI1-AskPrice") AS "AI1-AskPrice"
        from all_tables
        group by date_part, "Ticker"
    )
select *
from tofilter

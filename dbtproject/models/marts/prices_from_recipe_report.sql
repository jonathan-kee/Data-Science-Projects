with
    all_tables as (
        select
            stg_prices.date_part,
            stg_prices."Ticker",
            stg_prices."AI1-BidPrice",
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
        select *
        from all_tables
        -- Did filter below to make sure there's only one row to not cause issue
        -- Not sure why TI has two 1887
        where
            "AI1-AskPrice"
            not in (459.3333333333333, 761.3333333333334, 1887, 1870, 4304.5)
    )
select *
from tofilter

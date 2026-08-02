with
    habitat_total_buying_price as (
        select distinct
            raw.stg_prices."Ticker",
            raw.building_costs."amount"
            * raw.stg_prices."AI1-AskPrice" as "total buying price individually"
        from {{ ref("stg_prices") }}
        inner join
            raw.building_costs
            on raw.stg_prices."Ticker" = raw.building_costs."commodity_ticker"
        where
            raw.stg_prices.date_part = '2026-07-30'
            and raw.building_costs."buildingId" in ('79f8f9bf4a56c464041c18995b00c16e')
    ),
    habitat_total as (
        select sum("total buying price individually") as "total buying price"
        from habitat_total_buying_price
    ),
    two_habitat as (
        select
            habitat_total."total buying price" * 2 as "two habitant total buying price"
        from habitat_total
    ),
    inesmith_total_buying_price as (
        select distinct
            raw.stg_prices."Ticker",
            raw.building_costs."amount"
            * raw.stg_prices."AI1-AskPrice" as "total buying price individually"
        from {{ ref("stg_prices") }}
        inner join
            raw.building_costs
            on raw.stg_prices."Ticker" = raw.building_costs."commodity_ticker"
        where
            raw.stg_prices.date_part = '2026-07-30'
            and raw.building_costs."buildingId" in ('2d08c72c3801061979897525a8915fb2')
    ),
    finesmith_total as (
        select sum("total buying price individually") as "total buying price"
        from inesmith_total_buying_price
    ),
    total as (
        select
            two_habitat."two habitant total buying price"
            + finesmith_total."total buying price"
        from two_habitat
        inner join finesmith_total on 1 = 1
    )
select *
from total

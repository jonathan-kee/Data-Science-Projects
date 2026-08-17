with
    habitat_total_buying_price as (
        select distinct
            raw.stg_prices."ticker",
            raw.building_costs."amount"
            * raw.stg_prices."ai1_ask_price" as "total buying price individually"
        from {{ ref("stg_prices") }}
        inner join
            raw.building_costs
            on raw.stg_prices."ticker" = raw.building_costs."commodity_ticker"
        where
            -- maximum date --
            raw.stg_prices.date_part
            = (select max("date_part") from {{ ref("stg_prices") }})
            -- habitat id --
            and raw.building_costs."building_id" in ('79f8f9bf4a56c464041c18995b00c16e')
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
    finesmith_total_buying_price as (
        select distinct
            raw.stg_prices."ticker",
            raw.building_costs."amount"
            * raw.stg_prices."ai1_ask_price" as "total buying price individually"
        from {{ ref("stg_prices") }}
        inner join
            raw.building_costs
            on raw.stg_prices."ticker" = raw.building_costs."commodity_ticker"
        where
            -- maximum date --
            raw.stg_prices.date_part
            = (select max("date_part") from {{ ref("stg_prices") }})
            -- habitat id --
            and raw.building_costs."building_id" in ('2d08c72c3801061979897525a8915fb2')
    ),
    finesmith_total as (
        select sum("total buying price individually") as "total buying price"
        from finesmith_total_buying_price
    ),
    total as (
        select
            two_habitat."two habitant total buying price"
            + finesmith_total."total buying price" as "total buying price of goal"
        from two_habitat
        inner join finesmith_total on 1 = 1
    )
select *
from total

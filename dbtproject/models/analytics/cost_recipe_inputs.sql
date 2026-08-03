with
    joiningtable as (
        select raw.stg_recipe_inputs_time.*, "AI1-AskPrice"
        from raw.stg_recipe_inputs_time
        inner join
            raw.stg_prices
            on raw.stg_recipe_inputs_time."materialinput" = raw.stg_prices."Ticker"
        where
            -- maximum date --
            raw.stg_prices.date_part = (select max("date_part") from raw.stg_prices)

    ),
    filtertable as (
        select * from joiningtable 
        where prefix = 'SME' 
        and materialoutput = 'AL' 
        -- For matierialoutput like AL
        -- and materialoutputquantity = 4
    ),
    total_a1_askprice_per_unit as (
        select SUM("AI1-AskPrice") / MAX("materialoutputquantity") as "total_a1_askprice" from filtertable
    )
select "total_a1_askprice"
from total_a1_askprice_per_unit;


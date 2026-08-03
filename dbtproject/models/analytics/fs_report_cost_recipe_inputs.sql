with
    joining_table as (
        select raw.stg_recipe_inputs_time.*, "AI1-AskPrice"
        from raw.stg_recipe_inputs_time
        inner join
            raw.stg_prices
            on raw.stg_recipe_inputs_time."materialinput" = raw.stg_prices."Ticker"
        where
            -- maximum date --
            raw.stg_prices.date_part = (select max("date_part") from raw.stg_prices)
            and raw.stg_recipe_inputs_time."prefix" = 'FS'
    ),
    which_material as (
        select
            *
        from joining_table
        inner join
            raw.total_cost_recipe_inputs
            on joining_table."materialinput"
            = raw.total_cost_recipe_inputs."materialoutput"    )
    total_cost_recipe as (
        select
            joining_table."original_query",
            sum(raw.total_cost_recipe_inputs."total_a1_askprice") as "total price to buy",
            sum(raw.total_cost_recipe_inputs."minutes per order") as "minutes per order"
        from joining_table
        inner join
            raw.total_cost_recipe_inputs
            on joining_table."materialinput"
            = raw.total_cost_recipe_inputs."materialoutput"
        group by joining_table."original_query"
    )
select *
from total_cost_recipe

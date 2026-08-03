with
    joining_table as (
        select raw.stg_recipe_inputs_time.*, "AI1-AskPrice"
        from raw.stg_recipe_inputs_time
        -- joining on "materialinput"
        inner join
            raw.stg_prices
            on raw.stg_recipe_inputs_time."materialinput" = raw.stg_prices."Ticker"
        where
            -- maximum date --
            raw.stg_prices.date_part = (select max("date_part") from raw.stg_prices)
    ),
    filtertable as (
        select joining_table.*, joining_table."time_ms" / 60000.0 AS "minutes"
        from joining_table
        where
            prefix = 'SME'
            and materialoutput = 'AL'
            -- For matierialoutput like AL
            and materialoutputquantity = 4

        union all

        select joining_table.*, joining_table."time_ms" / 60000.0 AS "minutes"
        from joining_table
        where prefix = 'SME' and materialoutput = 'AU'

        union all

        select joining_table.*, joining_table."time_ms" / 60000.0 AS "minutes"
        from joining_table
        where prefix = 'SME' and materialoutput = 'CF'

        union all

        select joining_table.*, joining_table."time_ms" / 60000.0 AS "minutes"
        from joining_table
        where prefix = 'SME' and materialoutput = 'CU'

        union all

        select joining_table.*, joining_table."time_ms" / 60000.0 AS "minutes"
        from joining_table
        where prefix = 'SME' and materialoutput = 'FE' and materialoutputquantity = 4

        union all

        select joining_table.*, joining_table."time_ms" / 60000.0 AS "minutes"
        from joining_table
        where prefix = 'SME' and materialoutput = 'LI'

        union all

        select joining_table.*, joining_table."time_ms" / 60000.0 AS "minutes"
        from joining_table
        where prefix = 'SME' and materialoutput = 'RE' and materialoutputquantity = 5

        union all

        select joining_table.*, joining_table."time_ms" / 60000.0 AS "minutes"
        from joining_table
        where prefix = 'SME' and materialoutput = 'S'

        union all

        select joining_table.*, joining_table."time_ms" / 60000.0 AS "minutes"
        from joining_table
        where
            prefix = 'SME'
            and materialoutput = 'SI'
            and original_query = 'SME:3xSIO-1xAL=>1xSI'

        union all

        select joining_table.*, joining_table."time_ms" / 60000.0 AS "minutes"
        from joining_table
        where prefix = 'SME' and materialoutput = 'STL'

        union all

        select joining_table.*, joining_table."time_ms" / 60000.0 AS "minutes"
        from joining_table
        where
            prefix = 'SME'
            and materialoutput = 'TI'
            and original_query = 'SME:4xTIO-1xC-1xO-1xNA=>2xTI'
    ),
    group_by_total as (
        select
            filtertable."original_query",
            filtertable."prefix",
            filtertable."materialinput",
            filtertable."materialinputquantity",
            -- Ask Price is seller, You buy from them --
            filtertable."AI1-AskPrice",
            sum("AI1-AskPrice") / max("materialinputquantity") as "total_a1_askprice",
            max("minutes") as "minutes per order",
            CONCAT(
        CAST(MAX(minutes) AS INT) / 60, ' hours ', 
        CAST(MAX(minutes) AS INT) % 60, ' mins'
        ) AS "hour and minutes" 
        from filtertable 
        group by
            filtertable."original_query",
            filtertable."prefix",
            filtertable."materialinput",
            filtertable."materialinputquantity",
            filtertable."AI1-AskPrice"
        order by 1
    )
select *
from group_by_total

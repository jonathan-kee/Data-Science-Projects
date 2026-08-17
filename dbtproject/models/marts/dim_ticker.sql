with
    source_data as (
        select distinct "ticker" as "ticker"
        from {{ ref("stg_prices") }}
        where "ticker" is not null
    )

select
    -- Natural Primary Key for the Dimension
    "ticker",

    -- Metadata / Placeholder attributes (e.g., sector, company_name)
    current_timestamp as created_at

from source_data

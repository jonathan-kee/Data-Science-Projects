with
    source_data as (
        select distinct "Ticker" as "Ticker"
        from {{ ref("stg_prices") }}
        where "Ticker" is not null
    )

select
    -- Natural Primary Key for the Dimension
    "Ticker",

    -- Metadata / Placeholder attributes (e.g., sector, company_name)
    current_timestamp as created_at

from source_data

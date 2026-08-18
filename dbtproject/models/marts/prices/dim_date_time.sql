{{
    config(
        materialized='table'
    )
}}

with distinct_timestamps as (
    select distinct
        date_part,
        time_part,
        file_date,
        load_time
    from {{ ref('stg_prices') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['date_part', 'time_part', 'load_time']) }} as date_time_id,
    date_part::date as date_part,
    time_part,
    file_date::date as file_date,
    load_time::timestamp as load_timestamp
from distinct_timestamps
with
    source as (
        select * from {{ source("prosperous_universe_sources", "cxpc_alo_ai1_raw") }}
    ),
    renamed as (
        select
            to_timestamp("DateEpochMs" / 1000) at time zone 'UTC' as "timezone",
            (to_timestamp("DateEpochMs" / 1000) at time zone 'UTC')::date as date_part,
            (to_timestamp("DateEpochMs" / 1000) at time zone 'UTC')::time as time_part,
            {{ adapter.quote("Interval") }},
            {{ adapter.quote("DateEpochMs") }},
            {{ adapter.quote("Open") }},
            {{ adapter.quote("Close") }},
            {{ adapter.quote("High") }},
            {{ adapter.quote("Low") }},
            {{ adapter.quote("Volume") }},
            {{ adapter.quote("Traded") }}

        from source
    )
select *
from renamed

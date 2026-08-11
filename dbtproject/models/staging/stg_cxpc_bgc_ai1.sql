with source as (
        select * from {{ source('prosperous_universe_sources', 'cxpc_bgc_ai1_raw') }}
  ),
  renamed as (
      select
'BGC' as "ticker",
to_timestamp("DateEpochMs" / 1000) AT TIME ZONE 'UTC' as "timezone", 
(to_timestamp("DateEpochMs" / 1000) AT TIME ZONE 'UTC')::DATE AS date_part,
(to_timestamp("DateEpochMs" / 1000) AT TIME ZONE 'UTC')::TIME AS time_part,
*

      from source
  )
  select * from renamed
    
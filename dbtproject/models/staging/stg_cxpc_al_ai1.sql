SELECT 
'AL' as "ticker",
to_timestamp("date_epoch_ms" / 1000) AT TIME ZONE 'UTC' as "timezone", 
(to_timestamp("date_epoch_ms" / 1000) AT TIME ZONE 'UTC')::DATE AS date_part,
(to_timestamp("date_epoch_ms" / 1000) AT TIME ZONE 'UTC')::TIME AS time_part,
*
FROM {{source('prosperous_universe_sources','cxpc_al_ai1_raw')}}
WHERE "high" != 3000 -- Filter out outlier
and "high" != 2400 -- Filter out outlier
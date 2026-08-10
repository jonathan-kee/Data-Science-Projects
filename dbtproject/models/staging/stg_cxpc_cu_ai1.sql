SELECT 
'al' as "ticker",
to_timestamp("DateEpochMs" / 1000) AT TIME ZONE 'UTC' as "timezone", 
(to_timestamp("DateEpochMs" / 1000) AT TIME ZONE 'UTC')::DATE AS date_part,
(to_timestamp("DateEpochMs" / 1000) AT TIME ZONE 'UTC')::TIME AS time_part,
*
FROM {{source('prosperous_universe_sources','cxpc_cu_ai1_raw')}}
WHERE "High" != 3000 -- Filter out outlier
and "High" != 2400 -- Filter out outlier
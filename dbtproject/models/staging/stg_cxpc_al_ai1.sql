select to_timestamp("DateEpochMs" / 1000) AT TIME ZONE 'UTC' as "timezone", 
(to_timestamp("DateEpochMs" / 1000) AT TIME ZONE 'UTC')::DATE AS date_part,
(to_timestamp("DateEpochMs" / 1000) AT TIME ZONE 'UTC')::TIME AS time_part,
*
from {{source('prosperous_universe sources','cxpc_al_ai1_raw')}}
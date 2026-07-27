select to_timestamp("DateEpochMs" / 1000) AT TIME ZONE 'UTC' as "timezone", *
from {{source('prosperous_universe sources','cxpc_al_ai1_raw')}}
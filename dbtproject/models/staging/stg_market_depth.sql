select to_char(current_timestamp, 'DD/MM/YYYY HH24:MI:SS') as loaded_time, *
from {{source('prosperous_universe sources','market_depth_raw')}}
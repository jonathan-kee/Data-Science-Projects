{{ config(materialized="table") }}

with source_data as (select * from {{ ref("fs_cxpc") }})

select distinct
    source_data."DateEpochMs",
    source_data."timezone",
    source_data."date_part",
    source_data."time_part"
from source_data
where source_data."DateEpochMs" is not null

{{ config(materialized="table") }}

with source_data as (select * from {{ ref("fs_cxpc") }})

select distinct source_data."Interval" as interval_name
from source_data
where source_data."Interval" is not null

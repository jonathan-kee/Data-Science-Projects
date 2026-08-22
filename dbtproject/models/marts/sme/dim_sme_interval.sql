{{ config(materialized="table") }}

with source_data as (select * from {{ ref("sme_cxpc") }})

select distinct source_data."interval" as interval_name
from source_data
where source_data."interval" is not null

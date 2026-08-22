{{ config(materialized="table") }}

with source_data as (select * from {{ ref("sme_cxpc") }})

select
    -- Foreign Keys linking to your dimensions
    source_data."ticker",
    source_data."date_epoch_ms",
    source_data."interval" as interval_name,

    -- Fact Metrics
    source_data."open",
    source_data."close",
    source_data."high",
    source_data."low",
    source_data."volume",
    source_data."traded",

    -- Audit / Metadata columns
    source_data."file_date"
from source_data

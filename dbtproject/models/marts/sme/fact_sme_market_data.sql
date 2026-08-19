{{ config(materialized="table") }}

with source_data as (select * from {{ ref("sme_cxpc") }})

select
    -- Foreign Keys linking to your dimensions
    source_data."ticker",
    source_data."DateEpochMs",
    source_data."Interval" as interval_name,

    -- Fact Metrics
    source_data."Open",
    source_data."Close",
    source_data."High",
    source_data."Low",
    source_data."Volume",
    source_data."Traded",

    -- Audit / Metadata columns
    source_data."file_date"
from source_data

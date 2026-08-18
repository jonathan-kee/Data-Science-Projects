{{ config(
    materialized='table'
) }}

WITH source_data AS (
    SELECT * FROM {{ ref('sme_cxpc') }}
)

SELECT 
    -- Foreign Keys linking to your dimensions
    source_data."ticker",
    source_data."DateEpochMs",
    source_data."Interval" AS interval_name,
    
    -- Fact Metrics
    source_data."Open",
    source_data."Close",
    source_data."High",
    source_data."Low",
    source_data."Volume",
    source_data."Traded",
    
    -- Audit / Metadata columns
    source_data."file_date"
FROM source_data
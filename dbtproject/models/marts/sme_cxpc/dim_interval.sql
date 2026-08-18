{{ config(
    materialized='table'
) }}

WITH source_data AS (
    SELECT * FROM {{ ref('sme_cxpc') }}
)

SELECT DISTINCT 
    source_data."Interval" AS interval_name
FROM source_data
WHERE source_data."Interval" IS NOT NULL
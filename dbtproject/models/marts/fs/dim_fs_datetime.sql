{{ config(
    materialized='table'
) }}

WITH source_data AS (
    SELECT * FROM {{ ref('fs_cxpc') }}
)

SELECT DISTINCT 
    source_data."DateEpochMs",
    source_data."timezone",
    source_data."date_part",
    source_data."time_part"
FROM source_data
WHERE source_data."DateEpochMs" IS NOT NULL
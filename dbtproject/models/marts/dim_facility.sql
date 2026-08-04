WITH source_data AS (

    SELECT DISTINCT
        "NaturalId"    AS natural_id,
        "Name"         AS facility_name,
        "StorageType"  AS storage_type
    FROM {{ ref('stg_inventory') }}
    WHERE "NaturalId" IS NOT NULL

)

SELECT
    -- Deterministic surrogate primary key using MD5
    MD5(
        COALESCE(CAST(natural_id AS VARCHAR), '') || '-' ||
        COALESCE(CAST(storage_type AS VARCHAR), '')
    ) AS facility_key,

    natural_id,
    facility_name,
    storage_type,
    CURRENT_TIMESTAMP AS created_at
FROM source_data
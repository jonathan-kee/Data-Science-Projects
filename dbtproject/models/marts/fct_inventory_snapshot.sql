WITH stg_data AS (

    SELECT
        CAST("date_part" AS DATE)           AS snapshot_date,
        CAST("time_part" AS TIME)           AS snapshot_time,
        TO_TIMESTAMP("load time", 'DD/MM/YYYY HH24:MI:SS')    AS loaded_at,
        "Username"                          AS loaded_by_user,
        "NaturalId"                         AS natural_id,
        "StorageType"                       AS storage_type,
        "Ticker"                            AS ticker,
        "Amount"                            AS item_amount
    FROM {{ ref('stg_inventory') }}

),

dim_facility AS (

    SELECT 
        facility_key,
        natural_id,
        storage_type
    FROM {{ ref('dim_facility') }}

)

SELECT
    -- Primary Foreign Key referencing dim_facility
    dim.facility_key,

    -- Dimensional details & degenerate dimensions
    stg.ticker,
    stg.loaded_by_user,

    -- Timestamps / Date references
    stg.snapshot_date,
    stg.snapshot_time,
    stg.loaded_at,

    -- Fact / Numeric Measure
    stg.item_amount

FROM stg_data stg
LEFT JOIN dim_facility dim
    ON stg.natural_id = dim.natural_id
   AND stg.storage_type = dim.storage_type
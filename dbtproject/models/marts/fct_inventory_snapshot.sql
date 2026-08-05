with
    stg_data as (

        select
            cast("date_part" as date) as snapshot_date,
            cast("time_part" as time) as snapshot_time,
            to_timestamp("load time", 'DD/MM/YYYY HH24:MI:SS') as loaded_at,
            "Username" as loaded_by_user,
            "NaturalId" as natural_id,
            "StorageType" as storage_type,
            "Ticker" as ticker,
            "Amount" as item_amount
        from {{ ref("stg_inventory") }}

    ),

    dim_facility as (

        select facility_key, natural_id, storage_type from {{ ref("dim_facility") }}

    )

select
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

from stg_data stg
left join
    dim_facility dim
    on stg.natural_id = dim.natural_id
    and stg.storage_type = dim.storage_type

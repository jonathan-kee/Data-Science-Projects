with
    source_data as (

        select distinct
            "natural_id" as natural_id,
            "name" as facility_name,
            "storage_type" as storage_type
        from {{ ref("stg_inventory") }}
        where "natural_id" is not null

    )

select
    -- Deterministic surrogate primary key using MD5
    md5(
        coalesce(cast(natural_id as varchar), '')
        || '-'
        || coalesce(cast(storage_type as varchar), '')
    ) as facility_key,

    natural_id,
    facility_name,
    storage_type,
    current_timestamp as created_at
from source_data

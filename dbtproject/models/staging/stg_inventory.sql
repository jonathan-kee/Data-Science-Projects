with source as (
        select * from {{ source('prosperous_universe sources', 'inventory_raw') }}
  ),
  renamed as (
      select
          {{ adapter.quote("load time") }},
        {{ adapter.quote("Username") }},
        {{ adapter.quote("NaturalId") }},
        {{ adapter.quote("Name") }},
        {{ adapter.quote("StorageType") }},
        {{ adapter.quote("Ticker") }},
        {{ adapter.quote("Amount") }}

      from source
  )
  select * from renamed
    
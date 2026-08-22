{% macro stg_cxpc(ticker_name, source_table) %}
    SELECT 
        '{{ ticker_name }}' as "ticker",
        to_timestamp("date_epoch_ms" / 1000) AT TIME ZONE 'UTC' as "timezone", 
        (to_timestamp("date_epoch_ms" / 1000) AT TIME ZONE 'UTC')::DATE AS date_part,
        (to_timestamp("date_epoch_ms" / 1000) AT TIME ZONE 'UTC')::TIME AS time_part,
        *
    FROM {{ source('prosperous_universe_sources', source_table) }}
{% endmacro %}
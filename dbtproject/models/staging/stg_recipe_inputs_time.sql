-- Import CTEs
WITH raw_data AS (
    select raw.recipe_inputs_time_raw."Key" AS raw_string,
           raw.recipe_inputs_time_raw."TimeMs" as time_ms
    from {{source('prosperous_universe_sources','recipe_inputs_time_raw')}}
),
-- Logical CTEs
clean AS (
    SELECT
        replace(raw_string_one, ' ', '-') AS raw_string_two,
        time_ms
    FROM (
        SELECT
        replace(raw_string, '#', ':') AS raw_string_one,
        time_ms
    -- contains duplicate data
    -- Deduplicate the source strings first
    -- unique_raw_data
    FROM (
        SELECT DISTINCT raw_string, time_ms
        FROM raw_data
        )
    )
),
parsed_prefix AS (
    SELECT
        clean.raw_string_two AS original_query,
        split_part(clean.raw_string_two, ':', 1) AS prefix,
        split_part(clean.raw_string_two, ':', 2) AS recipe_string,
        time_ms
    FROM clean
),
split_sides AS (
    SELECT
        parsed_prefix.original_query,
        parsed_prefix.prefix,
        split_part(parsed_prefix.recipe_string, '=>', 1) AS input_str,
        split_part(parsed_prefix.recipe_string, '=>', 2) AS output_str,
        time_ms
    FROM parsed_prefix
),
clean_data AS (SELECT original_query,
                      prefix,
                      (regexp_matches(input_item, '(\d+)x([A-Z0-9]+)'))[1]::INT AS materialInputQuantity,
                      (regexp_matches(input_item, '(\d+)x([A-Z0-9]+)'))[2]      AS materialInput,
                      (regexp_matches(output_str, '(\d+)x([A-Z0-9]+)'))[1]::INT AS materialOutputQuantity,
                      (regexp_matches(output_str, '(\d+)x([A-Z0-9]+)'))[2]      AS materialOutput,
                      time_ms
               FROM split_sides,
                    LATERAL unnest(string_to_array(input_str, '-')) AS input_item
)
-- Final CTE
select * from clean_data
-- Have on join on prefix, materialInputQuantity, materialInput, materialOutputQuantity, materialOutput --

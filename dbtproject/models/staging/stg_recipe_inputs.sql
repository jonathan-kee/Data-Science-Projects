-- Import CTEs
WITH raw_data AS (
    select "key" AS raw_string
    from {{source('prosperous_universe_sources','recipe_inputs_raw')}}
),
-- Logical CTEs
parsed_prefix AS (
    SELECT
        raw_string AS original_query,
        split_part(raw_string, ':', 1) AS prefix,
        split_part(raw_string, ':', 2) AS recipe_string
    -- contains duplicate data
    -- Deduplicate the source strings first
    FROM (
        SELECT DISTINCT raw_string
        FROM raw_data
    )
),
split_sides AS (
    SELECT
        original_query,
        prefix,
        split_part(recipe_string, '=>', 1) AS input_str,
        split_part(recipe_string, '=>', 2) AS output_str
    FROM parsed_prefix
),
clean_data AS (SELECT original_query,
                      prefix,
                      (regexp_matches(input_item, '(\d+)x([A-Z0-9]+)'))[1]::INT AS materialInputQuantity,
                      (regexp_matches(input_item, '(\d+)x([A-Z0-9]+)'))[2]      AS materialInput,
                      (regexp_matches(output_str, '(\d+)x([A-Z0-9]+)'))[1]::INT AS materialOutputQuantity,
                      (regexp_matches(output_str, '(\d+)x([A-Z0-9]+)'))[2]      AS materialOutput
               FROM split_sides,
                    LATERAL unnest(string_to_array(input_str, '-')) AS input_item
)
-- Final CTE
select * from clean_data
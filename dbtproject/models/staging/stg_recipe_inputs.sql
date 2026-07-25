WITH raw_data AS (
    select "Key" AS raw_string
    from {{source('prosperous_universe sources','recipe_inputs_raw')}}
),
-- Deduplicate the source strings first
unique_raw_data AS (
    SELECT DISTINCT raw_string
    FROM raw_data
),
parsed_prefix AS (
    SELECT
        raw_string AS original_query,
        split_part(raw_string, ':', 1) AS prefix,
        split_part(raw_string, ':', 2) AS recipe_string
    FROM unique_raw_data
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
select
    *
from clean_data
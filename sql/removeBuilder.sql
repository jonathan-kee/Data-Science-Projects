-- Remove Building
select substring("Key" from (position(':' in "Key") + 1) for length("Key"))
from recipe_inputs_raw;

-- Get Material produced
select substring("Key" from (position('=>' in "Key") + 2) for length("Key"))
from recipe_inputs_raw;

-- Get Material required
SELECT SUBSTRING(
    "Key"
    FROM POSITION(':' IN "Key") + 1
    FOR POSITION('=>' IN "Key") - POSITION(':' IN "Key") - 1
)
FROM recipe_inputs_raw;

-- (Gemini) Turn data into sql format instead of using Java
WITH raw_data AS (
    select "Key" AS raw_string
    from recipe_inputs_raw
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
)
SELECT 
    original_query,
    prefix,
    (regexp_matches(input_item, '(\d+)x([A-Z0-9]+)'))[1]::INT AS materialInputQuantity,
    (regexp_matches(input_item, '(\d+)x([A-Z0-9]+)'))[2]      AS materialInput,
    (regexp_matches(output_str, '(\d+)x([A-Z0-9]+)'))[1]::INT AS materialOutputQuantity,
    (regexp_matches(output_str, '(\d+)x([A-Z0-9]+)'))[2]      AS materialOutput
FROM 
    split_sides,
    LATERAL unnest(string_to_array(input_str, '-')) AS input_item;

-- CTE code to show results that I need
WITH raw_data AS (
    select "Key" AS raw_string
    from recipe_inputs_raw
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
),
 totalCost AS (select clean_data.original_query,
                      clean_data.prefix,
                      clean_data.materialInputQuantity,
                      clean_data.materialInput,
                      market_depth_raw."AI1-Average",
                      clean_data.materialInputQuantity * market_depth_raw."AI1-Average" as "total cost",
                      clean_data.materialOutputQuantity,
                      clean_data.materialOutput
               from market_depth_raw
                        left join clean_data on clean_data.materialInput = market_depth_raw."Ticker"
)
select totalCost.original_query,
       totalCost.prefix,
totalCost.materialInputQuantity,
totalCost.materialInput,
totalCost."AI1-Average",
totalCost."total cost",
totalCost.materialOutputQuantity,
totalCost.materialOutput,
market_depth_raw."AI1-Average",
totalCost.materialOutputQuantity * market_depth_raw."AI1-Average" as "total price",
(totalCost.materialOutputQuantity * market_depth_raw."AI1-Average") - totalCost."total cost" as profit
from market_depth_raw left join totalCost on totalCost.materialOutput = market_depth_raw."Ticker"
-- The problem with the above query is that I can only accurately get one of the total cost,
-- need to split the data

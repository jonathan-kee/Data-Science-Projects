select
    stg_recipe_inputs_time.original_query,
    stg_recipe_inputs_time.prefix,
    stg_recipe_inputs_time.materialinput,
    stg_recipe_inputs_time.materialinputquantity,
    (1440 / recipe_table_input_aggregate."minutes per order") as "orders_per_day",
    (1440 / recipe_table_input_aggregate."minutes per order") * materialinputquantity as "material_used_per_day",
    stg_inventory.amount as "inventory_amount",
    stg_inventory.amount / ((1440 / recipe_table_input_aggregate."minutes per order") * materialinputquantity )as "days_left"
from {{ ref("stg_recipe_inputs_time") }} as stg_recipe_inputs_time
join {{ ref("sme_recipe_table_input_aggregate") }}as recipe_table_input_aggregate on
stg_recipe_inputs_time.original_query = recipe_table_input_aggregate.original_query
join {{ ref("stg_inventory") }} as stg_inventory on
stg_inventory.ticker = stg_recipe_inputs_time.materialinput
where stg_recipe_inputs_time.original_query = 'SME:6xALO-1xO-1xC-1xFLX=>4xAL'
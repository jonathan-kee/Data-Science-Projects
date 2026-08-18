with 
all_sources as (
    select *
    FROM {{ ref("stg_cxpc_al_ai1") }}
    union all
    select *
    FROM {{ ref("stg_cxpc_au_ai1") }}
    union all
    select *
    FROM {{ ref("stg_cxpc_cf_ai1") }}
    union all
    select *
    FROM {{ ref("stg_cxpc_cu_ai1") }}
    union all
    select *
    FROM {{ ref("stg_cxpc_fe_ai1") }}
    union all
    select *
    FROM {{ ref("stg_cxpc_li_ai1") }}
    union all
    select *
    FROM {{ ref("stg_cxpc_re_ai1") }}
    union all
    select *
    FROM {{ ref("stg_cxpc_s_ai1") }}
    union all
    select *
    FROM {{ ref("stg_cxpc_si_ai1") }}
    union all
    select *
    FROM {{ ref("stg_cxpc_stl_ai1") }}
    union all
    select *
    FROM {{ ref("stg_cxpc_ti_ai1") }}
) select * from all_sources
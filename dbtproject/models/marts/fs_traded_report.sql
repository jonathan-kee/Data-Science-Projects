with all_sources as (
    select *
    FROM {{ ref("stg_cxpc_seq_ai1") }}
    union all
    select *
    FROM {{ ref("stg_cxpc_bgo_ai1") }}
    union all
    select *
    FROM {{ ref("stg_cxpc_mfk_ai1") }}
    union all
    select *
    FROM {{ ref("stg_cxpc_bro_ai1") }}
    union all
    select *
    FROM {{ ref("stg_cxpc_bfr_ai1") }}
    union all
    select *
    FROM {{ ref("stg_cxpc_rgo_ai1") }}
    union all
    select *
    FROM {{ ref("stg_cxpc_uts_ai1") }}
    union all
    select *
    FROM {{ ref("stg_cxpc_bco_ai1") }}
    union all
    select *
    FROM {{ ref("stg_cxpc_afr_ai1") }}
    union all
    select *
    FROM {{ ref("stg_cxpc_sfk_ai1") }}
    union all
    select *
    FROM {{ ref("stg_cxpc_hcc_ai1") }}
    union all
    select *
    FROM {{ ref("stg_cxpc_bgc_ai1") }} 
    union all
    select *
    FROM {{ ref("stg_cxpc_flo_ai1") }} 
),
rank_all_sources as (
    select
        "ticker",
        SUM("Traded") as "total_traded",
        DENSE_RANK() OVER (ORDER BY SUM("Traded") DESC) as "traded_rank"
    from all_sources
    group by "ticker"
)
select * 
from rank_all_sources
order by "traded_rank" ASC
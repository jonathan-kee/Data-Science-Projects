with
    all_sources as (
        select *
        from {{ ref("stg_cxpc_seq_ai1") }}
        union all
        select *
        from {{ ref("stg_cxpc_bgo_ai1") }}
        union all
        select *
        from {{ ref("stg_cxpc_mfk_ai1") }}
        union all
        select *
        from {{ ref("stg_cxpc_bro_ai1") }}
        union all
        select *
        from {{ ref("stg_cxpc_bfr_ai1") }}
        union all
        select *
        from {{ ref("stg_cxpc_rgo_ai1") }}
        union all
        select *
        from {{ ref("stg_cxpc_uts_ai1") }}
        union all
        select *
        from {{ ref("stg_cxpc_bco_ai1") }}
        union all
        select *
        from {{ ref("stg_cxpc_afr_ai1") }}
        union all
        select *
        from {{ ref("stg_cxpc_sfk_ai1") }}
        union all
        select *
        from {{ ref("stg_cxpc_hcc_ai1") }}
        union all
        select *
        from {{ ref("stg_cxpc_bgc_ai1") }}
        union all
        select *
        from {{ ref("stg_cxpc_flo_ai1") }}
    )
select *
from all_sources

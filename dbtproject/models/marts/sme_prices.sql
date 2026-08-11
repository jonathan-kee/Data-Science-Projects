--  ------------------------------------- Smeltor -------------------------------------

with all_smeltor_sources as (
    select *
    from {{ ref("stg_cxpc_al_ai1") }} 
    union all
    select *
    from {{ ref("stg_cxpc_au_ai1") }} 
    union all
    select *
    from {{ ref("stg_cxpc_cf_ai1") }} 
    union all
    select *
    from {{ ref("stg_cxpc_cu_ai1") }} 
    union all
    select *
    from {{ ref("stg_cxpc_fe_ai1") }} 
    union all
    select *
    from {{ ref("stg_cxpc_li_ai1") }} 
    union all
    select *
    from {{ ref("stg_cxpc_s_ai1") }} 
    union all
    select *
    from {{ ref("stg_cxpc_stl_ai1") }} 
    union all
    select *
    from {{ ref("stg_cxpc_ti_ai1") }} 
    union all
    select *
    from {{ ref("stg_cxpc_si_ai1") }} 
    union all
    select *
    from {{ ref("stg_cxpc_re_ai1") }} 
),
 max_dates as (
    select
        ticker,
        max("date_part") as max_date
    from {{ ref("sme_prices") }}
    group by ticker
)
select s.*
from all_smeltor_sources s
join max_dates m
  on s.ticker = m.ticker
where s."Interval" = 'DAY_ONE'
  and s."date_part" = m.max_date 
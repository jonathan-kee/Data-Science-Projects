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
    from all_smeltor_sources
    group by ticker
),
 max_dates_table as (
    select s.*
    from all_smeltor_sources s
    join max_dates m
    on s.ticker = m.ticker
    where s."Interval" = 'DAY_ONE'
    -- Filters sme_prices to the 7-day range up to max_date
    and s."date_part" between m.max_date - interval '6 days' and m.max_date
 ) 
 select * from max_dates_table

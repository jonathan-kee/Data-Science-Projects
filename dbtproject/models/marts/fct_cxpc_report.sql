select *
from {{ ref("stg_cxpc_al_ai1") }}
union all
select * 
from {{ ref("stg_cxpc_alo_ai1") }}
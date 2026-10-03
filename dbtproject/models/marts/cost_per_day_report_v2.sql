select 
smeltor_cost_per_week,
smeltor_cost_per_week / 7 as smeltor_cost_per_day,
workforce_cost_per_week,
workforce_cost_per_week / 7 as workforce_cost_per_day, 
smeltor_cost_per_week + workforce_cost_per_week as total_cost_per_week,
(smeltor_cost_per_week + workforce_cost_per_week) / 7 as total_cost_per_day
from {{ ref("smeltor_cost_per_week") }} as smeltor_cost_per_week
join {{ ref("workforce_cost_per_week") }} as workforce_cost_per_week on 1=1
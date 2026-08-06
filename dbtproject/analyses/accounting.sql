select
    (select sum("total_selling_price") as "Assets"
from raw.inventory_price_report
where "Inventory Ticker" not in ('COF','DW', 'RAT', 'OVE','PWO')),
    (select sum("total_selling_price") as "Expense"
     from raw.inventory_price_report)
from (SELECT 1 + 1 AS result) as r;
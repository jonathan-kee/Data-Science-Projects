with aggregates as (
    select
        Sum("material input's total cost") as "material input's total cost",
        max("material output's total price") as "material output's total price",
        max("total_order_per_day") as "total order per day"
    from raw.dim_report
    where materialoutput = 'AL' and materialoutputquantity = 3
),
RoiPerDay as (
    select
        ("material output's total price" - "material input's total cost") * "total order per day" as RoiPerDay
    from aggregates
)
select * from RoiPerDay
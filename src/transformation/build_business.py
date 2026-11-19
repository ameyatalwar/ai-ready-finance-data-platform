from pathlib import Path
import duckdb
from src.config import DB_PATH

conn = duckdb.connect(DB_PATH)
print(f"Connected to database {DB_PATH}")

# ---------------------------------------------------------
# Create Business schema
# ---------------------------------------------------------

conn.execute(""" CREATE SCHEMA IF NOT EXISTS business """)
print("Business schema created successfully.")

# ---------------------------------------------------------
# Create monthly payroll actuals
# Grain: Cost Center + Department + Month + Year
# ---------------------------------------------------------

conn.execute(""" CREATE OR REPLACE TABLE business.monthly_payroll_actuals AS 
SELECT cost_center,department,month,year,SUM(payroll_expense) as actual_payroll
FROM trusted.payroll
GROUP BY cost_center, department, month, year
""" )

print("business.monthly_payroll_actuals created successfully")

# ---------------------------------------------------------
# Inspect  business.monthly_payroll_actuals
# ---------------------------------------------------------

monthly_payroll_actuals = conn.execute(""" SELECT * FROM business.monthly_payroll_actuals """).fetchall()


print("Monthly payroll actuals results: ")
for row in monthly_payroll_actuals:
    print(row)

# ---------------------------------------------------------
# Identify reporting periods
# ---------------------------------------------------------
reporting_periods = conn.execute(""" SELECT DISTINCT month,year from trusted.payroll
UNION
SELECT DISTINCT month,year from trusted.budget """).fetchall()
print("Reporting periods: ")
for row in reporting_periods:
    print(row)

# ---------------------------------------------------------
# Create monthly headcount actuals
# Grain: Cost Center + Department + Month + Year
# ---------------------------------------------------------
conn.execute(""" CREATE OR REPLACE TABLE business.monthly_headcount_actuals AS
with reporting_period as (SELECT DISTINCT month,year from trusted.payroll
UNION
SELECT DISTINCT month,year from trusted.budget )
SELECT e.cost_center,
e.department,
rp.month as month,
rp.year as year,count(distinct employee_id)  AS actual_headcount
FROM trusted.employees AS e INNER JOIN reporting_period AS rp
on e.start_date <= LAST_DAY(MAKE_DATE(rp.year,rp.month,1))
and (e.end_date IS NULL OR e.end_date >= MAKE_DATE(rp.year,rp.month,1))
GROUP BY e.cost_center,e.department,rp.month ,
rp.year """)

# ---------------------------------------------------------
# Inspect business.monthly_headcount_actuals
# ---------------------------------------------------------

monthly_headcount_actuals = conn.execute("""
    SELECT *
    FROM business.monthly_headcount_actuals
    ORDER BY
        year,
        month,
        cost_center,
        department
""").fetchall()

print("\nMonthly headcount actuals:")

for row in monthly_headcount_actuals:
    print(row)

# ---------------------------------------------------------
# Inspect Trusted Budget
# ---------------------------------------------------------

trusted_budget = conn.execute(""" SELECT 
cost_center,
department,
month,
year,
sum(planned_headcount) as planned_headcount,
sum(planned_payroll) as planned_budget
FROM trusted.budget
GROUP BY cost_center,department,month,year """).fetchall()

print("Trusted budget: ")
for row in trusted_budget:
    print(row)

# ---------------------------------------------------------
# Create Department Monthly Performance
# Grain: Cost Center + Department + Month + Year
# ---------------------------------------------------------

conn.execute("""
    CREATE OR REPLACE TABLE business.department_monthly_performance AS
    SELECT b.cost_center, b.department, b.month, b.year,
    SUM(mpa.actual_payroll) as actual_payroll,
    SUM(b.planned_payroll) as planned_payroll,
    SUM(mpa.actual_payroll) - SUM(b.planned_payroll)  as payroll_variance,
    SUM(mha.actual_headcount) as actual_headcount,
    SUM(b.planned_headcount) as planned_headcount,
    SUM(mha.actual_headcount) - SUM(b.planned_headcount) as headcount_variance
    
    FROM trusted.budget as b
    LEFT JOIN business.monthly_payroll_actuals as mpa
    ON b.cost_center = mpa.cost_center
    AND b.department = mpa.department
    AND b.month = mpa.month
    AND b.year = mpa.year
    LEFT JOIN business.monthly_headcount_actuals as mha
    ON b.cost_center = mha.cost_center
    AND b.department = mha.department
    AND b.month = mha.month
    AND b.year = mha.year
    GROUP BY b.cost_center, b.department, b.month, b.year
    """ )

# ---------------------------------------------------------
# Inspect business.department_monthly_performance
# ---------------------------------------------------------

department_monthly_reference = conn.execute(""" SELECT * FROM business.department_monthly_performance  """).fetchall()
print("Department monthly performance: ")
for row in department_monthly_reference:
    print(row)

conn.close()

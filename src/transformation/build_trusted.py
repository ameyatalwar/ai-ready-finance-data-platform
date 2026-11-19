import duckdb
from src.config import DB_PATH

conn = duckdb.connect(DB_PATH)
print(f"Connected to database : {DB_PATH}")

# ---------------------------------------------------------
# Create 'trusted' schema
# ---------------------------------------------------------


conn.execute("""CREATE SCHEMA IF NOT Exists trusted""")
print("Trusted schema created successfully")

conn.execute("""CREATE SCHEMA IF NOT EXISTS quality""")

schemas = conn.execute("""SELECT DISTINCT schema_name from information_schema.schemata order by schema_name""").fetchall()
print("\nSchemas : ")
print(schemas)



# ---------------------------------------------------------
# Create job level validation
# ---------------------------------------------------------

conn.execute("""CREATE OR REPLACE VIEW quality.job_level_validation AS
SELECT jl."Job Level",
TRIM(jl."Job level") is NOT NULL and TRIM(jl."Job level") <> '' AS valid_job_level_required,
COALESCE(REGEXP_MATCHES(TRIM(jl."Job level"),'^L[0-9]+$'), FALSE) AS valid_job_level_format,
COUNT(*) OVER(PARTITION BY TRIM(jl."Job level")) = 1 AS valid_unique_job_level
from raw.job_level as jl """)

# ---------------------------------------------------------
# Inspect job level validation
# ---------------------------------------------------------

job_level_validation_results = conn.execute("""SELECT * FROM quality.job_level_validation""").fetchall()

print("Job level validation results")
for row in job_level_validation_results:
    print(row)

# ---------------------------------------------------------
# Create trusted.job_level using job level validation
# ---------------------------------------------------------

conn.execute("""CREATE OR REPLACE TABLE trusted.job_level AS
SELECT trim("Job level") as job_level 
from quality.job_level_validation 
WHERE valid_job_level_required
AND valid_job_level_format
and valid_unique_job_level""").fetchall()

# ---------------------------------------------------------
# Inspect trusted.job_level
# ---------------------------------------------------------

trusted_job_level_results = conn.execute(""" SELECT * FROM trusted.job_level """).fetchall()

print("Trusted job level results: ")

for row in trusted_job_level_results:
    print(row)


# ------------------------------------------------------------
# Create quality.job_level_rejects using job level validation
# ------------------------------------------------------------

conn.execute(""" CREATE OR REPLACE TABLE quality.job_level_rejects AS
SELECT TRIM("Job level") ,
CONCAT_WS(',',
CASE WHEN NOT valid_job_level_required THEN 'MISSING JOB LEVEL' END,
CASE WHEN NOT valid_job_level_format THEN 'INVALID JOB LEVEL FORMAT' END,
CASE WHEN NOT valid_unique_job_level THEN 'DUPLICATE JOB LEVEL' END) AS rejection_reason
from quality.job_level_validation
WHERE NOT(valid_job_level_required
AND valid_job_level_format
AND valid_unique_job_level) """).fetchall()

# ---------------------------------------------------------
# Inspect quality.job_level_rejects
# ---------------------------------------------------------

job_level_rejects = conn.execute(""" SELECT * FROM quality.job_level_rejects """).fetchall()

print("Rejected Job level records: ")

for row in job_level_rejects:
    print(row)


# ---------------------------------------------------------
# Create job sub family validation
# ---------------------------------------------------------

conn.execute(""" CREATE OR REPLACE VIEW quality.job_sub_family_validation AS
SELECT "Job sub family code",
"Job sub family description",
TRIM("Job sub family code") IS NOT NULL AND TRIM("Job sub family code") <> '' as valid_jsf_code,
COALESCE(REGEXP_MATCHES(TRIM("Job sub family code"), '^JSF_[A-Z0-9_]+$'),FALSE) as valid_jsf_code_format ,
COUNT(*) OVER (PARTITION BY TRIM("Job sub family code")) = 1 as valid_unique_jsf_code,
TRIM("Job sub family description") IS NOT NULL AND TRIM("Job sub family description") <> '' as valid_jsf_description,
COUNT(*) OVER (PARTITION BY TRIM("Job sub family description")) = 1 as valid_unique_jsf_description

from raw.job_sub_family """)

# ---------------------------------------------------------
# Inspect job sub family validation
# ---------------------------------------------------------

job_sub_family_validation = conn.execute(""" SELECT "Job sub family code",
"Job sub family description",
valid_jsf_code,
valid_jsf_code_format,
valid_unique_jsf_code,
valid_jsf_description,
valid_unique_jsf_description from
quality.job_sub_family_validation """).fetchall()

print("Job sub family validation results: ")
for row in job_sub_family_validation:
    print(row)

# ------------------------------------------------------------
# Create trusted job sub family from job sub family validation
# ------------------------------------------------------------

conn.execute(""" CREATE OR REPLACE TABLE trusted.job_sub_family AS
SELECT TRIM("Job sub family code") AS job_sub_family_code,
TRIM("Job sub family description") AS job_sub_family_description
FROM  quality.job_sub_family_validation
WHERE valid_jsf_code
AND valid_jsf_code_format
and valid_unique_jsf_code
and valid_jsf_description
and valid_unique_jsf_description """)


# ---------------------------------------------------------
# Inspect trusted.job_sub_family
# ---------------------------------------------------------

trusted_job_sub_family_results = conn.execute(""" SELECT * FROM trusted.job_sub_family """).fetchall()

print("Trusted job sub family records: ")

for row in trusted_job_sub_family_results:
    print(row)

# --------------------------------------------------------------------
# Create quality.job_sub_family_rejects from job sub family validation
# --------------------------------------------------------------------

conn.execute(""" CREATE OR REPLACE TABLE quality.job_sub_family_rejects AS
SELECT TRIM("Job sub family code") ,
TRIM("Job sub family description"),
CONCAT_WS(',',CASE WHEN NOT valid_jsf_code THEN 'MISSING JSF CODE' END,
CASE WHEN NOT valid_jsf_code_format THEN 'INVALID JSF CODE' END,
CASE WHEN NOT valid_unique_jsf_code THEN 'DUPLICATE JSF CODE' END,
CASE WHEN NOT valid_jsf_description THEN 'MISSING JSF DESCRIPTION' END,
CASE WHEN NOT valid_unique_jsf_description THEN 'DUPLICATE JSF DESCRIPTION' END ) AS rejection_reason
FROM quality.job_sub_family_validation
WHERE NOT(valid_jsf_code
AND valid_jsf_code_format
AND valid_unique_jsf_code
AND valid_jsf_description
AND valid_unique_jsf_description) """)

# ---------------------------------------------------------
# Inspect quality.job_sub_family_rejects
# ---------------------------------------------------------

job_sub_family_rejects_results = conn.execute(""" SELECT * FROM quality.job_sub_family_rejects """).fetchall()

print("Job sub family rejects results: ")
for row in job_sub_family_rejects_results:
    print(row)


# ---------------------------------------------------------
# Create comp region validation
# ---------------------------------------------------------

conn.execute(""" CREATE OR REPLACE VIEW quality.comp_region_validation AS
SELECT "Comp Region Code",
"Comp Region Description",
TRIM("Comp Region Code") IS NOT NULL AND TRIM("Comp Region Code") <> '' as valid_comp_region_code,
COUNT(*) OVER (PARTITION BY TRIM("Comp Region Code")) = 1 as valid_unique_comp_region_code,
COALESCE(REGEXP_MATCHES(TRIM("Comp Region Code"),'^[A-Z0-9_]+$'), FALSE) as valid_format_comp_region_code,
TRIM("Comp Region Description") IS NOT NULL AND TRIM("Comp Region Description") <> '' as valid_comp_region_description,
COUNT(*) OVER (PARTITION BY TRIM("Comp Region Description"))  = 1 AS valid_unique_comp_region_description
FROM raw.comp_region """)

# ---------------------------------------------------------
# Inspect comp region validation
# ---------------------------------------------------------

comp_region_validation_results = conn.execute(""" SELECT * FROM quality.comp_region_validation """).fetchall()

print("Comp region validation results: ")
for row in comp_region_validation_results:
    print(row)

# ---------------------------------------------------------
# Create trusted.comp_region using comp region validation
# ---------------------------------------------------------

conn.execute(""" CREATE OR REPLACE TABLE trusted.comp_region AS
SELECT TRIM("Comp Region Code") AS comp_region_code,
TRIM("Comp Region Description") AS comp_region_description
from quality.comp_region_validation
WHERE valid_comp_region_code
AND valid_unique_comp_region_code
AND valid_format_comp_region_code
AND valid_comp_region_description
AND valid_unique_comp_region_description  """)

# ---------------------------------------------------------
# Inspect trusted.comp_region 
# ---------------------------------------------------------

comp_region_results = conn.execute(""" SELECT * FROM trusted.comp_region """).fetchall()

print("Trusted comp region results: ")
for row in comp_region_results:
    print(row)

# ---------------------------------------------------------
# Create quality.comp_region_rejects using comp region validation
# ---------------------------------------------------------

conn.execute(""" CREATE OR REPLACE TABLE quality.comp_region_rejects AS
SELECT "Comp Region Code",
"Comp Region Description",
CONCAT_WS(', ',
CASE WHEN NOT valid_comp_region_code THEN 'MISSING COMP REGION CODE' END,
CASE WHEN NOT valid_unique_comp_region_code THEN 'DUPLICATE COMP REGION CODE' END,
CASE WHEN NOT valid_format_comp_region_code THEN 'INVALID FORMAT COMP REGION CODE' END,
CASE WHEN NOT valid_comp_region_description THEN 'MISSING COMP REGION DESCRIPTION' END,
CASE WHEN NOT valid_unique_comp_region_description THEN 'DUPLICATE COMP REGION DESCRIPTION' END ) AS rejection_reason
from quality.comp_region_validation
WHERE NOT(valid_comp_region_code
AND valid_unique_comp_region_code
AND valid_format_comp_region_code
AND valid_comp_region_description
AND valid_unique_comp_region_description)  """)

# ---------------------------------------------------------
# Inspect quality.comp_region_rejects
# ---------------------------------------------------------

comp_region_rejects_results = conn.execute(""" SELECT * FROM quality.comp_region_rejects """).fetchall()

print("Comp Region Rejects results: ")
for row in comp_region_rejects_results:
    print(row)

# ---------------------------------------------------------
# Create cost center validation
# ---------------------------------------------------------

conn.execute(""" CREATE OR REPLACE VIEW quality.cost_center_validation AS 
SELECT "Cost Center",
"Cost Center Description", 
"Department" , 
"Department description",
"VP",
"Region",
TRIM("Cost Center") IS NOT NULL AND TRIM("Cost Center") <> '' AS valid_cost_center,
TRIM("Cost Center description") IS NOT NULL AND TRIM("Cost Center description") <> '' AS valid_cost_center_description,
TRIM("Department") IS NOT NULL AND TRIM("Department") <> '' AS valid_department,
TRIM("Department description") IS NOT NULL AND TRIM("Department description") <> '' AS valid_department_description,
TRIM("VP") IS NOT NULL AND TRIM("VP") <> '' AS valid_vp,
TRIM("Region") IS NOT NULL AND TRIM("Region") <> '' AS valid_region,
COUNT(*) OVER (PARTITION BY TRIM("Cost Center"),TRIM("Department")) = 1 AS valid_unique_cc_department,
COUNT(*) OVER (PARTITION BY TRIM("Department")) = 1 as valid_unique_department,
COUNT(*) OVER (
    PARTITION BY
        TRIM("Cost Center"),
        TRIM("Department description")
) = 1
AS valid_unique_cc_department_description
FROM raw.cost_center
""")

# ---------------------------------------------------------
# Inspect cost center validation
# ---------------------------------------------------------

cost_center_validation = conn.execute(""" SELECT * FROM quality.cost_center_validation """).fetchall()

print("Cost center validation results: ")
for row in cost_center_validation:
    print(row)

# ---------------------------------------------------------
# Create trusted.cost_center using cost center validation
# ---------------------------------------------------------

conn.execute(""" CREATE OR REPLACE TABLE trusted.cost_center AS
             SELECT TRIM("Cost Center") as cost_center,
             TRIM("Cost Center Description") AS cost_center_description,
             TRIM("Department") AS department,
             TRIM("Department Description") as department_description,
             TRIM("VP") as vp,
             TRIM("Region") as region
             FROM quality.cost_center_validation
             WHERE valid_cost_center
             AND valid_cost_center_description
             AND valid_department
             AND valid_department_description
             AND valid_vp
             AND valid_region
             AND valid_unique_cc_department
             AND valid_unique_department
             AND valid_unique_cc_department_description
             """ )

# ---------------------------------------------------------
# Inspect trusted.cost_center
# ---------------------------------------------------------

trusted_cost_center = conn.execute(""" SELECT * FROM trusted.cost_center """).fetchall()

print("Trusted cost center results: ")
for row in trusted_cost_center:
    print(row)

# ---------------------------------------------------------------
# Create quality.cost_center_rejects using cost center validation
# ---------------------------------------------------------------

conn.execute(""" CREATE OR REPLACE TABLE quality.cost_center_rejects AS
SELECT  TRIM("Cost Center") ,
             TRIM("Cost Center Description") ,
             TRIM("Department") ,
             TRIM("Department Description") ,
             TRIM("VP") ,
             TRIM("Region"),
             CONCAT_WS(', ', CASE WHEN NOT valid_cost_center THEN 'MISSING COST CENTER' END,
             CASE WHEN NOT valid_cost_center_description THEN 'MISSING COST CENTER DESCRIPTION' END,
             CASE WHEN NOT valid_department THEN 'MISSING DEPARTMENT' END,
             CASE WHEN NOT valid_department_description THEN 'MISSING DEPARTMENT DESCRIPTION' END,
             CASE WHEN NOT valid_vp THEN 'MISSING VP' END,
             CASE WHEN NOT valid_region THEN 'MISSING REGION' END,
             CASE WHEN NOT valid_unique_cc_department THEN 'DUPLICATE COST CENTER DEPARTMENT COMBINATION' END,
             CASE WHEN NOT valid_unique_department THEN 'DUPLICATE DEPARTMENT CODE' END,
             CASE
    WHEN NOT valid_unique_cc_department_description
    THEN 'DUPLICATE COST CENTER DEPARTMENT DESCRIPTION'
END) AS rejection_reason
FROM quality.cost_center_validation
WHERE NOT (valid_cost_center
AND valid_cost_center_description
AND valid_department
AND valid_department_description
AND valid_vp
AND valid_region
AND valid_unique_cc_department
AND valid_unique_department
AND valid_unique_cc_department_description) """)

# ---------------------------------------------------------
# Inspect quality.cost_center_rejects
# ---------------------------------------------------------

cost_center_rejects = conn.execute(""" SELECT * FROM quality.cost_center_rejects """).fetchall()

print("Cost center reject records: ")
for row in cost_center_rejects:
    print(row)


# ---------------------------------------------------------
# Create employee validation
# ---------------------------------------------------------

conn.execute("""
    CREATE OR REPLACE VIEW quality.employee_validation AS

    SELECT
        e.*, cc.department as department_code, jsf.job_sub_family_code AS job_sub_family_code,

        TRY_CAST(TRIM(e."Employee ID") AS INTEGER) IS NOT NULL
            AS valid_employee_id,

        COUNT(*) OVER (PARTITION BY TRIM(e."Employee ID")) = 1 as valid_unique_employee_id,

        TRIM(e."First name") IS NOT NULL AND
        TRIM(e."First name") <> ''
        AS valid_first_name,

        TRIM(e."Last name") IS NOT NULL AND
        TRIM(e."Last name") <> ''
        AS valid_last_name,

        TRY_STRPTIME(TRIM(e."Start date"),'%m/%d/%Y') IS NOT NULL 
        AS valid_start_date,

        CASE WHEN e."End date" IS NULL THEN TRUE
        WHEN TRY_STRPTIME(TRIM(CAST(e."End date" AS VARCHAR)),'%m/%d/%Y') IS NOT NULL THEN TRUE
        ELSE FALSE
        END
        AS valid_end_date,

        CASE WHEN e."End date" IS NULL THEN TRUE
        WHEN TRY_STRPTIME(TRIM(CAST(e."End date" AS VARCHAR)),'%m/%d/%Y') >= TRY_STRPTIME(CAST(e."Start date" as VARCHAR),'%m/%d/%Y') THEN TRUE
        ELSE FALSE
        END
        AS valid_date_sequence, 

        cc.department IS NOT NULL
            AS valid_department,

        TRIM(e."Cost Center") IS NOT NULL
        AND TRIM(e."Cost Center") <> ''
             AS valid_cost_center,

        jsf.job_sub_family_code IS NOT NULL
            AS valid_job_sub_family,

        jl.job_level IS NOT NULL
            AS valid_job_level,

        cr.comp_region_code IS NOT NULL
            AS valid_comp_region

    FROM raw.employees e

    LEFT JOIN trusted.cost_center cc
        ON TRIM(e."Cost Center") =
         TRIM(cc.cost_center)
        AND TRIM(e."Department") =
           TRIM(cc.department_description)

    LEFT JOIN trusted.job_sub_family jsf
        ON TRIM(e."Job sub family") =
           TRIM(jsf.job_sub_family_description)

    LEFT JOIN trusted.job_level jl
        ON TRIM(e."Job level") =
           TRIM(jl.job_level)

    LEFT JOIN trusted.comp_region cr
        ON TRIM(e."Comp region") =
           TRIM(cr.comp_region_code)
""")

# ---------------------------------------------------------
# Inspect employee validation
# ---------------------------------------------------------

employee_validation_results = conn.execute("""
    SELECT
        "Employee ID",
        valid_employee_id,
        valid_unique_employee_id,
        valid_first_name,
        valid_last_name,
        valid_start_date,
        valid_end_date,
        valid_date_sequence,
        valid_department,
        valid_job_sub_family,
        valid_job_level,
        valid_comp_region
    FROM quality.employee_validation
    ORDER BY "Employee ID"
""").fetchall()

print("\nEmployee validation results:")

for row in employee_validation_results:
    print(row)

# ------------------------------------------------------------
# Create trusted.employees table using employee validation
# ------------------------------------------------------------

conn.execute("""CREATE OR REPLACE TABLE trusted.employees as 
SELECT TRIM("Employee ID") AS employee_id,
TRIM("First name") as first_name,
TRIM("Last name") AS last_name,
CAST(TRY_STRPTIME(TRIM("Start date") , '%m/%d/%Y') as DATE) as start_date,
CAST(TRY_STRPTIME(CAST("End date" AS VARCHAR), '%m/%d/%Y') as DATE) as end_date,
TRIM("Cost Center") AS cost_center,
department_code as department,
job_sub_family_code as job_sub_family,
TRIM("Job level") as job_level,
TRIM("Comp region") as comp_region
 from quality.employee_validation
 where valid_employee_id
        AND valid_unique_employee_id
        AND valid_first_name
        AND valid_last_name
        AND valid_start_date
        AND valid_end_date
        AND valid_date_sequence
        AND valid_cost_center
        AND valid_department
        AND valid_job_sub_family
        AND valid_job_level
        AND valid_comp_region""")

# ---------------------------------------------------------
# Inspect trusted employees
# ---------------------------------------------------------

print("trusted.employees table created successfully")
trusted_employees = conn.execute("""SELECT * from trusted.employees""").fetchall()
for row in trusted_employees:
    print(row)

# -------------------------------------------------------------
# Create quality.employees_rejects using employee validation
# -------------------------------------------------------------

conn.execute("""CREATE OR REPLACE TABLE quality.employees_rejects as SELECT "Employee ID" as employee_id,
"First name" as first_name,
"Last name" as last_name, 
"Start date" as start_date,
"End date" as end_date,
"Department" as department, 
"Job sub family" as job_sub_family,"Job level" as job_level,
"Comp region" as comp_region, 
 CONCAT_WS(', ',CASE WHEN NOT valid_employee_id THEN 'INVALID EMPLOYEE ID' END,
 CASE WHEN NOT valid_unique_employee_id THEN 'DUPLICATE EMPLOYEE ID' END,
 CASE WHEN NOT valid_first_name THEN 'MISSING FIRST NAME' END,
 CASE WHEN NOT valid_last_name THEN 'MISSING LAST NAME' END,
 CASE WHEN NOT valid_start_date THEN 'INVALID START DATE' END,
 CASE WHEN NOT valid_end_date THEN 'INVALID END DATE' END,
 CASE WHEN NOT valid_date_sequence THEN 'END DATE BEFORE START DATE' END,
 CASE
    WHEN NOT valid_cost_center
    THEN 'INVALID OR MISSING COST CENTER'
END,
 CASE WHEN NOT  valid_department THEN 'INVALID DEPARTMENT' END,
  CASE WHEN NOT valid_job_sub_family THEN 'INVALID JOB SUB FAMILY' END,
   CASE WHEN NOT valid_job_level THEN 'INVALID JOB LEVEL' END,
    CASE WHEN NOT valid_comp_region THEN 'INVALID COMP REGION' END ) AS rejection_reason
 from quality.employee_validation 
WHERE NOT (valid_employee_id 
and valid_unique_employee_id
and valid_first_name
and valid_last_name
and valid_start_date
and valid_end_date
and valid_date_sequence
AND valid_cost_center
and valid_department 
and valid_job_sub_family 
and valid_job_level 
and valid_comp_region)
""")

print("quality.employees_rejects table created successfully")

# ---------------------------------------------------------
# Inspect employee rejects
# ---------------------------------------------------------

employee_rejects = conn.execute("""SELECT * FROM quality.employees_rejects""").fetchall()
print("Rejected employee records:")
for row in employee_rejects:
    print(row)

# ---------------------------------------------------------
# Inspect schema trusted.employees validation
# ---------------------------------------------------------

trusted_schema = conn.execute("""DESCRIBE trusted.employees""").fetchall()
print("\n Schema for trusted.employees")
for column in trusted_schema:
    print(column)

# ---------------------------------------------------------
# Create payroll validation 
# ---------------------------------------------------------

conn.execute(""" CREATE OR REPLACE VIEW quality.payroll_validation AS
SELECT p."Employee ID", p."Cost Center",  p."Department", cc.department AS department_code,
p."Month", p."Year", p."Salary", p."Bonus", p."Payroll expense",
TRIM(e.employee_id) IS NOT NULL  AS valid_employee_reference,
TRIM(p."Department") IS NOT NULL
AND TRIM(p."Department") <> ''
    AS valid_department,
 cc.department IS NOT NULL
    AS valid_department_reference,
COALESCE(
    TRIM(p."Cost Center") = TRIM(e.cost_center),
    FALSE
) AS valid_employee_cost_center,
COALESCE(TRIM(cc.department) = TRIM(e.department),FALSE)
    AS valid_employee_department,
    TRIM(p."Cost Center") IS NOT NULL
AND TRIM(p."Cost Center") <> ''
    AS valid_cost_center,
p."Month" IS NOT NULL AND p."Month" between 1 AND 12 as valid_month,
p."Year" IS NOT NULL AND p."Year" > 0 AS valid_year,
TRY_CAST(REPLACE(REPLACE(TRIM(p."Salary"),'$' , ''),',','') AS DECIMAL(18,2)) IS NOT NULL as valid_salary,
TRY_CAST(REPLACE(REPLACE(TRIM(p."Bonus"),'$' , ''),',','') AS DECIMAL(18,2)) IS NOT NULL  as valid_bonus,
TRY_CAST(REPLACE(REPLACE(TRIM(p."Payroll expense"),'$' , ''),',','') AS DECIMAL(18,2)) IS NOT NULL  as valid_payroll_expense,
COUNT(*) OVER (PARTITION BY p."Employee ID",p."Month",p."Year") = 1 AS valid_unique_employee_month,
COALESCE(TRY_CAST(REPLACE(REPLACE(TRIM(p."Salary"),'$' , ''),',','') AS DECIMAL(18,2)) + TRY_CAST(REPLACE(REPLACE(TRIM(p."Bonus"),'$' , ''),',','') AS DECIMAL(18,2)) = TRY_CAST(REPLACE(REPLACE(TRIM(p."Payroll expense"),'$' , ''),',','') AS DECIMAL(18,2)),FALSE) as valid_payroll_calculation
FROM raw.payroll as p LEFT JOIN trusted.employees AS e
ON CAST(p."Employee ID"  AS VARCHAR) = e."employee_id" 
LEFT JOIN trusted.cost_center cc
    ON TRIM(p."Cost Center") =
       TRIM(cc.cost_center)
   AND TRIM(p."Department") =
       TRIM(cc.department_description)
 """)

# ---------------------------------------------------------
# Inspect payroll validation
# ---------------------------------------------------------

payroll_validation_results = conn.execute(""" SELECT * FROM quality.payroll_validation """).fetchall()

print("Payroll validation results: ")
for row in payroll_validation_results:
    print(row)

# ---------------------------------------------------------
# Create trusted.payroll using payroll validation
# ---------------------------------------------------------

conn.execute(""" CREATE OR REPLACE TABLE trusted.payroll AS SELECT CAST("Employee ID" AS VARCHAR) AS employee_id,
TRIM("Cost Center") AS cost_center,
 department_code as department,
 CAST("Month" AS INTEGER) as month,
 CAST("Year" AS INTEGER) as year,
 TRY_CAST(REPLACE(REPLACE(TRIM("Salary"),',',''),'$','') AS DECIMAL(18,2)) as salary,
 TRY_CAST(REPLACE(REPLACE(TRIM("Bonus"),',',''),'$','') AS DECIMAL(18,2)) as bonus,
 TRY_CAST(REPLACE(REPLACE(TRIM("Payroll expense"),',',''),'$','') AS DECIMAL(18,2)) as payroll_expense
FROM quality.payroll_validation 
WHERE valid_employee_reference
AND valid_cost_center
AND valid_employee_cost_center
AND valid_department
AND valid_department_reference
AND valid_employee_department
AND valid_month
AND valid_year
AND valid_salary
AND valid_bonus
AND valid_payroll_expense
AND valid_unique_employee_month
AND valid_payroll_calculation
""")

# ---------------------------------------------------------
# Inspect trusted.payroll
# ---------------------------------------------------------

trusted_payroll = conn.execute(""" SELECT * FROM trusted.payroll """).fetchall()

print("Trusted payroll results: ")
for row in trusted_payroll:
    print(row)

# ---------------------------------------------------------
# Create quality.payroll_rejects using payroll validation
# ---------------------------------------------------------

conn.execute(""" CREATE OR REPLACE TABLE quality.payroll_rejects AS
SELECT "Employee ID",
"Cost Center",
"Department",
"Month",
"Year",
"Salary",
"Bonus",
"Payroll expense",
CONCAT_WS(', ', CASE WHEN NOT valid_employee_reference THEN 'INVALID EMPLOYEE REFERENCE' END,
CASE
    WHEN NOT valid_cost_center
        THEN 'MISSING COST CENTER'
END,

CASE
    WHEN NOT valid_department_reference
        THEN 'INVALID COST CENTER / DEPARTMENT COMBINATION'
END,

CASE
    WHEN NOT valid_employee_cost_center
        THEN 'EMPLOYEE COST CENTER MISMATCH'
END,

CASE
    WHEN NOT valid_employee_department
        THEN 'EMPLOYEE DEPARTMENT MISMATCH'
END,
CASE WHEN NOT valid_department THEN 'MISSING DEPARTMENT' END,

CASE WHEN NOT valid_month THEN 'INVALID MONTH' END,
CASE WHEN NOT valid_year THEN 'INVALID YEAR' END,
CASE WHEN NOT valid_salary THEN 'INVALID SALARY' END,
CASE WHEN NOT valid_bonus THEN 'INVALID BONUS' END,
CASE WHEN NOT valid_payroll_expense THEN 'INVALID PAYROLL EXPENSE' END,
CASE WHEN NOT valid_unique_employee_month THEN 'DUPLICATE PAYROLL RECORDS PER EMPLOYEE' END,
CASE WHEN NOT valid_payroll_calculation THEN 'INVALID PAYROLL CALCULATION' END) AS rejection_reason FROM quality.payroll_validation
WHERE NOT ( valid_employee_reference 
AND valid_cost_center
AND valid_employee_cost_center 
AND valid_department
AND valid_department_reference
AND valid_employee_department
AND valid_month
AND valid_year
AND valid_salary
AND valid_bonus
AND valid_payroll_expense
AND valid_unique_employee_month
AND valid_payroll_calculation) 
""")

# ---------------------------------------------------------
# Inspect quality.payroll_rejects
# ---------------------------------------------------------

payroll_rejects = conn.execute(""" SELECT * FROM quality.payroll_rejects""").fetchall()

print("Payroll reject results: ")
for row in payroll_rejects:
    print(row)

# ---------------------------------------------------------
# Create budget validation
# ---------------------------------------------------------

conn.execute(""" CREATE OR REPLACE VIEW quality.budget_validation AS
SELECT  b."Cost Center", 
b."Department", 
cc.department AS department_code,
"Month",
"Year",
"Planned headcount",
"Planned payroll",
TRIM(b."Cost Center") IS NOT NULL
AND TRIM(b."Cost Center") <> ''
    AS valid_cost_center,
TRIM(b."Department") IS NOT NULL AND TRIM(b."Department") <>'' as valid_department,
cc.department IS NOT NULL as valid_department_reference,
"Month" IS NOT NULL AND"Month" BETWEEN 1 and 12 as valid_month,
"Year" IS NOT NULL and "Year" > 0 AS valid_year,
CASE WHEN "Planned headcount" IS NULL THEN TRUE
WHEN "Planned headcount" >= 0 THEN TRUE
ELSE FALSE END as valid_planned_headcount,
CASE WHEN "Planned payroll" IS NULL THEN TRUE
WHEN TRY_CAST(REPLACE(REPLACE(TRIM("Planned payroll"),'$',''),',','') AS DECIMAL(18,2)) IS NOT NULL THEN TRUE
ELSE FALSE END as valid_planned_payroll,
CASE WHEN "Planned headcount" IS  NULL AND "Planned payroll" IS NULL THEN TRUE
WHEN "Planned headcount" IS NOT NULL AND "Planned payroll" IS NOT NULL THEN TRUE
ELSE FALSE
END AS valid_headcount_payroll_consistency,
COUNT(*) OVER (
    PARTITION BY
        TRIM(b."Cost Center"),
        TRIM(b."Department"),
        b."Month",
        b."Year"
) = 1 AS valid_unique_department_budget
 FROM raw.budget as b
 LEFT JOIN trusted.cost_center AS cc
    ON TRIM(b."Cost Center") =
       TRIM(cc.cost_center)
   AND TRIM(b."Department") =
       TRIM(cc.department_description)
 """)

# ---------------------------------------------------------
# Inspect budget validation
# ---------------------------------------------------------
budget_validation_results = conn.execute(""" SELECT * FROM quality.budget_validation
""").fetchall()

print("Budget validation results: ")
for row in budget_validation_results:
    print(row) 


# ---------------------------------------------------------
# Create trusted.budget using budget validation
# ---------------------------------------------------------

conn.execute(""" CREATE OR REPLACE TABLE trusted.budget AS
SELECT TRIM("Cost Center") AS cost_center, 
department_code as department,
CAST("Month" AS INTEGER) as month,
CAST("Year"  AS INTEGER) as year,
CAST("Planned headcount"  AS INTEGER) as planned_headcount,
TRY_CAST(REPLACE(REPLACE(TRIM("Planned payroll"),'$',''),',','') AS DECIMAL(18,2)) as planned_payroll
 FROM
quality.budget_validation
WHERE (valid_cost_center
AND valid_department
AND valid_department_reference
AND valid_month
AND valid_year
AND valid_planned_headcount
AND valid_planned_payroll
AND valid_headcount_payroll_consistency
AND valid_unique_department_budget)
""")

# ---------------------------------------------------------
# Inspect trusted.budget
# ---------------------------------------------------------

trusted_budget_results = conn.execute(""" SELECT * FROM trusted.budget """).fetchall()

print("Trusted budget results: ")
for row in trusted_budget_results:
    print(row)

# ---------------------------------------------------------
# Create quality.budget_rejects using budget validation
# ---------------------------------------------------------

conn.execute(""" CREATE OR REPLACE TABLE quality.budget_rejects AS
SELECT "Cost Center",
"Department",
"Month",
"Year",
"Planned headcount",
"Planned payroll",
CONCAT_WS(', ',CASE
    WHEN NOT valid_cost_center
        THEN 'MISSING COST CENTER'
END,CASE WHEN NOT valid_department THEN 'MISSING DEPARTMENT' END,
CASE
    WHEN NOT valid_department_reference
        THEN 'INVALID COST CENTER / DEPARTMENT COMBINATION'
END,
CASE WHEN NOT valid_month THEN 'INVALID MONTH' END,
CASE WHEN NOT valid_year THEN 'INVALID YEAR' END,
CASE WHEN NOT valid_planned_headcount THEN 'INVALID PLANNED HEADCOUNT' END,
CASE WHEN NOT valid_planned_payroll THEN 'INVALID PLANNED PAYROLL' END,
CASE WHEN NOT valid_headcount_payroll_consistency THEN 'INVALID HEADCOUNT PAYROLL CONSISTENCY' END,
CASE WHEN NOT valid_unique_department_budget THEN 'INVALID UNIQUE DEPARTMENT BUDGET' END
) FROM quality.budget_validation
WHERE NOT(valid_cost_center
AND valid_department
AND valid_department_reference
AND valid_month
AND valid_year
AND valid_planned_headcount
AND valid_planned_payroll
AND valid_headcount_payroll_consistency
AND valid_unique_department_budget) 
""")

# ---------------------------------------------------------
# Inspect quality.budget_rejects
# ---------------------------------------------------------

budget_reject_results = conn.execute(""" SELECT * FROM quality.budget_rejects """).fetchall()

print("Reject budget results: ")
for row in budget_reject_results:
    print(row)

conn.close()
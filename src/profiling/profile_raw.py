import duckdb
from src.config import DB_PATH

"""Connect to Finance Duckdb"""
conn = duckdb.connect(DB_PATH)
print(f"Connected to duck db : {DB_PATH}")

"""Check the raw schema for the employees table"""
schema_info = conn.execute("DESCRIBE raw.employees").fetchall()
print("Schema for raw.employees")
for column in schema_info:
    print(column)

"""Check for duplicate employee IDS"""
duplicate_emp_ids = conn.execute("""select "Employee ID",
 count("Employee ID") as emp_id_ct from raw.employees 
group by all having count("Employee ID") > 1""").fetchall()
print(f"Duplicate employee IDS : {duplicate_emp_ids}")

"""Check for validity of employee IDs"""
valid_emp_ids = conn.execute("""select "Employee ID" 
from raw.employees where try_cast("Employee ID" as INTEGER) is NULL""").fetchall()
print(f"Invalid employee IDS are:{valid_emp_ids}")

"""Check for nulls in raw.employees table"""
null_profile = conn.execute("""select count(*) as row_ct,count(*)-count("Employee ID") as emp_id_nulls,
count(*) - count("First name") as firstname_nulls,
count(*) - count("Last name") as lastname_nulls,
count(*) - count("Start date") as startdate_nulls,
count(*) - count("End date") as enddate_nulls,
count(*) - count("Department") as department_nulls, 
count(*) - count("Job sub family") as jobsubfam_nulls,
count(*) - count("Job level") as joblevel_nulls,
count(*) - count("Comp region") as compregion_nulls 
from raw.employees""").fetchall()

print(f"Null profile : {null_profile}")

"""Profile business domain values"""
departments = conn.execute("""select distinct "Department" from raw.employees""").fetchall()
print(f"\nDepartment : {departments}")

job_sub_family = conn.execute("""select distinct "Job sub family" from raw.employees""").fetchall()
print(f"\nJob sub family : {job_sub_family}")

job_level = conn.execute("""select distinct "Job level" from raw.employees""").fetchall()
print(f"\nJob level : {job_level}")

comp_region = conn.execute("""select distinct "Comp region" from raw.employees""").fetchall()
print(f"\nComp region : {comp_region}")


reference_tables = ["cost_center","job_sub_family","job_level","comp_region"]

"""Schema and data profiling"""
for table_name in reference_tables:
    schema = conn.execute(f"DESCRIBE raw.{table_name}").fetchall()
    print(f"Schema for table : {table_name}")
    for column in schema:
        print(column)

"""Referential integrity profiling"""
invalid_job_level = conn.execute(f"""select e."Job level" from raw.employees as e LEFT join raw.job_level as jl ON e."Job level"= jl."Job level" where jl."Job level" is NULL """).fetchall()
print(f"Invalid job levels : {invalid_job_level}")

invalid_comp_regions = conn.execute(f"""select e."Comp region" from raw.employees as e LEFT JOIN raw.comp_region as cr ON e."Comp region" = cr."Comp Region Code" where cr."Comp Region Code" is NULL """ ).fetchall()
print(f"Invalid comp region : {invalid_comp_regions}")

invalid_job_sub_family = conn.execute(f"""select e."Job sub family" from raw.employees as e LEFT JOIN raw."job_sub_family" as jsf ON e."Job sub family" = jsf."Job sub family description" where jsf."Job sub family code" is NULL""").fetchall()
print(f"Invalid job sub families : {invalid_job_sub_family}")

"""Close the connection to Finance Duckdb"""
conn.close()
import duckdb
from src.config import DB_PATH

conn = duckdb.connect(DB_PATH)

print(f"Connected to database: {DB_PATH}")
print("Starting Trusted layer controls...")

# ---------------------------------------------------------------------------
# CONTROL 1: RAW → TRUSTED ROW RECONCILIATION
# ---------------------------------------------------------------------------
# Every Raw record must be accounted for after Trusted-layer processing.
# A source record must either:
#   1. qualify for the Trusted dataset, or
#   2. be captured in the corresponding Quality reject table.
#
# Contract:
# Raw count = Trusted count + Rejected count
#
# This prevents records from being silently dropped during transformation.

def run_reconciliation_control(control_name):
    raw_count = conn.execute(f""" SELECT COUNT(*) FROM raw.{control_name} """).fetchone()[0]
    trusted_count = conn.execute(f""" SELECT COUNT(*) FROM trusted.{control_name} """).fetchone()[0]
    rejected_count = conn.execute(f""" SELECT COUNT(*) FROM quality.{control_name}_rejects """).fetchone()[0]
    print(f"\n{control_name} reconciliation controls:")
    print(f"Raw {control_name} count: {raw_count}")
    print(f"Trusted {control_name} count: {trusted_count}")
    print(f"Rejected {control_name} count: {rejected_count}")
    if raw_count != trusted_count + rejected_count:
        raise ValueError(
        f"{control_name} reconciliation failed: raw={raw_count}, trusted = {trusted_count}, rejected = {rejected_count}"
    )

    print(f"{control_name} reconciliation passed.")


run_reconciliation_control("job_level")
run_reconciliation_control("job_sub_family")
run_reconciliation_control("comp_region")
run_reconciliation_control("cost_center")
run_reconciliation_control("employees")
run_reconciliation_control("payroll")
run_reconciliation_control("budget")


# ---------------------------------------------------------------------------
# CONTROL 2: TRUSTED GRAIN UNIQUENESS
# ---------------------------------------------------------------------------
# Verify that each Trusted dataset contains only one record at its
# declared business grain.
#
# Examples:
#   employees → one row per employee
#   payroll   → one row per employee per reporting month
#   budget    → one row per cost center + department + reporting month
#
# Duplicate records at the declared grain could cause downstream
# measures such as payroll and headcount to be overstated.

def run_uniqueness_control(control_name, grain_columns):
    grain = ", ".join(grain_columns)
    duplicates = conn.execute(f""" SELECT
    {grain},
    COUNT(*) AS record_count
    FROM trusted.{control_name}
    GROUP BY {grain}
    HAVING COUNT(*) > 1; """).fetchall()
    print(f"\n{control_name} uniqueness control:")
    print(f"Grain: {grain}")
    print(f"Duplicate records: {duplicates}")

    if duplicates:
        raise ValueError(f"{control_name} uniqueness control failed: {duplicates}")
    print(f"{control_name} uniqueness control passed for grain {grain}")

run_uniqueness_control(
    "employees", 
    ["employee_id"]
    )

run_uniqueness_control(
    "payroll",
    ["employee_id", "month", "year"]
    )

run_uniqueness_control(
    "budget",
    ["cost_center", "department", "month", "year"]
    )



# ---------------------------------------------------------------------------
# CONTROL 3: CROSS-DATASET REFERENTIAL INTEGRITY
# ---------------------------------------------------------------------------
# Verify that relationships between Trusted datasets remain valid.
#
# These controls ensure that:
#   - every payroll employee exists in trusted.employees
#   - every payroll cost center/department exists in trusted.cost_center
#   - every budget cost center/department exists in trusted.cost_center
#
# LEFT JOIN + NULL on the parent side identifies orphaned child records.

def run_referential_integrity_control(control_name,child_table,parent_table,join_condition,parent_key):
    invalid_count = conn.execute(f"""
    SELECT COUNT(*)
    FROM trusted.{child_table} child
    LEFT JOIN trusted.{parent_table} parent
        ON {join_condition}
    WHERE parent.{parent_key} IS NULL
""").fetchone()[0]
    print(f"\n{control_name}:")
    print(f"Invalid references: {invalid_count}")

    if invalid_count:
        raise ValueError(f"{control_name} referential integrity control failed. Invalid references: {invalid_count}")
    print(f"{control_name} referential integrity control passed. ")

run_referential_integrity_control( "Payroll → Employee","payroll", "employees","child.employee_id = parent.employee_id","employee_id" )

run_referential_integrity_control( "Payroll → Cost Center & Department","payroll", "cost_center","child.cost_center = parent.cost_center AND child.department = parent.department","department" )

run_referential_integrity_control("Budget → Cost Center & Department","budget","cost_center","child.cost_center = parent.cost_center AND child.department = parent.department","department")


# ---------------------------------------------------------------------------
# CONTROL 4: PAYROLL → EMPLOYEE TEMPORAL CONSISTENCY
# ---------------------------------------------------------------------------
# Verify that payroll is not recorded outside an employee's active
# employment period.
#
# An employee is considered active for a payroll month when:
#   start_date <= last day of the payroll month
#   AND
#   end_date is NULL OR end_date >= first day of the payroll month
#
# Unlike row-level validation, this is a cross-domain consistency rule:
# payroll may be valid on its own and the employee record may be valid
# on its own, while the two records can still contradict each other.
#
# Violations are persisted as Quality evidence before the pipeline is
# blocked. This allows the inconsistency to be investigated rather than
# silently removing payroll or employee data.

conn.execute(""" CREATE OR REPLACE TABLE quality.payroll_temporal_violations AS SELECT
    p.employee_id,
    p.month,
    p.year,
    e.start_date,
    e.end_date
FROM trusted.payroll p
INNER JOIN trusted.employees e
    ON p.employee_id = e.employee_id
WHERE NOT (
    e.start_date <= LAST_DAY(MAKE_DATE(p.year, p.month, 1))
    AND (
        e.end_date IS NULL
        OR e.end_date >= MAKE_DATE(p.year, p.month, 1)
    )
) """)


# Read the persisted violation evidence to determine whether publication
# of the Trusted layer should be allowed to continue.

temporal_violations = conn.execute(""" SELECT * FROM quality.payroll_temporal_violations """).fetchall()

print("\nPayroll → Employee temporal consistency control:")
print(f"Temporal violations: {temporal_violations}")

if temporal_violations:
    raise ValueError(f"Payroll → Employee temporal consistency control failed. Payroll records exist outside employee active employment periods: {temporal_violations} ")
print("Payroll → Employee temporal consistency control passed.")

# ---------------------------------------------------------------------------
# TRUSTED PUBLICATION GATE
# ---------------------------------------------------------------------------
# Reaching this point means all Trusted-layer publication controls passed.
# The pipeline can proceed to build the Business layer.

print("\nAll Trusted layer controls passed.")

conn.close()


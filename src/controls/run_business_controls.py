import duckdb
from src.config import DB_PATH

conn = duckdb.connect(DB_PATH)

print(f"Connected to database: {DB_PATH}")
print("Starting Business layer controls...")

# ---------------------------------------------------------------------------
# CONTROL 1: BUSINESS GRAIN UNIQUENESS
# ---------------------------------------------------------------------------
# department_monthly_performance is defined at one row per
# cost center + department + reporting month + reporting year.
# Duplicate rows at this grain could cause downstream metrics to be overstated.

duplicates = conn.execute("""
    SELECT
        cost_center,
        department,
        month,
        year,
        COUNT(*) AS record_count
    FROM business.department_monthly_performance
    GROUP BY
        cost_center,
        department,
        month,
        year
    HAVING COUNT(*) > 1
""").fetchall()

print("\nBusiness grain uniqueness control:")
print(f"Duplicate records: {duplicates}")

if duplicates:
    raise ValueError(
        f"Business grain uniqueness control failed: {duplicates}"
    )

print("Business grain uniqueness control passed.")

# ---------------------------------------------------------------------------
# CONTROL 2: ACTUAL PAYROLL RECONCILIATION
# ---------------------------------------------------------------------------
# Verify that payroll dollars from the authoritative Trusted payroll dataset
# are fully preserved in the Business performance model.
# This detects dropped or duplicated amounts during joins and aggregation.

trusted_payroll_total = conn.execute("""
    SELECT cost_center,
        department,month,
        year, SUM(payroll_expense) 
    FROM trusted.payroll
    GROUP BY
        cost_center,
        department,
        month,
        year
    ORDER BY
       cost_center,
        department,
        year,
        month
""").fetchall()

business_payroll_total = conn.execute("""
    SELECT cost_center,
        department,month,
        year,SUM(actual_payroll)
    FROM business.department_monthly_performance
    WHERE actual_payroll IS NOT NULL
    GROUP BY
        cost_center,
        department,
        month,
        year
    ORDER BY
        cost_center,
        department,
        year,
        month
""").fetchall()

print("\nActual payroll reconciliation control:")
print(f"Trusted actual monthly payroll by Business grain: {trusted_payroll_total}")
print(f"Business actual monthly payroll by Business grain: {business_payroll_total}")

if trusted_payroll_total != business_payroll_total:
    raise ValueError(
        f"Actual payroll reconciliation failed: "
        f"Trusted = {trusted_payroll_total}, "
        f"Business = {business_payroll_total}"
    )

print("Actual payroll reconciliation control passed.")


# ---------------------------------------------------------------------------
# CONTROL 3: PLANNED PAYROLL RECONCILIATION
# ---------------------------------------------------------------------------
# Verify that planned payroll from the authoritative Trusted budget dataset
# is fully represented in the Business performance model.


trusted_planned_payroll_total = conn.execute("""
    SELECT   cost_center,
        department,month,
        year,SUM(planned_payroll)
    FROM trusted.budget
    GROUP BY
    cost_center,
    department,
    month,
    year
    ORDER BY
    cost_center,
    department,
    year,
    month
""").fetchall()

business_planned_payroll_total = conn.execute("""
    SELECT  cost_center,
        department,month,
        year,SUM(planned_payroll)
    FROM business.department_monthly_performance
    GROUP BY
    cost_center,
    department,
    month,
    year
    ORDER BY
    cost_center,
    department,
    year,
    month
""").fetchall()

print("\nPlanned payroll reconciliation control:")
print(f"Trusted planned monthly payroll by Business grain: {trusted_planned_payroll_total}")
print(f"Business planned monthly payroll by Business grain: {business_planned_payroll_total}")

if trusted_planned_payroll_total != business_planned_payroll_total:
    raise ValueError(
        f"Planned payroll reconciliation failed: "
        f"Trusted = {trusted_planned_payroll_total}, "
        f"Business = {business_planned_payroll_total}"
    )

print("Planned payroll reconciliation control passed.")


# ---------------------------------------------------------------------------
# CONTROL 4: ACTUAL HEADCOUNT RECONCILIATION
# ---------------------------------------------------------------------------
# Independently recalculate monthly headcount from trusted.employees.
#
# An employee counts as active when their employment overlaps any portion
# of the reporting month:
#   start_date <= last day of reporting month
#   AND
#   end_date is NULL OR end_date >= first day of reporting month
#
# Reporting periods are derived from the trusted.budget so the control
# validates the periods actually being published.

trusted_actual_headcount = conn.execute("""
    SELECT e.cost_center,
        e.department, p.month, p.year,COUNT(DISTINCT e.employee_id)
    FROM trusted.employees e
    CROSS JOIN (
        SELECT DISTINCT month, year
        FROM trusted.budget
    ) p
    WHERE
        e.start_date <= LAST_DAY(MAKE_DATE(p.year, p.month, 1))
        AND (
            e.end_date IS NULL
            OR e.end_date >= MAKE_DATE(p.year, p.month, 1)
        )
        GROUP BY e.cost_center, e.department, p.month, p.year
        ORDER BY e.cost_center,
        e.department, p.year, p.month
""").fetchall()

business_actual_headcount = conn.execute("""
    SELECT cost_center,
        department,month,
        year,SUM(actual_headcount)
    FROM business.department_monthly_performance
    GROUP BY cost_center,
        department,month, year
        ORDER BY cost_center,
        department, month, year
""").fetchall()

print("\nActual headcount reconciliation control:")
print(f"Trusted eligible employee headcount: {trusted_actual_headcount}")
print(f"Business actual headcount: {business_actual_headcount}")

if trusted_actual_headcount != business_actual_headcount:
    raise ValueError(
        f"Actual headcount reconciliation failed: "
        f"Trusted = {trusted_actual_headcount}, "
        f"Business = {business_actual_headcount}"
    )

print("Actual headcount reconciliation control passed.")


# ---------------------------------------------------------------------------
# CONTROL 5: PLANNED HEADCOUNT RECONCILIATION
# ---------------------------------------------------------------------------
# Verify that planned headcount from the Trusted budget dataset is fully
# represented in the Business performance model.

trusted_planned_headcount = conn.execute("""
    SELECT cost_center,
        department,month,
        year,SUM(planned_headcount)
    FROM trusted.budget
    GROUP BY cost_center,
        department, month, year
        ORDER BY cost_center,
        department, month, year
""").fetchall()

business_planned_headcount = conn.execute("""
    SELECT cost_center,
        department,month,
        year,SUM(planned_headcount)
    FROM business.department_monthly_performance
    GROUP BY cost_center,
        department,month, year
        ORDER BY cost_center,
        department, month, year
""").fetchall()

print("\nPlanned headcount reconciliation control:")
print(f"Trusted planned monthly headcount: {trusted_planned_headcount}")
print(f"Business planned monthly headcount: {business_planned_headcount}")

if trusted_planned_headcount != business_planned_headcount:
    raise ValueError(
        f"Planned headcount reconciliation failed: "
        f"Trusted = {trusted_planned_headcount}, "
        f"Business = {business_planned_headcount}"
    )

print("Planned headcount reconciliation control passed.")


# ---------------------------------------------------------------------------
# CONTROL 6: VARIANCE INTEGRITY
# ---------------------------------------------------------------------------
# Verify derived Business metrics at the row level.
#
# Payroll variance   = Actual payroll   - Planned payroll
# Headcount variance = Actual headcount - Planned headcount
#
# Checking every row prevents incorrect derived metrics from being hidden
# by totals that may still reconcile.

invalid_variances = conn.execute("""
    SELECT
        cost_center,
        department,
        month,
        year,
        actual_payroll,
        planned_payroll,
        payroll_variance,
        actual_headcount,
        planned_headcount,
        headcount_variance
    FROM business.department_monthly_performance
    WHERE
    (actual_payroll IS NULL AND payroll_variance IS NOT NULL)
    OR
    (actual_payroll IS NOT NULL
    AND (payroll_variance IS NULL OR payroll_variance != actual_payroll - planned_payroll))
    OR headcount_variance != actual_headcount - planned_headcount
""").fetchall()

print("\nVariance integrity control:")
print(f"Invalid variance records: {invalid_variances}")

if invalid_variances:
    raise ValueError(
        f"Variance integrity control failed: {invalid_variances}"
    )

print("Variance integrity control passed.")

print("\nAll Business layer controls passed.")

conn.close()

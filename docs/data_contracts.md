# Data Contracts

## Employees

### Source

`raw.employees`

### Trusted Target

`trusted.employees`

### Grain

One record per employee.

### Trusted Schema

| Column | Type | Required | Rule |
|---|---|---|---|
| employee_id | VARCHAR | Yes | Numeric format and unique |
| first_name | VARCHAR | Yes | Non-null and non-blank |
| last_name | VARCHAR | Yes | Non-null and non-blank |
| start_date | DATE | Yes | Valid date |
| end_date | DATE | No | Valid date when populated |
| department | VARCHAR | Yes | Must exist in department reference |
| job_sub_family | VARCHAR | Yes | Must exist in job-sub-family reference |
| job_level | VARCHAR | Yes | Must exist in job-level reference |
| comp_region | VARCHAR | Yes | Must exist in compensation-region reference |

### Cross-Field Rules

- `end_date` must be greater than or equal to `start_date` when populated.

### Standardization

- Leading and trailing whitespace is removed from text attributes.
- Source column names are converted to standardized snake_case names.
- Date strings are converted to DATE values.

### Rejection Handling

Records failing one or more required validation rules are excluded from
`trusted.employees` and written to:

`quality.employee_rejects`

A rejected record retains the source values and includes the applicable
rejection reason(s).

### Reconciliation

Every raw employee record must be accounted for as either Trusted or Rejected:

`raw_count = trusted_count + rejected_count`

---

## Job Level

### Source

`raw.job_level`

### Trusted Target

`trusted.job_level`

### Grain

One record per job level.

### Key

`job_level`

### Trusted Schema

| Column | Type | Required | Rule |
|---|---|---|---|
| job_level | VARCHAR | Yes | Non-null, non-blank, unique, and must follow the `L<number>` format |

### Validation Rules

- `job_level` must be populated.
- `job_level` must follow the `L<number>` format, such as `L3`, `L8`, or `L11`.
- `job_level` must be unique within the Job Level reference dataset.

### Standardization

- Leading and trailing whitespace is removed from `job_level`.

### Rejection Handling

Records failing one or more validation rules are excluded from
`trusted.job_level` and written to:

`quality.job_level_rejects`

The applicable rejection reason(s) are retained.

### Reconciliation

Every Raw Job Level record must be accounted for as either Trusted or Rejected:

`raw_count = trusted_count + rejected_count`

## Job Sub-Family

### Source

`raw.job_sub_family`

### Trusted Target

`trusted.job_sub_family`

### Grain

One record per job sub-family.

### Key

`job_sub_family_code`

### Trusted Schema

| Column | Type | Required | Rule |
|---|---|---|---|
| job_sub_family_code | VARCHAR | Yes | Non-null, non-blank, unique, and must follow the `JSF_...` format |
| job_sub_family_description | VARCHAR | Yes | Non-null, non-blank, and unique |

### Validation Rules

- `job_sub_family_code` must be populated.
- `job_sub_family_code` must be unique within the reference dataset.
- `job_sub_family_code` must follow the `JSF_...` code format.
- `job_sub_family_description` must be populated.
- `job_sub_family_description` must be unique within the reference dataset.

### Standardization

- Source column names are standardized to snake_case.
- Leading and trailing whitespace is removed from code and description.

### Rejection Handling

Records failing one or more required validation rules are excluded from
`trusted.job_sub_family` and written to:

`quality.job_sub_family_rejects`

### Reconciliation

Every Raw Job Sub-Family record must be accounted for as either Trusted or Rejected:

`raw_count = trusted_count + rejected_count`

---

## Compensation Region

### Source

`raw.comp_region`

### Trusted Target

`trusted.comp_region`

### Grain

One record per compensation region.

### Key

`comp_region_code`

### Trusted Schema

| Column | Type | Required | Rule |
|---|---|---|---|
| comp_region_code | VARCHAR | Yes | Non-null, non-blank, unique, uppercase code format |
| comp_region_description | VARCHAR | Yes | Non-null, non-blank, unique |

### Validation Rules

- `comp_region_code` must be populated.
- `comp_region_code` must be unique within the reference dataset.
- `comp_region_code` may contain uppercase letters, numbers, and underscores.
- `comp_region_description` must be populated.
- `comp_region_description` must be unique within the reference dataset.

### Standardization

- Source column names are standardized to snake_case.
- Leading and trailing whitespace is removed from code and description.

### Rejection Handling

Records failing one or more validation rules are excluded from
`trusted.comp_region` and written to:

`quality.comp_region_rejects`

### Reconciliation

Every Raw Compensation Region record must be accounted for as either Trusted or Rejected:

`raw_count = trusted_count + rejected_count`

---

## Cost Center

### Source

`raw.cost_center`

### Trusted Target

`trusted.cost_center`

### Grain

One record per Cost Center and Department combination.

### Key

Composite key:

`(cost_center, department)`

### Trusted Schema

| Column | Type | Required | Rule |
|---|---|---|---|
| cost_center | VARCHAR | Yes | Non-null and non-blank |
| cost_center_description | VARCHAR | Yes | Non-null and non-blank |
| department | VARCHAR | Yes | Non-null, non-blank, expected code format |
| department_description | VARCHAR | Yes | Non-null and non-blank |
| vp | VARCHAR | Yes | Non-null and non-blank |
| region | VARCHAR | Yes | Non-null and non-blank |

### Validation Rules

- `cost_center` must be populated.
- `cost_center_description` must be populated.
- `department` must be populated.
- `department_description` must be populated.
- `vp` must be populated.
- `region` must be populated.
- The combination `(cost_center, department)` must be unique.

### Standardization

- Source column names are standardized to snake_case.
- Leading and trailing whitespace is removed from text attributes.

### Rejection Handling

Records failing one or more validation rules are excluded from
`trusted.cost_center` and written to:

`quality.cost_center_rejects`

### Reconciliation

Every Raw Cost Center record must be accounted for as either Trusted or Rejected:

`raw_count = trusted_count + rejected_count`

---

## Payroll

### Source

`raw.payroll`

### Trusted Target

`trusted.payroll`

### Grain

One payroll record per employee per month and year.

### Key

Composite key:

`(employee_id, month, year)`

### Trusted Schema

| Column | Type | Required | Rule |
|---|---|---|---|
| employee_id | VARCHAR | Yes | Must reference a valid employee in `trusted.employees` |
| department | VARCHAR | Yes | Must match the employee's department in `trusted.employees` |
| month | INTEGER | Yes | Must be between 1 and 12 |
| year | INTEGER | Yes | Must represent a valid reporting year |
| salary | DECIMAL | Yes | Must be a valid monetary amount |
| bonus | DECIMAL | Yes | Must be a valid monetary amount |
| payroll_expense | DECIMAL | Yes | Must be a valid monetary amount |

### Validation Rules

- `employee_id` must be populated.
- `employee_id` must exist in `trusted.employees`.
- `department` must be populated.
- Payroll department must match the employee's department in `trusted.employees`.
- `month` must be between 1 and 12.
- `year` must be a valid reporting year.
- `salary` must be a valid monetary amount.
- `bonus` must be a valid monetary amount.
- `payroll_expense` must be a valid monetary amount.
- `(employee_id, month, year)` must be unique.
- `salary + bonus` must equal `payroll_expense`.

### Standardization

- Column names are standardized to snake_case.
- Employee ID is standardized to VARCHAR for consistency with `trusted.employees`.
- Currency formatting such as `$` and `,` is removed.
- Monetary values are converted to DECIMAL.
- Text attributes are trimmed.

### Rejection Handling

Records failing one or more validation rules are excluded from
`trusted.payroll` and written to:

`quality.payroll_rejects`

All applicable rejection reasons should be retained.

### Reconciliation

Every Raw Payroll record must be accounted for as either Trusted or Rejected:

`raw_count = trusted_count + rejected_count`

## Budget

**Source:** `raw.budget`  
**Target:** `trusted.budget`

### Grain
One record per Department + Month + Year.

### Key
Composite key:
- `department`
- `month`
- `year`

### Trusted Schema

| Field | Rule |
|---|---|
| `department` | Required; must reference a valid trusted department |
| `month` | Required; integer between 1 and 12 |
| `year` | Required; positive integer |
| `planned_headcount` | Optional. If populated, must be a non-negative integer. NULL is permitted and represents no planned headcount value for that department/month/year.|
| `planned_payroll` | Required; valid monetary value |

### Validation Rules
- Department must be populated.
- Department must exist in the trusted organizational data.
- Month must be between 1 and 12.
- Year must be valid.
- Planned headcount Optional and non-negative if exists.
- Planned payroll must be parseable as a monetary value.
- `(department, month, year)` must be unique.

### Standardization
- Rename columns to snake_case.
- Trim Department.
- Convert Planned headcount to integer.
- Remove `$` and `,` from Planned payroll and convert to `DECIMAL(18,2)`.

### Reject Handling
Records failing any validation rule are written to `quality.budget_rejects` with the applicable rejection reason(s).

### Reconciliation
`raw.budget count = trusted.budget count + quality.budget_rejects count`

## Metric Contract: Payroll Variance

**Metric Name:** Payroll Variance

**Business Definition:**  
Difference between actual payroll expense and planned payroll expense for a cost center and department during a reporting month.

**Formula:**  
Payroll Variance = Actual Payroll - Planned Payroll

**Grain:**  
Cost Center + Department + Month + Year

**Authoritative Source:**  
business.department_monthly_performance

**Input Metrics:**  
- actual_payroll
- planned_payroll

**Interpretation:**  
- Positive value = actual payroll is above plan
- Negative value = actual payroll is below plan
- Zero = actual payroll equals plan

**Unit:**  
Currency

**Aggregation Behavior:**  
Additive across departments and cost centers for the same reporting period.

Additive across reporting periods when measuring cumulative payroll variance.

**Null Handling:**  
A missing actual or planned payroll value should not automatically be interpreted as zero.

## Metric Contract: Actual Headcount

**Metric Name:** Actual Headcount

**Business Definition:**  
Number of distinct employees who were active for any portion of the reporting month, based on the employee master.

An employee is considered active during a reporting month when:
- start_date is on or before the last day of the reporting month, and
- end_date is NULL or on or after the first day of the reporting month.

**Formula:**  
COUNT(DISTINCT active employee_id)

**Grain:**  
Cost Center + Department + Month + Year

**Authoritative Source:**  
business.department_monthly_performance

**Underlying Source:**  
trusted.employees

**Interpretation:**  
Represents the number of employees whose employment period overlaps the reporting month.

Payroll activity does not determine whether an employee is counted as active.

**Unit:**  
Employees

**Aggregation Behavior:**  
Additive across mutually exclusive departments and cost centers within the same reporting period.

Not additive across reporting periods.

**Null Handling:**  
An employee with a NULL end_date is treated as having no recorded employment end date.

## Metric Contract: Actual Payroll

**Metric Name:** Actual Payroll

**Business Definition:**  
Total actual payroll expense incurred by a cost center and department during a reporting month.

**Formula:**  
SUM(payroll_expense)

**Grain:**  
Cost Center + Department + Month + Year

**Authoritative Source:**  
business.department_monthly_performance

**Underlying Source:**  
trusted.payroll

**Unit:**  
Currency

**Aggregation Behavior:**  
Additive across departments, cost centers, and reporting periods.

**Null Handling:**  
A missing actual payroll value should not automatically be interpreted as zero.


## Metric Contract: Planned Payroll

**Metric Name:** Planned Payroll

**Business Definition:**  
Planned payroll expense for a cost center and department during a reporting month.

**Grain:**  
Cost Center + Department + Month + Year

**Authoritative Source:**  
business.department_monthly_performance

**Underlying Source:**  
trusted.budget

**Unit:**  
Currency

**Aggregation Behavior:**  
Additive across departments, cost centers, and reporting periods.

**Null Handling:**  
A missing planned payroll value should not automatically be interpreted as zero.


## Metric Contract: Planned Headcount

**Metric Name:** Planned Headcount

**Business Definition:**  
Planned number of employees for a cost center and department during a reporting month.

**Grain:**  
Cost Center + Department + Month + Year

**Authoritative Source:**  
business.department_monthly_performance

**Underlying Source:**  
trusted.budget

**Unit:**  
Employees

**Aggregation Behavior:**  
Additive across mutually exclusive departments and cost centers within the same reporting period.

Not additive across reporting periods.

**Null Handling:**  
A missing planned headcount value should not automatically be interpreted as zero.


## Metric Contract: Headcount Variance

**Metric Name:** Headcount Variance

**Business Definition:**  
Difference between actual active employee headcount and planned headcount for a cost center and department during a reporting month.

**Formula:**  
Headcount Variance = Actual Headcount - Planned Headcount

**Grain:**  
Cost Center + Department + Month + Year

**Authoritative Source:**  
business.department_monthly_performance

**Input Metrics:**  
- actual_headcount
- planned_headcount

**Interpretation:**  
- Positive value = actual headcount is above plan
- Negative value = actual headcount is below plan
- Zero = actual headcount equals plan

**Unit:**  
Employees

**Aggregation Behavior:**  
Additive across mutually exclusive departments and cost centers within the same reporting period.

Not additive across reporting periods.

**Null Handling:**  
A missing actual or planned headcount value should not automatically be interpreted as zero.
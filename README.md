# AI-Ready Finance Data Platform

A governed finance data platform that transforms raw operational data into trusted, consumption-ready business metrics through deterministic data quality controls, semantic definitions, and pipeline observability.

The project demonstrates how a reliable data foundation can be established before introducing AI capabilities. The deterministic platform remains the source of truth, while future AI capabilities will focus on improving how governed data and metadata are discovered, investigated, and consumed.

## Project Objective

The platform models a simplified finance data ecosystem using employee, payroll, budget, and organizational reference data.

It demonstrates the journey from source data to governed business metrics:

**Source Data → Raw → Validation & Quality → Trusted → Business → Semantic Metrics → Observability**

The deterministic V1 focuses on establishing:

- Source-data preservation and profiling
- Explicit data contracts and validation rules
- Trusted datasets with rejected-record evidence
- Referential and temporal integrity controls
- Finance business metrics for payroll and headcount
- Actual-versus-plan variance analysis
- Governed semantic metric definitions
- Pipeline-level and dataset-level observability

AI capabilities are intentionally introduced only after this deterministic foundation is established.

## Architecture

The platform separates source fidelity, data validation, trusted data, business logic, semantic definitions, and operational monitoring into distinct layers.

```text
Source CSVs
    │
    ▼
┌─────────────────────────┐
│          RAW            │
│ Preserve what arrived   │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│   QUALITY & VALIDATION  │
│ Validate data contracts │
│ Capture rejected rows   │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│        TRUSTED          │
│ Standardized, validated │
│ canonical datasets      │
└────────────┬────────────┘
             │
        Quality Gates
             │
             ▼
┌─────────────────────────┐
│        BUSINESS         │
│ Finance-ready metrics   │
│ Actual vs. Plan         │
└────────────┬────────────┘
             │
        Quality Gates
             │
             ▼
┌─────────────────────────┐
│        SEMANTIC         │
│ Governed metric         │
│ definitions             │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│     OBSERVABILITY       │
│ Pipeline & dataset      │
│ run evidence            │
└─────────────────────────┘
```

### Layer Responsibilities

| Layer | Responsibility |
|---|---|
| **Source** | Synthetic employee, payroll, budget, and organizational reference data representing upstream operational systems. |
| **Raw** | Preserves source data with minimal transformation and provides a reproducible point of entry into the platform. |
| **Quality & Validation** | Evaluates data contracts and business rules, identifies invalid records, and preserves rejection evidence. |
| **Trusted** | Publishes standardized and validated datasets using canonical identifiers and consistent data types. |
| **Business** | Produces finance-ready payroll, headcount, plan, and variance metrics at a defined business grain. |
| **Semantic** | Defines governed metric meaning, grain, source, aggregation behavior, interpretation, and null handling. |
| **Observability** | Records pipeline execution status and dataset-level Raw → Trusted → Rejected reconciliation evidence. |

The pipeline uses quality gates between major publication layers. A failed critical control stops downstream processing rather than allowing invalid data to silently propagate.

## Data Journey & Governance

The platform follows a governed data journey in which records become progressively more standardized and consumption-ready while retaining evidence of validation outcomes.

### Raw → Trusted

Raw data preserves the structure and values received from source files. Before records are published to the Trusted layer, validation rules evaluate dataset-specific contracts such as:

- Required identifiers and valid data types
- Grain uniqueness
- Valid organizational mappings
- Reference-data integrity
- Employee and payroll relationships
- Employment-date and payroll-period consistency

Records that satisfy the required rules are standardized and published to Trusted datasets. Records that fail validation are preserved separately in the `quality` schema with rejection reasons rather than being silently discarded.

For example, duplicate payroll records at the employee-month grain are rejected, while valid payroll records are standardized into canonical identifiers and numeric monetary values.

### Reconciliation & Publication Gates

The platform treats data quality controls as publication gates rather than passive monitoring.

For each governed dataset:

**Raw Records = Trusted Records + Rejected Records**

Additional controls verify grain uniqueness, referential integrity, and temporal consistency. Critical control failures stop the pipeline before downstream Business datasets are published.

This prevents downstream metrics from being built on data that has failed required integrity checks.

### Canonical Business Identifiers

Source systems may represent the same business concept differently. The Trusted layer therefore uses canonical codes and identifiers rather than relying on descriptive labels.

For example, organizational descriptions are validated against reference data and resolved to governed cost-center and department codes before downstream consumption.

This separates human-readable descriptions from the identifiers used to establish reliable joins, relationships, and business grain.

### NULL Is Not Zero

The Business layer deliberately distinguishes missing data from a known value of zero.

For example, if payroll actuals are unavailable for a reporting period:

- `NULL` means the actual value is unavailable.
- `0` means the actual value is known and is zero.

The platform therefore preserves `NULL` for unavailable actuals and does not calculate a variance until the required values exist. This prevents missing finance data from being incorrectly interpreted as zero activity.

## Business & Semantic Layers

### Business Layer

The Business layer converts governed Trusted data into finance-ready datasets designed to answer a specific business question:

> **How is each cost center and department performing against monthly payroll and headcount budget?**

The primary dataset, `business.department_monthly_performance`, operates at the following grain:

**Cost Center + Department + Month + Year**

It brings together actual and planned measures to provide:

| Metric | Purpose |
|---|---|
| `actual_payroll` | Actual payroll expense from validated payroll records |
| `planned_payroll` | Budgeted payroll expense |
| `payroll_variance` | Actual payroll minus planned payroll |
| `actual_headcount` | Employees active during the reporting month |
| `planned_headcount` | Budgeted headcount |
| `headcount_variance` | Actual headcount minus planned headcount |

Payroll actuals are derived from validated payroll transactions, while actual headcount is calculated independently from employee employment dates. This avoids using payroll activity as a proxy for workforce headcount.

Business-layer controls reconcile these measures back to their governed Trusted sources and validate the integrity of calculated variances before publication.

### Semantic Layer

The Semantic layer defines the business meaning and expected behavior of metrics independently from the SQL that calculates them.

Metric definitions are maintained in:

`metadata/metrics.yaml`

Each governed metric can describe characteristics such as:

- Business definition
- Source table and column
- Business grain
- Unit of measure
- Input metrics
- Calculation formula
- Positive, negative, and zero interpretation
- Aggregation behavior
- NULL handling

The semantic validation process verifies that metric definitions are structurally complete and that referenced tables, columns, and grain fields exist in the deterministic data platform.

This distinction is particularly important for measures such as headcount. Payroll can generally be aggregated across both organizational dimensions and reporting periods, while headcount is additive across organizational units but **non-additive across time**.

The Semantic layer therefore provides governed context about not only where a metric comes from, but also how it should—and should not—be interpreted and aggregated.

## Observability

The pipeline records execution evidence in the `quality` schema so that successful and failed runs can be inspected after execution.

### Pipeline-Level Observability

`quality.pipeline_runs` records:

- Unique pipeline run ID
- Start time
- End time
- Final status
- Error message when a run fails

### Dataset-Level Observability

`quality.dataset_runs_summary` records Raw, Trusted, and Rejected row counts for each governed dataset.

This provides historical evidence of how records moved through the platform and complements the blocking quality controls used during pipeline execution.

Observability is deliberately separated from validation:

- **Validation** determines whether data satisfies defined rules.
- **Controls** determine whether downstream publication is allowed.
- **Observability** records evidence about what happened during execution.

## Running the Project

### Prerequisites

- Python 3
- Git
- A Python virtual environment

The project uses DuckDB as the local analytical database. Required Python packages are defined in `requirements.txt`.

### Setup

Clone the repository and navigate to the project directory:

```bash
git clone https://github.com/ameyatalwar/ai-ready-finance-data-platform.git
cd ai-ready-finance-data-platform
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### Run the Full Pipeline

From the project root, run:

```bash
python -m src.orchestration.run_pipeline
```

The orchestrator executes the platform in the following sequence:

```text
Raw Ingestion
      ↓
Raw Profiling
      ↓
Trusted Layer Build
      ↓
Trusted Quality Gate
      ↓
Business Layer Build
      ↓
Business Quality Gate
      ↓
Semantic Validation
      ↓
Observability
```

A successful run ends with a pipeline completion message and records execution evidence in the `quality` schema.

The local DuckDB database is generated at:

`data/finance.duckdb`

Database files are intentionally excluded from Git version control. The repository contains the source data and code required to rebuild the platform from scratch.

## Repository Structure

```text
ai-ready-finance-data-platform/
│
├── data/
│   └── source/                  # Synthetic source datasets
│
├── docs/
│   └── data_contracts.md        # Data contracts and governance rules
│
├── metadata/
│   └── metrics.yaml             # Governed semantic metric definitions
│
├── src/
│   ├── config.py                # Shared project paths and configuration
│   │
│   ├── ingestion/
│   │   └── ingest_raw.py        # Source → Raw ingestion
│   │
│   ├── profiling/
│   │   └── profile_raw.py       # Raw data profiling
│   │
│   ├── transformation/
│   │   ├── build_trusted.py     # Validation, standardization, Trusted datasets
│   │   └── build_business.py    # Finance-ready Business datasets
│   │
│   ├── controls/
│   │   ├── run_trusted_controls.py
│   │   └── run_business_controls.py
│   │
│   ├── semantic/
│   │   └── load_metrics.py      # Semantic metric validation
│   │
│   └── orchestration/
│       └── run_pipeline.py      # End-to-end pipeline orchestration
│
├── .gitignore
├── requirements.txt
└── README.md
```

The repository separates executable pipeline logic from governed metadata and documentation. Local database files, virtual environments, generated Python files, and developmental backups are excluded from version control.

## Design Decisions & V1 Limitations

The deterministic V1 intentionally prioritizes data correctness, governance, reproducibility, and explicit business meaning before introducing additional platform complexity.

### Reporting Period Authority

For the current Budget-vs-Actual data product, reporting periods are derived from `trusted.budget`.

This is appropriate for the scope of V1 because the business product is explicitly anchored to budget-versus-actual reporting periods.

A production implementation would typically introduce an independent governed calendar or fiscal-period dimension rather than relying on a transactional or planning dataset to establish reporting periods.

### Headcount Calculation

Actual headcount is calculated from employee employment dates rather than inferred from payroll activity.

An employee is considered active for a reporting month when their employment period overlaps that month.

The current V1 implementation derives organizational reporting periods from budget data and evaluates employees against those periods. A future version should explicitly support budgeted organization-period combinations with zero active employees through a governed reporting calendar and organizational reporting spine.

### Missing Actuals

Missing actual data is not automatically converted to zero.

If payroll actuals are unavailable for a reporting period, the platform preserves the value as `NULL`, and payroll variance remains `NULL`.

This distinction prevents incomplete data from being interpreted as a known financial result.

### Deterministic Controls Before AI

Business calculations, reconciliation, validation, and publication decisions remain deterministic.

AI is not used to determine whether financial data is valid or to replace governed metric calculations. This creates a stable foundation on which AI capabilities can safely operate.

## AI Enablement Roadmap

The next phase of the project will introduce AI capabilities above the governed deterministic foundation.

The guiding principle is:

> **The deterministic platform establishes truth; AI makes governed truth easier to discover, investigate, and use.**

Planned capabilities include:

1. **AI Metadata Intelligence**  
   Use governed schemas, contracts, metric definitions, and quality metadata to help users understand available data and its meaning.

2. **Embeddings & Semantic Search**  
   Enable semantic discovery across metric definitions, data contracts, business concepts, and platform metadata.

3. **Grounded Question Answering (RAG)**  
   Ground AI responses in governed platform context rather than relying solely on model knowledge.

4. **AI-Assisted Data Quality Investigation**  
   Use validation evidence, rejected records, and observability metadata to help investigate data-quality failures and explain likely causes.

5. **Agentic Finance Data Assistant**  
   Allow an AI agent to interact with explicitly governed tools and platform context for finance-data investigation and decision support.

6. **Model Context Protocol (MCP)**  
   Explore MCP as a controlled interface for exposing governed data-platform capabilities and context to AI applications.

AI evaluation will be introduced alongside these capabilities to assess grounding, correctness, tool usage, and adherence to governed definitions.

The objective is not to replace deterministic finance-data systems with an LLM. It is to build an AI interaction layer on top of a governed system of record.
import yaml
import duckdb
from src.config import METRICS_PATH,DB_PATH

conn = duckdb.connect(DB_PATH)

with open(METRICS_PATH, "r") as file:
    metric_catalog = yaml.safe_load(file)

payroll_variance = metric_catalog["metrics"]["payroll_variance"]

print("Metrics:", payroll_variance["display_name"])
print("Description: " , payroll_variance["description"])
print("Formula: ",payroll_variance["formula"])
print("Source table : ",payroll_variance["source"]["table"])
print("Source column : ",payroll_variance["source"]["column"])
print("Grain: ",payroll_variance["grain"])
print("Unit: ",payroll_variance["unit"])
print("Positive interpretation: ",payroll_variance["interpretation"]["positive"])
print("Across time aggregation: ",payroll_variance["aggregation"]["across_time"])

def get_metric(metric_name):
    metric =  metric_catalog["metrics"].get(metric_name)
    if metric is None:
        raise ValueError(f"Metric '{metric_name}' is not defined in the semantic catalog.")
    return metric

metric = get_metric("payroll_variance")
print("Metric: ",metric)

metric = get_metric("actual_payroll")

metric = get_metric("planned_payroll")

metric = get_metric("actual_headcount")


metric = get_metric("planned_headcount")

metric = get_metric("headcount_variance")

def validate_metric(metric_name,metric_definition):
    required_fields = ['display_name',
                       'description',
                       'source',
                       'grain',
                       'unit',
                       'aggregation',
                       'null_handling'
                        ]

    for field in required_fields:
        if field not in metric_definition:
            raise ValueError(f"Metric '{metric_name}' is missing field '{field}'")

def validate_input_metrics(metric_name,metric_definition,all_metrics):
    input_metrics = metric_definition.get("input_metrics",[])
    for input_metric_name in input_metrics:
        if input_metric_name not in all_metrics:
            raise ValueError(f"Metric '{metric_name}' references undefined input metric '{input_metric_name}'")

def validate_source_table(metric_name,metric_definition,conn):
    source_table = metric_definition["source"]["table"]
    schema_name,table_name = source_table.split(".")
    table_exists = conn.execute(""" SELECT COUNT(*) from information_schema.tables where
    table_schema = ?
    and table_name = ? """, [schema_name,table_name]).fetchone()[0]

    if table_exists == 0:
        raise ValueError(f"Metric '{metric_name}' references undefined source table '{source_table}'")

def validate_source_column(metric_name,metric_definition,conn):
    source_table = metric_definition["source"]["table"]
    source_column = metric_definition["source"]["column"]
    schema_name,table_name = source_table.split(".")
    column_exists = conn.execute(""" SELECT COUNT(*) FROM information_schema.columns 
     WHERE table_schema = ?
     AND table_name = ?
     AND column_name = ? """, [schema_name,table_name,source_column]).fetchone()[0] 

    if column_exists == 0:
        raise ValueError(f"Metric '{metric_name}' references undefined column name '{source_column}' in source table '{source_table}'")

def validate_source_grain(metric_name,metric_definition,conn):
    source_table = metric_definition["source"]["table"]
    grain_columns = metric_definition["grain"]
    schema_name,table_name = source_table.split(".")

    for grain_column in grain_columns:
        column_exists = conn.execute (""" SELECT COUNT(*) FROM information_schema.columns
        WHERE table_schema = ?
        AND table_name = ?
        AND column_name = ? """, [schema_name,table_name,grain_column]).fetchone()[0]

        if column_exists == 0:
            raise ValueError(f"Metric '{metric_name}' references undefined grain column '{grain_column}' in table '{source_table}'")

def validate_aggregation(metric_name,metric_definition):
    allowed_aggregations = ["additive",
                             "non_additive"]

    aggregation_definition = metric_definition["aggregation"]

    for aggregation_direction,aggregation_value in aggregation_definition.items():
        if aggregation_value not in allowed_aggregations:
            raise ValueError(f"Metric '{metric_name}' has undefined aggregation value '{aggregation_value}' for '{aggregation_direction}'")

def validate_unit(metric_name,metric_definition):
    allowed_units = ["currency","employees"]

    metric_unit = metric_definition["unit"]
    if metric_unit not in allowed_units:
        raise ValueError(f"Metric '{metric_name}' has undefined unit '{metric_unit}'")


all_metrics = metric_catalog["metrics"]

for metric_name,metric_definition in all_metrics.items():
    validate_metric(metric_name,metric_definition)
    validate_input_metrics(metric_name,metric_definition,all_metrics)
    validate_source_table(metric_name,metric_definition,conn)
    validate_source_column(metric_name,metric_definition,conn)
    validate_source_grain(metric_name,metric_definition,conn)
    validate_aggregation(metric_name,metric_definition)
    validate_unit(metric_name,metric_definition)

print("All metric definitions passed semantic validation.")

conn.close()

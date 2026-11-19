import subprocess
import sys
import duckdb
import uuid
from datetime import datetime
from src.config import DB_PATH

INGEST_MODULE = "src.ingestion.ingest_raw"
PROFILE_MODULE = "src.profiling.profile_raw"
TRUSTED_MODULE = "src.transformation.build_trusted"
BUSINESS_MODULE = "src.transformation.build_business"
SEMANTIC_MODULE = "src.semantic.load_metrics"
TRUSTED_CONTROLS_MODULE = "src.controls.run_trusted_controls"
BUSINESS_CONTROLS_MODULE = "src.controls.run_business_controls"

DATASETS = ["job_level",
            "job_sub_family",
            "comp_region",
            "cost_center",
            "employees",
            "payroll",
            "budget"]

def run_stage(stage_name,module):
    print(f"\n{'=' * 60}")
    print(f"STARTING: {stage_name}")
    print(f"{'=' * 60}")

    try:
        subprocess.run([sys.executable,"-m",module],check=True)
    except subprocess.CalledProcessError:
        print(f"{stage_name} failed, pipeline stopped.")
        raise

    print(f"COMPLETED: {stage_name}")

def record_dataset_summary(dataset, run_id, conn):
    raw_count = conn.execute(f""" SELECT COUNT(*) FROM
    raw.{dataset} """).fetchone()[0]

    trusted_count = conn.execute(f""" SELECT COUNT(*) FROM
    trusted.{dataset} """).fetchone()[0]

    rejected_count = conn.execute(f""" SELECT COUNT(*) FROM
     quality.{dataset}_rejects """).fetchone()[0]

    if raw_count == trusted_count + rejected_count:
        status = "PASS"
    else:
        status = "FAIL"

    conn.execute(""" INSERT INTO quality.dataset_runs_summary(run_id, dataset, raw_count,trusted_count,rejected_count,status) 
    VALUES (?,?,?,?,?,?)""",[run_id,dataset, raw_count,trusted_count,rejected_count,status])

    print(f"{dataset}: Raw = {raw_count}, Trusted = {trusted_count}, Rejected = {rejected_count}, Status = {status}")

    if status == "FAIL":
        raise ValueError(f"Dataset reconciliation failed for {dataset}: Raw = {raw_count}, Trusted = {trusted_count}, Rejected = {rejected_count} ")

run_id = str(uuid.uuid4())
start_time = datetime.now()

print(f"Pipeline run ID: {run_id}")
print(f"Pipeline started at: {start_time}")
with duckdb.connect(DB_PATH) as conn:

    conn.execute(""" CREATE SCHEMA IF NOT EXISTS quality""")

    # Create pipeline-level observability table
    conn.execute(""" CREATE TABLE IF NOT EXISTS quality.pipeline_runs(
    run_id VARCHAR,
    start_time timestamp,
    end_time timestamp,
    status VARCHAR,
    error_message VARCHAR) """)

    # Create dataset-level observability table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS quality.dataset_runs_summary(
            run_id VARCHAR,
            dataset VARCHAR,
            raw_count INTEGER,
            trusted_count INTEGER,
            rejected_count INTEGER,
            status VARCHAR
        )
    """)

    print("Observability tables verified.")
    
    # Record start of current pipeline run
    conn.execute(""" INSERT into quality.pipeline_runs(run_id, start_time, end_time, status, error_message) VALUES(?,?,?,?,?) """,
                [run_id, start_time, None, "RUNNING", None])

try:
    run_stage("Raw ingestion",INGEST_MODULE)
    run_stage("Raw profiling",PROFILE_MODULE)
    run_stage("Trusted layer build",TRUSTED_MODULE)
    run_stage("Trusted layer controls", TRUSTED_CONTROLS_MODULE)
    run_stage("Business layer build",BUSINESS_MODULE)
    run_stage("Business layer controls", BUSINESS_CONTROLS_MODULE)
    run_stage("Semantic layer validation",SEMANTIC_MODULE)

    print("Recording dataset observability...")

    with duckdb.connect(DB_PATH) as conn: 
        
        for dataset in DATASETS:
            record_dataset_summary(
            dataset,
            run_id,
            conn
            )


        end_time = datetime.now()

        conn.execute(""" UPDATE quality.pipeline_runs
        SET end_time = ?,
        status = ?,
        error_message = ? 
        WHERE run_id = ? """,[end_time, "PASSED", None, run_id])

        print(f"Pipeline completed successfully at: {end_time}")

except Exception as error:
    end_time = datetime.now()
    with duckdb.connect(DB_PATH) as conn:
        conn.execute(""" UPDATE quality.pipeline_runs
        SET end_time = ?,
        status =?,
        error_message = ?
        WHERE run_id = ? """, [end_time,"FAILED",str(error),run_id])

    print(f"Pipeline failed at: {end_time}")
    print(f"Error: {error}")
    

    raise



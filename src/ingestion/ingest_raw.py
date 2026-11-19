
import duckdb
import pandas as pd
from src.config import SOURCE_DIR, DB_PATH

def ingest_csv(file_name,table_name,conn):
    df = pd.read_csv(file_name)
    conn.register("source_df", df )
    conn.execute(f"create or replace table raw.{table_name} as select * from source_df")
    conn.unregister("source_df")
    print(f"Loaded {len(df)} rows into raw table raw.{table_name}")

"""Ingesting the employees_df into raw table"""
conn = duckdb.connect(DB_PATH)

print(f"Connected to Duck DB : {DB_PATH}")

conn.execute("CREATE SCHEMA IF NOT EXISTS raw")

for file_path in SOURCE_DIR.glob("*.csv"):
    table_name = file_path.stem
    ingest_csv(file_path,table_name,conn)

raw_tables = conn.execute("select table_name from information_schema.tables where table_schema = 'raw' order by table_name").fetchall()
print("\n Tables in raw schema")
print(raw_tables)

for table in raw_tables:
    table_name = table[0]
    raw_count = conn.execute(f"select count(*) from raw.{table_name}").fetchone()[0]
    print(f"raw.{table_name} row count is : {raw_count}")

print(conn.execute("""
    SELECT
      *
    FROM raw.payroll
    
""").fetchall())



conn.close()



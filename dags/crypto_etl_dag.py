"""
Crypto ETL Pipeline DAG

This is an ELT pipeline. Python owns ingestion (extract → validate → load raw)
and dbt owns transformation. The Python task loads the raw API records into the
raw_coins table; dbt then builds the PostgreSQL star schema from raw_coins and
asserts its data-quality tests.

    apply_migrations → run_python_etl → dbt_run → dbt_test
"""

import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

ETL_PROJECT_DIR = "/opt/crypto_etl"
if ETL_PROJECT_DIR not in sys.path:
    sys.path.insert(0, ETL_PROJECT_DIR)

from etl.migrations import apply_migrations  # noqa: E402
from main import run_pipeline  # noqa: E402

DBT_BIN = "/opt/dbt_venv/bin/dbt"
DBT_PROJECT_DIR = f"{ETL_PROJECT_DIR}/dbt"

# dbt models read PIPELINE_RUN_ID via env_var(), so the rows they build can be
# traced back to the ETL run that populated raw_coins. append_env keeps the
# database credentials that profiles.yml needs.
DBT_ENV = {"PIPELINE_RUN_ID": "{{ ti.xcom_pull(task_ids='run_python_etl') }}"}


def run_python_etl(**context):
    """Run the same pipeline as the CLI entry point, so behaviour cannot drift."""
    return run_pipeline()


default_args = {
    "owner": "crypto_etl",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    "crypto_etl_pipeline",
    default_args=default_args,
    description="Extract, validate, transform, and load cryptocurrency data, then run dbt models",
    schedule_interval="@hourly",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["crypto", "etl", "dbt"],
) as dag:

    migrate = PythonOperator(
        task_id="apply_migrations",
        python_callable=apply_migrations,
    )

    etl = PythonOperator(
        task_id="run_python_etl",
        python_callable=run_python_etl,
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"{DBT_BIN} run --project-dir {DBT_PROJECT_DIR}",
        env=DBT_ENV,
        append_env=True,
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"{DBT_BIN} test --project-dir {DBT_PROJECT_DIR}",
        env=DBT_ENV,
        append_env=True,
    )

    migrate >> etl >> dbt_run >> dbt_test

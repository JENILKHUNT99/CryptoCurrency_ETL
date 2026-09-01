"""
Crypto ETL Pipeline DAG

This DAG orchestrates the cryptocurrency data ETL pipeline:
1. Extract data from CoinGecko API
2. Validate data quality
3. Transform into star schema
4. Load to PostgreSQL
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator

import sys
sys.path.insert(0, '/opt/airflow')

from etl.extract import extract_crypto_data
from etl.validate import validate_data
from etl.transform import transform_data
from etl.load import (
    save_raw_snapshot,
    save_curated_snapshot,
    load_to_postgres,
    record_pipeline_run,
)
from etl.migrations import apply_migrations
from config.config import MIN_VALID_RECORDS
import uuid


def run_etl_pipeline(**context):
    """
    Main ETL pipeline function.
    Called by Airflow task.
    """
    pipeline_run_id = str(uuid.uuid4())
    started_at = datetime.utcnow()
    
    print(f"Starting ETL pipeline: run_id={pipeline_run_id}")
    
    # Run migrations first
    apply_migrations()
    record_pipeline_run(pipeline_run_id, started_at, "running")
    
    # Extract
    raw_data = extract_crypto_data()
    if not raw_data:
        raise RuntimeError("Extraction returned no data")
    
    # Save raw snapshot
    save_raw_snapshot(raw_data, pipeline_run_id, started_at, upload_to_s3=False)
    
    # Validate
    valid_data = validate_data(raw_data)
    if len(valid_data) < MIN_VALID_RECORDS:
        raise RuntimeError(
            f"Only {len(valid_data)} valid records received; minimum is {MIN_VALID_RECORDS}"
        )
    
    # Transform
    dimensions = transform_data(valid_data, run_at=started_at, run_id=pipeline_run_id)
    dim_category, dim_coin, dim_date, dim_currency, fact_crypto_prices = dimensions
    
    # Save curated snapshot
    save_curated_snapshot(fact_crypto_prices, pipeline_run_id, started_at, upload_to_s3=False)
    
    # Load to PostgreSQL
    load_to_postgres(dim_category, dim_coin, dim_date, dim_currency, fact_crypto_prices)
    
    # Record success
    record_pipeline_run(pipeline_run_id, started_at, "succeeded", len(raw_data), len(valid_data))
    
    print(f"ETL pipeline completed: run_id={pipeline_run_id}")
    return pipeline_run_id


# Default arguments for the DAG
default_args = {
    'owner': 'crypto_etl',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
with DAG(
    'crypto_etl_pipeline',
    default_args=default_args,
    description='Extract, validate, transform, and load cryptocurrency data',
    schedule_interval='@hourly',  # Run every hour
    start_date=datetime(2025, 1, 1),
    catchup=False,  # Don't run past schedules
    max_active_runs=1,  # Only one run at a time
    tags=['crypto', 'etl'],
) as dag:

    # Single task that runs the entire pipeline
    run_etl = PythonOperator(
        task_id='run_crypto_etl',
        python_callable=run_etl_pipeline,
    )

    run_etl

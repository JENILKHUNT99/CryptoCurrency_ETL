import json
from pathlib import Path

import boto3  # type: ignore
import psycopg2  # type: ignore
from psycopg2.extras import execute_values  # type: ignore

from config.config import AWS_REGION, CURATED_DATA_DIR, POSTGRES_CONFIG, RAW_DATA_DIR, S3_BUCKET_NAME
from etl.logger import get_logger

logger = get_logger(__name__)


def _get_pg_connection():
    return psycopg2.connect(**POSTGRES_CONFIG)


def _upsert_df(cursor, df, table_name, pk_column):
    if df is None or df.empty:
        logger.warning(f"Skipping {table_name}: empty DataFrame")
        return

    columns = list(df.columns)
    column_names = ", ".join(columns)
    update_set = ", ".join(f"{column} = EXCLUDED.{column}" for column in columns if column != pk_column)
    query = (
        f"INSERT INTO {table_name} ({column_names}) VALUES %s "
        f"ON CONFLICT ({pk_column}) DO UPDATE SET {update_set}"
    )
    execute_values(cursor, query, [tuple(row) for row in df.itertuples(index=False)], page_size=500)
    logger.info(f"Upserted {len(df)} rows into {table_name}")


def load_to_postgres(dim_category, dim_coin, dim_date, dim_currency, fact_crypto_prices):
    """Load a complete star-schema batch in one database transaction."""
    dataframes = [
        (dim_category, "dim_category", "category_id"),
        (dim_currency, "dim_currency", "currency_id"),
        (dim_coin, "dim_coin", "coin_id"),
        (dim_date, "dim_date", "date_id"),
        (fact_crypto_prices, "fact_crypto_prices", "price_id"),
    ]
    conn = _get_pg_connection()
    try:
        with conn.cursor() as cursor:
            for df, table_name, pk_column in dataframes:
                _upsert_df(cursor, df, table_name, pk_column)
        conn.commit()
        logger.info("PostgreSQL load complete")
    except Exception:
        conn.rollback()
        logger.exception("PostgreSQL load failed; transaction rolled back")
        raise
    finally:
        conn.close()


def record_pipeline_run(run_id, started_at, status, extracted_count=0, valid_count=0, error_message=None):
    """Insert or update the audit record for a pipeline execution."""
    conn = _get_pg_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO pipeline_runs (
                    pipeline_run_id, started_at, completed_at, status,
                    extracted_count, valid_count, error_message
                ) VALUES (%s, %s, CASE WHEN %s IN ('succeeded', 'failed') THEN NOW() ELSE NULL END,
                          %s, %s, %s, %s)
                ON CONFLICT (pipeline_run_id) DO UPDATE SET
                    completed_at = EXCLUDED.completed_at,
                    status = EXCLUDED.status,
                    extracted_count = EXCLUDED.extracted_count,
                    valid_count = EXCLUDED.valid_count,
                    error_message = EXCLUDED.error_message
                """,
                (run_id, started_at, status, status, extracted_count, valid_count, error_message),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        logger.exception("Unable to update pipeline audit record")
        raise
    finally:
        conn.close()


def _upload_snapshot(local_path, object_key):
    if not S3_BUCKET_NAME:
        raise ValueError("S3_BUCKET_NAME must be set when S3 uploads are enabled")

    try:
        s3 = boto3.client("s3", region_name=AWS_REGION)
        s3.upload_file(str(local_path), S3_BUCKET_NAME, object_key)
        logger.info(f"Uploaded snapshot to s3://{S3_BUCKET_NAME}/{object_key}")
    except Exception:
        logger.exception("S3 upload failed")
        raise


def save_raw_snapshot(raw_data, run_id, run_at, upload_to_s3=True):
    """Persist the unmodified source response before validation or transformation."""
    run_partition = run_at.strftime("run_date=%Y-%m-%d/run_hour=%H")
    raw_path = Path(RAW_DATA_DIR) / run_partition / f"{run_id}.json"
    raw_path.parent.mkdir(parents=True, exist_ok=True)

    with raw_path.open("w", encoding="utf-8") as raw_file:
        json.dump(raw_data, raw_file, ensure_ascii=False)
    logger.info(f"Saved raw snapshot to {raw_path}")

    if upload_to_s3:
        _upload_snapshot(raw_path, f"raw/{run_partition}/{run_id}.json")
    return raw_path


def save_curated_snapshot(fact_crypto_prices, run_id, run_at, upload_to_s3=True):
    """Persist the analytics-ready fact snapshot after successful transformation."""
    run_partition = run_at.strftime("run_date=%Y-%m-%d/run_hour=%H")
    curated_path = Path(CURATED_DATA_DIR) / run_partition / f"{run_id}.csv"
    curated_path.parent.mkdir(parents=True, exist_ok=True)

    fact_crypto_prices.to_csv(curated_path, index=False)
    logger.info(f"Saved curated snapshot to {curated_path}")

    if upload_to_s3:
        _upload_snapshot(curated_path, f"curated/{run_partition}/{run_id}.csv")
    return curated_path


def save_snapshots(raw_data, fact_crypto_prices, run_id, run_at, upload_to_s3=True):
    """Persist both snapshots; retained as a convenience for callers and tests."""
    raw_path = save_raw_snapshot(raw_data, run_id, run_at, upload_to_s3)
    curated_path = save_curated_snapshot(fact_crypto_prices, run_id, run_at, upload_to_s3)
    return raw_path, curated_path

import json
from pathlib import Path

import boto3  # type: ignore
import psycopg2  # type: ignore
from psycopg2.extras import execute_values  # type: ignore

from config.config import AWS_REGION, POSTGRES_CONFIG, RAW_DATA_DIR, S3_BUCKET_NAME
from etl.logger import get_logger

logger = get_logger(__name__)


def _get_pg_connection():
    return psycopg2.connect(**POSTGRES_CONFIG)


def load_raw_coins(raw_data, run_at):
    """Load raw coin data to raw_coins table for dbt transformation."""
    if not raw_data:
        logger.warning("No raw data to load")
        return

    conn = _get_pg_connection()
    try:
        with conn.cursor() as cursor:
            # Prepare raw data for insertion
            rows = []
            skipped = 0
            for coin in raw_data:
                # raw_coins requires an identity for every row; dbt applies the
                # remaining data-quality rules in stg_raw_coins.
                if not coin.get('id') or not coin.get('symbol') or not coin.get('name'):
                    skipped += 1
                    continue
                rows.append((
                    coin.get('id'),
                    coin.get('symbol'),
                    coin.get('name'),
                    coin.get('current_price'),
                    coin.get('market_cap'),
                    coin.get('total_volume'),
                    coin.get('high_24h'),
                    coin.get('low_24h'),
                    coin.get('price_change_percentage_24h'),
                    coin.get('last_updated'),
                    run_at  # loaded_at timestamp
                ))
            
            # Insert raw data
            insert_query = """
                INSERT INTO raw_coins (
                    id, symbol, name, current_price, market_cap, total_volume,
                    high_24h, low_24h, price_change_percentage_24h, last_updated, loaded_at
                ) VALUES %s
                ON CONFLICT (id) DO UPDATE SET
                    symbol = EXCLUDED.symbol,
                    name = EXCLUDED.name,
                    current_price = EXCLUDED.current_price,
                    market_cap = EXCLUDED.market_cap,
                    total_volume = EXCLUDED.total_volume,
                    high_24h = EXCLUDED.high_24h,
                    low_24h = EXCLUDED.low_24h,
                    price_change_percentage_24h = EXCLUDED.price_change_percentage_24h,
                    last_updated = EXCLUDED.last_updated,
                    loaded_at = EXCLUDED.loaded_at
            """
            execute_values(cursor, insert_query, rows, page_size=500)
            logger.info(f"Loaded {len(rows)} raw coins to raw_coins table")
            if skipped:
                logger.warning(f"Skipped {skipped} raw coins missing id, symbol, or name")
        conn.commit()
    except Exception:
        conn.rollback()
        logger.exception("Failed to load raw coins")
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

import json
from pathlib import Path

import boto3  # type: ignore
import psycopg2  # type: ignore
from psycopg2.extras import execute_values  # type: ignore
from psycopg2.sql import SQL, Identifier  # type: ignore

from config.config import AWS_REGION, CURATED_DATA_DIR, POSTGRES_CONFIG, RAW_DATA_DIR, S3_BUCKET_NAME
from etl.logger import get_logger

logger = get_logger(__name__)


def _get_pg_connection():
    return psycopg2.connect(**POSTGRES_CONFIG)


def _upsert_df(cursor, df, table_name, pk_column):
    """Upsert DataFrame using safe SQL identifier quoting to prevent SQL injection."""
    if df is None or df.empty:
        logger.warning(f"Skipping {table_name}: empty DataFrame")
        return

    # Convert column names to safe Identifier objects
    columns = [Identifier(col) for col in df.columns]
    pk_col = Identifier(pk_column)

    # Build safe column list: col1, col2, col3
    insert_cols = SQL(", ").join(columns)

    # Build safe UPDATE clause: col1 = EXCLUDED.col1, col2 = EXCLUDED.col2
    update_parts = SQL(", ").join([
        SQL("{} = EXCLUDED.{}").format(col, col)
        for col in columns
        if col != pk_col
    ])

    # Build safe query with proper identifier quoting
    query = SQL("INSERT INTO {} ({}) VALUES %s ON CONFLICT ({}) DO UPDATE SET {}").format(
        Identifier(table_name),
        insert_cols,
        pk_col,
        update_parts
    )

    execute_values(cursor, query, [tuple(row) for row in df.itertuples(index=False)], page_size=500)
    logger.info(f"Upserted {len(df)} rows into {table_name}")


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
            for coin in raw_data:
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
        conn.commit()
    except Exception:
        conn.rollback()
        logger.exception("Failed to load raw coins")
        raise
    finally:
        conn.close()


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

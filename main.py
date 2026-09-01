import argparse
import sys
import uuid
from datetime import datetime, timezone

from config.config import MIN_VALID_RECORDS, S3_ENABLED
from etl.extract import extract_crypto_data
from etl.load import (
    load_raw_coins,
    load_to_postgres,
    record_pipeline_run,
    save_curated_snapshot,
    save_raw_snapshot,
)
from etl.logger import get_logger
from etl.migrations import apply_migrations
from etl.transform import transform_data
from etl.validate import validate_data

logger = get_logger(__name__)


def parse_utc_timestamp(value):
    """Parse a timezone-aware ISO-8601 value and normalize it to UTC."""
    if isinstance(value, datetime):
        parsed = value
    else:
        timestamp = str(value).strip()
        if timestamp.endswith("Z"):
            timestamp = f"{timestamp[:-1]}+00:00"
        try:
            parsed = datetime.fromisoformat(timestamp)
        except ValueError as exc:
            raise ValueError(f"Invalid ISO-8601 timestamp: {value}") from exc

    if parsed.tzinfo is None:
        raise ValueError("The run timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def run_pipeline(run_at=None, upload_to_s3=S3_ENABLED, load_postgres=True):
    pipeline_run_id = str(uuid.uuid4())
    started_at = parse_utc_timestamp(run_at) if run_at is not None else datetime.now(timezone.utc)
    logger.info(f"Crypto ETL pipeline started: run_id={pipeline_run_id}")
    try:
        if load_postgres:
            apply_migrations()
            record_pipeline_run(pipeline_run_id, started_at, "running")

        raw_data = extract_crypto_data()
        # Preserve the source response before applying data-quality or business rules.
        save_raw_snapshot(raw_data, pipeline_run_id, started_at, upload_to_s3)
        if not raw_data:
            raise RuntimeError("Extraction returned no data")

        if load_postgres:
            # raw_coins is the source table for the dbt transformation layer.
            load_raw_coins(raw_data, started_at)

        valid_data = validate_data(raw_data)
        if len(valid_data) < MIN_VALID_RECORDS:
            raise RuntimeError(f"Only {len(valid_data)} valid records received; minimum is {MIN_VALID_RECORDS}")

        dimensions = transform_data(valid_data, run_at=started_at, run_id=pipeline_run_id)
        dim_category, dim_coin, dim_date, dim_currency, fact_crypto_prices = dimensions

        save_curated_snapshot(fact_crypto_prices, pipeline_run_id, started_at, upload_to_s3)
        if load_postgres:
            load_to_postgres(dim_category, dim_coin, dim_date, dim_currency, fact_crypto_prices)
            record_pipeline_run(pipeline_run_id, started_at, "succeeded", len(raw_data), len(valid_data))
        logger.info(f"Crypto ETL pipeline completed: run_id={pipeline_run_id}")
        return pipeline_run_id
    except Exception as exc:
        logger.exception(f"Crypto ETL pipeline failed: run_id={pipeline_run_id}")
        if load_postgres:
            try:
                record_pipeline_run(pipeline_run_id, started_at, "failed", error_message=str(exc))
            except Exception:
                logger.exception("Unable to record the failed pipeline run")
        raise


def parse_args():
    parser = argparse.ArgumentParser(description="Run the crypto market ETL pipeline.")
    parser.add_argument(
        "--run-at",
        type=parse_utc_timestamp,
        help="timezone-aware ISO-8601 timestamp used for a reproducible run",
    )
    parser.add_argument("--skip-s3", action="store_true", help="Write snapshots locally without uploading")
    parser.add_argument("--skip-postgres", action="store_true", help="Skip warehouse loading and audit records")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    try:
        run_pipeline(args.run_at, not args.skip_s3 and S3_ENABLED, not args.skip_postgres)
    except Exception:
        sys.exit(1)

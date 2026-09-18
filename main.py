import argparse
import sys
import uuid
from datetime import datetime, timezone
from typing import Optional, Union, List, Dict, Any

from config.config import MIN_VALID_RECORDS, S3_ENABLED
from etl.extract import extract_crypto_data
from etl.load import (
    load_raw_coins,
    record_pipeline_run,
    save_raw_snapshot,
)
from etl.logger import get_logger
from etl.migrations import apply_migrations
from etl.validate import validate_data

logger = get_logger(__name__)


def parse_utc_timestamp(value: Union[str, datetime]) -> datetime:
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


def run_pipeline(run_at: Optional[Union[str, datetime]] = None, upload_to_s3: bool = S3_ENABLED, load_postgres: bool = True) -> str:
    """Run the extract-load half of the pipeline.

    Python owns ingestion: it extracts from the API, preserves the raw response,
    gates the run on data quality, and loads the raw records into raw_coins. dbt
    owns the transformation into the star schema and runs as a separate step
    (the dbt_run / dbt_test tasks in the Airflow DAG).
    """
    pipeline_run_id = str(uuid.uuid4())
    started_at = parse_utc_timestamp(run_at) if run_at is not None else datetime.now(timezone.utc)
    logger.info(f"Crypto ETL ingestion started: run_id={pipeline_run_id}")
    try:
        if load_postgres:
            apply_migrations()
            record_pipeline_run(pipeline_run_id, started_at, "running")

        raw_data = extract_crypto_data()
        # Preserve the source response before applying data-quality or business rules.
        save_raw_snapshot(raw_data, pipeline_run_id, started_at, upload_to_s3)
        if not raw_data:
            raise RuntimeError("Extraction returned no data")

        valid_data = validate_data(raw_data)
        if len(valid_data) < MIN_VALID_RECORDS:
            raise RuntimeError(f"Only {len(valid_data)} valid records received; minimum is {MIN_VALID_RECORDS}")

        if load_postgres:
            # raw_coins is the source table the dbt transformation layer reads.
            load_raw_coins(raw_data, started_at)
            record_pipeline_run(pipeline_run_id, started_at, "succeeded", len(raw_data), len(valid_data))
        logger.info(f"Crypto ETL ingestion completed: run_id={pipeline_run_id}")
        return pipeline_run_id
    except Exception as exc:
        logger.exception(f"Crypto ETL ingestion failed: run_id={pipeline_run_id}")
        if load_postgres:
            try:
                record_pipeline_run(pipeline_run_id, started_at, "failed", error_message=str(exc))
            except Exception:
                logger.exception("Unable to record the failed pipeline run")
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the crypto market ETL ingestion.")
    parser.add_argument(
        "--run-at",
        type=parse_utc_timestamp,
        help="timezone-aware ISO-8601 timestamp used for a reproducible run",
    )
    parser.add_argument("--skip-s3", action="store_true", help="Write snapshots locally without uploading")
    parser.add_argument("--skip-postgres", action="store_true", help="Skip raw loading and audit records")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    try:
        run_pipeline(args.run_at, not args.skip_s3 and S3_ENABLED, not args.skip_postgres)
    except Exception:
        sys.exit(1)

from pathlib import Path
from unittest.mock import MagicMock

import pytest

import main
from tests.fixtures import SAMPLE_COINS_VALID


def test_run_pipeline_accepts_iso_timestamp_and_writes_both_snapshots(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "extract_crypto_data", MagicMock(return_value=SAMPLE_COINS_VALID))
    monkeypatch.setattr(main, "MIN_VALID_RECORDS", 1)
    monkeypatch.setattr("etl.load.RAW_DATA_DIR", str(tmp_path / "raw"))
    monkeypatch.setattr("etl.load.CURATED_DATA_DIR", str(tmp_path / "curated"))

    run_id = main.run_pipeline(
        "2025-07-20T15:30:00+05:30",
        upload_to_s3=False,
        load_postgres=False,
    )

    expected_partition = Path("run_date=2025-07-20/run_hour=10")
    assert (tmp_path / "raw" / expected_partition / f"{run_id}.json").exists()
    assert (tmp_path / "curated" / expected_partition / f"{run_id}.csv").exists()


def test_run_pipeline_preserves_raw_response_before_validation(monkeypatch):
    events = []
    monkeypatch.setattr(main, "MIN_VALID_RECORDS", 1)
    monkeypatch.setattr(main, "extract_crypto_data", MagicMock(return_value=SAMPLE_COINS_VALID))
    monkeypatch.setattr(main, "save_raw_snapshot", lambda *args: events.append("raw"))
    monkeypatch.setattr(main, "validate_data", lambda data: events.append("validate") or [])
    monkeypatch.setattr(main, "save_curated_snapshot", MagicMock())

    with pytest.raises(RuntimeError, match="Only 0 valid records"):
        main.run_pipeline(upload_to_s3=False, load_postgres=False)

    assert events == ["raw", "validate"]
    main.save_curated_snapshot.assert_not_called()


def test_run_pipeline_loads_raw_coins_for_dbt_before_transforming(monkeypatch):
    events = []
    monkeypatch.setattr(main, "MIN_VALID_RECORDS", 1)
    monkeypatch.setattr(main, "apply_migrations", MagicMock())
    monkeypatch.setattr(main, "record_pipeline_run", MagicMock())
    monkeypatch.setattr(main, "extract_crypto_data", MagicMock(return_value=SAMPLE_COINS_VALID))
    monkeypatch.setattr(main, "save_raw_snapshot", lambda *args: events.append("raw"))
    monkeypatch.setattr(main, "load_raw_coins", lambda *args: events.append("raw_coins"))
    monkeypatch.setattr(main, "validate_data", lambda data: events.append("validate") or data)
    monkeypatch.setattr(main, "transform_data", MagicMock(return_value=tuple(range(5))))
    monkeypatch.setattr(main, "save_curated_snapshot", MagicMock())
    monkeypatch.setattr(main, "load_to_postgres", MagicMock())

    main.run_pipeline(upload_to_s3=False, load_postgres=True)

    assert events == ["raw", "raw_coins", "validate"]


def test_parse_utc_timestamp_rejects_naive_value():
    with pytest.raises(ValueError, match="must include a timezone"):
        main.parse_utc_timestamp("2025-07-20T10:00:00")


def test_pipeline_preserves_original_error_when_failure_audit_also_fails(monkeypatch):
    monkeypatch.setattr(main, "apply_migrations", MagicMock())
    monkeypatch.setattr(main, "extract_crypto_data", MagicMock(side_effect=RuntimeError("source failed")))
    monkeypatch.setattr(
        main,
        "record_pipeline_run",
        MagicMock(side_effect=[None, RuntimeError("audit failed")]),
    )

    with pytest.raises(RuntimeError, match="source failed"):
        main.run_pipeline(upload_to_s3=False, load_postgres=True)

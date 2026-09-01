from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest

from etl.load import load_raw_coins, load_to_postgres, save_snapshots
from tests.fixtures import SAMPLE_COINS_VALID


def test_save_snapshots_creates_immutable_partitioned_files(tmp_path, monkeypatch):
    monkeypatch.setattr("etl.load.RAW_DATA_DIR", str(tmp_path / "raw"))
    monkeypatch.setattr("etl.load.CURATED_DATA_DIR", str(tmp_path / "curated"))
    fact = pd.DataFrame([{"price_id": "bitcoin_1", "price": 95000.5}])

    raw_path, curated_path = save_snapshots(
        SAMPLE_COINS_VALID,
        fact,
        "11111111-1111-1111-1111-111111111111",
        pd.Timestamp("2025-07-20T10:00:00Z"),
        upload_to_s3=False,
    )

    assert raw_path == Path(tmp_path / "raw/run_date=2025-07-20/run_hour=10/11111111-1111-1111-1111-111111111111.json")
    assert curated_path.exists()
    assert "bitcoin" in raw_path.read_text(encoding="utf-8")


def test_save_snapshots_uploads_stable_s3_object_keys(tmp_path, monkeypatch):
    monkeypatch.setattr("etl.load.RAW_DATA_DIR", str(tmp_path / "raw"))
    monkeypatch.setattr("etl.load.CURATED_DATA_DIR", str(tmp_path / "curated"))
    monkeypatch.setattr("etl.load.S3_BUCKET_NAME", "snapshot-bucket")
    s3 = MagicMock()
    monkeypatch.setattr("etl.load.boto3.client", MagicMock(return_value=s3))
    fact = pd.DataFrame([{"price_id": "bitcoin_usd_1", "price": 95000.5}])

    save_snapshots(
        SAMPLE_COINS_VALID,
        fact,
        "11111111-1111-1111-1111-111111111111",
        pd.Timestamp("2025-07-20T10:00:00Z"),
        upload_to_s3=True,
    )

    assert s3.upload_file.call_count == 2
    assert s3.upload_file.call_args_list[0].args[1:] == (
        "snapshot-bucket",
        "raw/run_date=2025-07-20/run_hour=10/11111111-1111-1111-1111-111111111111.json",
    )
    assert s3.upload_file.call_args_list[1].args[1:] == (
        "snapshot-bucket",
        "curated/run_date=2025-07-20/run_hour=10/11111111-1111-1111-1111-111111111111.csv",
    )


def test_load_to_postgres_commits_tables_in_dependency_order(monkeypatch):
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    monkeypatch.setattr("etl.load._get_pg_connection", MagicMock(return_value=connection))
    loaded_tables = []

    def capture_upsert(actual_cursor, dataframe, table_name, pk_column):
        assert actual_cursor is cursor
        loaded_tables.append((table_name, pk_column, dataframe))

    monkeypatch.setattr("etl.load._upsert_df", capture_upsert)
    frames = [pd.DataFrame([{"value": index}]) for index in range(5)]

    load_to_postgres(*frames)

    assert [(table, pk) for table, pk, _ in loaded_tables] == [
        ("dim_category", "category_id"),
        ("dim_currency", "currency_id"),
        ("dim_coin", "coin_id"),
        ("dim_date", "date_id"),
        ("fact_crypto_prices", "price_id"),
    ]
    connection.commit.assert_called_once_with()
    connection.rollback.assert_not_called()
    connection.close.assert_called_once_with()


def test_load_to_postgres_rolls_back_failed_batch(monkeypatch):
    connection = MagicMock()
    monkeypatch.setattr("etl.load._get_pg_connection", MagicMock(return_value=connection))
    monkeypatch.setattr("etl.load._upsert_df", MagicMock(side_effect=RuntimeError("load failed")))
    frames = [pd.DataFrame([{"value": index}]) for index in range(5)]

    with pytest.raises(RuntimeError, match="load failed"):
        load_to_postgres(*frames)

    connection.commit.assert_not_called()
    connection.rollback.assert_called_once_with()
    connection.close.assert_called_once_with()


def test_load_raw_coins_skips_rows_without_an_identity(monkeypatch):
    """raw_coins requires id, symbol and name; dbt applies the remaining rules."""
    connection = MagicMock()
    monkeypatch.setattr("etl.load._get_pg_connection", MagicMock(return_value=connection))
    execute_values = MagicMock()
    monkeypatch.setattr("etl.load.execute_values", execute_values)
    raw_data = [
        *SAMPLE_COINS_VALID,
        {**SAMPLE_COINS_VALID[0], "id": None},
        {**SAMPLE_COINS_VALID[0], "symbol": None},
        {**SAMPLE_COINS_VALID[0], "name": None},
    ]

    load_raw_coins(raw_data, pd.Timestamp("2025-07-20T10:00:00Z"))

    loaded_rows = execute_values.call_args.args[2]
    assert [row[0] for row in loaded_rows] == ["bitcoin"]
    connection.commit.assert_called_once_with()
    connection.rollback.assert_not_called()


def test_load_raw_coins_rolls_back_on_failure(monkeypatch):
    connection = MagicMock()
    monkeypatch.setattr("etl.load._get_pg_connection", MagicMock(return_value=connection))
    monkeypatch.setattr("etl.load.execute_values", MagicMock(side_effect=RuntimeError("insert failed")))

    with pytest.raises(RuntimeError, match="insert failed"):
        load_raw_coins(SAMPLE_COINS_VALID, pd.Timestamp("2025-07-20T10:00:00Z"))

    connection.commit.assert_not_called()
    connection.rollback.assert_called_once_with()
    connection.close.assert_called_once_with()

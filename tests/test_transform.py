import pytest
from etl.transform import transform_data
from tests.fixtures import SAMPLE_COINS_VALID


def test_transform_returns_all_five_tables():
    result = transform_data(SAMPLE_COINS_VALID)
    assert result[0] is not None
    dim_category, dim_coin, dim_date, dim_currency, fact = result
    assert len(dim_category) > 0
    assert len(dim_coin) > 0
    assert len(dim_date) > 0
    assert len(dim_currency) > 0
    assert len(fact) > 0


def test_transform_empty_input():
    result = transform_data([])
    assert result == (None, None, None, None, None)


def test_transform_coin_fields():
    _, dim_coin, _, _, _ = transform_data(SAMPLE_COINS_VALID)
    assert list(dim_coin.columns) == ["coin_id", "coin_symbol", "coin_name", "category_id"]
    assert dim_coin.loc[0, "coin_id"] == "bitcoin"
    assert dim_coin.loc[0, "coin_symbol"] == "btc"


def test_transform_fact_fields():
    *_, fact = transform_data(SAMPLE_COINS_VALID)
    expected_cols = [
        "price_id", "coin_id", "etl_run_date_id", "api_updated_date_id",
        "currency_id", "observed_at", "ingested_at", "pipeline_run_id",
        "price", "market_cap", "volume",
        "high_24h", "low_24h", "price_change_percent",
    ]
    assert list(fact.columns) == expected_cols


def test_transform_date_dimension():
    _, _, dim_date, _, _ = transform_data(SAMPLE_COINS_VALID, run_date="2025-07-20T10:00:00Z")
    expected_cols = [
        "date_id", "datetime", "full_date", "hour", "day", "day_name",
        "month", "month_name", "quarter", "year", "is_weekend",
    ]
    assert list(dim_date.columns) == expected_cols
    assert dim_date.loc[0, "year"] == 2025


def test_transform_uses_exact_observed_timestamp_and_floors_date_key():
    *_, fact = transform_data(
        SAMPLE_COINS_VALID,
        run_at="2025-07-20T10:40:00Z",
        run_id="11111111-1111-1111-1111-111111111111",
    )
    assert fact.loc[0, "api_updated_date_id"] == 2025072010
    assert fact.loc[0, "etl_run_date_id"] == 2025072010
    assert fact.loc[0, "pipeline_run_id"] == "11111111-1111-1111-1111-111111111111"
    assert fact.loc[0, "price_id"].endswith("20250720T100000000000Z")

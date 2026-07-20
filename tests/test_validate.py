import pytest
from etl.validate import validate_data
from tests.fixtures import (
    SAMPLE_COIN_VALID,
    SAMPLE_COIN_MISSING_FIELD,
    SAMPLE_COIN_NULL_VALUE,
    SAMPLE_COIN_NEGATIVE_PRICE,
    SAMPLE_COIN_WRONG_TYPE,
)


def test_validate_empty_input():
    assert validate_data([]) == []


def test_validate_none_input():
    assert validate_data(None) == []


def test_validate_single_valid_coin():
    result = validate_data([SAMPLE_COIN_VALID])
    assert len(result) == 1
    assert result[0]["id"] == "bitcoin"


def test_validate_missing_fields():
    result = validate_data([SAMPLE_COIN_MISSING_FIELD])
    assert len(result) == 0


def test_validate_null_values():
    result = validate_data([SAMPLE_COIN_NULL_VALUE])
    assert len(result) == 0


def test_validate_negative_price():
    result = validate_data([SAMPLE_COIN_NEGATIVE_PRICE])
    assert len(result) == 0


def test_validate_wrong_type():
    result = validate_data([SAMPLE_COIN_WRONG_TYPE])
    assert len(result) == 0


def test_validate_mixed_coins():
    data = [
        SAMPLE_COIN_VALID,
        SAMPLE_COIN_MISSING_FIELD,
        SAMPLE_COIN_NEGATIVE_PRICE,
    ]
    result = validate_data(data)
    assert len(result) == 1


def test_validate_rejects_duplicate_ids_and_invalid_timestamp():
    duplicate = SAMPLE_COIN_VALID.copy()
    invalid_timestamp = SAMPLE_COIN_VALID.copy()
    invalid_timestamp["id"] = "ethereum"
    invalid_timestamp["last_updated"] = "not-a-date"

    result = validate_data([SAMPLE_COIN_VALID, duplicate, invalid_timestamp])
    assert result == [SAMPLE_COIN_VALID]


def test_validate_rejects_invalid_price_range_and_non_finite_values():
    invalid_range = SAMPLE_COIN_VALID.copy()
    invalid_range["high_24h"] = 90000
    invalid_range["low_24h"] = 94000
    non_finite = SAMPLE_COIN_VALID.copy()
    non_finite["id"] = "ethereum"
    non_finite["market_cap"] = float("inf")

    assert validate_data([invalid_range, non_finite]) == []

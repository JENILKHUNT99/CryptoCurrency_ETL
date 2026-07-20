import pytest
from unittest.mock import patch, MagicMock
from etl.extract import extract_crypto_data

MOCK_RESPONSE = [
    {
        "id": "bitcoin",
        "symbol": "btc",
        "name": "Bitcoin",
        "current_price": 95000.50,
        "market_cap": 1900000000000,
        "total_volume": 35000000000,
        "high_24h": 96000.00,
        "low_24h": 94000.00,
        "price_change_percentage_24h": 1.2,
        "last_updated": "2025-07-20T10:00:00.000Z",
    }
]


@patch("etl.extract.requests.get")
def test_extract_success(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = MOCK_RESPONSE
    mock_get.return_value = mock_resp

    result = extract_crypto_data()
    assert len(result) == 1
    assert result[0]["id"] == "bitcoin"


@patch("etl.extract.requests.get")
def test_extract_http_error(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "Internal Server Error"
    mock_get.return_value = mock_resp

    result = extract_crypto_data()
    assert result == []


@patch("etl.extract.requests.get")
def test_extract_connection_error(mock_get):
    import requests
    mock_get.side_effect = requests.exceptions.ConnectionError("No connection")

    result = extract_crypto_data()
    assert result == []


@patch("etl.extract.time.sleep")
@patch("etl.extract.requests.get")
def test_extract_rate_limit_retry(mock_get, mock_sleep):
    mock_rate_limited = MagicMock()
    mock_rate_limited.status_code = 429
    mock_success = MagicMock()
    mock_success.status_code = 200
    mock_success.json.return_value = MOCK_RESPONSE
    mock_get.side_effect = [mock_rate_limited, mock_success]

    result = extract_crypto_data()
    assert len(result) == 1
    assert mock_get.call_count == 2
    mock_sleep.assert_called_once_with(5)

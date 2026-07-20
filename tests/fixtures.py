SAMPLE_COIN_VALID = {
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

SAMPLE_COIN_MISSING_FIELD = {
    "id": "bitcoin",
    "symbol": "btc",
    "name": "Bitcoin",
    "current_price": 95000.50,
}

SAMPLE_COIN_NULL_VALUE = {
    "id": "bitcoin",
    "symbol": "btc",
    "name": "Bitcoin",
    "current_price": None,
    "market_cap": 1900000000000,
    "total_volume": 35000000000,
    "high_24h": 96000.00,
    "low_24h": 94000.00,
    "price_change_percentage_24h": 1.2,
    "last_updated": "2025-07-20T10:00:00.000Z",
}

SAMPLE_COIN_NEGATIVE_PRICE = {
    "id": "bitcoin",
    "symbol": "btc",
    "name": "Bitcoin",
    "current_price": -100,
    "market_cap": 1900000000000,
    "total_volume": 35000000000,
    "high_24h": 96000.00,
    "low_24h": 94000.00,
    "price_change_percentage_24h": 1.2,
    "last_updated": "2025-07-20T10:00:00.000Z",
}

SAMPLE_COIN_WRONG_TYPE = {
    "id": "bitcoin",
    "symbol": "btc",
    "name": "Bitcoin",
    "current_price": "not_a_number",
    "market_cap": 1900000000000,
    "total_volume": 35000000000,
    "high_24h": 96000.00,
    "low_24h": 94000.00,
    "price_change_percentage_24h": 1.2,
    "last_updated": "2025-07-20T10:00:00.000Z",
}

SAMPLE_COINS_VALID = [SAMPLE_COIN_VALID]
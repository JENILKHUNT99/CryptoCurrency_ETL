from etl.logger import get_logger

logger = get_logger(__name__)

REQUIRED_FIELDS = [
    'id', 'symbol', 'name',
    'current_price', 'market_cap', 'total_volume',
    'high_24h', 'low_24h', 'price_change_percentage_24h'
]

NUMERIC_FIELDS = [
    'current_price', 'market_cap', 'total_volume',
    'high_24h', 'low_24h', 'price_change_percentage_24h'
]

def validate_data(data):
    logger.info("Validating data...")

    if not data:
        logger.error("No data to validate!")
        return []

    valid_data = []

    for coin in data:
        try:
            coin_id = coin.get("id", "unknown")

            # 1. Required field check
            if not all(field in coin for field in REQUIRED_FIELDS):
                logger.warning(f"Missing fields in coin: {coin_id}")
                continue

            # 2. Null check
            if any(coin[field] is None for field in REQUIRED_FIELDS):
                logger.warning(f"Null values in coin: {coin_id}")
                continue

            # 3. Type + numeric validation
            for field in NUMERIC_FIELDS:
                if not isinstance(coin[field], (int, float)):
                    logger.warning(f"Invalid type for {field} in {coin_id}")
                    raise ValueError(f"Invalid value for {field}")

                # Business rule
                if field != "price_change_percentage_24h" and coin[field] <= 0:
                    logger.warning(f"Invalid value for {field} in {coin_id}")
                    raise ValueError(f"Invalid value for {field}")

            # Passed all checks ✅
            valid_data.append(coin)

        except Exception as e:
            logger.error(f"Validation failed for coin: {coin.get('id', 'unknown')}: {e}")
            continue

    logger.info(f"Valid records: {len(valid_data)} / {len(data)}")

    return valid_data
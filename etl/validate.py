import math
from datetime import datetime

from etl.logger import get_logger

logger = get_logger(__name__)

REQUIRED_FIELDS = [
    'id', 'symbol', 'name',
    'current_price', 'market_cap', 'total_volume',
    'high_24h', 'low_24h', 'price_change_percentage_24h','last_updated'
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
    seen_ids = set()

    for coin in data:
        if not isinstance(coin, dict):
            logger.warning("Skipping non-object record from source")
            continue
        coin_id = coin.get("id", "unknown")

        if not all(field in coin for field in REQUIRED_FIELDS):
            logger.warning(f"Missing fields in coin: {coin_id}")
            continue

        if any(coin[field] is None for field in REQUIRED_FIELDS):
            logger.warning(f"Null values in coin: {coin_id}")
            continue

        if not all(isinstance(coin[field], str) and coin[field].strip() for field in ("id", "symbol", "name")):
            logger.warning(f"Invalid identifier fields in coin: {coin_id}")
            continue

        if coin_id in seen_ids:
            logger.warning(f"Duplicate coin ID in source response: {coin_id}")
            continue

        type_valid = True
        for field in NUMERIC_FIELDS:
            if isinstance(coin[field], bool) or not isinstance(coin[field], (int, float)):
                logger.warning(f"Invalid type for {field} in {coin_id}")
                type_valid = False
                break

            if not math.isfinite(coin[field]):
                logger.warning(f"Non-finite value for {field} in {coin_id}")
                type_valid = False
                break

            if field != "price_change_percentage_24h" and coin[field] <= 0:
                logger.warning(f"Invalid value for {field} in {coin_id}")
                type_valid = False
                break

        if not type_valid:
            continue

        try:
            datetime.fromisoformat(coin["last_updated"].replace("Z", "+00:00"))
        except (AttributeError, ValueError):
            logger.warning(f"Invalid last_updated timestamp in {coin_id}")
            continue

        if coin["high_24h"] < coin["low_24h"]:
            logger.warning(f"24-hour high is lower than low in {coin_id}")
            continue

        valid_data.append(coin)
        seen_ids.add(coin_id)

    logger.info(f"Valid records: {len(valid_data)} / {len(data)}")
    return valid_data

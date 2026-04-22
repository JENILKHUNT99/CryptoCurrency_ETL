import requests # type: ignore
from etl.logger import get_logger
from config.config import COINS, CURRENCY

logger = get_logger(__name__)

URL = "https://api.coingecko.com/api/v3/coins/markets"

def extract_crypto_data():
    logger.info("Extracting crypto data...")
    try:
        params = {
            'vs_currency': CURRENCY,
            'ids': ','.join(COINS)
        }
        response = requests.get(URL, params=params)

        if response.status_code == 200:
            data = response.json()
            logger.info(f"Extracted {len(data)} coins successfully!")
            return data
        else:
            logger.error(f"API Error: {response.status_code}")
            return []

    except requests.exceptions.ConnectionError:
        logger.error("No internet connection!")
        return []

    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return []
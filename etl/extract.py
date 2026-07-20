import time

import requests  # type: ignore
from etl.logger import get_logger
from config.config import COINS, CURRENCY

logger = get_logger(__name__)

URL = "https://api.coingecko.com/api/v3/coins/markets"
TIMEOUT = 30
MAX_RETRIES = 3
RETRY_BACKOFF = 5

def extract_crypto_data():
    logger.info("Extracting crypto data...")
    params = {
        'vs_currency': CURRENCY,
        'ids': ','.join(COINS),
        'per_page': 250,
        'page': 1,
        'sparkline': 'false'
    }

    for attempt in range(1, MAX_RETRIES + 1):
        retry_delay = RETRY_BACKOFF
        try:
            response = requests.get(
                URL,
                params=params,
                timeout=TIMEOUT,
                headers={"Accept": "application/json"},
            )

            if response.status_code == 200:
                data = response.json()
                if not isinstance(data, list):
                    logger.error("API response was not a list of coins")
                    return []
                logger.info(f"Extracted {len(data)} coins successfully!")
                return data
            if response.status_code == 429 or 500 <= response.status_code < 600:
                retry_after = response.headers.get("Retry-After")
                retry_delay = (
                    int(retry_after)
                    if isinstance(retry_after, str) and retry_after.isdigit()
                    else RETRY_BACKOFF * attempt
                )
                logger.warning(
                    f"API returned {response.status_code}; retrying in {retry_delay}s "
                    f"(attempt {attempt}/{MAX_RETRIES})"
                )
            else:
                logger.error(f"API Error: {response.status_code} - {response.text[:200]}")
                return []

        except requests.exceptions.Timeout:
            logger.warning(f"Request timed out (attempt {attempt}/{MAX_RETRIES})")
        except requests.exceptions.ConnectionError:
            logger.warning(f"Connection error (attempt {attempt}/{MAX_RETRIES})")
        except requests.exceptions.RequestException as exc:
            logger.error(f"Extraction failed: {exc}")
            return []
        except ValueError as exc:
            logger.error(f"API returned invalid JSON: {exc}")
            return []
        except Exception as exc:
            logger.exception(f"Unexpected extraction failure: {exc}")
            return []

        if attempt < MAX_RETRIES:
            time.sleep(retry_delay)

    logger.error(f"Max retries ({MAX_RETRIES}) exhausted. No data extracted.")
    return []

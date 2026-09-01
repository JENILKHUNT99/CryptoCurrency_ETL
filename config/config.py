import os
from dotenv import load_dotenv

try:
    from config.coins import COINS
except ImportError:
    from coins import COINS

load_dotenv()


def _env_flag(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes"}


POSTGRES_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
    "dbname": os.getenv("DB_NAME", "crypto_etl"),
}

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "")
S3_ENABLED = _env_flag("S3_ENABLED", default=False)
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "ap-south-1")
MIN_VALID_RECORDS = int(os.getenv("MIN_VALID_RECORDS", "1"))

COINS = COINS
CURRENCY = os.getenv("CURRENCY", "usd").strip().lower()
if not CURRENCY or len(CURRENCY) > 10 or not CURRENCY.replace("-", "").isalnum():
    raise ValueError("CURRENCY must be a non-empty alphanumeric code of at most 10 characters")

RAW_DATA_DIR = os.getenv("RAW_DATA_DIR", "data/raw")
CURATED_DATA_DIR = os.getenv("CURATED_DATA_DIR", "data/curated")

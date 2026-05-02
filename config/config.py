import os 
from config.coins import COINS

POSTGRES_CONFIG = {
    'host': os.getenv('DB_HOST', '127.0.0.1'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'dbname': os.getenv('DB_NAME', 'crypto_etl')
}

S3_BUCKET_NAME='jenilkhunt-etl-storage'
PROCESSED_KEY='crypto_data/crypto_data.csv'

COINS = COINS
CURRENCY = 'usd'

PROCESSED_DATA_DIR='data/processed/crypto_prices.csv'
CREATE TABLE IF NOT EXISTS dim_category (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_coin (
    coin_id SERIAL PRIMARY KEY,
    coin_symbol VARCHAR(20) UNIQUE NOT NULL,
    coin_name VARCHAR(100) NOT NULL,
    category_id INTEGER NOT NULL,
    FOREIGN KEY (category_id) REFERENCES dim_category(category_id)
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_id SERIAL PRIMARY KEY,
    full_date DATE UNIQUE NOT NULL,
    hour INTEGER NOT NULL,
    day INTEGER NOT NULL,
    day_name VARCHAR(20) NOT NULL,
    month INTEGER NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    quarter VARCHAR(5) NOT NULL,
    year INTEGER NOT NULL,
    is_weekend BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_currency (
    currency_id SERIAL PRIMARY KEY,
    currency_name VARCHAR(50) NOT NULL,
    currency_symbol VARCHAR(10) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_crypto_prices (
    price_id SERIAL PRIMARY KEY,
    coin_id INTEGER NOT NULL,
    etl_run_date_id INTEGER NOT NULL,
    api_updated_date_id INTEGER NOT NULL,
    currency_id INTEGER NOT NULL,
    price NUMERIC(20, 10) NOT NULL,
    market_cap NUMERIC(20, 2) NOT NULL,
    volume NUMERIC(20, 2) NOT NULL,
    high_24h NUMERIC(20, 10) NOT NULL,
    low_24h NUMERIC(20, 10) NOT NULL,
    price_change_percent NUMERIC(10, 2) NOT NULL,
    FOREIGN KEY (coin_id) REFERENCES dim_coin(coin_id),
    FOREIGN KEY (etl_run_date_id) REFERENCES dim_date(date_id),
    FOREIGN KEY (api_updated_date_id) REFERENCES dim_date(date_id),
    FOREIGN KEY (currency_id) REFERENCES dim_currency(currency_id)
);
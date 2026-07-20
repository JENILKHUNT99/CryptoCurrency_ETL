CREATE TABLE IF NOT EXISTS dim_category (
    category_id INTEGER PRIMARY KEY,
    category_name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_coin (
    coin_id VARCHAR(100) PRIMARY KEY,
    coin_symbol VARCHAR(20) NOT NULL,
    coin_name VARCHAR(100) NOT NULL,
    category_id INTEGER NOT NULL REFERENCES dim_category(category_id)
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_id BIGINT PRIMARY KEY,
    datetime TIMESTAMPTZ UNIQUE NOT NULL,
    full_date DATE NOT NULL,
    hour INTEGER NOT NULL CHECK (hour BETWEEN 0 AND 23),
    day INTEGER NOT NULL CHECK (day BETWEEN 1 AND 31),
    day_name VARCHAR(20) NOT NULL,
    month INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
    month_name VARCHAR(20) NOT NULL,
    quarter INTEGER NOT NULL CHECK (quarter BETWEEN 1 AND 4),
    year INTEGER NOT NULL,
    is_weekend BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_currency (
    currency_id INTEGER PRIMARY KEY,
    currency_name VARCHAR(50) NOT NULL,
    currency_symbol VARCHAR(10) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    pipeline_run_id UUID PRIMARY KEY,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL CHECK (status IN ('running', 'succeeded', 'failed')),
    extracted_count INTEGER NOT NULL DEFAULT 0,
    valid_count INTEGER NOT NULL DEFAULT 0,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS fact_crypto_prices (
    price_id VARCHAR(120) PRIMARY KEY,
    coin_id VARCHAR(100) NOT NULL REFERENCES dim_coin(coin_id),
    etl_run_date_id BIGINT NOT NULL REFERENCES dim_date(date_id),
    api_updated_date_id BIGINT NOT NULL REFERENCES dim_date(date_id),
    currency_id INTEGER NOT NULL REFERENCES dim_currency(currency_id),
    observed_at TIMESTAMPTZ NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL,
    pipeline_run_id UUID NOT NULL REFERENCES pipeline_runs(pipeline_run_id),
    price NUMERIC(20, 10) NOT NULL CHECK (price > 0),
    market_cap NUMERIC(24, 2) NOT NULL CHECK (market_cap > 0),
    volume NUMERIC(24, 2) NOT NULL CHECK (volume > 0),
    high_24h NUMERIC(20, 10) NOT NULL CHECK (high_24h >= low_24h),
    low_24h NUMERIC(20, 10) NOT NULL CHECK (low_24h > 0),
    price_change_percent NUMERIC(12, 4) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_fact_crypto_prices_coin_observed_at
    ON fact_crypto_prices (coin_id, observed_at DESC);
CREATE INDEX IF NOT EXISTS idx_fact_crypto_prices_pipeline_run_id
    ON fact_crypto_prices (pipeline_run_id);

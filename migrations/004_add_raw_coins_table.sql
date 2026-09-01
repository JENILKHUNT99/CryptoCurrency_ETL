-- Migration: Create raw coins table
-- This table stores the raw data loaded by Python before dbt transformation

CREATE TABLE IF NOT EXISTS raw_coins (
    id VARCHAR(100) PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    current_price NUMERIC(20, 10),
    market_cap NUMERIC(24, 2),
    total_volume NUMERIC(24, 2),
    high_24h NUMERIC(20, 10),
    low_24h NUMERIC(20, 10),
    price_change_percentage_24h NUMERIC(12, 4),
    last_updated TIMESTAMPTZ,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for efficient queries on loaded_at
CREATE INDEX IF NOT EXISTS idx_raw_coins_loaded_at ON raw_coins(loaded_at);

-- Index for coin lookups
CREATE INDEX IF NOT EXISTS idx_raw_coins_symbol ON raw_coins(symbol);

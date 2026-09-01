-- Note: pipeline_runs table is created in 001_initial_schema.sql
-- This migration only upgrades existing tables and adds missing columns

ALTER TABLE dim_date
    ALTER COLUMN datetime TYPE TIMESTAMPTZ USING datetime AT TIME ZONE 'UTC';

ALTER TABLE dim_coin DROP CONSTRAINT IF EXISTS dim_coin_coin_symbol_key;
ALTER TABLE dim_coin ALTER COLUMN coin_id TYPE VARCHAR(100);

ALTER TABLE fact_crypto_prices ALTER COLUMN price_id TYPE VARCHAR(120);
ALTER TABLE fact_crypto_prices ADD COLUMN IF NOT EXISTS observed_at TIMESTAMPTZ;
ALTER TABLE fact_crypto_prices ADD COLUMN IF NOT EXISTS ingested_at TIMESTAMPTZ;
ALTER TABLE fact_crypto_prices ADD COLUMN IF NOT EXISTS pipeline_run_id UUID;

UPDATE fact_crypto_prices AS fact
SET observed_at = date_dimension.datetime
FROM dim_date AS date_dimension
WHERE fact.api_updated_date_id = date_dimension.date_id
  AND fact.observed_at IS NULL;

UPDATE fact_crypto_prices AS fact
SET ingested_at = date_dimension.datetime
FROM dim_date AS date_dimension
WHERE fact.etl_run_date_id = date_dimension.date_id
  AND fact.ingested_at IS NULL;

UPDATE fact_crypto_prices
SET pipeline_run_id = '00000000-0000-0000-0000-000000000000'
WHERE pipeline_run_id IS NULL;

ALTER TABLE fact_crypto_prices ALTER COLUMN observed_at SET NOT NULL;
ALTER TABLE fact_crypto_prices ALTER COLUMN ingested_at SET NOT NULL;
ALTER TABLE fact_crypto_prices ALTER COLUMN pipeline_run_id SET NOT NULL;
ALTER TABLE fact_crypto_prices DROP CONSTRAINT IF EXISTS fact_crypto_prices_pipeline_run_id_fkey;
ALTER TABLE fact_crypto_prices
    ADD CONSTRAINT fact_crypto_prices_pipeline_run_id_fkey
    FOREIGN KEY (pipeline_run_id) REFERENCES pipeline_runs(pipeline_run_id);

CREATE INDEX IF NOT EXISTS idx_fact_crypto_prices_coin_observed_at
    ON fact_crypto_prices (coin_id, observed_at DESC);
CREATE INDEX IF NOT EXISTS idx_fact_crypto_prices_pipeline_run_id
    ON fact_crypto_prices (pipeline_run_id);

ALTER TABLE fact_crypto_prices
    DROP CONSTRAINT IF EXISTS fact_crypto_prices_currency_id_fkey;

ALTER TABLE dim_currency
    ALTER COLUMN currency_id TYPE VARCHAR(10)
    USING CASE WHEN currency_id = 1 THEN 'usd' ELSE LOWER(currency_id::TEXT) END;

ALTER TABLE fact_crypto_prices
    ALTER COLUMN currency_id TYPE VARCHAR(10)
    USING CASE WHEN currency_id = 1 THEN 'usd' ELSE LOWER(currency_id::TEXT) END;

ALTER TABLE fact_crypto_prices
    ALTER COLUMN price_id TYPE VARCHAR(160);

UPDATE fact_crypto_prices
SET price_id = coin_id || '_' || currency_id || '_' ||
    TO_CHAR(observed_at AT TIME ZONE 'UTC', 'YYYYMMDD"T"HH24MISSUS"Z"');

ALTER TABLE fact_crypto_prices
    ADD CONSTRAINT fact_crypto_prices_currency_id_fkey
    FOREIGN KEY (currency_id) REFERENCES dim_currency(currency_id);

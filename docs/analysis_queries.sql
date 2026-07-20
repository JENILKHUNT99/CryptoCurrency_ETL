-- Daily market-cap and volume by category.
SELECT
    date_dimension.full_date,
    category.category_name,
    SUM(price.market_cap) AS total_market_cap_usd,
    SUM(price.volume) AS total_volume_usd
FROM fact_crypto_prices AS price
JOIN dim_date AS date_dimension ON price.api_updated_date_id = date_dimension.date_id
JOIN dim_coin AS coin ON price.coin_id = coin.coin_id
JOIN dim_category AS category ON coin.category_id = category.category_id
GROUP BY date_dimension.full_date, category.category_name
ORDER BY date_dimension.full_date DESC, total_market_cap_usd DESC;

-- Biggest absolute 24-hour moves in the most recent observed hour.
WITH latest_hour AS (
    SELECT MAX(observed_at) AS observed_at
    FROM fact_crypto_prices
)
SELECT
    coin.coin_name,
    coin.coin_symbol,
    price.price,
    price.price_change_percent,
    price.observed_at
FROM fact_crypto_prices AS price
JOIN dim_coin AS coin ON price.coin_id = coin.coin_id
JOIN latest_hour ON price.observed_at = latest_hour.observed_at
ORDER BY ABS(price.price_change_percent) DESC
LIMIT 10;

-- Pipeline reliability and data-quality trend.
SELECT
    started_at,
    status,
    extracted_count,
    valid_count,
    extracted_count - valid_count AS rejected_count,
    completed_at - started_at AS duration
FROM pipeline_runs
ORDER BY started_at DESC;

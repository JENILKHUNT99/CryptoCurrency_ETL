-- End-of-day market-cap and volume by category and reporting currency.
-- Select one latest observation per coin/day so repeated intraday snapshots are not double counted.
WITH ranked_daily_prices AS (
    SELECT
        price.*,
        date_dimension.full_date,
        ROW_NUMBER() OVER (
            PARTITION BY price.coin_id, price.currency_id, date_dimension.full_date
            ORDER BY price.observed_at DESC
        ) AS observation_rank
    FROM fact_crypto_prices AS price
    JOIN dim_date AS date_dimension ON price.api_updated_date_id = date_dimension.date_id
)
SELECT
    price.full_date,
    category.category_name,
    currency.currency_symbol,
    SUM(price.market_cap) AS total_market_cap,
    SUM(price.volume) AS total_volume
FROM ranked_daily_prices AS price
JOIN dim_coin AS coin ON price.coin_id = coin.coin_id
JOIN dim_category AS category ON coin.category_id = category.category_id
JOIN dim_currency AS currency ON price.currency_id = currency.currency_id
WHERE price.observation_rank = 1
GROUP BY price.full_date, category.category_name, currency.currency_symbol
ORDER BY price.full_date DESC, total_market_cap DESC;

-- Biggest absolute 24-hour moves in the most recent successful pipeline batch.
WITH latest_successful_run AS (
    SELECT pipeline_run_id
    FROM pipeline_runs
    WHERE status = 'succeeded'
    ORDER BY completed_at DESC
    LIMIT 1
)
SELECT
    coin.coin_name,
    coin.coin_symbol,
    currency.currency_symbol AS reporting_currency,
    price.price,
    price.price_change_percent,
    price.observed_at
FROM fact_crypto_prices AS price
JOIN dim_coin AS coin ON price.coin_id = coin.coin_id
JOIN dim_currency AS currency ON price.currency_id = currency.currency_id
JOIN latest_successful_run AS pipeline
    ON price.pipeline_run_id = pipeline.pipeline_run_id
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

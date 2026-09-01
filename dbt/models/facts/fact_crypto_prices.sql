-- Fact model: Crypto Prices
-- Hourly cryptocurrency price observations

WITH coins AS (
    SELECT 
        coin_id,
        category_id
    FROM {{ ref('dim_coin') }}
),

staging AS (
    SELECT
        coin_id,
        current_price,
        market_cap,
        total_volume,
        high_24h,
        low_24h,
        price_change_percentage_24h,
        observed_at,
        pipeline_run_id,
        ingested_at
    FROM {{ ref('stg_raw_coins') }}
),

dates AS (
    SELECT
        date_id,
        datetime
    FROM {{ ref('dim_date') }}
),

fact AS (
    SELECT
        -- Surrogate key: coin_id + currency + observed_at
        s.coin_id || '_' || '{{ env_var("CURRENCY", "usd") }}' || '_' || 
        TO_CHAR(s.observed_at, 'YYYYMMDD"T"HH24MISSUS"Z"') AS price_id,
        
        s.coin_id,
        c.category_id,
        d.date_id AS api_updated_date_id,
        TO_CHAR(DATE_TRUNC('hour', s.ingested_at), 'YYYYMMDDHH')::INTEGER AS etl_run_date_id,
        '{{ env_var("CURRENCY", "usd") }}' AS currency_id,
        
        -- Timestamps
        s.observed_at,
        s.ingested_at,
        s.pipeline_run_id,
        
        -- Measures
        s.current_price AS price,
        s.market_cap,
        s.total_volume AS volume,
        s.high_24h,
        s.low_24h,
        s.price_change_percentage_24h
        
    FROM staging s
    JOIN coins c ON s.coin_id = c.coin_id
    JOIN dates d ON DATE_TRUNC('hour', s.observed_at) = d.datetime
)

SELECT * FROM fact

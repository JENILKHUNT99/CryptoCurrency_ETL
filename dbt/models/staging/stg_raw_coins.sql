-- Staging model: Clean raw coin data from API
-- This model reads from raw_coins table and applies basic cleaning

WITH source_data AS (
    SELECT * FROM {{ source('raw', 'coins') }}
),

cleaned AS (
    SELECT
        -- Identifiers
        id AS coin_id,
        symbol AS coin_symbol,
        name AS coin_name,
        
        -- Price data (rounded to 10 decimals)
        ROUND(current_price, 10) AS current_price,
        ROUND(high_24h, 10) AS high_24h,
        ROUND(low_24h, 10) AS low_24h,
        
        -- Market data
        market_cap,
        total_volume,
        ROUND(price_change_percentage_24h, 4) AS price_change_percentage_24h,
        
        -- Timestamps
        last_updated::TIMESTAMPTZ AS observed_at,
        
        -- Metadata
        -- Cast to UUID so joins against pipeline_runs.pipeline_run_id (UUID) work.
        -- Falls back to the nil UUID when no run id is supplied (e.g. a standalone
        -- dbt run outside the pipeline).
        NULLIF('{{ env_var("PIPELINE_RUN_ID", "") }}', '')::UUID AS pipeline_run_id,
        NOW() AS ingested_at
        
    FROM source_data
    WHERE 
        -- Basic data quality
        id IS NOT NULL
        AND symbol IS NOT NULL
        AND name IS NOT NULL
        AND current_price > 0
        AND market_cap > 0
        AND total_volume > 0
        AND high_24h >= low_24h
)

SELECT * FROM cleaned

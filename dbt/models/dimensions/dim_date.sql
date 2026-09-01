-- Dimension model: Date
-- Hourly calendar dimension from observed timestamps

WITH date_times AS (
    SELECT DISTINCT
        DATE_TRUNC('hour', observed_at) AS datetime_hour
    FROM {{ ref('stg_raw_coins') }}
    WHERE observed_at IS NOT NULL
    
    UNION
    
    SELECT DATE_TRUNC('hour', NOW())
),

date_dimension AS (
    SELECT
        TO_CHAR(datetime_hour, 'YYYYMMDDHH')::INTEGER AS date_id,
        datetime_hour AS datetime,
        datetime_hour::DATE AS full_date,
        EXTRACT(HOUR FROM datetime_hour)::INTEGER AS hour,
        EXTRACT(DAY FROM datetime_hour)::INTEGER AS day,
        TO_CHAR(datetime_hour, 'Day') AS day_name,
        EXTRACT(MONTH FROM datetime_hour)::INTEGER AS month,
        TO_CHAR(datetime_hour, 'Month') AS month_name,
        EXTRACT(QUARTER FROM datetime_hour)::INTEGER AS quarter,
        EXTRACT(YEAR FROM datetime_hour)::INTEGER AS year,
        EXTRACT(DOW FROM datetime_hour)::INTEGER AS week_number,
        CASE WHEN EXTRACT(DOW FROM datetime_hour) IN (0, 6) THEN TRUE ELSE FALSE END AS is_weekend
    FROM date_times
)

SELECT
    date_id,
    datetime,
    full_date,
    hour,
    day,
    day_name,
    month,
    month_name,
    quarter,
    year,
    is_weekend
FROM date_dimension
ORDER BY datetime

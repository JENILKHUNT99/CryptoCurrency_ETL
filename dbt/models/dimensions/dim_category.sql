-- Dimension model: Categories
-- Distinct list of cryptocurrency categories

WITH categories AS (
    SELECT DISTINCT
        category_id,
        category_name
    FROM {{ ref('dim_coin') }}
    WHERE category_id IS NOT NULL
)

SELECT
    category_id,
    category_name
FROM categories
ORDER BY category_id

-- Dimension model: Currency
-- Reporting currency for prices

SELECT
    '{{ var("currency", "usd") }}' AS currency_id,
    CASE '{{ var("currency", "usd") }}'
        WHEN 'aud' THEN 'Australian Dollar'
        WHEN 'btc' THEN 'Bitcoin'
        WHEN 'cad' THEN 'Canadian Dollar'
        WHEN 'chf' THEN 'Swiss Franc'
        WHEN 'cny' THEN 'Chinese Yuan'
        WHEN 'eth' THEN 'Ether'
        WHEN 'eur' THEN 'Euro'
        WHEN 'gbp' THEN 'British Pound'
        WHEN 'inr' THEN 'Indian Rupee'
        WHEN 'jpy' THEN 'Japanese Yen'
        WHEN 'usd' THEN 'US Dollar'
        ELSE UPPER('{{ var("currency", "usd") }}')
    END AS currency_name,
    '{{ var("currency", "usd") }}' AS currency_symbol

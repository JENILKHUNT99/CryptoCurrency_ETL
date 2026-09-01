-- Dimension model: Currency
-- Reporting currency for prices

SELECT
    '{{ env_var("CURRENCY", "usd") }}' AS currency_id,
    CASE '{{ env_var("CURRENCY", "usd") }}'
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
        ELSE UPPER('{{ env_var("CURRENCY", "usd") }}')
    END AS currency_name,
    '{{ env_var("CURRENCY", "usd") }}' AS currency_symbol

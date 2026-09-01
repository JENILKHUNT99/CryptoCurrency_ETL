-- Dimension model: Coins
-- Each row represents a unique cryptocurrency

WITH coins AS (
    SELECT 
        coin_id,
        coin_symbol,
        coin_name,
        -- Map category based on coin_id
        CASE 
            WHEN coin_id IN ('bitcoin', 'litecoin', 'bitcoin-cash', 'bitcoin-sv', 'dash', 'zcash', 'monero', 'decred', 'via') THEN 'Currency'
            WHEN coin_id IN ('ethereum', 'solana', 'cardano', 'avalanche-2', 'polkadot', 'near', 'cosmos', 'algorand', 'fantom', 'tezos', 'elrond-erd-2', 'aptos', 'flow', 'harmony', 'icon', 'ontology', 'qtum', 'neo', 'waves', 'ethereum-classic') THEN 'Smart Contract Platform'
            WHEN coin_id IN ('ripple', 'stellar', 'nano', 'pundi-x') THEN 'Payment Protocol'
            WHEN coin_id IN ('tether', 'usd-coin', 'dai') THEN 'Stablecoin'
            WHEN coin_id IN ('uniswap', 'aave', 'maker', 'pancakeswap-token', 'sushiswap', 'yearn-finance', 'curve-dao-token', 'compound-governance-token', 'balancer', 'synthetix-network-token', '1inch', 'loopring', 'kyber-network-crystal') THEN 'DeFi'
            WHEN coin_id IN ('binancecoin', 'leo-token', 'okb', 'kucoin-shares', 'crypto-com-chain') THEN 'Exchange Token'
            WHEN coin_id IN ('wrapped-bitcoin', 'staked-ether') THEN 'Wrapped Token'
            WHEN coin_id IN ('arbitrum', 'optimism', 'immutable-x', 'celer-network') THEN 'Layer 2'
            WHEN coin_id IN ('chainlink', 'the-graph', 'band-protocol', 'numeraire') THEN 'Oracle'
            WHEN coin_id IN ('decentraland', 'the-sandbox', 'axie-infinity', 'gala', 'chiliz') THEN 'Metaverse'
            WHEN coin_id IN ('filecoin', 'storj', 'ocean-protocol') THEN 'Storage'
            WHEN coin_id IN ('fetch-ai', 'render-token', 'cortex') THEN 'AI'
            WHEN coin_id IN ('vechain', 'iota', 'hedera-hashgraph', 'internet-computer') THEN 'Enterprise'
            WHEN coin_id IN ('dogecoin', 'shiba-inu') THEN 'Meme'
            ELSE 'Other'
        END AS category_name
    FROM {{ ref('stg_raw_coins') }}
),

with_category_id AS (
    SELECT
        coin_id,
        coin_symbol,
        coin_name,
        category_name,
        CASE category_name
            WHEN 'Currency' THEN 1
            WHEN 'Smart Contract Platform' THEN 2
            WHEN 'Payment Protocol' THEN 3
            WHEN 'Stablecoin' THEN 4
            WHEN 'DeFi' THEN 5
            WHEN 'Exchange Token' THEN 6
            WHEN 'Wrapped Token' THEN 7
            WHEN 'Layer 2' THEN 8
            WHEN 'Oracle' THEN 9
            WHEN 'Metaverse' THEN 10
            WHEN 'Storage' THEN 11
            WHEN 'AI' THEN 12
            WHEN 'Privacy' THEN 13
            WHEN 'Enterprise' THEN 14
            WHEN 'Meme' THEN 15
            WHEN 'Utility' THEN 16
            WHEN 'IoT' THEN 17
            ELSE 99
        END AS category_id
    FROM coins
)

SELECT
    coin_id,
    coin_symbol,
    coin_name,
    category_id,
    category_name
FROM with_category_id

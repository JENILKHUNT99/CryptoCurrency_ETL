COINS = [
    "bitcoin", "ethereum", "tether", "binancecoin", "ripple",
    "usd-coin", "solana", "staked-ether", "dogecoin", "cardano",
    "tron", "avalanche-2", "shiba-inu", "wrapped-bitcoin", "chainlink",
    "polkadot", "bitcoin-cash", "near", "litecoin", "uniswap",
    "leo-token", "dai", "internet-computer", "ethereum-classic", "aptos",
    "cosmos", "stellar", "monero", "okb", "hedera-hashgraph",
    "filecoin", "crypto-com-chain", "immutable-x", "vechain", "arbitrum",
    "optimism", "maker", "aave", "quant-network", "algorand",
    "render-token", "injective-protocol", "the-graph", "fantom", "theta-token",
    "elrond-erd-2", "axie-infinity", "decentraland", "the-sandbox", "chiliz",
    "eos", "flow", "tezos", "iota", "neo",
    "kucoin-shares", "waves", "dash", "zcash", "bitcoin-sv",
    "gala", "loopring", "1inch", "curve-dao-token", "compound-governance-token",
    "pancakeswap-token", "sushiswap", "yearn-finance", "balancer", "synthetix-network-token",
    "decred", "qtum", "ontology", "icon", "zilliqa",
    "harmony", "theta-fuel", "basic-attention-token", "ankr", "storj",
    "ocean-protocol", "band-protocol", "fetch-ai", "numeraire", "kyber-network-crystal",
    "republic-protocol", "civic", "metal", "power-ledger", "airswap",
    "celer-network", "origin-protocol", "district0x", "cortex", "adex",
    "loom-network", "gifto", "bluzelle", "via", "pundi-x"
]

COIN_CATEGORIES = {
    # Currency / Store of Value
    'bitcoin': 'Currency',
    'litecoin': 'Currency',
    'bitcoin-cash': 'Currency',
    'bitcoin-sv': 'Currency',
    'dash': 'Currency',
    'zcash': 'Currency',
    'monero': 'Currency',
    'decred': 'Currency',
    'via': 'Currency',

    # Smart Contract Platforms
    'ethereum': 'Smart Contract Platform',
    'solana': 'Smart Contract Platform',
    'cardano': 'Smart Contract Platform',
    'avalanche-2': 'Smart Contract Platform',
    'polkadot': 'Smart Contract Platform',
    'near': 'Smart Contract Platform',
    'cosmos': 'Smart Contract Platform',
    'algorand': 'Smart Contract Platform',
    'fantom': 'Smart Contract Platform',
    'tezos': 'Smart Contract Platform',
    'elrond-erd-2': 'Smart Contract Platform',
    'aptos': 'Smart Contract Platform',
    'flow': 'Smart Contract Platform',
    'harmony': 'Smart Contract Platform',
    'icon': 'Smart Contract Platform',
    'ontology': 'Smart Contract Platform',
    'qtum': 'Smart Contract Platform',
    'neo': 'Smart Contract Platform',
    'waves': 'Smart Contract Platform',
    'ethereum-classic': 'Smart Contract Platform',

    # Payment Protocols
    'ripple': 'Payment Protocol',
    'stellar': 'Payment Protocol',
    'nano': 'Payment Protocol',
    'pundi-x': 'Payment Protocol',

    # Stablecoins
    'tether': 'Stablecoin',
    'usd-coin': 'Stablecoin',
    'dai': 'Stablecoin',

    # DeFi
    'uniswap': 'DeFi',
    'aave': 'DeFi',
    'maker': 'DeFi',
    'pancakeswap-token': 'DeFi',
    'sushiswap': 'DeFi',
    'yearn-finance': 'DeFi',
    'curve-dao-token': 'DeFi',
    'compound-governance-token': 'DeFi',
    'balancer': 'DeFi',
    'synthetix-network-token': 'DeFi',
    '1inch': 'DeFi',
    'loopring': 'DeFi',
    'kyber-network-crystal': 'DeFi',

    # Exchange Tokens
    'binancecoin': 'Exchange Token',
    'leo-token': 'Exchange Token',
    'okb': 'Exchange Token',
    'kucoin-shares': 'Exchange Token',
    'crypto-com-chain': 'Exchange Token',

    # Wrapped Tokens
    'wrapped-bitcoin': 'Wrapped Token',
    'staked-ether': 'Wrapped Token',

    # Layer 2 / Scaling
    'arbitrum': 'Layer 2',
    'optimism': 'Layer 2',
    'immutable-x': 'Layer 2',
    'celer-network': 'Layer 2',

    # Oracle / Data
    'chainlink': 'Oracle',
    'the-graph': 'Oracle',
    'band-protocol': 'Oracle',
    'numeraire': 'Oracle',

    # Metaverse / Gaming / NFT
    'decentraland': 'Metaverse',
    'the-sandbox': 'Metaverse',
    'axie-infinity': 'Metaverse',
    'gala': 'Metaverse',
    'chiliz': 'Metaverse',

    # Storage / Infrastructure
    'filecoin': 'Storage',
    'storj': 'Storage',
    'ocean-protocol': 'Storage',

    # AI / Data
    'fetch-ai': 'AI',
    'render-token': 'AI',
    'cortex': 'AI',

    # Privacy
    'zcash': 'Privacy',

    # IoT / Enterprise
    'vechain': 'Enterprise',
    'iota': 'IoT',
    'hedera-hashgraph': 'Enterprise',
    'internet-computer': 'Enterprise',

    # Meme
    'dogecoin': 'Meme',
    'shiba-inu': 'Meme',

    # Utility / Other
    'tron': 'Utility',
    'eos': 'Utility',
    'theta-token': 'Utility',
    'theta-fuel': 'Utility',
    'basic-attention-token': 'Utility',
    'ankr': 'Utility',
    'republic-protocol': 'Utility',
    'civic': 'Utility',
    'metal': 'Utility',
    'power-ledger': 'Utility',
    'airswap': 'Utility',
    'origin-protocol': 'Utility',
    'district0x': 'Utility',
    'adex': 'Utility',
    'loom-network': 'Utility',
    'gifto': 'Utility',
    'bluzelle': 'Utility',
    'zilliqa': 'Utility',
    'quant-network': 'Utility',
    'injective-protocol': 'Utility',
    'maker': 'Utility',
}
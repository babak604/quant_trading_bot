# Strategy Execution Thresholds for Kinetiq Arbitrum Engine

REGIME_CONFIG = {
    0: {
        "name": "Bear",
        "min_prob": 0,
        "target_allocation_weth": 0.20,  # De-risk into stable/MOR_USD (80%)
        "rebalance_trigger": False
    },
    1: {
        "name": "Sideways",
        "min_prob": 5000,                # 50.00%
        "target_allocation_weth": 0.50,  # Neutral 50/50 balance
        "rebalance_trigger": False
    },
    2: {
        "name": "Bull",
        "min_prob": 5500,                # 55.00%
        "target_allocation_weth": 0.80,  # Overweight WETH (80%)
        "rebalance_trigger": True
    }
}

MAX_SLIPPAGE_BPS = 50   # 0.50%
SWAP_AMOUNT_WEI = 10 * 10**18  # Standard 10 unit rebalance step

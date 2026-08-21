import numpy as np

class PairArbitrageEngine:
    def __init__(self, lookback=30, z_entry=2.0, z_exit=0.5):
        self.lookback = lookback
        self.z_entry = z_entry
        self.z_exit = z_exit
        self.ratio_history = []

    def update_ratio(self, eth_price, sol_price):
        if sol_price == 0:
            return 0.0, "NEUTRAL"
        
        ratio = eth_price / sol_price
        self.ratio_history.append(ratio)
        
        if len(self.ratio_history) > self.lookback:
            self.ratio_history.pop(0)

        if len(self.ratio_history) < 10:
            return 0.0, "NEUTRAL"

        mean = np.mean(self.ratio_history)
        std = np.std(self.ratio_history)
        if std == 0:
            return 0.0, "NEUTRAL"

        z_score = (ratio - mean) / std

        signal = "NEUTRAL"
        if z_score >= self.z_entry:
            signal = "SHORT_ETH_LONG_SOL"  # Spread overpriced
        elif z_score <= -self.z_entry:
            signal = "LONG_ETH_SHORT_SOL"  # Spread underpriced

        return z_score, signal

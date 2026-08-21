
import math

class RiskEngine:
    def __init__(self, min_win_prob=0.54, kelly_fraction=0.25, max_account_risk=0.025):
        self.min_win_prob = min_win_prob
        self.kelly_fraction = kelly_fraction
        self.max_account_risk = max_account_risk

    def calculate_position_size(self, account_balance, win_prob, reward_to_risk=2.0):
        if win_prob < self.min_win_prob:
            return 0.0  # Pass Monte Carlo Gate
        
        # Full Kelly Formula: f* = (p*b - (1-p)) / b
        full_kelly = (win_prob * reward_to_risk - (1.0 - win_prob)) / reward_to_risk
        applied_kelly = max(0.0, full_kelly * self.kelly_fraction)
        
        # Enforce max 2.5% single-trade risk cap
        final_fraction = min(applied_kelly, self.max_account_risk)
        return round(account_balance * final_fraction, 2)

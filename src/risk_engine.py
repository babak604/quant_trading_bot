class KellyRiskManager:
    def __init__(self, max_portfolio_risk=0.05, kelly_fraction=0.25, min_win_prob=0.53):
        self.max_portfolio_risk = max_portfolio_risk
        self.kelly_fraction = kelly_fraction
        self.min_win_prob = min_win_prob

    def calculate_position_size(self, account_balance, win_prob, expected_price, current_price, tail_risk):
        # Enforce minimum win probability threshold to filter weak signals
        if win_prob < self.min_win_prob or expected_price <= current_price:
            return 0.0

        b = (expected_price - current_price) / current_price
        p = win_prob
        q = 1.0 - p

        f_star = (p * b - q) / b if b > 0 else 0
        f_adjusted = max(0, f_star * self.kelly_fraction)

        # Cap position sizing at max risk limit
        f_final = min(f_adjusted, self.max_portfolio_risk)
        return round(account_balance * f_final, 2)

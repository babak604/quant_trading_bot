import numpy as np

class MarkovQuantEngine:
    def __init__(self, states_count=3):
        self.states_count = states_count
        self.transition_matrix = None

    def define_states(self, returns):
        # Tighter 25th / 75th percentile bounds for higher conviction regimes
        quantiles = np.quantile(returns, [0.25, 0.75])
        states = np.digitize(returns, quantiles)
        return states

    def fit_transition_matrix(self, states):
        matrix = np.zeros((self.states_count, self.states_count))
        for i in range(len(states) - 1):
            matrix[states[i]][states[i+1]] += 1
        
        row_sums = matrix.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0
        self.transition_matrix = matrix / row_sums
        return self.transition_matrix

    def run_monte_carlo(self, current_state, initial_price, steps=20, n_sims=5000):
        if self.transition_matrix is None:
            raise ValueError("Transition matrix not fitted.")

        simulations = []
        for _ in range(n_sims):
            price = initial_price
            state = current_state
            for _ in range(steps):
                next_state = np.random.choice(
                    self.states_count, 
                    p=self.transition_matrix[state]
                )
                
                # Volatility shock multipliers per state
                if next_state == 2:
                    ret = np.random.normal(0.004, 0.0025)
                elif next_state == 0:
                    ret = np.random.normal(-0.004, 0.0025)
                else:
                    ret = np.random.normal(0.000, 0.001)
                
                price *= (1 + ret)
                state = next_state
            simulations.append(price)

        simulations = np.array(simulations)
        win_probability = np.mean(simulations > initial_price)
        tail_risk_5pct = (initial_price - np.percentile(simulations, 5)) / initial_price
        expected_price = np.mean(simulations)

        return {
            "win_probability": win_probability,
            "tail_risk_5pct": tail_risk_5pct,
            "expected_price": expected_price
        }

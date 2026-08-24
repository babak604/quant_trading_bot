import warnings
import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
from arch import arch_model

# Suppress convergence and optimization warnings
warnings.filterwarnings("ignore")

class QuantRiskEngine:
    def __init__(self, n_states=2):
        self.n_states = n_states
        self.hmm_model = GaussianHMM(
            n_components=n_states, 
            covariance_type="diag", 
            n_iter=1000, 
            tol=1e-4, 
            random_state=42
        )

    def detect_market_regime(self, df: pd.DataFrame) -> dict:
        returns = np.log(df['close'] / df['close'].shift(1)).dropna().values.reshape(-1, 1)
        self.hmm_model.fit(returns)
        hidden_states = self.hmm_model.predict(returns)
        
        variances = [np.var(returns[hidden_states == i]) for i in range(self.n_states)]
        high_vol_state = np.argmax(variances)
        current_state = hidden_states[-1]
        
        is_high_risk = bool(current_state == high_vol_state)
        return {
            "current_state": int(current_state),
            "high_vol_state": int(high_vol_state),
            "is_high_risk": is_high_risk,
            "regime_label": "HIGH_VOLATILITY_CHOP" if is_high_risk else "LOW_VOLATILITY_TREND"
        }

    def calculate_garch_position_scale(self, df: pd.DataFrame, target_vol=0.02) -> float:
        returns = 100 * np.log(df['close'] / df['close'].shift(1)).dropna()
        model = arch_model(returns, vol='Garch', p=1, q=1)
        res = model.fit(disp="off")
        
        forecast_vol = np.sqrt(res.forecast(horizon=1).variance.values[-1, :][0]) / 100
        scale = target_vol / forecast_vol if forecast_vol > 0 else 1.0
        return float(np.clip(scale, 0.1, 1.0))

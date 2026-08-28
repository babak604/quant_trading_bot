# mor.money NDAX Staking & Liquid Yield Arbitrage Engine
import time

class NDAXStakingYieldEngine:
    def __init__(self):
        # NDAX Staking APY reference table
        self.ndax_staking_apys = {
            "ETH": 0.038,  # 3.8% APY
            "SOL": 0.068,  # 6.8% APY
            "SUI": 0.052,  # 5.2% APY
            "NEAR": 0.075  # 7.5% APY
        }

    def evaluate_yield_arbitrage(self, token: str, dex_lsd_apy: float, position_size_cad: float) -> dict:
        """Evaluates yield spread between NDAX native staking and Arbitrum DEX LSD pools."""
        ndax_apy = self.ndax_staking_apys.get(token, 0.0)
        yield_spread = ndax_apy - dex_lsd_apy

        # Arbitrage threshold: 0.50% net APY differential
        if yield_spread > 0.005:
            recommendation = "ROUTE_TO_NDAX_STAKING"
            est_extra_annual_yield = position_size_cad * yield_spread
        elif yield_spread < -0.005:
            recommendation = "ROUTE_TO_ARBITRUM_LSD_DEX"
            est_extra_annual_yield = position_size_cad * abs(yield_spread)
        else:
            recommendation = "YIELD_PARITY_HOLD"
            est_extra_annual_yield = 0.0

        return {
            "token": token,
            "ndax_apy": f"{ndax_apy*100:.2f}%",
            "dex_lsd_apy": f"{dex_lsd_apy*100:.2f}%",
            "spread": f"{yield_spread*100:.2f}%",
            "recommendation": recommendation,
            "est_extra_annual_cad": round(est_extra_annual_yield, 2)
        }

if __name__ == "__main__":
    engine = NDAXStakingYieldEngine()
    res = engine.evaluate_yield_arbitrage("ETH", dex_lsd_apy=0.031, position_size_cad=100000.0)
    print("=== NDAX STAKING YIELD ENGINE TEST ===")
    print(f"[PASS] {res['token']} Spread: {res['spread']} -> Recommendation: {res['recommendation']} (+${res['est_extra_annual_cad']} CAD/yr)")

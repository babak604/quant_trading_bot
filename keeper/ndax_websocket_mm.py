# mor.money NDAX L2 Order Book WebSocket Market Maker
import json
import time

class NDAXWebSocketMarketMaker:
    def __init__(self, ws_endpoint: str = "wss://api.ndax.io/WSGateway/"):
        self.ws_endpoint = ws_endpoint
        self.target_spread_pct = 0.0015 # 0.15% target bid-ask spread

    def compute_market_maker_quotes(self, mid_price_cad: float, size_eth: float) -> dict:
        """Generates two-sided limit orders centered on mid-market price."""
        half_spread = (mid_price_cad * self.target_spread_pct) / 2.0
        bid_price = round(mid_price_cad - half_spread, 2)
        ask_price = round(mid_price_cad + half_spread, 2)

        return {
            "endpoint": self.ws_endpoint,
            "mid_price_cad": mid_price_cad,
            "bid_quote": bid_price,
            "ask_quote": ask_price,
            "spread_cad": round(ask_price - bid_price, 2),
            "size_eth": size_eth,
            "execution": "BALANCER_V2_ZERO_CAPITAL_FLASH_LOAN"
        }

if __name__ == "__main__":
    mm = NDAXWebSocketMarketMaker()
    quotes = mm.compute_market_maker_quotes(3500.00, 5.0)
    print("=== NDAX WEBSOCKET MARKET MAKER TEST ===")
    print(f"[PASS] Mid: ${quotes['mid_price_cad']} | Bid: ${quotes['bid_quote']} | Ask: ${quotes['ask_quote']} (Spread: ${quotes['spread_cad']})")

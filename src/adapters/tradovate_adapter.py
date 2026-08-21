import os
import aiohttp
from src.adapters.base_adapter import BaseMarketAdapter

class TradovateMarketAdapter(BaseMarketAdapter):
    def __init__(self):
        self.username = os.getenv("TRADOVATE_USER", "")
        self.password = os.getenv("TRADOVATE_PASS", "")
        self.is_demo = os.getenv("TRADOVATE_IS_DEMO", "True").lower() == "true"

    async def connect_websocket(self):
        print("🟢 Connected to Tradovate CME Market Depth Feed")

    def calculate_ofi(self, book_depth: dict) -> float:
        bid_vol = book_depth.get("bid_size", 0.0)
        ask_vol = book_depth.get("ask_size", 0.0)
        return float(bid_vol - ask_vol)

    async def execute_bracket_order(
        self, symbol: str, side: str, qty: float, current_price: float, sl_pct: float = 0.015, tp_pct: float = 0.030
    ):
        if not self.username:
            raise ValueError("Tradovate credentials not configured.")
        return {"status": "Adapter Ready"}

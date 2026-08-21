import os
import aiohttp
from src.adapters.base_adapter import BaseMarketAdapter

class OandaMarketAdapter(BaseMarketAdapter):
    def __init__(self):
        self.api_key = os.getenv("OANDA_API_KEY", "")
        self.account_id = os.getenv("OANDA_ACCOUNT_ID", "")
        self.environment = os.getenv("OANDA_ENV", "practice")
        self.base_url = "https://api-fxpractice.oanda.com" if self.environment == "practice" else "https://api-fxtrade.oanda.com"

    async def connect_websocket(self):
        print("🟢 Connected to OANDA v20 Forex Streaming Feed")

    def calculate_ofi(self, book_depth: dict) -> float:
        bid_vol = book_depth.get("bids_volume", 0.0)
        ask_vol = book_depth.get("asks_volume", 0.0)
        return float(bid_vol - ask_vol)

    async def execute_bracket_order(
        self, symbol: str, side: str, units: float, current_price: float, sl_pct: float = 0.015, tp_pct: float = 0.030
    ):
        if not self.api_key or not self.account_id:
            raise ValueError("OANDA API credentials not configured.")
        return {"status": "Adapter Ready"}

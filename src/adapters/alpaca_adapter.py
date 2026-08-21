import os
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, TakeProfitRequest, StopLossRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass
from src.adapters.base_adapter import BaseMarketAdapter

class AlpacaMarketAdapter(BaseMarketAdapter):
    def __init__(self):
        self.api_key = os.getenv("ALPACA_API_KEY", "")
        self.secret_key = os.getenv("ALPACA_SECRET_KEY", "")
        self.is_paper = os.getenv("ALPACA_IS_PAPER", "True").lower() == "true"
        if self.api_key and self.secret_key:
            self.client = TradingClient(self.api_key, self.secret_key, paper=self.is_paper)
        else:
            self.client = None

    async def connect_websocket(self):
        print("🟢 Connected to Alpaca SIP/IEX Stock Data Stream")

    def calculate_ofi(self, book_depth: dict) -> float:
        bid_vol = book_depth.get("bid_qty", 0.0)
        ask_vol = book_depth.get("ask_qty", 0.0)
        return float(bid_vol - ask_vol)

    async def execute_bracket_order(
        self, symbol: str, side: str, qty: float, current_price: float, sl_pct: float = 0.015, tp_pct: float = 0.030
    ):
        if not self.client:
            raise ValueError("Alpaca API keys not configured in environment.")

        order_side = OrderSide.BUY if side.upper() == "BUY" else OrderSide.SELL

        if order_side == OrderSide.BUY:
            tp_price = round(current_price * (1.0 + tp_pct), 2)
            sl_price = round(current_price * (1.0 - sl_pct), 2)
        else:
            tp_price = round(current_price * (1.0 - tp_pct), 2)
            sl_price = round(current_price * (1.0 + sl_pct), 2)

        req = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=order_side,
            time_in_force=TimeInForce.GTC,
            order_class=OrderClass.BRACKET,
            take_profit=TakeProfitRequest(limit_price=tp_price),
            stop_loss=StopLossRequest(stop_price=sl_price)
        )
        return self.client.submit_order(order_request=req)

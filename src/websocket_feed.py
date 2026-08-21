import json
import threading
import websocket

class HyperliquidWSFeed:
    def __init__(self, coins=["ETH", "SOL", "MSTR", "GOLD"], is_testnet=True):
        self.coins = coins
        self.ws_url = "wss://api.hyperliquid-testnet.xyz/ws" if is_testnet else "wss://api.hyperliquid.xyz/ws"
        self.orderbooks = {coin: {"bids": [], "asks": []} for coin in coins}

    def _on_message(self, ws, message):
        try:
            data = json.loads(message)
            if data.get("channel") == "l2Book":
                book_data = data.get("data", {})
                coin = book_data.get("coin")
                if coin in self.orderbooks:
                    levels = book_data.get("levels", [[], []])
                    self.orderbooks[coin]["bids"] = levels[0]
                    self.orderbooks[coin]["asks"] = levels[1]
        except: pass

    def _on_open(self, ws):
        for coin in self.coins:
            ws.send(json.dumps({"method": "subscribe", "subscription": {"type": "l2Book", "coin": coin}}))

    def start(self):
        ws = websocket.WebSocketApp(self.ws_url, on_open=self._on_open, on_message=self._on_message)
        threading.Thread(target=ws.run_forever, daemon=True).start()

    def get_ofi_and_price(self, coin, depth_levels=5):
        book = self.orderbooks.get(coin, {"bids": [], "asks": []})
        bids = book["bids"][:depth_levels]
        asks = book["asks"][:depth_levels]
        if not bids or not asks: return 0.0, 0.0
        ofi = (sum(float(b["sz"]) for b in bids) - sum(float(a["sz"]) for a in asks)) / (sum(float(b["sz"]) for b in bids) + sum(float(a["sz"]) for a in asks) + 1e-9)
        return float(bids[0]["px"]), ofi

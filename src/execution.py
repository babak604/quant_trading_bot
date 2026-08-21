import os
import requests
from eth_account import Account
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants

class HyperliquidExecutor:
    def __init__(self, is_testnet=True):
        self.is_testnet = is_testnet
        self.secret_key = os.getenv("HL_SECRET_KEY")
        self.account_address = os.getenv("HL_ACCOUNT_ADDRESS")
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

        if not self.secret_key or "YOUR_PRIVATE_KEY" in self.secret_key:
            print("[WARN] Valid HL_SECRET_KEY not found in .env. Running in DRY-RUN mode.")
            self.exchange = None
        else:
            account = Account.from_key(self.secret_key)
            base_url = constants.TESTNET_API_URL if is_testnet else constants.MAINNET_API_URL
            self.exchange = Exchange(account, base_url, account_address=self.account_address)

    def send_telegram_alert(self, message):
        if not self.telegram_token or not self.telegram_chat_id:
            return
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            payload = {"chat_id": self.telegram_chat_id, "text": message, "parse_mode": "Markdown"}
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            print(f"[WARN] Failed to send Telegram alert: {e}")

    def execute_market_buy(self, coin, sz_units):
        if not self.exchange:
            msg = f"🧪 [DRY-RUN] Simulated BUY order: {sz_units} {coin}"
            print(msg)
            self.send_telegram_alert(msg)
            return {"status": "simulated", "size": sz_units}

        try:
            print(f"[EXECUTION] Submitting live BUY order: {sz_units} {coin}...")
            order_result = self.exchange.market_open(
                name=coin,
                is_buy=True,
                sz=sz_units,
                px=None,
                slippage=0.01
            )
            print(f"[EXECUTION SUCCESS] Order Response: {order_result}")
            self.send_telegram_alert(
                f"🚀 *TRADE EXECUTED*\n"
                f"• Asset: {coin}\n"
                f"• Size: {sz_units} units\n"
                f"• Network: {'Testnet' if self.is_testnet else 'Mainnet'}"
            )
            return order_result
        except Exception as e:
            error_msg = f"❌ [EXECUTION ERROR] Order failed: {e}"
            print(error_msg)
            self.send_telegram_alert(error_msg)
            return None

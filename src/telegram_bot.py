import os, requests, sqlite3
from dotenv import load_dotenv

load_dotenv()

class TelegramCommandCenter:
    def __init__(self, executor, db_path="markov_1.db"):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.executor = executor
        self.running = True

    def poll_updates(self):
        try:
            res = requests.get(f"https://api.telegram.org/bot{self.token}/getUpdates?timeout=1").json()
            for result in res.get("result", []):
                text = result.get("message", {}).get("text", "")
                if text == "/status": self.send("🟢 *Markov-1 Operational*")
                elif text == "/stop": 
                    self.running = False
                    self.send("⚠️ *Engine Paused* - Manual intervention required to restart.")
                elif text == "/closeall":
                    self.executor.close_all_positions()
                    self.send("🚨 *Positions Liquidated* - All assets closed.")
                elif text == "/resume":
                    self.running = True
                    self.send("✅ *Engine Resumed*")
        except: pass

    def send(self, text):
        requests.post(f"https://api.telegram.org/bot{self.token}/sendMessage", json={"chat_id": self.chat_id, "text": text, "parse_mode": "Markdown"})

import asyncio
import sqlite3
import datetime
import random

DB_PATH = "markov_1.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trading_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            symbol TEXT,
            regime TEXT,
            win_prob REAL,
            ofi_value REAL,
            signal TEXT
        )
    """)
    conn.commit()
    conn.close()

async def telemetry_loop():
    init_db()
    print("🟢 Telemetry Engine initialized...")

    while True:
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            regimes = ["Range-Bound", "Bullish", "Bearish"]
            regime = random.choice(regimes)
            win_prob = round(random.uniform(0.48, 0.56), 4)
            ofi_val = round(random.uniform(-0.15, 0.15), 4)
            signal = "HOLD" if win_prob < 0.53 else "BUY"

            timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
            cursor.execute(
                "INSERT INTO trading_signals (timestamp, symbol, regime, win_prob, ofi_value, signal) VALUES (?, ?, ?, ?, ?, ?)",
                (timestamp, "BTC-PERP", regime, win_prob, ofi_val, signal)
            )
            conn.commit()
            conn.close()

            print(f"[{timestamp}] Snapshot recorded | Regime: {regime} | Win Prob: {win_prob:.2%}")
            await asyncio.sleep(5)  # Captures 12 snapshots/minute

        except Exception as e:
            print(f"⚠️ Telemetry loop error: {e}. Retrying in 5s...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(telemetry_loop())

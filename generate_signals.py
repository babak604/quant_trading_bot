import time
import sqlite3
import pandas as pd
import yfinance as yf
from datetime import datetime
from quant_engine import QuantRiskEngine

DB_PATH = "/home/ubuntu/quant_trading_bot/signals.db"
COOLDOWN_SECONDS = 3600  # 1 hour minimum between signals

def parse_timestamp(val):
    if isinstance(val, int):
        return val
    if isinstance(val, str):
        try:
            return int(val)
        except ValueError:
            try:
                dt = datetime.strptime(val, "%Y-%m-%d %H:%M:%S")
                return int(dt.timestamp())
            except ValueError:
                return 0
    return 0

def run_pipeline(symbol="BTC", ticker="BTC-USD"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS markov_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            regime TEXT NOT NULL,
            win_prob_bps INTEGER NOT NULL,
            timestamp INTEGER NOT NULL,
            executed INTEGER DEFAULT 0
        )
    """)

    # 1. Cooldown Guard: Safely parse timestamp of the latest signal overall
    cursor.execute("""
        SELECT timestamp FROM markov_signals 
        ORDER BY id DESC LIMIT 1
    """)
    last_row = cursor.fetchone()
    current_time = int(time.time())

    if last_row and last_row[0] is not None:
        last_time = parse_timestamp(last_row[0])
        elapsed = current_time - last_time
        if elapsed < COOLDOWN_SECONDS:
            print(f"Cooldown active. Last signal was generated {elapsed}s ago (Min required: {COOLDOWN_SECONDS}s). Skipping execution.")
            conn.close()
            return

    # 2. Fetch market data
    print(f"Fetching market data for {ticker}...")
    df = yf.download(ticker, period="30d", interval="1h", progress=False)
    
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0].lower() for c in df.columns]
    else:
        df.columns = [c.lower() for c in df.columns]

    # 3. Quant Risk Engine Checks
    engine = QuantRiskEngine()
    regime_data = engine.detect_market_regime(df)
    scale = engine.calculate_garch_position_scale(df)

    print(f"Market Regime: {regime_data['regime_label']}")
    print(f"GARCH Position Scale: {scale:.2f}x")

    # 4. Compute Probability & Signals
    base_win_prob_bps = 5800
    target_win_prob = int(base_win_prob_bps * scale)
    regime_str = "BULL_EXPANSION" if not regime_data['is_high_risk'] else "HIGH_VOLATILITY_CHOP"

    if regime_data['is_high_risk']:
        print(f"Regime is HIGH VOLATILITY CHOP. Signal for {symbol} blocked.")
        executed_flag = 1
    else:
        executed_flag = 0
        print(f"Generated Signal: {symbol} | Regime: {regime_str} | Win Prob: {target_win_prob} bps")

    cursor.execute("""
        INSERT INTO markov_signals (symbol, regime, win_prob_bps, timestamp, executed)
        VALUES (?, ?, ?, ?, ?)
    """, (symbol, regime_str, target_win_prob, current_time, executed_flag))

    conn.commit()
    conn.close()
    print("Signal stored in markov_signals table.")

if __name__ == "__main__":
    run_pipeline()

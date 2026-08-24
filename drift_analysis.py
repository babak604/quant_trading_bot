import sqlite3
import pandas as pd
import yfinance as yf
from datetime import datetime

DB_PATH = "/home/ubuntu/quant_trading_bot/signals.db"

def analyze_drift():
    conn = sqlite3.connect(DB_PATH)
    df_signals = pd.read_sql_query("SELECT id, symbol, regime, timestamp FROM markov_signals ORDER BY id DESC LIMIT 20", conn)
    conn.close()

    if df_signals.empty:
        print("No historical signals available for drift evaluation.")
        return

    print("=== MARKOV SIGNAL FORWARD PERFORMANCE & DRIFT ANALYSIS ===")
    
    ticker_df = yf.download("BTC-USD", period="7d", interval="1h", progress=False)
    if isinstance(ticker_df.columns, pd.MultiIndex):
        ticker_df.columns = [c[0].lower() for c in ticker_df.columns]
    else:
        ticker_df.columns = [c.lower() for c in ticker_df.columns]

    print(f"\nAnalyzed Signals: {len(df_signals)}")
    print(df_signals[['id', 'symbol', 'regime', 'timestamp']].head(10))

if __name__ == '__main__':
    analyze_drift()

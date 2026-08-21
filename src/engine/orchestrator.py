
import os
import sqlite3
import datetime

EXECUTION_MODE = "LIVE"  # Options: 'SIMULATED' or 'LIVE'

def process_signal(symbol, regime, win_prob, ofi_value):
    if win_prob < 0.54:
        return
        
    print(f"[{datetime.datetime.now()}] 🚀 LIVE SIGNAL DETECTED: {symbol} | Prob: {win_prob:.2%} | Mode: {EXECUTION_MODE}")
    # Execution adapters (Hyperliquid / IBKR / OANDA) trigger here

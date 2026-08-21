import sqlite3
import pandas as pd
from datetime import datetime, timedelta

def generate_daily_summary(db_path="markov_1.db"):
    conn = sqlite3.connect(db_path)
    twenty_four_hours_ago = (datetime.utcnow() - timedelta(days=1)).isoformat()
    
    query = f"""
    SELECT coin, regime, signal, win_prob, count(*) as count
    FROM trading_signals
    WHERE timestamp >= '{twenty_four_hours_ago}'
    GROUP BY coin, regime, signal
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        return "📊 *Markov-1 Daily Report*: No cycles recorded in the last 24h."
        
    summary = "📊 *MARKOV-1 24H TELEMETRY REPORT*\n"
    summary += "=============================\n"
    for coin in df['coin'].unique():
        coin_df = df[df['coin'] == coin]
        total_cycles = coin_df['count'].sum()
        avg_win_prob = coin_df['win_prob'].mean() * 100
        summary += f"\n*Asset:* `{coin}`\n"
        summary += f"• Total Cycles: `{total_cycles}`\n"
        summary += f"• Mean Win Prob: `{avg_win_prob:.1f}%`\n"
        
        buys = coin_df[coin_df['signal'] == 'BUY']['count'].sum()
        holds = coin_df[coin_df['signal'] == 'HOLD']['count'].sum()
        summary += f"• Signals: `{buys} BUYs` | `{holds} HOLDs`\n"
        
    return summary

import os
import sqlite3
import pandas as pd
import streamlit as st

DB_PATH = os.getenv("DB_PATH", "markov_1.db")

st.set_page_config(page_title="Markov Strategy Dashboard", layout="wide")
st.title("📊 Markov Strategy Performance & Signals")

@st.cache_data(ttl=5)
def load_data():
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
    
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM trading_signals ORDER BY id DESC LIMIT 200", conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

df = load_data()

# Summary Metrics Row
col1, col2, col3 = st.columns(3)
col1.metric("Total Signals", len(df) if not df.empty else 0)

if not df.empty and 'win_prob' in df.columns:
    col2.metric("Avg Win Prob", f"{df['win_prob'].mean():.2%}")
elif not df.empty and 'win_prob_bps' in df.columns:
    col2.metric("Avg Win Prob", f"{(df['win_prob_bps'].mean() / 100):.2f}%")
else:
    col2.metric("Avg Win Prob", "N/A")

if not df.empty and 'coin' in df.columns and 'price' in df.columns:
    eth_df = df[df['coin'] == 'ETH']
    eth_price_str = f"${eth_df['price'].iloc[0]:.2f}" if not eth_df.empty else "N/A"
elif not df.empty and 'symbol' in df.columns and 'price' in df.columns:
    eth_df = df[df['symbol'].str.contains('ETH', case=False, na=False)]
    eth_price_str = f"${eth_df['price'].iloc[0]:.2f}" if not eth_df.empty else "N/A"
else:
    eth_price_str = "N/A"

col3.metric("Latest ETH Price", eth_price_str)

st.subheader("Signal Logs")
if not df.empty:
    st.dataframe(df, use_container_width=True)
else:
    st.info("No signal data found.")

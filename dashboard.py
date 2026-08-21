import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Markov-1 Dashboard", layout="wide")
st.title("⚡ Markov-1 Quantitative Trading Dashboard")

def load_data():
    conn = sqlite3.connect("markov_1.db")
    df = pd.read_sql_query("SELECT * FROM trading_signals ORDER BY id DESC LIMIT 200", conn)
    conn.close()
    return df

df = load_data()

if not df.empty:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Cycles Evaluated", len(df))
    col2.metric("Mean Win Probability", f"{df['win_prob'].mean()*100:.1f}%")
    col3.metric("Latest ETH Price", f"${df[df['coin']=='ETH']['price'].iloc[0]:.2f}" if not df[df['coin']=='ETH'].empty else "N/A")
    col4.metric("Latest SOL Price", f"${df[df['coin']=='SOL']['price'].iloc[0]:.2f}" if not df[df['coin']=='SOL'].empty else "N/A")

    st.subheader("📊 Recent Telemetry & Regime Logs")
    st.dataframe(df[['timestamp', 'coin', 'price', 'ofi', 'regime', 'win_prob', 'signal', 'pos_size_usd']], use_container_width=True)

    st.subheader("📈 Order Flow Imbalance (OFI) Distribution")
    st.line_chart(df.pivot(columns='coin', values='ofi'))
else:
    st.info("No database records found yet.")

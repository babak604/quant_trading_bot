import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime, timezone
from web3 import Web3
from keeper import VAULT_ADDRESS, VAULT_ABI, RPC_ENDPOINTS

st.set_page_config(page_title="mor.money Dashboard", page_icon="⚡", layout="wide")

st.title("⚡ mor.money — Quantitative Engine Dashboard")
st.caption(f"Arbitrum Sepolia | Active Vault: `{VAULT_ADDRESS}`")

# -------------------------------------------------------------------
# Sidebar Component 1: On-Chain Vault State
# -------------------------------------------------------------------
st.sidebar.header("On-Chain Vault State")
try:
    w3 = Web3(Web3.HTTPProvider(RPC_ENDPOINTS[0]))
    contract = w3.eth.contract(address=VAULT_ADDRESS, abi=VAULT_ABI)
    owner = contract.functions.owner().call()
    regime = contract.functions.currentRegime().call()
    prob = contract.functions.currentWinProbBps().call()

    st.sidebar.success("Connected to Arbitrum Sepolia")
    st.sidebar.metric("Current On-Chain Regime", regime)
    st.sidebar.metric("Win Probability (BPS)", f"{prob} BPS")
    st.sidebar.text(f"Owner:\n{owner[:10]}...{owner[-8:]}")
except Exception as e:
    st.sidebar.error(f"On-chain connection error: {e}")

st.sidebar.markdown("---")

# -------------------------------------------------------------------
# Sidebar Component 2: Signal Injection Controls
# -------------------------------------------------------------------
st.sidebar.header("Inject Test Signal")
with st.sidebar.form("signal_injection_form"):
    symbol = st.selectbox("Trading Pair Symbol", ["ETH/USD", "BTC/USD", "ARB/USD"])
    regime_input = st.selectbox("Target Regime", ["BULL_MOMENTUM", "BEAR_REVERSAL", "NEUTRAL_RANGE", "HIGH_VOLATILITY"])
    win_prob_pct = st.slider("Win Probability (%)", min_value=10, max_value=100, value=75, step=5)
    
    submit_button = st.form_submit_button("Broadcast Signal")

if submit_button:
    win_prob_bps = int(win_prob_pct * 100)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    try:
        conn = sqlite3.connect("signals.db")
        c = conn.cursor()
        c.execute("""
            INSERT INTO markov_signals (timestamp, symbol, regime, win_prob_bps, executed)
            VALUES (?, ?, ?, ?, 0)
        """, (timestamp, symbol, regime_input, win_prob_bps))
        signal_id = c.lastrowid
        conn.commit()
        conn.close()

        st.sidebar.success(f"Signal #{signal_id} ({symbol}: {regime_input}) injected successfully!")
    except Exception as e:
        st.sidebar.error(f"Failed to insert signal: {e}")

# -------------------------------------------------------------------
# Main Dashboard: SQLite Signal Queue View
# -------------------------------------------------------------------
st.header("Signal Pipeline (signals.db)")

def get_signals():
    conn = sqlite3.connect("signals.db")
    df = pd.read_sql_query(
        "SELECT id, timestamp, symbol, regime, win_prob_bps, executed FROM markov_signals ORDER BY id DESC LIMIT 50",
        conn
    )
    conn.close()
    
    # Type casting for PyArrow compatibility
    df['id'] = df['id'].astype(int)
    df['timestamp'] = df['timestamp'].astype(str)
    df['symbol'] = df['symbol'].astype(str)
    df['regime'] = df['regime'].astype(str)
    df['win_prob_bps'] = df['win_prob_bps'].astype(int)
    df['executed'] = df['executed'].astype(int)
    return df

try:
    df = get_signals()
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Signals", len(df))
    col2.metric("Executed Signals", int((df['executed'] == 1).sum()))
    col3.metric("Pending Signals", int((df['executed'] == 0).sum()))

    st.subheader("Recent Markov Signals")
    st.dataframe(df, width="stretch")

    if st.button("Refresh Signals"):
        st.rerun()

except Exception as e:
    st.error(f"Failed to read signals.db: {e}")

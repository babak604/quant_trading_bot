import sqlite3, os
import streamlit as st
import pandas as pd
from web3 import Web3

st.set_page_config(page_title="QuantVault Strategy Engine", layout="wide")

st.title("⚡ QuantVault | Markov Strategy & Arbitrum Engine")
st.caption("Target Contract: 0x586C59EF9eAC77f5386fC814Bb6626Ac67f4fAdD (Arbitrum Sepolia)")

RPC_URL = "https://sepolia-rollup.arbitrum.io/rpc"
VAULT_ADDRESS = "0x586C59EF9eAC77f5386fC814Bb6626Ac67f4fAdD"

@st.cache_resource
def get_onchain_state():
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        abi = [
            {"inputs": [], "name": "currentRegime", "outputs": [{"type": "string"}], "stateMutability": "view", "type": "function"},
            {"inputs": [], "name": "currentWinProbBps", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
            {"inputs": [], "name": "paused", "outputs": [{"type": "bool"}], "stateMutability": "view", "type": "function"}
        ]
        contract = w3.eth.contract(address=VAULT_ADDRESS, abi=abi)
        regime = contract.functions.currentRegime().call() or "UNINITIALIZED"
        win_prob = contract.functions.currentWinProbBps().call()
        is_paused = contract.functions.paused().call()
        return True, regime, win_prob, is_paused
    except Exception as e:
        return False, str(e), 0, False

connected, regime, win_prob, is_paused = get_onchain_state()

col1, col2, col3, col4 = st.columns(4)
col1.metric("On-Chain Regime", regime)
col2.metric("Win Probability", f"{win_prob / 100:.2f}%")
col3.metric("Arbitrum RPC", "Connected" if connected else "Offline")
col4.metric("Circuit Breaker", "PAUSED" if is_paused else "ACTIVE")

st.markdown("---")

st.subheader("🎯 Ecosystem Strategy Allocation")
if win_prob >= 8000:
    st.info("🔥 **Active Strategy: Camelot V3 Concentrated Liquidity** (High-Volume Fee Capture)")
elif win_prob >= 5000:
    st.success("🛡️ **Active Strategy: GMX v2 GM Liquidity** (Delta-Neutral Yield Generation)")
else:
    st.warning("💵 **Active Strategy: 100% USDC Cash Reserves** (Capital Preservation)")

st.markdown("---")

st.subheader("📊 Markov Strategy Performance & Signals Log")

def load_data():
    for db_file in ["signals.db", "markov_1.db"]:
        path = f"/home/ubuntu/quant_trading_bot/{db_file}"
        if os.path.exists(path) and os.path.getsize(path) > 0:
            try:
                conn = sqlite3.connect(path)
                df = pd.read_sql_query("SELECT * FROM markov_signals ORDER BY id DESC LIMIT 50", conn)
                conn.close()
                if not df.empty:
                    return df, db_file
            except Exception:
                pass
    return pd.DataFrame(), None

df, source_db = load_data()

if not df.empty:
    st.caption(f"Connected to database source:  ({len(df)} recent records displayed)")
    st.dataframe(df, use_container_width=True)
else:
    st.info("No signal data found across database files.")

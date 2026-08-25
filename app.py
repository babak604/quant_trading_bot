import os
import sqlite3
import streamlit as st
from web3 import Web3

st.set_page_config(page_title="QuantVault Strategy Engine", layout="wide")

st.title("⚡ QuantVault | Markov Strategy & Arbitrum Engine")
st.caption("Target Contract: 0x586C59EF9eAC77f5386fC814Bb6626Ac67f4fAdD (Arbitrum Sepolia)")

RPC_URL = st.secrets.get("web3", {}).get("rpc_url", "https://sepolia-rollup.arbitrum.io/rpc")
VAULT_ADDRESS = "0x586C59EF9eAC77f5386fC814Bb6626Ac67f4fAdD"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "signals.db")

@st.cache_resource
def get_onchain_state():
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        if not w3.is_connected():
            return False, "RPC_DISCONNECTED", 0, False
            
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

st.sidebar.markdown(f"**Web3 Status:** `{'Connected' if connected else 'Disconnected'}`")
st.sidebar.markdown(f"**Target Chain:** Arbitrum Sepolia")

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
try:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS markov_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            symbol TEXT,
            regime TEXT,
            win_prob_bps INTEGER,
            executed INTEGER
        )
    """)
    conn.commit()
    
    c.execute("SELECT id, timestamp, symbol, regime, win_prob_bps, executed FROM markov_signals ORDER BY id DESC LIMIT 20")
    rows = c.fetchall()
    conn.close()

    if rows:
        st.dataframe(
            rows,
            column_config={
                "0": "ID",
                "1": "Timestamp",
                "2": "Symbol",
                "3": "Regime",
                "4": "Win Prob (BPS)",
                "5": "On-Chain Status"
            },
            use_container_width=True
        )
    else:
        st.info("No signals found in signals.db")
except Exception as e:
    st.error(f"Error reading signals.db: {e}")

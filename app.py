import sqlite3, os
import streamlit as st
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

def load_signals():
    for db_name in ["signals.db", "markov_1.db"]:
        path = f"/home/ubuntu/quant_trading_bot/{db_name}"
        if os.path.exists(path) and os.path.getsize(path) > 0:
            try:
                conn = sqlite3.connect(path)
                c = conn.cursor()
                c.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [t[0] for t in c.fetchall() if t[0] != 'sqlite_sequence']
                if tables:
                    target_table = tables[0]
                    c.execute(f"SELECT * FROM {target_table} ORDER BY 1 DESC LIMIT 50")
                    rows = c.fetchall()
                    c.execute(f"PRAGMA table_info({target_table})")
                    cols = [col[1] for col in c.fetchall()]
                    conn.close()
                    if rows:
                        return rows, cols, db_name, target_table
            except Exception:
                pass
    return None, None, None, None

rows, cols, active_db, active_table = load_signals()

if rows:
    st.caption(f"Source: Database  | Table ")
    import pandas as pd
    df = pd.DataFrame(rows, columns=cols)
    st.dataframe(df, use_container_width=True)
else:
    st.info("No active signal logs found across signals.db or markov_1.db.")

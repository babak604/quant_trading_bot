import os
import sqlite3
import streamlit as st
from web3 import Web3
from web3.providers.rpc import HTTPProvider

st.set_page_config(page_title="QuantVault Strategy Engine", layout="wide")

st.title("⚡ QuantVault | Markov Strategy & Arbitrum Engine")
st.caption("Target Contract: 0xDc68b9285A395AE027a0eD82e937A8e3832F17CA (Arbitrum Sepolia)")

VAULT_ADDRESS = Web3.to_checksum_address("0xDc68b9285A395AE027a0eD82e937A8e3832F17CA")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "signals.db")

# Read Secret RPC first
secret_rpc = ""
try:
    secret_rpc = st.secrets["web3"]["rpc_url"].strip()
except Exception:
    pass

RPC_ENDPOINTS = [
    secret_rpc,
    "https://sepolia-rollup.arbitrum.io/rpc",
    "https://arbitrum-sepolia.publicnode.com",
    "https://endpoints.omniatech.io/v1/arbitrum/sepolia/public",
    "https://rpc.ankr.com/arbitrum_sepolia"
]

def get_onchain_state():
    last_err = ""
    for rpc in RPC_ENDPOINTS:
        if not rpc or "YOUR_KEY" in rpc:
            continue
        try:
            provider = HTTPProvider(
                rpc, 
                request_kwargs={
                    'timeout': 8,
                    'headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                }
            )
            w3 = Web3(provider)
            if w3.is_connected():
                abi = [
                    {"inputs": [], "name": "totalAssets", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
                    {"inputs": [], "name": "currentRegime", "outputs": [{"type": "string"}], "stateMutability": "view", "type": "function"},
                    {"inputs": [], "name": "currentWinProbBps", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
                    {"inputs": [], "name": "paused", "outputs": [{"type": "bool"}], "stateMutability": "view", "type": "function"}
                ]
                contract = w3.eth.contract(address=VAULT_ADDRESS, abi=abi)
                total_assets = contract.functions.totalAssets().call()
                regime = contract.functions.currentRegime().call() or "UNINITIALIZED"
                win_prob = contract.functions.currentWinProbBps().call()
                is_paused = contract.functions.paused().call()
                return True, regime, win_prob, total_assets, is_paused, rpc
        except Exception as e:
            last_err = str(e)
            continue
    return False, "RPC_DISCONNECTED", 0, 0, False, last_err

connected, regime, win_prob, total_assets, is_paused, rpc_info = get_onchain_state()

st.sidebar.markdown(f"**Web3 Status:** `{'Connected' if connected else 'Disconnected'}`")
st.sidebar.markdown(f"**Target Chain:** Arbitrum Sepolia")
if connected:
    st.sidebar.caption(f"RPC: `{rpc_info[:30]}...`")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Vault Assets", f"${total_assets / 1e6:,.2f} USDC")
col2.metric("Win Probability", f"{win_prob / 100:.2f}%")
col3.metric("On-Chain Regime", regime)
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
    
    c.execute("SELECT id, timestamp, symbol, regime, win_prob_bps, executed FROM markov_signals ORDER BY id DESC LIMIT 50")
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
        st.info("No signals recorded in signals.db yet.")
except Exception as e:
    st.error(f"Error reading signals.db: {e}")

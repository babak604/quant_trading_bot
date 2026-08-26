import os, time
import streamlit as st
import pandas as pd
from web3 import Web3
from dotenv import load_dotenv

load_dotenv('/home/ubuntu/quant_trading_bot/.env')

st.set_page_config(page_title="Kinetiq Quant Engine | Arbitrum", layout="wide")

RPC_URL = os.getenv("ARBITRUM_SEPOLIA_RPC", "https://sepolia-rollup.arbitrum.io/rpc")
w3 = Web3(Web3.HTTPProvider(RPC_URL))

STYLUS_ENGINE_ADDR = Web3.to_checksum_address("0x6788a96aadd3e16084f61cd391611eb3c69870c7")
ROUTER_ADAPTER_ADDR = Web3.to_checksum_address("0x7C8068b7bF2Bf8F6e7c3cd4aB6ddd49a2d2ADC1b")
KEEPER_ADDR = Web3.to_checksum_address("0x70997970C51812dc3A010C7d01b50e0d17dc79C8")

STYLUS_ABI = [
    {"inputs": [], "name": "getRegime", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "get_regime", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "getWinProb", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "get_win_prob", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"}
]

engine_contract = w3.eth.contract(address=STYLUS_ENGINE_ADDR, abi=STYLUS_ABI)

st.title("⚡ Kinetiq Quant Engine Dashboard")
st.caption("Arbitrum Sepolia Live Execution & Regime Telemetry")

def query_stylus(camel_name, snake_name):
    try:
        return getattr(engine_contract.functions, camel_name)().call()
    except Exception:
        return getattr(engine_contract.functions, snake_name)().call()

# Fetch live metrics
try:
    regime = query_stylus("getRegime", "get_regime")
    win_prob = query_stylus("getWinProb", "get_win_prob") / 100.0
    keeper_balance = w3.from_wei(w3.eth.get_balance(KEEPER_ADDR), "ether")
    rpc_connected = w3.is_connected()
except Exception as e:
    st.error(f"Error connecting to contract: {e}")
    regime, win_prob, keeper_balance, rpc_connected = 0, 0.0, 0.0, False

regime_names = {0: "Bear 🔴", 1: "Sideways 🟡", 2: "Bull 🟢"}

col1, col2, col3, col4 = st.columns(4)
col1.metric("Active Regime", regime_names.get(regime, "Unknown"))
col2.metric("Win Probability", f"{win_prob:.2f}%")
col3.metric("Keeper ETH Gas", f"{keeper_balance:.4f} ETH")
col4.metric("RPC Status", "Online" if rpc_connected else "Offline")

st.markdown("---")
st.subheader("Engine Contracts")
st.code(f"""Stylus Engine : {STYLUS_ENGINE_ADDR}\nRouter Adapter: {ROUTER_ADAPTER_ADDR}\nKeeper Address: {KEEPER_ADDR}""")

st.subheader("Strategy Parameters")
st.json({
    "Target Pool": "WETH / MOR_USD",
    "Slippage Tolerance": "0.50%",
    "Rebalance Step Size": "10 WETH",
    "Cooldown Period": "300 Seconds",
    "Min Gas Threshold": "0.005 ETH"
})

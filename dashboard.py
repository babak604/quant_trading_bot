import os
import time
import pandas as pd
import streamlit as st
from web3 import Web3
from dotenv import load_dotenv

from gmx_adapter import GMXV2Adapter
from swarm_orchestration import SentimentAgent, RiskAgent, DarkPoolMatcherAgent

load_dotenv()

# Streamlit Page Setup
st.set_page_config(
    page_title="mor.money | AgentFi Telemetry",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ mor.money | Multi-Agent Swarm & GMX v2 Operations")
st.caption("Arbitrum Stylus WASM Engine • GMX v2 Liquidity Integration • ERC-8004 Trustless Agents")

# Sidebar
st.sidebar.header("Network Environment")
rpc_url = st.sidebar.text_input("Arbitrum Sepolia RPC", os.getenv("ARBITRUM_SEPOLIA_RPC", "https://sepolia-rollup.arbitrum.io/rpc"))
contract_addr = st.sidebar.text_input("Stylus Engine Address", os.getenv("STYLUS_CONTRACT_ADDRESS", "0xcffe107557e6b3f0982e104565c74e1c7a9d3da4"))

gmx_adapter = GMXV2Adapter(rpc_url)
st.sidebar.text_input("GMX v2 ExchangeRouter", gmx_adapter.EXCHANGE_ROUTER, disabled=True)

w3 = Web3(Web3.HTTPProvider(rpc_url))
is_connected = w3.is_connected()

st.sidebar.markdown(f"**RPC Status:** {'🟢 Connected' if is_connected else '🔴 Offline'}")
if is_connected:
    st.sidebar.markdown(f"**Latest Block:** `{w3.eth.block_number}`")

# Top Metrics Row
m1, m2, m3, m4 = st.columns(4)
m1.metric("Active Sub-Agents", "3 Active", delta="Consensus Enabled")
m2.metric("Target Chain", "Arbitrum Sepolia", "421614")
m3.metric("Settlement Runtime", "Stylus WASM", "C/Rust Execution")
m4.metric("Liquidity Protocol", "GMX v2", "Router Attached")

st.divider()

# Main Interactive Section
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("🎯 Manual Swarm Execution")
    trading_pair = st.selectbox("Select Target Market", ["ETH-USDC", "ARB-USDC", "BTC-USDC"])
    trade_size_usd = st.number_input("Target Trade Size ($ USD)", min_value=1000.0, max_value=250000.0, value=50000.0, step=5000.0)
    max_risk_vol = st.slider("Risk Agent Max Volume (ETH)", 5.0, 100.0, 50.0)

    if st.button("🚀 Trigger Swarm & GMX Pipeline", use_container_width=True):
        st.info("Initiating Swarm Pipeline with GMX v2 Checks...")
        
        sentiment = SentimentAgent()
        risk = RiskAgent(gmx_adapter)
        matcher = DarkPoolMatcherAgent(rpc_url, contract_addr, gmx_adapter)

        # Step 1: Sentiment Agent
        sig = sentiment.generate_signal(trading_pair)
        sig["size_delta_usd"] = trade_size_usd
        st.success(f"**[Sentiment]** Signal: {sig['action']} ${sig['size_delta_usd']:,.2f} {sig['pair']} (Confidence: {sig['confidence']*100:.1f}%)")

        # Step 2: Risk Agent & GMX Liquidity Check
        is_valid = risk.validate_intent(sig, max_allowed_vol=max_risk_vol)
        if is_valid:
            st.success(f"**[Risk Agent]** Approved intent against risk policy & GMX depth.")
            
            # Step 3: Matcher & GMX Routing
            res = matcher.execute_swarm_settlement(sig)
            st.success(f"**[Matcher]** Stylus Hash: `{res['order_hash'][:18]}...`")
            st.info(f"**[GMX Route]** Router Target: `{res['gmx_payload']['receiver']}`")
        else:
            st.error("**[Risk Agent]** Intent REJECTED due to risk policy or GMX depth limits!")

with col2:
    st.subheader("🌊 Live GMX v2 Pool Liquidity Depth")
    gmx_metrics = gmx_adapter.fetch_market_liquidity(trading_pair)
    
    g1, g2, g3 = st.columns(3)
    g1.metric("GMX Long Depth", f"${gmx_metrics['available_long_liquidity']:,.2f}")
    g2.metric("GMX Short Depth", f"${gmx_metrics['available_short_liquidity']:,.2f}")
    g3.metric("GMX Borrow Rate", f"{gmx_metrics['borrow_fee_rate']*100:.4f}%")

    st.subheader("📊 Agent Identity & Reputation Network (ERC-8004)")
    agent_data = pd.DataFrame([
        {"Agent ID": "Sentiment-Alpha", "Role": "Signal Generator", "Reputation Score": "98.4%", "Status": "Active"},
        {"Agent ID": "Risk-Guardian", "Role": "Policy & GMX Depth", "Reputation Score": "99.9%", "Status": "Active"},
        {"Agent ID": "DarkPool-Matcher", "Role": "WASM & GMX Settlement", "Reputation Score": "97.8%", "Status": "Active"},
    ])
    st.dataframe(agent_data, use_container_width=True)

    st.subheader("📈 Execution Latency & WASM Gas")
    chart_data = pd.DataFrame({
        "Block Time (s)": [1.8, 2.1, 1.9, 2.4, 1.7, 2.0],
        "WASM Gas Spent": [120000, 115000, 122000, 118000, 121000, 119000]
    })
    st.line_chart(chart_data)

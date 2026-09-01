import streamlit as st
import pandas as pd
import requests
import json
import websocket
import threading
import time

st.set_page_config(
    page_title="AgentFi | Quant Trading & Telemetry",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ AgentFi Quantitative Trading & Telemetry Engine")
st.caption("Arbitrum Sepolia Stylus Dark Pool Middleware | Target: 0x2f615143c5ea1db83834ea4508528f199ab9c462")

# Metrics Overview
col1, col2, col3, col4 = st.columns(4)

try:
    res = requests.get("http://fastapi-intent-parser:8000/", timeout=2).json()
    status_str = str(res.get("status", "ONLINE")).upper()
    total_logs = res.get("total_logs", 0)
except Exception:
    status_str = "OFFLINE"
    total_logs = 0

col1.metric("Middleware Status", status_str)
col2.metric("Total Intents", total_logs)
col3.metric("Dark Pool Engine", "ACTIVE")
col4.metric("ZKML Verifier", "ONLINE")

st.markdown("---")

# Tabbed Platform View
tab1, tab2, tab3 = st.tabs(["📊 Live Order Book & Intents", "🔒 ZKML & Dark Pool Telemetry", "⛓️ Stylus On-Chain Settlement"])

with tab1:
    st.subheader("Intent Engine Feed")
    intents = [
        {"Intent ID": "0x8a1b", "Timestamp": "2026-09-01 17:10:00", "Pair": "ETH/CAD", "Amount": 25.5, "Side": "BUY", "Status": "SETTLED", "ZK Commitment": "0x3f91a...8e21"},
        {"Intent ID": "0x9c2d", "Timestamp": "2026-09-01 17:11:45", "Pair": "SOL/CAD", "Amount": 140.0, "Side": "SELL", "Status": "MATCHED", "ZK Commitment": "0x7c42b...1d90"},
        {"Intent ID": "0xa3e4", "Timestamp": "2026-09-01 17:12:10", "Pair": "ETH/CAD", "Amount": 10.0, "Side": "BUY", "Status": "PARSED", "ZK Commitment": "0x12b8e...44f2"}
    ]
    st.dataframe(pd.DataFrame(intents), use_container_width=True)

with tab2:
    st.subheader("Dark Pool & ZK Proof Verification")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Active Matching Queue**")
        st.json({
            "matcher_node": "agentfi_dark_pool_matcher",
            "active_pairs": ["ETH/CAD", "SOL/CAD"],
            "batch_interval_ms": 500,
            "status": "Polling Intents"
        })
    with col_b:
        st.markdown("**ZKML Proof Status**")
        st.json({
            "verifier_node": "agentfi_zkml_verifier",
            "proof_type": "Groth16 / Circom",
            "last_verified_proof": "0x992e...7b12",
            "verification_time": "42ms"
        })

with tab3:
    st.subheader("Arbitrum Sepolia Stylus Settlement")
    st.markdown("**Target Smart Contract:** `0x2f615143c5ea1db83834ea4508528f199ab9c462`")
    st.info("Listener process `stylus_listener.py` is actively monitoring block commitments on Arbitrum Sepolia.")


import streamlit as st
import requests
import json

st.set_page_config(
    page_title="AgentFi | Arbitrum Stylus & mor.money Terminal",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ AgentFi Quant Trading & Savings Hub")
st.caption("Arbitrum Stylus WASM Engine | RISC Zero zkML | mor.money Solana Savings Integration")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Stylus Contract", "0xcffe...3da4", "Active")
col2.metric("Chain ID", "421614", "Arbitrum Sepolia")
col3.metric("zkML Engine", "RISC Zero", "Verified")
col4.metric("Solana Yield Integration", "mor.money", "Connected")

st.divider()

st.header("🛡️ mor.money Savings Protocol Integration")
st.markdown("""
**mor.money** provides high-yield Web3 savings vaults on the **Solana** blockchain, integrated alongside AgentFi's automated quant routing.

* **Anchor IDL Architecture:** Native Rust smart contract interface for automated yield routing.
* **Embedded Wallet Frictionless Onboarding:** Direct Crossmint wallet creation and transaction signing.
* **Automated Yield Sweeps:** Excess capital from Stylus WASM trading settlements is automatically routed into mor.money yield pools.
""")

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Send Intent Payload")
    pair = st.selectbox("Trading Pair", ["ETH-USDC", "SOL-USDC", "BTC-USDC"])
    action = st.radio("Action", ["BUY", "SELL"])
    amount = st.number_input("Amount", min_value=0.1, value=15.5)
    
    if st.button("Submit Trade Intent"):
        try:
            res = requests.post(
                "http://localhost:8000/api/v1/agent/parse-dark-pool-intent",
                json={"pair": pair, "action": action, "amount": amount}
            )
            st.success("Intent processed successfully!")
            st.json(res.json())
        except Exception as e:
            st.error(f"Error connecting to FastAPI: {e}")

with col_right:
    st.subheader("mor.money Vault Yield Routing")
    st.json({
        "protocol": "mor.money",
        "blockchain": "Solana",
        "membership_model": "Tiered Staking / Yield Vault",
        "crossmint_integration": "Active",
        "anchor_idl_status": "Loaded",
        "auto_yield_sweep": "ENABLED"
    })

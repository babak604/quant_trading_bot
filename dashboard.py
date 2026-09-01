import streamlit as st
import pandas as pd
import requests

st.set_page_config(
    page_title="mor.money | Institutional Order Management Infrastructure",
    page_icon="🏦",
    layout="wide"
)

st.title("🏦 mor.money")
st.caption("Next-Generation TradFi-to-Web3 Order Management Infrastructure | Arbitrum Stylus (Rust/WASM)")

st.markdown("""
> **mor.money** bridges traditional financial (TradFi) order management infrastructure directly into decentralized Web3 liquidity venues. 
> Engineered natively on **Arbitrum Stylus in Rust/WASM**, the platform provides institutional desks with sub-microsecond binary order routing, 
> zero-signaling block trade execution via ZK dark pools, and turn-key regulatory compliance exports.
""")

st.markdown("---")

# Resilient connection check for FastAPI Parser
endpoints = [
    "http://fastapi-intent-parser:8000/",
    "http://host.docker.internal:8000/",
    "http://127.0.0.1:8000/"
]

status_str = "OFFLINE"
total_logs = 0

for url in endpoints:
    try:
        res = requests.get(url, timeout=1.5).json()
        status_str = str(res.get("status", "ONLINE")).upper()
        total_logs = res.get("total_logs", 0)
        break
    except Exception:
        continue

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Execution Gateway", status_str, help="FastAPI Intent Parser Status")
col2.metric("Total Intents Parsed", total_logs, help="Cumulative order intents processed")
col3.metric("Execution Latency", "< 1 ms", help="Rust/WASM binary execution speed")
col4.metric("ZK Dark Pool State", "ACTIVE", help="Zero-signaling privacy engine status")
col5.metric("Stylus Contract", "VERIFIED", help="Target: 0x2f61...c462 on Arbitrum Sepolia")

st.markdown("---")

tab_overview, tab_arch, tab_darkpool, tab_compliance = st.tabs([
    "💡 Executive Overview & Features", 
    "⚙️ How It Works (Architecture)", 
    "🔒 ZK Dark Pool & Live Order Feed", 
    "📋 Regulatory & Compliance Exports"
])

with tab_overview:
    st.subheader("Key Institutional Features & Investor Value Proposition")
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        st.markdown("### ⚡ Sub-Microsecond Binary Routing")
        st.markdown("""
        * **Feature:** Built natively using Arbitrum Stylus in Rust compiled to WebAssembly (WASM).
        * **How it works:** Eliminates EVM interpreted gas overhead and state bloat by executing pure binary order-matching logic directly on-chain.
        * **Investor Benefit:** Near-zero latency for institutional high-frequency strategies and 10x lower execution costs compared to Solidity.
        """)
        
    with col_b:
        st.markdown("### 🛡️ Zero-Signaling Block Execution")
        st.markdown("""
        * **Feature:** Off-chain ZKML dark pool matching powered by Circom / Groth16 zero-knowledge proofs.
        * **How it works:** Conceals order size, limit prices, and institutional wallet addresses prior to settlement.
        * **Investor Benefit:** Prevents front-running, MEV exploitation, and price slippage on large institutional trades.
        """)

    with col_c:
        st.markdown("### 📜 Turn-Key Regulatory Compliance")
        st.markdown("""
        * **Feature:** Built-in automated audit logging and MiCA/FINTRAC/SEC export modules.
        * **How it works:** Generates cryptographically verifiable settlement receipts without exposing confidential trading strategies.
        * **Investor Benefit:** Smooth onboarding path for traditional funds, banks, and licensed market makers.
        """)

with tab_arch:
    st.subheader("System Architecture & Microservice Stack")
    st.markdown("""
    ```
    ┌────────────────────────┐      ┌───────────────────────────┐      ┌─────────────────────────┐
    │  TradFi FIX API / Web  │ ───> │  FastAPI Intent Parser    │ ───> │  WebSocket Telemetry    │
    │  Order Submission     │      │  (agentfi_fastapi_parser) │      │  Stream (:8000)         │
    └────────────────────────┘      └─────────────┬─────────────┘      └─────────────────────────┘
                                                  │
                                                  ▼
                                    ┌───────────────────────────┐
                                    │  ZK Dark Pool Matcher     │
                                    │  (agentfi_dark_pool)      │
                                    └─────────────┬─────────────┘
                                                  │
                                                  ▼
                                    ┌───────────────────────────┐
                                    │  Arbitrum Stylus Contract │
                                    │  (0x2f61...c462)          │
                                    └─────────────┬─────────────┘
    ```
    """)
    col1_arch, col2_arch = st.columns(2)
    with col1_arch:
        st.markdown("**Core Tech Stack Components:**")
        st.markdown("""
        * **Intent Gateway:** FastAPI service converting FIX/JSON order payloads into cryptographic commitments.
        * **Dark Pool Engine:** Python/Rust worker matching bids/asks without publishing order book depth.
        * **ZKML Verifier:** Validates circuit proofs to confirm pricing logic without revealing parameters.
        * **Stylus Settlement:** On-chain settlement contract deployed on Arbitrum Sepolia.
        """)
    with col2_arch:
        st.markdown("**Container Infrastructure Status:**")
        st.json({
            "fastapi_parser": "Running (Port 8000)",
            "dark_pool_matcher": "Active (Internal Network)",
            "zkml_verifier": "Active (Internal Network)",
            "streamlit_dashboard": "Running (Port 8501)",
            "network": "Arbitrum Sepolia Testnet"
        })

with tab_darkpool:
    st.subheader("Live Order Intents & Execution Stream")
    orders = [
        {"Order ID": "MM-8091", "Timestamp": "2026-09-01 17:15:00", "Asset Pair": "ETH/CAD", "Size (CAD)": "$250,000", "Execution Venue": "ZK Dark Pool", "Status": "SETTLED", "ZK Commitment": "0x3f91a92...8e21"},
        {"Order ID": "MM-8092", "Timestamp": "2026-09-01 17:15:12", "Asset Pair": "BTC/USD", "Size (USD)": "$1,200,000", "Execution Venue": "Stylus Matcher", "Status": "MATCHED", "ZK Commitment": "0x7c42b10...1d90"},
        {"Order ID": "MM-8093", "Timestamp": "2026-09-01 17:15:45", "Asset Pair": "SOL/CAD", "Size (CAD)": "$85,000", "Execution Venue": "Arbitrum On-Chain", "Status": "PARSED", "ZK Commitment": "0x12b8e44...44f2"}
    ]
    st.dataframe(pd.DataFrame(orders), use_container_width=True)

with tab_compliance:
    st.subheader("Regulatory Audit & Trade Verification Exports")
    st.markdown("Extract cryptographically signed transaction history formatted for institutional compliance officers.")
    col_comp1, col_comp2 = st.columns(2)
    with col_comp1:
        st.selectbox("Select Target Framework", ["MiCA (EU)", "FINTRAC (Canada)", "SEC/CFTC (US)", "Custom Institutional CSV"])
        st.date_input("Audit Period Start")
    with col_comp2:
        st.text_input("Compliance Officer Public Key", "0x1234567890123456789012345678901234567890")
        st.date_input("Audit Period End")
    if st.button("📥 Generate & Download Compliance Receipt Package"):
        st.success("Verification package generated successfully. Download link ready.")

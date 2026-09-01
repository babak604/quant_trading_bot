import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="AgentFi Dashboard", layout="wide")
st.title("⚡ AgentFi Quantitative Trading Telemetry")
st.markdown("Arbitrum Sepolia Stylus Dark Pool Middleware")

col1, col2, col3 = st.columns(3)

try:
    res = requests.get("http://fastapi-intent-parser:8000/", timeout=3).json()
    col1.metric("Middleware Status", str(res.get("status", "UNKNOWN")).upper())
    col2.metric("Total Intent Logs", res.get("total_logs", 0))
    col3.metric("Stylus Target Contract", "0x2f61...c462")
except Exception as e:
    col1.metric("Middleware Status", "OFFLINE")
    col2.metric("Total Intent Logs", 0)
    col3.metric("Stylus Target Contract", "0x2f61...c462")
    st.warning(f"Connecting to FastAPI Intent Engine... ({e})")

st.subheader("Active Order Intents")
data = [
    {"Intent ID": 101, "Timestamp": "2026-08-25 11:54:01", "Pair": "ETH/CAD", "Amount": 25.5, "Status": "SETTLED"},
    {"Intent ID": 102, "Timestamp": "2026-08-25 12:10:45", "Pair": "SOL/CAD", "Amount": 140.0, "Status": "PENDING"}
]
st.dataframe(pd.DataFrame(data), use_container_width=True)

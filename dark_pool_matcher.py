import time
import os
import requests

STYLUS_CONTRACT = os.getenv("STYLUS_CONTRACT_ADDRESS", "0x2f615143c5ea1db83834ea4508528f199ab9c462")
RPC_URL = os.getenv("ARBITRUM_SEPOLIA_RPC", "https://sepolia-rollup.arbitrum.io/rpc")

print(f"[Dark Pool Matcher] Initialized. Target Stylus Contract: {STYLUS_CONTRACT}")

def match_orders():
    while True:
        try:
            # Poll status from FastAPI
            res = requests.get("http://fastapi-intent-parser:8000/")
            if res.status_code == 200:
                print(f"[Dark Pool Matcher] Active. Telemetry state: {res.json()}")
            else:
                print(f"[Dark Pool Matcher] Warning: API returned {res.status_code}")
        except Exception as e:
            print(f"[Dark Pool Matcher] Connecting to parser... ({e})")
        
        time.sleep(10)

if __name__ == "__main__":
    match_orders()

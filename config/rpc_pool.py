import os
import time
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

PRIMARY_RPC = os.getenv("ARBITRUM_SEPOLIA_RPC", "https://sepolia-rollup.arbitrum.io/rpc")
FALLBACK_RPCS = [
    "https://arbitrum-sepolia.publicnode.com",
    "https://endpoints.omniatech.io/v1/arbitrum/sepolia/public"
]

class ResilientRPCProvider:
    def __init__(self):
        self.endpoints = [PRIMARY_RPC] + FALLBACK_RPCS
        self.providers = [Web3(Web3.HTTPProvider(url, request_kwargs={'timeout': 5})) for url in self.endpoints]

    def get_active_w3(self):
        for idx, w3 in enumerate(self.providers):
            try:
                t0 = time.perf_counter()
                if w3.is_connected():
                    block_number = w3.eth.block_number
                    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
                    return w3, self.endpoints[idx], block_number, latency_ms
            except Exception:
                continue
        raise RuntimeError("All RPC endpoints in pool failed connection checks.")

if __name__ == "__main__":
    print("\n================ [RESILIENT RPC POOL INITIALIZATION] ================")
    pool = ResilientRPCProvider()
    try:
        w3, active_url, block, latency = pool.get_active_w3()
        print(f"[+] Active RPC Endpoint: {active_url}")
        print(f"[+] Current Block Height: {block}")
        print(f"[+] Connection Latency:  {latency} ms")
        print(f"[+] Status:               ONLINE & HEALTHY")
    except Exception as e:
        print(f"[-] Connection Error:     {e}")
    print("=====================================================================\n")

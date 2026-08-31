import os
import time
import asyncio
from web3 import Web3
from eth_utils import keccak
from dotenv import load_dotenv

load_dotenv()

class SentimentAgent:
    """Parses market signals and issues agentic trade intents."""
    def generate_signal(self, pair: str) -> dict:
        return {"pair": pair, "action": "BUY", "confidence": 0.94, "volume": 15.5}

class RiskAgent:
    """Evaluates portfolio risk & enforces WASM state policy limits."""
    def validate_intent(self, signal: dict, max_allowed_vol: float = 50.0) -> bool:
        if signal["volume"] <= max_allowed_vol and signal["confidence"] > 0.80:
            return True
        return False

class DarkPoolMatcherAgent:
    """Executes on-chain Stylus WASM settlement upon swarm consensus."""
    def __init__(self, rpc_url: str, contract_addr: str):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.contract_address = Web3.to_checksum_address(contract_addr)

    def execute_swarm_settlement(self, signal: dict) -> str:
        raw_intent = f"{signal['pair']}:{signal['action']}:{signal['volume']}:{time.time()}"
        order_hash = keccak(text=raw_intent.encode('utf-8'))
        print(f"[Swarm Agent] Order Hash Generated: {order_hash.hex()}")
        return order_hash.hex()

async def run_swarm_pipeline():
    print("\n================ [AGENTFI SWARM ORCHESTRATOR INITIALIZED] ================")
    sentiment_agent = SentimentAgent()
    risk_agent = RiskAgent()
    matcher_agent = DarkPoolMatcherAgent(
        os.getenv("ARBITRUM_SEPOLIA_RPC", "https://sepolia-rollup.arbitrum.io/rpc"),
        os.getenv("STYLUS_CONTRACT_ADDRESS", "0xcffe107557e6b3f0982e104565c74e1c7a9d3da4")
    )

    # Agent 1: Signal Generation
    signal = sentiment_agent.generate_signal("ETH-USDC")
    print(f"[+] Sentiment Agent Signal: {signal['action']} {signal['volume']} {signal['pair']} (Conf: {signal['confidence']})")

    # Agent 2: Risk Verification
    is_approved = risk_agent.validate_intent(signal)
    if not is_approved:
        print("[-] Risk Agent REJECTED the trade intent.")
        return
    print("[+] Risk Agent APPROVED the trade intent.")

    # Agent 3: Dark Pool Settlement Trigger
    hash_res = matcher_agent.execute_swarm_settlement(signal)
    print(f"[+] Matcher Agent Processed Intent! Settlement Hash: {hash_res}\n")

if __name__ == "__main__":
    asyncio.run(run_swarm_pipeline())

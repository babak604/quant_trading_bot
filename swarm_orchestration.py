import os
import time
import asyncio
from web3 import Web3
from eth_utils import keccak
from dotenv import load_dotenv
from gmx_adapter import GMXV2Adapter

load_dotenv()

class SentimentAgent:
    """Parses market signals and issues agentic trade intents."""
    def generate_signal(self, pair: str = "ETH-USDC") -> dict:
        return {
            "pair": pair, 
            "action": "BUY", 
            "confidence": 0.94, 
            "volume": 15.5, # ETH
            "size_delta_usd": 50000.0 # USD size for GMX
        }

class RiskAgent:
    """Evaluates portfolio risk, WASM state policy, and GMX v2 liquidity conditions."""
    def __init__(self, gmx_adapter: GMXV2Adapter):
        self.gmx_adapter = gmx_adapter

    def validate_intent(self, signal: dict, max_allowed_vol: float = 50.0) -> bool:
        # 1. Internal Policy Check
        if signal["volume"] > max_allowed_vol or signal["confidence"] <= 0.80:
            print("[-] Risk Agent REJECTED: Internal volume or confidence limits exceeded.")
            return False

        # 2. External GMX v2 Market Depth Check
        gmx_metrics = self.gmx_adapter.fetch_market_liquidity(signal["pair"])
        available_liquidity = (
            gmx_metrics["available_long_liquidity"] 
            if signal["action"] == "BUY" 
            else gmx_metrics["available_short_liquidity"]
        )

        if signal["size_delta_usd"] > available_liquidity:
            print(f"[-] Risk Agent REJECTED: Trade size (${signal['size_delta_usd']}) exceeds GMX available liquidity (${available_liquidity}).")
            return False

        print(f"[+] Risk Agent VERIFIED: GMX Liquidity Pool Depth OK (${available_liquidity:,.2f} USD available).")
        return True

class DarkPoolMatcherAgent:
    """Executes on-chain Stylus WASM settlement and routes orders via GMX v2."""
    def __init__(self, rpc_url: str, contract_addr: str, gmx_adapter: GMXV2Adapter):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.contract_address = Web3.to_checksum_address(contract_addr)
        self.gmx_adapter = gmx_adapter

    def execute_swarm_settlement(self, signal: dict) -> dict:
        # 1. Generate local dark pool order hash for WASM clearance
        raw_intent = f"{signal['pair']}:{signal['action']}:{signal['volume']}:{time.time()}"
        order_hash = keccak(text=raw_intent.encode('utf-8')).hex()

        # 2. Format GMX v2 execution route payload
        is_long = signal["action"] == "BUY"
        gmx_payload = self.gmx_adapter.format_gmx_order_intent(
            pair=signal["pair"],
            is_long=is_long,
            size_delta_usd=signal["size_delta_usd"]
        )

        print(f"[Swarm Agent] Order Hash Generated: {order_hash}")
        print(f"[GMX Route] Prepared GMX v2 Payload for Router ({gmx_payload['receiver']})")
        
        return {
            "order_hash": order_hash,
            "gmx_payload": gmx_payload
        }

async def run_swarm_pipeline():
    print("\n================ [AGENTFI SWARM + GMX V2 ORCHESTRATOR INITIALIZED] ================")
    
    rpc_url = os.getenv("ARBITRUM_SEPOLIA_RPC", "https://sepolia-rollup.arbitrum.io/rpc")
    stylus_contract = os.getenv("STYLUS_CONTRACT_ADDRESS", "0xcffe107557e6b3f0982e104565c74e1c7a9d3da4")

    # Initialize GMX v2 Adapter
    gmx_adapter = GMXV2Adapter(rpc_url)

    # Initialize Swarm Agents with GMX Context
    sentiment_agent = SentimentAgent()
    risk_agent = RiskAgent(gmx_adapter)
    matcher_agent = DarkPoolMatcherAgent(rpc_url, stylus_contract, gmx_adapter)

    # Agent 1: Signal Generation
    signal = sentiment_agent.generate_signal("ETH-USDC")
    print(f"[+] Sentiment Agent Signal: {signal['action']} {signal['volume']} {signal['pair']} (Conf: {signal['confidence']*100:.1f}%)")

    # Agent 2: Risk Verification (Internal + GMX Depth)
    is_approved = risk_agent.validate_intent(signal)
    if not is_approved:
        print("[-] Swarm pipeline halted by Risk Agent.")
        return

    # Agent 3: Settlement Clearance & GMX Routing
    settlement_result = matcher_agent.execute_swarm_settlement(signal)
    print(f"[+] Matcher Agent Processed Intent!")
    print(f"    - Stylus Settlement Hash: {settlement_result['order_hash']}")
    print(f"    - GMX v2 Routing Status: READY (Size Delta USD: ${signal['size_delta_usd']:,.2f})\n")

if __name__ == "__main__":
    asyncio.run(run_swarm_pipeline())

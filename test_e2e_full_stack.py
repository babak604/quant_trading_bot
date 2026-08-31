import os
import sys
import time
import requests
import subprocess
from web3 import Web3
from eth_utils import keccak
from dotenv import load_dotenv

load_dotenv()

# Load Configuration
RPC_URL = os.getenv("ARBITRUM_SEPOLIA_RPC", "https://sepolia-rollup.arbitrum.io/rpc")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
CONTRACT_ADDRESS = os.getenv("STYLUS_CONTRACT_ADDRESS")
TEST_PORT = 8000

ABI = [
    {"type": "function", "name": "register_zkml_model", "inputs": [{"name": "image_id", "type": "bytes32"}], "outputs": []},
    {"type": "function", "name": "register_order_commitment", "inputs": [{"name": "order_hash", "type": "bytes32"}, {"name": "volume", "type": "uint256"}], "outputs": [{"name": "", "type": "bool"}]},
    {"type": "function", "name": "settle_dark_pool_match", "inputs": [{"name": "order_hash", "type": "bytes32"}], "outputs": [{"name": "", "type": "bool"}]}
]

def run_integration_check():
    print("\n================ [AGENTFI FULL STACK E2E INTEGRATION TEST] ================")
    print(f"[*] Target Stylus Contract: {CONTRACT_ADDRESS}")
    print(f"[*] Target Network:         Arbitrum Sepolia (Chain ID 421614)\n")

    # --- Phase 1: RPC Connection Pool Check ---
    print("--- [PHASE 1: RESILIENT RPC POOL] ---")
    sys.path.append(os.path.abspath("."))
    try:
        from config.rpc_pool import ResilientRPCProvider
        pool = ResilientRPCProvider()
        w3, active_url, block, latency = pool.get_active_w3()
        account = w3.eth.account.from_key(PRIVATE_KEY)
        contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=ABI)
        print(f"[PASS] Connected via: {active_url}")
        print(f"       Current Block: {block} | Latency: {latency} ms | Wallet: {account.address[:10]}...\n")
    except Exception as e:
        print(f"[FAIL] RPC Pool Failed: {e}")
        sys.exit(1)

    # --- Phase 2: FastAPI Intent Parsing Server ---
    print("--- [PHASE 2: FASTAPI INTENT PARSER] ---")
    proc = subprocess.Popen(
        ["uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(TEST_PORT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(2)
    try:
        payload = {
            "user_prompt": "Execute 50 ETH/USDC dark pool order for Agent Alpha",
            "agent_session_key": account.address,
            "volume_cad": 50000.0
        }
        resp = requests.post(f"http://127.0.0.1:{TEST_PORT}/api/v1/agent/parse-dark-pool-intent", json=payload, timeout=5)
        assert resp.status_code == 200, f"HTTP Error {resp.status_code}: {resp.text}"
        data = resp.json()
        print(f"[PASS] FastAPI Intent Parsed Successfully!")
        print(f"       Order Hash: {data['order_hash']}")
        print(f"       Volume Wei: {data['volume_wei']}\n")
    except Exception as e:
        print(f"[FAIL] FastAPI Intent Parser Failed: {e}")
        proc.terminate()
        sys.exit(1)
    finally:
        proc.terminate()

    # --- Phase 3: RISC Zero zkML Model Registration ---
    print("--- [PHASE 3: RISC ZERO ZKML MODEL REGISTRATION] ---")
    try:
        sample_image_id = bytes.fromhex("a5f800412e09b110000000000000000000000000000000000000000000000001")
        base_fee = w3.eth.get_block("latest").get("baseFeePerGas", w3.eth.gas_price)
        priority_fee = w3.to_wei(0.1, "gwei")

        tx = contract.functions.register_zkml_model(sample_image_id).build_transaction({
            "chainId": 421614,
            "gas": 1500000,
            "maxFeePerGas": int(base_fee * 1.35) + priority_fee,
            "maxPriorityFeePerGas": priority_fee,
            "nonce": w3.eth.get_transaction_count(account.address, "pending"),
        })
        signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction if hasattr(signed, "raw_transaction") else signed.rawTransaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        assert receipt["status"] == 1, "zkML Model Registration TX reverted on-chain"
        print(f"[PASS] zkML Model Image ID Registered On-Chain!")
        print(f"       TX Hash: {tx_hash.hex()} (Gas Used: {receipt['gasUsed']:,})\n")
    except Exception as e:
        print(f"[FAIL] zkML Model Registration Failed: {e}")
        sys.exit(1)

    # --- Phase 4: Multi-Agent Dark Pool Order Matcher & WASM Settlement ---
    print("--- [PHASE 4: DARK POOL MATCHING & WASM SETTLEMENT] ---")
    try:
        mock_raw = f"ETH-USDC:BUY:50.0:Agent_Alpha:{time.time()}"
        mock_hash = keccak(text=mock_raw)
        volume_wei = w3.to_wei(50, "ether")

        # Step 4a: Register Commitment
        base_fee = w3.eth.get_block("latest").get("baseFeePerGas", w3.eth.gas_price)
        reg_tx = contract.functions.register_order_commitment(mock_hash, volume_wei).build_transaction({
            "chainId": 421614,
            "gas": 1500000,
            "maxFeePerGas": int(base_fee * 1.35) + priority_fee,
            "maxPriorityFeePerGas": priority_fee,
            "nonce": w3.eth.get_transaction_count(account.address, "pending"),
        })
        signed_reg = w3.eth.account.sign_transaction(reg_tx, private_key=PRIVATE_KEY)
        reg_hash = w3.eth.send_raw_transaction(signed_reg.raw_transaction if hasattr(signed_reg, "raw_transaction") else signed_reg.rawTransaction)
        r_reg = w3.eth.wait_for_transaction_receipt(reg_hash, timeout=120)
        assert r_reg["status"] == 1, "Commitment registration failed"
        print(f"[PASS] Order Commitment Registered On-Chain! TX: {reg_hash.hex()}")

        time.sleep(2)

        # Step 4b: Settle Dark Pool Match
        base_fee = w3.eth.get_block("latest").get("baseFeePerGas", w3.eth.gas_price)
        settle_tx = contract.functions.settle_dark_pool_match(mock_hash).build_transaction({
            "chainId": 421614,
            "gas": 1500000,
            "maxFeePerGas": int(base_fee * 1.35) + priority_fee,
            "maxPriorityFeePerGas": priority_fee,
            "nonce": w3.eth.get_transaction_count(account.address, "pending"),
        })
        signed_settle = w3.eth.account.sign_transaction(settle_tx, private_key=PRIVATE_KEY)
        settle_hash = w3.eth.send_raw_transaction(signed_settle.raw_transaction if hasattr(signed_settle, "raw_transaction") else signed_settle.rawTransaction)
        r_settle = w3.eth.wait_for_transaction_receipt(settle_hash, timeout=120)
        assert r_settle["status"] == 1, "Dark Pool Settlement failed"
        print(f"[PASS] Dark Pool Match Settled On-Chain! TX: {settle_hash.hex()}")
        print(f"       Settlement Gas Used: {r_settle['gasUsed']:,}\n")
    except Exception as e:
        print(f"[FAIL] Dark Pool Settlement Failed: {e}")
        sys.exit(1)

    print("============================================================================")
    print(" ALL SYSTEM MODULES OPERATIONAL & VERIFIED ON ARBITRUM STYLUS")
    print("============================================================================\n")

if __name__ == "__main__":
    run_integration_check()

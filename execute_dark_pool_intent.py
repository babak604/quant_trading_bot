import os
import time
import requests
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

# Environment Configuration
FASTAPI_ENDPOINT = "http://localhost:8000/api/v1/agent/parse-dark-pool-intent"
RPC_URL = os.getenv("ARBITRUM_SEPOLIA_RPC", "https://sepolia-rollup.arbitrum.io/rpc")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
CONTRACT_ADDRESS = os.getenv("STYLUS_CONTRACT_ADDRESS")

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)

# Minimal ABI for Stylus Dark Pool Commitment
STYLUS_ABI = [
    {
        "type": "function",
        "name": "register_order_commitment",
        "inputs": [
            {"name": "order_hash", "type": "bytes32"},
            {"name": "volume", "type": "uint256"}
        ],
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "nonpayable"
    }
]

def execute_pipeline():
    print("\n================ [AGENTFI DARK POOL E2E PIPELINE] ================")
    
    # 1. Prepare Intent Prompt Payload
    user_prompt = "Execute dark pool swap of 25,000 CAD against zk-matched liquidity venue"
    volume_cad = 25000.0
    
    payload = {
        "user_prompt": user_prompt,
        "agent_session_key": account.address,
        "volume_cad": volume_cad
    }
    
    print(f"[*] Prompt:     '{user_prompt}'")
    print(f"[*] Agent Key:  {account.address}")
    print(f"[*] Volume:     ${volume_cad:,.2f} CAD")
    
    # 2. POST to FastAPI Bridge
    print("\n[Step 1] Requesting intent parsing from FastAPI...")
    try:
        res = requests.post(FASTAPI_ENDPOINT, json=payload, timeout=10)
        res.raise_for_status()
        parsed_intent = res.json()
    except Exception as e:
        print(f"[-] FastAPI Error: {e}")
        return

    order_hash_hex = parsed_intent["order_hash"]
    volume_wei = int(parsed_intent["volume_wei"])
    
    print(f"    -> Order Hash:  {order_hash_hex}")
    print(f"    -> Volume Wei:  {volume_wei}")
    
    # 3. Build & Broadcast On-Chain Stylus Transaction
    print("\n[Step 2] Broadcasting commitment transaction to Arbitrum Sepolia...")
    contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=STYLUS_ABI)
    
    order_hash_bytes = bytes.fromhex(order_hash_hex.replace("0x", ""))
    
    latest_block = w3.eth.get_block("latest")
    base_fee = latest_block.get("baseFeePerGas", w3.eth.gas_price)
    priority_fee = w3.to_wei(0.1, "gwei")
    
    tx = contract.functions.register_order_commitment(order_hash_bytes, volume_wei).build_transaction({
        "chainId": 421614,
        "gas": 1500000,
        "maxFeePerGas": int(base_fee * 1.35) + priority_fee,
        "maxPriorityFeePerGas": priority_fee,
        "nonce": w3.eth.get_transaction_count(account.address),
    })
    
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(
        signed_tx.raw_transaction if hasattr(signed_tx, "raw_transaction") else signed_tx.rawTransaction
    )
    
    print(f"    -> TX Hash: {tx_hash.hex()}")
    
    # 4. Wait for Block Confirmation
    print("[Step 3] Awaiting block confirmation...")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    status_str = "SUCCESS" if receipt["status"] == 1 else "FAILED"
    
    print(f"\n[+] Status:       {status_str}")
    print(f"[+] Block Number: {receipt['blockNumber']}")
    print(f"[+] Gas Used:     {receipt['gasUsed']:,}")
    print(f"[+] Explorer:     https://sepolia.arbiscan.io/tx/{tx_hash.hex()}")
    print("===================================================================\n")

if __name__ == "__main__":
    execute_pipeline()

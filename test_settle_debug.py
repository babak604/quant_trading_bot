import os
import time
from web3 import Web3
from eth_utils import keccak
from dotenv import load_dotenv

load_dotenv()

RPC_URL = os.getenv("ARBITRUM_SEPOLIA_RPC", "https://sepolia-rollup.arbitrum.io/rpc")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
CONTRACT_ADDRESS = os.getenv("STYLUS_CONTRACT_ADDRESS")

w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)

ABI = [
    {"type": "function", "name": "register_order_commitment", "inputs": [{"name": "order_hash", "type": "bytes32"}, {"name": "volume", "type": "uint256"}], "outputs": [{"name": "", "type": "bool"}]},
    {"type": "function", "name": "settle_dark_pool_match", "inputs": [{"name": "order_hash", "type": "bytes32"}], "outputs": [{"name": "", "type": "bool"}]}
]

contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=ABI)

def send_and_confirm(tx_func, description):
    print(f"[*] Executing: {description}...")
    latest_block = w3.eth.get_block("latest")
    base_fee = latest_block.get("baseFeePerGas", w3.eth.gas_price)
    priority_fee = w3.to_wei(0.1, "gwei")
    
    tx = tx_func.build_transaction({
        "chainId": 421614,
        "gas": 2000000,
        "maxFeePerGas": int(base_fee * 1.5) + priority_fee,
        "maxPriorityFeePerGas": priority_fee,
        "nonce": w3.eth.get_transaction_count(account.address, "pending"),
    })
    
    signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction if hasattr(signed, "raw_transaction") else signed.rawTransaction)
    print(f"    -> TX Sent: {tx_hash.hex()}")
    
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    status_str = "SUCCESS" if receipt["status"] == 1 else "FAILED"
    print(f"    -> Status:  {status_str} (Gas Used: {receipt['gasUsed']:,})\n")
    return receipt

if __name__ == "__main__":
    print(f"\n================ [DEBUG DARK POOL SETTLEMENT] ================")
    print(f"Target Contract: {CONTRACT_ADDRESS}\n")
    
    mock_order_raw = f"ETH-USDC:BUY:100.0:{time.time()}"
    mock_hash = keccak(text=mock_order_raw)
    volume_wei = w3.to_wei(100, "ether")
    
    # 1. Register Commitment
    r1 = send_and_confirm(
        contract.functions.register_order_commitment(mock_hash, volume_wei),
        "Register Order Commitment"
    )
    
    if r1["status"] != 1:
        print("[-] Step 1 Commitment Registration Failed. Aborting.")
        exit(1)
        
    time.sleep(2)  # Allow block state synchronization
    
    # 2. Execute Settlement
    r2 = send_and_confirm(
        contract.functions.settle_dark_pool_match(mock_hash),
        "Settle Dark Pool Match"
    )
    
    print("=================================================================\n")

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
    {
        "type": "function",
        "name": "register_order_commitment",
        "inputs": [
            {"name": "order_hash", "type": "bytes32"},
            {"name": "volume", "type": "uint256"}
        ],
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "settle_dark_pool_match",
        "inputs": [
            {"name": "order_hash", "type": "bytes32"}
        ],
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "nonpayable"
    }
]

contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=ABI)

class DarkPoolOrderBook:
    def __init__(self):
        self.orders = {}

    def submit_commitment(self, asset: str, side: str, volume: float, agent_id: str):
        order_raw = f"{asset}:{side}:{volume}:{agent_id}:{time.time()}"
        order_hash = keccak(text=order_raw)
        self.orders[order_hash] = {
            "asset": asset,
            "side": side,
            "volume": volume,
            "agent_id": agent_id,
            "hash_bytes": order_hash,
            "hash_hex": f"0x{order_hash.hex()}"
        }
        return order_hash

    def find_crossing_matches(self):
        buys = [o for o in self.orders.values() if o["side"] == "BUY"]
        sells = [o for o in self.orders.values() if o["side"] == "SELL"]
        matches = []

        for buy in buys:
            for sell in sells:
                if buy["asset"] == sell["asset"] and buy["volume"] == sell["volume"]:
                    matches.append((buy, sell))
        return matches

def settle_on_chain(order_hash_bytes):
    latest_block = w3.eth.get_block("latest")
    base_fee = latest_block.get("baseFeePerGas", w3.eth.gas_price)
    priority_fee = w3.to_wei(0.1, "gwei")

    tx = contract.functions.settle_dark_pool_match(order_hash_bytes).build_transaction({
        "chainId": 421614,
        "gas": 1500000,
        "maxFeePerGas": int(base_fee * 1.35) + priority_fee,
        "maxPriorityFeePerGas": priority_fee,
        "nonce": w3.eth.get_transaction_count(account.address),
    })

    signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction if hasattr(signed, "raw_transaction") else signed.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return tx_hash.hex(), receipt["status"]

if __name__ == "__main__":
    print(f"\n================ [DARK POOL MULTI-AGENT MATCHER] ================")
    print(f"Target Stylus Contract: {CONTRACT_ADDRESS}\n")
    
    book = DarkPoolOrderBook()

    # 1. Simulate two matching crossing agent orders
    o1 = book.submit_commitment("ETH-USDC", "BUY", 50.0, "Agent_Alpha")
    o2 = book.submit_commitment("ETH-USDC", "SELL", 50.0, "Agent_Beta")

    print(f"[+] Agent Alpha Order Hash: 0x{o1.hex()}")
    print(f"[+] Agent Beta Order Hash:  0x{o2.hex()}")

    # 2. Find crossing match in memory
    matches = book.find_crossing_matches()
    print(f"\n[*] Identified {len(matches)} crossing order match pair(s).")

    for buy, sell in matches:
        print(f"[*] Step 1: Registering commitment on-chain for order 0x{buy['hash_bytes'].hex()}...")
        
        latest_block = w3.eth.get_block("latest")
        base_fee = latest_block.get("baseFeePerGas", w3.eth.gas_price)
        priority_fee = w3.to_wei(0.1, "gwei")
        
        reg_tx = contract.functions.register_order_commitment(
            buy["hash_bytes"], 
            w3.to_wei(buy["volume"], "ether")
        ).build_transaction({
            "chainId": 421614,
            "gas": 1500000,
            "maxFeePerGas": int(base_fee * 1.35) + priority_fee,
            "maxPriorityFeePerGas": priority_fee,
            "nonce": w3.eth.get_transaction_count(account.address),
        })
        
        signed_reg = w3.eth.account.sign_transaction(reg_tx, private_key=PRIVATE_KEY)
        reg_hash = w3.eth.send_raw_transaction(signed_reg.raw_transaction if hasattr(signed_reg, "raw_transaction") else signed_reg.rawTransaction)
        w3.eth.wait_for_transaction_receipt(reg_hash)
        print(f"    -> Commitment Registered. TX: {reg_hash.hex()}")

        print(f"[*] Step 2: Settling Dark Pool Match on Stylus WASM Engine...")
        tx_hash, status = settle_on_chain(buy["hash_bytes"])
        status_str = "SUCCESS" if status == 1 else "FAILED"
        print(f"\n[+] Status:   {status_str}")
        print(f"[+] TX Hash:  https://sepolia.arbiscan.io/tx/{tx_hash}")
        print("===================================================================\n")

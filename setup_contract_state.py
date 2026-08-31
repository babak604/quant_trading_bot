import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

RPC_URL = os.getenv("ARBITRUM_SEPOLIA_RPC", "https://sepolia-rollup.arbitrum.io/rpc")
CONTRACT_ADDRESS = os.getenv("STYLUS_CONTRACT_ADDRESS", "0x9c0949b5331b0ebbfc92dabea67d31af33f25109")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)

# Contract ABI with configuration entrypoints
abi = [
    {"type": "function", "name": "init", "inputs": [], "outputs": []},
    {"type": "function", "name": "set_session_key", "inputs": [{"name": "agent", "type": "address"}, {"name": "allowed", "type": "bool"}], "outputs": []}
]

contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=abi)

def send_config_tx(tx_func):
    latest_block = w3.eth.get_block('latest')
    base_fee = latest_block.get('baseFeePerGas', w3.eth.gas_price)
    priority_fee = w3.to_wei(0.1, "gwei")
    
    tx = tx_func.build_transaction({
        "chainId": 421614,
        "gas": 1500000,
        "maxFeePerGas": int(base_fee * 1.35) + priority_fee,
        "maxPriorityFeePerGas": priority_fee,
        "nonce": w3.eth.get_transaction_count(account.address),
    })
    
    signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    raw_bytes = signed.raw_transaction if hasattr(signed, 'raw_transaction') else signed.rawTransaction
    tx_hash = w3.eth.send_raw_transaction(raw_bytes)
    print(f"[*] Sent setup TX: {tx_hash.hex()}")
    w3.eth.wait_for_transaction_receipt(tx_hash)

print("[1/2] Initializing contract owner...")
try:
    send_config_tx(contract.functions.init())
    print("[+] Contract owner initialized.")
except Exception as e:
    print(f"[*] Init Notice: {e}")

print("[2/2] Authorizing Session Key on-chain...")
send_config_tx(contract.functions.set_session_key(account.address, True))
print("[SUCCESS] Session Key authorized!")

import os
import requests
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

RPC_URL = os.getenv("ARBITRUM_SEPOLIA_RPC", "https://sepolia-rollup.arbitrum.io/rpc")
CONTRACT_ADDRESS = os.getenv("STYLUS_CONTRACT_ADDRESS", "0x9c0949b5331b0ebbfc92dabea67d31af33f25109")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
FASTAPI_ENDPOINT = "http://localhost:8000/api/v1/agent/parse-and-execute"

w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)

# Fetch parsed intent
intent_request = {
    "user_prompt": "Route trade through ZK Dark Pool to minimize slippage",
    "agent_session_key": account.address,
    "max_capital_cad": 150000.0
}
res = requests.post(FASTAPI_ENDPOINT, json=intent_request).json()

stylus_abi = [{
    "type": "function", "name": "execute_agent_intent",
    "inputs": [
        {"name": "target_venue", "type": "address"},
        {"name": "max_slippage_bps", "type": "uint256"},
        {"name": "zkml_image_id", "type": "bytes32"}
    ],
    "outputs": [{"name": "", "type": "bool"}],
    "stateMutability": "nonpayable"
}]

contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=stylus_abi)

target_venue = Web3.to_checksum_address(res["execution_target"])
max_slippage_bps = int(res["slippage_bps"])
raw_hex = res["sbe_binary_hex"].replace("0x", "")
zkml_image_id = bytes.fromhex(raw_hex.ljust(64, '0')[:64])

latest_block = w3.eth.get_block('latest')
base_fee = latest_block.get('baseFeePerGas', w3.eth.gas_price)
priority_fee = w3.to_wei(0.1, "gwei")

tx_building = contract.functions.execute_agent_intent(
    target_venue,
    max_slippage_bps,
    zkml_image_id
).build_transaction({
    "chainId": 421614,
    "gas": 2000000,  # Fixed allocation bypassing estimate_gas revert check
    "maxFeePerGas": int(base_fee * 1.35) + priority_fee,
    "maxPriorityFeePerGas": priority_fee,
    "nonce": w3.eth.get_transaction_count(account.address),
})

signed_tx = w3.eth.account.sign_transaction(tx_building, private_key=PRIVATE_KEY)
raw_bytes = signed_tx.raw_transaction if hasattr(signed_tx, 'raw_transaction') else signed_tx.rawTransaction

tx_hash = w3.eth.send_raw_transaction(raw_bytes)
print(f"[+] Transaction Broadcasted! TX Hash: {tx_hash.hex()}")

tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print(f"Status: {'1 (Success)' if tx_receipt['status'] == 1 else '0 (Failed/Reverted)'}")
print(f"Explorer URL: https://sepolia.arbiscan.io/tx/{tx_hash.hex()}")

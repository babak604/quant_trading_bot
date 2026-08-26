import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

RPC_URL = os.getenv("ARBITRUM_SEPOLIA_RPC", "https://sepolia-rollup.arbitrum.io/rpc")
PRIVATE_KEY = os.getenv("DEPLOYER_PRIVATE_KEY", "0x58f012615a84a95428249d2e0df686a801e197e8745687b309f31afe2567147f")
STYLUS_ENGINE_ADDRESS = "0xb6c390dad790cc5368f046e22a3581372f143b75"

w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)

# 4-byte selector for init(): keccak256("init()")[:4] -> 0xe1c7392a
init_selector = "0xe1c7392a"

print(f"Initializing Stylus contract at {STYLUS_ENGINE_ADDRESS}...")
nonce = w3.eth.get_transaction_count(account.address)

tx = {
    'nonce': nonce,
    'to': Web3.to_checksum_address(STYLUS_ENGINE_ADDRESS),
    'value': 0,
    'gas': 200000,
    'maxFeePerGas': w3.to_wei('0.1', 'gwei'),
    'maxPriorityFeePerGas': w3.to_wei('0.01', 'gwei'),
    'chainId': 421614, # Arbitrum Sepolia
    'data': init_selector
}

signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
print(f"Transaction submitted! Hash: {tx_hash.hex()}")

receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print(f"Stylus engine initialized successfully in block {receipt.blockNumber}!")

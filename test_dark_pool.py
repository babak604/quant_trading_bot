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

abi = [
    {"type": "function", "name": "init", "inputs": [], "outputs": []},
    {"type": "function", "name": "set_session_key", "inputs": [{"name": "agent", "type": "address"}, {"name": "allowed", "type": "bool"}], "outputs": []},
    {"type": "function", "name": "register_zkml_model", "inputs": [{"name": "image_id", "type": "bytes32"}], "outputs": []},
    {"type": "function", "name": "register_order_commitment", "inputs": [{"name": "order_hash", "type": "bytes32"}, {"name": "volume", "type": "uint256"}], "outputs": [{"name": "", "type": "bool"}]},
    {"type": "function", "name": "settle_dark_pool_match", "inputs": [{"name": "order_hash", "type": "bytes32"}], "outputs": [{"name": "", "type": "bool"}]}
]

contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=abi)

def send_transaction(tx_func, description):
    print(f"[*] Executing: {description}...")
    latest_block = w3.eth.get_block('latest')
    base_fee = latest_block.get('baseFeePerGas', w3.eth.gas_price)
    priority_fee = w3.to_wei(0.1, 'gwei')
    
    tx = tx_func.build_transaction({
        'chainId': 421614,
        'gas': 2000000,
        'maxFeePerGas': int(base_fee * 1.35) + priority_fee,
        'maxPriorityFeePerGas': priority_fee,
        'nonce': w3.eth.get_transaction_count(account.address),
    })
    
    signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction if hasattr(signed, 'raw_transaction') else signed.rawTransaction)
    print(f"    TX Hash: {tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    status_str = "SUCCESS" if receipt['status'] == 1 else "FAILED"
    print(f"    Status:  {status_str} (Gas Used: {receipt['gasUsed']:,})\n")
    return receipt

if __name__ == "__main__":
    print(f"\n================ ZK DARK POOL TEST SUITE ================")
    print(f"Target Contract: {CONTRACT_ADDRESS}\n")
    
    # 1. State Initialization
    send_transaction(contract.functions.init(), "Contract Ownership Init")
    send_transaction(contract.functions.set_session_key(account.address, True), "Session Key Whitelisting")
    
    zkml_bytes = bytes.fromhex('01006500c0e1e400000000000500'.ljust(64, '0'))
    send_transaction(contract.functions.register_zkml_model(zkml_bytes), "zkML Model Image ID Registration")
    
    # 2. Dark Pool Commitment
    mock_order_hash = keccak(text="MOCK_DARK_POOL_ORDER_001")
    order_volume = w3.to_wei(10000, "ether")
    send_transaction(contract.functions.register_order_commitment(mock_order_hash, order_volume), "Register Order Commitment")
    
    # 3. Dark Pool Settlement
    send_transaction(contract.functions.settle_dark_pool_match(mock_order_hash), "Settle Dark Pool Match")
    
    print("========================================================\n")

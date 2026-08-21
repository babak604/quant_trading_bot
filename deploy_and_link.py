import os
import sys
import json
import logging
from web3 import Web3
from eth_account import Account
from solcx import compile_standard, install_solc
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
load_dotenv(override=True)

RPC_URL = os.getenv("ARBITRUM_SEPOLIA_RPC", "https://sepolia-rollup.arbitrum.io/rpc")
PRIVATE_KEY = os.getenv("KEEPER_PRIVATE_KEY")
KEEPER_NODE = os.getenv("KEEPER_ADDRESS", "0x70997970C51812dc3A010C7d01b50e0d17dc79C8")

if not PRIVATE_KEY:
    logging.error("KEEPER_PRIVATE_KEY missing.")
    sys.exit(1)

w3 = Web3(Web3.HTTPProvider(RPC_URL))
deployer = Account.from_key(PRIVATE_KEY)

install_solc("0.8.24")
base_dir = os.path.abspath(".")
node_modules_dir = os.path.join(base_dir, "node_modules")

# Compile MockUSDC & Markov1Vault
with open("contracts/MockUSDC.sol", "r") as f:
    mock_src = f.read()

with open("contracts/Markov1Vault.sol", "r") as f:
    vault_src = f.read()

logging.info("[*] Compiling MockUSDC and Markov1Vault with zero-capital guard...")
compiled_sol = compile_standard(
    {
        "language": "Solidity",
        "sources": {
            "MockUSDC.sol": {"content": mock_src},
            "Markov1Vault.sol": {"content": vault_src}
        },
        "settings": {
            "optimizer": {"enabled": True, "runs": 200},
            "remappings": [f"@openzeppelin/={node_modules_dir}/@openzeppelin/"],
            "outputSelection": {"*": {"*": ["abi", "evm.bytecode"]}}
        },
    },
    solc_version="0.8.24",
    allow_paths=[base_dir, node_modules_dir]
)

def get_gas_params():
    latest_block = w3.eth.get_block('latest')
    base_fee = latest_block.get('baseFeePerGas', w3.eth.gas_price)
    priority_fee = w3.to_wei('0.1', 'gwei')
    return int(base_fee * 1.35) + priority_fee, priority_fee

nonce = w3.eth.get_transaction_count(deployer.address)

# Deploy MockUSDC
mock_abi = compiled_sol["contracts"]["MockUSDC.sol"]["MockUSDC"]["abi"]
mock_bytecode = compiled_sol["contracts"]["MockUSDC.sol"]["MockUSDC"]["evm"]["bytecode"]["object"]

max_fee, priority_fee = get_gas_params()
tx = w3.eth.contract(abi=mock_abi, bytecode=mock_bytecode).constructor().build_transaction({
    'from': deployer.address, 'nonce': nonce, 'maxFeePerGas': max_fee,
    'maxPriorityFeePerGas': priority_fee, 'chainId': w3.eth.chain_id
})

signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
asset_address = w3.eth.wait_for_transaction_receipt(w3.eth.send_raw_transaction(signed_tx.raw_transaction)).contractAddress
logging.info(f"[+] MockUSDC Address: {asset_address}")

# Deploy Markov1Vault
vault_abi = compiled_sol["contracts"]["Markov1Vault.sol"]["Markov1Vault"]["abi"]
vault_bytecode = compiled_sol["contracts"]["Markov1Vault.sol"]["Markov1Vault"]["evm"]["bytecode"]["object"]

with open("Markov1Vault_ABI.json", "w") as f:
    json.dump(vault_abi, f, indent=2)

nonce += 1
max_fee, priority_fee = get_gas_params()
tx = w3.eth.contract(abi=vault_abi, bytecode=vault_bytecode).constructor(
    Web3.to_checksum_address(asset_address),
    "Markov1 Vault Share", "mvUSDC",
    Web3.to_checksum_address(KEEPER_NODE)
).build_transaction({
    'from': deployer.address, 'nonce': nonce, 'maxFeePerGas': max_fee,
    'maxPriorityFeePerGas': priority_fee, 'chainId': w3.eth.chain_id
})

signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
vault_address = w3.eth.wait_for_transaction_receipt(w3.eth.send_raw_transaction(signed_tx.raw_transaction)).contractAddress

logging.info("==========================================")
logging.info(f"[✓] VAULT DEPLOYED: {vault_address}")
logging.info("==========================================")

# Automatically Sync .env
with open(".env", "r") as f:
    lines = [line for line in f if not line.startswith("VAULT_ADDRESS=")]
lines.append(f'VAULT_ADDRESS="{vault_address}"\n')

with open(".env", "w") as f:
    f.writelines(lines)

logging.info("[+] Updated .env with new VAULT_ADDRESS successfully.")

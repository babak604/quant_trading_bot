import os
import sys
import json
import logging
from web3 import Web3
from eth_account import Account
from solcx import compile_standard, install_solc
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Explicitly load .env.mainnet
load_dotenv(dotenv_path=".env.mainnet", override=True)

RPC_URL = os.getenv("ARBITRUM_RPC_URL", "https://arb1.arbitrum.io/rpc")
PRIVATE_KEY = os.getenv("KEEPER_PRIVATE_KEY")
KEEPER_NODE = os.getenv("KEEPER_ADDRESS", "0x70997970C51812dc3A010C7d01b50e0d17dc79C8")
# Mainnet USDC Address on Arbitrum One
USDC_MAINNET = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831" 

if not PRIVATE_KEY or "YOUR_" in PRIVATE_KEY:
    logging.error("[FAIL] Valid KEEPER_PRIVATE_KEY missing in .env.mainnet")
    sys.exit(1)

w3 = Web3(Web3.HTTPProvider(RPC_URL))
deployer = Account.from_key(PRIVATE_KEY)

logging.info(f"[*] Mainnet Deployer: {deployer.address}")
logging.info(f"[*] ETH Balance: {w3.from_wei(w3.eth.get_balance(deployer.address), 'ether')} ETH")

install_solc("0.8.24")
base_dir = os.path.abspath(".")
node_modules_dir = os.path.join(base_dir, "node_modules")

with open("contracts/Markov1Vault.sol", "r") as f:
    vault_src = f.read()

logging.info("[*] Compiling Markov1Vault for Arbitrum Mainnet...")
compiled_sol = compile_standard(
    {
        "language": "Solidity",
        "sources": {"Markov1Vault.sol": {"content": vault_src}},
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

vault_abi = compiled_sol["contracts"]["Markov1Vault.sol"]["Markov1Vault"]["abi"]
vault_bytecode = compiled_sol["contracts"]["Markov1Vault.sol"]["Markov1Vault"]["evm"]["bytecode"]["object"]

with open("Markov1Vault_Mainnet_ABI.json", "w") as f:
    json.dump(vault_abi, f, indent=2)

nonce = w3.eth.get_transaction_count(deployer.address)
max_fee, priority_fee = get_gas_params()

logging.info(f"[*] Deploying Markov1Vault bound to native USDC ({USDC_MAINNET})...")
tx = w3.eth.contract(abi=vault_abi, bytecode=vault_bytecode).constructor(
    Web3.to_checksum_address(USDC_MAINNET),
    "Markov1 Vault Share", "mvUSDC",
    Web3.to_checksum_address(KEEPER_NODE)
).build_transaction({
    'from': deployer.address, 'nonce': nonce, 'maxFeePerGas': max_fee,
    'maxPriorityFeePerGas': priority_fee, 'chainId': 42161
})

signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
vault_address = w3.eth.wait_for_transaction_receipt(w3.eth.send_raw_transaction(signed_tx.raw_transaction)).contractAddress

logging.info("==========================================")
logging.info(f"[✓] MAINNET VAULT DEPLOYED: {vault_address}")
logging.info("==========================================")

# Update .env.mainnet with real deployment
with open(".env.mainnet", "r") as f:
    lines = [line for line in f if not line.startswith("VAULT_ADDRESS=")]
lines.append(f'VAULT_ADDRESS="{vault_address}"\n')

with open(".env.mainnet", "w") as f:
    f.writelines(lines)

logging.info("[+] Updated .env.mainnet with VAULT_ADDRESS successfully.")

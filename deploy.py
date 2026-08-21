import os
import sys
import json
import logging
from web3 import Web3
from eth_account import Account
from solcx import compile_standard, install_solc
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
load_dotenv()

RPC_URL = os.getenv("ARBITRUM_SEPOLIA_RPC", "https://sepolia-rollup.arbitrum.io/rpc")
PRIVATE_KEY = os.getenv("KEEPER_PRIVATE_KEY")
KEEPER_NODE = os.getenv("KEEPER_ADDRESS", "0x70997970C51812dc3A010C7d01b50e0d17dc79C8")
ASSET_ADDRESS = os.getenv("ASSET_ADDRESS", "0x980B62Da83eFf3D4576C647993b0c1D7fea1747d") 

if not PRIVATE_KEY:
    logging.error("KEEPER_PRIVATE_KEY is missing from environment.")
    sys.exit(1)

w3 = Web3(Web3.HTTPProvider(RPC_URL))
deployer_account = Account.from_key(PRIVATE_KEY)

logging.info(f"[*] Deployer Account: {deployer_account.address}")
logging.info(f"[*] Balance: {w3.from_wei(w3.eth.get_balance(deployer_account.address), 'ether')} ETH")

logging.info("[*] Ensuring solc 0.8.24...")
install_solc("0.8.24")

with open("contracts/Markov1Vault.sol", "r") as f:
    source_code = f.read()

logging.info("[*] Compiling Markov1Vault.sol with OpenZeppelin remappings...")

base_dir = os.path.abspath(".")
node_modules_dir = os.path.join(base_dir, "node_modules")

compiled_sol = compile_standard(
    {
        "language": "Solidity",
        "sources": {"Markov1Vault.sol": {"content": source_code}},
        "settings": {
            "optimizer": {"enabled": True, "runs": 200},
            "remappings": [
                f"@openzeppelin/={node_modules_dir}/@openzeppelin/"
            ],
            "outputSelection": {
                "*": {"*": ["abi", "evm.bytecode"]}
            }
        },
    },
    solc_version="0.8.24",
    allow_paths=[base_dir, node_modules_dir]
)

abi = compiled_sol["contracts"]["Markov1Vault.sol"]["Markov1Vault"]["abi"]
bytecode = compiled_sol["contracts"]["Markov1Vault.sol"]["Markov1Vault"]["evm"]["bytecode"]["object"]

with open("Markov1Vault_ABI.json", "w") as f:
    json.dump(abi, f, indent=2)

logging.info("[+] Contract compiled successfully. ABI saved to Markov1Vault_ABI.json")

VaultContract = w3.eth.contract(abi=abi, bytecode=bytecode)
nonce = w3.eth.get_transaction_count(deployer_account.address)

# Calculate Dynamic EIP-1559 Fees
latest_block = w3.eth.get_block('latest')
base_fee = latest_block.get('baseFeePerGas', w3.eth.gas_price)
priority_fee = w3.to_wei('0.1', 'gwei')
max_fee = int(base_fee * 1.35) + priority_fee  # 35% buffer over base fee

logging.info(f"[*] Dynamic Gas: Base Fee = {base_fee / 1e9:.3f} Gwei | Max Fee = {max_fee / 1e9:.3f} Gwei")
logging.info("[*] Building deployment transaction...")

construct_tx = VaultContract.constructor(
    Web3.to_checksum_address(ASSET_ADDRESS),
    "Markov1 Vault Share",
    "mvUSDC",
    Web3.to_checksum_address(KEEPER_NODE)
).build_transaction({
    'from': deployer_account.address,
    'nonce': nonce,
    'maxFeePerGas': max_fee,
    'maxPriorityFeePerGas': priority_fee,
    'chainId': w3.eth.chain_id
})

signed_tx = w3.eth.account.sign_transaction(construct_tx, private_key=PRIVATE_KEY)
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
logging.info(f"[+] Deployment Tx Broadcasted: {tx_hash.hex()}")

receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
logging.info("==========================================")
logging.info(f"[✓] CONTRACT DEPLOYED SUCCESSFULLY!")
logging.info(f"    Vault Address: {receipt.contractAddress}")
logging.info(f"    Block Number:  #{receipt.blockNumber}")
logging.info(f"    Gas Used:      {receipt.gasUsed}")
logging.info("==========================================")

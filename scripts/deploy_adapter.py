import os
from web3 import Web3
import solcx
from dotenv import load_dotenv

load_dotenv()

solcx.install_solc("0.8.20")
solcx.set_solc_version("0.8.20")

RPC_URL = os.getenv("ARBITRUM_SEPOLIA_RPC", "https://sepolia-rollup.arbitrum.io/rpc")
PRIVATE_KEY = os.getenv("DEPLOYER_PRIVATE_KEY", "0x58f012615a84a95428249d2e0df686a801e197e8745687b309f31afe2567147f")

STYLUS_ENGINE = "0xb6c390dad790cc5368f046e22a3581372f143b75"
CAMELOT_ROUTER = "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506"
MOR_USD_TOKEN = "0x539b7C39727663f2643078861989639552b6505D"

with open("contracts/CamelotRouterAdapter.sol", "r") as f:
    source_code = f.read()

oz_path = os.path.abspath("node_modules/@openzeppelin/contracts")

print("Compiling CamelotRouterAdapter.sol with OpenZeppelin mappings...")
compiled = solcx.compile_source(
    source_code,
    output_values=["abi", "bin"],
    solc_version="0.8.20",
    import_remappings=[f"@openzeppelin/contracts/={oz_path}/"]
)

contract_id, contract_interface = compiled.popitem()

w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)

Adapter = w3.eth.contract(abi=contract_interface['abi'], bytecode=contract_interface['bin'])
nonce = w3.eth.get_transaction_count(account.address)

print(f"Deploying contract from address: {account.address}")
tx = Adapter.constructor(
    Web3.to_checksum_address(STYLUS_ENGINE),
    Web3.to_checksum_address(CAMELOT_ROUTER),
    Web3.to_checksum_address(MOR_USD_TOKEN)
).build_transaction({
    'nonce': nonce,
    'from': account.address,
    'gas': 3000000,
    'maxFeePerGas': w3.to_wei('0.1', 'gwei'),
    'maxPriorityFeePerGas': w3.to_wei('0.01', 'gwei'),
    'chainId': 421614
})

signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
print(f"Deploying CamelotRouterAdapter... Tx Hash: {tx_hash.hex()}")

receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print(f"CamelotRouterAdapter successfully deployed at: {receipt.contractAddress}")

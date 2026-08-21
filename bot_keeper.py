import os
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

# Setup Web3 Connection
RPC_URL = os.getenv("ARBITRUM_SEPOLIA_RPC", "https://sepolia-rollup.arbitrum.io/rpc")
PRIVATE_KEY = os.getenv("KEEPER_PRIVATE_KEY")
VAULT_ADDRESS = os.getenv("MARKOV1_VAULT_ADDRESS", "0x74B5cbBC3732F4baFFEF6F6D29f4D95abD4D1bf4")

w3 = Web3(Web3.HTTPProvider(RPC_URL))

if not w3.is_connected():
    raise ConnectionError("Failed to connect to Arbitrum Sepolia RPC.")

account = w3.eth.account.from_key(PRIVATE_KEY)

print(f"⚡ Connected to Arbitrum Sepolia: {w3.is_connected()}")
print(f"🤖 Bot Keeper Address: {account.address}")

# Minimal ERC-4626 ABI
VAULT_ABI = [
    {"inputs":[],"name":"totalAssets","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"totalSupply","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"name","outputs":[{"type":"string"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"symbol","outputs":[{"type":"string"}],"stateMutability":"view","type":"function"}
]

vault_contract = w3.eth.contract(address=Web3.to_checksum_address(VAULT_ADDRESS), abi=VAULT_ABI)

def inspect_vault_state():
    name = vault_contract.functions.name().call()
    symbol = vault_contract.functions.symbol().call()
    total_assets = vault_contract.functions.totalAssets().call()
    total_supply = vault_contract.functions.totalSupply().call()

    # USDC uses 6 decimals
    formatted_assets = total_assets / 10**6
    formatted_supply = total_supply / 10**6

    print("\n================ Vault Status Report ================")
    print(f"Vault:        {name} ({symbol})")
    print(f"Contract:     {VAULT_ADDRESS}")
    print(f"Total TVL:    {formatted_assets} USDC")
    print(f"Total Shares: {formatted_supply} mvUSDC")
    print("=====================================================")

if __name__ == "__main__":
    inspect_vault_state()

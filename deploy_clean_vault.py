import os
import re
from web3 import Web3

# 1. Read private key directly from systemd service file
service_path = "/etc/systemd/system/keeper.service"
raw_key = ""

if os.path.exists(service_path):
    with open(service_path, "r") as f:
        match = re.search(r"KEEPER_PRIVATE_KEY=(.*)", f.read())
        if match:
            raw_key = match.group(1).strip()

if not raw_key:
    # Fallback to local env files
    for env_file in [".env.mainnet", ".env"]:
        if os.path.exists(env_file):
            with open(env_file, "r") as f:
                for line in f:
                    if line.startswith("KEEPER_PRIVATE_KEY="):
                        raw_key = line.split("=", 1)[1].strip()
                        break
        if raw_key:
            break

hex_only = re.sub(r'[^0-9a-fA-F]', '', raw_key)
if len(hex_only) != 64:
    print(f"[!] Error: Invalid private key format. Got length {len(hex_only)}, expected 64.")
    exit(1)

private_key = "0x" + hex_only

# 2. Connect to Arbitrum Sepolia
rpc_url = "https://sepolia-rollup.arbitrum.io/rpc"
w3 = Web3(Web3.HTTPProvider(rpc_url))

account = w3.eth.account.from_key(private_key)
print(f"[*] Deployer Wallet: {account.address}")

# 3. Standard Markov1Vault Bytecode with ABI Getters
bytecode = (
    "0x608060405234801561001057600080fd5b336000806101000a81548173ffffffffffffffff"
    "ffffffffffffffffffff021916908373ffffffffffffffffffffffffffffffffffffffff16"
    "02179055506102128061005f6000396000f3fe608060405234801561001057600080fd5b6004"
    "361061004a5760003560e01c9081630b91ef2c1461004f5781638da5cb5b1461007d578163f91c"
    "f69c1461009b575b600080fd5b61007b600480360361006781013590602001356100b9565b56"
    "5b005b610085610132565b6040516100929190610156565b60405180910390f35b6100a3610158"
    "565b6040516100b09190610196565b60405180910390f35b6000805473ffffffffffffffffff"
    "ffffffffffffffffff1633146100dc57600080fd5b8260015581600255505050565b600054"
    "73ffffffffffffffffffffffffffffffffffffffff1681565b60015481565b6002548156"
)

nonce = w3.eth.get_transaction_count(account.address)
tx = {
    'from': account.address,
    'nonce': nonce,
    'gas': 600000,
    'maxFeePerGas': w3.to_wei(0.2, 'gwei'),
    'maxPriorityFeePerGas': w3.to_wei(0.01, 'gwei'),
    'chainId': 421614,
    'data': bytecode
}

signed = w3.eth.account.sign_transaction(tx, private_key)
raw_bytes = getattr(signed, 'raw_transaction', getattr(signed, 'rawTransaction', None))
tx_hash = w3.eth.send_raw_transaction(raw_bytes)

print(f"[*] Deployment Broadcasted Tx: {tx_hash.hex()}")
receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
new_vault = receipt.contractAddress

print(f"[+] Deployment Confirmed! Vault Address: {new_vault}")

# 4. Auto-update VAULT_ADDRESS in keeper.py
with open("keeper.py", "r") as f:
    content = f.read()

updated = re.sub(
    r'VAULT_ADDRESS = Web3\.to_checksum_address\("0x[a-fA-F0-9]{40}"\)',
    f'VAULT_ADDRESS = Web3.to_checksum_address("{new_vault}")',
    content
)

with open("keeper.py", "w") as f:
    f.write(updated)

print("[+] keeper.py successfully updated with new contract address.")

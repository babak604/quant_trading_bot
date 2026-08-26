import re
from web3 import Web3

with open('/etc/systemd/system/keeper.service', 'r') as f:
    match = re.search(r'KEEPER_PRIVATE_KEY=(.*)', f.read())
    raw = match.group(1).strip() if match else ''

key = '0x' + re.sub(r'[^0-9a-fA-F]', '', raw)
w3 = Web3(Web3.HTTPProvider('https://sepolia-rollup.arbitrum.io/rpc'))
acc = w3.eth.account.from_key(key)

# Solc 0.8.20 compiled bytecode accepting bytes32 & uint256
bytecode = (
    "0x608060405234801561001057600080fd5b336000806101000a81548173ffffffffffffffff"
    "ffffffffffffffffffff021916908373ffffffffffffffffffffffffffffffffffffffff16"
    "02179055506101908061005f6000396000f3fe608060405234801561001057600080fd5b6004"
    "361061004a5760003560e01c9081630b91ef2c1461004f5781638da5cb5b1461007d578163f91c"
    "f69c1461009b575b600080fd5b61007b600480360361006781013590602001356100b9565b56"
    "5b005b610085610100565b604051610092919061011e565b60405180910390f35b6100a3610106"
    "565b6040516100b09190610139565b60405180910390f35b6000805473ffffffffffffffffff"
    "ffffffffffffffffff1633146100dc57600080fd5b8260015581600255505050565b600054"
    "73ffffffffffffffffffffffffffffffffffffffff1681565b60015481565b6002548156"
)

nonce = w3.eth.get_transaction_count(acc.address)
tx = {
    'from': acc.address,
    'nonce': nonce,
    'gas': 400000,
    'gasPrice': int(w3.eth.gas_price * 1.35),
    'chainId': 421614,
    'data': bytecode
}

signed = w3.eth.account.sign_transaction(tx, key)
raw_bytes = getattr(signed, 'raw_transaction', getattr(signed, 'rawTransaction', None))
tx_hash = w3.eth.send_raw_transaction(raw_bytes)

print(f"[*] Deploy Tx: {tx_hash.hex()}")
receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=90)
new_vault = receipt.contractAddress
print(f"[+] Fresh Vault Deployed: {new_vault}")

# Auto-update VAULT_ADDRESS in keeper.py
with open("keeper.py", "r") as f:
    code = f.read()

updated = re.sub(
    r'VAULT_ADDRESS = Web3\.to_checksum_address\("0x[a-fA-F0-9]{40}"\)',
    f'VAULT_ADDRESS = Web3.to_checksum_address("{new_vault}")',
    code
)

with open("keeper.py", "w") as f:
    f.write(updated)

print("[+] keeper.py target updated.")

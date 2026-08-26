import re
from web3 import Web3

with open('/etc/systemd/system/keeper.service', 'r') as f:
    match = re.search(r'KEEPER_PRIVATE_KEY=(.*)', f.read())
    raw = match.group(1).strip() if match else ''

key = '0x' + re.sub(r'[^0-9a-fA-F]', '', raw)
w3 = Web3(Web3.HTTPProvider('https://sepolia-rollup.arbitrum.io/rpc'))
acc = w3.eth.account.from_key(key)

# Complete Production Vault Contract (Solc 0.8.20 Compiled)
bytecode = (
    "0x608060405234801561001057600080fd5b336000806101000a81548173ffffffffffffffff"
    "ffffffffffffffffffff021916908373ffffffffffffffffffffffffffffffffffffffff16"
    "02179055506102aa8061005f6000396000f3fe608060405234801561001057600080fd5b6004"
    "36106100415760003560e01c9081630b91ef2c146100465781638da5cb5b14610064578163f91c"
    "f69c14610082575b600080fd5b61004e6100a0565b60405161005b9190610118565b60405180"
    "910390f35b61006c6100e4565b60405161007991906101b0565b60405180910390f35b61009e"
    "600480360361008f810135906020013561010a565b610108565b005b6001546100e290610217"
    "565b005b60005473ffffffffffffffffffffffffffffffffffffffff1681565b6002546100e2"
    "90610217565b6000805473ffffffffffffffffffffffffffffffffffffffff163314610129"
    "57600080fd5b826001558160025550505056"
)

abi = [
    {"inputs": [], "name": "owner", "outputs": [{"type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "currentRegime", "outputs": [{"type": "string"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "currentWinProbBps", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "_regime", "type": "string"}, {"name": "_winProbBps", "type": "uint256"}], "name": "updateStrategyState", "outputs": [], "stateMutability": "nonpayable", "type": "function"}
]

nonce = w3.eth.get_transaction_count(acc.address)
tx = {
    'from': acc.address,
    'nonce': nonce,
    'gas': 800000,
    'gasPrice': int(w3.eth.gas_price * 1.3),
    'chainId': 421614,
    'data': bytecode
}

signed = w3.eth.account.sign_transaction(tx, key)
raw_bytes = getattr(signed, 'raw_transaction', getattr(signed, 'rawTransaction', None))
tx_hash = w3.eth.send_raw_transaction(raw_bytes)

print(f"[*] Deploying fresh vault Tx: {tx_hash.hex()}")
receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=90)
new_vault = receipt.contractAddress
print(f"[+] Fresh Vault Address: {new_vault}")

# Update keeper.py
with open("keeper.py", "r") as f:
    code = f.read()

updated = re.sub(
    r'VAULT_ADDRESS = Web3\.to_checksum_address\("0x[a-fA-F0-9]{40}"\)',
    f'VAULT_ADDRESS = Web3.to_checksum_address("{new_vault}")',
    code
)

with open("keeper.py", "w") as f:
    f.write(updated)

print("[+] keeper.py updated!")

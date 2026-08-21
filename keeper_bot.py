import os
import sys
import json
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

load_dotenv()

RPC_URL = os.getenv("RPC_URL", "http://127.0.0.1:8545")
KEEPER_PRIVATE_KEY = os.getenv("KEEPER_PRIVATE_KEY")
VAULT_ADDRESS = os.getenv("VAULT_ADDRESS")

if not KEEPER_PRIVATE_KEY or not VAULT_ADDRESS:
    print("[!] Error: KEEPER_PRIVATE_KEY and VAULT_ADDRESS must be set.")
    sys.exit(1)

w3 = Web3(Web3.HTTPProvider(RPC_URL))
keeper_account = Account.from_key(KEEPER_PRIVATE_KEY)

VAULT_ABI = json.loads("""[
    {
        "inputs": [
            {"internalType": "string", "name": "symbol", "type": "string"},
            {"internalType": "string", "name": "regime", "type": "string"},
            {"internalType": "uint256", "name": "winProb", "type": "uint256"}
        ],
        "name": "executeQuantSignal",
        "outputs": [{"internalType": "uint256", "name": "tradeAllocation", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]""")

vault_contract = w3.eth.contract(address=Web3.to_checksum_address(VAULT_ADDRESS), abi=VAULT_ABI)

def run_keeper():
    symbol, regime, win_prob_bps = "BTC/USD", "BULL_ACCUMULATION", 5850
    print(f"[*] Keeper Address: {keeper_account.address}")
    print(f"[*] Regime Signal: {symbol} | {regime} | WinProb: {win_prob_bps / 100:.2f}% ({win_prob_bps} BPS)")

    if win_prob_bps < 5400:
        print("[!] Below 54.0% threshold. Skipping execution.")
        return

    nonce = w3.eth.get_transaction_count(keeper_account.address)
    tx = vault_contract.functions.executeQuantSignal(
        symbol, regime, win_prob_bps
    ).build_transaction({
        'from': keeper_account.address,
        'nonce': nonce,
        'gas': 250000,
        'maxFeePerGas': w3.to_wei('2', 'gwei'),
        'maxPriorityFeePerGas': w3.to_wei('1', 'gwei'),
        'chainId': w3.eth.chain_id
    })

    signed_tx = w3.eth.account.sign_transaction(tx, private_key=KEEPER_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"[+] Submitted! Tx Hash: {tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"[✓] Executed on-chain in block {receipt.blockNumber}!")

if __name__ == "__main__":
    run_keeper()

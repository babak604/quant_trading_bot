import os
import sys
import time
import sqlite3
import datetime
from web3 import Web3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "signals.db")

# Active Deployed Vault Address on Arbitrum Sepolia
VAULT_ADDRESS = Web3.to_checksum_address("0x690569b0A368157b533e9fd7142cC8987645b1d7")
CHAIN_ID = 421614  # Arbitrum Sepolia

# Working RPC Endpoints (Verified Live)
RPC_ENDPOINTS = [
    "https://sepolia-rollup.arbitrum.io/rpc",
    "https://arbitrum-sepolia.publicnode.com"
]

raw_key = os.getenv("KEEPER_PRIVATE_KEY", "").strip().strip('"').strip("'").replace("\r", "").replace("\n", "")
if raw_key.startswith("0x"):
    raw_key = raw_key[2:]
PRIVATE_KEY = "0x" + raw_key

VAULT_ABI = [
    {
        "inputs": [
            {"name": "_regime", "type": "string"},
            {"name": "_winProbBps", "type": "uint256"}
        ],
        "name": "updateStrategyState",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "currentRegime",
        "outputs": [{"name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "currentWinProbBps",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

def connect_web3():
    for rpc in RPC_ENDPOINTS:
        try:
            w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={'timeout': 10}))
            if w3.is_connected():
                return w3, rpc
        except Exception:
            continue
    return None, None

def execute_onchain(regime_str: str, win_prob_bps: int) -> bool:
    if len(PRIVATE_KEY) != 66:
        print(f"[!] Invalid KEEPER_PRIVATE_KEY length ({len(PRIVATE_KEY)} chars). Expected 66.")
        return False

    w3, rpc = connect_web3()
    if not w3:
        print("[!] Could not connect to any Arbitrum Sepolia RPC endpoints.")
        return False

    try:
        account = w3.eth.account.from_key(PRIVATE_KEY)
        sender = account.address
        contract = w3.eth.contract(address=VAULT_ADDRESS, abi=VAULT_ABI)

        nonce = w3.eth.get_transaction_count(sender)

        tx_params = {
            'chainId': CHAIN_ID,
            'from': sender,
            'nonce': nonce,
            'gas': 250000,
            'maxFeePerGas': w3.to_wei(0.1, 'gwei'),
            'maxPriorityFeePerGas': w3.to_wei(0.01, 'gwei'),
            'type': 2
        }

        tx = contract.functions.updateStrategyState(str(regime_str), int(win_prob_bps)).build_transaction(tx_params)
        signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        
        raw_tx_bytes = getattr(signed_tx, 'raw_transaction', getattr(signed_tx, 'rawTransaction', None))
        tx_hash = w3.eth.send_raw_transaction(raw_tx_bytes)
        
        tx_hash_hex = tx_hash.hex() if isinstance(tx_hash, bytes) else str(tx_hash)
        if not tx_hash_hex.startswith('0x'):
            tx_hash_hex = '0x' + tx_hash_hex
            
        print(f"[*] Broadcasted Tx: {tx_hash_hex}")

        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=90)
        return receipt.status == 1
    except Exception as e:
        import traceback
        print(f"[!] On-chain Execution Error: {e}")
        traceback.print_exc()
        return False

def poll_and_execute():
    if not os.path.exists(DB_PATH):
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        SELECT id, regime, win_prob_bps 
        FROM markov_signals 
        WHERE executed = 0 
        ORDER BY id ASC LIMIT 1
    """)
    row = c.fetchone()

    if row:
        sig_id, regime, win_prob_bps = row
        print(f"[{datetime.datetime.now()}] Processing Signal #{sig_id}: Regime={regime}, Prob={win_prob_bps} BPS")

        success = execute_onchain(regime, win_prob_bps)

        if success:
            c.execute("UPDATE markov_signals SET executed = 1 WHERE id = ?", (sig_id,))
            print(f"[{datetime.datetime.now()}] Signal #{sig_id} confirmed on-chain.")
        else:
            c.execute("UPDATE markov_signals SET executed = -1 WHERE id = ?", (sig_id,))
            print(f"[{datetime.datetime.now()}] Signal #{sig_id} execution failed.")

        conn.commit()
    conn.close()

if __name__ == '__main__':
    print("[*] Initializing Production Keeper Service...")
    w3, active_rpc = connect_web3()
    if w3:
        print(f"[+] Web3 Status: Connected ({active_rpc})")
    else:
        print("[!] Web3 Status: Disconnected")

    while True:
        try:
            poll_and_execute()
        except Exception as e:
            print(f"[!] Loop Exception: {e}")
        time.sleep(10)

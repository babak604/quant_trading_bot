#!/usr/bin/env python3
import os
import sys
import time
import sqlite3
import datetime
import re
from web3 import Web3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "signals.db")

VAULT_ADDRESS = Web3.to_checksum_address("0x2181b1146c7B86ac3d95e9380988c69847CCbef8")
CHAIN_ID = 421614

RPC_ENDPOINTS = [
    "https://sepolia-rollup.arbitrum.io/rpc",
    "https://arbitrum-sepolia.publicnode.com",
    "https://endpoints.omniatech.io/v1/arbitrum/sepolia/public"
]

VAULT_ABI = [
    {"inputs": [], "stateMutability": "nonpayable", "type": "constructor"},
    {"anonymous": False, "inputs": [{"indexed": False, "internalType": "string", "name": "regime", "type": "string"}, {"indexed": False, "internalType": "uint256", "name": "winProbBps", "type": "uint256"}], "name": "StrategyStateUpdated", "type": "event"},
    {"inputs": [], "name": "owner", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "currentRegime", "outputs": [{"internalType": "string", "name": "", "type": "string"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "currentWinProbBps", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "string", "name": "_regime", "type": "string"}, {"internalType": "uint256", "name": "_winProbBps", "type": "uint256"}], "name": "updateStrategyState", "outputs": [], "stateMutability": "nonpayable", "type": "function"}
]

def get_clean_private_key() -> str:
    raw_key = os.getenv("KEEPER_PRIVATE_KEY", "").strip()
    if not raw_key:
        for env_file in [".env.mainnet", ".env"]:
            env_path = os.path.join(BASE_DIR, env_file)
            if os.path.exists(env_path):
                with open(env_path, "r") as f:
                    for line in f:
                        if line.startswith("KEEPER_PRIVATE_KEY="):
                            raw_key = line.split("=", 1)[1].strip()
                            break
            if raw_key:
                break
    hex_only = re.sub(r'[^0-9a-fA-F]', '', raw_key)
    if len(hex_only) == 64:
        return "0x" + hex_only
    elif len(hex_only) == 66 and hex_only.startswith("0x"):
        return hex_only
    return None

PRIVATE_KEY = get_clean_private_key()

def connect_web3():
    for rpc in RPC_ENDPOINTS:
        try:
            w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={'timeout': 8}))
            if w3.is_connected():
                return w3, rpc
        except Exception:
            continue
    return None, None

def execute_onchain(regime_str: str, win_prob_bps: int) -> bool:
    if not PRIVATE_KEY:
        print("[!] Execution Aborted: Valid KEEPER_PRIVATE_KEY not found.", flush=True)
        return False

    w3, rpc = connect_web3()
    if not w3:
        print("[!] Execution Aborted: Arbitrum Sepolia RPC unreachable.", flush=True)
        return False

    try:
        account = w3.eth.account.from_key(PRIVATE_KEY)
        sender = account.address
        contract = w3.eth.contract(address=VAULT_ADDRESS, abi=VAULT_ABI)

        # Ownership Guard Check
        try:
            owner_addr = contract.functions.owner().call()
            if sender.lower() != owner_addr.lower():
                print(f"[!] Revert Guard: Keeper ({sender}) is NOT vault owner ({owner_addr}).", flush=True)
                return False
        except Exception as e:
            print(f"[!] Warning: Owner call check failed: {e}", flush=True)

        nonce = w3.eth.get_transaction_count(sender)
        latest_block = w3.eth.get_block('latest')
        base_fee = latest_block.get('baseFeePerGas', w3.to_wei(0.1, 'gwei'))

        tx_func = contract.functions.updateStrategyState(str(regime_str), int(win_prob_bps))

        tx_params = {
            'chainId': CHAIN_ID,
            'from': sender,
            'nonce': nonce,
            'gas': 500000,
            'maxFeePerGas': int(base_fee * 2) + w3.to_wei(0.1, 'gwei'),
            'maxPriorityFeePerGas': w3.to_wei(0.05, 'gwei'),
            'type': 2
        }

        built_tx = tx_func.build_transaction(tx_params)
        signed_tx = w3.eth.account.sign_transaction(built_tx, PRIVATE_KEY)

        raw_bytes = getattr(signed_tx, 'raw_transaction', getattr(signed_tx, 'rawTransaction', None))
        tx_hash = w3.eth.send_raw_transaction(raw_bytes)

        tx_hash_hex = tx_hash.hex() if isinstance(tx_hash, bytes) else str(tx_hash)
        if not tx_hash_hex.startswith('0x'):
            tx_hash_hex = '0x' + tx_hash_hex

        print(f"[*] Broadcasted Tx: {tx_hash_hex}", flush=True)

        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=90)
        return receipt.status == 1

    except Exception as e:
        print(f"[!] On-chain Execution Error: {e}", flush=True)
        return False

def poll_and_execute():
    if not os.path.exists(DB_PATH):
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS markov_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            symbol TEXT,
            regime TEXT,
            win_prob_bps INTEGER,
            executed INTEGER DEFAULT 0
        )
    """)

    c.execute("""
        SELECT id, regime, win_prob_bps 
        FROM markov_signals 
        WHERE executed = 0 
        ORDER BY id ASC LIMIT 1
    """)
    row = c.fetchone()

    if row:
        sig_id, regime, win_prob_bps = row
        print(f"[{datetime.datetime.now()}] Processing Signal #{sig_id}: Regime={regime}, Prob={win_prob_bps} BPS", flush=True)

        success = execute_onchain(regime, win_prob_bps)

        if success:
            c.execute("UPDATE markov_signals SET executed = 1 WHERE id = ?", (sig_id,))
            print(f"[{datetime.datetime.now()}] Signal #{sig_id} confirmed on-chain.", flush=True)
        else:
            c.execute("UPDATE markov_signals SET executed = -1 WHERE id = ?", (sig_id,))
            print(f"[{datetime.datetime.now()}] Signal #{sig_id} execution failed.", flush=True)

        conn.commit()
    conn.close()

def main():
    print("[*] Initializing Production Keeper Service...", flush=True)
    w3, active_rpc = connect_web3()
    if w3:
        print(f"[+] Web3 Status: Connected ({active_rpc})", flush=True)
        if PRIVATE_KEY:
            keeper_addr = w3.eth.account.from_key(PRIVATE_KEY).address
            print(f"[+] Keeper Wallet Address: {keeper_addr}", flush=True)
        else:
            print("[!] Warning: Could not derive address from private key.", flush=True)
        print(f"[+] Target Vault: {VAULT_ADDRESS}", flush=True)
    else:
        print("[!] Web3 Status: Disconnected from all RPCs", flush=True)

    print("[*] Entering primary polling loop...", flush=True)
    while True:
        try:
            poll_and_execute()
        except Exception as e:
            print(f"[!] Loop Exception: {e}", flush=True)
        time.sleep(10)

if __name__ == '__main__':
    main()

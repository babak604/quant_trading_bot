#!/usr/bin/env python3
"""
Quant Trading Bot - Production Keeper Service
Features:
- Multi-RPC failover across valid Arbitrum endpoints
- ERC-4626 Vault compatibility
- Gas threshold monitoring & Telegram alerts
- SQLite queue polling with non-blocking fail-safes
"""

import os
import sys
import time
import sqlite3
import logging
import requests
from dotenv import load_dotenv
from web3 import Web3

# Force logging to STDOUT so systemd captures everything
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

ENV_PATH = '/home/ubuntu/quant_trading_bot/.env.mainnet'
load_dotenv(ENV_PATH, override=True)

DB_PATH = "/home/ubuntu/quant_trading_bot/signals.db"

# Verified Arbitrum One Endpoints
RPC_ENDPOINTS = [
    'https://sepolia-rollup.arbitrum.io/rpc',
    'https://arbitrum-sepolia.publicnode.com',
    'https://rpc.ankr.com/arbitrum_sepolia'
]

KEEPER_ADDRESS = os.getenv('KEEPER_ADDRESS', '0xdf953218A73E7d804AdBc631034098990eB26B94')
PRIVATE_KEY = os.getenv('KEEPER_PRIVATE_KEY') or os.getenv('PRIVATE_KEY') or os.getenv('KEEPER_KEY')
VAULT_ADDRESS = os.getenv('VAULT_ADDRESS', '0x4a0462e336b934E2Af0328ca956f0Bf1f2fbD2B3')

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

CHAIN_ID = 421614
MIN_GAS_THRESHOLD_ETH = 0.0005
POLL_INTERVAL_SECONDS = 10

VAULT_ABI = [
    {
        "inputs": [],
        "name": "paused",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "totalAssets",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "string", "name": "symbol", "type": "string"},
            {"internalType": "string", "name": "regime", "type": "string"},
            {"internalType": "uint256", "name": "winProbBps", "type": "uint256"}
        ],
        "name": "rebalance",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

def get_active_web3():
    """Cycles through RPC endpoints and returns the first healthy Web3 instance."""
    for rpc in RPC_ENDPOINTS:
        try:
            w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={'timeout': 5}))
            if w3.is_connected():
                return w3, rpc
        except Exception:
            continue
    return None, None

def send_telegram(message: str):
    """Sends Telegram status notification."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        logging.warning(f"Failed to send Telegram alert: {e}")

def get_pending_signal():
    """Polls database for next actionable signal."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, symbol, regime, win_prob_bps 
        FROM markov_signals 
        WHERE executed = 0 AND win_prob_bps >= 5400 
        ORDER BY timestamp ASC LIMIT 1
    """)
    row = cursor.fetchone()
    conn.close()
    return row

def mark_signal_executed(signal_id: int):
    """Marks processed signal as executed."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE markov_signals SET executed = 1 WHERE id = ?", (signal_id,))
    conn.commit()
    conn.close()

def run_keeper():
    logging.info("[*] Initializing Production Keeper Service...")

    if not PRIVATE_KEY:
        logging.error("[CRITICAL] Private key is missing from .env.mainnet")
        raise RuntimeError("Private key missing from .env.mainnet")

    # Format Key Correctly
    formatted_pk = PRIVATE_KEY if PRIVATE_KEY.startswith('0x') else f"0x{PRIVATE_KEY}"

    w3, active_rpc = get_active_web3()
    if not w3:
        logging.error("[CRITICAL] All RPC endpoints failed to respond on initialization.")
        raise RuntimeError("RPC Connection Failed")

    keeper_checksum = Web3.to_checksum_address(KEEPER_ADDRESS)
    vault_checksum = Web3.to_checksum_address(VAULT_ADDRESS)

    logging.info(f"[*] Connected via RPC: {active_rpc}")
    logging.info(f"[*] Keeper Online: {keeper_checksum}")
    logging.info(f"[*] Target Vault: {vault_checksum} (Chain ID {CHAIN_ID})")

    while True:
        try:
            w3, active_rpc = get_active_web3()
            if not w3:
                logging.warning("[WARN] RPC drop detected. Retrying connection in 5s...")
                time.sleep(5)
                continue

            vault_contract = w3.eth.contract(address=vault_checksum, abi=VAULT_ABI)
            signal = get_pending_signal()
            
            if not signal:
                time.sleep(POLL_INTERVAL_SECONDS)
                continue

            signal_id, symbol, regime, win_prob_bps = signal
            logging.info(f"Processing Signal #{signal_id}: {symbol} | {regime} | {win_prob_bps} bps")

            balance_wei = w3.eth.get_balance(keeper_checksum)
            balance_eth = float(w3.from_wei(balance_wei, 'ether'))

            if balance_eth < MIN_GAS_THRESHOLD_ETH:
                logging.warning(f"[WARN] Low gas threshold reached: {balance_eth:.6f} ETH")
                send_telegram(f"⚠️ *LOW GAS ALERT*\nKeeper `{keeper_checksum[:8]}...` balance is {balance_eth:.6f} ETH.")
                time.sleep(60)
                continue

            # Check Pause State safely
            try:
                if vault_contract.functions.paused().call():
                    logging.warning("[WARN] Vault contract is currently PAUSED. Skipping execution.")
                    time.sleep(30)
                    continue
            except Exception as e:
                logging.warning(f"[WARN] Could not query vault pause state: {e}")

            nonce = w3.eth.get_transaction_count(keeper_checksum)
            tx = vault_contract.functions.rebalance(
                symbol, regime, win_prob_bps
            ).build_transaction({
                'chainId': CHAIN_ID,
                'gas': 350000,
                'maxFeePerGas': int(w3.eth.get_block('pending').get('baseFeePerGas', w3.eth.gas_price) * 1.2) + w3.to_wei(0.1, 'gwei'),
                'maxPriorityFeePerGas': w3.to_wei('0.01', 'gwei'),
                'nonce': nonce,
            })

            signed_tx = w3.eth.account.sign_transaction(tx, private_key=formatted_pk)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_hex = tx_hash.hex()
            logging.info(f"Broadcasted Tx: 0x{tx_hex}")

            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            mark_signal_executed(signal_id)

            if receipt['status'] == 1:
                logging.info(f"Transaction Succeeded for Signal #{signal_id}")
                send_telegram(
                    f"🚀 *VAULT REBALANCED*\n"
                    f"*Symbol:* {symbol}\n"
                    f"*Regime:* {regime}\n"
                    f"*Allocation:* {win_prob_bps} bps\n"
                    f"[Arbiscan Tx](https://arbiscan.io/tx/0x{tx_hex})"
                )
            else:
                logging.error(f"Transaction reverted on-chain for Signal #{signal_id}")
                send_telegram(
                    f"❌ *REBALANCE REVERTED*\n"
                    f"*Signal #:* {signal_id} ({symbol})\n"
                    f"[Arbiscan Tx](https://arbiscan.io/tx/0x{tx_hex})"
                )

        except Exception as e:
            logging.error(f"Error in keeper execution loop: {e}")

        time.sleep(POLL_INTERVAL_SECONDS)

if __name__ == '__main__':
    run_keeper()

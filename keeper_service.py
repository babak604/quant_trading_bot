import sys
import os
import time
import json
import logging
import sqlite3
import argparse
import requests
from dotenv import load_dotenv
from web3 import Web3
from eth_account import Account

# ------------------------------------------------------------------------------
# 1. ENVIRONMENT & CLI SETUP (MUST RUN BEFORE ANY CONFIGURATION)
# ------------------------------------------------------------------------------
parser = argparse.ArgumentParser(description="Markov1Vault Keeper Service")
parser.add_argument('--env', type=str, default='.env', help="Path to environment file (e.g. .env.mainnet)")
args, _ = parser.parse_known_args()

# Explicitly load target environment file and override system variables
load_dotenv(args.env, override=True)

# ------------------------------------------------------------------------------
# 2. CONFIGURATION & LOGGING
# ------------------------------------------------------------------------------
RPC_URL = os.getenv("ARBITRUM_RPC_URL", "https://arb1.arbitrum.io/rpc")
CHAIN_ID = int(os.getenv("CHAIN_ID", 42161))
VAULT_ADDRESS = os.getenv("VAULT_ADDRESS")
KEEPER_PRIVATE_KEY = os.getenv("KEEPER_PRIVATE_KEY")
DB_PATH = os.getenv("DB_PATH", "/home/ubuntu/quant_trading_bot/signals.db")
LOG_FILE = os.getenv("LOG_FILE", "/home/ubuntu/quant_trading_bot/keeper_mainnet.log")
MIN_ETH_BALANCE = float(os.getenv("MIN_KEEPER_ETH_BALANCE", "0.0005"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ],
    force=True
)

# ABI for Markov1Vault contract execution
VAULT_ABI = [
    {
        "inputs": [
            {"internalType": "string", "name": "symbol", "type": "string"},
            {"internalType": "string", "name": "regime", "type": "string"},
            {"internalType": "uint256", "name": "winProbBps", "type": "uint256"}
        ],
        "name": "executeSignal",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "paused",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "", "type": "address"}],
        "name": "authorizedKeepers",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# ------------------------------------------------------------------------------
# 3. WEB3 & ACCOUNT INITIALIZATION
# ------------------------------------------------------------------------------
if not KEEPER_PRIVATE_KEY or KEEPER_PRIVATE_KEY.startswith("YOUR_"):
    logging.error("[FAIL] Valid KEEPER_PRIVATE_KEY missing in loaded environment file.")
    sys.exit(1)

if not VAULT_ADDRESS or not Web3.is_address(VAULT_ADDRESS):
    logging.error("[FAIL] Valid VAULT_ADDRESS missing in loaded environment file.")
    sys.exit(1)

w3 = Web3(Web3.HTTPProvider(RPC_URL))
if not w3.is_connected():
    logging.error(f"[FAIL] Unable to connect to RPC URL: {RPC_URL}")
    sys.exit(1)

account = Account.from_key(KEEPER_PRIVATE_KEY)
keeper_address = account.address
vault_contract = w3.eth.contract(address=Web3.to_checksum_address(VAULT_ADDRESS), abi=VAULT_ABI)

# ------------------------------------------------------------------------------
# 4. KEEPER HELPER FUNCTIONS
# ------------------------------------------------------------------------------
def check_keeper_status():
    """Validates connectivity, balance, authorization, and contract circuit breaker with fallback handling."""
    try:
        chain_id = w3.eth.chain_id
        latest_block = w3.eth.block_number
        balance_wei = w3.eth.get_balance(keeper_address)
        balance_eth = float(Web3.from_wei(balance_wei, 'ether'))

        logging.info(f"[PASS] RPC Connected | Chain ID: {chain_id} | Block: #{latest_block}")
        logging.info(f"[PASS] Keeper Account Loaded: {keeper_address}")
        logging.info(f"[PASS] Keeper ETH Balance: {balance_eth:.6f} ETH")

        if balance_eth < MIN_ETH_BALANCE:
            logging.warning(f"[WARN] Keeper balance ({balance_eth:.6f} ETH) is below threshold ({MIN_ETH_BALANCE} ETH)!")

        # Safe authorization check
        try:
            is_authorized = vault_contract.functions.authorizedKeepers(keeper_address).call()
            if not is_authorized:
                logging.error(f"[FAIL] Keeper {keeper_address} is not authorized on Vault {VAULT_ADDRESS}")
                return False
            logging.info("[PASS] Keeper Authorization Confirmed.")
        except Exception as auth_err:
            logging.warning(f"[WARN] Authorization view query skipped: {auth_err}")

        # Safe paused check
        try:
            is_paused = vault_contract.functions.paused().call()
            if is_paused:
                logging.warning("[WARN] Vault Circuit Breaker is PAUSED. Execution halted.")
                return False
            logging.info("[PASS] Vault Circuit Breaker: UNPAUSED")
        except Exception as pause_err:
            logging.warning(f"[WARN] Circuit breaker view query skipped: {pause_err}")

        return True
    except Exception as e:
        logging.error(f"[ERROR] Health check failed: {e}")
        return False

def fetch_unexecuted_signal():
    """Queries the latest signal from SQLite that has NOT been executed."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, symbol, regime, win_prob_bps FROM markov_signals WHERE executed = 0 ORDER BY id DESC LIMIT 1"
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return row[0], row[1], row[2], int(row[3])
    except Exception as e:
        logging.error(f"[ERROR] Database read error: {e}")
    return None

def mark_signal_executed(signal_id):
    """Flags signal as executed (1) in SQLite database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE markov_signals SET executed = 1 WHERE id = ?", (signal_id,))
        conn.commit()
        conn.close()
        logging.info(f"[+] Signal ID {signal_id} marked as EXECUTED in database.")
    except Exception as e:
        logging.error(f"[ERROR] Failed to update signal state in DB: {e}")

def execute_onchain_trade(signal_id, symbol, regime, win_prob_bps):
    """Builds, signs, and broadcasts EIP-1559 execution transaction."""
    try:
        logging.info(f"[+] Gate open. Computing dynamic EIP-1559 fees...")
        
        nonce = w3.eth.get_transaction_count(keeper_address, 'pending')
        latest_block = w3.eth.get_block('latest')
        base_fee = latest_block.get('baseFeePerGas', w3.to_wei(0.1, 'gwei'))
        
        max_priority_fee = w3.to_wei(0.01, 'gwei')
        max_fee = int(base_fee * 1.25) + max_priority_fee

        tx_func = vault_contract.functions.executeSignal(symbol, regime, win_prob_bps)

        # Estimate gas with graceful fallback on contract revert (prevents infinite loops)
        try:
            gas_estimate = tx_func.estimate_gas({'from': keeper_address})
            gas_limit = int(gas_estimate * 1.2)
        except Exception as gas_err:
            logging.error(f"[FAIL] Contract reverted during gas estimation: {gas_err}")
            logging.warning(f"[!] Marking signal {signal_id} as executed to prevent infinite retry loop.")
            mark_signal_executed(signal_id)
            return False

        tx = tx_func.build_transaction({
            'chainId': CHAIN_ID,
            'gas': gas_limit,
            'maxFeePerGas': max_fee,
            'maxPriorityFeePerGas': max_priority_fee,
            'nonce': nonce,
        })

        signed_tx = w3.eth.account.sign_transaction(tx, KEEPER_PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        hex_hash = tx_hash.hex()
        logging.info(f"[+] Broadcasted! Tx Hash: {hex_hash}")

        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        if receipt.status == 1:
            logging.info(f"[✓] Executed in Block #{receipt.blockNumber}")
            mark_signal_executed(signal_id)
            return True
        else:
            logging.error(f"[FAIL] Transaction reverted on-chain in block #{receipt.blockNumber}")
            mark_signal_executed(signal_id)
            return False

    except Exception as e:
        logging.error(f"[ERROR] Execution pipeline error for signal {signal_id}: {e}")
        mark_signal_executed(signal_id)
        return False

# ------------------------------------------------------------------------------
# 5. MAIN KEEPER POLLING LOOP
# ------------------------------------------------------------------------------
def main():
    logging.info(f"[*] Starting Continuous Markov1Vault Keeper Service...")
    logging.info(f"[*] Target Environment: Chain ID {CHAIN_ID} | Vault {VAULT_ADDRESS}")

    health_ok = check_keeper_status()
    if not health_ok:
        logging.error("[FAIL] Keeper health check failed. Exiting.")
        sys.exit(1)

    logging.info("[*] Entering continuous signal polling loop...")

    while True:
        try:
            signal = fetch_unexecuted_signal()
            if signal:
                signal_id, symbol, regime, win_prob_bps = signal
                win_prob_pct = win_prob_bps / 100.0
                logging.info(f"[*] New Unexecuted Signal Found [ID {signal_id}]: {symbol} | {regime} | WinProb: {win_prob_pct:.2f}%")
                execute_onchain_trade(signal_id, symbol, regime, win_prob_bps)
            
            time.sleep(3)
        except KeyboardInterrupt:
            logging.info("[*] Service stopped manually.")
            break
        except Exception as e:
            logging.error(f"[ERROR] Main loop exception: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()

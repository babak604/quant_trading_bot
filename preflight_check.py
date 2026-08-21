import os
import sys
import json
import logging
import argparse
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

parser = argparse.ArgumentParser(description="Pre-flight check runner")
parser.add_argument("--env", default=".env", help="Path to environment file")
args = parser.parse_args()

load_dotenv(dotenv_path=args.env, override=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

RPC_URL = os.getenv("ARBITRUM_RPC_URL", os.getenv("ARBITRUM_SEPOLIA_RPC"))
KEEPER_PRIVATE_KEY = os.getenv("KEEPER_PRIVATE_KEY")
VAULT_ADDRESS = os.getenv("VAULT_ADDRESS")

def run_preflight():
    logging.info("==========================================")
    logging.info(f"   PRE-FLIGHT VERIFICATION ({args.env})   ")
    logging.info("==========================================")
    
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        if not w3.is_connected():
            logging.error("[FAIL] RPC Endpoint Unreachable.")
            sys.exit(1)
        logging.info(f"[PASS] RPC Connected | Chain ID: {w3.eth.chain_id} | Block: #{w3.eth.block_number}")
    except Exception as e:
        logging.error(f"[FAIL] Connection Error: {str(e)}")
        sys.exit(1)

    if not KEEPER_PRIVATE_KEY or "YOUR_" in KEEPER_PRIVATE_KEY:
        logging.error("[FAIL] Valid KEEPER_PRIVATE_KEY missing in environment file.")
        sys.exit(1)
        
    keeper_account = Account.from_key(KEEPER_PRIVATE_KEY)
    logging.info(f"[PASS] Keeper Account Loaded: {keeper_account.address}")

    balance_eth = float(w3.from_wei(w3.eth.get_balance(keeper_account.address), 'ether'))
    logging.info(f"[PASS] Keeper ETH Balance: {balance_eth:.4f} ETH")

    if not VAULT_ADDRESS or "YOUR_" in VAULT_ADDRESS:
        logging.error("[FAIL] Valid VAULT_ADDRESS missing in environment file.")
        sys.exit(1)

    logging.info(f"[*] Verifying Vault at Address: {VAULT_ADDRESS}")

    VAULT_ABI = json.loads("""[
        {"inputs": [], "name": "keeperNode", "outputs": [{"type": "address"}], "stateMutability": "view", "type": "function"},
        {"inputs": [], "name": "paused", "outputs": [{"type": "bool"}], "stateMutability": "view", "type": "function"},
        {"inputs": [{"type": "string"}, {"type": "string"}, {"type": "uint256"}], "name": "executeQuantSignal", "outputs": [{"type": "uint256"}], "stateMutability": "nonpayable", "type": "function"}
    ]""")

    try:
        vault = w3.eth.contract(address=Web3.to_checksum_address(VAULT_ADDRESS), abi=VAULT_ABI)
        
        onchain_keeper = vault.functions.keeperNode().call()
        if onchain_keeper.lower() != keeper_account.address.lower():
            logging.error(f"[FAIL] Keeper Mismatch! Contract: {onchain_keeper} | Wallet: {keeper_account.address}")
            sys.exit(1)
        logging.info(f"[PASS] Keeper Authorization Confirmed.")

        is_paused = vault.functions.paused().call()
        if is_paused:
            logging.error("[FAIL] Vault Circuit Breaker ACTIVE: Contract is PAUSED.")
            sys.exit(1)
        logging.info("[PASS] Vault Circuit Breaker: UNPAUSED")

    except Exception as e:
        logging.error(f"[FAIL] Contract Read Error: {str(e)}")
        sys.exit(1)

    logging.info("[*] Simulating execution via eth_call (Dry Run)...")
    try:
        simulated_result = vault.functions.executeQuantSignal("ETH/USD", "BULL_EXPANSION", 6000).call({
            'from': keeper_account.address
        })
        logging.info(f"[PASS] Dry-run Simulation Successful! Calculated Allocation: {simulated_result} units")
    except Exception as e:
        logging.error(f"[FAIL] Simulation Reverted: {str(e)}")
        sys.exit(1)

    logging.info("==========================================")
    logging.info("  [SUCCESS] PRE-FLIGHT VERIFICATION PASSED ")
    logging.info("==========================================")

if __name__ == "__main__":
    run_preflight()

import os
import sys
import logging
from dotenv import load_dotenv
from web3 import Web3

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/home/ubuntu/quant_trading_bot/keeper_balance.log')
    ]
)

# Load environment
ENV_PATH = '/home/ubuntu/quant_trading_bot/.env.mainnet'
load_dotenv(ENV_PATH, override=True)

RPC_URL = os.getenv('ARBITRUM_RPC_URL')
KEEPER_ADDRESS = os.getenv('KEEPER_ADDRESS')
ALERT_THRESHOLD_ETH = 0.0005  # Threshold trigger in ETH

def check_balance():
    if not RPC_URL or not KEEPER_ADDRESS:
        logging.error("Missing ARBITRUM_RPC_URL or KEEPER_ADDRESS in .env.mainnet")
        sys.exit(1)

    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        logging.error("Failed to connect to Arbitrum RPC endpoint.")
        sys.exit(1)

    keeper_checksum = Web3.to_checksum_address(KEEPER_ADDRESS)
    balance_wei = w3.eth.get_balance(keeper_checksum)
    balance_eth = float(w3.from_wei(balance_wei, 'ether'))

    logging.info(f"Keeper Address: {keeper_checksum}")
    logging.info(f"Current ETH Balance: {balance_eth:.6f} ETH")

    if balance_eth < ALERT_THRESHOLD_ETH:
        alert_msg = (
            f"🚨 CRITICAL LOW BALANCE WARNING 🚨\n"
            f"Keeper {keeper_checksum} balance is {balance_eth:.6f} ETH!\n"
            f"Below safety threshold of {ALERT_THRESHOLD_ETH} ETH. Refund required."
        )
        logging.warning(alert_msg)
        return False, balance_eth
    else:
        logging.info(f"[PASS] Keeper balance is healthy (>= {ALERT_THRESHOLD_ETH} ETH).")
        return True, balance_eth

if __name__ == '__main__':
    check_balance()

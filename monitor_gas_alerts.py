import os
import time
import logging
from web3 import Web3
from dotenv import load_dotenv

# Setup logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

load_dotenv()

RPC_URL = os.getenv("ARBITRUM_SEPOLIA_RPC", "https://sepolia-rollup.arbitrum.io/rpc")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
CONTRACT_ADDRESS = os.getenv("STYLUS_CONTRACT_ADDRESS")

# Gas limit threshold for alerting (default: 1,000,000 gas units)
GAS_ALERT_THRESHOLD = int(os.getenv("GAS_ALERT_THRESHOLD", 1000000))

w3 = Web3(Web3.HTTPProvider(RPC_URL))
agent_account = w3.eth.account.from_key(PRIVATE_KEY).address

def check_gas_usage(tx_hash):
    """Fetch transaction receipt and analyze gas metrics."""
    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        tx_details = w3.eth.get_transaction(tx_hash)
        
        gas_used = receipt['gasUsed']
        gas_limit = tx_details['gas']
        effective_price_gwei = w3.from_wei(receipt['effectiveGasPrice'], 'gwei')
        tx_fee_eth = w3.from_wei(gas_used * receipt['effectiveGasPrice'], 'ether')
        
        status_str = "SUCCESS" if receipt['status'] == 1 else "REVERTED"
        
        logging.info(f"[*] TX Hash: {tx_hash.hex() if isinstance(tx_hash, bytes) else tx_hash}")
        logging.info(f"    Status:         {status_str}")
        logging.info(f"    Gas Used:       {gas_used:,} / {gas_limit:,} ({gas_used/gas_limit:.1%})")
        logging.info(f"    Effective Price: {effective_price_gwei:.4f} gwei")
        logging.info(f"    Total Fee:      {tx_fee_eth:.6f} ETH")
        
        # Check against warning threshold
        if gas_used > GAS_ALERT_THRESHOLD:
            logging.warning(
                f"\n[ALERT] 🚨 HIGH GAS USAGE DETECTED!\n"
                f"        Executed Gas: {gas_used:,} units\n"
                f"        Threshold:    {GAS_ALERT_THRESHOLD:,} units\n"
                f"        Exceeded By:  {gas_used - GAS_ALERT_THRESHOLD:,} units\n"
                f"        Contract:     {receipt['to']}\n"
                f"        Explorer:     https://sepolia.arbiscan.io/tx/{tx_hash.hex() if isinstance(tx_hash, bytes) else tx_hash}\n"
            )
        else:
            logging.info(f"[OK] Gas consumption within normal parameters (<= {GAS_ALERT_THRESHOLD:,} units).\n")

    except Exception as e:
        logging.error(f"Error inspecting transaction {tx_hash}: {e}")

def monitor_agent_transactions(poll_interval=5):
    """Monitor for new agent transactions and evaluate gas consumption."""
    logging.info(f"[*] Starting Gas Alert Monitor for Agent Wallet: {agent_account}")
    logging.info(f"[*] Targeting Stylus Contract: {CONTRACT_ADDRESS}")
    logging.info(f"[*] Alert Threshold: {GAS_ALERT_THRESHOLD:,} gas units")
    
    last_processed_nonce = w3.eth.get_transaction_count(agent_account)
    
    while True:
        try:
            current_nonce = w3.eth.get_transaction_count(agent_account)
            
            # If nonce has increased, check recent blocks for the transaction
            if current_nonce > last_processed_nonce:
                latest_block = w3.eth.block_number
                found = False
                
                # Scan recent blocks for matching sender
                for b_num in range(latest_block, latest_block - 10, -1):
                    block = w3.eth.get_block(b_num, full_transactions=True)
                    for tx in block.transactions:
                        if tx['from'].lower() == agent_account.lower():
                            check_gas_usage(tx['hash'])
                            found = True
                            break
                    if found:
                        break
                
                last_processed_nonce = current_nonce
            
            time.sleep(poll_interval)
            
        except KeyboardInterrupt:
            logging.info("Stopping Gas Alert Monitor.")
            break
        except Exception as e:
            logging.error(f"Error during polling loop: {e}")
            time.sleep(poll_interval)

if __name__ == "__main__":
    monitor_agent_transactions()

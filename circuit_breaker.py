import os
import sys
import sqlite3
import logging
import requests
from dotenv import load_dotenv
from web3 import Web3

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

ENV_PATH = '/home/ubuntu/quant_trading_bot/.env.mainnet'
load_dotenv(ENV_PATH, override=True)

DB_PATH = "/home/ubuntu/quant_trading_bot/signals.db"
RPC_URL = os.getenv('ARBITRUM_RPC_URL', 'https://arb1.arbitrum.io/rpc')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

def send_alert(msg):
    logging.warning(msg)
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)

def check_circuit_breaker():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check for excessive unexecuted signal backlog (queue bottleneck guard)
    cursor.execute("SELECT COUNT(*) FROM markov_signals WHERE executed = 0")
    pending_count = cursor.fetchone()[0]
    
    if pending_count > 5:
        send_alert(f"🚨 *CIRCUIT BREAKER TRIGGERED*\nUnexecuted signal backlog high ({pending_count} pending). Check Keeper pipeline.")
    else:
        logging.info(f"[PASS] Circuit Breaker Normal. Pending signals: {pending_count}")
        
    conn.close()

if __name__ == '__main__':
    check_circuit_breaker()

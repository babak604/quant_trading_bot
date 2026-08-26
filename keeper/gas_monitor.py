import os, sys, requests
from web3 import Web3
from dotenv import load_dotenv

load_dotenv('/home/ubuntu/quant_trading_bot/.env')

PRIMARY_RPC = os.getenv("ARBITRUM_SEPOLIA_RPC", "https://sepolia-rollup.arbitrum.io/rpc")
FALLBACK_RPC = os.getenv("ARBITRUM_SEPOLIA_FALLBACK_RPC", "https://arbitrum-sepolia.publicnode.com")
KEEPER_KEY = os.getenv("KEEPER_PRIVATE_KEY", os.getenv("DEPLOYER_PRIVATE_KEY"))
WEBHOOK_URL = os.getenv("ALERT_WEBHOOK_URL", "")

# Thresholds in ETH
WARNING_THRESHOLD = 0.01   # Warn when below 0.01 ETH
CRITICAL_THRESHOLD = 0.003 # Critical alert when below 0.003 ETH

def get_web3():
    for rpc in [PRIMARY_RPC, FALLBACK_RPC]:
        try:
            w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={'timeout': 5}))
            if w3.is_connected():
                return w3
        except Exception:
            continue
    return None

def send_alert(title, description, color):
    if not WEBHOOK_URL:
        print("No WEBHOOK_URL set. Skipping alert.")
        return

    payload = {
        "embeds": [
            {
                "title": title,
                "description": description,
                "color": color,
                "fields": [
                    {"name": "Host", "value": "The1 (Ubuntu VPS)", "inline": True},
                    {"name": "Action Required", "value": "Refill keeper wallet with Sepolia ETH.", "inline": False}
                ]
            }
        ]
    }
    try:
        requests.post(WEBHOOK_URL, json=payload, timeout=5)
        print(f"Alert dispatched: {title}")
    except Exception as e:
        print(f"Failed to send alert: {e}")

def check_gas():
    w3 = get_web3()
    if not w3:
        print("RPC connection failed during gas check.")
        sys.exit(1)

    account = w3.eth.account.from_key(KEEPER_KEY)
    balance_wei = w3.eth.get_balance(account.address)
    balance_eth = float(w3.from_wei(balance_wei, "ether"))

    print(f"[{account.address}] Current ETH Balance: {balance_eth:.6f} ETH")

    if balance_eth < CRITICAL_THRESHOLD:
        send_alert(
            "🚨 CRITICAL: Keeper Gas Depleted!",
            f"Keeper wallet `{account.address}` has **{balance_eth:.6f} ETH** remaining.\nRebalance transactions will fail soon!",
            15158332 # Red
        )
    elif balance_eth < WARNING_THRESHOLD:
        send_alert(
            "⚠️ WARNING: Low Keeper Gas Balance",
            f"Keeper wallet `{account.address}` balance is low: **{balance_eth:.6f} ETH**.",
            16763904 # Orange/Yellow
        )
    else:
        print("Gas level healthy. No alerts triggered.")

if __name__ == "__main__":
    check_gas()

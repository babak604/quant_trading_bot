import os, sys
from web3 import Web3
from dotenv import load_dotenv

load_dotenv('/home/ubuntu/quant_trading_bot/.env.mainnet')

MAINNET_RPC = os.getenv("ARBITRUM_MAINNET_RPC", "https://arb1.arbitrum.io/rpc")
w3 = Web3(Web3.HTTPProvider(MAINNET_RPC))

def verify_mainnet_readiness():
    print("--- Kinetiq Arbitrum One Mainnet Readiness Verification ---")
    
    # 1. Chain ID Check
    try:
        chain_id = w3.eth.chain_id
        print(f"[{'OK' if chain_id == 42161 else 'FAIL'}] Network Chain ID: {chain_id} (Expected 42161)")
    except Exception as e:
        print(f"[FAIL] Could not connect to RPC: {e}")
        return

    # 2. Key Check
    keeper_key = os.getenv("KEEPER_PRIVATE_KEY")
    if keeper_key:
        account = w3.eth.account.from_key(keeper_key)
        balance = w3.from_wei(w3.eth.get_balance(account.address), 'ether')
        print(f"[OK] Keeper Wallet: {account.address} | Balance: {balance:.4f} ETH")
    else:
        print("[WARN] KEEPER_PRIVATE_KEY missing in .env.mainnet")

    # 3. Gas Price Readiness
    gas_price = w3.from_wei(w3.eth.gas_price, 'gwei')
    print(f"[OK] Current Mainnet Gas Price: {gas_price:.3f} Gwei")

if __name__ == "__main__":
    verify_mainnet_readiness()

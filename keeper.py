import time
import sqlite3
import datetime

DB_PATH = "/home/ubuntu/quant_trading_bot/signals.db"

def poll_and_execute():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, action, size, regime 
        FROM signals 
        WHERE status = 'PENDING' 
        ORDER BY id ASC LIMIT 1
    """)
    row = cursor.fetchone()

    if row:
        sig_id, action, size, regime = row
        print(f"[{datetime.datetime.now()}] Processing Signal #{sig_id}: {action} {size:.3f} ETH (Regime: {regime})")

        # --- ON-CHAIN EXECUTION PLACEHOLDER ---
        # tx_hash = vault_contract.functions.rebalance(action, web3.to_wei(size, 'ether')).transact()
        # --------------------------------------
        
        success = True  # Replace with actual web3 receipt check

        if success:
            cursor.execute("UPDATE signals SET status = 'EXECUTED' WHERE id = ?", (sig_id,))
            print(f"[{datetime.datetime.now()}] Signal #{sig_id} successfully executed on-chain.")
        else:
            cursor.execute("UPDATE signals SET status = 'FAILED' WHERE id = ?", (sig_id,))
            print(f"[{datetime.datetime.now()}] Signal #{sig_id} execution failed.")

        conn.commit()
    conn.close()

if __name__ == "__main__":
    print("Keeper service started. Listening for PENDING signals in signals.db...")
    while True:
        try:
            poll_and_execute()
        except Exception as e:
            print(f"Keeper error: {e}")
        time.sleep(10)

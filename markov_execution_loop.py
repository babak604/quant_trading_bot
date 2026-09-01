import os
import time
import asyncio
from dotenv import load_dotenv

load_dotenv()

TARGET_COINS = ["ETH", "SOL"]
CYCLE_INTERVAL_SECONDS = 60

async def start_autonomous_loop():
    print(f"🚀 Markov-1 Autonomous Engine Active (Assets: {', '.join(TARGET_COINS)})")
    while True:
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        print(f"[{timestamp}] MARKOV-1 CYCLE ACTIVE - Monitoring orderbooks...")
        await asyncio.sleep(CYCLE_INTERVAL_SECONDS)

if __name__ == "__main__":
    asyncio.run(start_autonomous_loop())

import re

KEEPER_SCRIPT = "/home/ubuntu/quant_trading_bot/keeper_service.py"

with open(KEEPER_SCRIPT, "r") as f:
    content = f.read()

# Update Chain ID to 421614 (Arbitrum Sepolia)
content = re.sub(r'CHAIN_ID = \d+', 'CHAIN_ID = 421614', content)

# Update RPC list to Sepolia Endpoints
new_rpcs = """RPC_ENDPOINTS = [
    os.getenv('ARBITRUM_RPC_URL', 'https://sepolia-rollup.arbitrum.io/rpc'),
    'https://arbitrum-sepolia.publicnode.com',
    'https://rpc.ankr.com/arbitrum_sepolia',
    'https://1rpc.io/sepolia/arb'
]"""

content = re.sub(r'RPC_ENDPOINTS = \[.*?\]', new_rpcs, content, flags=re.DOTALL)

with open(KEEPER_SCRIPT, "w") as f:
    f.write(content)

print("[SUCCESS] Updated keeper_service.py for Arbitrum Sepolia (Chain ID 421614).")

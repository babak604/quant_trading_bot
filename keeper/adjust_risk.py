import sys, os
from dotenv import load_dotenv

load_dotenv('/home/ubuntu/quant_trading_bot/.env')

def update_slippage_and_step(max_slippage_bps, step_size_eth):
    config_path = "/home/ubuntu/quant_trading_bot/keeper/strategy_config.py"
    with open(config_path, "r") as f:
        content = f.read()

    content = content.replace(f"MAX_SLIPPAGE_BPS = 50", f"MAX_SLIPPAGE_BPS = {max_slippage_bps}")
    content = content.replace(f"SWAP_AMOUNT_WEI = 10 * 10**18", f"SWAP_AMOUNT_WEI = {step_size_eth} * 10**18")

    with open(config_path, "w") as f:
        f.write(content)
    
    print(f"Strategy updated: Max Slippage = {max_slippage_bps} BPS ({max_slippage_bps/100}%), Step Size = {step_size_eth} ETH")

if __name__ == "__main__":
    slippage = sys.argv[1] if len(sys.argv) > 1 else "50"
    step = sys.argv[2] if len(sys.argv) > 2 else "10"
    update_slippage_and_step(int(slippage), int(step))

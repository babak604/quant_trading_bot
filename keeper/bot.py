import os, time, sys, requests
from web3 import Web3
from dotenv import load_dotenv

# Import directly from sibling module in same directory
from router_matrix import ROUTERS, TOKENS, resolve_swap_path

try:
    import sdnotify
    notifier = sdnotify.SystemdNotifier()
except Exception:
    notifier = None

load_dotenv('/home/ubuntu/quant_trading_bot/.env')

PRIMARY_RPC = os.getenv("ARBITRUM_SEPOLIA_RPC", "https://sepolia-rollup.arbitrum.io/rpc")
FALLBACK_RPC = os.getenv("ARBITRUM_SEPOLIA_FALLBACK_RPC", "https://arbitrum-sepolia.publicnode.com")
KEEPER_KEY = os.getenv("KEEPER_PRIVATE_KEY", os.getenv("DEPLOYER_PRIVATE_KEY"))
WEBHOOK_URL = os.getenv("ALERT_WEBHOOK_URL", "")

STYLUS_ENGINE_ADDR = Web3.to_checksum_address("0x6788a96aadd3e16084f61cd391611eb3C69870c7")
ROUTER_ADAPTER_ADDR = ROUTERS["adapter_contract"]
CAMELOT_ROUTER_ADDR = ROUTERS["camelot_v2"]

STATE_FILE = os.path.join(os.path.dirname(__file__), "last_execution.txt")
COOLDOWN_SECONDS = 300
MIN_ETH_BALANCE = Web3.to_wei(0.005, "ether")

STYLUS_ABI = [
    {"inputs": [], "name": "getRegime", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "get_regime", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "getWinProb", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "get_win_prob", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"}
]

ADAPTER_ABI = [
    {
        "inputs": [
            {"name": "path", "type": "address[]"},
            {"name": "amountIn", "type": "uint256"},
            {"name": "minAmountOut", "type": "uint256"}
        ],
        "name": "rebalanceMultiHop",
        "outputs": [{"name": "amountOut", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "tokenOut", "type": "address"},
            {"name": "amountIn", "type": "uint256"},
            {"name": "minAmountOut", "type": "uint256"}
        ],
        "name": "rebalance",
        "outputs": [{"name": "amountOut", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

CAMELOT_ROUTER_ABI = [
    {
        "inputs": [
            {"name": "amountIn", "type": "uint256"},
            {"name": "path", "type": "address[]"}
        ],
        "name": "getAmountsOut",
        "outputs": [{"name": "amounts", "type": "uint256[]"}],
        "stateMutability": "view", "type": "function"
    }
]

def send_alert(message):
    if not WEBHOOK_URL:
        return
    payload = {"embeds": [{"title": "⚠️ Keeper Warning", "description": message, "color": 16763904}]}
    try:
        requests.post(WEBHOOK_URL, json=payload, timeout=5)
    except Exception as e:
        print(f"Alert error: {e}")

def get_web3_provider():
    for rpc in [PRIMARY_RPC, FALLBACK_RPC]:
        try:
            w3_instance = Web3(Web3.HTTPProvider(rpc, request_kwargs={'timeout': 5}))
            if w3_instance.is_connected():
                return w3_instance, rpc
        except Exception:
            continue
    raise ConnectionError("All RPC endpoints unavailable")

w3, active_rpc = get_web3_provider()
keeper_account = w3.eth.account.from_key(KEEPER_KEY)
engine_contract = w3.eth.contract(address=STYLUS_ENGINE_ADDR, abi=STYLUS_ABI)
adapter_contract = w3.eth.contract(address=ROUTER_ADAPTER_ADDR, abi=ADAPTER_ABI)
camelot_router = w3.eth.contract(address=CAMELOT_ROUTER_ADDR, abi=CAMELOT_ROUTER_ABI)

print("--- Keeper Active ---", flush=True)
print(f"Connected RPC          : {active_rpc}", flush=True)
print(f"Monitoring Engine      : {STYLUS_ENGINE_ADDR}", flush=True)
print(f"Keeper Address         : {keeper_account.address}\n", flush=True)

def get_last_execution_time():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return float(f.read().strip())
        except Exception:
            return 0.0
    return 0.0

def set_last_execution_time(ts):
    with open(STATE_FILE, "w") as f:
        f.write(str(ts))

def query_stylus(func_name_camel, func_name_snake):
    global w3, engine_contract
    try:
        return getattr(engine_contract.functions, func_name_camel)().call()
    except Exception:
        try:
            return getattr(engine_contract.functions, func_name_snake)().call()
        except Exception as e:
            w3, rpc = get_web3_provider()
            engine_contract = w3.eth.contract(address=STYLUS_ENGINE_ADDR, abi=STYLUS_ABI)
            raise e

def execute_rebalance(win_prob):
    global w3, adapter_contract
    last_execution_time = get_last_execution_time()
    current_time = time.time()
    
    if current_time - last_execution_time < COOLDOWN_SECONDS:
        remaining = int(COOLDOWN_SECONDS - (current_time - last_execution_time))
        print(f" -> Execution locked. Cooldown active for {remaining}s...", flush=True)
        return

    eth_balance = w3.eth.get_balance(keeper_account.address)
    if eth_balance < MIN_ETH_BALANCE:
        msg = f"Low gas balance: {w3.from_wei(eth_balance, 'ether')} ETH remaining. Minimum required: 0.005 ETH."
        print(f" -> {msg}", flush=True)
        send_alert(msg)
        return

    try:
        amount_in = w3.to_wei(10, "ether")
        swap_path = resolve_swap_path("WETH", "MOR_USD")
        
        try:
            amounts = camelot_router.functions.getAmountsOut(amount_in, swap_path).call()
            expected_out = amounts[-1]
            slippage_tolerance = 0.005
            min_amount_out = int(expected_out * (1 - slippage_tolerance))
            print(f" -> Live Multi-Hop Route Output ({len(swap_path)} tokens): {expected_out} wei | minOut: {min_amount_out}", flush=True)
        except Exception:
            min_amount_out = int(amount_in * 0.995)
            print(f" -> Direct route quote fallback minOut: {min_amount_out}", flush=True)

        nonce = w3.eth.get_transaction_count(keeper_account.address)
        
        if len(swap_path) > 2:
            tx = adapter_contract.functions.rebalanceMultiHop(
                swap_path,
                amount_in,
                min_amount_out
            ).build_transaction({
                "nonce": nonce,
                "from": keeper_account.address,
                "gas": 600000,
                "maxFeePerGas": w3.to_wei("0.1", "gwei"),
                "maxPriorityFeePerGas": w3.to_wei("0.01", "gwei"),
                "chainId": 421614
            })
        else:
            tx = adapter_contract.functions.rebalance(
                swap_path[-1],
                amount_in,
                min_amount_out
            ).build_transaction({
                "nonce": nonce,
                "from": keeper_account.address,
                "gas": 500000,
                "maxFeePerGas": w3.to_wei("0.1", "gwei"),
                "maxPriorityFeePerGas": w3.to_wei("0.01", "gwei"),
                "chainId": 421614
            })

        signed_tx = w3.eth.account.sign_transaction(tx, KEEPER_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(f" -> Multi-Token Rebalance Tx Sent: {tx_hash.hex()}", flush=True)
        set_last_execution_time(current_time)
        
    except Exception as e:
        print(f" -> Rebalance Execution Error: {e}", flush=True)

def check_and_execute():
    try:
        if notifier:
            notifier.notify("WATCHDOG=1")

        regime = query_stylus("getRegime", "get_regime")
        win_prob = query_stylus("getWinProb", "get_win_prob")
        
        regime_names = {0: "Bear", 1: "Sideways", 2: "Bull"}
        prob_pct = win_prob / 100.0

        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Regime: {regime_names.get(regime, 'Unknown')} ({regime}) | Win Prob: {prob_pct:.2f}%", flush=True)

        if regime >= 1 and win_prob > 5500:
            print(" -> Signal condition satisfied! Executing multi-token rebalance...", flush=True)
            execute_rebalance(win_prob)
        else:
            print(" -> Signal conditions hold. Standing by.", flush=True)

    except Exception as e:
        print(f"Error querying contract: {e}", flush=True)

if __name__ == "__main__":
    while True:
        check_and_execute()
        time.sleep(30)

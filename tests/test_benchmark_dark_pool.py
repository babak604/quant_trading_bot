import os
import time
import json
import subprocess
from datetime import datetime, timezone
import requests
import pytest
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

TEST_PORT = 8005
FASTAPI_ENDPOINT = f"http://127.0.0.1:{TEST_PORT}/api/v1/agent/parse-dark-pool-intent"
RPC_URL = os.getenv("ARBITRUM_SEPOLIA_RPC", "https://sepolia-rollup.arbitrum.io/rpc")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
CONTRACT_ADDRESS = os.getenv("STYLUS_CONTRACT_ADDRESS")
LOG_FILE_PATH = "benchmark_metrics.json"

STYLUS_ABI = [
    {
        "type": "function",
        "name": "register_order_commitment",
        "inputs": [
            {"name": "order_hash", "type": "bytes32"},
            {"name": "volume", "type": "uint256"}
        ],
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "nonpayable"
    }
]

def append_metrics_to_json(metric_data: dict, file_path: str = LOG_FILE_PATH):
    logs = []
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                logs = json.load(f)
        except json.JSONDecodeError:
            logs = []
    logs.append(metric_data)
    with open(file_path, "w") as f:
        json.dump(logs, f, indent=2)
    print(f"\n[+] Metrics appended to {file_path}")

@pytest.fixture(scope="module", autouse=True)
def start_fastapi_server():
    """Spin up an isolated FastAPI server process for testing."""
    proc = subprocess.Popen(
        ["uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(TEST_PORT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(2)  # Allow server time to bind port
    yield proc
    proc.terminate()
    proc.wait()

@pytest.fixture
def setup_web3():
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    account = w3.eth.account.from_key(PRIVATE_KEY)
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(CONTRACT_ADDRESS), 
        abi=STYLUS_ABI
    )
    return w3, account, contract

def test_e2e_dark_pool_latency_benchmark(setup_web3):
    w3, account, contract = setup_web3

    # --- Phase 1: FastAPI Intent Parsing ---
    prompt_payload = {
        "user_prompt": "Benchmark dark pool commitment execution for 100,000 CAD",
        "agent_session_key": account.address,
        "volume_cad": 100000.0
    }

    t0 = time.perf_counter()
    response = requests.post(FASTAPI_ENDPOINT, json=prompt_payload, timeout=10)
    t1 = time.perf_counter()

    assert response.status_code == 200, f"FastAPI request failed: {response.text}"
    parsed_data = response.json()
    
    order_hash_hex = parsed_data["order_hash"]
    volume_wei = int(parsed_data["volume_wei"])
    parsing_latency_ms = round((t1 - t0) * 1000, 2)

    # --- Phase 2: Tx Build & Sign ---
    order_hash_bytes = bytes.fromhex(order_hash_hex.replace("0x", ""))
    latest_block = w3.eth.get_block("latest")
    base_fee = latest_block.get("baseFeePerGas", w3.eth.gas_price)
    priority_fee = w3.to_wei(0.1, "gwei")

    tx = contract.functions.register_order_commitment(order_hash_bytes, volume_wei).build_transaction({
        "chainId": 421614,
        "gas": 1500000,
        "maxFeePerGas": int(base_fee * 1.35) + priority_fee,
        "maxPriorityFeePerGas": priority_fee,
        "nonce": w3.eth.get_transaction_count(account.address),
    })

    signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    signing_latency_ms = round((time.perf_counter() - t1) * 1000, 2)

    # --- Phase 3: Broadcast & Confirmation ---
    t2 = time.perf_counter()
    tx_hash = w3.eth.send_raw_transaction(
        signed_tx.raw_transaction if hasattr(signed_tx, "raw_transaction") else signed_tx.rawTransaction
    )
    
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    t3 = time.perf_counter()

    confirmation_latency_s = round(t3 - t2, 2)
    total_e2e_latency_s = round(t3 - t0, 2)

    assert receipt["status"] == 1, f"On-chain transaction reverted: {tx_hash.hex()}"

    metrics_payload = {
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "test_name": "test_e2e_dark_pool_latency_benchmark",
        "contract_address": CONTRACT_ADDRESS,
        "tx_hash": tx_hash.hex(),
        "block_number": receipt["blockNumber"],
        "gas_used": receipt["gasUsed"],
        "latency_metrics": {
            "fastapi_parsing_ms": parsing_latency_ms,
            "tx_signing_ms": signing_latency_ms,
            "onchain_confirmation_s": confirmation_latency_s,
            "total_e2e_latency_s": total_e2e_latency_s
        }
    }

    append_metrics_to_json(metrics_payload)

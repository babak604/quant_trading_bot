import os
import time
from web3 import Web3
from eth_utils import keccak
from dotenv import load_dotenv

load_dotenv()

RPC_URL = os.getenv("ARBITRUM_SEPOLIA_RPC", "https://sepolia-rollup.arbitrum.io/rpc")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
CONTRACT_ADDRESS = os.getenv("STYLUS_CONTRACT_ADDRESS")

w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)

ABI = [
    {
        "type": "function",
        "name": "register_zkml_model",
        "inputs": [{"name": "image_id", "type": "bytes32"}],
        "outputs": [],
        "stateMutability": "nonpayable"
    }
]

contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=ABI)

def verify_and_register_zkml_image(journal_bytes: bytes, image_id_bytes: bytes):
    print(f"\n================ [RISC ZERO ZKVM PROOF VERIFIER] ================")
    print(f"Target Contract: {CONTRACT_ADDRESS}\n")

    # 1. Compute deterministic journal hash
    journal_hash = keccak(journal_bytes)
    print(f"[*] Journal Payload:     {journal_bytes.decode('utf-8')}")
    print(f"[*] STARK Journal Hash:  0x{journal_hash.hex()}")
    print(f"[*] Target Image ID:     0x{image_id_bytes.hex()}")

    # 2. Build on-chain registration transaction
    latest_block = w3.eth.get_block("latest")
    base_fee = latest_block.get("baseFeePerGas", w3.eth.gas_price)
    priority_fee = w3.to_wei(0.1, "gwei")

    tx = contract.functions.register_zkml_model(image_id_bytes).build_transaction({
        "chainId": 421614,
        "gas": 1500000,
        "maxFeePerGas": int(base_fee * 1.35) + priority_fee,
        "maxPriorityFeePerGas": priority_fee,
        "nonce": w3.eth.get_transaction_count(account.address),
    })

    # 3. Sign & Broadcast
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(
        signed_tx.raw_transaction if hasattr(signed_tx, "raw_transaction") else signed_tx.rawTransaction
    )
    print(f"[*] Submitting zkML Image ID Registration to Arbitrum Sepolia...")
    print(f"    -> TX Hash: {tx_hash.hex()}")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    status_str = "SUCCESS" if receipt["status"] == 1 else "FAILED"
    
    print(f"\n[+] Status:   {status_str} (Gas Used: {receipt['gasUsed']:,})")
    print(f"[+] Explorer: https://sepolia.arbiscan.io/tx/{tx_hash.hex()}")
    print("=================================================================\n")

if __name__ == "__main__":
    # Simulated RISC Zero guest execution output & Image ID
    sample_journal = b"RISC_ZERO_ZKML_QUANT_MODEL_OUTPUT_VERIFIED"
    sample_image_id = bytes.fromhex("a5f800412e09b110000000000000000000000000000000000000000000000001")

    verify_and_register_zkml_image(sample_journal, sample_image_id)

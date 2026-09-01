import time
import requests
import os

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://fastapi-intent-parser:8000")
used_nullifiers = set()

def verify_proof_and_nullifier(intent_data):
    nullifier = intent_data.get("zk_commitment")
    amount = intent_data.get("amount", 0)

    if not nullifier or nullifier in used_nullifiers:
        print(f"[ZKML Verifier] REJECTED: Replay attack or duplicate nullifier ({nullifier})")
        return False

    # Simulate Groth16 proof check
    time.sleep(0.04)
    used_nullifiers.add(nullifier)
    print(f"[ZKML Verifier] SUCCESS: Valid proof for nullifier {nullifier[:10]}... | Amount: {amount}")
    return True

if __name__ == "__main__":
    print("[ZKML Proof Verifier] Online with Poseidon Nullifier Tracking...")
    while True:
        try:
            res = requests.get(f"{FASTAPI_URL}/", timeout=2).json()
        except Exception:
            pass
        time.sleep(5)

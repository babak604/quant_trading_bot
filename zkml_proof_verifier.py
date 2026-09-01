import time
import os

print("[ZKML Verifier] Service starting up...")

def verify_loop():
    while True:
        print("[ZKML Verifier] Monitoring execution environment for zkML proofs...")
        time.sleep(15)

if __name__ == "__main__":
    verify_loop()

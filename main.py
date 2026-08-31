from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from eth_utils import keccak
import time

app = FastAPI(title="AgentFi Intent Parser")

class DarkPoolIntentRequest(BaseModel):
    pair: str = "ETH-USDC"
    action: str = "BUY"
    amount: float = 10.0
    max_slippage: float = 0.005
    user_address: str = "0xdf95321890333246830d128493820a2f20a0192a"

@app.get("/")
def health_check():
    return {"status": "ok", "service": "fastapi-intent-parser"}

@app.post("/api/v1/agent/parse-dark-pool-intent")
def parse_dark_pool_intent(payload: DarkPoolIntentRequest):
    try:
        raw_str = f"{payload.pair}_{payload.action}_{payload.amount}_{time.time()}"
        order_hash = keccak(text=raw_str).hex()
        amount_wei = int(payload.amount * 1e18)
        
        return {
            "status": "SUCCESS",
            "order_hash": order_hash,
            "volume_wei": amount_wei,
            "parsed_intent": {
                "pair": payload.pair,
                "action": payload.action,
                "amount": payload.amount,
                "user_address": payload.user_address
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

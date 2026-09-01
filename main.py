import os
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
from agent_session_verifier import ZKDarkPoolMatcher, SessionKeyPermission

app = FastAPI(title="AgentFi FastAPI Intent Parser", version="1.0.0")

INTENT_LOGS = [
    {"intent_id": 101, "timestamp": "2026-08-25 11:54:01", "pair": "ETH/CAD", "amount": 25.5, "status": "SETTLED"},
    {"intent_id": 102, "timestamp": "2026-08-25 12:10:45", "pair": "SOL/CAD", "amount": 140.0, "status": "PENDING"}
]

matcher = ZKDarkPoolMatcher()

@app.get("/")
def read_root():
    df = pd.DataFrame(INTENT_LOGS)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return {"status": "active", "total_logs": len(df)}

class IntentPayload(BaseModel):
    account_address: str
    session_validator: str
    valid_until: int
    signature: str
    pair: str
    amount: float
    side: str
    secret_salt: str

@app.post("/parse-intent")
def parse_intent(payload: IntentPayload):
    try:
        permission = SessionKeyPermission(
            account_address=payload.account_address,
            session_validator=payload.session_validator,
            valid_until=payload.valid_until
        )
        
        if not matcher.verify_session_key(permission, payload.signature):
            raise HTTPException(status_code=400, detail="Invalid Session Key or Signature")
            
        commitment = matcher.generate_zk_commitment(
            pair=payload.pair,
            amount=payload.amount,
            side=payload.side,
            secret_salt=payload.secret_salt
        )
        
        return {
            "status": "ACCEPTED",
            "zk_commitment": commitment,
            "stylus_target": os.getenv("STYLUS_CONTRACT_ADDRESS", "0x2f615143c5ea1db83834ea4508528f199ab9c462")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)

import os
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from eth_utils import keccak
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AgentFi Dark Pool Bridge", version="1.0.0")

class DarkPoolIntentRequest(BaseModel):
    user_prompt: str
    agent_session_key: str
    volume_cad: float

@app.get("/")
def health_check():
    return {"status": "ok"}

@app.post("/api/v1/agent/parse-dark-pool-intent")
async def parse_dark_pool_intent(req: DarkPoolIntentRequest):
    try:
        raw_commitment = f"{req.user_prompt}:{req.agent_session_key}:{req.volume_cad}"
        order_hash = keccak(text=raw_commitment).hex()
        volume_wei = int(req.volume_cad * 10**18)
        
        return {
            "status": "success",
            "order_hash": f"0x{order_hash}",
            "volume_wei": volume_wei,
            "session_key": req.agent_session_key,
            "target_contract": os.getenv("STYLUS_CONTRACT_ADDRESS")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

# ==========================================
# AgentFi Swarm Trading Endpoint Extension
# ==========================================
from swarm_orchestration import SentimentAgent, RiskAgent, DarkPoolMatcherAgent

@app.post("/api/v1/agent/swarm-trade")
async def execute_swarm_trade(pair: str = "ETH-USDC"):
    sentiment = SentimentAgent()
    risk = RiskAgent()

    sig = sentiment.generate_signal(pair)
    if not risk.validate_intent(sig):
        return {"status": "rejected", "reason": "Risk limits exceeded"}

    return {
        "status": "approved",
        "action": sig["action"],
        "volume": sig["volume"],
        "confidence": sig["confidence"],
        "timestamp": time.time()
    }

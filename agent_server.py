import os
import json
import struct
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from web3 import Web3

app = FastAPI(title="mor.money AgentFi Intent Execution Bridge")

RPC_URL = os.getenv("ARBITRUM_RPC_URL", "https://sepolia-rollup.arbitrum.io/rpc")
STYLUS_CONTRACT_ADDRESS = os.getenv("STYLUS_CONTRACT_ADDRESS", "0x0000000000000000000000000000000000000000")

w3 = Web3(Web3.HTTPProvider(RPC_URL))

class NaturalLanguageIntent(BaseModel):
    user_prompt: str
    agent_session_key: str
    max_capital_cad: float

class SBEBinaryPacket(BaseModel):
    venue_address: str
    max_slippage_bps: int
    sbe_hex_payload: str

def parse_intent_to_sbe(prompt: str, max_capital: float) -> SBEBinaryPacket:
    venue = "0x1111111111111111111111111111111111111111"
    slippage_bps = 15
    
    if "dark pool" in prompt.lower() or max_capital >= 100000:
        venue = "0x2222222222222222222222222222222222222222"
        slippage_bps = 5
        
    sbe_payload = struct.pack("<HHQH", 1, 101, int(max_capital * 100), slippage_bps)
    
    return SBEBinaryPacket(
        venue_address=venue,
        max_slippage_bps=slippage_bps,
        sbe_hex_payload=sbe_payload.hex()
    )

@app.post("/api/v1/agent/parse-and-execute")
async def process_agent_intent(intent: NaturalLanguageIntent):
    try:
        binary_packet = parse_intent_to_sbe(intent.user_prompt, intent.max_capital_cad)
        return {
            "status": "SUCCESS",
            "prompt": intent.user_prompt,
            "session_key": intent.agent_session_key,
            "execution_target": binary_packet.venue_address,
            "slippage_bps": binary_packet.max_slippage_bps,
            "sbe_binary_hex": f"0x{binary_packet.sbe_hex_payload}",
            "stylus_wasm_route": STYLUS_CONTRACT_ADDRESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

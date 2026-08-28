# mor.money FIX Protocol & REST Middleware Bridge
import json
import time

class FIXOrderBridge:
    def __init__(self, sender_comp_id="ITG_DESK", target_comp_id="MOR_MONEY"):
        self.sender_comp_id = sender_comp_id
        self.target_comp_id = target_comp_id

    def parse_fix_new_order_single(self, fix_msg: str) -> dict:
        """Parses FIX 4.4 NewOrderSingle (35=D) into mor.money execution parameters."""
        fields = {}
        for tag_value in fix_msg.split("\x01"):
            if "=" in tag_value:
                k, v = tag_value.split("=", 1)
                fields[k] = v
                
        # FIX Tags: 55=Symbol, 54=Side (1=Buy, 2=Sell), 38=OrderQty, 44=Price
        symbol = fields.get("55", "WETH-USDC")
        tokens = symbol.split("-")
        
        return {
            "cl_ord_id": fields.get("11", f"ORD_{int(time.time())}"),
            "side": "BUY" if fields.get("54") == "1" else "SELL",
            "token_in": tokens[0] if fields.get("54") == "1" else tokens[1],
            "token_out": tokens[1] if fields.get("54") == "1" else tokens[0],
            "amount": float(fields.get("38", 1.0)),
            "fix_sender": fields.get("49", self.sender_comp_id)
        }

    def generate_fix_execution_report(self, cl_ord_id: str, status: str, fill_price: float) -> str:
        """Generates FIX 4.4 ExecutionReport (35=8) response back to institutional OMS."""
        # Tag 39: 2=Filled, 8=Rejected
        ord_status = "2" if status == "SUCCESS" else "8"
        fix_body = f"8=FIX.4.4\x0135=8\x0111={cl_ord_id}\x0139={ord_status}\x016={fill_price}\x01"
        return fix_body

if __name__ == "__main__":
    bridge = FIXOrderBridge()
    sample_fix = "8=FIX.4.4\x0135=D\x0111=ORD_9912\x0155=WETH-USDC\x0154=1\x0138=10.5\x0149=VIRTU_DESK\x01"
    parsed = bridge.parse_fix_new_order_single(sample_fix)
    print(f"[OK] Parsed FIX Order: {parsed}")

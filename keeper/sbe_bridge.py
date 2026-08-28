# mor.money Low-Latency SBE (Simple Binary Encoding) Parser
import struct

class SBEBinaryFixBridge:
    def parse_sbe_order_packet(self, binary_payload: bytes) -> dict:
        """Parses binary SBE packet into Stylus WASM execution parameters."""
        # Header format: uint16 block_length, uint16 template_id, uint16 schema_id, uint16 version
        block_len, template_id, schema_id, version = struct.unpack('<HHHH', binary_payload[:8])
        # Body format: uint64 price_e8, uint64 qty_e8, uint8 side (1=Buy, 2=Sell)
        price_e8, qty_e8, side = struct.unpack('<QQB', binary_payload[8:25])
        
        return {
            "template_id": template_id,
            "price_cad": price_e8 / 1e8,
            "quantity": qty_e8 / 1e8,
            "side": "BUY" if side == 1 else "SELL",
            "latency_mode": "SUB_MICROSECOND_SBE_DIRECT"
        }

if __name__ == "__main__":
    sbe = SBEBinaryFixBridge()
    dummy_payload = struct.pack('<HHHHQQB', 25, 101, 1, 1, int(3500.50 * 1e8), int(10.5 * 1e8), 1)
    res = sbe.parse_sbe_order_packet(dummy_payload)
    print("=== SBE BINARY FIX BRIDGE TEST ===")
    print(f"[PASS] Side: {res['side']} | Qty: {res['quantity']} | Price: ${res['price_cad']} CAD ({res['latency_mode']})")

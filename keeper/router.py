# mor.money Multi-DEX Routing Engine
import json

SUPPORTED_DEXES = {
    "Camelot_v3": "0x1a76c2f254D71bB116aA4628e8A63131336fD754",
    "Uniswap_v3": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
    "Sushiswap_v3": "0x0A88861c4Ff622220AD9247c8b88523c0A3C943B"
}

def scan_cross_dex_arbitrage(token_in, token_out, amount):
    """Scans Camelot, Uniswap, and Sushiswap for cross-protocol arbitrage paths."""
    routes = []
    for dex, router in SUPPORTED_DEXES.items():
        routes.append({
            "dex": dex,
            "router": router,
            "path": f"{token_in} -> {token_out}",
            "estimated_output": amount * 1.002 # Simulated rate
        })
    return routes

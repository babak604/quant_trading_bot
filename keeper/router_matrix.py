from web3 import Web3

# Arbitrum Sepolia Contract Addresses
ROUTERS = {
    "camelot_v2": Web3.to_checksum_address("0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506"),
    "camelot_v3": Web3.to_checksum_address("0x1a84f33194B4E8C2224A8eF6b080B1E627A59891"),
    "adapter_contract": Web3.to_checksum_address("0x7C8068b7bF2Bf8F6e7c3cd4aB6ddd49a2d2ADC1b")
}

TOKENS = {
    "WETH": Web3.to_checksum_address("0x980B62Da83eFf3D4576C647993b0c1D7faf17c73"),
    "USDC": Web3.to_checksum_address("0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d"),
    "USDT": Web3.to_checksum_address("0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"),
    "MOR_USD": Web3.to_checksum_address("0x7C8068b7bF2Bf8F6e7c3cd4aB6ddd49a2d2ADC1b")
}

# Multi-Hop Route Definitions
ROUTE_PATHS = {
    ("WETH", "MOR_USD"): [TOKENS["WETH"], TOKENS["MOR_USD"]],
    ("WETH", "USDC", "MOR_USD"): [TOKENS["WETH"], TOKENS["USDC"], TOKENS["MOR_USD"]],
    ("MOR_USD", "WETH"): [TOKENS["MOR_USD"], TOKENS["WETH"]],
    ("MOR_USD", "USDC", "WETH"): [TOKENS["MOR_USD"], TOKENS["USDC"], TOKENS["WETH"]]
}

def resolve_swap_path(token_in_key, token_out_key, intermediate_key=None):
    """
    Returns the array of checksummed token addresses for multi-hop DEX swaps.
    """
    if intermediate_key:
        key = (token_in_key, intermediate_key, token_out_key)
    else:
        key = (token_in_key, token_out_key)
        
    if key in ROUTE_PATHS:
        return ROUTE_PATHS[key]
    
    # Default direct path fallback
    return [TOKENS.get(token_in_key, Web3.to_checksum_address(token_in_key)), 
            TOKENS.get(token_out_key, Web3.to_checksum_address(token_out_key))]

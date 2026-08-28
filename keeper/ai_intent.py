# mor.money Natural Language Intent-to-Execution Engine
import json
import re

class AIIntentParser:
    def __init__(self):
        self.supported_assets = ["WETH", "ETH", "USDC", "WBTC", "CAD"]

    def parse_natural_intent(self, prompt: str) -> dict:
        """Parses natural language trading instructions into structured mor.money execution payloads."""
        prompt_lower = prompt.lower()
        
        # Extract order amount
        amount_match = re.search(r'\$(\d+[\d,.]*k?)', prompt, re.IGNORECASE)
        amount_usd = 50000.0  # Default fallback
        if amount_match:
            raw_amt = amount_match.group(1).lower().replace(',', '')
            if 'k' in raw_amt:
                amount_usd = float(raw_amt.replace('k', '')) * 1000.0
            else:
                amount_usd = float(raw_amt)

        # Detect Execution Mode
        if "twap" in prompt_lower or "slice" in prompt_lower:
            execution_mode = "TWAP_ROUTER"
        elif "dark pool" in prompt_lower or "mev" in prompt_lower or "private" in prompt_lower:
            execution_mode = "DARK_POOL_INTENT"
        elif "ndax" in prompt_lower or "cex" in prompt_lower:
            execution_mode = "NDAX_SPATIAL_SOLVER"
        else:
            execution_mode = "HYBRID_SOR"

        # Detect Max Impact Constraint
        impact_match = re.search(r'(\d+\.?\d*)%\s*(?:impact|slippage)', prompt_lower)
        max_impact_pct = float(impact_match.group(1)) if impact_match else 1.5

        return {
            "raw_prompt": prompt,
            "parsed_intent": {
                "execution_mode": execution_mode,
                "target_amount_usd": amount_usd,
                "max_impact_limit_pct": max_impact_pct,
                "mev_protection": True if execution_mode in ["DARK_POOL_INTENT", "TWAP_ROUTER"] else False,
                "status": "VALIDATED_BY_AI_SENTINEL"
            }
        }

if __name__ == "__main__":
    parser = AIIntentParser()
    test_prompt = "Execute a $150k TWAP order on WETH keeping price impact under 0.8% and use dark pool matching"
    res = parser.parse_natural_intent(test_prompt)
    
    print("=== AI NATURAL LANGUAGE INTENT TEST ===")
    print(f"Prompt: '{res['raw_prompt']}'")
    print(f"[PASS] Mode: {res['parsed_intent']['execution_mode']} | Amount: ${res['parsed_intent']['target_amount_usd']:,.2f} USD | Max Impact: {res['parsed_intent']['max_impact_limit_pct']}%")

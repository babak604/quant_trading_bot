# mor.money Public Yield Vault Auto-Compounder & Fee Collector
import time
import math

class YieldVaultAutoCompounder:
    def __init__(self, treasury_address: str = "0x6857aFDB82fFCf0bd3e12A1e2FD80B5936cEA67f"):
        self.treasury_address = treasury_address
        self.management_fee_annual_pct = 0.02  # 2% annual management fee
        self.performance_fee_pct = 0.20        # 20% performance fee on net yield
        self.min_compound_yield_usd = 25.0     # Min yield threshold before triggering harvest gas spend

    def calculate_compound_harvest(self, total_deposits_usd: float, unharvested_yield_usd: float, days_since_last_harvest: float) -> dict:
        """
        Calculates net vault auto-compounding harvest, protocol 2/20 fee deductions,
        and net APY impact for LP vault depositors.
        """
        if unharvested_yield_usd < self.min_compound_yield_usd:
            return {
                "status": "SKIP_HARVEST",
                "reason": f"Yield (${unharvested_yield_usd:.2f}) below threshold (${self.min_compound_yield_usd:.2f})",
                "net_reinvested_usd": 0.0,
                "protocol_fee_usd": 0.0
            }

        # 1. Calculate pro-rata annual management fee deduction
        annual_mgmt_fee = total_deposits_usd * self.management_fee_annual_pct
        period_mgmt_fee = annual_mgmt_fee * (days_since_last_harvest / 365.0)

        # 2. Calculate performance fee on gross harvest yield
        performance_fee = unharvested_yield_usd * self.performance_fee_pct

        # 3. Total protocol fee captured
        total_protocol_fee = period_mgmt_fee + performance_fee
        net_yield_to_reinvest = max(0.0, unharvested_yield_usd - total_protocol_fee)

        # 4. Updated vault total value locked (TVL) post-compound
        new_tvl_usd = total_deposits_usd + net_yield_to_reinvest

        # 5. Projected Net APY calculation
        annualized_yield_rate = (unharvested_yield_usd / total_deposits_usd) * (365.0 / max(1.0, days_since_last_harvest))
        net_annualized_apy = max(0.0, annualized_yield_rate * (1.0 - self.performance_fee_pct) - self.management_fee_annual_pct)

        return {
            "status": "HARVEST_EXECUTED",
            "treasury_address": self.treasury_address,
            "gross_harvest_yield_usd": round(unharvested_yield_usd, 2),
            "management_fee_usd": round(period_mgmt_fee, 2),
            "performance_fee_usd": round(performance_fee, 2),
            "total_protocol_fee_usd": round(total_protocol_fee, 2),
            "net_reinvested_usd": round(net_yield_to_reinvest, 2),
            "previous_tvl_usd": round(total_deposits_usd, 2),
            "new_tvl_usd": round(new_tvl_usd, 2),
            "projected_net_apy": f"{net_annualized_apy * 100:.2f}%",
            "execution": "BALANCER_V2_FLASH_REBALANCE"
        }

if __name__ == "__main__":
    compounder = YieldVaultAutoCompounder()
    
    # Simulate a vault with $500,000 TVL that generated $1,200 in yield over 3 days
    result = compounder.calculate_compound_harvest(
        total_deposits_usd=500000.0, 
        unharvested_yield_usd=1200.0, 
        days_since_last_harvest=3.0
    )
    
    print("=== YIELD VAULT AUTO-COMPOUNDER TEST ===")
    print(f"Status: {result['status']}")
    print(f"Gross Yield: ${result['gross_harvest_yield_usd']} USD")
    print(f"Protocol Fee (2/20): ${result['total_protocol_fee_usd']} USD -> Sent to {result['treasury_address']}")
    print(f"Net Reinvested: ${result['net_reinvested_usd']} USD")
    print(f"New Vault TVL: ${result['new_tvl_usd']} USD")
    print(f"Projected Net APY: {result['projected_net_apy']}")

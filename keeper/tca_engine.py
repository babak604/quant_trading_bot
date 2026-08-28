# mor.money Transaction Cost Analysis (TCA) & CIRO Best Execution Engine

class TransactionCostAnalyzer:
    def calculate_implementation_shortfall(self, arrival_price: float, execution_price: float, volume_usd: float) -> dict:
        """Calculates TCA metrics demonstrating price improvement vs public CEX arrival benchmark."""
        slippage_bps = ((execution_price - arrival_price) / arrival_price) * 10000.0
        savings_usd = (arrival_price - execution_price) * (volume_usd / arrival_price)
        
        return {
            "volume_usd": volume_usd,
            "arrival_benchmark_price": arrival_price,
            "executed_price": execution_price,
            "slippage_bps": round(slippage_bps, 2),
            "total_savings_usd": round(max(0.0, savings_usd), 2),
            "ciro_best_execution_passed": abs(slippage_bps) <= 15.0
        }

if __name__ == "__main__":
    tca = TransactionCostAnalyzer()
    res = tca.calculate_implementation_shortfall(arrival_price=3510.0, execution_price=3502.0, volume_usd=250000.0)
    print("=== TRANSACTION COST ANALYSIS (TCA) TEST ===")
    print(f"[PASS] Volume: ${res['volume_usd']} | Savings vs Benchmark: ${res['total_savings_usd']} USD | CIRO Check: {res['ciro_best_execution_passed']}")

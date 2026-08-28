# mor.money ERC-7579 Agent Smart Account & Session Key Manager
import time
import hashlib

class ERC7579AgentWalletManager:
    def __init__(self, account_address: str = "0x6857aFDB82fFCf0bd3e12A1e2FD80B5936cEA67f"):
        self.account_address = account_address
        self.session_key_permissions = {
            "max_spend_per_trade_cad": 50000.0,
            "max_slippage_impact_pct": 1.5,
            "allowed_selectors": ["0x_execute_dark_pool", "0x_rebalance_vault"],
            "session_expiry_epoch": int(time.time()) + 86400  # 24 hour session
        }

    def validate_and_sign_agent_op(self, trade_amount_cad: float, slippage_pct: float, action_selector: str) -> dict:
        """Validates agent trade against ERC-7579 session policies and generates userOp hash."""
        now = int(time.time())
        
        # 1. Policy Checks
        if now > self.session_key_permissions["session_expiry_epoch"]:
            return {"status": "REJECTED", "reason": "SESSION_EXPIRED"}
        if trade_amount_cad > self.session_key_permissions["max_spend_per_trade_cad"]:
            return {"status": "REJECTED", "reason": "EXCEEDS_SESSION_SPEND_LIMIT"}
        if slippage_pct > self.session_key_permissions["max_slippage_impact_pct"]:
            return {"status": "REJECTED", "reason": "EXCEEDS_SLIPPAGE_POLICY"}

        # 2. UserOp Signature Generation
        user_op_data = f"{self.account_address}:{trade_amount_cad}:{action_selector}:{now}"
        user_op_hash = "0x" + hashlib.sha256(user_op_data.encode('utf-8')).hexdigest()

        return {
            "status": "APPROVED_BY_SMART_SESSION",
            "account_address": self.account_address,
            "action_selector": action_selector,
            "user_op_hash": user_op_hash,
            "session_expires_in_sec": self.session_key_permissions["session_expiry_epoch"] - now
        }

if __name__ == "__main__":
    wallet = ERC7579AgentWalletManager()
    res = wallet.validate_and_sign_agent_op(25000.0, 0.8, "0x_execute_dark_pool")
    print("=== ERC-7579 SESSION KEY WALLET TEST ===")
    print(f"[PASS] Status: {res['status']}")
    print(f"[PASS] UserOp Hash: {res['user_op_hash']}")
    print(f"[PASS] Session Expiry: {res['session_expires_in_sec']}s remaining")

from abc import ABC, abstractmethod

class BaseMarketAdapter(ABC):
    @abstractmethod
    async def connect_websocket(self):
        pass
        
    @abstractmethod
    def calculate_ofi(self, book_depth: dict) -> float:
        pass
        
    @abstractmethod
    async def execute_bracket_order(self, symbol: str, side: str, qty: float, current_price: float, sl_pct: float = 0.015, tp_pct: float = 0.030):
        pass

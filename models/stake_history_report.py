from dataclasses import dataclass
from typing import Dict, List


@dataclass
class StakeHistoryReport:
    gambler_id: int
    total_transactions: int
    opening_balance: float
    closing_balance: float
    net_change: float
    by_type: Dict[str, int]
    transactions: List[dict]

    def to_dict(self) -> dict:
        return {
            "gambler_id": self.gambler_id,
            "total_transactions": self.total_transactions,
            "opening_balance": self.opening_balance,
            "closing_balance": self.closing_balance,
            "net_change": self.net_change,
            "by_type": self.by_type,
            "transactions": self.transactions,
        }

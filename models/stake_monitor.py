from dataclasses import dataclass
from typing import Dict, List


@dataclass
class StakeMonitor:
    gambler_id: int
    current_balance: float
    peak_balance: float
    low_balance: float
    change_count: int
    volatility: float
    balance_history: List[float]

    @staticmethod
    def from_balances(gambler_id: int, balances: List[float]) -> "StakeMonitor":
        if not balances:
            return StakeMonitor(gambler_id, 0.0, 0.0, 0.0, 0, 0.0, [])

        deltas = [abs(balances[i] - balances[i - 1]) for i in range(1, len(balances))]
        volatility = (sum(deltas) / len(deltas)) if deltas else 0.0

        return StakeMonitor(
            gambler_id=gambler_id,
            current_balance=balances[-1],
            peak_balance=max(balances),
            low_balance=min(balances),
            change_count=max(len(balances) - 1, 0),
            volatility=volatility,
            balance_history=balances,
        )

    def to_dict(self) -> Dict[str, float]:
        return {
            "gambler_id": self.gambler_id,
            "current_balance": self.current_balance,
            "peak_balance": self.peak_balance,
            "low_balance": self.low_balance,
            "change_count": self.change_count,
            "volatility": self.volatility,
            "balance_history": self.balance_history,
        }

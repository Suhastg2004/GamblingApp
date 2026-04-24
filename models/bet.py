from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Bet:
    bet_id: str
    gambler_id: int
    amount: float
    win_probability: float
    odds_multiplier: float
    stake_before: float
    stake_after: float
    is_win: bool
    strategy_name: Optional[str] = None
    session_id: Optional[str] = None
    created_at: Optional[datetime] = None

    @property
    def potential_win(self) -> float:
        return self.amount * self.odds_multiplier

    @property
    def net_change(self) -> float:
        return self.stake_after - self.stake_before

    def to_dict(self) -> dict:
        return {
            "bet_id": self.bet_id,
            "gambler_id": self.gambler_id,
            "amount": self.amount,
            "win_probability": self.win_probability,
            "odds_multiplier": self.odds_multiplier,
            "potential_win": self.potential_win,
            "stake_before": self.stake_before,
            "stake_after": self.stake_after,
            "is_win": self.is_win,
            "strategy_name": self.strategy_name,
            "session_id": self.session_id,
            "net_change": self.net_change,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

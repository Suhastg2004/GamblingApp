from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class BettingSession:
    session_id: str
    gambler_id: int
    strategy_name: str
    win_probability: float
    started_at: datetime
    ended_at: Optional[datetime] = None
    total_bets: int = 0
    wins: int = 0
    losses: int = 0
    profit: float = 0.0
    bet_ids: Optional[List[str]] = None

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "gambler_id": self.gambler_id,
            "strategy_name": self.strategy_name,
            "win_probability": self.win_probability,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "total_bets": self.total_bets,
            "wins": self.wins,
            "losses": self.losses,
            "profit": self.profit,
            "win_rate": (self.wins / self.total_bets) if self.total_bets else 0.0,
            "bet_ids": self.bet_ids or [],
        }

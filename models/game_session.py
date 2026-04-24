from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class SessionStatus(Enum):
    INITIALIZED = "INITIALIZED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ENDED_WIN = "ENDED_WIN"
    ENDED_LOSS = "ENDED_LOSS"
    ENDED_MANUAL = "ENDED_MANUAL"
    ENDED_TIMEOUT = "ENDED_TIMEOUT"
    ENDED_MAX_GAMES = "ENDED_MAX_GAMES"


class SessionEndReason(Enum):
    UPPER_LIMIT_REACHED = "UPPER_LIMIT_REACHED"
    LOWER_LIMIT_REACHED = "LOWER_LIMIT_REACHED"
    MANUAL = "MANUAL"
    TIMEOUT = "TIMEOUT"
    MAX_GAMES_REACHED = "MAX_GAMES_REACHED"


@dataclass
class SessionParameters:
    lower_limit: float
    upper_limit: float
    min_bet: float
    max_bet: float
    max_games: int
    max_duration_seconds: int
    default_win_probability: float


@dataclass
class GameRecord:
    game_no: int
    bet_id: str
    bet_amount: float
    is_win: bool
    stake_before: float
    stake_after: float
    duration_seconds: float
    played_at: datetime

    def to_dict(self):
        return {
            "game_no": self.game_no,
            "bet_id": self.bet_id,
            "bet_amount": self.bet_amount,
            "is_win": self.is_win,
            "stake_before": self.stake_before,
            "stake_after": self.stake_after,
            "duration_seconds": self.duration_seconds,
            "played_at": self.played_at.isoformat(),
        }


@dataclass
class PauseRecord:
    paused_at: datetime
    reason: str
    resumed_at: Optional[datetime] = None
    duration_seconds: float = 0.0

    def to_dict(self):
        return {
            "paused_at": self.paused_at.isoformat(),
            "reason": self.reason,
            "resumed_at": self.resumed_at.isoformat() if self.resumed_at else None,
            "duration_seconds": self.duration_seconds,
        }


@dataclass
class GamingSession:
    session_id: str
    gambler_id: int
    parameters: SessionParameters
    status: SessionStatus
    started_at: datetime
    end_reason: Optional[SessionEndReason] = None
    ended_at: Optional[datetime] = None
    total_paused_seconds: float = 0.0
    games: List[GameRecord] = field(default_factory=list)
    pauses: List[PauseRecord] = field(default_factory=list)
    wins: int = 0
    losses: int = 0
    total_profit: float = 0.0

    def total_duration_seconds(self) -> float:
        end = self.ended_at or datetime.utcnow()
        return max((end - self.started_at).total_seconds(), 0.0)

    def active_duration_seconds(self) -> float:
        return max(self.total_duration_seconds() - self.total_paused_seconds, 0.0)

    def to_dict(self):
        total_games = len(self.games)
        return {
            "session_id": self.session_id,
            "gambler_id": self.gambler_id,
            "status": self.status.value,
            "end_reason": self.end_reason.value if self.end_reason else None,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "total_games": total_games,
            "wins": self.wins,
            "losses": self.losses,
            "win_rate": (self.wins / total_games) if total_games else 0.0,
            "total_profit": self.total_profit,
            "total_duration_seconds": self.total_duration_seconds(),
            "active_duration_seconds": self.active_duration_seconds(),
            "pause_duration_seconds": self.total_paused_seconds,
            "parameters": {
                "lower_limit": self.parameters.lower_limit,
                "upper_limit": self.parameters.upper_limit,
                "min_bet": self.parameters.min_bet,
                "max_bet": self.parameters.max_bet,
                "max_games": self.parameters.max_games,
                "max_duration_seconds": self.parameters.max_duration_seconds,
                "default_win_probability": self.parameters.default_win_probability,
            },
            "games": [g.to_dict() for g in self.games],
            "pauses": [p.to_dict() for p in self.pauses],
        }

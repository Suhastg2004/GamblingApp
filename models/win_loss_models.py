from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class OutcomeStrategyType(Enum):
    RANDOM = "RANDOM"
    WEIGHTED = "WEIGHTED"


class OddsType(Enum):
    FIXED = "FIXED"
    PROBABILITY_BASED = "PROBABILITY_BASED"
    AMERICAN = "AMERICAN"
    DECIMAL = "DECIMAL"


@dataclass
class OddsConfiguration:
    odds_type: OddsType
    value: float


@dataclass
class GameResult:
    bet_id: str
    amount: float
    is_win: bool
    stake_before: float
    stake_after: float
    odds_multiplier: float
    winnings: float
    losses: float

    @property
    def net_change(self) -> float:
        return self.stake_after - self.stake_before

    def to_dict(self) -> dict:
        return {
            "bet_id": self.bet_id,
            "amount": self.amount,
            "is_win": self.is_win,
            "stake_before": self.stake_before,
            "stake_after": self.stake_after,
            "odds_multiplier": self.odds_multiplier,
            "winnings": self.winnings,
            "losses": self.losses,
            "net_change": self.net_change,
        }


@dataclass
class RunningTotals:
    total_games: int
    wins: int
    losses: int
    pushes: int
    total_winnings: float
    total_losses: float
    net_profit: float
    balance_history: List[float]
    profit_progression: List[float]

    def to_dict(self) -> dict:
        return {
            "total_games": self.total_games,
            "wins": self.wins,
            "losses": self.losses,
            "pushes": self.pushes,
            "total_winnings": self.total_winnings,
            "total_losses": self.total_losses,
            "net_profit": self.net_profit,
            "balance_history": self.balance_history,
            "profit_progression": self.profit_progression,
        }


@dataclass
class WinLossStatistics:
    win_rate: float
    loss_rate: float
    win_loss_ratio: float
    average_win: float
    average_loss: float
    largest_win: float
    largest_loss: float
    profit_factor: float
    roi: float
    return_on_risk: float
    current_win_streak: int
    current_loss_streak: int
    longest_win_streak: int
    longest_loss_streak: int

    def to_dict(self) -> dict:
        return {
            "win_rate": self.win_rate,
            "loss_rate": self.loss_rate,
            "win_loss_ratio": self.win_loss_ratio,
            "average_win": self.average_win,
            "average_loss": self.average_loss,
            "largest_win": self.largest_win,
            "largest_loss": self.largest_loss,
            "profit_factor": self.profit_factor,
            "roi": self.roi,
            "return_on_risk": self.return_on_risk,
            "current_win_streak": self.current_win_streak,
            "current_loss_streak": self.current_loss_streak,
            "longest_win_streak": self.longest_win_streak,
            "longest_loss_streak": self.longest_loss_streak,
        }


@dataclass
class WinLossAnalysis:
    running_totals: RunningTotals
    statistics: WinLossStatistics
    game_results: Optional[List[GameResult]] = None

    def to_dict(self) -> dict:
        return {
            "running_totals": self.running_totals.to_dict(),
            "statistics": self.statistics.to_dict(),
            "game_results": [g.to_dict() for g in self.game_results] if self.game_results else [],
        }

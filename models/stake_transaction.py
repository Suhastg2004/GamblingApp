from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class TransactionType(Enum):
    INITIAL_STAKE = "INITIAL_STAKE"
    BET_PLACED = "BET_PLACED"
    BET_WIN = "BET_WIN"
    BET_LOSS = "BET_LOSS"
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    ADJUSTMENT = "ADJUSTMENT"
    RESET = "RESET"


@dataclass(frozen=True)
class StakeTransaction:
    gambler_id: int
    transaction_type: TransactionType
    amount: float
    balance_before: float
    balance_after: float
    bet_id: Optional[str] = None
    note: Optional[str] = None
    created_at: Optional[datetime] = None

from dataclasses import dataclass


@dataclass(frozen=True)
class StakeBoundary:
    lower_limit: float
    upper_limit: float

    def __post_init__(self):
        if self.lower_limit < 0 or self.upper_limit <= 0:
            raise ValueError("Stake boundaries must be positive")
        if self.lower_limit >= self.upper_limit:
            raise ValueError("Lower limit must be less than upper limit")

    @property
    def lower_warning(self) -> float:
        return self.lower_limit * 1.2

    @property
    def upper_warning(self) -> float:
        return self.upper_limit * 0.8

    def status_for(self, amount: float) -> str:
        if amount < self.lower_limit:
            return "OUT_LOW"
        if amount > self.upper_limit:
            return "OUT_HIGH"
        if amount <= self.lower_warning:
            return "WARN_LOW"
        if amount >= self.upper_warning:
            return "WARN_HIGH"
        return "OK"

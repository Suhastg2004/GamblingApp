from models.stake_boundary import StakeBoundary
from models.stake_monitor import StakeMonitor


class StakeManager:
    def __init__(self, lower_limit, upper_limit):
        self.boundary = StakeBoundary(lower_limit, upper_limit)

    def track(self, gambler_id, balances):
        return StakeMonitor.from_balances(gambler_id, balances)

    def validate(self, amount):
        status = self.boundary.status_for(amount)
        return {
            "status": status,
            "is_within_boundaries": status in {"OK", "WARN_LOW", "WARN_HIGH"},
            "lower_limit": self.boundary.lower_limit,
            "upper_limit": self.boundary.upper_limit,
            "lower_warning": self.boundary.lower_warning,
            "upper_warning": self.boundary.upper_warning,
        }

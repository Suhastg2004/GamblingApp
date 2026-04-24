from abc import ABC, abstractmethod


class BettingStrategy(ABC):
    def __init__(self):
        self._last_outcome_win = None

    @abstractmethod
    def next_bet(self, current_stake, min_bet, max_bet):
        raise NotImplementedError()

    def record_outcome(self, is_win):
        self._last_outcome_win = is_win


class FixedAmountStrategy(BettingStrategy):
    def __init__(self, fixed_amount):
        super().__init__()
        self.fixed_amount = fixed_amount

    def next_bet(self, current_stake, min_bet, max_bet):
        return min(max(self.fixed_amount, min_bet), max_bet, current_stake)


class PercentageStrategy(BettingStrategy):
    def __init__(self, percentage):
        super().__init__()
        self.percentage = percentage

    def next_bet(self, current_stake, min_bet, max_bet):
        amount = current_stake * self.percentage
        return min(max(amount, min_bet), max_bet, current_stake)


class MartingaleStrategy(BettingStrategy):
    def __init__(self, base_bet):
        super().__init__()
        self.base_bet = base_bet
        self.current_bet = base_bet

    def next_bet(self, current_stake, min_bet, max_bet):
        return min(max(self.current_bet, min_bet), max_bet, current_stake)

    def record_outcome(self, is_win):
        super().record_outcome(is_win)
        self.current_bet = self.base_bet if is_win else self.current_bet * 2


class ReverseMartingaleStrategy(BettingStrategy):
    def __init__(self, base_bet):
        super().__init__()
        self.base_bet = base_bet
        self.current_bet = base_bet

    def next_bet(self, current_stake, min_bet, max_bet):
        return min(max(self.current_bet, min_bet), max_bet, current_stake)

    def record_outcome(self, is_win):
        super().record_outcome(is_win)
        self.current_bet = self.current_bet * 2 if is_win else self.base_bet


class FibonacciStrategy(BettingStrategy):
    def __init__(self, unit_bet):
        super().__init__()
        self.unit_bet = unit_bet
        self.index = 1

    def _fib(self, n):
        if n <= 1:
            return 1
        a, b = 1, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b

    def next_bet(self, current_stake, min_bet, max_bet):
        amount = self._fib(self.index) * self.unit_bet
        return min(max(amount, min_bet), max_bet, current_stake)

    def record_outcome(self, is_win):
        super().record_outcome(is_win)
        if is_win:
            self.index = max(1, self.index - 2)
        else:
            self.index += 1


class DAlembertStrategy(BettingStrategy):
    def __init__(self, base_bet, step):
        super().__init__()
        self.base_bet = base_bet
        self.step = step
        self.current_bet = base_bet

    def next_bet(self, current_stake, min_bet, max_bet):
        return min(max(self.current_bet, min_bet), max_bet, current_stake)

    def record_outcome(self, is_win):
        super().record_outcome(is_win)
        if is_win:
            self.current_bet = max(self.base_bet, self.current_bet - self.step)
        else:
            self.current_bet += self.step


def build_strategy(strategy_name, base_bet, percentage=0.05, step=1.0):
    normalized = strategy_name.strip().lower()

    if normalized == "fixed":
        return FixedAmountStrategy(base_bet)
    if normalized == "percentage":
        return PercentageStrategy(percentage)
    if normalized == "martingale":
        return MartingaleStrategy(base_bet)
    if normalized == "reverse_martingale":
        return ReverseMartingaleStrategy(base_bet)
    if normalized == "fibonacci":
        return FibonacciStrategy(base_bet)
    if normalized == "dalembert":
        return DAlembertStrategy(base_bet, step)

    raise ValueError("Unsupported strategy")

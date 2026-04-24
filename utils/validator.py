def validate_stake(s):
    if s <= 0:
        raise ValueError("Stake must be positive")

def validate_thresholds(i, w, l):
    if not (l < i < w):
        raise ValueError("Invalid thresholds")

def validate_bets(min_b, max_b):
    if min_b <= 0 or max_b <= 0 or min_b > max_b:
        raise ValueError("Invalid bet limits")


def validate_positive_amount(amount, field_name="amount"):
    if amount is None or amount <= 0:
        raise ValueError(f"{field_name} must be positive")


def validate_boundaries(lower_limit, upper_limit):
    if lower_limit < 0 or upper_limit <= 0:
        raise ValueError("Boundary limits must be positive")
    if lower_limit >= upper_limit:
        raise ValueError("Lower limit must be smaller than upper limit")


def validate_balance_transition(balance_before, amount_delta):
    balance_after = balance_before + amount_delta
    if balance_after < 0:
        raise ValueError("Stake cannot become negative")
    return balance_after
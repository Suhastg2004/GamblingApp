def validate_stake(s):
    if s <= 0:
        raise ValueError("Stake must be positive")

def validate_thresholds(i, w, l):
    if not (l < i < w):
        raise ValueError("Invalid thresholds")

def validate_bets(min_b, max_b):
    if min_b <= 0 or max_b <= 0 or min_b > max_b:
        raise ValueError("Invalid bet limits")
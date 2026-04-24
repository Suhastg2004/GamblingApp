from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Any, Callable, List, Optional


class ValidationErrorType(Enum):
    STAKE_ERROR = "STAKE_ERROR"
    BET_ERROR = "BET_ERROR"
    LIMIT_ERROR = "LIMIT_ERROR"
    PROBABILITY_ERROR = "PROBABILITY_ERROR"
    NUMERIC_ERROR = "NUMERIC_ERROR"
    RANGE_ERROR = "RANGE_ERROR"
    NULL_ERROR = "NULL_ERROR"


class ValidationException(ValueError):
    def __init__(self, message, error_type, field=None, attempted_value=None):
        super().__init__(message)
        self.error_type = error_type
        self.field = field
        self.attempted_value = attempted_value

    def to_dict(self):
        return {
            "message": str(self),
            "error_type": self.error_type.value,
            "field": self.field,
            "attempted_value": self.attempted_value,
        }


class StakeValidationException(ValidationException):
    pass


class BetValidationException(ValidationException):
    pass


class LimitValidationException(ValidationException):
    pass


class ProbabilityValidationException(ValidationException):
    pass


@dataclass
class ValidationResult:
    success: bool = True
    errors: List[ValidationException] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_error(self, error):
        self.errors.append(error)
        self.success = False

    def add_warning(self, warning):
        self.warnings.append(warning)

    def to_dict(self):
        return {
            "success": self.success,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": self.warnings,
        }


@dataclass
class ValidationConfig:
    min_stake: float = 0.0
    max_stake: float = 1_000_000.0
    min_bet: float = 0.01
    max_bet: float = 100_000.0
    min_probability: float = 0.0
    max_probability: float = 1.0
    strict_mode: bool = True
    allow_zero_stake: bool = False


class InputValidator:
    def __init__(self, config=None):
        self.config = config or ValidationConfig()

    def parse_and_validate_numeric(self, raw_value, field_name, cast_type=float):
        if raw_value is None:
            raise ValidationException(
                f"{field_name} is required",
                ValidationErrorType.NULL_ERROR,
                field=field_name,
                attempted_value=raw_value,
            )

        if isinstance(raw_value, str):
            raw_value = raw_value.strip()
            if raw_value == "":
                raise ValidationException(
                    f"{field_name} cannot be empty",
                    ValidationErrorType.NULL_ERROR,
                    field=field_name,
                    attempted_value=raw_value,
                )

        try:
            value = cast_type(raw_value)
        except (ValueError, TypeError):
            raise ValidationException(
                f"{field_name} must be a valid number",
                ValidationErrorType.NUMERIC_ERROR,
                field=field_name,
                attempted_value=raw_value,
            )

        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            raise ValidationException(
                f"{field_name} cannot be NaN or Infinity",
                ValidationErrorType.NUMERIC_ERROR,
                field=field_name,
                attempted_value=raw_value,
            )

        return value

    def validate_initial_stake(self, stake):
        value = self.parse_and_validate_numeric(stake, "initial_stake", float)

        if value < 0 or (value == 0 and not self.config.allow_zero_stake):
            raise StakeValidationException(
                "Initial stake must be positive",
                ValidationErrorType.STAKE_ERROR,
                field="initial_stake",
                attempted_value=value,
            )

        if value < self.config.min_stake or value > self.config.max_stake:
            raise StakeValidationException(
                f"Initial stake must be within [{self.config.min_stake}, {self.config.max_stake}]",
                ValidationErrorType.RANGE_ERROR,
                field="initial_stake",
                attempted_value=value,
            )

        return value

    def validate_bet_amount(self, amount, current_stake, min_bet=None, max_bet=None):
        bet = self.parse_and_validate_numeric(amount, "bet_amount", float)
        stake = self.parse_and_validate_numeric(current_stake, "current_stake", float)

        effective_min = self.config.min_bet if min_bet is None else float(min_bet)
        effective_max = self.config.max_bet if max_bet is None else float(max_bet)

        if bet <= 0:
            raise BetValidationException(
                "Bet amount must be positive",
                ValidationErrorType.BET_ERROR,
                field="bet_amount",
                attempted_value=bet,
            )
        if bet < effective_min or bet > effective_max:
            raise BetValidationException(
                f"Bet amount must be within [{effective_min}, {effective_max}]",
                ValidationErrorType.RANGE_ERROR,
                field="bet_amount",
                attempted_value=bet,
            )
        if bet > stake:
            raise BetValidationException(
                "Bet amount cannot exceed current stake",
                ValidationErrorType.BET_ERROR,
                field="bet_amount",
                attempted_value=bet,
            )

        return bet

    def validate_limits(self, initial_stake, upper_limit, lower_limit):
        i = self.parse_and_validate_numeric(initial_stake, "initial_stake", float)
        upper = self.parse_and_validate_numeric(upper_limit, "upper_limit", float)
        lower = self.parse_and_validate_numeric(lower_limit, "lower_limit", float)

        if lower < 0 or upper <= 0:
            raise LimitValidationException(
                "Limits must be positive",
                ValidationErrorType.LIMIT_ERROR,
                field="limits",
                attempted_value={"lower": lower, "upper": upper},
            )
        if lower >= upper:
            raise LimitValidationException(
                "Lower limit must be less than upper limit",
                ValidationErrorType.LIMIT_ERROR,
                field="limits",
                attempted_value={"lower": lower, "upper": upper},
            )
        if not (lower < i < upper):
            raise LimitValidationException(
                "Initial stake must be between lower and upper limits",
                ValidationErrorType.RANGE_ERROR,
                field="initial_stake",
                attempted_value=i,
            )

        return i, upper, lower

    def validate_stake_non_negative(self, stake):
        value = self.parse_and_validate_numeric(stake, "stake", float)
        if value < 0 or (value == 0 and not self.config.allow_zero_stake and self.config.strict_mode):
            raise StakeValidationException(
                "Stake cannot be negative",
                ValidationErrorType.STAKE_ERROR,
                field="stake",
                attempted_value=value,
            )
        return value

    def validate_probability(self, probability):
        value = self.parse_and_validate_numeric(probability, "probability", float)
        if value < self.config.min_probability or value > self.config.max_probability:
            raise ProbabilityValidationException(
                f"Probability must be between {self.config.min_probability} and {self.config.max_probability}",
                ValidationErrorType.PROBABILITY_ERROR,
                field="probability",
                attempted_value=value,
            )
        return value

    def validate_batch(self, checks):
        result = ValidationResult()
        for check in checks:
            validator = check.get("validator")
            args = check.get("args", [])
            kwargs = check.get("kwargs", {})
            warning_on_fail = check.get("warning_on_fail", False)

            try:
                validator(*args, **kwargs)
            except ValidationException as exc:
                if warning_on_fail:
                    result.add_warning(str(exc))
                else:
                    result.add_error(exc)
        return result

    # Camel-case aliases for UC wording consistency
    def validateInitialStake(self, stake):
        return self.validate_initial_stake(stake)

    def validateBetAmount(self, amount, current_stake, min_bet=None, max_bet=None):
        return self.validate_bet_amount(amount, current_stake, min_bet=min_bet, max_bet=max_bet)

    def validateLimits(self, initial_stake, upper_limit, lower_limit):
        return self.validate_limits(initial_stake, upper_limit, lower_limit)

    def parseAndValidateNumeric(self, raw_value, field_name, cast_type=float):
        return self.parse_and_validate_numeric(raw_value, field_name, cast_type=cast_type)

    def validateStakeNonNegative(self, stake):
        return self.validate_stake_non_negative(stake)

    def validateProbability(self, probability):
        return self.validate_probability(probability)


_DEFAULT_VALIDATOR = InputValidator()


def validate_stake(s):
    return _DEFAULT_VALIDATOR.validate_initial_stake(s)


def validate_thresholds(i, w, l):
    return _DEFAULT_VALIDATOR.validate_limits(i, w, l)


def validate_bets(min_b, max_b):
    min_value = _DEFAULT_VALIDATOR.parse_and_validate_numeric(min_b, "min_bet")
    max_value = _DEFAULT_VALIDATOR.parse_and_validate_numeric(max_b, "max_bet")
    if min_value <= 0 or max_value <= 0 or min_value > max_value:
        raise BetValidationException(
            "Invalid bet limits",
            ValidationErrorType.BET_ERROR,
            field="bet_limits",
            attempted_value={"min_bet": min_value, "max_bet": max_value},
        )
    return min_value, max_value


def validate_positive_amount(amount, field_name="amount"):
    value = _DEFAULT_VALIDATOR.parse_and_validate_numeric(amount, field_name)
    if value <= 0:
        raise ValidationException(
            f"{field_name} must be positive",
            ValidationErrorType.RANGE_ERROR,
            field=field_name,
            attempted_value=value,
        )
    return value


def validate_boundaries(lower_limit, upper_limit):
    lower = _DEFAULT_VALIDATOR.parse_and_validate_numeric(lower_limit, "lower_limit")
    upper = _DEFAULT_VALIDATOR.parse_and_validate_numeric(upper_limit, "upper_limit")
    if lower < 0 or upper <= 0:
        raise LimitValidationException(
            "Boundary limits must be positive",
            ValidationErrorType.LIMIT_ERROR,
            field="boundaries",
            attempted_value={"lower_limit": lower, "upper_limit": upper},
        )
    if lower >= upper:
        raise LimitValidationException(
            "Lower limit must be smaller than upper limit",
            ValidationErrorType.LIMIT_ERROR,
            field="boundaries",
            attempted_value={"lower_limit": lower, "upper_limit": upper},
        )
    return lower, upper


def validate_balance_transition(balance_before, amount_delta):
    before = _DEFAULT_VALIDATOR.parse_and_validate_numeric(balance_before, "balance_before")
    delta = _DEFAULT_VALIDATOR.parse_and_validate_numeric(amount_delta, "amount_delta")
    balance_after = before + delta
    if balance_after < 0:
        raise StakeValidationException(
            "Stake cannot become negative",
            ValidationErrorType.STAKE_ERROR,
            field="balance_after",
            attempted_value=balance_after,
        )
    return balance_after


def validate_probability(value):
    return _DEFAULT_VALIDATOR.validate_probability(value)
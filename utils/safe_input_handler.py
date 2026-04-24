from utils.validator import InputValidator, ValidationErrorType, ValidationException


class SafeInputHandler:
    def __init__(self, validator=None, retries=3):
        self.validator = validator or InputValidator()
        self.retries = retries

    def prompt_number(self, prompt, field_name, cast_type=float, allow_blank=False, default=None):
        attempts = 0
        while attempts < self.retries:
            raw = input(prompt)
            if allow_blank and raw.strip() == "":
                return default

            try:
                return self.validator.parse_and_validate_numeric(raw, field_name, cast_type=cast_type)
            except ValidationException as exc:
                attempts += 1
                print(f"Invalid input: {exc}")

        raise ValidationException(
            f"Maximum retries reached for {field_name}",
            error_type=ValidationErrorType.NUMERIC_ERROR,
            field=field_name,
            attempted_value=None,
        )

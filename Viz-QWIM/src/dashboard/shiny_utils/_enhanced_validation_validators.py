"""Validation helpers for enhanced dashboard validation.

This private module holds the non-model validation logic re-exported by
:mod:`src.dashboard.shiny_utils.utils_enhanced_validation`.
"""

from __future__ import annotations

import re

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

from ._enhanced_validation_types import (
    Financial_Validation_Config,
    Gender_Enum,
    Marital_Status_Enum,
    Risk_Tolerance_Enum,
    Validation_Severity_Enum,
)


_logger = get_logger(name = "src.dashboard.shiny_utils.utils_enhanced_validation")


def validate_enhanced_financial_amount(
    *, amount: int | float | str | Decimal, minimum_value: float = Financial_Validation_Config.MINIMUM_FINANCIAL_AMOUNT, maximum_value: float | None = None, field_name: str = "Financial amount", allow_negative: bool = False, decimal_places: int = Financial_Validation_Config.CURRENCY_DECIMAL_PLACES) -> float:
    """Enhanced validation for financial amounts with flexible input handling.

    This function provides comprehensive validation for financial amounts,
    supporting various input formats including currency strings, numeric types,
    and Decimal values. It handles locale-specific formatting, currency symbols,
    and validates ranges and precision.
    """
    if isinstance(amount, bool):
        raise TypeError(f"{field_name} must be int, float, str, or Decimal, got {type(amount)}")
    if isinstance(minimum_value, bool):
        raise Exception_Validation_Input("minimum_value must be numeric")
    if isinstance(maximum_value, bool):
        raise Exception_Validation_Input("maximum_value must be numeric")

    if minimum_value is None:
        minimum_value = Financial_Validation_Config.MINIMUM_FINANCIAL_AMOUNT
    if maximum_value is None:
        maximum_value = Financial_Validation_Config.MAXIMUM_FINANCIAL_AMOUNT
    if isinstance(decimal_places, bool) or not isinstance(decimal_places, int) or decimal_places < 0:
        raise Exception_Validation_Input("decimal_places must be a non-negative integer")

    try:
        decimal_amount: Decimal
        if amount is None:
            raise Exception_Validation_Input(f"{field_name} cannot be None")

        if isinstance(amount, str):
            cleaned_amount = amount.strip()
            if not cleaned_amount:
                raise Exception_Validation_Input(f"{field_name} cannot be empty")

            is_negative_accounting = (
                cleaned_amount.startswith("(") and cleaned_amount.endswith(")")
            )
            if is_negative_accounting:
                cleaned_amount = cleaned_amount[1:-1]

            currency_symbols = [
                "$",
                "EUR",
                "GBP",
                "USD",
                "JPY",
                "CAD",
                "AUD",
                "CHF",
                "SEK",
                "NOK",
                "DKK",
            ]
            for symbol in currency_symbols:
                cleaned_amount = cleaned_amount.replace(symbol, "")

            cleaned_amount = cleaned_amount.replace("%", "")

            if "." in cleaned_amount and "," in cleaned_amount:
                last_dot = cleaned_amount.rfind(".")
                last_comma = cleaned_amount.rfind(",")
                if last_dot > last_comma:
                    cleaned_amount = cleaned_amount.replace(",", "")
                else:
                    cleaned_amount = cleaned_amount.replace(".", "").replace(",", ".")
            elif (
                "," in cleaned_amount
                and cleaned_amount.count(",") == 1
                and len(cleaned_amount.split(",")[1]) <= 3
            ):
                if len(cleaned_amount.split(",")[1]) <= 2:
                    cleaned_amount = cleaned_amount.replace(",", ".")
                else:
                    cleaned_amount = cleaned_amount.replace(",", "")
            else:
                cleaned_amount = cleaned_amount.replace(",", "")

            cleaned_amount = cleaned_amount.replace(" ", "")

            if is_negative_accounting:
                cleaned_amount = "-" + cleaned_amount

            if not cleaned_amount or cleaned_amount in ["-", "+", "."]:
                raise Exception_Validation_Input(
                    f"{field_name} is empty or contains only formatting characters",
                )

            try:
                decimal_amount = Decimal(cleaned_amount)
            except InvalidOperation as exc_error:
                raise Exception_Validation_Input(
                    f"{field_name} '{amount}' is not a valid number format",
                ) from exc_error

        elif isinstance(amount, (int, float)):
            decimal_amount = Decimal(str(amount))
        elif isinstance(amount, Decimal):
            decimal_amount = amount
        else:
            raise TypeError(f"{field_name} must be int, float, str, or Decimal, got {type(amount)}")

        if decimal_amount < 0 and not allow_negative:
            raise Exception_Validation_Input(
                f"{field_name} cannot be negative. Got {decimal_amount}",
            )

        _sign, _digits, exponent = decimal_amount.as_tuple()
        if isinstance(exponent, int) and exponent < 0:
            current_decimal_places = abs(exponent)
            if current_decimal_places > decimal_places:
                raise Exception_Validation_Input(
                    f"{field_name} has too many decimal places. "
                    f"Maximum allowed: {decimal_places}, got: {current_decimal_places}",
                )

        quantizer = Decimal("0.1") ** decimal_places
        rounded_amount = decimal_amount.quantize(quantizer, rounding=ROUND_HALF_UP)
        float_amount = float(rounded_amount)

        if float_amount < minimum_value:
            raise Exception_Validation_Input(
                f"{field_name} must be at least {minimum_value:,.{decimal_places}f}. "
                f"Got {float_amount:,.{decimal_places}f}",
            )

        if float_amount > maximum_value:
            raise Exception_Validation_Input(
                f"{field_name} cannot exceed {maximum_value:,.{decimal_places}f}. "
                f"Got {float_amount:,.{decimal_places}f}",
            )

        return float_amount

    except ValueError as exc_error:  # pragma: no cover
        raise exc_error  # pragma: no cover
    except Exception as exc_error:
        raise Exception_Validation_Input(
            f"Unexpected error validating {field_name}: {exc_error!s}",
        ) from exc_error


def validate_enhanced_percentage_value(
    *, percentage: int | float | str, minimum_value: float = 0.0, maximum_value: float = 100.0, field_name: str = "Percentage", decimal_places: int = Financial_Validation_Config.PERCENTAGE_DECIMAL_PLACES, input_as_decimal: bool = False) -> float:
    """Enhanced validation for percentage values with flexible input handling."""
    if isinstance(minimum_value, bool):
        raise Exception_Validation_Input("minimum_value must be numeric")
    if isinstance(maximum_value, bool):
        raise Exception_Validation_Input("maximum_value must be numeric")

    try:
        if isinstance(percentage, str) and "%" in percentage:
            cleaned_percentage = percentage.replace("%", "").strip()
        else:
            cleaned_percentage = percentage

        validated_amount = validate_enhanced_financial_amount(
            amount=cleaned_percentage,
            minimum_value=minimum_value if not input_as_decimal else minimum_value / 100,
            maximum_value=maximum_value if not input_as_decimal else maximum_value / 100,
            field_name=field_name,
            allow_negative=minimum_value < 0,
            decimal_places=decimal_places,
        )

        if input_as_decimal and validated_amount <= 1.0:
            validated_amount *= 100

        if validated_amount < minimum_value or validated_amount > maximum_value:  # pragma: no branch
            raise Exception_Validation_Input(  # pragma: no cover
                f"{field_name} must be between {minimum_value}% and {maximum_value}%. "
                f"Got {validated_amount}%",
            )

        return validated_amount

    except ValueError as exc_error:  # pragma: no cover
        raise Exception_Validation_Input(
            f"Percentage validation error: {exc_error!s}",
        ) from exc_error  # pragma: no cover


def validate_enhanced_age_value(
    *, age: int | float | str, minimum_age: int = Financial_Validation_Config.MINIMUM_AGE, maximum_age: int = Financial_Validation_Config.MAXIMUM_AGE, field_name: str = "Age", allow_decimal: bool = False) -> int | float:
    """Enhanced validation for age values with comprehensive range and format checking."""
    if isinstance(age, bool):
        raise TypeError(f"{field_name} must be a number, got {type(age)}")
    if isinstance(minimum_age, bool):
        raise Exception_Validation_Input("minimum_age must be an integer")
    if isinstance(maximum_age, bool):
        raise Exception_Validation_Input("maximum_age must be an integer")

    try:
        if isinstance(age, str):
            cleaned_age = age.strip()
            if not cleaned_age:
                raise Exception_Validation_Input(f"{field_name} cannot be empty")
            numeric_age = float(cleaned_age)
        elif isinstance(age, (int, float)):
            numeric_age = float(age)
        else:
            raise TypeError(f"{field_name} must be a number, got {type(age)}")

        if not allow_decimal and numeric_age != int(numeric_age):
            raise Exception_Validation_Input(
                f"{field_name} must be a whole number, got {numeric_age}",
            )

        if numeric_age < minimum_age:
            raise Exception_Validation_Input(
                f"{field_name} must be at least {minimum_age} years, got {numeric_age}",
            )

        if numeric_age > maximum_age:
            raise Exception_Validation_Input(
                f"{field_name} cannot exceed {maximum_age} years, got {numeric_age}",
            )

        return int(numeric_age) if not allow_decimal else numeric_age

    except ValueError as exc_error:
        raise exc_error
    except Exception as exc_error:
        raise Exception_Validation_Input(
            f"Unexpected error validating {field_name}: {exc_error!s}",
        ) from exc_error


def validate_enhanced_name_value(
    *, name: str, field_name: str = "Name", min_length: int = Financial_Validation_Config.NAME_MIN_LENGTH, max_length: int = Financial_Validation_Config.NAME_MAX_LENGTH, allow_special_characters: bool = True) -> str:
    """Enhanced validation for name fields with format and length checking."""
    if not isinstance(name, str):
        raise TypeError(f"{field_name} must be a string, got {type(name)}")
    if isinstance(min_length, bool):
        raise Exception_Validation_Input("min_length must be an integer")
    if isinstance(max_length, bool):
        raise Exception_Validation_Input("max_length must be an integer")

    cleaned_name = name.strip()
    if not cleaned_name:
        raise Exception_Validation_Input(f"{field_name} cannot be empty")

    if len(cleaned_name) < min_length:
        raise Exception_Validation_Input(
            f"{field_name} must be at least {min_length} characters long",
        )

    if len(cleaned_name) > max_length:
        raise Exception_Validation_Input(
            f"{field_name} cannot exceed {max_length} characters",
        )

    if allow_special_characters:
        if not re.match(Financial_Validation_Config.NAME_PATTERN, cleaned_name):
            raise Exception_Validation_Input(
                f"{field_name} can only contain letters, spaces, hyphens, periods, and apostrophes",
            )
    else:
        if not re.match(r"^[a-zA-Z\s]+$", cleaned_name):
            raise Exception_Validation_Input(f"{field_name} can only contain letters and spaces")

    if "  " in cleaned_name:
        raise Exception_Validation_Input(f"{field_name} cannot contain multiple consecutive spaces")

    return cleaned_name.title()


def get_validation_configuration() -> dict[str, Any]:
    """Get comprehensive validation configuration for the application."""
    return {
        "age_constraints": {
            "minimum_age": Financial_Validation_Config.MINIMUM_AGE,
            "maximum_age": Financial_Validation_Config.MAXIMUM_AGE,
            "minimum_retirement_age": Financial_Validation_Config.MINIMUM_RETIREMENT_AGE,
            "maximum_retirement_age": Financial_Validation_Config.MAXIMUM_RETIREMENT_AGE,
        },
        "financial_constraints": {
            "minimum_amount": Financial_Validation_Config.MINIMUM_FINANCIAL_AMOUNT,
            "maximum_amount": Financial_Validation_Config.MAXIMUM_FINANCIAL_AMOUNT,
            "currency_decimal_places": Financial_Validation_Config.CURRENCY_DECIMAL_PLACES,
            "percentage_decimal_places": Financial_Validation_Config.PERCENTAGE_DECIMAL_PLACES,
        },
        "text_constraints": {
            "name_min_length": Financial_Validation_Config.NAME_MIN_LENGTH,
            "name_max_length": Financial_Validation_Config.NAME_MAX_LENGTH,
        },
        "patterns": {
            "name_pattern": Financial_Validation_Config.NAME_PATTERN,
            "email_pattern": Financial_Validation_Config.EMAIL_PATTERN,
            "phone_pattern": Financial_Validation_Config.PHONE_PATTERN,
        },
        "enumerations": {
            "risk_tolerance_options": [item.value for item in Risk_Tolerance_Enum],
            "gender_options": [item.value for item in Gender_Enum],
            "marital_status_options": [item.value for item in Marital_Status_Enum],
            "validation_severity_levels": [item.value for item in Validation_Severity_Enum],
        },
        "version": "2.0.0",
        "module_info": {
            "description": "Enhanced validation utilities for financial dashboard applications",
            "dependencies": ["pydantic", "marshmallow", "decimal", "datetime", "re"],
            "author": "QWIM Dashboard Development Team",
            "features": [
                "Comprehensive financial amount validation",
                "Cross-field validation for business logic",
                "Pydantic model integration",
                "Detailed error messaging",
                "Currency and locale support",
            ],
        },
    }


def configure_enhanced_validation_module(
    *, custom_age_limits: dict[str, int] | None = None, custom_financial_limits: dict[str, float] | None = None, log_level: str = "INFO") -> None:
    """Configure the enhanced validation module with custom settings."""
    try:
        _logger.debug("Logging level configured to %s", log_level)

        if custom_age_limits:
            if isinstance(custom_age_limits, dict):
                for key, value in custom_age_limits.items():
                    if hasattr(Financial_Validation_Config, key.upper()):
                        setattr(Financial_Validation_Config, key.upper(), value)
            else:
                raise Exception_Validation_Input("custom_age_limits must be a dictionary")

        if custom_financial_limits:
            if isinstance(custom_financial_limits, dict):
                for key, value in custom_financial_limits.items():
                    if hasattr(Financial_Validation_Config, key.upper()):
                        setattr(Financial_Validation_Config, key.upper(), value)
            else:
                raise Exception_Validation_Input("custom_financial_limits must be a dictionary")

    except Exception as exc_error:
        raise Exception_Validation_Input(
            f"Error configuring enhanced validation module: {exc_error!s}",
        ) from exc_error


def validate_and_constrain_numeric_value(
    *, value: float, min_value: float, max_value: float) -> float:
    """Validate and constrain value within specified bounds."""
    if isinstance(value, bool):
        raise TypeError(f"value must be a real number, got {type(value)}")

    rounded_value = round(value)

    if rounded_value < min_value:
        return min_value
    if rounded_value > max_value:
        return max_value
    return rounded_value


__all__ = [
    "configure_enhanced_validation_module",
    "get_validation_configuration",
    "validate_and_constrain_numeric_value",
    "validate_enhanced_age_value",
    "validate_enhanced_financial_amount",
    "validate_enhanced_name_value",
    "validate_enhanced_percentage_value",
]
"""Pure-Python formatting and normalization helpers for client worksheet data.

This module intentionally avoids PDF/reporting dependencies so the helpers
remain lightweight and reusable across parser, validator, unit-test, Behave,
and Robot Framework workflows.

Functions
---------
_safe_numeric
_parse_whole_dollar_amount
_safe_whole_dollar_numeric
_normalize_text_trademark_symbols
_normalize_phone_number_US
_is_currency_field_name
"""

from __future__ import annotations

from typing import Any

from ._client_constants import (
    _CURRENCY_FIELD_KEYS_BY_SECTION,
    _WS_CURRENCY_FIELD_KEYS_CONTINGENCY,
    REGEX_PATTERN_MARK_REGISTERED,
    REGEX_PATTERN_MARK_SERVICE,
    REGEX_PATTERN_MARK_TRADEMARK,
    REGEX_PATTERN_PHONE_NUMBER_DIGITS,
    REGEX_PATTERN_WHOLE_DOLLAR_AMOUNT,
)


def _safe_numeric(
    *, value: Any, default: float = 0.0) -> float:
    """Convert *value* to float, stripping ``$`` and ``,`` characters."""
    if value is None or value == "" or isinstance(value, bool):
        return default
    try:
        return float(str(value).replace(",", "").replace("$", "").strip())
    except (ValueError, TypeError):
        return default


def _parse_whole_dollar_amount(*, value: Any) -> int | None:
    """Parse a whole-dollar amount and return the integer value when valid."""
    if value is None or value == "":
        return None

    if isinstance(value, bool):
        return None

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        if value.is_integer():
            return int(value)
        return None

    value_text = str(value).strip().replace("$", "")
    if value_text == "":
        return None

    if REGEX_PATTERN_WHOLE_DOLLAR_AMOUNT.fullmatch(value_text) is None:
        return None

    try:
        return int(value_text.replace(",", ""))
    except (ValueError, TypeError):  # pragma: no cover
        return None  # pragma: no cover



def _safe_whole_dollar_numeric(
    *, value: Any, default: float = 0.0) -> float:
    """Convert a whole-dollar value to float, returning *default* when invalid."""
    amount_value = _parse_whole_dollar_amount(value = value)
    if amount_value is None:
        return default
    return float(amount_value)


def _normalize_text_trademark_symbols(*, value_text: str) -> str:
    """Normalize ASCII trademark markers to Unicode symbols."""
    return REGEX_PATTERN_MARK_SERVICE.sub(
        "℠",
        REGEX_PATTERN_MARK_TRADEMARK.sub(
            "™",
            REGEX_PATTERN_MARK_REGISTERED.sub("®", value_text.strip()),
        ),
    )


def _normalize_phone_number_US(*, value_text: str) -> str:
    """Normalize a US phone number to ``NNN-NNN-NNNN`` when possible."""
    digits_phone_number = REGEX_PATTERN_PHONE_NUMBER_DIGITS.sub("", value_text)
    if len(digits_phone_number) == 11 and digits_phone_number.startswith("1"):
        digits_phone_number = digits_phone_number[1:]

    if len(digits_phone_number) != 10:
        return value_text.strip()

    return f"{digits_phone_number[0:3]}-{digits_phone_number[3:6]}-{digits_phone_number[6:10]}"


def _is_currency_field_name(*, field_name: str) -> bool:
    """Return True when *field_name* identifies a dollar amount text field."""
    parts = field_name.split(".")
    if len(parts) != 3:
        return False

    section_key = parts[0]
    field_key = parts[2]

    if field_key in _CURRENCY_FIELD_KEYS_BY_SECTION.get(section_key, frozenset()):
        return True

    return field_key in _WS_CURRENCY_FIELD_KEYS_CONTINGENCY.get(section_key, frozenset())

"""Private helpers for the client goals subtab."""

from __future__ import annotations

from typing import Any


def _coerce_goals_worksheet_amount_int_or_default(
    *, raw_value: Any, default_value: int = 0) -> int:
    """Coerce worksheet goal amounts while keeping booleans on the default path."""
    if raw_value is None or isinstance(raw_value, bool):
        return default_value

    if str(raw_value).strip() == "":
        return default_value

    return int(float(str(raw_value).replace(",", "")))
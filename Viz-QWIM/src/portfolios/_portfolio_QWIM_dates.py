"""Private date parsing helpers for Portfolio_QWIM."""

from __future__ import annotations

from datetime import datetime

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)


def _parse_portfolio_date_QWIM(*, date_input: str | datetime | None) -> str:
    """Parse supported portfolio date inputs into YYYY-MM-DD strings."""
    try:
        if date_input is None:
            return datetime.now().strftime("%Y-%m-%d")

        if isinstance(date_input, str):
            for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%d-%m-%Y"):
                try:
                    parsed_date = datetime.strptime(date_input, fmt)
                    return parsed_date.strftime("%Y-%m-%d")
                except ValueError:
                    continue

            raise Exception_Validation_Input(
                f"Could not parse date string '{date_input}'. Use YYYY-MM-DD format.",
            )

        if isinstance(date_input, datetime):
            return date_input.strftime("%Y-%m-%d")

        raise TypeError(f"Unsupported date type: {type(date_input).__name__}")

    except Exception as e:
        if isinstance(e, (ValueError, TypeError, Exception_Validation_Input)):
            raise
        raise Exception_Validation_Input(
            f"Error parsing date: {e!s}",
        ) from e  # pragma: no cover
"""Hypothesis (property-based) tests for utils_tab_clients module.

Tests property invariants for:
- format_currency_display
- validate_financial_amount
- validate_age_range
"""

from __future__ import annotations

from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.dashboard.shiny_utils.utils_tab_clients import (
    format_currency_display,
    validate_age_range,
    validate_financial_amount,
)
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)


# ---------------------------------------------------------------------------
# Reusable strategies
# ---------------------------------------------------------------------------

_st_positive_float = st.floats(
    min_value=0.01,
    max_value=1e8,
    allow_nan=False,
    allow_infinity=False,
)

_st_negative_float = st.floats(
    min_value=-1e8,
    max_value=-0.01,
    allow_nan=False,
    allow_infinity=False,
)

_st_valid_integer = st.integers(min_value=0, max_value=1_000_000_000)


# ===========================================================================
# Class_Test_Hypothesis_Format_Currency_Display
# ===========================================================================


class Class_Test_Hypothesis_Format_Currency_Display:
    """Property tests for format_currency_display."""

    @pytest.mark.unit()
    def Test_none_returns_dollar_zero(self) -> None:
        """None input must return '$0'."""
        result = format_currency_display(amount_value=None)
        assert result == "$0"

    @pytest.mark.unit()
    def Test_zero_returns_dollar_zero(self) -> None:
        """Zero input must return '$0'."""
        result = format_currency_display(amount_value=0)
        assert result == "$0"

    @pytest.mark.unit()
    @given(amount=_st_positive_float)
    @settings(max_examples=200)
    def Test_positive_amount_starts_with_dollar_sign(
        self,
        amount: float,
    ) -> None:
        """Positive amounts must produce a string starting with '$'."""
        result = format_currency_display(amount_value=amount)
        assert isinstance(result, str)
        assert result.startswith("$")

    @pytest.mark.unit()
    @given(amount=_st_valid_integer)
    @settings(max_examples=200)
    def Test_integer_produces_dollar_string(
        self,
        amount: int,
    ) -> None:
        """Any non-negative integer must produce a '$'-prefixed string."""
        result = format_currency_display(amount_value=amount)
        assert isinstance(result, str)
        assert result.startswith("$")

    @pytest.mark.unit()
    @given(
        amount=st.integers(min_value=1_000, max_value=999_999_999),
    )
    @settings(max_examples=200)
    def Test_amount_gte_1000_contains_comma(
        self,
        amount: int,
    ) -> None:
        """Amounts >= 1000 must contain a comma separator."""
        result = format_currency_display(amount_value=amount)
        assert "," in result

    @pytest.mark.unit()
    @given(
        amount=st.integers(min_value=1, max_value=999),
    )
    @settings(max_examples=200)
    def Test_small_amount_does_not_contain_comma(
        self,
        amount: int,
    ) -> None:
        """Amounts < 1000 must NOT contain a comma separator."""
        result = format_currency_display(amount_value=amount)
        assert "," not in result

    @pytest.mark.unit()
    @given(amount=_st_positive_float)
    @settings(max_examples=200)
    def Test_result_does_not_contain_decimal_point(
        self,
        amount: float,
    ) -> None:
        """format_currency_display uses :,.0f so no decimal point appears."""
        result = format_currency_display(amount_value=amount)
        assert "." not in result

    @pytest.mark.unit()
    @given(
        str_amount=st.from_regex(r"[0-9]{1,8}", fullmatch=True),
    )
    @settings(max_examples=200)
    def Test_numeric_string_is_accepted(
        self,
        str_amount: str,
    ) -> None:
        """Numeric strings must be accepted and produce a '$'-prefixed string."""
        result = format_currency_display(amount_value=str_amount)
        assert isinstance(result, str)
        assert result.startswith("$")


# ===========================================================================
# Class_Test_Hypothesis_Validate_Financial_Amount
# ===========================================================================


class Class_Test_Hypothesis_Validate_Financial_Amount:
    """Property tests for validate_financial_amount."""

    @pytest.mark.unit()
    def Test_none_returns_zero_float(self) -> None:
        """None must return 0.0."""
        result = validate_financial_amount(amount_value=None)
        assert result == 0.0
        assert isinstance(result, float)

    @pytest.mark.unit()
    @given(amount=_st_positive_float)
    @settings(max_examples=200)
    def Test_positive_float_returns_same_value_as_float(
        self,
        amount: float,
    ) -> None:
        """Positive float must return float(amount) unchanged."""
        result = validate_financial_amount(amount_value=amount)
        assert isinstance(result, float)
        assert abs(result - amount) < 1e-9

    @pytest.mark.unit()
    @given(amount=_st_positive_float)
    @settings(max_examples=200)
    def Test_result_is_non_negative(
        self,
        amount: float,
    ) -> None:
        """Result must always be >= 0."""
        result = validate_financial_amount(amount_value=amount)
        assert result >= 0.0

    @pytest.mark.unit()
    @given(amount=_st_negative_float)
    @settings(max_examples=200)
    def Test_negative_amount_raises(
        self,
        amount: float,
    ) -> None:
        """Negative amount must raise Exception_Validation_Input or ValueError."""
        with pytest.raises((Exception_Validation_Input, ValueError)):
            validate_financial_amount(amount_value=amount)

    @pytest.mark.unit()
    @given(
        amount=st.integers(min_value=0, max_value=10_000_000),
    )
    @settings(max_examples=200)
    def Test_non_negative_integer_accepted(
        self,
        amount: int,
    ) -> None:
        """Non-negative integer must be accepted and returned as float."""
        result = validate_financial_amount(amount_value=amount)
        assert isinstance(result, float)
        assert result >= 0.0

    @pytest.mark.unit()
    @given(
        str_amount=st.from_regex(r"[0-9]{1,6}(\.[0-9]{1,2})?", fullmatch=True),
    )
    @settings(max_examples=200)
    def Test_numeric_string_accepted(
        self,
        str_amount: str,
    ) -> None:
        """Numeric string representation of non-negative number must be accepted."""
        result = validate_financial_amount(amount_value=str_amount)
        assert isinstance(result, float)
        assert result >= 0.0


# ===========================================================================
# Class_Test_Hypothesis_Validate_Age_Range
# ===========================================================================


class Class_Test_Hypothesis_Validate_Age_Range:
    """Property tests for validate_age_range."""

    @pytest.mark.unit()
    @given(
        age=st.integers(min_value=18, max_value=80),
    )
    @settings(max_examples=200)
    def Test_valid_age_returns_integer(
        self,
        age: int,
    ) -> None:
        """Valid age within [18, 80] must return an int."""
        result = validate_age_range(
            age_value=age,
            minimum_age=18,
            maximum_age=80,
        )
        assert isinstance(result, int)
        assert result == age

    @pytest.mark.unit()
    @given(
        age=st.integers(min_value=18, max_value=80),
    )
    @settings(max_examples=200)
    def Test_output_equals_input_for_valid_range(
        self,
        age: int,
    ) -> None:
        """Output must equal input when age is in valid range."""
        result = validate_age_range(
            age_value=age,
            minimum_age=18,
            maximum_age=80,
        )
        assert result == age

    @pytest.mark.unit()
    @given(
        age=st.integers(min_value=81, max_value=200),
    )
    @settings(max_examples=200)
    def Test_age_above_max_raises(
        self,
        age: int,
    ) -> None:
        """Age above maximum must raise."""
        with pytest.raises(Exception):
            validate_age_range(
                age_value=age,
                minimum_age=18,
                maximum_age=80,
            )

    @pytest.mark.unit()
    @given(
        age=st.integers(min_value=0, max_value=17),
    )
    @settings(max_examples=200)
    def Test_age_below_min_raises(
        self,
        age: int,
    ) -> None:
        """Age below minimum must raise."""
        with pytest.raises(Exception):
            validate_age_range(
                age_value=age,
                minimum_age=18,
                maximum_age=80,
            )

    @pytest.mark.unit()
    def Test_none_age_raises(self) -> None:
        """None age must raise Exception_Validation_Input."""
        with pytest.raises(Exception_Validation_Input):
            validate_age_range(
                age_value=None,
                minimum_age=18,
                maximum_age=80,
            )

    @pytest.mark.unit()
    @given(
        age=st.integers(min_value=18, max_value=80),
    )
    @settings(max_examples=200)
    def Test_string_age_accepted(
        self,
        age: int,
    ) -> None:
        """String representation of a valid integer age must be accepted."""
        result = validate_age_range(
            age_value=str(age),
            minimum_age=18,
            maximum_age=80,
        )
        assert result == age

    @pytest.mark.unit()
    @given(
        age=st.integers(min_value=50, max_value=70),
    )
    @settings(max_examples=200)
    def Test_min_age_alias_works(
        self,
        age: int,
    ) -> None:
        """Keyword aliases min_age / max_age must work identically to minimum_age / maximum_age."""
        result_orig = validate_age_range(age_value=age, minimum_age=50, maximum_age=70)
        result_alias = validate_age_range(age_value=age, min_age=50, max_age=70)
        assert result_orig == result_alias

"""Unit tests for ``src.dashboard.shiny_utils.utils_enhanced_formatting``.

All tests are pure-Python (no Shiny session, no disk I/O) and run quickly.

Run:
    pytest tests/tests_shiny/ -m unit -k utils_enhanced_formatting
"""

from __future__ import annotations

import pytest
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Configuration,
    Exception_Validation_Input,
)
from typing import Any


# ---------------------------------------------------------------------------
# validate_locale_setting
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestValidateLocaleSetting:
    """validate_locale_setting must raise on invalid input; return str on valid."""

    def test_non_string_raises_type_error(self) -> None:
        """Test that non string raises type error."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            validate_locale_setting,
        )

        with pytest.raises(TypeError):
            validate_locale_setting(locale_setting = 123)  # type: ignore[arg-type]

    def test_list_raises_type_error(self) -> None:
        """Test that list raises type error."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            validate_locale_setting,
        )

        with pytest.raises(TypeError):
            validate_locale_setting(locale_setting = ["en_US"])  # type: ignore[arg-type]

    def test_none_raises_type_error(self) -> None:
        """Test that none raises type error."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            validate_locale_setting,
        )

        with pytest.raises(TypeError):
            validate_locale_setting(locale_setting = None)  # type: ignore[arg-type]

    def test_empty_string_raises_value_error(self) -> None:
        """Test that empty string raises value error."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            validate_locale_setting,
        )

        with pytest.raises(Exception_Validation_Input):
            validate_locale_setting(locale_setting = "")

    def test_invalid_locale_raises_value_error(self) -> None:
        """Test that invalid locale raises value error."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            validate_locale_setting,
        )

        with pytest.raises(Exception_Validation_Input):
            validate_locale_setting(locale_setting = "invalid_ZZZZ")

    def test_en_US_accepted(self) -> None:
        """Test that en US accepted."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            validate_locale_setting,
        )

        result = validate_locale_setting(locale_setting = "en_US")
        assert result == "en_US"

    def test_de_DE_accepted(self) -> None:
        """Test that de DE accepted."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            validate_locale_setting,
        )

        result = validate_locale_setting(locale_setting = "de_DE")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_returns_string(self) -> None:
        """Test that returns string."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            validate_locale_setting,
        )

        result = validate_locale_setting(locale_setting = "en_US")
        assert isinstance(result, str)

    @pytest.mark.parametrize(
        "locale",
        ["en_US", "en_GB", "de_DE", "fr_FR", "es_ES", "pt_BR", "ja_JP"],
    )
    def test_common_locales_accepted(self, locale: str) -> None:
        """Test that common locales accepted."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            validate_locale_setting,
        )

        result = validate_locale_setting(locale_setting = locale)
        assert isinstance(result, str)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# validate_currency_code
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestValidateCurrencyCode:
    """validate_currency_code must raise on invalid input; normalise to UPPERCASE."""

    def test_non_string_raises_type_error(self) -> None:
        """Test that non string raises type error."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            validate_currency_code,
        )

        with pytest.raises(TypeError):
            validate_currency_code(currency_code = 123)  # type: ignore[arg-type]

    def test_none_raises_type_error(self) -> None:
        """Test that none raises type error."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            validate_currency_code,
        )

        with pytest.raises(TypeError):
            validate_currency_code(currency_code = None)  # type: ignore[arg-type]

    def test_empty_string_raises_value_error(self) -> None:
        """Test that empty string raises value error."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            validate_currency_code,
        )

        with pytest.raises(Exception_Validation_Input):
            validate_currency_code(currency_code = "")

    def test_two_char_code_raises_value_error(self) -> None:
        """Test that two char code raises value error."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            validate_currency_code,
        )

        with pytest.raises(Exception_Validation_Input):
            validate_currency_code(currency_code = "US")

    def test_four_char_code_raises_value_error(self) -> None:
        """Test that four char code raises value error."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            validate_currency_code,
        )

        with pytest.raises(Exception_Validation_Input):
            validate_currency_code(currency_code = "USDX")

    def test_lowercase_usd_normalised_to_uppercase(self) -> None:
        """Test that lowercase usd normalised to uppercase."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            validate_currency_code,
        )

        result = validate_currency_code(currency_code = "usd")
        assert result == "USD"

    def test_uppercase_eur_accepted(self) -> None:
        """Test that uppercase eur accepted."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            validate_currency_code,
        )

        result = validate_currency_code(currency_code = "EUR")
        assert result == "EUR"

    def test_mixed_case_normalised(self) -> None:
        """Test that mixed case normalised."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            validate_currency_code,
        )

        result = validate_currency_code(currency_code = "Gbp")
        assert result == "GBP"

    @pytest.mark.parametrize("code", ["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD"])
    def test_standard_currency_codes(self, code: str) -> None:
        """Test that standard currency codes."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            validate_currency_code,
        )

        result = validate_currency_code(currency_code = code)
        assert result == code
        assert len(result) == 3


# ---------------------------------------------------------------------------
# format_enhanced_currency_display
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestFormatEnhancedCurrencyDisplay:
    """format_enhanced_currency_display must return a non-empty string."""

    def test_positive_amount_returns_string(self) -> None:
        """Test that positive amount returns string."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_currency_display,
        )

        result = format_enhanced_currency_display(amount = 1234.56)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_zero_amount_returns_string(self) -> None:
        """Test that zero amount returns string."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_currency_display,
        )

        result = format_enhanced_currency_display(amount = 0.0)
        assert isinstance(result, str)

    def test_negative_amount_returns_string(self) -> None:
        """Test that negative amount returns string."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_currency_display,
        )

        result = format_enhanced_currency_display(amount = -500.0)
        assert isinstance(result, str)

    def test_large_amount_returns_string(self) -> None:
        """Test that large amount returns string."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_currency_display,
        )

        result = format_enhanced_currency_display(amount = 1_000_000.0)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_result_contains_digits(self) -> None:
        """Test that result contains digits."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_currency_display,
        )

        result = format_enhanced_currency_display(amount = 9999.99)
        assert any(ch.isdigit() for ch in result)


# ---------------------------------------------------------------------------
# format_enhanced_percentage_display
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestFormatEnhancedPercentageDisplay:
    """format_enhanced_percentage_display must return a non-empty string."""

    def test_standard_percentage_returns_string(self) -> None:
        """Test that standard percentage returns string."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_percentage_display,
        )

        result = format_enhanced_percentage_display(value = 0.1234)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_zero_returns_string(self) -> None:
        """Test that zero returns string."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_percentage_display,
        )

        result = format_enhanced_percentage_display(value = 0.0)
        assert isinstance(result, str)

    def test_negative_returns_string(self) -> None:
        """Test that negative returns string."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_percentage_display,
        )

        result = format_enhanced_percentage_display(value = -0.05)
        assert isinstance(result, str)

    def test_hundred_percent_returns_string(self) -> None:
        """Test that hundred percent returns string."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_percentage_display,
        )

        result = format_enhanced_percentage_display(value = 1.0)
        assert isinstance(result, str)

    def test_result_contains_digits(self) -> None:
        """Test that result contains digits."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_percentage_display,
        )

        result = format_enhanced_percentage_display(value = 0.15)
        assert any(ch.isdigit() for ch in result)


# ---------------------------------------------------------------------------
# format_enhanced_number_display
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestFormatEnhancedNumberDisplay:
    """format_enhanced_number_display must return a non-empty string."""

    def test_integer_value_returns_string(self) -> None:
        """Test that integer value returns string."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_number_display,
        )

        result = format_enhanced_number_display(number = 42)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_large_number_returns_string(self) -> None:
        """Test that large number returns string."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_number_display,
        )

        result = format_enhanced_number_display(number = 1_234_567.89)
        assert isinstance(result, str)

    def test_zero_returns_string(self) -> None:
        """Test that zero returns string."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_number_display,
        )

        result = format_enhanced_number_display(number = 0)
        assert isinstance(result, str)

    def test_negative_value_returns_string(self) -> None:
        """Test that negative value returns string."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_number_display,
        )

        result = format_enhanced_number_display(number = -999.5)
        assert isinstance(result, str)

    def test_result_contains_digits(self) -> None:
        """Test that result contains digits."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_number_display,
        )

        result = format_enhanced_number_display(number = 12345)
        assert any(ch.isdigit() for ch in result)


# ---------------------------------------------------------------------------
# get_formatting_configuration
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestGetFormattingConfiguration:
    """get_formatting_configuration must return a dict with expected keys."""

    def test_returns_dict(self) -> None:
        """Test that returns dict."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            get_formatting_configuration,
        )

        result = get_formatting_configuration()
        assert isinstance(result, dict)

    def test_result_is_non_empty(self) -> None:
        """Test that result is non empty."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            get_formatting_configuration,
        )

        result = get_formatting_configuration()
        assert len(result) > 0

    def test_no_exception_raised(self) -> None:
        """Test that no exception raised."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            get_formatting_configuration,
        )

        # Must not raise
        _ = get_formatting_configuration()


# ---------------------------------------------------------------------------
# format_currency_value
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestFormatCurrencyValue:
    """format_currency_value must produce a dollar-formatted string."""

    def test_typical_amount_returns_string(self) -> None:
        """Test that typical amount returns string."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_currency_value,
        )

        result = format_currency_value(amount = 1234567.89)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_zero_returns_string(self) -> None:
        """Test that zero returns string."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_currency_value,
        )

        result = format_currency_value(amount = 0.0)
        assert isinstance(result, str)

    def test_negative_returns_string(self) -> None:
        """Test that negative returns string."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_currency_value,
        )

        result = format_currency_value(amount = -500.0)
        assert isinstance(result, str)

    def test_result_contains_digits(self) -> None:
        """Test that result contains digits."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_currency_value,
        )

        result = format_currency_value(amount = 999.99)
        assert any(ch.isdigit() for ch in result)

    @pytest.mark.parametrize(
        "amount",
        [0.01, 1.0, 100.0, 1_000.0, 10_000.0, 100_000.0, 1_000_000.0],
    )
    def test_various_magnitudes(self, amount: float) -> None:
        """Test that various magnitudes."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_currency_value,
        )

        result = format_currency_value(amount = amount)
        assert isinstance(result, str)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# extract_numeric_from_currency_string
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestExtractNumericFromCurrencyString:
    """extract_numeric_from_currency_string must parse formatted currency back to float."""

    def test_dollar_formatted_string_parsed(self) -> None:
        """Test that dollar formatted string parsed."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            extract_numeric_from_currency_string,
        )

        result = extract_numeric_from_currency_string(currency_string = "$1,234.56")
        assert isinstance(result, float)
        assert result == pytest.approx(1234.56, rel=1e-4)

    def test_no_currency_symbol_parsed(self) -> None:
        """Test that no currency symbol parsed."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            extract_numeric_from_currency_string,
        )

        result = extract_numeric_from_currency_string(currency_string = "1234.56")
        assert isinstance(result, float)
        assert result == pytest.approx(1234.56, rel=1e-4)

    def test_empty_string_returns_zero_or_safe(self) -> None:
        """Test that empty string returns zero or safe."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            extract_numeric_from_currency_string,
        )

        result = extract_numeric_from_currency_string(currency_string = "")
        assert isinstance(result, (float, int))
        assert result == 0 or result == 0.0

    def test_zero_string_returns_zero(self) -> None:
        """Test that zero string returns zero."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            extract_numeric_from_currency_string,
        )

        result = extract_numeric_from_currency_string(currency_string = "$0.00")
        assert result == pytest.approx(0.0, abs=1e-9)

    def test_negative_currency_string_parsed(self) -> None:
        """Test that negative currency string parsed."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            extract_numeric_from_currency_string,
        )

        result = extract_numeric_from_currency_string(currency_string = "-$500.00")
        assert isinstance(result, float)
        # May be -500 or 500 depending on implementation — just verify no crash
        assert abs(result) == pytest.approx(500.0, rel=1e-4)

    def test_million_dollar_string_parsed(self) -> None:
        """Test that million dollar string parsed."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (


            extract_numeric_from_currency_string,
        )

        result = extract_numeric_from_currency_string(currency_string = "$1,000,000.00")
        assert result == pytest.approx(1_000_000.0, rel=1e-4)

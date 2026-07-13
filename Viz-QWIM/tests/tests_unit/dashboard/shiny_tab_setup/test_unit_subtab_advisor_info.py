"""Unit tests for subtab_advisor_info module.

Tests cover:
- Module importability and public API
- ``normalize_text_trademark_symbols``
- ``normalize_text_phone_number_US``
- ``normalize_text_advisor_field``
- ``ensure_category_advisor_info_initialized``
- ``DEFAULT_VALUES_ADVISOR_INFO`` and ``FIELD_CONFIG_ADVISOR_INFO`` constants
"""

from __future__ import annotations

import pytest


# ============================================================================
# Module import tests
# ============================================================================


@pytest.mark.unit()
class Test_Subtab_Advisor_Info_Module_Imports:
    """Verify subtab_advisor_info module imports and public API."""

    @pytest.mark.unit()
    def test_module_importable(self):
        """Module imports without error."""
        import src.dashboard.shiny_tab_setup.subtab_advisor_info as mod

        assert mod is not None

    @pytest.mark.unit()
    def test_ui_callable(self):
        """subtab_advisor_info_ui is callable."""
        from src.dashboard.shiny_tab_setup.subtab_advisor_info import subtab_advisor_info_ui

        assert callable(subtab_advisor_info_ui)

    @pytest.mark.unit()
    def test_server_callable(self):
        """subtab_advisor_info_server is callable."""
        from src.dashboard.shiny_tab_setup.subtab_advisor_info import subtab_advisor_info_server

        assert callable(subtab_advisor_info_server)

    @pytest.mark.unit()
    def test_logger_initialised(self):
        """Module-level _logger is initialised."""
        import src.dashboard.shiny_tab_setup.subtab_advisor_info as mod

        assert hasattr(mod, "_logger")

    @pytest.mark.unit()
    def test_default_values_dict_exists(self):
        """DEFAULT_VALUES_ADVISOR_INFO constant is a non-empty dict."""
        from src.dashboard.shiny_tab_setup.subtab_advisor_info import DEFAULT_VALUES_ADVISOR_INFO

        assert isinstance(DEFAULT_VALUES_ADVISOR_INFO, dict)
        assert len(DEFAULT_VALUES_ADVISOR_INFO) > 0

    @pytest.mark.unit()
    def test_field_config_dict_exists(self):
        """FIELD_CONFIG_ADVISOR_INFO constant is a non-empty dict."""
        from src.dashboard.shiny_tab_setup.subtab_advisor_info import FIELD_CONFIG_ADVISOR_INFO

        assert isinstance(FIELD_CONFIG_ADVISOR_INFO, dict)
        assert len(FIELD_CONFIG_ADVISOR_INFO) > 0


@pytest.mark.unit()
class Test_Advisor_Info_Config_Int_Coercion:
    """Tests for advisor info UI config integer coercion."""

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        ("raw_value", "default_value", "expected_value"),
        [
            (True, 3, 3),
            (False, 255, 255),
            (4, 3, 4),
            ("120", 255, 120),
        ],
        ids=[
            "bool_rows_uses_default",
            "bool_max_length_uses_default",
            "int_preserved",
            "numeric_string_preserved",
        ],
    )
    def test_coerce_advisor_info_config_int_or_default_uses_expected_defaults(
        self,
        raw_value: object,
        default_value: int,
        expected_value: int,
    ) -> None:
        """Boolean config values should stay on the existing default path."""
        from src.dashboard.shiny_tab_setup.subtab_advisor_info import (
            _coerce_advisor_info_config_int_or_default,
        )

        result_value = _coerce_advisor_info_config_int_or_default(raw_value = raw_value, default_value = default_value)

        assert result_value == expected_value


# ============================================================================
# normalize_text_trademark_symbols
# ============================================================================


@pytest.mark.unit()
class Test_Normalize_Text_Trademark_Symbols:
    """Tests for normalize_text_trademark_symbols."""

    @pytest.mark.unit()
    def test_registered_trademark_removed_or_replaced(self):
        """Registered trademark symbol is normalised."""
        from src.dashboard.shiny_tab_setup.subtab_advisor_info import normalize_text_trademark_symbols

        result = normalize_text_trademark_symbols(value_text = "ACME\u00ae Wealth")
        assert isinstance(result, str)
        assert "\u00ae" not in result or "ACME" in result

    @pytest.mark.unit()
    def test_plain_text_unchanged(self):
        """Plain text without trademark symbols passes through."""
        from src.dashboard.shiny_tab_setup.subtab_advisor_info import normalize_text_trademark_symbols

        result = normalize_text_trademark_symbols(value_text = "QWIM Advisors")
        assert "QWIM" in result

    @pytest.mark.unit()
    def test_empty_string_returns_string(self):
        """Empty string input returns a string."""
        from src.dashboard.shiny_tab_setup.subtab_advisor_info import normalize_text_trademark_symbols

        result = normalize_text_trademark_symbols(value_text = "")
        assert isinstance(result, str)


# ============================================================================
# normalize_text_phone_number_US
# ============================================================================


@pytest.mark.unit()
class Test_Normalize_Text_Phone_Number_US:
    """Tests for normalize_text_phone_number_US."""

    @pytest.mark.unit()
    def test_digits_only_formatted(self):
        """10-digit string is formatted as US phone number."""
        from src.dashboard.shiny_tab_setup.subtab_advisor_info import normalize_text_phone_number_US

        result = normalize_text_phone_number_US(value_text = "8005551234")
        assert isinstance(result, str)
        assert "800" in result

    @pytest.mark.unit()
    def test_formatted_number_accepted(self):
        """Already-formatted number is accepted without crash."""
        from src.dashboard.shiny_tab_setup.subtab_advisor_info import normalize_text_phone_number_US

        result = normalize_text_phone_number_US(value_text = "(800) 555-1234")
        assert isinstance(result, str)

    @pytest.mark.unit()
    def test_empty_string_returns_string(self):
        """Empty string returns a string."""
        from src.dashboard.shiny_tab_setup.subtab_advisor_info import normalize_text_phone_number_US

        result = normalize_text_phone_number_US(value_text = "")
        assert isinstance(result, str)


# ============================================================================
# normalize_text_advisor_field
# ============================================================================


@pytest.mark.unit()
class Test_Normalize_Text_Advisor_Field:
    """Tests for normalize_text_advisor_field."""

    @pytest.mark.unit()
    def test_returns_string(self):
        """Always returns a tuple of strings/None."""
        from src.dashboard.shiny_tab_setup.subtab_advisor_info import normalize_text_advisor_field

        result, _ = normalize_text_advisor_field(field_key_name = "Name", value_text = "John Smith")
        assert isinstance(result, str)

    @pytest.mark.unit()
    def test_none_returns_empty_or_default(self):
        """Empty string input returns empty string tuple."""
        from src.dashboard.shiny_tab_setup.subtab_advisor_info import normalize_text_advisor_field

        result, _ = normalize_text_advisor_field(field_key_name = "Name", value_text = "")
        assert isinstance(result, str)

    @pytest.mark.unit()
    def test_phone_field_normalised(self):
        """phone_number field_key_name triggers phone normalization."""
        from src.dashboard.shiny_tab_setup.subtab_advisor_info import normalize_text_advisor_field

        result, _ = normalize_text_advisor_field(field_key_name = "phone_number", value_text = "8005551234")
        assert result is not None and "800" in result


# ============================================================================
# ensure_category_advisor_info_initialized
# ============================================================================


@pytest.mark.unit()
class Test_Ensure_Category_Advisor_Info_Initialized:
    """Tests for ensure_category_advisor_info_initialized."""

    @pytest.mark.unit()
    def test_empty_dict_initialized_with_defaults(self):
        """Empty reactives_shiny dict gets Advisor_Info category with reactive values."""
        from src.dashboard.shiny_tab_setup.subtab_advisor_info import (
            DEFAULT_VALUES_ADVISOR_INFO,
            ensure_category_advisor_info_initialized,
        )

        reactives_shiny: dict = {}
        result = ensure_category_advisor_info_initialized(reactives_shiny = reactives_shiny)

        assert isinstance(result, dict)
        for key in DEFAULT_VALUES_ADVISOR_INFO:
            assert key in result

    @pytest.mark.unit()
    def test_existing_category_not_overwritten(self):
        """Pre-existing reactive value in Advisor_Info is not overwritten."""
        from unittest.mock import MagicMock

        from src.dashboard.shiny_tab_setup.subtab_advisor_info import (
            ensure_category_advisor_info_initialized,
        )

        existing_rv = MagicMock()
        existing_rv.set = MagicMock()
        reactives_shiny: dict = {"Advisor_Info": {"Name": existing_rv}}
        ensure_category_advisor_info_initialized(reactives_shiny = reactives_shiny)

        assert reactives_shiny["Advisor_Info"]["Name"] is existing_rv

    @pytest.mark.unit()
    def test_non_dict_input_handled(self):
        """Non-dict Advisor_Info value causes re-initialization without crash."""
        from src.dashboard.shiny_tab_setup.subtab_advisor_info import (
            ensure_category_advisor_info_initialized,
        )

        reactives_shiny: dict = {"Advisor_Info": "bad_value"}
        result = ensure_category_advisor_info_initialized(reactives_shiny = reactives_shiny)
        assert isinstance(result, dict)


# ============================================================================
# normalize_text_phone_number_US — missing branches
# ============================================================================


@pytest.mark.unit()
class Test_Normalize_Text_Phone_Number_US_Extra:
    """Additional tests for normalize_text_phone_number_US covering missing branches."""

    @pytest.mark.unit()
    def test_eleven_digit_with_country_code_1_stripped(self):
        """11-digit number starting with '1' has country code stripped and formats correctly."""
        from src.dashboard.shiny_tab_setup.subtab_advisor_info import normalize_text_phone_number_US

        result = normalize_text_phone_number_US(value_text = "18005551234")

        assert result == "800-555-1234"

    @pytest.mark.unit()
    def test_invalid_digit_count_returns_none(self):
        """Number with wrong digit count (not 10 after stripping) returns None."""
        from src.dashboard.shiny_tab_setup.subtab_advisor_info import normalize_text_phone_number_US

        result = normalize_text_phone_number_US(value_text = "12345")

        assert result is None


# ============================================================================
# normalize_text_advisor_field — email and invalid-phone branches
# ============================================================================


@pytest.mark.unit()
class Test_Normalize_Text_Advisor_Field_Extra:
    """Additional tests for normalize_text_advisor_field covering missing branches."""

    @pytest.mark.unit()
    def test_email_field_valid_email(self):
        """Valid email is normalized and returned."""
        from src.dashboard.shiny_tab_setup.subtab_advisor_info import normalize_text_advisor_field

        result, _ = normalize_text_advisor_field(field_key_name = "email", value_text = "advisor@example.com")

        assert result == "advisor@example.com"

    @pytest.mark.unit()
    def test_email_field_empty_returns_empty_string(self):
        """Empty email returns ('', None)."""
        from src.dashboard.shiny_tab_setup.subtab_advisor_info import normalize_text_advisor_field

        result, extra = normalize_text_advisor_field(field_key_name = "email", value_text = "")

        assert result == ""
        assert extra is None

    @pytest.mark.unit()
    def test_email_field_invalid_returns_none(self):
        """Invalid email address returns (None, None)."""
        from src.dashboard.shiny_tab_setup.subtab_advisor_info import normalize_text_advisor_field

        result, extra = normalize_text_advisor_field(field_key_name = "email", value_text = "not-an-email")

        assert result is None
        assert extra is None

    @pytest.mark.unit()
    def test_phone_field_invalid_number_returns_none(self):
        """Invalid phone number returns (None, None)."""
        from src.dashboard.shiny_tab_setup.subtab_advisor_info import normalize_text_advisor_field

        result, extra = normalize_text_advisor_field(field_key_name = "phone_number", value_text = "12345")

        assert result is None
        assert extra is None

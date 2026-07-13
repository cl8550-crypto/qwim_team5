"""Unit tests for utils_tab_clients module.

Covers the pure-function layer:
- format_currency_display
- validate_financial_amount
- validate_age_range
- validate_string_input
- get_investor_data_from_dashboard (error-path only — requires no reactive mock)
- get_investor_primary_personal_info / get_investor_partner_personal_info (error paths)
"""

from __future__ import annotations

import pytest
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Configuration,
    Exception_Validation_Input,
)


# ============================================================================
# format_currency_display
# ============================================================================


@pytest.mark.unit()
class Test_Format_Currency_Display:
    """Tests for format_currency_display function."""

    @pytest.mark.unit()
    def test_integer_amount(self):
        """Integer amounts are formatted with dollar sign and commas."""
        from src.dashboard.shiny_utils.utils_tab_clients import format_currency_display

        result = format_currency_display(amount_value = 1234567)

        assert result == "$1,234,567"

    @pytest.mark.unit()
    def test_float_amount_truncated(self):
        """Float amounts are truncated to 0 decimal places."""
        from src.dashboard.shiny_utils.utils_tab_clients import format_currency_display

        result = format_currency_display(amount_value = 1234567.89)

        assert result == "$1,234,568"  # rounded to nearest integer via ,.0f

    @pytest.mark.unit()
    def test_zero_returns_dollar_zero(self):
        """Zero amount returns '$0'."""
        from src.dashboard.shiny_utils.utils_tab_clients import format_currency_display

        result = format_currency_display(amount_value = 0)

        assert result == "$0"

    @pytest.mark.unit()
    def test_none_returns_dollar_zero(self):
        """None amount returns '$0'."""
        from src.dashboard.shiny_utils.utils_tab_clients import format_currency_display

        result = format_currency_display(amount_value = None)

        assert result == "$0"

    @pytest.mark.unit()
    def test_string_numeric_accepted(self):
        """Numeric string is converted and formatted correctly."""
        from src.dashboard.shiny_utils.utils_tab_clients import format_currency_display

        result = format_currency_display(amount_value = "500000")

        assert result == "$500,000"

    @pytest.mark.unit()
    def test_non_numeric_string_raises_value_error(self):
        """Non-numeric string raises ValueError."""
        from src.dashboard.shiny_utils.utils_tab_clients import format_currency_display

        with pytest.raises(Exception_Validation_Input):
            format_currency_display(amount_value = "not a number")

    @pytest.mark.unit()
    def test_boolean_amount_raises_value_error(self):
        """Boolean values are rejected instead of formatting as $1 or $0."""
        from src.dashboard.shiny_utils.utils_tab_clients import format_currency_display

        with pytest.raises(Exception_Validation_Input, match="Invalid amount"):
            format_currency_display(amount_value = True)

    @pytest.mark.unit()
    def test_small_amount(self):
        """Small amounts (< 1000) have no comma separators."""
        from src.dashboard.shiny_utils.utils_tab_clients import format_currency_display

        result = format_currency_display(amount_value = 500)

        assert result == "$500"

    @pytest.mark.unit()
    def test_return_type_is_str(self):
        """Return type is str for valid numeric inputs."""
        from src.dashboard.shiny_utils.utils_tab_clients import format_currency_display

        result = format_currency_display(amount_value = 10000)

        assert isinstance(result, str)


# ============================================================================
# validate_financial_amount
# ============================================================================


@pytest.mark.unit()
class Test_Validate_Financial_Amount:
    """Tests for validate_financial_amount function."""

    @pytest.mark.unit()
    def test_positive_float_returned_unchanged(self):
        """Positive float is returned as float."""
        from src.dashboard.shiny_utils.utils_tab_clients import validate_financial_amount

        result = validate_financial_amount(amount_value = 1000.0)

        assert result == 1000.0
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_positive_integer_returned_as_float(self):
        """Positive integer is returned as float."""
        from src.dashboard.shiny_utils.utils_tab_clients import validate_financial_amount

        result = validate_financial_amount(amount_value = 5000)

        assert result == 5000.0
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_zero_returns_zero_float(self):
        """Zero is valid — returned as 0.0."""
        from src.dashboard.shiny_utils.utils_tab_clients import validate_financial_amount

        result = validate_financial_amount(amount_value = 0)

        assert result == 0.0

    @pytest.mark.unit()
    def test_none_returns_zero_float(self):
        """None is converted to 0.0."""
        from src.dashboard.shiny_utils.utils_tab_clients import validate_financial_amount

        result = validate_financial_amount(amount_value = None)

        assert result == 0.0

    @pytest.mark.unit()
    def test_negative_raises_value_error(self):
        """Negative amount raises ValueError."""
        from src.dashboard.shiny_utils.utils_tab_clients import validate_financial_amount

        with pytest.raises(Exception_Validation_Input, match="negative"):
            validate_financial_amount(amount_value = -500.0)

    @pytest.mark.unit()
    def test_non_numeric_string_raises_value_error(self):
        """Non-numeric string raises ValueError."""
        from src.dashboard.shiny_utils.utils_tab_clients import validate_financial_amount

        with pytest.raises(Exception_Validation_Input):
            validate_financial_amount(amount_value = "invalid")

    @pytest.mark.unit()
    def test_boolean_amount_raises_value_error(self):
        """Boolean values are rejected instead of coercing to numeric amounts."""
        from src.dashboard.shiny_utils.utils_tab_clients import validate_financial_amount

        with pytest.raises(Exception_Validation_Input, match="Invalid financial amount"):
            validate_financial_amount(amount_value = True)

    @pytest.mark.unit()
    def test_numeric_string_accepted(self):
        """Numeric string is coerced to float."""
        from src.dashboard.shiny_utils.utils_tab_clients import validate_financial_amount

        result = validate_financial_amount(amount_value = "250000")

        assert result == 250000.0

    @pytest.mark.parametrize("amount", [0.0, 0.01, 100.0, 1_000_000.0])
    @pytest.mark.unit()
    def test_various_valid_amounts(self, amount):
        """Various valid non-negative amounts are accepted."""
        from src.dashboard.shiny_utils.utils_tab_clients import validate_financial_amount

        result = validate_financial_amount(amount_value = amount)

        assert result == amount


# ============================================================================
# validate_age_range
# ============================================================================


@pytest.mark.unit()
class Test_Validate_Age_Range:
    """Tests for validate_age_range function."""

    @pytest.mark.unit()
    def test_valid_age_returned_as_int(self):
        """Age within valid range is returned as int."""
        from src.dashboard.shiny_utils.utils_tab_clients import validate_age_range

        result = validate_age_range(age_value = 45, minimum_age=18, maximum_age=100, age_type_description="current age")

        assert result == 45
        assert isinstance(result, int)

    @pytest.mark.unit()
    def test_minimum_boundary_accepted(self):
        """Age exactly at minimum is accepted."""
        from src.dashboard.shiny_utils.utils_tab_clients import validate_age_range

        result = validate_age_range(age_value = 18, minimum_age=18, maximum_age=100, age_type_description="age")

        assert result == 18

    @pytest.mark.unit()
    def test_maximum_boundary_accepted(self):
        """Age exactly at maximum is accepted."""
        from src.dashboard.shiny_utils.utils_tab_clients import validate_age_range

        result = validate_age_range(age_value = 100, minimum_age=18, maximum_age=100, age_type_description="age")

        assert result == 100

    @pytest.mark.unit()
    def test_below_minimum_raises_value_error(self):
        """Age below minimum raises ValueError with 'between' in message."""
        from src.dashboard.shiny_utils.utils_tab_clients import validate_age_range

        with pytest.raises(Exception_Validation_Input, match="between"):
            validate_age_range(age_value = 17, minimum_age=18, maximum_age=100, age_type_description="age")

    @pytest.mark.unit()
    def test_above_maximum_raises_value_error(self):
        """Age above maximum raises ValueError."""
        from src.dashboard.shiny_utils.utils_tab_clients import validate_age_range

        with pytest.raises(Exception_Validation_Input):
            validate_age_range(age_value = 101, minimum_age=18, maximum_age=100, age_type_description="age")

    @pytest.mark.unit()
    def test_none_raises_value_error(self):
        """None age raises ValueError."""
        from src.dashboard.shiny_utils.utils_tab_clients import validate_age_range

        with pytest.raises(Exception_Validation_Input):
            validate_age_range(age_value = None, minimum_age=18, maximum_age=100, age_type_description="age")

    @pytest.mark.unit()
    def test_string_numeric_age_accepted(self):
        """Numeric string is coerced to int."""
        from src.dashboard.shiny_utils.utils_tab_clients import validate_age_range

        result = validate_age_range(age_value = "65", minimum_age=18, maximum_age=100, age_type_description="age")

        assert result == 65

    @pytest.mark.unit()
    def test_non_numeric_string_raises_value_error(self):
        """Non-numeric string raises ValueError."""
        from src.dashboard.shiny_utils.utils_tab_clients import validate_age_range

        with pytest.raises(Exception_Validation_Input):
            validate_age_range(age_value = "old", minimum_age=18, maximum_age=100, age_type_description="age")

    @pytest.mark.unit()
    def test_boolean_age_raises_value_error(self):
        """Boolean values are rejected instead of coercing to age 1 or 0."""
        from src.dashboard.shiny_utils.utils_tab_clients import validate_age_range

        with pytest.raises(Exception_Validation_Input, match="Invalid age"):
            validate_age_range(age_value = True, minimum_age=18, maximum_age=100, age_type_description="age")

    @pytest.mark.unit()
    def test_age_type_description_in_error_message(self):
        """Age type description appears in error message for None input."""
        from src.dashboard.shiny_utils.utils_tab_clients import validate_age_range

        with pytest.raises(Exception_Validation_Input, match="retirement age"):
            validate_age_range(age_value = None, minimum_age=40, maximum_age=100, age_type_description="retirement age")


# ============================================================================
# validate_string_input
# ============================================================================


@pytest.mark.unit()
class Test_Validate_String_Input:
    """Tests for validate_string_input function."""

    @pytest.mark.unit()
    def test_valid_string_returned_stripped(self):
        """Valid string with surrounding whitespace is stripped and returned."""
        from src.dashboard.shiny_utils.utils_tab_clients import validate_string_input

        result = validate_string_input(input_value = "  John Doe  ", field_description="name")

        assert result == "John Doe"


# ============================================================================
# _parse_currency_string
# ============================================================================


@pytest.mark.unit()
class Test_Parse_Currency_String:
    """Tests for _parse_currency_string helper."""

    @pytest.mark.unit()
    def test_comma_separated_string_parsed(self):
        """Currency string with commas converts to integer."""
        from src.dashboard.shiny_utils.utils_tab_clients import _parse_currency_string

        assert _parse_currency_string(value_raw = "100,000") == 100000

    @pytest.mark.unit()
    def test_plain_number_string_parsed(self):
        """Plain numeric string converts to integer."""
        from src.dashboard.shiny_utils.utils_tab_clients import _parse_currency_string

        assert _parse_currency_string(value_raw = "50000") == 50000

    @pytest.mark.unit()
    def test_none_returns_zero(self):
        """None input returns 0."""
        from src.dashboard.shiny_utils.utils_tab_clients import _parse_currency_string

        assert _parse_currency_string(value_raw = None) == 0

    @pytest.mark.unit()
    def test_empty_string_returns_zero(self):
        """Empty string returns 0."""
        from src.dashboard.shiny_utils.utils_tab_clients import _parse_currency_string

        assert _parse_currency_string(value_raw = "") == 0

    @pytest.mark.unit()
    def test_boolean_returns_zero(self):
        """Boolean input stays on the existing zero-default path."""
        from src.dashboard.shiny_utils.utils_tab_clients import _parse_currency_string

        assert _parse_currency_string(value_raw = True) == 0

    @pytest.mark.unit()
    def test_non_numeric_string_returns_zero(self):
        """Non-numeric string returns 0."""
        from src.dashboard.shiny_utils.utils_tab_clients import _parse_currency_string

        assert _parse_currency_string(value_raw = "abc") == 0

    @pytest.mark.unit()
    def test_integer_input_passes_through(self):
        """Integer input converts correctly."""
        from src.dashboard.shiny_utils.utils_tab_clients import _parse_currency_string

        assert _parse_currency_string(value_raw = 75000) == 75000


# ============================================================================
# _blank_partner_section
# ============================================================================


@pytest.mark.unit()
class Test_Blank_Partner_Section:
    """Tests for _blank_partner_section helper."""

    @pytest.mark.unit()
    def test_string_fields_blanked_to_empty(self):
        """String values in client_partner are cleared to ''."""
        from src.dashboard.shiny_utils.utils_tab_clients import _blank_partner_section

        section = {
            "client_primary": {"name": "Alice"},
            "client_partner": {"name": "Bob", "status_marital": "Married"},
        }
        result = _blank_partner_section(section_data = section)

        assert result["client_partner"]["name"] == ""
        assert result["client_partner"]["status_marital"] == ""

    @pytest.mark.unit()
    def test_numeric_fields_blanked_to_zero(self):
        """Numeric values in client_partner are cleared to 0."""
        from src.dashboard.shiny_utils.utils_tab_clients import _blank_partner_section

        section = {
            "client_primary": {"assets_taxable": 100000},
            "client_partner": {"assets_taxable": 50000},
        }
        result = _blank_partner_section(section_data = section)

        assert result["client_partner"]["assets_taxable"] == 0

    @pytest.mark.unit()
    def test_bool_fields_blanked_to_false(self):
        """Bool values in client_partner are cleared to False."""
        from src.dashboard.shiny_utils.utils_tab_clients import _blank_partner_section

        section = {
            "client_primary": {"cola_indexed": True},
            "client_partner": {"cola_indexed": True},
        }
        result = _blank_partner_section(section_data = section)

        assert result["client_partner"]["cola_indexed"] is False

    @pytest.mark.unit()
    def test_missing_client_partner_returns_empty_dict(self):
        """Section without client_partner gets empty dict partner."""
        from src.dashboard.shiny_utils.utils_tab_clients import _blank_partner_section

        section = {"client_primary": {"name": "Alice"}}
        result = _blank_partner_section(section_data = section)

        assert result["client_partner"] == {}

    @pytest.mark.unit()
    def test_primary_data_unchanged(self):
        """Primary client data is not modified."""
        from src.dashboard.shiny_utils.utils_tab_clients import _blank_partner_section

        section = {
            "client_primary": {"name": "Alice", "assets_taxable": 200000},
            "client_partner": {"name": "Bob", "assets_taxable": 100000},
        }
        result = _blank_partner_section(section_data = section)

        assert result["client_primary"]["name"] == "Alice"
        assert result["client_primary"]["assets_taxable"] == 200000


# ============================================================================
# _apply_partner_blanking
# ============================================================================


@pytest.mark.unit()
class Test_Apply_Partner_Blanking:
    """Tests for _apply_partner_blanking helper."""

    @pytest.mark.unit()
    def test_all_client_sections_blanked(self):
        """All sections with client_partner have their partner data blanked."""
        from src.dashboard.shiny_utils.utils_tab_clients import _apply_partner_blanking

        extracted = {
            "Advisor_Info": {"name": "John Advisor"},
            "Personal_Info": {
                "client_primary": {"name": "Alice"},
                "client_partner": {"name": "Bob"},
            },
            "Assets": {
                "client_primary": {"assets_taxable": 100000},
                "client_partner": {"assets_taxable": 50000},
            },
        }
        result = _apply_partner_blanking(extracted_data = extracted)

        assert result["Personal_Info"]["client_partner"]["name"] == ""
        assert result["Assets"]["client_partner"]["assets_taxable"] == 0
        assert result["Advisor_Info"] == {"name": "John Advisor"}

    @pytest.mark.unit()
    def test_non_client_sections_unchanged(self):
        """Sections without client_partner key are passed through unchanged."""
        from src.dashboard.shiny_utils.utils_tab_clients import _apply_partner_blanking

        extracted = {
            "Advisor_Info": {"name": "Advisor"},
            "Personal_Info": {
                "client_primary": {"name": "Alice"},
                "client_partner": {"name": "Bob"},
            },
        }
        result = _apply_partner_blanking(extracted_data = extracted)

        assert result["Advisor_Info"] == {"name": "Advisor"}


# ============================================================================
# sync_user_inputs_shiny_from_extracted_worksheet
# ============================================================================


@pytest.mark.unit()
class Test_Sync_User_Inputs_Shiny_From_Extracted_Worksheet:
    """Tests for sync_user_inputs_shiny_from_extracted_worksheet."""

    @pytest.mark.unit()
    def test_invalid_reactives_shiny_returns_early(self):
        """Non-dict reactives_shiny is handled gracefully."""
        from src.dashboard.shiny_utils.utils_tab_clients import (
            sync_user_inputs_shiny_from_extracted_worksheet,
        )

        sync_user_inputs_shiny_from_extracted_worksheet(
            reactives_shiny=None,  # type: ignore[arg-type]
            extracted_worksheet_data={},
            has_client_partner=False,
        )

    @pytest.mark.unit()
    def test_invalid_extracted_data_returns_early(self):
        """Non-dict extracted_worksheet_data is handled gracefully."""
        from src.dashboard.shiny_utils.utils_tab_clients import (
            sync_user_inputs_shiny_from_extracted_worksheet,
        )

        sync_user_inputs_shiny_from_extracted_worksheet(
            reactives_shiny={},
            extracted_worksheet_data=None,  # type: ignore[arg-type]
            has_client_partner=False,
        )

    @pytest.mark.unit()
    def test_no_reactive_value_logs_warning(self, caplog):
        """Missing Extracted_Worksheet_Data reactive is handled without crash."""
        import logging

        from src.dashboard.shiny_utils.utils_tab_clients import (
            sync_user_inputs_shiny_from_extracted_worksheet,
        )

        reactives_shiny = {"Inner_Variables_Shiny": {}}
        with caplog.at_level(logging.WARNING):
            sync_user_inputs_shiny_from_extracted_worksheet(
                reactives_shiny=reactives_shiny,
                extracted_worksheet_data={"Personal_Info": {}},
                has_client_partner=True,
            )

    @pytest.mark.unit()
    def test_has_client_partner_true_stores_raw_data(self):
        """When has_client_partner=True, raw data is stored unchanged."""
        from unittest.mock import MagicMock

        from src.dashboard.shiny_utils.utils_tab_clients import (
            sync_user_inputs_shiny_from_extracted_worksheet,
        )

        mock_rv = MagicMock()
        extracted = {
            "Personal_Info": {
                "client_primary": {"name": "Alice"},
                "client_partner": {"name": "Bob"},
            },
        }
        reactives_shiny = {"Inner_Variables_Shiny": {"Extracted_Worksheet_Data": mock_rv}}
        sync_user_inputs_shiny_from_extracted_worksheet(
            reactives_shiny=reactives_shiny,
            extracted_worksheet_data=extracted,
            has_client_partner=True,
        )

        mock_rv.set.assert_called_once_with(extracted)

    @pytest.mark.unit()
    def test_has_client_partner_false_blanks_partner(self):
        """When has_client_partner=False, partner sections are blanked before storing."""
        from unittest.mock import MagicMock

        from src.dashboard.shiny_utils.utils_tab_clients import (
            sync_user_inputs_shiny_from_extracted_worksheet,
        )

        mock_rv = MagicMock()
        extracted = {
            "Personal_Info": {
                "client_primary": {"name": "Alice"},
                "client_partner": {"name": "Bob"},
            },
        }
        reactives_shiny = {"Inner_Variables_Shiny": {"Extracted_Worksheet_Data": mock_rv}}
        sync_user_inputs_shiny_from_extracted_worksheet(
            reactives_shiny=reactives_shiny,
            extracted_worksheet_data=extracted,
            has_client_partner=False,
        )

        stored = mock_rv.set.call_args[0][0]
        assert stored["Personal_Info"]["client_partner"]["name"] == ""

    @pytest.mark.unit()
    def test_none_raises_value_error(self):
        """None input raises ValueError."""
        from src.dashboard.shiny_utils.utils_tab_clients import validate_string_input

        with pytest.raises(Exception_Validation_Input):
            validate_string_input(input_value = None, field_description="first name")

    @pytest.mark.unit()
    def test_empty_string_raises_value_error(self):
        """Empty string raises ValueError."""
        from src.dashboard.shiny_utils.utils_tab_clients import validate_string_input

        with pytest.raises(Exception_Validation_Input):
            validate_string_input(input_value = "", field_description="last name")

    @pytest.mark.unit()
    def test_whitespace_only_raises_value_error(self):
        """Whitespace-only string is treated as empty and raises ValueError."""
        from src.dashboard.shiny_utils.utils_tab_clients import validate_string_input

        with pytest.raises(Exception_Validation_Input):
            validate_string_input(input_value = "   ", field_description="email")

    @pytest.mark.unit()
    def test_field_description_in_error_message(self):
        """Field description appears in the ValueError message."""
        from src.dashboard.shiny_utils.utils_tab_clients import validate_string_input

        with pytest.raises(Exception_Validation_Input, match="email address"):
            validate_string_input(input_value = None, field_description="email address")

    @pytest.mark.parametrize("valid_name", ["Alice", "Bob Smith", "José", "A B C"])
    @pytest.mark.unit()
    def test_various_valid_strings(self, valid_name):
        """Various non-empty strings are accepted without error."""
        from src.dashboard.shiny_utils.utils_tab_clients import validate_string_input

        result = validate_string_input(input_value = valid_name, field_description="name")

        assert result == valid_name


# ============================================================================
# get_investor_data_from_dashboard — error paths only
# ============================================================================


@pytest.mark.unit()
class Test_Get_Investor_Data_From_Dashboard_Error_Paths:
    """Tests for error paths in get_investor_data_from_dashboard.

    Full happy-path testing requires a Shiny reactive context.
    These tests cover defensive validation that fires before any reactive access.
    """

    @pytest.mark.unit()
    def test_none_input_raises_value_error(self):
        """None reactives_shiny raises ValueError."""
        from src.dashboard.shiny_utils.utils_tab_clients import get_investor_data_from_dashboard

        with pytest.raises((Exception_Validation_Input, Exception_Configuration, ValueError, RuntimeError, KeyError)):
            get_investor_data_from_dashboard(reactives_shiny = None)  # type: ignore[arg-type]

    @pytest.mark.unit()
    def test_empty_dict_raises_or_runtime_error(self):
        """Empty dict raises ValueError or RuntimeError (data utilities may be unavailable)."""
        from src.dashboard.shiny_utils.utils_tab_clients import get_investor_data_from_dashboard

        with pytest.raises((Exception_Validation_Input, Exception_Configuration, ValueError, RuntimeError, KeyError)):
            get_investor_data_from_dashboard(reactives_shiny = {})

    @pytest.mark.unit()
    def test_missing_user_inputs_shiny_key_raises(self):
        """Missing 'User_Inputs_Shiny' key raises KeyError or RuntimeError."""
        from src.dashboard.shiny_utils.utils_tab_clients import get_investor_data_from_dashboard

        bad_reactives = {"Inner_Variables_Shiny": {}}

        with pytest.raises((KeyError, RuntimeError)):
            get_investor_data_from_dashboard(reactives_shiny = bad_reactives)


# ============================================================================
# Regression tests
# ============================================================================


@pytest.mark.regression()
class Test_Utils_Tab_Clients_Regression:
    """Regression tests ensuring pure-function behaviors remain stable."""

    @pytest.mark.unit()
    def test_format_currency_known_values(self):
        """Known input-output pairs for format_currency_display."""
        from src.dashboard.shiny_utils.utils_tab_clients import format_currency_display

        cases = [
            (0, "$0"),
            (1000, "$1,000"),
            (1000000, "$1,000,000"),
        ]

        for amount, expected in cases:
            result = format_currency_display(amount_value = amount)
            assert result == expected, f"format_currency_display({amount}) = {result!r}, expected {expected!r}"

    @pytest.mark.unit()
    def test_validate_financial_amount_none_regression(self):
        """None → 0.0 must remain stable."""
        from src.dashboard.shiny_utils.utils_tab_clients import validate_financial_amount

        assert validate_financial_amount(amount_value = None) == 0.0

    @pytest.mark.unit()
    def test_validate_age_range_valid_regression(self):
        """Known valid ages always return expected int value."""
        from src.dashboard.shiny_utils.utils_tab_clients import validate_age_range

        result = validate_age_range(age_value = 65, minimum_age=18, maximum_age=100, age_type_description="age")

        assert result == 65

    @pytest.mark.unit()
    def test_validate_string_input_strips_whitespace_regression(self):
        """Leading/trailing whitespace is always stripped."""
        from src.dashboard.shiny_utils.utils_tab_clients import validate_string_input

        assert validate_string_input(input_value = "  Alice  ", field_description="name") == "Alice"

    @pytest.mark.unit()
    def test_format_currency_return_type_always_str_or_none(self):
        """format_currency_display always returns str | None."""
        from src.dashboard.shiny_utils.utils_tab_clients import format_currency_display


        valid_inputs = [0, 1, 100.5, None, "500"]

        for inp in valid_inputs:
            result = format_currency_display(amount_value = inp)
            assert result is None or isinstance(result, str), (
                f"Unexpected return type {type(result)} for input {inp!r}"
            )


# ============================================================================
# validate_age_range — missing-min/max branches
# ============================================================================


@pytest.mark.unit()
class Test_Validate_Age_Range_Missing_Bounds:
    """Tests for validate_age_range when min or max bounds are not provided."""

    @pytest.mark.unit()
    def test_no_minimum_age_raises(self):
        """Calling without minimum_age and min_age raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.utils_tab_clients import validate_age_range

        with pytest.raises(Exception_Validation_Input, match="min_age"):
            validate_age_range(age_value = 50, maximum_age=100, age_type_description="age")

    @pytest.mark.unit()
    def test_no_maximum_age_raises(self):
        """Calling without maximum_age and max_age raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.utils_tab_clients import validate_age_range

        with pytest.raises(Exception_Validation_Input, match="max_age"):
            validate_age_range(age_value = 50, minimum_age=18, age_type_description="age")


# ============================================================================
# get_investor_data_from_dashboard — happy path with mock
# ============================================================================


@pytest.mark.unit()
class Test_Get_Investor_Data_From_Dashboard_Happy_Path:
    """Happy-path tests for get_investor_data_from_dashboard using a mock."""

    @pytest.mark.unit()
    def test_returns_four_dicts_with_mock(self):
        """With mocked get_value_from_reactives_shiny, returns four data dicts."""
        from unittest.mock import patch

        from src.dashboard.shiny_utils.utils_tab_clients import get_investor_data_from_dashboard

        reactives_shiny = {"User_Inputs_Shiny": {}}
        with patch(
            "src.dashboard.shiny_utils.utils_tab_clients.get_value_from_reactives_shiny",
            return_value=None,
        ):
            personal_info, assets, goals, income = get_investor_data_from_dashboard(reactives_shiny = reactives_shiny)

        assert isinstance(personal_info, dict)
        assert isinstance(assets, dict)
        assert isinstance(goals, dict)
        assert isinstance(income, dict)

    @pytest.mark.unit()
    def test_primary_and_partner_keys_present(self):
        """Result dicts contain primary, partner, and combined keys."""
        from unittest.mock import patch

        from src.dashboard.shiny_utils.utils_tab_clients import get_investor_data_from_dashboard

        reactives_shiny = {"User_Inputs_Shiny": {}}
        with patch(
            "src.dashboard.shiny_utils.utils_tab_clients.get_value_from_reactives_shiny",
            return_value=None,
        ):
            personal_info, assets, goals, income = get_investor_data_from_dashboard(reactives_shiny = reactives_shiny)

        assert "primary" in personal_info
        assert "partner" in personal_info
        assert "combined" in assets
        assert "combined" in goals
        assert "combined" in income

    @pytest.mark.unit()
    def test_known_error_reraises_key_error(self):
        """KeyError from a getter propagates out as KeyError."""
        from unittest.mock import patch

        from src.dashboard.shiny_utils.utils_tab_clients import get_investor_data_from_dashboard

        reactives_shiny = {"User_Inputs_Shiny": {}}
        with patch(
            "src.dashboard.shiny_utils.utils_tab_clients.get_investor_primary_personal_info",
            side_effect=KeyError("test-key"),
        ):
            with pytest.raises(KeyError):
                get_investor_data_from_dashboard(reactives_shiny = reactives_shiny)

    @pytest.mark.unit()
    def test_unexpected_error_raises_exception_configuration(self):
        """Unexpected error from a getter raises Exception_Configuration."""
        from unittest.mock import patch

        from src.dashboard.shiny_utils.utils_tab_clients import get_investor_data_from_dashboard

        reactives_shiny = {"User_Inputs_Shiny": {}}
        with patch(
            "src.dashboard.shiny_utils.utils_tab_clients.get_investor_primary_personal_info",
            side_effect=OSError("disk error"),
        ):
            with pytest.raises(Exception_Configuration):
                get_investor_data_from_dashboard(reactives_shiny = reactives_shiny)


# ============================================================================
# get_investor_* getter functions
# ============================================================================


@pytest.mark.unit()
class Test_Get_Investor_Getter_Functions:
    """Tests for individual investor getter functions using a mock."""

    @pytest.mark.unit()
    def test_get_investor_primary_personal_info_returns_dict(self):
        """get_investor_primary_personal_info returns a dict with name key."""
        from unittest.mock import patch

        from src.dashboard.shiny_utils.utils_tab_clients import get_investor_primary_personal_info

        with patch(
            "src.dashboard.shiny_utils.utils_tab_clients.get_value_from_reactives_shiny",
            return_value=None,
        ):
            result = get_investor_primary_personal_info(reactives_shiny = {})

        assert isinstance(result, dict)
        assert result["name"] == "Primary Client"

    @pytest.mark.unit()
    def test_get_investor_partner_personal_info_returns_dict(self):
        """get_investor_partner_personal_info returns a dict with name key."""
        from unittest.mock import patch

        from src.dashboard.shiny_utils.utils_tab_clients import get_investor_partner_personal_info

        with patch(
            "src.dashboard.shiny_utils.utils_tab_clients.get_value_from_reactives_shiny",
            return_value=None,
        ):
            result = get_investor_partner_personal_info(reactives_shiny = {})

        assert isinstance(result, dict)
        assert result["name"] == "Partner Client"

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        ("getter_name", "expected_ages"),
        [
            (
                "get_investor_primary_personal_info",
                {"age_current": 35, "age_retirement": 65, "age_income_starting": 65},
            ),
            (
                "get_investor_partner_personal_info",
                {"age_current": 33, "age_retirement": 65, "age_income_starting": 65},
            ),
        ],
    )
    def test_personal_info_getters_treat_boolean_age_values_as_defaults(self, getter_name, expected_ages):
        """Boolean reactive age values stay on the established getter defaults."""
        from unittest.mock import patch

        import src.dashboard.shiny_utils.utils_tab_clients as utils_tab_clients

        getter = getattr(utils_tab_clients, getter_name)

        def _mock_get_value_from_reactives_shiny(*args, **kwargs):
            key_name = kwargs.get("key_name", "")
            if "_Age_" in key_name:
                return True
            return None

        with patch(
            "src.dashboard.shiny_utils.utils_tab_clients.get_value_from_reactives_shiny",
            side_effect=_mock_get_value_from_reactives_shiny,
        ):
            result = getter(reactives_shiny={})

        assert result["name"] in {"Primary Client", "Partner Client"}
        assert result["age_current"] == expected_ages["age_current"]
        assert result["age_retirement"] == expected_ages["age_retirement"]
        assert result["age_income_starting"] == expected_ages["age_income_starting"]

    @pytest.mark.unit()
    def test_get_investor_primary_assets_returns_float_values(self):
        """get_investor_primary_assets returns dict with float values defaulting to 0.0."""
        from unittest.mock import patch

        from src.dashboard.shiny_utils.utils_tab_clients import get_investor_primary_assets

        with patch(
            "src.dashboard.shiny_utils.utils_tab_clients.get_value_from_reactives_shiny",
            return_value=None,
        ):
            result = get_investor_primary_assets(reactives_shiny = {})

        assert result["taxable"] == 0.0
        assert result["tax_deferred"] == 0.0
        assert result["tax_free"] == 0.0

    @pytest.mark.unit()
    def test_get_investor_partner_assets_returns_float_values(self):
        """get_investor_partner_assets returns dict with float values defaulting to 0.0."""
        from unittest.mock import patch

        from src.dashboard.shiny_utils.utils_tab_clients import get_investor_partner_assets

        with patch(
            "src.dashboard.shiny_utils.utils_tab_clients.get_value_from_reactives_shiny",
            return_value=None,
        ):
            result = get_investor_partner_assets(reactives_shiny = {})

        assert result["taxable"] == 0.0

    @pytest.mark.unit()
    def test_get_investor_primary_goals_returns_float_values(self):
        """get_investor_primary_goals returns dict with float values defaulting to 0.0."""
        from unittest.mock import patch

        from src.dashboard.shiny_utils.utils_tab_clients import get_investor_primary_goals

        with patch(
            "src.dashboard.shiny_utils.utils_tab_clients.get_value_from_reactives_shiny",
            return_value=None,
        ):
            result = get_investor_primary_goals(reactives_shiny = {})

        assert result["essential"] == 0.0

    @pytest.mark.unit()
    def test_get_investor_partner_goals_returns_float_values(self):
        """get_investor_partner_goals returns dict with float values."""
        from unittest.mock import patch

        from src.dashboard.shiny_utils.utils_tab_clients import get_investor_partner_goals

        with patch(
            "src.dashboard.shiny_utils.utils_tab_clients.get_value_from_reactives_shiny",
            return_value=None,
        ):
            result = get_investor_partner_goals(reactives_shiny = {})

        assert isinstance(result, dict)

    @pytest.mark.unit()
    def test_get_investor_primary_income_returns_float_values(self):
        """get_investor_primary_income returns dict with float values defaulting to 0.0."""
        from unittest.mock import patch

        from src.dashboard.shiny_utils.utils_tab_clients import get_investor_primary_income

        with patch(
            "src.dashboard.shiny_utils.utils_tab_clients.get_value_from_reactives_shiny",
            return_value=None,
        ):
            result = get_investor_primary_income(reactives_shiny = {})

        assert result["social_security"] == 0.0

    @pytest.mark.unit()
    def test_get_investor_partner_income_returns_float_values(self):
        """get_investor_partner_income returns dict with float values."""
        from unittest.mock import patch

        from src.dashboard.shiny_utils.utils_tab_clients import get_investor_partner_income

        with patch(
            "src.dashboard.shiny_utils.utils_tab_clients.get_value_from_reactives_shiny",
            return_value=None,
        ):
            result = get_investor_partner_income(reactives_shiny = {})

        assert isinstance(result, dict)

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        ("getter_name", "expected_keys"),
        [
            ("get_investor_primary_assets", {"taxable", "tax_deferred", "tax_free"}),
            ("get_investor_partner_assets", {"taxable", "tax_deferred", "tax_free"}),
            ("get_investor_primary_goals", {"essential", "important", "aspirational"}),
            ("get_investor_partner_goals", {"essential", "important", "aspirational"}),
            (
                "get_investor_primary_income",
                {"social_security", "pension", "annuity_existing", "other"},
            ),
            (
                "get_investor_partner_income",
                {"social_security", "pension", "annuity_existing", "other"},
            ),
        ],
    )
    def test_getters_treat_boolean_numeric_values_as_zero_defaults(self, getter_name, expected_keys):
        """Boolean reactive numeric values stay on the existing 0.0 default path."""
        from unittest.mock import patch

        import src.dashboard.shiny_utils.utils_tab_clients as utils_tab_clients

        getter = getattr(utils_tab_clients, getter_name)

        with patch(
            "src.dashboard.shiny_utils.utils_tab_clients.get_value_from_reactives_shiny",
            return_value=True,
        ):
            result = getter(reactives_shiny={})

        assert set(result) == expected_keys
        assert all(value == 0.0 for value in result.values())


# ============================================================================
# _calculate_* helper functions
# ============================================================================


@pytest.mark.unit()
class Test_Calculate_Helper_Functions:
    """Tests for _calculate_individual_totals and _calculate_combined_* helpers."""

    def _make_assets(self, taxable=0.0, tax_deferred=0.0, tax_free=0.0):
        return {"taxable": taxable, "tax_deferred": tax_deferred, "tax_free": tax_free}

    def _make_goals(self, essential=0.0, important=0.0, aspirational=0.0):
        return {"essential": essential, "important": important, "aspirational": aspirational}

    def _make_income(self, ss=0.0, pension=0.0, annuity=0.0, other=0.0):
        return {"social_security": ss, "pension": pension, "annuity_existing": annuity, "other": other}

    @pytest.mark.unit()
    def test_calculate_individual_totals_sums_correctly(self):
        """_calculate_individual_totals fills 'total' key for all six dicts."""
        from src.dashboard.shiny_utils.utils_tab_clients import _calculate_individual_totals

        pa = self._make_assets(100.0, 200.0, 300.0)
        qa = self._make_assets(10.0, 20.0, 30.0)
        pg = self._make_goals(50.0, 60.0, 70.0)
        qg = self._make_goals(5.0, 6.0, 7.0)
        pi = self._make_income(1000.0, 500.0, 200.0, 100.0)
        qi = self._make_income(100.0, 50.0, 20.0, 10.0)

        _calculate_individual_totals(primary_assets = pa, partner_assets = qa, primary_goals = pg, partner_goals = qg, primary_income = pi, partner_income = qi)

        assert pa["total"] == 600.0
        assert qa["total"] == 60.0
        assert pg["total"] == 180.0
        assert qg["total"] == 18.0
        assert pi["total"] == 1800.0
        assert qi["total"] == 180.0

    @pytest.mark.unit()
    def test_calculate_combined_assets_sums_correctly(self):
        """_calculate_combined_assets returns combined dict with total."""
        from src.dashboard.shiny_utils.utils_tab_clients import _calculate_combined_assets

        pa = {**self._make_assets(100.0, 200.0, 300.0), "total": 600.0}
        qa = {**self._make_assets(10.0, 20.0, 30.0), "total": 60.0}

        result = _calculate_combined_assets(primary_assets = pa, partner_assets = qa)

        assert result["taxable"] == 110.0
        assert result["total"] == 660.0

    @pytest.mark.unit()
    def test_calculate_combined_goals_sums_correctly(self):
        """_calculate_combined_goals returns combined dict with total."""
        from src.dashboard.shiny_utils.utils_tab_clients import _calculate_combined_goals

        pg = {**self._make_goals(50.0, 60.0, 70.0), "total": 180.0}
        qg = {**self._make_goals(5.0, 6.0, 7.0), "total": 18.0}

        result = _calculate_combined_goals(primary_goals = pg, partner_goals = qg)

        assert result["essential"] == 55.0
        assert result["total"] == 198.0

    @pytest.mark.unit()
    def test_calculate_combined_income_sums_correctly(self):
        """_calculate_combined_income returns combined dict with total."""
        from src.dashboard.shiny_utils.utils_tab_clients import _calculate_combined_income

        pi = {**self._make_income(1000.0, 500.0, 200.0, 100.0), "total": 1800.0}
        qi = {**self._make_income(100.0, 50.0, 20.0, 10.0), "total": 180.0}

        result = _calculate_combined_income(primary_income = pi, partner_income = qi)

        assert result["social_security"] == 1100.0
        assert result["total"] == 1980.0

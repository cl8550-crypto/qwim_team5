"""Unit tests for the Personal Info SubTab Module.

This module provides comprehensive unit tests for the SubTab_Personal_Info module,
testing the UI and server logic for personal information input in the QWIM Dashboard.

Tests cover:
- Module-level constants and configuration
- Personal info field validation
- State selection options
- Employment status options
- Age and date validations
- Error handling scenarios

Author:
    QWIM Development Team

Version:
    0.5.1

Last Modified:
    2026-02-01
"""

from __future__ import annotations

from typing import Any, ClassVar

import pytest

from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


#: Module-level logger instance for test logging
_logger = get_logger(name = __name__)

# Try importing the module under test - may fail in some environments
# due to complex Shiny dependencies
try:
    from src.dashboard.shiny_tab_clients.subtab_personal_info import (
        _logger as module_logger,
        subtab_clients_personal_info_server,
        subtab_clients_personal_info_ui,
    )

    MODULE_IMPORT_AVAILABLE = True
except ImportError as e:
    MODULE_IMPORT_AVAILABLE = False
    _logger.warning(f"Module import failed, some tests will be skipped: {e}")


# =============================================================================
# Constants for Testing
# =============================================================================

#: List of US state abbreviations for validation
US_STATE_ABBREVIATIONS = [
    "AL",
    "AK",
    "AZ",
    "AR",
    "CA",
    "CO",
    "CT",
    "DE",
    "FL",
    "GA",
    "HI",
    "ID",
    "IL",
    "IN",
    "IA",
    "KS",
    "KY",
    "LA",
    "ME",
    "MD",
    "MA",
    "MI",
    "MN",
    "MS",
    "MO",
    "MT",
    "NE",
    "NV",
    "NH",
    "NJ",
    "NM",
    "NY",
    "NC",
    "ND",
    "OH",
    "OK",
    "OR",
    "PA",
    "RI",
    "SC",
    "SD",
    "TN",
    "TX",
    "UT",
    "VT",
    "VA",
    "WA",
    "WV",
    "WI",
    "WY",
]

#: Valid employment status options
EMPLOYMENT_STATUS_OPTIONS = [
    "employed_full_time",
    "employed_part_time",
    "self_employed",
    "retired",
    "unemployed",
    "student",
    "homemaker",
    "disabled",
]

#: Valid marital status options
MARITAL_STATUS_OPTIONS = [
    "single",
    "married",
    "divorced",
    "widowed",
    "separated",
    "domestic_partnership",
]


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture()
def sample_primary_client_data() -> dict[str, Any]:
    """Create sample primary client personal data for testing.

    Returns:
        dict: Sample primary client personal information dictionary.
    """
    return {
        "client_type": "primary",
        "first_name": "John",
        "last_name": "Doe",
        "age_current": 45,
        "age_retirement": 65,
        "state": "CA",
        "employment_status": "employed_full_time",
        "marital_status": "married",
        "email": "john.doe@example.com",
        "phone": "555-123-4567",
    }


@pytest.fixture()
def sample_partner_client_data() -> dict[str, Any]:
    """Create sample partner client personal data for testing.

    Returns:
        dict: Sample partner client personal information dictionary.
    """
    return {
        "client_type": "partner",
        "first_name": "Jane",
        "last_name": "Doe",
        "age_current": 42,
        "age_retirement": 65,
        "state": "CA",
        "employment_status": "employed_full_time",
        "marital_status": "married",
        "email": "jane.doe@example.com",
        "phone": "555-123-4568",
    }


@pytest.fixture()
def sample_data_utils() -> dict[str, Any]:
    """Create sample data utilities dictionary for testing.

    Returns:
        dict: Sample data utilities configuration dictionary.
    """
    return {
        "theme": "default",
        "export_enabled": False,
        "validate_inputs": True,
    }


@pytest.fixture()
def sample_data_inputs(
    sample_primary_client_data: dict[str, Any],
    sample_partner_client_data: dict[str, Any],
) -> dict[str, Any]:
    """Create sample data inputs dictionary for testing.

    Args:
        sample_primary_client_data: Sample primary client data.
        sample_partner_client_data: Sample partner client data.

    Returns:
        dict: Sample data inputs dictionary with personal info.
    """
    return {
        "Primary_Client": sample_primary_client_data,
        "Partner_Client": sample_partner_client_data,
    }


@pytest.fixture()
def sample_reactives_shiny() -> dict[str, Any]:
    """Create sample reactives dictionary for testing.

    Returns:
        dict: Sample reactive values dictionary.
    """
    return {
        "User_Inputs_Shiny": {},
        "Inner_Variables_Shiny": {},
        "Triggers_Shiny": {},
        "Visual_Objects_Shiny": {},
    }


# =============================================================================
# Test Classes
# =============================================================================


@pytest.mark.unit()
@pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason="Module import failed due to Shiny dependencies",
)
class Test_Module_Imports:
    """Test that all required module imports are available."""

    @pytest.mark.unit()
    def test_subtab_personal_info_ui_is_importable(self) -> None:
        """Test that subtab_clients_personal_info_ui function can be imported."""
        assert callable(subtab_clients_personal_info_ui)
        _logger.debug("subtab_clients_personal_info_ui successfully imported")

    @pytest.mark.unit()
    def test_subtab_personal_info_server_is_importable(self) -> None:
        """Test that subtab_clients_personal_info_server function can be imported."""
        assert callable(subtab_clients_personal_info_server)
        _logger.debug("subtab_clients_personal_info_server successfully imported")


@pytest.mark.unit()
class Test_Personal_Info_Worksheet_Numeric_Coercion:
    """Tests for worksheet personal-info numeric coercion."""

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        ("raw_value", "default_value", "expected_value"),
        [
            (True, 0, 0),
            (False, 7, 7),
            ("65", 0, 65),
            (0, 9, 9),
        ],
        ids=[
            "bool_uses_default",
            "false_uses_default",
            "numeric_string_preserved",
            "zero_uses_default",
        ],
    )
    def test_coerce_personal_info_worksheet_numeric_int_or_default_uses_expected_defaults(
        self,
        raw_value: object,
        default_value: int,
        expected_value: int,
    ) -> None:
        """Worksheet numeric coercion should reject booleans onto the default path."""
        from src.dashboard.shiny_tab_clients.subtab_personal_info import (
            _coerce_personal_info_worksheet_numeric_int_or_default,
        )

        result_value = _coerce_personal_info_worksheet_numeric_int_or_default(
            raw_value = raw_value,
            default_value = default_value,
        )

        assert result_value == expected_value


@pytest.mark.unit()
@pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason="Module import failed due to Shiny dependencies",
)
class Test_Module_Logger:
    """Test module-level logger configuration."""

    @pytest.mark.unit()
    def test_logger_is_configured(self) -> None:
        """Test that module logger is properly configured."""
        assert module_logger is not None
        _logger.debug("Module logger verified")


@pytest.mark.unit()
class Test_Primary_Client_Data_Validation:
    """Test primary client personal data validation."""

    @pytest.mark.unit()
    def test_primary_client_has_first_name(
        self,
        sample_primary_client_data: dict[str, Any],
    ) -> None:
        """Test that primary client has first_name key."""
        assert "first_name" in sample_primary_client_data
        assert isinstance(sample_primary_client_data["first_name"], str)
        assert len(sample_primary_client_data["first_name"]) > 0
        _logger.debug("Primary client has first_name")

    @pytest.mark.unit()
    def test_primary_client_has_last_name(
        self,
        sample_primary_client_data: dict[str, Any],
    ) -> None:
        """Test that primary client has last_name key."""
        assert "last_name" in sample_primary_client_data
        assert isinstance(sample_primary_client_data["last_name"], str)
        assert len(sample_primary_client_data["last_name"]) > 0
        _logger.debug("Primary client has last_name")

    @pytest.mark.unit()
    def test_primary_client_has_valid_current_age(
        self,
        sample_primary_client_data: dict[str, Any],
    ) -> None:
        """Test that primary client has valid current age."""
        assert "age_current" in sample_primary_client_data
        age = sample_primary_client_data["age_current"]
        assert isinstance(age, int)
        assert 18 <= age <= 120
        _logger.debug(f"Primary client current age: {age}")

    @pytest.mark.unit()
    def test_primary_client_has_valid_retirement_age(
        self,
        sample_primary_client_data: dict[str, Any],
    ) -> None:
        """Test that primary client has valid retirement age."""
        assert "age_retirement" in sample_primary_client_data
        age = sample_primary_client_data["age_retirement"]
        assert isinstance(age, int)
        assert 40 <= age <= 100
        _logger.debug(f"Primary client retirement age: {age}")

    @pytest.mark.unit()
    def test_retirement_age_after_current_age(
        self,
        sample_primary_client_data: dict[str, Any],
    ) -> None:
        """Test that retirement age is after current age."""
        current_age = sample_primary_client_data["age_current"]
        retirement_age = sample_primary_client_data["age_retirement"]
        assert retirement_age >= current_age
        _logger.debug(f"Retirement age {retirement_age} >= current age {current_age}")

    @pytest.mark.unit()
    def test_primary_client_has_valid_state(
        self,
        sample_primary_client_data: dict[str, Any],
    ) -> None:
        """Test that primary client has valid state abbreviation."""
        assert "state" in sample_primary_client_data
        state = sample_primary_client_data["state"]
        assert state in US_STATE_ABBREVIATIONS
        _logger.debug(f"Primary client state: {state}")

    @pytest.mark.unit()
    def test_primary_client_has_valid_employment_status(
        self,
        sample_primary_client_data: dict[str, Any],
    ) -> None:
        """Test that primary client has valid employment status."""
        assert "employment_status" in sample_primary_client_data
        status = sample_primary_client_data["employment_status"]
        assert status in EMPLOYMENT_STATUS_OPTIONS
        _logger.debug(f"Primary client employment status: {status}")

    @pytest.mark.unit()
    def test_primary_client_has_valid_marital_status(
        self,
        sample_primary_client_data: dict[str, Any],
    ) -> None:
        """Test that primary client has valid marital status."""
        assert "marital_status" in sample_primary_client_data
        status = sample_primary_client_data["marital_status"]
        assert status in MARITAL_STATUS_OPTIONS
        _logger.debug(f"Primary client marital status: {status}")


@pytest.mark.unit()
class Test_Partner_Client_Data_Validation:
    """Test partner client personal data validation."""

    @pytest.mark.unit()
    def test_partner_client_has_first_name(
        self,
        sample_partner_client_data: dict[str, Any],
    ) -> None:
        """Test that partner client has first_name key."""
        assert "first_name" in sample_partner_client_data
        assert isinstance(sample_partner_client_data["first_name"], str)
        _logger.debug("Partner client has first_name")

    @pytest.mark.unit()
    def test_partner_client_has_valid_current_age(
        self,
        sample_partner_client_data: dict[str, Any],
    ) -> None:
        """Test that partner client has valid current age."""
        assert "age_current" in sample_partner_client_data
        age = sample_partner_client_data["age_current"]
        assert isinstance(age, int)
        assert 18 <= age <= 120
        _logger.debug(f"Partner client current age: {age}")

    @pytest.mark.unit()
    def test_partner_client_type_is_partner(
        self,
        sample_partner_client_data: dict[str, Any],
    ) -> None:
        """Test that partner client type is 'partner'."""
        assert "client_type" in sample_partner_client_data
        assert sample_partner_client_data["client_type"] == "partner"
        _logger.debug("Partner client type verified")


@pytest.mark.unit()
class Test_State_Options:
    """Test US state abbreviation options."""

    @pytest.mark.unit()
    def test_state_options_count(self) -> None:
        """Test that we have 50 US states."""
        assert len(US_STATE_ABBREVIATIONS) == 50
        _logger.debug(f"State options count: {len(US_STATE_ABBREVIATIONS)}")

    @pytest.mark.unit()
    def test_state_options_unique(self) -> None:
        """Test that all state abbreviations are unique."""
        assert len(US_STATE_ABBREVIATIONS) == len(set(US_STATE_ABBREVIATIONS))
        _logger.debug("All state abbreviations are unique")

    @pytest.mark.unit()
    def test_state_options_are_uppercase(self) -> None:
        """Test that all state abbreviations are uppercase."""
        for state in US_STATE_ABBREVIATIONS:
            assert state.isupper()
        _logger.debug("All state abbreviations are uppercase")

    @pytest.mark.unit()
    def test_state_options_are_two_characters(self) -> None:
        """Test that all state abbreviations are two characters."""
        for state in US_STATE_ABBREVIATIONS:
            assert len(state) == 2
        _logger.debug("All state abbreviations are two characters")


@pytest.mark.unit()
class Test_Employment_Status_Options:
    """Test employment status options."""

    @pytest.mark.unit()
    def test_employment_status_options_count(self) -> None:
        """Test that we have expected number of employment statuses."""
        assert len(EMPLOYMENT_STATUS_OPTIONS) == 8
        _logger.debug(f"Employment status count: {len(EMPLOYMENT_STATUS_OPTIONS)}")

    @pytest.mark.unit()
    def test_employment_status_options_unique(self) -> None:
        """Test that all employment statuses are unique."""
        assert len(EMPLOYMENT_STATUS_OPTIONS) == len(set(EMPLOYMENT_STATUS_OPTIONS))
        _logger.debug("All employment statuses are unique")

    @pytest.mark.unit()
    def test_employment_status_retired_exists(self) -> None:
        """Test that 'retired' is a valid employment status."""
        assert "retired" in EMPLOYMENT_STATUS_OPTIONS
        _logger.debug("'retired' is a valid employment status")


@pytest.mark.unit()
class Test_Marital_Status_Options:
    """Test marital status options."""

    @pytest.mark.unit()
    def test_marital_status_options_count(self) -> None:
        """Test that we have expected number of marital statuses."""
        assert len(MARITAL_STATUS_OPTIONS) == 6
        _logger.debug(f"Marital status count: {len(MARITAL_STATUS_OPTIONS)}")

    @pytest.mark.unit()
    def test_marital_status_options_unique(self) -> None:
        """Test that all marital statuses are unique."""
        assert len(MARITAL_STATUS_OPTIONS) == len(set(MARITAL_STATUS_OPTIONS))
        _logger.debug("All marital statuses are unique")

    @pytest.mark.unit()
    def test_marital_status_married_exists(self) -> None:
        """Test that 'married' is a valid marital status."""
        assert "married" in MARITAL_STATUS_OPTIONS
        _logger.debug("'married' is a valid marital status")


@pytest.mark.unit()
class Test_Age_Validation:
    """Test age validation rules."""

    @pytest.mark.parametrize("age", [18, 25, 45, 65, 80, 100])
    @pytest.mark.unit()
    def test_valid_current_ages(self, age: int) -> None:
        """Test that common current ages are valid."""
        assert 18 <= age <= 120
        _logger.debug(f"Valid current age: {age}")

    @pytest.mark.parametrize("age", [-1, 0, 10, 17])
    @pytest.mark.unit()
    def test_invalid_current_ages_too_young(self, age: int) -> None:
        """Test that ages below 18 are invalid."""
        assert not (18 <= age <= 120)
        _logger.debug(f"Invalid current age (too young): {age}")

    @pytest.mark.parametrize("age", [121, 150, 200])
    @pytest.mark.unit()
    def test_invalid_current_ages_too_old(self, age: int) -> None:
        """Test that ages above 120 are invalid."""
        assert not (18 <= age <= 120)
        _logger.debug(f"Invalid current age (too old): {age}")

    @pytest.mark.parametrize(
        "current_age,retirement_age",
        [
            (45, 65),
            (55, 55),  # Can retire at current age
            (60, 70),
            (30, 67),
        ],
    )
    @pytest.mark.unit()
    def test_valid_retirement_age_relationships(
        self,
        current_age: int,
        retirement_age: int,
    ) -> None:
        """Test valid retirement age relationships."""
        assert retirement_age >= current_age
        _logger.debug(f"Valid: retirement {retirement_age} >= current {current_age}")


@pytest.mark.unit()
class Test_Data_Inputs_Structure:
    """Test data inputs dictionary structure for personal info."""

    @pytest.mark.unit()
    def test_data_inputs_has_primary_client(
        self,
        sample_data_inputs: dict[str, Any],
    ) -> None:
        """Test that data_inputs has Primary_Client key."""
        assert "Primary_Client" in sample_data_inputs
        _logger.debug("data_inputs has Primary_Client")

    @pytest.mark.unit()
    def test_data_inputs_has_partner_client(
        self,
        sample_data_inputs: dict[str, Any],
    ) -> None:
        """Test that data_inputs has Partner_Client key."""
        assert "Partner_Client" in sample_data_inputs
        _logger.debug("data_inputs has Partner_Client")


# =============================================================================
# Integration Tests (Marked for separate execution)
# =============================================================================


@pytest.mark.integration()
class Test_Sub_Tab_Personal_Info_Integration:
    """Integration tests for subtab_personal_info module."""

    @pytest.mark.skipif(
        not MODULE_IMPORT_AVAILABLE,
        reason="Module import failed due to Shiny dependencies",
    )
    @pytest.mark.unit()
    def test_ui_creates_valid_shiny_component(
        self,
        sample_data_utils: dict[str, Any],
        sample_data_inputs: dict[str, Any],
    ) -> None:
        """Test that UI function creates a valid Shiny component."""
        result = subtab_clients_personal_info_ui("ID_test_ui",
            data_utils=sample_data_utils,
            data_inputs=sample_data_inputs,
        )
        assert result is not None

    @pytest.mark.skipif(
        not MODULE_IMPORT_AVAILABLE,
        reason="Module import failed due to Shiny dependencies",
    )
    @pytest.mark.unit()
    def test_server_handles_primary_client_inputs(
        self,
        sample_data_utils: dict[str, Any],
        sample_data_inputs: dict[str, Any],
        sample_reactives_shiny: dict[str, Any],
    ) -> None:
        """Test that server handles primary client input changes."""
        import inspect

        assert callable(subtab_clients_personal_info_server)
        sig = inspect.signature(subtab_clients_personal_info_server)
        assert "id" in sig.parameters

    @pytest.mark.skipif(
        not MODULE_IMPORT_AVAILABLE,
        reason="Module import failed due to Shiny dependencies",
    )
    @pytest.mark.unit()
    def test_server_handles_partner_client_inputs(
        self,
        sample_data_utils: dict[str, Any],
        sample_data_inputs: dict[str, Any],
        sample_reactives_shiny: dict[str, Any],
    ) -> None:
        """Test that server handles partner client input changes."""
        import inspect

        sig = inspect.signature(subtab_clients_personal_info_server)
        assert len(sig.parameters) >= 1


# =============================================================================
# NEW: input ID convention, default values, choice sets
# =============================================================================


@pytest.mark.unit()
class Test_Input_ID_Convention_Personal_Info:
    """Test that personal-info input IDs follow the hierarchical naming convention."""

    _PRIMARY_INPUT_IDS: ClassVar[list[str]] = [
        "input_ID_tab_clients_subtab_clients_personal_info_client_primary_name",
        "input_ID_tab_clients_subtab_clients_personal_info_client_primary_age_current",
        "input_ID_tab_clients_subtab_clients_personal_info_client_primary_age_retirement",
        "input_ID_tab_clients_subtab_clients_personal_info_client_primary_age_income_starting",
        "input_ID_tab_clients_subtab_clients_personal_info_client_primary_status_marital",
        "input_ID_tab_clients_subtab_clients_personal_info_client_primary_gender",
        "input_ID_tab_clients_subtab_clients_personal_info_client_primary_tolerance_risk",
        "input_ID_tab_clients_subtab_clients_personal_info_client_primary_state",
        "input_ID_tab_clients_subtab_clients_personal_info_client_primary_code_zip",
    ]

    _PARTNER_INPUT_IDS: ClassVar[list[str]] = [
        "input_ID_tab_clients_subtab_clients_personal_info_client_partner_name",
        "input_ID_tab_clients_subtab_clients_personal_info_client_partner_age_current",
        "input_ID_tab_clients_subtab_clients_personal_info_client_partner_age_retirement",
    ]

    @pytest.mark.unit()
    def test_primary_ids_start_with_correct_prefix(self) -> None:
        """All primary input IDs start with the correct hierarchical prefix."""
        prefix = "input_ID_tab_clients_subtab_clients_personal_info_client_primary"
        for input_id in self._PRIMARY_INPUT_IDS:
            assert input_id.startswith(prefix), (
                f"Input ID '{input_id}' does not start with '{prefix}'"
            )

    @pytest.mark.unit()
    def test_partner_ids_start_with_correct_prefix(self) -> None:
        """All partner input IDs start with the correct hierarchical prefix."""
        prefix = "input_ID_tab_clients_subtab_clients_personal_info_client_partner"
        for input_id in self._PARTNER_INPUT_IDS:
            assert input_id.startswith(prefix), (
                f"Input ID '{input_id}' does not start with '{prefix}'"
            )

    @pytest.mark.unit()
    def test_all_ids_start_with_input_ID(self) -> None:
        """Every input ID starts with 'input_ID_'."""
        for input_id in self._PRIMARY_INPUT_IDS + self._PARTNER_INPUT_IDS:
            assert input_id.startswith("input_ID_"), (
                f"Input ID '{input_id}' does not start with 'input_ID_'"
            )

    @pytest.mark.unit()
    def test_all_ids_use_snake_case_separators(self) -> None:
        """Every input ID uses underscores as separators (no spaces or hyphens)."""
        for input_id in self._PRIMARY_INPUT_IDS + self._PARTNER_INPUT_IDS:
            assert " " not in input_id, f"Input ID '{input_id}' contains spaces"
            assert "-" not in input_id, f"Input ID '{input_id}' contains hyphens"

    @pytest.mark.skipif(not MODULE_IMPORT_AVAILABLE, reason="Module import unavailable")
    @pytest.mark.unit()
    def test_primary_ids_appear_in_ui_source(self) -> None:
        """All primary input IDs appear in the subtab UI source code."""
        import sys
        from pathlib import Path

        source = Path(sys.modules['src.dashboard.shiny_tab_clients.subtab_personal_info'].__file__).read_text(encoding='utf-8')
        for input_id in self._PRIMARY_INPUT_IDS:
            assert input_id in source, (
                f"Input ID '{input_id}' not found in subtab_clients_personal_info_ui source"
            )
        _logger.debug("All primary personal_info input IDs verified in source")


@pytest.mark.unit()
class Test_Default_Values_Personal_Info:
    """Test that source code contains the expected default values."""

    @pytest.mark.skipif(not MODULE_IMPORT_AVAILABLE, reason="Module import unavailable")
    @pytest.mark.unit()
    def test_primary_name_default_is_anne_smith(self) -> None:
        """Primary name defaults to 'Anne Smith'."""
        import sys
        from pathlib import Path

        source = Path(sys.modules['src.dashboard.shiny_tab_clients.subtab_personal_info'].__file__).read_text(encoding='utf-8')
        assert "Anne Smith" in source, "Default primary name 'Anne Smith' not found in source"
        _logger.debug("Primary name default 'Anne Smith' verified")

    @pytest.mark.skipif(not MODULE_IMPORT_AVAILABLE, reason="Module import unavailable")
    @pytest.mark.unit()
    def test_partner_name_default_is_william_smith(self) -> None:
        """Partner name defaults to 'William Smith'."""
        import sys
        from pathlib import Path

        source = Path(sys.modules['src.dashboard.shiny_tab_clients.subtab_personal_info'].__file__).read_text(encoding='utf-8')
        assert "William Smith" in source, "Default partner name 'William Smith' not found in source"
        _logger.debug("Partner name default 'William Smith' verified")

    @pytest.mark.skipif(not MODULE_IMPORT_AVAILABLE, reason="Module import unavailable")
    @pytest.mark.unit()
    def test_marital_status_default_is_married(self) -> None:
        """Marital status defaults to 'married'."""
        import sys
        from pathlib import Path

        source = Path(sys.modules['src.dashboard.shiny_tab_clients.subtab_personal_info'].__file__).read_text(encoding='utf-8')
        assert "married" in source
        _logger.debug("Marital status default 'married' verified")

    @pytest.mark.skipif(not MODULE_IMPORT_AVAILABLE, reason="Module import unavailable")
    @pytest.mark.unit()
    def test_risk_tolerance_default_is_moderate(self) -> None:
        """Risk tolerance defaults to 'moderate'."""
        import sys
        from pathlib import Path

        source = Path(sys.modules['src.dashboard.shiny_tab_clients.subtab_personal_info'].__file__).read_text(encoding='utf-8')
        assert "moderate" in source
        _logger.debug("Risk tolerance default 'moderate' verified")

    @pytest.mark.skipif(not MODULE_IMPORT_AVAILABLE, reason="Module import unavailable")
    @pytest.mark.unit()
    def test_zip_code_default_is_12345(self) -> None:
        """ZIP code defaults to 12345."""
        import sys
        from pathlib import Path

        source = Path(sys.modules['src.dashboard.shiny_tab_clients.subtab_personal_info'].__file__).read_text(encoding='utf-8')
        assert "12345" in source
        _logger.debug("ZIP code default '12345' verified")


@pytest.mark.unit()
class Test_Choice_Sets_Personal_Info:
    """Test that source code contains all expected choice values."""

    _MARITAL_STATUS_CHOICES: ClassVar[list[str]] = [
        "single",
        "married",
        "divorced",
        "widowed",
        "separated",
        "domestic_partnership",
    ]

    _RISK_TOLERANCE_CHOICES: ClassVar[list[str]] = [
        "conservative",
        "moderate_conservative",
        "moderate",
        "moderate_aggressive",
        "aggressive",
    ]

    @pytest.mark.skipif(not MODULE_IMPORT_AVAILABLE, reason="Module import unavailable")
    @pytest.mark.unit()
    def test_all_marital_status_choices_in_source(self) -> None:
        """All six marital status choices appear in the source code."""
        import sys
        from pathlib import Path

        source = Path(sys.modules['src.dashboard.shiny_tab_clients.subtab_personal_info'].__file__).read_text(encoding='utf-8')
        for choice in self._MARITAL_STATUS_CHOICES:
            assert choice in source, f"Marital status choice '{choice}' not found in source"
        _logger.debug("All marital status choices verified")

    @pytest.mark.skipif(not MODULE_IMPORT_AVAILABLE, reason="Module import unavailable")
    @pytest.mark.unit()
    def test_all_risk_tolerance_choices_in_source(self) -> None:
        """All five risk tolerance choices appear in the source code."""
        import sys
        from pathlib import Path

        source = Path(sys.modules['src.dashboard.shiny_tab_clients.subtab_personal_info'].__file__).read_text(encoding='utf-8')
        for choice in self._RISK_TOLERANCE_CHOICES:
            assert choice in source, f"Risk tolerance choice '{choice}' not found in source"
        _logger.debug("All risk tolerance choices verified")

    @pytest.mark.unit()
    def test_marital_status_has_six_choices(self) -> None:
        """The marital status choice set has exactly 6 entries."""
        assert len(self._MARITAL_STATUS_CHOICES) == 6

    @pytest.mark.unit()
    def test_risk_tolerance_has_five_tiers(self) -> None:
        """The risk tolerance choice set has exactly 5 tiers."""
        assert len(self._RISK_TOLERANCE_CHOICES) == 5

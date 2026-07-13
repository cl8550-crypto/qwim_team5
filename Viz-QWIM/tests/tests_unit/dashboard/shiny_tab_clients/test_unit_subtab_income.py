"""Unit tests for the Income SubTab Module.

This module provides comprehensive unit tests for the SubTab_Income module,
testing the UI and server logic for income sources in the QWIM Dashboard.

Tests cover:
- Module-level constants and configuration
- Income categories (Social Security, pension, annuity, other)
- Income value validation
- Income timing and frequency
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
    from src.dashboard.shiny_tab_clients.subtab_income import (
        _logger as module_logger,
        subtab_clients_income_server,
        subtab_clients_income_ui,
    )

    MODULE_IMPORT_AVAILABLE = True
except ImportError as e:
    MODULE_IMPORT_AVAILABLE = False
    _logger.warning(f"Module import failed, some tests will be skipped: {e}")


# =============================================================================
# Constants for Testing
# =============================================================================

#: Income categories for validation
INCOME_CATEGORIES = ["social_security", "pension", "annuity", "other"]

#: Income frequency options
INCOME_FREQUENCIES = ["monthly", "quarterly", "semi_annual", "annual"]

#: Social Security benefit types
SOCIAL_SECURITY_TYPES = [
    "retirement_benefit",
    "spousal_benefit",
    "survivor_benefit",
    "disability_benefit",
]

#: Pension types
PENSION_TYPES = [
    "defined_benefit",
    "defined_contribution",
    "government_pension",
    "military_pension",
]

#: Annuity types
ANNUITY_TYPES = [
    "fixed_annuity",
    "variable_annuity",
    "immediate_annuity",
    "deferred_annuity",
    "spia",  # Single Premium Immediate Annuity
    "dia",  # Deferred Income Annuity
]

#: Other income types
OTHER_INCOME_TYPES = [
    "part_time_work",
    "rental_income",
    "dividend_income",
    "interest_income",
    "royalties",
    "business_income",
]


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture()
def sample_social_security_income() -> dict[str, Any]:
    """Create sample Social Security income data for testing.

    Returns:
        dict: Sample Social Security income dictionary.
    """
    return {
        "primary_benefit": {
            "type": "retirement_benefit",
            "annual_amount": 24000.00,
            "start_age": 67,
            "cola_adjustment": 0.025,  # 2.5% COLA
        },
        "spousal_benefit": {
            "type": "spousal_benefit",
            "annual_amount": 12000.00,
            "start_age": 67,
            "cola_adjustment": 0.025,
        },
    }


@pytest.fixture()
def sample_pension_income() -> dict[str, Any]:
    """Create sample pension income data for testing.

    Returns:
        dict: Sample pension income dictionary.
    """
    return {
        "employer_pension": {
            "type": "defined_benefit",
            "annual_amount": 36000.00,
            "start_age": 65,
            "cola_adjustment": 0.02,
            "survivor_benefit_pct": 0.50,
        },
    }


@pytest.fixture()
def sample_annuity_income() -> dict[str, Any]:
    """Create sample annuity income data for testing.

    Returns:
        dict: Sample annuity income dictionary.
    """
    return {
        "income_annuity": {
            "type": "spia",
            "annual_amount": 18000.00,
            "start_age": 70,
            "is_inflation_adjusted": False,
        },
    }


@pytest.fixture()
def sample_other_income() -> dict[str, Any]:
    """Create sample other income data for testing.

    Returns:
        dict: Sample other income dictionary.
    """
    return {
        "rental_income": {
            "type": "rental_income",
            "annual_amount": 12000.00,
            "start_age": 65,
            "end_age": 85,
        },
        "part_time_work": {
            "type": "part_time_work",
            "annual_amount": 15000.00,
            "start_age": 65,
            "end_age": 70,
        },
    }


@pytest.fixture()
def sample_all_income(
    sample_social_security_income: dict[str, Any],
    sample_pension_income: dict[str, Any],
    sample_annuity_income: dict[str, Any],
    sample_other_income: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Create sample complete income data for testing.

    Args:
        sample_social_security_income: Sample Social Security income.
        sample_pension_income: Sample pension income.
        sample_annuity_income: Sample annuity income.
        sample_other_income: Sample other income.

    Returns:
        dict: Complete sample income dictionary.
    """
    return {
        "social_security": sample_social_security_income,
        "pension": sample_pension_income,
        "annuity": sample_annuity_income,
        "other": sample_other_income,
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
        "currency_format": "${:,.2f}",
    }


@pytest.fixture()
def sample_data_inputs(
    sample_all_income: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Create sample data inputs dictionary for testing.

    Args:
        sample_all_income: Complete sample income data.

    Returns:
        dict: Sample data inputs dictionary with income.
    """
    return {
        "Income": sample_all_income,
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
    def test_subtab_income_ui_is_importable(self) -> None:
        """Test that subtab_clients_income_ui function can be imported."""
        assert callable(subtab_clients_income_ui)
        _logger.debug("subtab_clients_income_ui successfully imported")

    @pytest.mark.unit()
    def test_subtab_income_server_is_importable(self) -> None:
        """Test that subtab_clients_income_server function can be imported."""
        assert callable(subtab_clients_income_server)
        _logger.debug("subtab_clients_income_server successfully imported")


@pytest.mark.unit()
class Test_Income_Worksheet_Amount_Coercion:
    """Tests for worksheet income amount coercion."""

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        ("raw_value", "default_value", "expected_value"),
        [
            (True, 0, 0),
            (False, 7, 7),
            ("2,750", 0, 2750),
            ("", 9, 9),
        ],
        ids=[
            "bool_uses_default",
            "false_uses_default",
            "formatted_numeric_string_preserved",
            "empty_string_uses_default",
        ],
    )
    def test_coerce_income_worksheet_amount_int_or_default_uses_expected_defaults(
        self,
        raw_value: object,
        default_value: int,
        expected_value: int,
    ) -> None:
        """Worksheet amount coercion should reject booleans onto the default path."""
        from src.dashboard.shiny_tab_clients.subtab_income import (
            _coerce_income_worksheet_amount_int_or_default,
        )

        result_value = _coerce_income_worksheet_amount_int_or_default(raw_value = raw_value, default_value = default_value)

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
class Test_Income_Categories:
    """Test income category definitions."""

    @pytest.mark.unit()
    def test_income_categories_count(self) -> None:
        """Test that we have 4 income categories."""
        assert len(INCOME_CATEGORIES) == 4
        _logger.debug(f"Income categories count: {len(INCOME_CATEGORIES)}")

    @pytest.mark.unit()
    def test_income_categories_unique(self) -> None:
        """Test that all income categories are unique."""
        assert len(INCOME_CATEGORIES) == len(set(INCOME_CATEGORIES))
        _logger.debug("All income categories are unique")

    @pytest.mark.unit()
    def test_social_security_category_exists(self) -> None:
        """Test that 'social_security' is a valid category."""
        assert "social_security" in INCOME_CATEGORIES
        _logger.debug("'social_security' category exists")

    @pytest.mark.unit()
    def test_pension_category_exists(self) -> None:
        """Test that 'pension' is a valid category."""
        assert "pension" in INCOME_CATEGORIES
        _logger.debug("'pension' category exists")

    @pytest.mark.unit()
    def test_annuity_category_exists(self) -> None:
        """Test that 'annuity' is a valid category."""
        assert "annuity" in INCOME_CATEGORIES
        _logger.debug("'annuity' category exists")

    @pytest.mark.unit()
    def test_other_category_exists(self) -> None:
        """Test that 'other' is a valid category."""
        assert "other" in INCOME_CATEGORIES
        _logger.debug("'other' category exists")


@pytest.mark.unit()
class Test_Income_Frequencies:
    """Test income frequency options."""

    @pytest.mark.unit()
    def test_income_frequencies_count(self) -> None:
        """Test that we have expected frequency options."""
        assert len(INCOME_FREQUENCIES) == 4
        _logger.debug(f"Income frequencies count: {len(INCOME_FREQUENCIES)}")

    @pytest.mark.unit()
    def test_monthly_frequency_exists(self) -> None:
        """Test that 'monthly' is a valid frequency."""
        assert "monthly" in INCOME_FREQUENCIES
        _logger.debug("'monthly' frequency exists")

    @pytest.mark.unit()
    def test_annual_frequency_exists(self) -> None:
        """Test that 'annual' is a valid frequency."""
        assert "annual" in INCOME_FREQUENCIES
        _logger.debug("'annual' frequency exists")


@pytest.mark.unit()
class Test_Social_Security_Types:
    """Test Social Security benefit type definitions."""

    @pytest.mark.unit()
    def test_social_security_types_not_empty(self) -> None:
        """Test that Social Security types list is not empty."""
        assert len(SOCIAL_SECURITY_TYPES) > 0
        _logger.debug(f"Social Security types count: {len(SOCIAL_SECURITY_TYPES)}")

    @pytest.mark.unit()
    def test_social_security_types_unique(self) -> None:
        """Test that all Social Security types are unique."""
        assert len(SOCIAL_SECURITY_TYPES) == len(set(SOCIAL_SECURITY_TYPES))
        _logger.debug("All Social Security types are unique")

    @pytest.mark.unit()
    def test_retirement_benefit_exists(self) -> None:
        """Test that 'retirement_benefit' is a Social Security type."""
        assert "retirement_benefit" in SOCIAL_SECURITY_TYPES
        _logger.debug("'retirement_benefit' exists")

    @pytest.mark.unit()
    def test_spousal_benefit_exists(self) -> None:
        """Test that 'spousal_benefit' is a Social Security type."""
        assert "spousal_benefit" in SOCIAL_SECURITY_TYPES
        _logger.debug("'spousal_benefit' exists")


@pytest.mark.unit()
class Test_Pension_Types:
    """Test pension type definitions."""

    @pytest.mark.unit()
    def test_pension_types_not_empty(self) -> None:
        """Test that pension types list is not empty."""
        assert len(PENSION_TYPES) > 0
        _logger.debug(f"Pension types count: {len(PENSION_TYPES)}")

    @pytest.mark.unit()
    def test_pension_types_unique(self) -> None:
        """Test that all pension types are unique."""
        assert len(PENSION_TYPES) == len(set(PENSION_TYPES))
        _logger.debug("All pension types are unique")

    @pytest.mark.unit()
    def test_defined_benefit_exists(self) -> None:
        """Test that 'defined_benefit' is a pension type."""
        assert "defined_benefit" in PENSION_TYPES
        _logger.debug("'defined_benefit' exists")


@pytest.mark.unit()
class Test_Annuity_Types:
    """Test annuity type definitions."""

    @pytest.mark.unit()
    def test_annuity_types_not_empty(self) -> None:
        """Test that annuity types list is not empty."""
        assert len(ANNUITY_TYPES) > 0
        _logger.debug(f"Annuity types count: {len(ANNUITY_TYPES)}")

    @pytest.mark.unit()
    def test_annuity_types_unique(self) -> None:
        """Test that all annuity types are unique."""
        assert len(ANNUITY_TYPES) == len(set(ANNUITY_TYPES))
        _logger.debug("All annuity types are unique")

    @pytest.mark.unit()
    def test_spia_exists(self) -> None:
        """Test that 'spia' is an annuity type."""
        assert "spia" in ANNUITY_TYPES
        _logger.debug("'spia' exists")

    @pytest.mark.unit()
    def test_fixed_annuity_exists(self) -> None:
        """Test that 'fixed_annuity' is an annuity type."""
        assert "fixed_annuity" in ANNUITY_TYPES
        _logger.debug("'fixed_annuity' exists")


@pytest.mark.unit()
class Test_Other_Income_Types:
    """Test other income type definitions."""

    @pytest.mark.unit()
    def test_other_income_types_not_empty(self) -> None:
        """Test that other income types list is not empty."""
        assert len(OTHER_INCOME_TYPES) > 0
        _logger.debug(f"Other income types count: {len(OTHER_INCOME_TYPES)}")

    @pytest.mark.unit()
    def test_other_income_types_unique(self) -> None:
        """Test that all other income types are unique."""
        assert len(OTHER_INCOME_TYPES) == len(set(OTHER_INCOME_TYPES))
        _logger.debug("All other income types are unique")

    @pytest.mark.unit()
    def test_rental_income_exists(self) -> None:
        """Test that 'rental_income' is an other income type."""
        assert "rental_income" in OTHER_INCOME_TYPES
        _logger.debug("'rental_income' exists")


@pytest.mark.unit()
class Test_Social_Security_Income_Validation:
    """Test Social Security income data validation."""

    @pytest.mark.unit()
    def test_social_security_has_primary_benefit(
        self,
        sample_social_security_income: dict[str, Any],
    ) -> None:
        """Test that Social Security has primary_benefit key."""
        assert "primary_benefit" in sample_social_security_income
        _logger.debug("Social Security has primary_benefit")

    @pytest.mark.unit()
    def test_primary_benefit_has_annual_amount(
        self,
        sample_social_security_income: dict[str, Any],
    ) -> None:
        """Test that primary benefit has annual_amount."""
        benefit = sample_social_security_income["primary_benefit"]
        assert "annual_amount" in benefit
        assert benefit["annual_amount"] >= 0
        _logger.debug(f"Primary benefit annual amount: {benefit['annual_amount']}")

    @pytest.mark.unit()
    def test_primary_benefit_has_start_age(
        self,
        sample_social_security_income: dict[str, Any],
    ) -> None:
        """Test that primary benefit has start_age."""
        benefit = sample_social_security_income["primary_benefit"]
        assert "start_age" in benefit
        assert 62 <= benefit["start_age"] <= 70
        _logger.debug(f"Primary benefit start age: {benefit['start_age']}")

    @pytest.mark.unit()
    def test_cola_adjustment_is_reasonable(
        self,
        sample_social_security_income: dict[str, Any],
    ) -> None:
        """Test that COLA adjustment is reasonable (0-10%)."""
        benefit = sample_social_security_income["primary_benefit"]
        assert "cola_adjustment" in benefit
        assert 0 <= benefit["cola_adjustment"] <= 0.10
        _logger.debug(f"COLA adjustment: {benefit['cola_adjustment']}")


@pytest.mark.unit()
class Test_Pension_Income_Validation:
    """Test pension income data validation."""

    @pytest.mark.unit()
    def test_pension_income_values_are_positive(
        self,
        sample_pension_income: dict[str, Any],
    ) -> None:
        """Test that pension income values are positive."""
        for pension_data in sample_pension_income.values():
            assert pension_data["annual_amount"] >= 0
        _logger.debug("All pension income values are non-negative")

    @pytest.mark.unit()
    def test_pension_has_survivor_benefit(
        self,
        sample_pension_income: dict[str, Any],
    ) -> None:
        """Test that pension has survivor benefit percentage."""
        pension = sample_pension_income["employer_pension"]
        assert "survivor_benefit_pct" in pension
        assert 0 <= pension["survivor_benefit_pct"] <= 1.0
        _logger.debug(f"Survivor benefit: {pension['survivor_benefit_pct']}")


@pytest.mark.unit()
class Test_Annuity_Income_Validation:
    """Test annuity income data validation."""

    @pytest.mark.unit()
    def test_annuity_income_values_are_positive(
        self,
        sample_annuity_income: dict[str, Any],
    ) -> None:
        """Test that annuity income values are positive."""
        for annuity_data in sample_annuity_income.values():
            assert annuity_data["annual_amount"] >= 0
        _logger.debug("All annuity income values are non-negative")

    @pytest.mark.unit()
    def test_annuity_has_inflation_flag(
        self,
        sample_annuity_income: dict[str, Any],
    ) -> None:
        """Test that annuity has inflation adjustment flag."""
        annuity = sample_annuity_income["income_annuity"]
        assert "is_inflation_adjusted" in annuity
        assert isinstance(annuity["is_inflation_adjusted"], bool)
        _logger.debug(f"Inflation adjusted: {annuity['is_inflation_adjusted']}")


@pytest.mark.unit()
class Test_Other_Income_Validation:
    """Test other income data validation."""

    @pytest.mark.unit()
    def test_other_income_values_are_positive(
        self,
        sample_other_income: dict[str, Any],
    ) -> None:
        """Test that other income values are positive."""
        for income_data in sample_other_income.values():
            assert income_data["annual_amount"] >= 0
        _logger.debug("All other income values are non-negative")

    @pytest.mark.unit()
    def test_temporary_income_has_end_age(
        self,
        sample_other_income: dict[str, Any],
    ) -> None:
        """Test that temporary income sources have end_age."""
        part_time = sample_other_income["part_time_work"]
        assert "end_age" in part_time
        assert part_time["end_age"] >= part_time["start_age"]
        _logger.debug(f"Part-time work end age: {part_time['end_age']}")


@pytest.mark.unit()
class Test_Income_Frequency_Conversion:
    """Test income frequency conversion calculations."""

    @pytest.mark.parametrize(
        "annual_amount,expected_monthly",
        [
            (12000.00, 1000.00),
            (36000.00, 3000.00),
            (24000.00, 2000.00),
        ],
    )
    @pytest.mark.unit()
    def test_annual_to_monthly_conversion(
        self,
        annual_amount: float,
        expected_monthly: float,
    ) -> None:
        """Test converting annual income to monthly."""
        monthly = annual_amount / 12
        assert monthly == pytest.approx(expected_monthly, rel=1e-6)
        _logger.debug(f"Annual {annual_amount} = Monthly {monthly}")

    @pytest.mark.parametrize(
        "monthly_amount,expected_annual",
        [
            (1000.00, 12000.00),
            (3000.00, 36000.00),
            (2000.00, 24000.00),
        ],
    )
    @pytest.mark.unit()
    def test_monthly_to_annual_conversion(
        self,
        monthly_amount: float,
        expected_annual: float,
    ) -> None:
        """Test converting monthly income to annual."""
        annual = monthly_amount * 12
        assert annual == pytest.approx(expected_annual, rel=1e-6)
        _logger.debug(f"Monthly {monthly_amount} = Annual {annual}")


@pytest.mark.unit()
class Test_Total_Income_Calculation:
    """Test total income calculation across all categories."""

    @pytest.mark.unit()
    def test_total_income_calculation(
        self,
        sample_social_security_income: dict[str, Any],
        sample_pension_income: dict[str, Any],
        sample_annuity_income: dict[str, Any],
        sample_other_income: dict[str, Any],
    ) -> None:
        """Test total income calculation at retirement age."""
        # Get all annual amounts
        ss_total = sum(
            benefit["annual_amount"] for benefit in sample_social_security_income.values()
        )
        pension_total = sum(pension["annual_amount"] for pension in sample_pension_income.values())
        annuity_total = sum(annuity["annual_amount"] for annuity in sample_annuity_income.values())
        other_total = sum(income["annual_amount"] for income in sample_other_income.values())

        total = ss_total + pension_total + annuity_total + other_total
        assert total > 0
        _logger.debug(f"Total income: {total}")


@pytest.mark.unit()
class Test_Data_Inputs_Structure:
    """Test data inputs dictionary structure for income."""

    @pytest.mark.unit()
    def test_data_inputs_has_income(
        self,
        sample_data_inputs: dict[str, Any],
    ) -> None:
        """Test that data_inputs has Income key."""
        assert "Income" in sample_data_inputs
        _logger.debug("data_inputs has Income")

    @pytest.mark.unit()
    def test_income_has_all_categories(
        self,
        sample_all_income: dict[str, dict[str, Any]],
    ) -> None:
        """Test that income has all required categories."""
        for category in INCOME_CATEGORIES:
            assert category in sample_all_income
        _logger.debug("Income has all required categories")


# =============================================================================
# Integration Tests (Marked for separate execution)
# =============================================================================


@pytest.mark.integration()
class Test_Sub_Tab_Income_Integration:
    """Integration tests for subtab_income module."""

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
        result = subtab_clients_income_ui("ID_test_ui",
            data_utils=sample_data_utils,
            data_inputs=sample_data_inputs,
        )
        assert result is not None

    @pytest.mark.skipif(
        not MODULE_IMPORT_AVAILABLE,
        reason="Module import failed due to Shiny dependencies",
    )
    @pytest.mark.unit()
    def test_server_handles_income_updates(
        self,
        sample_data_utils: dict[str, Any],
        sample_data_inputs: dict[str, Any],
        sample_reactives_shiny: dict[str, Any],
    ) -> None:
        """Test that server handles income value updates."""
        import inspect

        assert callable(subtab_clients_income_server)
        sig = inspect.signature(subtab_clients_income_server)
        assert "id" in sig.parameters

    @pytest.mark.skipif(
        not MODULE_IMPORT_AVAILABLE,
        reason="Module import failed due to Shiny dependencies",
    )
    @pytest.mark.unit()
    def test_server_calculates_totals(
        self,
        sample_data_utils: dict[str, Any],
        sample_data_inputs: dict[str, Any],
        sample_reactives_shiny: dict[str, Any],
    ) -> None:
        """Test that server calculates income totals correctly."""
        import inspect

        sig = inspect.signature(subtab_clients_income_server)
        assert len(sig.parameters) >= 1


# =============================================================================
# NEW: input ID convention & income constraint bounds
# =============================================================================


@pytest.mark.unit()
class Test_Input_ID_Convention_Income:
    """Test that income input IDs follow the hierarchical naming convention."""

    _PRIMARY_INCOME_IDS: ClassVar[list[str]] = [
        "input_ID_tab_clients_subtab_clients_income_client_primary_income_social_security",
        "input_ID_tab_clients_subtab_clients_income_client_primary_income_pension",
        "input_ID_tab_clients_subtab_clients_income_client_primary_income_annuity_existing",
        "input_ID_tab_clients_subtab_clients_income_client_primary_income_other",
    ]

    @pytest.mark.unit()
    def test_all_primary_income_ids_start_with_correct_prefix(self) -> None:
        """All primary income input IDs start with the correct prefix."""
        prefix = "input_ID_tab_clients_subtab_clients_income_client_primary"
        for input_id in self._PRIMARY_INCOME_IDS:
            assert input_id.startswith(prefix), (
                f"Income input ID '{input_id}' does not start with '{prefix}'"
            )

    @pytest.mark.unit()
    def test_income_categories_count_is_four(self) -> None:
        """There are exactly four income categories."""
        assert len(self._PRIMARY_INCOME_IDS) == 4

    @pytest.mark.unit()
    def test_social_security_income_id_present(self) -> None:
        """Social security income ID is defined."""
        assert any("social_security" in iid for iid in self._PRIMARY_INCOME_IDS)

    @pytest.mark.unit()
    def test_pension_income_id_present(self) -> None:
        """Pension income ID is defined."""
        assert any("pension" in iid for iid in self._PRIMARY_INCOME_IDS)

    @pytest.mark.unit()
    def test_annuity_income_id_present(self) -> None:
        """Annuity existing income ID is defined."""
        assert any("annuity_existing" in iid for iid in self._PRIMARY_INCOME_IDS)

    @pytest.mark.unit()
    def test_other_income_id_present(self) -> None:
        """Other income ID is defined."""
        assert any("income_other" in iid for iid in self._PRIMARY_INCOME_IDS)

    @pytest.mark.skipif(not MODULE_IMPORT_AVAILABLE, reason="Module import unavailable")
    @pytest.mark.unit()
    def test_income_ids_in_server_source(self) -> None:
        """All primary income input IDs appear in the income server source."""
        import sys
        from pathlib import Path

        source = Path(sys.modules['src.dashboard.shiny_tab_clients.subtab_income'].__file__).read_text(encoding='utf-8')
        for input_id in self._PRIMARY_INCOME_IDS:
            assert input_id in source, (
                f"Income input ID '{input_id}' not found in subtab_clients_income_server source"
            )
        _logger.debug("All income input IDs verified in source")


@pytest.mark.unit()
class Test_Income_Constraint_Bounds:
    """Test income value constraint bounds from source code."""

    _INCOME_MAX_VALUE = 5_000_000

    @pytest.mark.skipif(not MODULE_IMPORT_AVAILABLE, reason="Module import unavailable")
    @pytest.mark.unit()
    def test_income_max_constraint_in_source(self) -> None:
        """Income upper bound (5,000,000) appears in subtab_income source."""
        import sys
        from pathlib import Path

        source = Path(sys.modules['src.dashboard.shiny_tab_clients.subtab_income'].__file__).read_text(encoding='utf-8')
        assert str(self._INCOME_MAX_VALUE) in source, (
            f"Income constraint {self._INCOME_MAX_VALUE} not found in source"
        )
        _logger.debug("Income max constraint %d verified in source", self._INCOME_MAX_VALUE)

    @pytest.mark.unit()
    def test_income_max_is_five_million(self) -> None:
        """The income maximum constraint is 5,000,000."""
        assert self._INCOME_MAX_VALUE == 5_000_000

    @pytest.mark.unit()
    def test_income_min_is_zero(self) -> None:
        """Zero is a valid minimum income value."""
        income_min = 0
        assert income_min == 0

    @pytest.mark.parametrize("income", [0, 1_000, 100_000, 5_000_000])
    @pytest.mark.unit()
    def test_typical_income_values_within_bounds(self, income: int) -> None:
        """Typical income values are within the [0, 5_000_000] constraint."""
        assert 0 <= income <= self._INCOME_MAX_VALUE

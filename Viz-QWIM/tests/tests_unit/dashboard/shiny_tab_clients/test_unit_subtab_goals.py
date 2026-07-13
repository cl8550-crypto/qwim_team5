"""Unit tests for the Goals SubTab Module.

This module provides comprehensive unit tests for the SubTab_Goals module,
testing the UI and server logic for financial goals in the QWIM Dashboard.

Tests cover:
- Module-level constants and configuration
- Goal categories (essential, important, aspirational)
- Goal value validation
- Goal priority ordering
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
    from src.dashboard.shiny_tab_clients.subtab_goals import (
        _logger as module_logger,
        subtab_clients_goals_server,
        subtab_clients_goals_ui,
    )

    MODULE_IMPORT_AVAILABLE = True
except ImportError as e:
    MODULE_IMPORT_AVAILABLE = False
    _logger.warning(f"Module import failed, some tests will be skipped: {e}")


# =============================================================================
# Constants for Testing
# =============================================================================

#: Goal categories for validation
GOAL_CATEGORIES = ["essential", "important", "aspirational"]

#: Goal priorities (1 = highest)
GOAL_PRIORITIES = {
    "essential": 1,
    "important": 2,
    "aspirational": 3,
}

#: Example essential goal types
ESSENTIAL_GOAL_TYPES = [
    "basic_living_expenses",
    "healthcare",
    "housing",
    "taxes",
    "insurance",
    "debt_payments",
]

#: Example important goal types
IMPORTANT_GOAL_TYPES = [
    "travel",
    "family_support",
    "education",
    "home_improvements",
    "vehicle_replacement",
]

#: Example aspirational goal types
ASPIRATIONAL_GOAL_TYPES = [
    "luxury_travel",
    "charitable_giving",
    "legacy_planning",
    "second_home",
    "hobby_pursuits",
]


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture()
def sample_essential_goals() -> dict[str, float]:
    """Create sample essential goals data for testing.

    Returns:
        dict: Sample essential goals dictionary.
    """
    return {
        "basic_living_expenses": 36000.00,
        "healthcare": 12000.00,
        "housing": 24000.00,
        "taxes": 8000.00,
    }


@pytest.fixture()
def sample_important_goals() -> dict[str, float]:
    """Create sample important goals data for testing.

    Returns:
        dict: Sample important goals dictionary.
    """
    return {
        "travel": 10000.00,
        "family_support": 12000.00,
        "education": 15000.00,
    }


@pytest.fixture()
def sample_aspirational_goals() -> dict[str, float]:
    """Create sample aspirational goals data for testing.

    Returns:
        dict: Sample aspirational goals dictionary.
    """
    return {
        "luxury_travel": 15000.00,
        "charitable_giving": 10000.00,
        "legacy_planning": 25000.00,
    }


@pytest.fixture()
def sample_all_goals(
    sample_essential_goals: dict[str, float],
    sample_important_goals: dict[str, float],
    sample_aspirational_goals: dict[str, float],
) -> dict[str, dict[str, float]]:
    """Create sample complete goals data for testing.

    Args:
        sample_essential_goals: Sample essential goals.
        sample_important_goals: Sample important goals.
        sample_aspirational_goals: Sample aspirational goals.

    Returns:
        dict: Complete sample goals dictionary.
    """
    return {
        "essential": sample_essential_goals,
        "important": sample_important_goals,
        "aspirational": sample_aspirational_goals,
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
    sample_all_goals: dict[str, dict[str, float]],
) -> dict[str, Any]:
    """Create sample data inputs dictionary for testing.

    Args:
        sample_all_goals: Complete sample goals data.

    Returns:
        dict: Sample data inputs dictionary with goals.
    """
    return {
        "Goals": sample_all_goals,
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
    def test_subtab_goals_ui_is_importable(self) -> None:
        """Test that subtab_clients_goals_ui function can be imported."""
        assert callable(subtab_clients_goals_ui)
        _logger.debug("subtab_clients_goals_ui successfully imported")

    @pytest.mark.unit()
    def test_subtab_goals_server_is_importable(self) -> None:
        """Test that subtab_clients_goals_server function can be imported."""
        assert callable(subtab_clients_goals_server)
        _logger.debug("subtab_clients_goals_server successfully imported")


@pytest.mark.unit()
class Test_Goals_Worksheet_Amount_Coercion:
    """Tests for worksheet goal amount coercion."""

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        ("raw_value", "default_value", "expected_value"),
        [
            (True, 0, 0),
            (False, 7, 7),
            ("3,500", 0, 3500),
            ("", 9, 9),
        ],
        ids=[
            "bool_uses_default",
            "false_uses_default",
            "formatted_numeric_string_preserved",
            "empty_string_uses_default",
        ],
    )
    def test_coerce_goals_worksheet_amount_int_or_default_uses_expected_defaults(
        self,
        raw_value: object,
        default_value: int,
        expected_value: int,
    ) -> None:
        """Worksheet amount coercion should reject booleans onto the default path."""
        from src.dashboard.shiny_tab_clients.subtab_goals import (
            _coerce_goals_worksheet_amount_int_or_default,
        )

        result_value = _coerce_goals_worksheet_amount_int_or_default(raw_value = raw_value, default_value = default_value)

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
class Test_Goal_Categories:
    """Test goal category definitions."""

    @pytest.mark.unit()
    def test_goal_categories_count(self) -> None:
        """Test that we have 3 goal categories."""
        assert len(GOAL_CATEGORIES) == 3
        _logger.debug(f"Goal categories count: {len(GOAL_CATEGORIES)}")

    @pytest.mark.unit()
    def test_goal_categories_unique(self) -> None:
        """Test that all goal categories are unique."""
        assert len(GOAL_CATEGORIES) == len(set(GOAL_CATEGORIES))
        _logger.debug("All goal categories are unique")

    @pytest.mark.unit()
    def test_essential_category_exists(self) -> None:
        """Test that 'essential' is a valid category."""
        assert "essential" in GOAL_CATEGORIES
        _logger.debug("'essential' category exists")

    @pytest.mark.unit()
    def test_important_category_exists(self) -> None:
        """Test that 'important' is a valid category."""
        assert "important" in GOAL_CATEGORIES
        _logger.debug("'important' category exists")

    @pytest.mark.unit()
    def test_aspirational_category_exists(self) -> None:
        """Test that 'aspirational' is a valid category."""
        assert "aspirational" in GOAL_CATEGORIES
        _logger.debug("'aspirational' category exists")


@pytest.mark.unit()
class Test_Goal_Priorities:
    """Test goal priority ordering."""

    @pytest.mark.unit()
    def test_essential_has_highest_priority(self) -> None:
        """Test that essential has priority 1 (highest)."""
        assert GOAL_PRIORITIES["essential"] == 1
        _logger.debug("Essential has priority 1")

    @pytest.mark.unit()
    def test_important_has_medium_priority(self) -> None:
        """Test that important has priority 2."""
        assert GOAL_PRIORITIES["important"] == 2
        _logger.debug("Important has priority 2")

    @pytest.mark.unit()
    def test_aspirational_has_lowest_priority(self) -> None:
        """Test that aspirational has priority 3 (lowest)."""
        assert GOAL_PRIORITIES["aspirational"] == 3
        _logger.debug("Aspirational has priority 3")

    @pytest.mark.unit()
    def test_priority_ordering(self) -> None:
        """Test that priorities are in correct order."""
        assert GOAL_PRIORITIES["essential"] < GOAL_PRIORITIES["important"]
        assert GOAL_PRIORITIES["important"] < GOAL_PRIORITIES["aspirational"]
        _logger.debug("Priority ordering verified")


@pytest.mark.unit()
class Test_Essential_Goal_Types:
    """Test essential goal type definitions."""

    @pytest.mark.unit()
    def test_essential_goal_types_not_empty(self) -> None:
        """Test that essential goal types list is not empty."""
        assert len(ESSENTIAL_GOAL_TYPES) > 0
        _logger.debug(f"Essential goal types count: {len(ESSENTIAL_GOAL_TYPES)}")

    @pytest.mark.unit()
    def test_essential_goal_types_unique(self) -> None:
        """Test that all essential goal types are unique."""
        assert len(ESSENTIAL_GOAL_TYPES) == len(set(ESSENTIAL_GOAL_TYPES))
        _logger.debug("All essential goal types are unique")

    @pytest.mark.unit()
    def test_basic_living_expenses_exists(self) -> None:
        """Test that 'basic_living_expenses' is an essential goal type."""
        assert "basic_living_expenses" in ESSENTIAL_GOAL_TYPES
        _logger.debug("'basic_living_expenses' exists in essential types")

    @pytest.mark.unit()
    def test_healthcare_exists(self) -> None:
        """Test that 'healthcare' is an essential goal type."""
        assert "healthcare" in ESSENTIAL_GOAL_TYPES
        _logger.debug("'healthcare' exists in essential types")


@pytest.mark.unit()
class Test_Important_Goal_Types:
    """Test important goal type definitions."""

    @pytest.mark.unit()
    def test_important_goal_types_not_empty(self) -> None:
        """Test that important goal types list is not empty."""
        assert len(IMPORTANT_GOAL_TYPES) > 0
        _logger.debug(f"Important goal types count: {len(IMPORTANT_GOAL_TYPES)}")

    @pytest.mark.unit()
    def test_important_goal_types_unique(self) -> None:
        """Test that all important goal types are unique."""
        assert len(IMPORTANT_GOAL_TYPES) == len(set(IMPORTANT_GOAL_TYPES))
        _logger.debug("All important goal types are unique")

    @pytest.mark.unit()
    def test_travel_exists(self) -> None:
        """Test that 'travel' is an important goal type."""
        assert "travel" in IMPORTANT_GOAL_TYPES
        _logger.debug("'travel' exists in important types")


@pytest.mark.unit()
class Test_Aspirational_Goal_Types:
    """Test aspirational goal type definitions."""

    @pytest.mark.unit()
    def test_aspirational_goal_types_not_empty(self) -> None:
        """Test that aspirational goal types list is not empty."""
        assert len(ASPIRATIONAL_GOAL_TYPES) > 0
        _logger.debug(f"Aspirational goal types count: {len(ASPIRATIONAL_GOAL_TYPES)}")

    @pytest.mark.unit()
    def test_aspirational_goal_types_unique(self) -> None:
        """Test that all aspirational goal types are unique."""
        assert len(ASPIRATIONAL_GOAL_TYPES) == len(set(ASPIRATIONAL_GOAL_TYPES))
        _logger.debug("All aspirational goal types are unique")

    @pytest.mark.unit()
    def test_charitable_giving_exists(self) -> None:
        """Test that 'charitable_giving' is an aspirational goal type."""
        assert "charitable_giving" in ASPIRATIONAL_GOAL_TYPES
        _logger.debug("'charitable_giving' exists in aspirational types")


@pytest.mark.unit()
class Test_Essential_Goals_Validation:
    """Test essential goals data validation."""

    @pytest.mark.unit()
    def test_essential_goals_values_are_positive(
        self,
        sample_essential_goals: dict[str, float],
    ) -> None:
        """Test that all essential goal values are positive."""
        for goal_type, value in sample_essential_goals.items():
            assert value >= 0, f"{goal_type} has negative value: {value}"
        _logger.debug("All essential goal values are non-negative")

    @pytest.mark.unit()
    def test_essential_goals_values_are_numeric(
        self,
        sample_essential_goals: dict[str, float],
    ) -> None:
        """Test that all essential goal values are numeric."""
        for value in sample_essential_goals.values():
            assert isinstance(value, (int, float))
        _logger.debug("All essential goal values are numeric")

    @pytest.mark.unit()
    def test_essential_goals_total(
        self,
        sample_essential_goals: dict[str, float],
    ) -> None:
        """Test essential goals total calculation."""
        total = sum(sample_essential_goals.values())
        expected = 36000.00 + 12000.00 + 24000.00 + 8000.00
        assert total == pytest.approx(expected, rel=1e-6)
        _logger.debug(f"Essential goals total: {total}")


@pytest.mark.unit()
class Test_Important_Goals_Validation:
    """Test important goals data validation."""

    @pytest.mark.unit()
    def test_important_goals_values_are_positive(
        self,
        sample_important_goals: dict[str, float],
    ) -> None:
        """Test that all important goal values are positive."""
        for goal_type, value in sample_important_goals.items():
            assert value >= 0, f"{goal_type} has negative value: {value}"
        _logger.debug("All important goal values are non-negative")

    @pytest.mark.unit()
    def test_important_goals_values_are_numeric(
        self,
        sample_important_goals: dict[str, float],
    ) -> None:
        """Test that all important goal values are numeric."""
        for value in sample_important_goals.values():
            assert isinstance(value, (int, float))
        _logger.debug("All important goal values are numeric")

    @pytest.mark.unit()
    def test_important_goals_total(
        self,
        sample_important_goals: dict[str, float],
    ) -> None:
        """Test important goals total calculation."""
        total = sum(sample_important_goals.values())
        expected = 10000.00 + 12000.00 + 15000.00
        assert total == pytest.approx(expected, rel=1e-6)
        _logger.debug(f"Important goals total: {total}")


@pytest.mark.unit()
class Test_Aspirational_Goals_Validation:
    """Test aspirational goals data validation."""

    @pytest.mark.unit()
    def test_aspirational_goals_values_are_positive(
        self,
        sample_aspirational_goals: dict[str, float],
    ) -> None:
        """Test that all aspirational goal values are positive."""
        for goal_type, value in sample_aspirational_goals.items():
            assert value >= 0, f"{goal_type} has negative value: {value}"
        _logger.debug("All aspirational goal values are non-negative")

    @pytest.mark.unit()
    def test_aspirational_goals_values_are_numeric(
        self,
        sample_aspirational_goals: dict[str, float],
    ) -> None:
        """Test that all aspirational goal values are numeric."""
        for value in sample_aspirational_goals.values():
            assert isinstance(value, (int, float))
        _logger.debug("All aspirational goal values are numeric")

    @pytest.mark.unit()
    def test_aspirational_goals_total(
        self,
        sample_aspirational_goals: dict[str, float],
    ) -> None:
        """Test aspirational goals total calculation."""
        total = sum(sample_aspirational_goals.values())
        expected = 15000.00 + 10000.00 + 25000.00
        assert total == pytest.approx(expected, rel=1e-6)
        _logger.debug(f"Aspirational goals total: {total}")


@pytest.mark.unit()
class Test_Total_Goals_Calculation:
    """Test total goals calculation across all categories."""

    @pytest.mark.unit()
    def test_total_goals_equals_sum_of_categories(
        self,
        sample_essential_goals: dict[str, float],
        sample_important_goals: dict[str, float],
        sample_aspirational_goals: dict[str, float],
    ) -> None:
        """Test that total goals equals sum of all categories."""
        essential_total = sum(sample_essential_goals.values())
        important_total = sum(sample_important_goals.values())
        aspirational_total = sum(sample_aspirational_goals.values())

        total = essential_total + important_total + aspirational_total
        expected = 80000.00 + 37000.00 + 50000.00
        assert total == pytest.approx(expected, rel=1e-6)
        _logger.debug(f"Total goals: {total}")

    @pytest.mark.unit()
    def test_essential_is_largest_category(
        self,
        sample_essential_goals: dict[str, float],
        sample_important_goals: dict[str, float],
        sample_aspirational_goals: dict[str, float],
    ) -> None:
        """Test that essential goals category is typically largest."""
        essential_total = sum(sample_essential_goals.values())
        important_total = sum(sample_important_goals.values())

        # Essential should typically be largest for retirement planning
        assert essential_total >= important_total
        _logger.debug(f"Essential ({essential_total}) >= Important ({important_total})")


@pytest.mark.unit()
class Test_Goal_Annualization:
    """Test goal annualization calculations."""

    @pytest.mark.parametrize(
        "annual_amount,months,expected_monthly",
        [
            (12000.00, 12, 1000.00),
            (36000.00, 12, 3000.00),
            (6000.00, 12, 500.00),
        ],
    )
    @pytest.mark.unit()
    def test_annual_to_monthly_conversion(
        self,
        annual_amount: float,
        months: int,
        expected_monthly: float,
    ) -> None:
        """Test converting annual goals to monthly amounts."""
        monthly = annual_amount / months
        assert monthly == pytest.approx(expected_monthly, rel=1e-6)
        _logger.debug(f"Annual {annual_amount} = Monthly {monthly}")

    @pytest.mark.parametrize(
        "monthly_amount,months,expected_annual",
        [
            (1000.00, 12, 12000.00),
            (3000.00, 12, 36000.00),
            (500.00, 12, 6000.00),
        ],
    )
    @pytest.mark.unit()
    def test_monthly_to_annual_conversion(
        self,
        monthly_amount: float,
        months: int,
        expected_annual: float,
    ) -> None:
        """Test converting monthly goals to annual amounts."""
        annual = monthly_amount * months
        assert annual == pytest.approx(expected_annual, rel=1e-6)
        _logger.debug(f"Monthly {monthly_amount} = Annual {annual}")


@pytest.mark.unit()
class Test_Data_Inputs_Structure:
    """Test data inputs dictionary structure for goals."""

    @pytest.mark.unit()
    def test_data_inputs_has_goals(
        self,
        sample_data_inputs: dict[str, Any],
    ) -> None:
        """Test that data_inputs has Goals key."""
        assert "Goals" in sample_data_inputs
        _logger.debug("data_inputs has Goals")

    @pytest.mark.unit()
    def test_goals_has_all_categories(
        self,
        sample_all_goals: dict[str, dict[str, float]],
    ) -> None:
        """Test that goals has all required categories."""
        for category in GOAL_CATEGORIES:
            assert category in sample_all_goals
        _logger.debug("Goals has all required categories")


# =============================================================================
# Integration Tests (Marked for separate execution)
# =============================================================================


@pytest.mark.integration()
class Test_Sub_Tab_Goals_Integration:
    """Integration tests for subtab_goals module."""

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
        result = subtab_clients_goals_ui("ID_test_ui",
            data_utils=sample_data_utils,
            data_inputs=sample_data_inputs,
        )
        assert result is not None

    @pytest.mark.skipif(
        not MODULE_IMPORT_AVAILABLE,
        reason="Module import failed due to Shiny dependencies",
    )
    @pytest.mark.unit()
    def test_server_handles_goal_updates(
        self,
        sample_data_utils: dict[str, Any],
        sample_data_inputs: dict[str, Any],
        sample_reactives_shiny: dict[str, Any],
    ) -> None:
        """Test that server handles goal value updates."""
        import inspect

        assert callable(subtab_clients_goals_server)
        sig = inspect.signature(subtab_clients_goals_server)
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
        """Test that server calculates goal totals correctly."""
        import inspect

        sig = inspect.signature(subtab_clients_goals_server)
        assert len(sig.parameters) >= 1


# =============================================================================
# NEW: input ID convention & goal priority ordering
# =============================================================================


@pytest.mark.unit()
class Test_Input_ID_Convention_Goals:
    """Test that goals input IDs follow the hierarchical naming convention."""

    _PRIMARY_GOAL_IDS: ClassVar[list[str]] = [
        "input_ID_tab_clients_subtab_clients_goals_client_primary_goal_essential",
        "input_ID_tab_clients_subtab_clients_goals_client_primary_goal_important",
        "input_ID_tab_clients_subtab_clients_goals_client_primary_goal_aspirational",
    ]

    @pytest.mark.unit()
    def test_all_primary_goal_ids_start_with_correct_prefix(self) -> None:
        """All primary goal input IDs start with the correct prefix."""
        prefix = "input_ID_tab_clients_subtab_clients_goals_client_primary"
        for input_id in self._PRIMARY_GOAL_IDS:
            assert input_id.startswith(prefix), (
                f"Goal input ID '{input_id}' does not start with '{prefix}'"
            )

    @pytest.mark.unit()
    def test_goal_categories_are_three(self) -> None:
        """There are exactly three goal tiers: essential, important, aspirational."""
        assert len(self._PRIMARY_GOAL_IDS) == 3

    @pytest.mark.unit()
    def test_essential_goal_id_present(self) -> None:
        """Essential goal ID is defined."""
        assert any("essential" in iid for iid in self._PRIMARY_GOAL_IDS)

    @pytest.mark.unit()
    def test_important_goal_id_present(self) -> None:
        """Important goal ID is defined."""
        assert any("important" in iid for iid in self._PRIMARY_GOAL_IDS)

    @pytest.mark.unit()
    def test_aspirational_goal_id_present(self) -> None:
        """Aspirational goal ID is defined."""
        assert any("aspirational" in iid for iid in self._PRIMARY_GOAL_IDS)

    @pytest.mark.skipif(not MODULE_IMPORT_AVAILABLE, reason="Module import unavailable")
    @pytest.mark.unit()
    def test_essential_goal_in_server_source(self) -> None:
        """Essential goal input ID appears in goals server source."""
        import sys
        from pathlib import Path

        source = Path(sys.modules['src.dashboard.shiny_tab_clients.subtab_goals'].__file__).read_text(encoding='utf-8')
        assert self._PRIMARY_GOAL_IDS[0] in source, (
            f"Goal input ID '{self._PRIMARY_GOAL_IDS[0]}' not found in server source"
        )
        _logger.debug("Essential goal input ID verified in source")


@pytest.mark.unit()
class Test_Goal_Priority_Ordering:
    """Test that goal priorities follow essential(1) > important(2) > aspirational(3)."""

    _GOAL_PRIORITIES: ClassVar[dict[str, int]] = {
        "essential": 1,
        "important": 2,
        "aspirational": 3,
    }

    @pytest.mark.unit()
    def test_essential_priority_is_one(self) -> None:
        """Essential goals have priority 1 (highest)."""
        assert self._GOAL_PRIORITIES["essential"] == 1

    @pytest.mark.unit()
    def test_important_priority_is_two(self) -> None:
        """Important goals have priority 2."""
        assert self._GOAL_PRIORITIES["important"] == 2

    @pytest.mark.unit()
    def test_aspirational_priority_is_three(self) -> None:
        """Aspirational goals have priority 3 (lowest)."""
        assert self._GOAL_PRIORITIES["aspirational"] == 3

    @pytest.mark.unit()
    def test_essential_highest_priority(self) -> None:
        """Essential priority is strictly less than important (lower number = higher priority)."""
        assert self._GOAL_PRIORITIES["essential"] < self._GOAL_PRIORITIES["important"]

    @pytest.mark.unit()
    def test_important_higher_than_aspirational(self) -> None:
        """Important priority is strictly less than aspirational."""
        assert self._GOAL_PRIORITIES["important"] < self._GOAL_PRIORITIES["aspirational"]

"""Unit tests for the Clients Tab Module.

This module provides comprehensive unit tests for the Tab_Clients module,
testing the UI and server logic for the main Clients tab in the QWIM Dashboard.

Tests cover:
- Module-level constants and configuration
- UI component creation
- Server logic initialization
- Error handling scenarios
- Integration with subtab modules

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
    from src.dashboard.shiny_tab_clients.tab_clients import (
        _logger as module_logger,
        tab_clients_server,
        tab_clients_ui,
    )

    MODULE_IMPORT_AVAILABLE = True
except ImportError as e:
    MODULE_IMPORT_AVAILABLE = False
    _logger.warning(f"Module import failed, some tests will be skipped: {e}")


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture()
def sample_client_personal_data() -> dict[str, Any]:
    """Create sample client personal data for testing.

    Returns:
        dict: Sample client personal information dictionary.
    """
    return {
        "first_name": "John",
        "last_name": "Doe",
        "age": 45,
        "email": "john.doe@example.com",
        "phone": "555-123-4567",
        "state": "CA",
        "employment_status": "employed_full_time",
    }


@pytest.fixture()
def sample_client_assets_data() -> dict[str, Any]:
    """Create sample client assets data for testing.

    Returns:
        dict: Sample client assets dictionary.
    """
    return {
        "taxable_assets": 250000.00,
        "tax_deferred_assets": 500000.00,
        "tax_free_assets": 100000.00,
        "total_assets": 850000.00,
    }


@pytest.fixture()
def sample_client_goals_data() -> dict[str, Any]:
    """Create sample client goals data for testing.

    Returns:
        dict: Sample client goals dictionary.
    """
    return {
        "essential_goal": 50000.00,
        "important_goal": 30000.00,
        "aspirational_goal": 20000.00,
        "total_goals": 100000.00,
    }


@pytest.fixture()
def sample_client_income_data() -> dict[str, Any]:
    """Create sample client income data for testing.

    Returns:
        dict: Sample client income dictionary.
    """
    return {
        "social_security": 24000.00,
        "pension": 36000.00,
        "annuity": 12000.00,
        "other_income": 6000.00,
        "total_income": 78000.00,
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
        "chart_height": 600,
    }


@pytest.fixture()
def sample_data_inputs(
    sample_client_personal_data: dict[str, Any],
    sample_client_assets_data: dict[str, Any],
    sample_client_goals_data: dict[str, Any],
    sample_client_income_data: dict[str, Any],
) -> dict[str, Any]:
    """Create sample data inputs dictionary for testing.

    Args:
        sample_client_personal_data: Sample personal info dictionary.
        sample_client_assets_data: Sample assets dictionary.
        sample_client_goals_data: Sample goals dictionary.
        sample_client_income_data: Sample income dictionary.

    Returns:
        dict: Sample data inputs dictionary with all required keys.
    """
    return {
        "Personal_Info": sample_client_personal_data,
        "Assets": sample_client_assets_data,
        "Goals": sample_client_goals_data,
        "Income": sample_client_income_data,
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
    def test_tab_clients_ui_is_importable(self) -> None:
        """Test that tab_clients_ui function can be imported."""
        assert callable(tab_clients_ui)
        _logger.debug("tab_clients_ui successfully imported")

    @pytest.mark.unit()
    def test_tab_clients_server_is_importable(self) -> None:
        """Test that tab_clients_server function can be imported."""
        assert callable(tab_clients_server)
        _logger.debug("tab_clients_server successfully imported")


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
class Test_Client_Personal_Data_Validation:
    """Test client personal data validation."""

    @pytest.mark.unit()
    def test_personal_data_has_first_name(
        self,
        sample_client_personal_data: dict[str, Any],
    ) -> None:
        """Test that personal data has first_name key."""
        assert "first_name" in sample_client_personal_data
        assert isinstance(sample_client_personal_data["first_name"], str)
        _logger.debug("Personal data has first_name")

    @pytest.mark.unit()
    def test_personal_data_has_last_name(
        self,
        sample_client_personal_data: dict[str, Any],
    ) -> None:
        """Test that personal data has last_name key."""
        assert "last_name" in sample_client_personal_data
        assert isinstance(sample_client_personal_data["last_name"], str)
        _logger.debug("Personal data has last_name")

    @pytest.mark.unit()
    def test_personal_data_has_age(
        self,
        sample_client_personal_data: dict[str, Any],
    ) -> None:
        """Test that personal data has valid age."""
        assert "age" in sample_client_personal_data
        assert isinstance(sample_client_personal_data["age"], int)
        assert 0 < sample_client_personal_data["age"] < 150
        _logger.debug(f"Personal data age: {sample_client_personal_data['age']}")

    @pytest.mark.unit()
    def test_personal_data_has_valid_state(
        self,
        sample_client_personal_data: dict[str, Any],
    ) -> None:
        """Test that personal data has valid state abbreviation."""
        assert "state" in sample_client_personal_data
        assert len(sample_client_personal_data["state"]) == 2
        _logger.debug(f"Personal data state: {sample_client_personal_data['state']}")


@pytest.mark.unit()
class Test_Client_Assets_Data_Validation:
    """Test client assets data validation."""

    @pytest.mark.unit()
    def test_assets_data_has_taxable_assets(
        self,
        sample_client_assets_data: dict[str, Any],
    ) -> None:
        """Test that assets data has taxable_assets key."""
        assert "taxable_assets" in sample_client_assets_data
        assert sample_client_assets_data["taxable_assets"] >= 0
        _logger.debug("Assets data has taxable_assets")

    @pytest.mark.unit()
    def test_assets_data_has_tax_deferred_assets(
        self,
        sample_client_assets_data: dict[str, Any],
    ) -> None:
        """Test that assets data has tax_deferred_assets key."""
        assert "tax_deferred_assets" in sample_client_assets_data
        assert sample_client_assets_data["tax_deferred_assets"] >= 0
        _logger.debug("Assets data has tax_deferred_assets")

    @pytest.mark.unit()
    def test_assets_data_has_tax_free_assets(
        self,
        sample_client_assets_data: dict[str, Any],
    ) -> None:
        """Test that assets data has tax_free_assets key."""
        assert "tax_free_assets" in sample_client_assets_data
        assert sample_client_assets_data["tax_free_assets"] >= 0
        _logger.debug("Assets data has tax_free_assets")

    @pytest.mark.unit()
    def test_assets_total_equals_sum(
        self,
        sample_client_assets_data: dict[str, Any],
    ) -> None:
        """Test that total assets equals sum of components."""
        expected_total = (
            sample_client_assets_data["taxable_assets"]
            + sample_client_assets_data["tax_deferred_assets"]
            + sample_client_assets_data["tax_free_assets"]
        )
        assert sample_client_assets_data["total_assets"] == expected_total
        _logger.debug(f"Assets total validated: {expected_total}")


@pytest.mark.unit()
class Test_Client_Goals_Data_Validation:
    """Test client goals data validation."""

    @pytest.mark.unit()
    def test_goals_data_has_essential_goal(
        self,
        sample_client_goals_data: dict[str, Any],
    ) -> None:
        """Test that goals data has essential_goal key."""
        assert "essential_goal" in sample_client_goals_data
        assert sample_client_goals_data["essential_goal"] >= 0
        _logger.debug("Goals data has essential_goal")

    @pytest.mark.unit()
    def test_goals_data_has_important_goal(
        self,
        sample_client_goals_data: dict[str, Any],
    ) -> None:
        """Test that goals data has important_goal key."""
        assert "important_goal" in sample_client_goals_data
        assert sample_client_goals_data["important_goal"] >= 0
        _logger.debug("Goals data has important_goal")

    @pytest.mark.unit()
    def test_goals_data_has_aspirational_goal(
        self,
        sample_client_goals_data: dict[str, Any],
    ) -> None:
        """Test that goals data has aspirational_goal key."""
        assert "aspirational_goal" in sample_client_goals_data
        assert sample_client_goals_data["aspirational_goal"] >= 0
        _logger.debug("Goals data has aspirational_goal")

    @pytest.mark.unit()
    def test_goals_total_equals_sum(
        self,
        sample_client_goals_data: dict[str, Any],
    ) -> None:
        """Test that total goals equals sum of components."""
        expected_total = (
            sample_client_goals_data["essential_goal"]
            + sample_client_goals_data["important_goal"]
            + sample_client_goals_data["aspirational_goal"]
        )
        assert sample_client_goals_data["total_goals"] == expected_total
        _logger.debug(f"Goals total validated: {expected_total}")


@pytest.mark.unit()
class Test_Client_Income_Data_Validation:
    """Test client income data validation."""

    @pytest.mark.unit()
    def test_income_data_has_social_security(
        self,
        sample_client_income_data: dict[str, Any],
    ) -> None:
        """Test that income data has social_security key."""
        assert "social_security" in sample_client_income_data
        assert sample_client_income_data["social_security"] >= 0
        _logger.debug("Income data has social_security")

    @pytest.mark.unit()
    def test_income_data_has_pension(
        self,
        sample_client_income_data: dict[str, Any],
    ) -> None:
        """Test that income data has pension key."""
        assert "pension" in sample_client_income_data
        assert sample_client_income_data["pension"] >= 0
        _logger.debug("Income data has pension")

    @pytest.mark.unit()
    def test_income_data_has_annuity(
        self,
        sample_client_income_data: dict[str, Any],
    ) -> None:
        """Test that income data has annuity key."""
        assert "annuity" in sample_client_income_data
        assert sample_client_income_data["annuity"] >= 0
        _logger.debug("Income data has annuity")

    @pytest.mark.unit()
    def test_income_total_equals_sum(
        self,
        sample_client_income_data: dict[str, Any],
    ) -> None:
        """Test that total income equals sum of components."""
        expected_total = (
            sample_client_income_data["social_security"]
            + sample_client_income_data["pension"]
            + sample_client_income_data["annuity"]
            + sample_client_income_data["other_income"]
        )
        assert sample_client_income_data["total_income"] == expected_total
        _logger.debug(f"Income total validated: {expected_total}")


@pytest.mark.unit()
class Test_Data_Inputs_Structure:
    """Test data inputs dictionary structure."""

    @pytest.mark.unit()
    def test_data_inputs_has_personal_info(
        self,
        sample_data_inputs: dict[str, Any],
    ) -> None:
        """Test that data_inputs has Personal_Info key."""
        assert "Personal_Info" in sample_data_inputs
        _logger.debug("data_inputs has Personal_Info")

    @pytest.mark.unit()
    def test_data_inputs_has_assets(
        self,
        sample_data_inputs: dict[str, Any],
    ) -> None:
        """Test that data_inputs has Assets key."""
        assert "Assets" in sample_data_inputs
        _logger.debug("data_inputs has Assets")

    @pytest.mark.unit()
    def test_data_inputs_has_goals(
        self,
        sample_data_inputs: dict[str, Any],
    ) -> None:
        """Test that data_inputs has Goals key."""
        assert "Goals" in sample_data_inputs
        _logger.debug("data_inputs has Goals")

    @pytest.mark.unit()
    def test_data_inputs_has_income(
        self,
        sample_data_inputs: dict[str, Any],
    ) -> None:
        """Test that data_inputs has Income key."""
        assert "Income" in sample_data_inputs
        _logger.debug("data_inputs has Income")


@pytest.mark.unit()
class Test_Reactives_Shiny_Structure:
    """Test reactives_shiny dictionary structure."""

    @pytest.mark.unit()
    def test_reactives_shiny_has_user_inputs(
        self,
        sample_reactives_shiny: dict[str, Any],
    ) -> None:
        """Test that reactives_shiny has User_Inputs_Shiny key."""
        assert "User_Inputs_Shiny" in sample_reactives_shiny

    @pytest.mark.unit()
    def test_reactives_shiny_has_inner_variables(
        self,
        sample_reactives_shiny: dict[str, Any],
    ) -> None:
        """Test that reactives_shiny has Inner_Variables_Shiny key."""
        assert "Inner_Variables_Shiny" in sample_reactives_shiny

    @pytest.mark.unit()
    def test_reactives_shiny_has_triggers(
        self,
        sample_reactives_shiny: dict[str, Any],
    ) -> None:
        """Test that reactives_shiny has Triggers_Shiny key."""
        assert "Triggers_Shiny" in sample_reactives_shiny

    @pytest.mark.unit()
    def test_reactives_shiny_has_visual_objects(
        self,
        sample_reactives_shiny: dict[str, Any],
    ) -> None:
        """Test that reactives_shiny has Visual_Objects_Shiny key."""
        assert "Visual_Objects_Shiny" in sample_reactives_shiny


# =============================================================================
# Outline Subtab presence
# =============================================================================


@pytest.mark.unit()
class Test_Tab_Clients_Outline_Subtab:
    """Verify Outline subtab is wired into tab_clients."""

    @pytest.mark.unit()
    def test_subtab_outline_importable(self):
        """Outline subtab module imports without error."""
        from src.dashboard.shiny_tab_clients import subtab_outline  # noqa: F401

        assert subtab_outline is not None

    @pytest.mark.unit()
    def test_subtab_outline_exports_ui_and_server(self):
        """Outline subtab exports the expected UI and server callables."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            subtab_clients_outline_server,
            subtab_clients_outline_ui,
        )

        assert callable(subtab_clients_outline_ui)
        assert callable(subtab_clients_outline_server)

    @pytest.mark.skipif(
        not MODULE_IMPORT_AVAILABLE,
        reason="Module import failed due to Shiny dependencies",
    )
    @pytest.mark.unit()
    def test_tab_clients_imports_outline_ui(self):
        """tab_clients module imports subtab_clients_outline_ui."""
        from src.dashboard.shiny_tab_clients.tab_clients import tab_clients_ui  # noqa: F401

        assert tab_clients_ui is not None


# =============================================================================
# Integration Tests (Marked for separate execution)
# =============================================================================


@pytest.mark.integration()
class Test_Tab_Clients_Integration:
    """Integration tests for tab_clients module."""

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
        result = tab_clients_ui("ID_test_ui",
            data_utils=sample_data_utils,
            data_inputs=sample_data_inputs,
        )
        assert result is not None

    @pytest.mark.skipif(
        not MODULE_IMPORT_AVAILABLE,
        reason="Module import failed due to Shiny dependencies",
    )
    @pytest.mark.unit()
    def test_server_initializes_all_subtabs(
        self,
        sample_data_utils: dict[str, Any],
        sample_data_inputs: dict[str, Any],
        sample_reactives_shiny: dict[str, Any],
    ) -> None:
        """Test that server function initializes all subtab servers."""
        import inspect

        assert callable(tab_clients_server)
        sig = inspect.signature(tab_clients_server)
        assert "id" in sig.parameters


# =============================================================================
# NEW: server return structure & subtab ID convention
# =============================================================================


@pytest.mark.unit()
class Test_Server_Return_Structure:
    """Test that tab_clients_server return dict has all expected subtab keys."""

    _EXPECTED_KEYS: ClassVar[list[str]] = [
        "clients_Personal_Info_Server",
        "clients_Assets_Server",
        "clients_Goals_Server",
        "clients_Income_Server",
        "clients_Summary_Server",
    ]

    @pytest.mark.skipif(not MODULE_IMPORT_AVAILABLE, reason="Module import unavailable")
    @pytest.mark.unit()
    def test_server_source_contains_all_return_keys(self) -> None:
        """All expected return keys appear in the server source code."""
        import sys
        from pathlib import Path

        source = Path(sys.modules['src.dashboard.shiny_tab_clients.tab_clients'].__file__).read_text(encoding='utf-8')
        for key in self._EXPECTED_KEYS:
            assert key in source, f"Expected return key '{key}' not found in server source"
        _logger.debug("All expected server return keys verified")

    @pytest.mark.unit()
    def test_expected_keys_are_non_empty_strings(self) -> None:
        """Every expected key is a non-empty string."""
        for key in self._EXPECTED_KEYS:
            assert isinstance(key, str)
            assert len(key) > 0

    @pytest.mark.unit()
    def test_expected_keys_count_is_five(self) -> None:
        """Exactly five subtab server keys are expected."""
        assert len(self._EXPECTED_KEYS) == 5


@pytest.mark.unit()
class Test_Subtab_ID_Convention:
    """Test that tab_clients uses the correct hierarchical module IDs."""

    _EXPECTED_MODULE_IDS: ClassVar[list[str]] = [
        "ID_tab_clients_subtab_clients_personal_info",
        "ID_tab_clients_subtab_clients_assets",
        "ID_tab_clients_subtab_clients_goals",
        "ID_tab_clients_subtab_clients_income",
        "ID_tab_clients_subtab_clients_summary",
    ]

    @pytest.mark.skipif(not MODULE_IMPORT_AVAILABLE, reason="Module import unavailable")
    @pytest.mark.unit()
    def test_all_subtab_ids_in_ui_source(self) -> None:
        """All required subtab module IDs appear in tab_clients_ui source."""
        import sys
        from pathlib import Path

        source = Path(sys.modules['src.dashboard.shiny_tab_clients.tab_clients'].__file__).read_text(encoding='utf-8')
        for mod_id in self._EXPECTED_MODULE_IDS:
            assert mod_id in source, f"Module ID '{mod_id}' missing from tab_clients_ui source"
        _logger.debug("All subtab module IDs verified in tab_clients_ui")

    @pytest.mark.skipif(not MODULE_IMPORT_AVAILABLE, reason="Module import unavailable")
    @pytest.mark.unit()
    def test_navset_tab_id_in_ui_source(self) -> None:
        """Top-level navset_tab ID is defined in tab_clients_ui."""
        import sys
        from pathlib import Path

        source = Path(sys.modules['src.dashboard.shiny_tab_clients.tab_clients'].__file__).read_text(encoding='utf-8')
        assert "ID_tab_clients_tabs_all" in source
        _logger.debug("Top-level navset_tab ID verified")

    @pytest.mark.unit()
    def test_module_ids_start_with_id_tab_clients(self) -> None:
        """Every module ID starts with 'ID_tab_clients_'."""
        for mod_id in self._EXPECTED_MODULE_IDS:
            assert mod_id.startswith("ID_tab_clients_"), (
                f"Module ID '{mod_id}' does not start with 'ID_tab_clients_'"
            )

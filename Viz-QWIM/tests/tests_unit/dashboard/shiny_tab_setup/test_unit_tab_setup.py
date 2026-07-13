"""Unit tests for tab_setup module.

Tests cover:
- Module imports correctly
- ``tab_setup_ui`` and ``tab_setup_server`` callables exist and are exported
- Advisor subtab is imported into the module
"""

from __future__ import annotations

import pytest


# Try importing the module under test
try:
    from src.dashboard.shiny_tab_setup.tab_setup import (
        tab_setup_server,
        tab_setup_ui,
    )

    MODULE_IMPORT_AVAILABLE = True
except ImportError:
    MODULE_IMPORT_AVAILABLE = False


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture()
def mock_data_utils():
    """Create mock data_utils dictionary."""
    return {
        "project_dir": "/mock/project",
        "DEFAULTS": {},
    }


@pytest.fixture()
def mock_data_inputs():
    """Create mock data_inputs dictionary."""
    return {}


# ============================================================================
# Module-level import tests
# ============================================================================


@pytest.mark.unit()
class Test_Tab_Setup_Module_Imports:
    """Verify tab_setup module imports and exports are correct."""

    @pytest.mark.unit()
    def test_module_importable(self):
        """tab_setup module imports without error."""
        import src.dashboard.shiny_tab_setup.tab_setup as tab_setup_mod

        assert tab_setup_mod is not None

    @pytest.mark.unit()
    def test_tab_setup_ui_callable(self):
        """tab_setup_ui is a callable."""
        from src.dashboard.shiny_tab_setup.tab_setup import tab_setup_ui

        assert callable(tab_setup_ui)

    @pytest.mark.unit()
    def test_tab_setup_server_callable(self):
        """tab_setup_server is a callable."""
        from src.dashboard.shiny_tab_setup.tab_setup import tab_setup_server

        assert callable(tab_setup_server)

    @pytest.mark.unit()
    def test_advisor_subtab_ui_imported(self):
        """subtab_advisor_info_ui is imported into tab_setup module."""
        import src.dashboard.shiny_tab_setup.tab_setup as tab_setup_mod

        assert hasattr(tab_setup_mod, "subtab_advisor_info_ui")

    @pytest.mark.unit()
    def test_advisor_subtab_server_imported(self):
        """subtab_advisor_info_server is imported into tab_setup module."""
        import src.dashboard.shiny_tab_setup.tab_setup as tab_setup_mod

        assert hasattr(tab_setup_mod, "subtab_advisor_info_server")

    @pytest.mark.unit()
    def test_computation_subtab_ui_imported(self):
        """subtab_computation_ui is imported into tab_setup module."""
        import src.dashboard.shiny_tab_setup.tab_setup as tab_setup_mod

        assert hasattr(tab_setup_mod, "subtab_computation_ui")

    @pytest.mark.unit()
    def test_computation_subtab_server_imported(self):
        """subtab_computation_server is imported into tab_setup module."""
        import src.dashboard.shiny_tab_setup.tab_setup as tab_setup_mod

        assert hasattr(tab_setup_mod, "subtab_computation_server")

    @pytest.mark.unit()
    def test_logger_initialised(self):
        """Module-level _logger is initialised."""
        import src.dashboard.shiny_tab_setup.tab_setup as tab_setup_mod

        assert hasattr(tab_setup_mod, "_logger")
        assert tab_setup_mod._logger is not None


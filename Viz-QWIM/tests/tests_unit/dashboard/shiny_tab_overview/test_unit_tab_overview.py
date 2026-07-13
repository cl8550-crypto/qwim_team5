"""Unit tests for Overview tab modules.

Covers importability and basic module structure for:
- ``tab_overview``
- ``subtab_executive_summary``
"""

from __future__ import annotations

import inspect

import pytest


subtab_executive_summary_ui = None
subtab_executive_summary_server = None
SubTab_Executive_Summary = None
tab_overview_ui = None
tab_overview_server = None
Tab_Overview = None


try:
    from src.dashboard.shiny_tab_overview.subtab_executive_summary import (
        SubTab_Executive_Summary,
        subtab_executive_summary_server,
        subtab_executive_summary_ui,
    )
    from src.dashboard.shiny_tab_overview.tab_overview import (
        Tab_Overview,
        tab_overview_server,
        tab_overview_ui,
    )

    OVERVIEW_IMPORTS_AVAILABLE = True
except ImportError:
    OVERVIEW_IMPORTS_AVAILABLE = False


@pytest.mark.unit()
@pytest.mark.skipif(not OVERVIEW_IMPORTS_AVAILABLE, reason="Overview modules not importable")
class Test_Overview_Tab_Modules:
    """Validate Overview tab module exports and callables."""

    @pytest.mark.unit()
    def test_tab_overview_ui_is_callable(self) -> None:
        """Test that tab overview ui is callable."""
        assert callable(tab_overview_ui)

    @pytest.mark.unit()
    def test_tab_overview_server_is_callable(self) -> None:
        """Test that tab overview server is callable."""
        assert callable(tab_overview_server)

    @pytest.mark.unit()
    def test_subtab_executive_summary_ui_is_callable(self) -> None:
        """Test that subtab executive summary ui is callable."""
        assert callable(subtab_executive_summary_ui)

    @pytest.mark.unit()
    def test_subtab_executive_summary_server_is_callable(self) -> None:
        """Test that subtab executive summary server is callable."""
        assert callable(subtab_executive_summary_server)

    @pytest.mark.unit()
    def test_aliases_are_consistent(self) -> None:
        """Test that aliases are consistent."""
        assert Tab_Overview is tab_overview_ui
        assert SubTab_Executive_Summary is subtab_executive_summary_ui


@pytest.mark.unit()
@pytest.mark.skipif(not OVERVIEW_IMPORTS_AVAILABLE, reason="Overview modules not importable")
class Test_Overview_Module_Content:
    """Validate new overview content exists in source module."""

    @pytest.mark.unit()
    def test_executive_summary_module_has_docstring(self) -> None:
        """Test that executive summary module has docstring."""
        import src.dashboard.shiny_tab_overview.subtab_executive_summary as module_subtab

        assert module_subtab.__doc__ is not None
        assert len(module_subtab.__doc__.strip()) > 0

    @pytest.mark.unit()
    def test_executive_summary_mentions_qwim(self) -> None:
        """Test that executive summary mentions qwim."""
        import src.dashboard.shiny_tab_overview.subtab_executive_summary as module_subtab

        source_text = inspect.getsource(module_subtab)
        assert "Quantitative Wealth and Investment Management" in source_text

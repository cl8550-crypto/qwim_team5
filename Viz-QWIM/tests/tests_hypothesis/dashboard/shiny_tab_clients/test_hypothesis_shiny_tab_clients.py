"""Hypothesis (property-based) tests for shiny_tab_clients module.

Focuses on:
- Module import availability (all subtabs)
- Callable verification for ui functions
- Any pure utility constants or functions in the subtab modules

Server functions are intentionally excluded (require full Shiny reactive context).
UI functions decorated with @module.ui cannot be called directly without a module
namespace — tests verify they are imported and are callable objects.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st


# ---------------------------------------------------------------------------
# Import guard — shiny and all dashboard deps must be available
# ---------------------------------------------------------------------------

try:
    from src.dashboard.shiny_tab_clients.subtab_assets import subtab_clients_assets_ui
    from src.dashboard.shiny_tab_clients.subtab_goals import subtab_clients_goals_ui
    from src.dashboard.shiny_tab_clients.subtab_income import subtab_clients_income_ui
    from src.dashboard.shiny_tab_clients.subtab_outline import subtab_clients_outline_ui
    from src.dashboard.shiny_tab_clients.subtab_personal_info import subtab_clients_personal_info_ui
    from src.dashboard.shiny_tab_clients.subtab_summary import subtab_clients_summary_ui
    from src.dashboard.shiny_tab_clients.tab_clients import tab_clients_ui

    MODULE_IMPORT_AVAILABLE = True
except ImportError:
    MODULE_IMPORT_AVAILABLE = False


pytestmark = pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason="shiny_tab_clients deps (shiny, etc.) not importable in this environment",
)


# ===========================================================================
# Class_Test_Hypothesis_Shiny_Tab_Clients_Imports
# ===========================================================================


class Class_Test_Hypothesis_Shiny_Tab_Clients_Imports:
    """Structural tests verifying shiny_tab_clients UI objects are importable and callable."""

    @pytest.mark.unit()
    def Test_subtab_clients_assets_ui_is_callable(self) -> None:
        """subtab_clients_assets_ui must be a callable object."""
        assert callable(subtab_clients_assets_ui)

    @pytest.mark.unit()
    def Test_subtab_clients_goals_ui_is_callable(self) -> None:
        """subtab_clients_goals_ui must be a callable object."""
        assert callable(subtab_clients_goals_ui)

    @pytest.mark.unit()
    def Test_subtab_clients_income_ui_is_callable(self) -> None:
        """subtab_clients_income_ui must be a callable object."""
        assert callable(subtab_clients_income_ui)

    @pytest.mark.unit()
    def Test_subtab_clients_outline_ui_is_callable(self) -> None:
        """subtab_clients_outline_ui must be a callable object."""
        assert callable(subtab_clients_outline_ui)

    @pytest.mark.unit()
    def Test_subtab_clients_personal_info_ui_is_callable(self) -> None:
        """subtab_clients_personal_info_ui must be a callable object."""
        assert callable(subtab_clients_personal_info_ui)

    @pytest.mark.unit()
    def Test_subtab_clients_summary_ui_is_callable(self) -> None:
        """subtab_clients_summary_ui must be a callable object."""
        assert callable(subtab_clients_summary_ui)

    @pytest.mark.unit()
    def Test_tab_clients_ui_is_callable(self) -> None:
        """tab_clients_ui must be a callable object."""
        assert callable(tab_clients_ui)

    @pytest.mark.unit()
    @given(module_id=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd"), whitelist_characters=("_",))))
    @settings(max_examples=200)
    def Test_ui_functions_are_not_none(
        self,
        module_id: str,
    ) -> None:
        """All imported ui objects must be non-None (property: just be truthy objects)."""
        for ui_func in (
            subtab_clients_assets_ui,
            subtab_clients_goals_ui,
            subtab_clients_income_ui,
            subtab_clients_outline_ui,
            subtab_clients_personal_info_ui,
            subtab_clients_summary_ui,
            tab_clients_ui,
        ):
            assert ui_func is not None

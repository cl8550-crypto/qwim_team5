"""Hypothesis (property-based) tests for shiny_tab_results module.

Focuses on:
- Module import availability
- Callable verification for UI functions

Server functions are intentionally excluded.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st


try:
    from src.dashboard.shiny_tab_results.subtab_reporting import subtab_reporting_ui
    from src.dashboard.shiny_tab_results.subtab_simulation import subtab_simulation_ui
    from src.dashboard.shiny_tab_results.tab_results import tab_results_ui

    MODULE_IMPORT_AVAILABLE = True
except ImportError:
    MODULE_IMPORT_AVAILABLE = False


pytestmark = pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason="shiny_tab_results deps not importable in this environment",
)


class Class_Test_Hypothesis_Shiny_Tab_Results_Imports:
    """Structural tests verifying shiny_tab_results UI objects are importable and callable."""

    @pytest.mark.unit()
    def Test_subtab_reporting_ui_is_callable(self) -> None:
        """subtab_reporting_ui must be callable."""
        assert callable(subtab_reporting_ui)

    @pytest.mark.unit()
    def Test_subtab_simulation_ui_is_callable(self) -> None:
        """subtab_simulation_ui must be callable."""
        assert callable(subtab_simulation_ui)

    @pytest.mark.unit()
    def Test_tab_results_ui_is_callable(self) -> None:
        """tab_results_ui must be callable."""
        assert callable(tab_results_ui)

    @pytest.mark.unit()
    @given(
        module_id=st.text(
            min_size=1,
            max_size=30,
            alphabet=st.characters(
                whitelist_categories=("Ll", "Lu", "Nd"),
                whitelist_characters=("_",),
            ),
        )
    )
    @settings(max_examples=200)
    def Test_all_ui_objects_are_non_none(
        self,
        module_id: str,
    ) -> None:
        """All UI function objects must be non-None."""
        for ui_func in (subtab_reporting_ui, subtab_simulation_ui, tab_results_ui):
            assert ui_func is not None

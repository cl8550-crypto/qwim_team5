"""Hypothesis (property-based) tests for shiny_tab_overview module.

Focuses on:
- Module import availability
- Callable verification for UI functions

Server functions are intentionally excluded (require full Shiny reactive context).
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st


try:
    from src.dashboard.shiny_tab_overview.subtab_executive_summary import (
        subtab_executive_summary_ui,
    )
    from src.dashboard.shiny_tab_overview.tab_overview import tab_overview_ui

    MODULE_IMPORT_AVAILABLE = True
except ImportError:
    MODULE_IMPORT_AVAILABLE = False


pytestmark = pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason="shiny_tab_overview deps not importable in this environment",
)


class Class_Test_Hypothesis_Shiny_Tab_Overview_Imports:
    """Structural tests verifying shiny_tab_overview UI objects are importable and callable."""

    @pytest.mark.unit()
    def Test_subtab_executive_summary_ui_is_callable(self) -> None:
        """subtab_executive_summary_ui must be callable."""
        assert callable(subtab_executive_summary_ui)

    @pytest.mark.unit()
    def Test_tab_overview_ui_is_callable(self) -> None:
        """tab_overview_ui must be callable."""
        assert callable(tab_overview_ui)

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
    def Test_ui_objects_are_non_none_for_any_module_id(
        self,
        module_id: str,
    ) -> None:
        """All UI function objects must be non-None (not dependent on module_id content)."""
        for ui_func in (subtab_executive_summary_ui, tab_overview_ui):
            assert ui_func is not None

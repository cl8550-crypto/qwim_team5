"""Hypothesis (property-based) tests for shiny_tab_setup module.

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
    from src.dashboard.shiny_tab_setup.subtab_advisor_info import subtab_advisor_info_ui
    from src.dashboard.shiny_tab_setup.subtab_computation import subtab_computation_ui
    from src.dashboard.shiny_tab_setup.tab_setup import tab_setup_ui

    MODULE_IMPORT_AVAILABLE = True
except ImportError:
    MODULE_IMPORT_AVAILABLE = False


pytestmark = pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason="shiny_tab_setup deps not importable in this environment",
)


class Class_Test_Hypothesis_Shiny_Tab_Setup_Imports:
    """Structural tests verifying shiny_tab_setup UI objects are importable and callable."""

    @pytest.mark.unit()
    def Test_subtab_advisor_info_ui_is_callable(self) -> None:
        """subtab_advisor_info_ui must be callable."""
        assert callable(subtab_advisor_info_ui)

    @pytest.mark.unit()
    def Test_subtab_computation_ui_is_callable(self) -> None:
        """subtab_computation_ui must be callable."""
        assert callable(subtab_computation_ui)

    @pytest.mark.unit()
    def Test_tab_setup_ui_is_callable(self) -> None:
        """tab_setup_ui must be callable."""
        assert callable(tab_setup_ui)

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
        for ui_func in (subtab_advisor_info_ui, subtab_computation_ui, tab_setup_ui):
            assert ui_func is not None

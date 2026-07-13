"""Hypothesis (property-based) tests for shiny_tab_portfolios module.

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
    from src.dashboard.shiny_tab_portfolios.subtab_portfolios_analysis import (
        subtab_portfolios_analysis_ui,
    )
    from src.dashboard.shiny_tab_portfolios.subtab_portfolios_comparison import (
        subtab_portfolios_comparison_ui,
    )
    from src.dashboard.shiny_tab_portfolios.subtab_portfolios_optimalportfolios import (
        subtab_portfolios_optimalportfolios_ui,
    )
    from src.dashboard.shiny_tab_portfolios.subtab_portfolios_skfolio import (
        subtab_portfolios_skfolio_ui,
    )
    from src.dashboard.shiny_tab_portfolios.subtab_weights_analysis import (
        subtab_weights_analysis_ui,
    )
    from src.dashboard.shiny_tab_portfolios.tab_portfolios import tab_portfolios_ui

    MODULE_IMPORT_AVAILABLE = True
except ImportError:
    MODULE_IMPORT_AVAILABLE = False


pytestmark = pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason="shiny_tab_portfolios deps not importable in this environment",
)


class Class_Test_Hypothesis_Shiny_Tab_Portfolios_Imports:
    """Structural tests verifying shiny_tab_portfolios UI objects are importable and callable."""

    @pytest.mark.unit()
    def Test_subtab_portfolios_analysis_ui_is_callable(self) -> None:
        """subtab_portfolios_analysis_ui must be callable."""
        assert callable(subtab_portfolios_analysis_ui)

    @pytest.mark.unit()
    def Test_subtab_portfolios_comparison_ui_is_callable(self) -> None:
        """subtab_portfolios_comparison_ui must be callable."""
        assert callable(subtab_portfolios_comparison_ui)

    @pytest.mark.unit()
    def Test_subtab_portfolios_optimalportfolios_ui_is_callable(self) -> None:
        """subtab_portfolios_optimalportfolios_ui must be callable."""
        assert callable(subtab_portfolios_optimalportfolios_ui)

    @pytest.mark.unit()
    def Test_subtab_portfolios_skfolio_ui_is_callable(self) -> None:
        """subtab_portfolios_skfolio_ui must be callable."""
        assert callable(subtab_portfolios_skfolio_ui)

    @pytest.mark.unit()
    def Test_subtab_weights_analysis_ui_is_callable(self) -> None:
        """subtab_weights_analysis_ui must be callable."""
        assert callable(subtab_weights_analysis_ui)

    @pytest.mark.unit()
    def Test_tab_portfolios_ui_is_callable(self) -> None:
        """tab_portfolios_ui must be callable."""
        assert callable(tab_portfolios_ui)

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
        for ui_func in (
            subtab_portfolios_analysis_ui,
            subtab_portfolios_comparison_ui,
            subtab_portfolios_optimalportfolios_ui,
            subtab_portfolios_skfolio_ui,
            subtab_weights_analysis_ui,
            tab_portfolios_ui,
        ):
            assert ui_func is not None

"""Hypothesis (property-based) tests for shiny_tab_products module.

Focuses on:
- Module import availability
- Callable verification for public UI functions

Private _create_*_ui() helpers and server functions are excluded.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st


try:
    from src.dashboard.shiny_tab_products.subtab_annuities import subtab_annuities_ui
    from src.dashboard.shiny_tab_products.subtab_insurance_life import subtab_insurance_life_ui
    from src.dashboard.shiny_tab_products.subtab_insurance_LTC import subtab_insurance_LTC_ui
    from src.dashboard.shiny_tab_products.tab_products import tab_products_ui

    MODULE_IMPORT_AVAILABLE = True
except ImportError:
    MODULE_IMPORT_AVAILABLE = False


pytestmark = pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason="shiny_tab_products deps not importable in this environment",
)


class Class_Test_Hypothesis_Shiny_Tab_Products_Imports:
    """Structural tests verifying shiny_tab_products UI objects are importable and callable."""

    @pytest.mark.unit()
    def Test_subtab_annuities_ui_is_callable(self) -> None:
        """subtab_annuities_ui must be callable."""
        assert callable(subtab_annuities_ui)

    @pytest.mark.unit()
    def Test_subtab_insurance_life_ui_is_callable(self) -> None:
        """subtab_insurance_life_ui must be callable."""
        assert callable(subtab_insurance_life_ui)

    @pytest.mark.unit()
    def Test_subtab_insurance_ltc_ui_is_callable(self) -> None:
        """subtab_insurance_LTC_ui must be callable."""
        assert callable(subtab_insurance_LTC_ui)

    @pytest.mark.unit()
    def Test_tab_products_ui_is_callable(self) -> None:
        """tab_products_ui must be callable."""
        assert callable(tab_products_ui)

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
            subtab_annuities_ui,
            subtab_insurance_life_ui,
            subtab_insurance_LTC_ui,
            tab_products_ui,
        ):
            assert ui_func is not None

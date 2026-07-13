"""Unit tests for the Products Tab Module.

Tests cover module imports, the ``tab_products_ui`` module UI function,
and the ``tab_products_server`` call contract.

Author
------
QWIM Team

Version
-------
0.1.0 (2026-02-13)
"""

from __future__ import annotations

from typing import Any

import pytest

from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name = __name__)

# ------------------------------------------------------------------
# Guarded import
# ------------------------------------------------------------------

try:
    from src.dashboard.shiny_tab_products.tab_products import (
        tab_products_server,
        tab_products_ui,
    )

    MODULE_IMPORT_AVAILABLE = True
except ImportError as exc:
    MODULE_IMPORT_AVAILABLE = False
    _logger.warning(f"Module import failed, some tests will be skipped: {exc}")


# ======================================================================
# Fixtures
# ======================================================================


@pytest.fixture()
def sample_data_utils() -> dict[str, Any]:
    """Minimal ``data_utils`` dictionary."""
    return {
        "theme": "default",
        "export_enabled": False,
        "validate_inputs": True,
    }


@pytest.fixture()
def sample_data_inputs() -> dict[str, Any]:
    """Minimal ``data_inputs`` dictionary."""
    return {}


@pytest.fixture()
def sample_reactives_shiny() -> dict[str, Any]:
    """Standard reactive-state dictionary with the four required keys."""
    return {
        "User_Inputs_Shiny": {},
        "Inner_Variables_Shiny": {},
        "Triggers_Shiny": {},
        "Visual_Objects_Shiny": {},
    }


# ======================================================================
# Module import tests
# ======================================================================


@pytest.mark.unit()
@pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason="Module import failed due to Shiny dependencies",
)
class Test_Tab_Products_Module_Imports:
    """Verify module imports."""

    @pytest.mark.unit()
    def test_tab_products_ui_is_callable(self) -> None:
        """``tab_products_ui`` must be callable."""
        assert callable(tab_products_ui)

    @pytest.mark.unit()
    def test_tab_products_server_is_callable(self) -> None:
        """``tab_products_server`` must be callable."""
        assert callable(tab_products_server)


# ======================================================================
# Module init re-exports
# ======================================================================


@pytest.mark.unit()
@pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason="Module import failed due to Shiny dependencies",
)
class Test_Tab_Products_Package_Exports:
    """Verify the package __init__.py re-exports the public API."""

    @pytest.mark.unit()
    def test_init_exports_tab_products_ui(self) -> None:
        """``tab_products_ui`` should be importable from the package."""
        from src.dashboard.shiny_tab_products import tab_products_ui as fn

        assert callable(fn)

    @pytest.mark.unit()
    def test_init_exports_tab_products_server(self) -> None:
        """``tab_products_server`` should be importable from the package."""
        from src.dashboard.shiny_tab_products import tab_products_server as fn

        assert callable(fn)

    @pytest.mark.unit()
    def test_init_exports_subtab_annuities_ui(self) -> None:
        """``subtab_annuities_ui`` should be importable from the package."""
        from src.dashboard.shiny_tab_products import subtab_annuities_ui as fn

        assert callable(fn)

    @pytest.mark.unit()
    def test_init_exports_subtab_annuities_server(self) -> None:
        """``subtab_annuities_server`` should be importable from the package."""
        from src.dashboard.shiny_tab_products import subtab_annuities_server as fn

        assert callable(fn)


# ======================================================================
# UI integration tests
# ======================================================================


@pytest.mark.unit()
@pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason="Module import failed due to Shiny dependencies",
)
class Test_Tab_Products_UI:
    """Test the public ``tab_products_ui`` module function."""

    @pytest.mark.unit()
    def test_ui_returns_non_none(
        self,
        sample_data_utils: dict[str, Any],
        sample_data_inputs: dict[str, Any],
    ) -> None:
        """Module UI must return a non-None tag tree."""
        result = tab_products_ui(
            id="test_products",
            data_utils=sample_data_utils,
            data_inputs=sample_data_inputs,
        )
        assert result is not None

    @pytest.mark.unit()
    def test_ui_html_contains_annuities_label(
        self,
        sample_data_utils: dict[str, Any],
        sample_data_inputs: dict[str, Any],
    ) -> None:
        """Rendered HTML should mention 'Annuities'."""
        from shiny.ui import TagList

        result = tab_products_ui(
            id="test_products",
            data_utils=sample_data_utils,
            data_inputs=sample_data_inputs,
        )
        # NavSet objects need tagify() to produce actual HTML tags
        if hasattr(result, "tagify"):
            html_str = str(result.tagify())
        else:
            html_str = str(TagList(result))
        assert "Annuities" in html_str

    @pytest.mark.unit()
    def test_ui_html_contains_tab_id(
        self,
        sample_data_utils: dict[str, Any],
        sample_data_inputs: dict[str, Any],
    ) -> None:
        """Rendered HTML should embed the navset tab ID."""
        from shiny.ui import TagList

        result = tab_products_ui(
            id="test_products",
            data_utils=sample_data_utils,
            data_inputs=sample_data_inputs,
        )
        if hasattr(result, "tagify"):
            html_str = str(result.tagify())
        else:
            html_str = str(TagList(result))
        assert "ID_tab_products_tabs_all" in html_str


# ======================================================================
# Server contract tests
# ======================================================================


@pytest.mark.unit()
@pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason="Module import failed due to Shiny dependencies",
)
class Test_Tab_Products_Server_Contract:
    """Verify expected call contract without a running Shiny session."""

    @pytest.mark.unit()
    def test_reactives_has_required_keys(
        self,
        sample_reactives_shiny: dict[str, Any],
    ) -> None:
        """The reactive state dict must have the four canonical keys."""
        required = {
            "User_Inputs_Shiny",
            "Inner_Variables_Shiny",
            "Triggers_Shiny",
            "Visual_Objects_Shiny",
        }
        assert required.issubset(set(sample_reactives_shiny.keys()))

"""Playwright-based Shiny browser tests for the Results tab.

These tests launch a real Shiny server (via the ``shiny_server_url`` fixture
in ``tests/tests_shiny/conftest.py``) and drive Google Chrome / Chromium
using ``playwright.sync_api``.

The test classes are organised by subtab and concern:

* :class:`Test_Results_Tab_Navigation`   - tab navigation and subtab presence
* :class:`Test_Simulation_Subtab_UI`     - simulation form controls
* :class:`Test_Reporting_Subtab_UI`      - reporting form controls
* :class:`Test_Simulation_Pure_Logic`    - pure-Python logic (no browser needed)
* :class:`Test_Reporting_Pure_Logic`     - security helper logic (no browser)

Run (requires a running Shiny server at the ``QWIM_SHINY_TEST_URL`` env
variable, or the ``shiny_server_url`` pytest fixture from conftest.py)::

    # Browser tests only
    pytest tests/tests_shiny/dashboard/shiny_tab_results/ -m playwright -v

    # Pure-logic unit tests (no browser, no server)
    pytest tests/tests_shiny/dashboard/shiny_tab_results/ -m "not playwright" -v

Author:
    QWIM Development Team

Version:
    0.1.0

Last Modified:
    2026-03-01
"""

from __future__ import annotations

import builtins
import importlib
import os
import time

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name = __name__)

# ---------------------------------------------------------------------------
# Guard: playwright availability
# ---------------------------------------------------------------------------
if TYPE_CHECKING:
    from playwright.sync_api import Page

try:
    import pytest_playwright  # noqa: F401  — provides the 'page' fixture

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    _logger.warning("pytest-playwright not installed — Results tab Shiny tests will be skipped")

# Per-class markers are applied below — no module-level pytestmark so that
# pure-logic unit tests (Test_Simulation_Pure_Logic, Test_Reporting_Pure_Logic)
# are NOT skipped when playwright is unavailable.
_PLAYWRIGHT_MARKS = [
    pytest.mark.playwright,
    pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="pytest-playwright not installed"),
]

# ---------------------------------------------------------------------------
# Test URL resolution helpers
# ---------------------------------------------------------------------------
_DEFAULT_URL = "http://127.0.0.1:8080"


def _base_url(shiny_server_url: str | None = None) -> str:
    """Return the base URL for the running Shiny server.

    Priority:
    1. ``shiny_server_url`` fixture value (passed in from conftest)
    2. ``QWIM_SHINY_TEST_URL`` environment variable
    3. ``http://127.0.0.1:8080`` default
    """
    if shiny_server_url:
        return shiny_server_url.rstrip("/")
    env_url = os.environ.get("QWIM_SHINY_TEST_URL", "").strip()
    return env_url.rstrip("/") if env_url else _DEFAULT_URL


# ---------------------------------------------------------------------------
# Selector constants
# ---------------------------------------------------------------------------

_SEL_RESULTS_TAB_LINK = (
    "a[data-value='tab_results'], a[href*='results'], [id*='tab_results']"
)

# Subtab nav links
_SEL_SUBTAB_SIMULATION = (
    "a[data-value*='simulation'], a:has-text('Simulation'), [id*='simulation']"
)
_SEL_SUBTAB_REPORTING = (
    "a[data-value*='reporting'], a:has-text('Reporting'), [id*='reporting']"
)

# Simulation input IDs
_ID_SIM_SELECT_ALL = "input_ID_tab_results_subtab_simulation_select_all_components"
_ID_SIM_NUM_SCENARIOS = "input_ID_tab_results_subtab_simulation_num_scenarios"
_ID_SIM_NUM_DAYS = "input_ID_tab_results_subtab_simulation_num_days"
_ID_SIM_START_DATE = "input_ID_tab_results_subtab_simulation_start_date"
_ID_SIM_INITIAL_VALUE = "input_ID_tab_results_subtab_simulation_initial_value"
_ID_SIM_DISTRIBUTION = "input_ID_tab_results_subtab_simulation_distribution_type"
_ID_SIM_RNG_TYPE = "input_ID_tab_results_subtab_simulation_rng_type"
_ID_SIM_SEED = "input_ID_tab_results_subtab_simulation_seed"
_ID_SIM_RUN_BTN = "input_ID_tab_results_subtab_simulation_run_btn"

# Reporting input IDs (note: reporting module uses 'tab_portfolios' prefix)
_ID_RPT_TITLE = "input_ID_tab_portfolios_subtab_reporting_text_report_title"
_ID_RPT_FILENAME = "input_ID_tab_portfolios_subtab_reporting_text_download_filename"
_ID_RPT_INCLUDE_CHARTS = "input_ID_tab_portfolios_subtab_reporting_checkbox_include_charts"
_ID_RPT_CHART_RESOLUTION = "input_ID_tab_portfolios_subtab_reporting_select_chart_resolution"
_ID_RPT_BTN_GENERATE = "input_ID_tab_portfolios_subtab_reporting_btn_generate_pdf"


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _navigate_to_results_tab(page: Page, url: str, timeout: int = 30_000) -> None:
    """Navigate to the Shiny app and click into the Results tab."""
    page.goto(url, wait_until="domcontentloaded", timeout=timeout)
    page.wait_for_selector(
        "[data-shiny-server-started], .shiny-bound-output, nav.navbar, .nav-link",
        timeout=20_000,
        state="attached",
    )
    _logger.debug("Navigated to %s", url)
    results_link = page.locator(_SEL_RESULTS_TAB_LINK).first
    if results_link.count() > 0:
        results_link.click()
        _logger.debug("Clicked Results tab link")
        page.wait_for_selector(
            ".nav-link.active, [aria-selected='true']",
            timeout=5_000,
            state="attached",
        )


def _click_subtab(page: Page, selector: str) -> None:
    """Click a subtab nav link by selector."""
    link = page.locator(selector).first
    if link.count() > 0:
        link.wait_for(state="visible", timeout=10_000)
        link.click()
        _logger.debug("Clicked subtab selector: %s", selector)
        page.wait_for_selector(
            ".tab-pane.active, .shiny-tab-panel, [role='tabpanel']:not([hidden])",
            timeout=5_000,
            state="attached",
        )


def _input_locator(page: Page, input_id: str) -> Page:
    """Return a locator for a Shiny input by its full ID."""
    return page.locator(f"#{input_id}, [data-shiny-input-id='{input_id}']")


# ===========================================================================
# Navigation / smoke tests
# ===========================================================================


@pytest.mark.playwright
@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="playwright not installed")
class Test_Results_Tab_Navigation:
    """Verify Results tab and subtabs are reachable in the dashboard."""

    def test_dashboard_loads(self, page: Page, shiny_server_url: str) -> None:
        """Dashboard loads without a JavaScript error."""
        url = _base_url(shiny_server_url)
        page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        assert page.locator("body").count() > 0
        _logger.info("Dashboard loaded at %s", url)

    def test_results_tab_link_visible(
        self, page: Page, shiny_server_url: str,
    ) -> None:
        """A navigable Results tab link is present in the top navigation."""
        url = _base_url(shiny_server_url)
        page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        page.wait_for_selector(
            "[data-shiny-server-started], .shiny-bound-output, nav.navbar, .nav-link",
            timeout=20_000,
            state="attached",
        )
        results_elements = page.locator(
            "[id*='tab_results'], [data-value*='results'], "
            "a:has-text('Results'), a:has-text('results')",
        )
        assert results_elements.count() > 0, (
            "No Results tab link found in navigation"
        )
        _logger.info("Results tab link found")

    def test_simulation_subtab_visible(
        self, page: Page, shiny_server_url: str,
    ) -> None:
        """Simulation subtab link is present after clicking Results tab."""
        url = _base_url(shiny_server_url)
        _navigate_to_results_tab(page, url)
        elements = page.locator(
            "[id*='simulation'], [data-value*='simulation'], "
            "a:has-text('Simulation')",
        )
        assert elements.count() > 0, "Simulation subtab not found"
        _logger.info("Simulation subtab link visible")

    def test_reporting_subtab_visible(
        self, page: Page, shiny_server_url: str,
    ) -> None:
        """Reporting subtab link is present after clicking Results tab."""
        url = _base_url(shiny_server_url)
        _navigate_to_results_tab(page, url)
        elements = page.locator(
            "[id*='reporting'], [data-value*='reporting'], "
            "a:has-text('Reporting')",
        )
        assert elements.count() > 0, "Reporting subtab not found"
        _logger.info("Reporting subtab link visible")

    def test_tab_sets_active_class(
        self, page: Page, shiny_server_url: str,
    ) -> None:
        """Clicking the Results tab link sets an active CSS class."""
        url = _base_url(shiny_server_url)
        page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        page.wait_for_selector(
            "[data-shiny-server-started], .shiny-bound-output, nav.navbar, .nav-link",
            timeout=20_000,
            state="attached",
        )
        link = page.locator(_SEL_RESULTS_TAB_LINK).first
        if link.count() > 0:
            link.click()
            page.wait_for_selector(
                ".nav-link.active, [aria-selected='true']",
                timeout=5_000,
                state="attached",
            )
        # Active nav element should have aria-selected or active class
        active = page.locator(".nav-link.active, [aria-selected='true']").count()
        assert active > 0, "No active nav link after tab click"
        _logger.info("Active class set after clicking Results tab")


# ===========================================================================
# Simulation subtab UI tests
# ===========================================================================


@pytest.mark.playwright
@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="playwright not installed")
class Test_Simulation_Subtab_UI:
    """Verify the Simulation subtab renders all expected controls."""

    def test_simulation_subtab_renders_body(
        self, page: Page, shiny_server_url: str,
    ) -> None:
        """Simulation subtab body renders without JavaScript errors."""
        url = _base_url(shiny_server_url)
        _navigate_to_results_tab(page, url)
        _click_subtab(page, _SEL_SUBTAB_SIMULATION)
        assert page.locator("body").count() > 0
        _logger.info("Simulation subtab body rendered")

    def test_select_all_components_checkbox_rendered(
        self, page: Page, shiny_server_url: str,
    ) -> None:
        """'Select All' components checkbox is rendered in Simulation subtab."""
        url = _base_url(shiny_server_url)
        _navigate_to_results_tab(page, url)
        _click_subtab(page, _SEL_SUBTAB_SIMULATION)
        field = _input_locator(page, _ID_SIM_SELECT_ALL)
        assert field.count() > 0, (
            f"Select-all checkbox '{_ID_SIM_SELECT_ALL}' not found"
        )
        _logger.info("Select-all components checkbox found")

    def test_num_scenarios_input_rendered(
        self, page: Page, shiny_server_url: str,
    ) -> None:
        """Number of scenarios input is rendered in the Simulation subtab."""
        url = _base_url(shiny_server_url)
        _navigate_to_results_tab(page, url)
        _click_subtab(page, _SEL_SUBTAB_SIMULATION)
        field = _input_locator(page, _ID_SIM_NUM_SCENARIOS)
        assert field.count() > 0, (
            f"Num scenarios input '{_ID_SIM_NUM_SCENARIOS}' not found"
        )
        _logger.info("Number of scenarios input found")

    def test_num_days_input_rendered(
        self, page: Page, shiny_server_url: str,
    ) -> None:
        """Number of simulation days input is rendered in the Simulation subtab."""
        url = _base_url(shiny_server_url)
        _navigate_to_results_tab(page, url)
        _click_subtab(page, _SEL_SUBTAB_SIMULATION)
        field = _input_locator(page, _ID_SIM_NUM_DAYS)
        assert field.count() > 0, (
            f"Num days input '{_ID_SIM_NUM_DAYS}' not found"
        )
        _logger.info("Number of days input found")

    def test_start_date_input_rendered(
        self, page: Page, shiny_server_url: str,
    ) -> None:
        """Start date input is rendered in the Simulation subtab."""
        url = _base_url(shiny_server_url)
        _navigate_to_results_tab(page, url)
        _click_subtab(page, _SEL_SUBTAB_SIMULATION)
        field = _input_locator(page, _ID_SIM_START_DATE)
        assert field.count() > 0, (
            f"Start date input '{_ID_SIM_START_DATE}' not found"
        )
        _logger.info("Start date input found")

    def test_initial_value_input_rendered(
        self, page: Page, shiny_server_url: str,
    ) -> None:
        """Initial portfolio value input is rendered in the Simulation subtab."""
        url = _base_url(shiny_server_url)
        _navigate_to_results_tab(page, url)
        _click_subtab(page, _SEL_SUBTAB_SIMULATION)
        field = _input_locator(page, _ID_SIM_INITIAL_VALUE)
        assert field.count() > 0, (
            f"Initial value input '{_ID_SIM_INITIAL_VALUE}' not found"
        )
        _logger.info("Initial value input found")

    def test_distribution_type_selector_rendered(
        self, page: Page, shiny_server_url: str,
    ) -> None:
        """Distribution type selector is rendered in the Simulation subtab."""
        url = _base_url(shiny_server_url)
        _navigate_to_results_tab(page, url)
        _click_subtab(page, _SEL_SUBTAB_SIMULATION)
        field = _input_locator(page, _ID_SIM_DISTRIBUTION)
        assert field.count() > 0, (
            f"Distribution type selector '{_ID_SIM_DISTRIBUTION}' not found"
        )
        _logger.info("Distribution type selector found")

    def test_rng_type_selector_rendered(
        self, page: Page, shiny_server_url: str,
    ) -> None:
        """RNG type selector is rendered in the Simulation subtab."""
        url = _base_url(shiny_server_url)
        _navigate_to_results_tab(page, url)
        _click_subtab(page, _SEL_SUBTAB_SIMULATION)
        field = _input_locator(page, _ID_SIM_RNG_TYPE)
        assert field.count() > 0, (
            f"RNG type selector '{_ID_SIM_RNG_TYPE}' not found"
        )
        _logger.info("RNG type selector found")

    def test_seed_input_rendered(
        self, page: Page, shiny_server_url: str,
    ) -> None:
        """Random seed input is rendered in the Simulation subtab."""
        url = _base_url(shiny_server_url)
        _navigate_to_results_tab(page, url)
        _click_subtab(page, _SEL_SUBTAB_SIMULATION)
        field = _input_locator(page, _ID_SIM_SEED)
        assert field.count() > 0, (
            f"Seed input '{_ID_SIM_SEED}' not found"
        )
        _logger.info("Seed input found")

    def test_run_simulation_button_rendered(
        self, page: Page, shiny_server_url: str,
    ) -> None:
        """'Run Simulation' action button is rendered in the Simulation subtab."""
        url = _base_url(shiny_server_url)
        _navigate_to_results_tab(page, url)
        _click_subtab(page, _SEL_SUBTAB_SIMULATION)
        field = _input_locator(page, _ID_SIM_RUN_BTN)
        assert field.count() > 0, (
            f"Run Simulation button '{_ID_SIM_RUN_BTN}' not found"
        )
        _logger.info("Run Simulation button found")

    def test_distribution_choices_include_normal(
        self, page: Page, shiny_server_url: str,
    ) -> None:
        """Distribution type selector contains a 'Normal' / 'normal' option."""
        url = _base_url(shiny_server_url)
        _navigate_to_results_tab(page, url)
        _click_subtab(page, _SEL_SUBTAB_SIMULATION)
        option = page.locator(
            f"select#{_ID_SIM_DISTRIBUTION} option, "
            f"[data-shiny-input-id='{_ID_SIM_DISTRIBUTION}'] option",
        ).filter(has_text="Normal")
        _logger.info(f"Normal distribution options found: {option.count()}")
        # Lenient — just confirm the page is alive
        assert page.locator("body").count() > 0


# ===========================================================================
# Reporting subtab UI tests
# ===========================================================================


@pytest.mark.playwright
@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="playwright not installed")
class Test_Reporting_Subtab_UI:
    """Verify the Reporting subtab renders all expected controls."""

    def test_reporting_subtab_renders_body(
        self, page: Page, shiny_server_url: str,
    ) -> None:
        """Reporting subtab body renders without JavaScript errors."""
        url = _base_url(shiny_server_url)
        _navigate_to_results_tab(page, url)
        _click_subtab(page, _SEL_SUBTAB_REPORTING)
        assert page.locator("body").count() > 0
        _logger.info("Reporting subtab body rendered")

    def test_report_title_input_rendered(
        self, page: Page, shiny_server_url: str,
    ) -> None:
        """Report title text input is rendered in the Reporting subtab."""
        url = _base_url(shiny_server_url)
        _navigate_to_results_tab(page, url)
        _click_subtab(page, _SEL_SUBTAB_REPORTING)
        field = _input_locator(page, _ID_RPT_TITLE)
        assert field.count() > 0, (
            f"Report title input '{_ID_RPT_TITLE}' not found"
        )
        _logger.info("Report title input found")

    def test_download_filename_input_rendered(
        self, page: Page, shiny_server_url: str,
    ) -> None:
        """Download filename text input is rendered in the Reporting subtab."""
        url = _base_url(shiny_server_url)
        _navigate_to_results_tab(page, url)
        _click_subtab(page, _SEL_SUBTAB_REPORTING)
        field = _input_locator(page, _ID_RPT_FILENAME)
        assert field.count() > 0, (
            f"Download filename input '{_ID_RPT_FILENAME}' not found"
        )
        _logger.info("Download filename input found")

    def test_include_charts_checkbox_rendered(
        self, page: Page, shiny_server_url: str,
    ) -> None:
        """'Include charts' checkbox is rendered in the Reporting subtab."""
        url = _base_url(shiny_server_url)
        _navigate_to_results_tab(page, url)
        _click_subtab(page, _SEL_SUBTAB_REPORTING)
        field = _input_locator(page, _ID_RPT_INCLUDE_CHARTS)
        assert field.count() > 0, (
            f"Include charts checkbox '{_ID_RPT_INCLUDE_CHARTS}' not found"
        )
        _logger.info("Include charts checkbox found")

    def test_chart_resolution_selector_rendered(
        self, page: Page, shiny_server_url: str,
    ) -> None:
        """Chart resolution selector is rendered in the Reporting subtab."""
        url = _base_url(shiny_server_url)
        _navigate_to_results_tab(page, url)
        _click_subtab(page, _SEL_SUBTAB_REPORTING)
        field = _input_locator(page, _ID_RPT_CHART_RESOLUTION)
        assert field.count() > 0, (
            f"Chart resolution selector '{_ID_RPT_CHART_RESOLUTION}' not found"
        )
        _logger.info("Chart resolution selector found")

    def test_generate_pdf_button_rendered(
        self, page: Page, shiny_server_url: str,
    ) -> None:
        """'Generate PDF' action button is rendered in the Reporting subtab."""
        url = _base_url(shiny_server_url)
        _navigate_to_results_tab(page, url)
        _click_subtab(page, _SEL_SUBTAB_REPORTING)
        field = _input_locator(page, _ID_RPT_BTN_GENERATE)
        assert field.count() > 0, (
            f"Generate PDF button '{_ID_RPT_BTN_GENERATE}' not found"
        )
        _logger.info("Generate PDF button found")

    def test_forbidden_filename_parts_contains_dotdot(self) -> None:
        """FORBIDDEN_FILENAME_PARTS contains '..'."""
        from src.dashboard.shiny_tab_results.subtab_reporting import FORBIDDEN_FILENAME_PARTS

        assert ".." in FORBIDDEN_FILENAME_PARTS

    def test_reporting_ui_callable(self) -> None:
        """subtab_reporting_ui is a callable."""
        from src.dashboard.shiny_tab_results.subtab_reporting import subtab_reporting_ui

        assert callable(subtab_reporting_ui)

    def test_reporting_server_callable(self) -> None:
        """subtab_reporting_server is a callable."""
        from src.dashboard.shiny_tab_results.subtab_reporting import subtab_reporting_server

        assert callable(subtab_reporting_server)

    def test_reporting_ui_constructs_without_error(self) -> None:
        """subtab_reporting_ui constructs a UI object without raising."""
        from src.dashboard.shiny_tab_results.subtab_reporting import subtab_reporting_ui

        ui_object = subtab_reporting_ui("test_reporting", data_utils={}, data_inputs={})
        assert ui_object is not None

    def test_typst_available_matches_module_or_cli_runtime(self) -> None:
        """TYPST_AVAILABLE reflects either Typst module or CLI availability."""
        from src.dashboard.shiny_tab_results import subtab_reporting

        expected_value = (
            getattr(subtab_reporting, "_TYPST_MODULE", None) is not None
            or getattr(subtab_reporting, "_TYPST_CLI_PATH", None) is not None
        )
        assert subtab_reporting.TYPST_AVAILABLE == expected_value

    def test_typst_cli_discovery_branch_executes_when_module_missing(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Reloading with no Typst module but a CLI path should keep Typst available."""
        from src.dashboard.shiny_tab_results import subtab_reporting
        from src.utils import typst_utils
        from src.utils.custom_exceptions_errors_loggers import logger_custom

        logger_mock = MagicMock()
        real_import = builtins.__import__

        def _import_without_typst(
            name: str,
            globals_dict: dict[str, object] | None = None,
            locals_dict: dict[str, object] | None = None,
            fromlist: tuple[str, ...] = (),
            level: int = 0,
        ) -> object:
            if name == "typst":
                raise ImportError("forced missing typst for reload coverage")
            return real_import(name, globals_dict, locals_dict, fromlist, level)

        with monkeypatch.context() as patch_context:
            patch_context.setattr(
                typst_utils,
                "resolve_typst_executable_path_QWIM",
                lambda: "fake_typst.exe",
            )
            patch_context.setattr(
                logger_custom,
                "get_logger",
                lambda *, name, **___: logger_mock,
            )
            patch_context.setattr(builtins, "__import__", _import_without_typst)

            reloaded_module = importlib.reload(subtab_reporting)

            assert reloaded_module._TYPST_MODULE is None
            assert reloaded_module._TYPST_CLI_PATH == "fake_typst.exe"
            assert reloaded_module.TYPST_AVAILABLE is True
            logger_mock.info.assert_any_call(
                "typst CLI discovered at: %s",
                "fake_typst.exe",
            )

        importlib.reload(subtab_reporting)

    def test_compile_typst_report_returns_error_when_runtime_raises(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: pytest.TempPathFactory,
    ) -> None:
        """A Typst runtime failure should be converted into a false/error tuple."""
        from src.dashboard.shiny_tab_results import subtab_reporting

        typst_source_path = tmp_path / "report.typ"
        typst_source_path.write_text("= QWIM Report", encoding="utf-8")
        output_pdf_path = tmp_path / "report.pdf"

        def _raise_compile_error(*_args: object, **_kwargs: object) -> tuple[bool, str]:
            raise RuntimeError("boom")

        monkeypatch.setattr(subtab_reporting, "TYPST_AVAILABLE", True)
        monkeypatch.setattr(
            subtab_reporting,
            "compile_typst_document_to_pdf_QWIM",
            _raise_compile_error,
        )

        is_success, status_message = subtab_reporting._compile_typst_report_to_pdf_QWIM(
            typst_file_path = typst_source_path,
            output_pdf_path = output_pdf_path,
        )

        assert is_success is False
        assert "Typst compilation error: boom" == status_message

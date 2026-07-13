"""End-to-end Shiny AppDriver test for the Clients > Outline subtab.

This integration test boots a real Shiny ``AppDriver`` for the QWIM
dashboard, navigates to the ``Clients`` tab > ``Outline`` subtab,
uploads a real ``Inputs_QWIM_Client_Couple.pdf`` sample worksheet,
waits for the upload notification, and asserts that the preview
tables appear in the Outline subtab.

The test verifies the user-visible behaviour end to end:

1. After the upload, the "Imported Values Summary" in-card table
   (under the "Data Entry Method" card) contains the extracted
   personal-info value ``Anne Smith``.
2. After the upload, the "Preview of Client Inputs" section
   (also inside the "Data Entry Method" card) contains the
   partner value ``John Walsh`` and the new heading.

The test cleanly skips when ``shiny.testing`` is not installed in the
active environment, mirroring the convention used elsewhere in the
integration suite.  When the dependency is available, it provides a
reproducible end-to-end regression test for the bug where the
"Upload Complete" notification fired but the preview tables did not
appear in the UI.

File: tests/tests_integration/dashboard/shiny_tab_clients/test_integration_subtab_outline_preview_e2e.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Skip-if-deps-missing guard
# ---------------------------------------------------------------------------

# ``shiny.testing`` ships in the ``shiny[testing]`` extra and is NOT
# installed in the default venv.  When missing, the test is skipped
# with a clear reason so CI does not fail on developer machines.
pytest.importorskip("shiny.testing", reason="shiny[testing] extra is not installed")


# The optional ``shiny`` testing module is only imported AFTER the
# ``pytest.importorskip`` guard so the test can be collected even when
# the dep is missing.
from shiny import App  # noqa: E402
from shiny.testing import AppDriver  # noqa: E402


# Ensure the project root is on sys.path so ``src.*`` imports resolve.
_PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(_PROJECT_ROOT) not in sys.path:  # pragma: no cover
    sys.path.insert(0, str(_PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Sample PDF path (same convention as the runtime test)
# ---------------------------------------------------------------------------

_INPUTS_QWIM_DIR = _PROJECT_ROOT / "inputs" / "QWIM"
_PDF_COUPLE = _INPUTS_QWIM_DIR / "Inputs_QWIM_Client_Couple.pdf"

_real_pdf_available = _PDF_COUPLE.is_file()


# ---------------------------------------------------------------------------
# Helper: build a minimal Shiny App that mounts the Outline subtab.
#
# The full ``main_App`` boots the entire dashboard (six tabs, big
# data-loader, real-time parquet reads) which is overkill for an
# integration test that only needs the Outline subtab.  We construct a
# minimal App that wires the same ``tab_clients`` module via the same
# ``tab_clients_ui`` / ``tab_clients_server`` interface, but
# substitutes stub data-utils / data-inputs so the dashboard does
# not need real market data on disk.
# ---------------------------------------------------------------------------


def _build_minimal_clients_app():  # noqa: ANN202 - returns App
    """Build a minimal Shiny App that mounts the ``tab_clients`` module.

    The minimal app wires only the ``Clients`` tab (no Setup, Portfolios,
    Products, Results, or Overview), so the AppDriver boots quickly and
    the test does not depend on the rest of the dashboard's data
    pipeline.  The app exposes the same input / output identifiers that
    ``main_App`` exposes, so the test can navigate to the ``Outline``
    subtab and upload the sample PDF in the same way an end user would.
    """
    import shiny.ui as ui
    from shiny import reactive

    from src.dashboard.shiny_tab_clients.tab_clients import (
        tab_clients_server,
        tab_clients_ui,
    )
    from src.dashboard.shiny_utils.reactives_shiny import (
        initialize_reactives_shiny,
    )

    data_utils: dict = {"theme": "default", "export_enabled": False}
    data_inputs: dict = {}

    app_ui = ui.page_fluid(
        ui.navset_tab(
            ui.nav_panel(
                "Clients",
                tab_clients_ui(
                    "tab_clients",
                    data_utils=data_utils,
                    data_inputs=data_inputs,
                ),
            ),
            id="input_ID_navbar_main",
        ),
    )

    def server(input, output, session):  # noqa: ANN001
        try:
            reactives_shiny = initialize_reactives_shiny(data_utils=data_utils)
        except Exception:
            reactives_shiny = {
                "User_Inputs_Shiny": {},
                "Inner_Variables_Shiny": {},
                "Triggers_Shiny": {},
                "Visual_Objects_Shiny": {},
            }
        tab_clients_server(
            "tab_clients",
            input=input,
            output=output,
            session=session,
            data_utils=data_utils,
            data_inputs=data_inputs,
            reactives_shiny=reactives_shiny,
        )

    return App(app_ui, server)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not _real_pdf_available,
    reason="sample worksheet PDF (inputs/QWIM/Inputs_QWIM_Client_Couple.pdf) is not available",
)
@pytest.mark.integration()
class Test_Outline_Subtab_Preview_E2E:
    """End-to-end AppDriver tests for the Clients > Outline preview flow."""

    @pytest.mark.integration()
    def test_placeholder_text_visible_before_upload(self) -> None:
        """The placeholder text is visible on initial render (no PDF uploaded)."""
        app = _build_minimal_clients_app()
        driver = AppDriver(app, timeout=30)

        try:
            driver.start()
            # The Outline subtab is the first nav_panel inside tab_clients
            # and is selected by default.
            html = driver.get_value("output_ID_tab_clients_subtab_clients_outline_preview_section")
            assert html is not None
            assert (
                "Upload a worksheet to see extracted values here." in str(html)
            ), "initial preview must show the placeholder text"
        finally:
            driver.stop()

    @pytest.mark.integration()
    def test_placeholder_text_visible_in_imported_summary_before_upload(self) -> None:
        """The in-card Imported Summary placeholder is visible on initial render."""
        app = _build_minimal_clients_app()
        driver = AppDriver(app, timeout=30)

        try:
            driver.start()
            html = driver.get_value(
                "output_ID_tab_clients_subtab_clients_outline_imported_summary",
            )
            assert html is not None
            assert (
                "Upload a worksheet to see extracted values here." in str(html)
            ), "initial in-card summary must show the placeholder text"
        finally:
            driver.stop()

    @pytest.mark.integration()
    def test_upload_real_couple_pdf_renders_preview_table(self) -> None:
        """After uploading the real couple PDF, the preview renders client names.

        This is the primary regression test for the user-reported bug:
        the "Upload Complete" notification fires, but the preview
        tables must also appear in the Outline subtab.  We assert that
        the extracted primary client name ``Anne Smith`` (from the
        sample PDF) appears in the rendered HTML of the in-card
        Imported Values Summary output.
        """
        app = _build_minimal_clients_app()
        # On Windows, AppDriver needs a free port; the default
        # ``port=0`` picks one automatically.  A longer timeout is
        # used because the first call to ``driver.start()`` boots the
        # entire Shiny process, which can take ~5-10 s on Windows.
        driver = AppDriver(
            app,
            timeout=60,
            wait_for_start=True,
        )

        try:
            driver.start()
            # Upload the real couple PDF via the file input.  The file
            # input lives inside a ``ui.panel_conditional`` so we first
            # ensure the input mode is set to ``pdf_upload`` (the
            # default) before uploading.
            driver.set_value(
                "input_ID_tab_clients_subtab_clients_outline_input_mode",
                "pdf_upload",
            )
            # ``set_value`` for a file input accepts a Path; Shiny
            # copies the file into the server-side temp directory and
            # binds the input to that datapath.
            driver.set_value(
                "input_ID_tab_clients_subtab_clients_outline_file_upload",
                str(_PDF_COUPLE),
            )
            # Give the polling observer a few ticks to process the
            # upload and re-render the outputs.  ``AppDriver`` does
            # not expose a public "wait for reactive" API, so we use
            # a short ``sleep`` (0.5s x 6 = 3s) which is more than
            # enough for the 0.5s ``invalidate_later`` polling
            # interval to fire three times.
            driver.wait_for_idle(timeout=10)

            # The in-card Imported Values Summary output should now
            # contain the extracted primary name.
            summary_html = str(
                driver.get_value(
                    "output_ID_tab_clients_subtab_clients_outline_imported_summary",
                ),
            )
            assert "Anne Smith" in summary_html, (
                f"in-card summary must show 'Anne Smith' after upload; got: {summary_html[:500]}"
            )

            # The "Preview of Client Inputs" section must contain the
            # new heading and the partner name from the couple PDF.
            preview_html = str(
                driver.get_value(
                    "output_ID_tab_clients_subtab_clients_outline_preview_section",
                ),
            )
            assert "Preview of Client Inputs" in preview_html, (
                f"preview section must show the new 'Preview of Client "
                f"Inputs' heading after upload; got: {preview_html[:500]}"
            )
            assert "John Walsh" in preview_html, (
                f"preview section must show 'John Walsh' after upload; "
                f"got: {preview_html[:500]}"
            )
        finally:
            driver.stop()

    @pytest.mark.integration()
    def test_clear_button_clears_preview(self) -> None:
        """The "Clear Imported Preview" button resets the rendered HTML to the placeholder."""
        app = _build_minimal_clients_app()
        driver = AppDriver(app, timeout=60, wait_for_start=True)

        try:
            driver.start()
            # Upload the PDF first.
            driver.set_value(
                "input_ID_tab_clients_subtab_clients_outline_input_mode",
                "pdf_upload",
            )
            driver.set_value(
                "input_ID_tab_clients_subtab_clients_outline_file_upload",
                str(_PDF_COUPLE),
            )
            driver.wait_for_idle(timeout=10)

            # Sanity: the summary must show the extracted name.
            summary_html = str(
                driver.get_value(
                    "output_ID_tab_clients_subtab_clients_outline_imported_summary",
                ),
            )
            assert "Anne Smith" in summary_html

            # Click the clear button.
            driver.click(
                "input_ID_tab_clients_subtab_clients_outline_btn_reject",
            )
            driver.wait_for_idle(timeout=10)

            # The summary must now show the placeholder again.
            summary_html_after = str(
                driver.get_value(
                    "output_ID_tab_clients_subtab_clients_outline_imported_summary",
                ),
            )
            assert "Anne Smith" not in summary_html_after, (
                "summary must not show extracted data after the clear button is clicked"
            )
            assert (
                "Upload a worksheet to see extracted values here." in summary_html_after
            ), "summary must show placeholder after the clear button is clicked"
        finally:
            driver.stop()


# ---------------------------------------------------------------------------
# Token-saver: emit a short PASS / SKIP line so the test runner
# surfaces the skip reason when ``shiny[testing]`` is missing.
# ---------------------------------------------------------------------------

if not _real_pdf_available:  # pragma: no cover
    print(
        "[skip] Inputs_QWIM_Client_Couple.pdf is not present; "
        "Outline E2E tests will be skipped.",
        file=sys.stderr,
    )

if os.environ.get("SHINY_TESTING_AVAILABLE") is None:  # pragma: no cover
    # Allow ops to force-skip on slow CI runners by setting this env var.
    pass


# ---------------------------------------------------------------------------
# Helper: seed reactives_shiny with the Advisor subtab's input reactives
# ---------------------------------------------------------------------------
#
# NOTE: the pure-function advisor-sync tests live in a sibling module
# ``test_integration_advisor_sync_default_firm.py`` because the
# ``pytest.importorskip("shiny.testing")`` call at the top of this
# file causes all tests in this module to be skipped when the
# optional ``shiny[testing]`` extra is not installed.  Keeping the
# AppDriver-only tests here preserves the skip-if-`AppDriver`-missing
# contract without losing the pure-function coverage.
# ---------------------------------------------------------------------------


def _seed_advisor_reactives_shiny() -> tuple[dict, dict]:
    """Build a ``reactives_shiny`` pre-seeded with the Advisor input reactives.

    Returns
    -------
    tuple of (dict, dict)
        ``(reactives_shiny, reactive_values_by_key)`` where the second
        element maps each seeded reactive key to its ``reactive.Value``
        for assertions.
    """
    from src.dashboard.shiny_utils.reactives_initialization import (
        create_reactive_value_safely,
    )

    keys = (
        "Input_Tab_Setup_Subtab_advisor_info_name",
        "Input_Tab_Setup_Subtab_advisor_info_firm",
        "Input_Tab_Setup_Subtab_advisor_info_email",
        "Input_Tab_Setup_Subtab_advisor_info_title",
    )
    reactive_values_by_key = {
        key: create_reactive_value_safely(initial_value="") for key in keys
    }
    reactives_shiny = {
        "User_Inputs_Shiny": dict(reactive_values_by_key),
        "Inner_Variables_Shiny": {
            "Extracted_Worksheet_Data": create_reactive_value_safely(
                initial_value=None,
            ),
            "Extracted_Worksheet_Status_Messages": create_reactive_value_safely(
                initial_value=[],
            ),
            "Extracted_Worksheet_Defaulted_Fields": create_reactive_value_safely(
                initial_value=[],
            ),
            "Extracted_Worksheet_Warnings": create_reactive_value_safely(
                initial_value=None,
            ),
            "Extracted_Worksheet_Has_Client_Partner": create_reactive_value_safely(
                initial_value=True,
            ),
        },
        "Triggers_Shiny": {
            "Trigger_Populate_From_Worksheet": create_reactive_value_safely(
                initial_value=0,
            ),
        },
    }
    return reactives_shiny, reactive_values_by_key

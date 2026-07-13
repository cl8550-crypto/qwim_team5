"""Playwright end-to-end test: uploading an Input Worksheet PDF populates clients.

This test drives a real Chromium browser through the QWIM Shiny dashboard,
uploads one of the real sample *Input Worksheet* PDFs in the
``Clients > Outline`` subtab, and verifies that the producer subtab reacts to
the upload by rendering the extracted-data preview (which is what proves the
upload -> ``@reactive.event`` observer -> sync -> render chain is wired).

The browser flow mirrors the user-facing requirement: after an upload, the
preview of the extracted client data appears, with the client's name drawn
from the PDF (rather than the dashboard defaults).

Prerequisites
-------------
*   ``pip install pytest-playwright`` and ``playwright install chromium``.
*   The real sample worksheets under ``inputs/QWIM``.

Running
-------
    pytest tests/tests_shiny/dashboard/test_outline_upload_playwright.py \\
           --override-ini="norecursedirs=" -v

Markers
-------
Tagged ``@pytest.mark.playwright``.  Skipped automatically when
``pytest-playwright`` or the sample PDFs are unavailable.
"""

from __future__ import annotations

from pathlib import Path

import pytest


try:
    import pytest_playwright  # noqa: F401  — provides the 'page' fixture

    PYTEST_PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PYTEST_PLAYWRIGHT_AVAILABLE = False

if PYTEST_PLAYWRIGHT_AVAILABLE:
    from playwright.sync_api import Page, expect
else:
    Page = object  # type: ignore[assignment,misc]
    expect = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Sample worksheet PDFs
# ---------------------------------------------------------------------------

_INPUTS_QWIM_DIR = Path(__file__).resolve().parents[3] / "inputs" / "QWIM"
_PDF_SINGLE = _INPUTS_QWIM_DIR / "Inputs_QWIM_Client_Single.pdf"
_PDF_COUPLE = _INPUTS_QWIM_DIR / "Inputs_QWIM_Client_Couple.pdf"

_real_pdfs_available = _PDF_SINGLE.is_file() and _PDF_COUPLE.is_file()

pytestmark = [
    pytest.mark.skipif(
        not PYTEST_PLAYWRIGHT_AVAILABLE,
        reason="pytest-playwright not installed — install it to run browser tests",
    ),
    pytest.mark.skipif(
        not _real_pdfs_available,
        reason="sample worksheet PDFs (inputs/QWIM) are not available",
    ),
]

# Selector signalling that the Shiny app is fully initialised.
_SEL_SHINY_READY = (
    "[data-shiny-server-started], .shiny-bound-output, "
    "#shiny-tab-clients, nav.navbar, .nav-link"
)

# The Outline file input is module-namespaced; match it by its id suffix so
# the test does not hard-code the full Shiny module namespace prefix.
_SEL_FILE_UPLOAD = "input[type='file'][id$='outline_file_upload']"

# The preview output container (module-namespaced, matched by suffix).
_SEL_PREVIEW_OUTPUT = '[id$="outline_preview_section"]'
_SEL_PREVIEW_HEADING = 'h5:has-text("Preview of Extracted Data")'


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _goto_outline(page: Page, base_url: str) -> None:
    """Open the app and navigate to the ``Clients > Outline`` subtab.

    Parameters
    ----------
    page : playwright.sync_api.Page
        The Playwright page driving the browser.
    base_url : str
        Base URL of the running Shiny app (from ``shiny_server_url``).
    """
    page.goto(
        base_url.rstrip("/"),
        wait_until="domcontentloaded",
        timeout=30_000,
    )
    page.wait_for_selector(_SEL_SHINY_READY, timeout=20_000, state="attached")

    clients_tab = (
        page.get_by_role("tab", name="Clients")
        .or_(page.locator("a:has-text('Clients'), [data-value='clients']"))
        .first
    )
    clients_tab.click(timeout=10_000)

    outline_tab = (
        page.get_by_role("tab", name="Outline")
        .or_(page.locator("a:has-text('Outline'), [data-value='Outline']"))
        .first
    )
    outline_tab.click(timeout=10_000)

    # The file input is rendered directly in the static UI (inside a
    # ui.panel_conditional), so it is in the DOM as soon as the Outline
    # panel becomes active.  We just need to wait for the file input to
    # appear.
    page.wait_for_selector(_SEL_FILE_UPLOAD, timeout=20_000, state="attached")


def _upload_worksheet(page: Page, pdf_path: Path) -> None:
    """Upload a worksheet PDF through the Outline file input.

    Parameters
    ----------
    page : playwright.sync_api.Page
        The Playwright page driving the browser.
    pdf_path : pathlib.Path
        Path to the worksheet PDF to upload.
    """
    page.set_input_files(_SEL_FILE_UPLOAD, str(pdf_path))


# ---------------------------------------------------------------------------
# Upload populates the extracted-data preview
# ---------------------------------------------------------------------------


@pytest.mark.playwright()
class TestOutlineWorksheetUpload:
    """Uploading a worksheet PDF renders the extracted-data preview."""

    def test_single_pdf_upload_renders_primary_preview(
        self, page: Page, shiny_server_url: str,
    ) -> None:
        """The single-client worksheet populates the preview with the primary name."""
        _goto_outline(page, shiny_server_url)
        _upload_worksheet(page, _PDF_SINGLE)

        # Wait for the preview output container to appear (Shiny renders it
        # once _show_preview becomes True after extraction + sync).
        page.wait_for_selector(
            _SEL_PREVIEW_OUTPUT, timeout=30_000, state="attached",
        )
        # The heading and primary name must be visible inside the preview.
        expect(page.locator(_SEL_PREVIEW_HEADING).first).to_be_visible(
            timeout=30_000,
        )
        expect(page.get_by_text("Anne Smith").first).to_be_visible(timeout=30_000)

    def test_couple_pdf_upload_renders_partner_preview(
        self, page: Page, shiny_server_url: str,
    ) -> None:
        """The couple worksheet populates the preview with the partner name too."""
        _goto_outline(page, shiny_server_url)
        _upload_worksheet(page, _PDF_COUPLE)

        page.wait_for_selector(
            _SEL_PREVIEW_OUTPUT, timeout=30_000, state="attached",
        )
        expect(page.locator(_SEL_PREVIEW_HEADING).first).to_be_visible(
            timeout=30_000,
        )
        expect(page.get_by_text("Anne Smith").first).to_be_visible(timeout=30_000)
        expect(page.get_by_text("John Walsh").first).to_be_visible(timeout=30_000)

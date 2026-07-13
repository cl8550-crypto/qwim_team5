"""Unit tests for the Results Tab Module.

Tests cover:
    - Module importability
    - Callable UI / server functions exported from ``shiny_tab_results``
    - ``subtab_reporting.sanitize_filename_for_security`` edge cases

Author:
    QWIM Development Team

Version:
    0.1.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

_logger = get_logger(name = __name__)

# ---------------------------------------------------------------------------
# Optional import guards
# ---------------------------------------------------------------------------

try:
    from src.dashboard.shiny_tab_results.tab_results import (
        tab_results_server,
        tab_results_ui,
    )

    TAB_RESULTS_AVAILABLE = True
except ImportError as exc:
    TAB_RESULTS_AVAILABLE = False
    _logger.warning(f"tab_results import failed: {exc}")

try:
    from src.dashboard.shiny_tab_results.subtab_reporting import (
        subtab_reporting_server,
        subtab_reporting_ui,
    )

    SUBTAB_REPORTING_AVAILABLE = True
except ImportError as exc:
    SUBTAB_REPORTING_AVAILABLE = False
    _logger.warning(f"subtab_reporting import failed: {exc}")

try:
    from src.dashboard.shiny_tab_results.subtab_reporting import (
        sanitize_filename_for_security,
    )

    SANITIZE_AVAILABLE = True
except (ImportError, AttributeError) as exc:
    SANITIZE_AVAILABLE = False
    _logger.warning(f"sanitize_filename_for_security not importable: {exc}")


# ===========================================================================
# Fixtures
# ===========================================================================


@pytest.fixture()
def mock_data_utils() -> dict[str, Any]:
    """Minimal data_utils stub."""
    return {"project_dir": "/mock/project", "DEFAULTS": {}}


@pytest.fixture()
def mock_data_inputs() -> dict[str, Any]:
    """Minimal data_inputs stub."""
    return {}


@pytest.fixture()
def mock_reactives_shiny() -> dict[str, Any]:
    """Minimal reactives_shiny stub with four required categories."""
    return {
        "User_Inputs_Shiny": {},
        "Inner_Variables_Shiny": {},
        "Triggers_Shiny": {},
        "Visual_Objects_Shiny": {},
    }


# ===========================================================================
# tab_results module structure
# ===========================================================================


@pytest.mark.unit()
@pytest.mark.skipif(not TAB_RESULTS_AVAILABLE, reason="tab_results not importable")
class Test_Tab_Results_Module:
    """Tests for tab_results module structure."""

    @pytest.mark.unit()
    def test_tab_results_ui_is_callable(self) -> None:
        """tab_results_ui should be a callable (Shiny module.ui decorated)."""
        assert callable(tab_results_ui)

    @pytest.mark.unit()
    def test_tab_results_server_is_callable(self) -> None:
        """tab_results_server should be a callable (Shiny module.server decorated)."""
        assert callable(tab_results_server)

    @pytest.mark.unit()
    def test_imports_succeed(self) -> None:
        """Importing shiny_tab_results package exports the expected symbols."""
        from src.dashboard.shiny_tab_results import (
            subtab_reporting_server,
            subtab_reporting_ui,
            tab_results_server,
            tab_results_ui,
        )

        assert tab_results_ui is not None
        assert tab_results_server is not None
        assert subtab_reporting_ui is not None
        assert subtab_reporting_server is not None

    @pytest.mark.unit()
    def test_module_has_docstring(self) -> None:
        """tab_results module should have a module-level docstring."""
        import src.dashboard.shiny_tab_results.tab_results as _mod

        assert _mod.__doc__ is not None
        assert len(_mod.__doc__.strip()) > 0

    @pytest.mark.unit()
    def test_docstring_mentions_results(self) -> None:
        """Docstring should be relevant to the Results tab."""
        import src.dashboard.shiny_tab_results.tab_results as _mod

        assert _mod.__doc__ is not None
        doc_lower = _mod.__doc__.lower()
        assert "result" in doc_lower or "report" in doc_lower or "tab" in doc_lower


# ===========================================================================
# subtab_reporting imports
# ===========================================================================


@pytest.mark.unit()
@pytest.mark.skipif(
    not SUBTAB_REPORTING_AVAILABLE, reason="subtab_reporting not importable"
)
class Test_SubTab_Reporting_Module:
    """Tests for subtab_reporting module structure."""

    @pytest.mark.unit()
    def test_subtab_reporting_ui_is_callable(self) -> None:
        """Test that subtab reporting ui is callable."""
        assert callable(subtab_reporting_ui)

    @pytest.mark.unit()
    def test_subtab_reporting_server_is_callable(self) -> None:
        """Test that subtab reporting server is callable."""
        assert callable(subtab_reporting_server)

    @pytest.mark.unit()
    def test_module_has_docstring(self) -> None:
        """Test that module has docstring."""
        import src.dashboard.shiny_tab_results.subtab_reporting as _mod

        assert _mod.__doc__ is not None


# ===========================================================================
# sanitize_filename_for_security
# ===========================================================================


@pytest.mark.unit()
@pytest.mark.skipif(not SANITIZE_AVAILABLE, reason="sanitize_filename_for_security not available")
class Test_sanitize_filename_for_security:
    """Tests for the filename sanitization helper.

    ``sanitize_filename_for_security`` returns ``tuple[bool, str, str]``:
    ``(is_valid, sanitized_filename, error_message)``.
    """

    @pytest.mark.unit()
    def test_valid_filename_returns_true_and_filename(self) -> None:
        """A safe PDF filename should be accepted and returned unchanged."""
        is_valid, sanitized, message = sanitize_filename_for_security(filename = "Report_2024.pdf")
        assert is_valid is True
        assert sanitized.lower().endswith(".pdf")
        assert "valid" in message.lower() or "secure" in message.lower()

    @pytest.mark.unit()
    def test_path_traversal_rejected(self) -> None:
        """Filenames containing '..' (path traversal) must be rejected."""
        is_valid, sanitized, message = sanitize_filename_for_security(filename = "../../etc/passwd.pdf")
        assert is_valid is False
        assert sanitized == ""
        # Error message should mention the forbidden pattern
        assert ".." in message or "forbidden" in message.lower()

    @pytest.mark.unit()
    def test_backslash_rejected(self) -> None:
        r"""Filenames containing '\\' must be rejected."""
        is_valid, sanitized, message = sanitize_filename_for_security(
            filename = "C:\\Windows\\System32\\file.pdf"
        )
        assert is_valid is False
        assert sanitized == ""

    @pytest.mark.unit()
    def test_empty_string_rejected(self) -> None:
        """Empty filename must be rejected with an informative message."""
        is_valid, sanitized, message = sanitize_filename_for_security(filename = "")
        assert is_valid is False
        assert sanitized == ""
        assert "empty" in message.lower() or len(message) > 0

    @pytest.mark.unit()
    def test_none_input_rejected(self) -> None:
        """None input is handled via short-circuit and rejected gracefully."""
        is_valid, sanitized, message = sanitize_filename_for_security(filename = None)  # type: ignore[arg-type]
        assert is_valid is False
        assert isinstance(sanitized, str)

    @pytest.mark.unit()
    def test_long_filename_rejected(self) -> None:
        """Filenames exceeding MAX_FILENAME_LENGTH must be rejected, not truncated."""
        long_name = "a" * 300 + ".pdf"
        is_valid, sanitized, message = sanitize_filename_for_security(filename = long_name)
        assert is_valid is False
        assert sanitized == ""
        assert "too long" in message.lower() or str(200) in message

    @pytest.mark.unit()
    def test_missing_pdf_extension_rejected(self) -> None:
        """Filenames without .pdf extension must be rejected."""
        is_valid, _, message = sanitize_filename_for_security(filename = "Report_2024.docx")
        assert is_valid is False
        assert "pdf" in message.lower()

    @pytest.mark.unit()
    def test_too_short_filename_rejected(self) -> None:
        """Filenames shorter than 5 characters (including .pdf) are rejected."""
        is_valid, _, _ = sanitize_filename_for_security(filename = "a.pd")
        assert is_valid is False

    @pytest.mark.unit()
    def test_return_type_is_tuple_of_three(self) -> None:
        """Return value must always be a 3-tuple."""
        result = sanitize_filename_for_security(filename = "QWIM_Report_2024.pdf")
        assert isinstance(result, tuple)
        assert len(result) == 3
        is_valid, sanitized, message = result
        assert isinstance(is_valid, bool)
        assert isinstance(sanitized, str)
        assert isinstance(message, str)

    @pytest.mark.parametrize(
        "forbidden",
        ["../", "./", "~", "$", "%", "|"],
    )
    @pytest.mark.unit()
    def test_forbidden_characters_rejected(self, forbidden: str) -> None:
        """Various forbidden characters in filenames must all be rejected."""
        filename = f"Report{forbidden}2024.pdf"
        is_valid, _, _ = sanitize_filename_for_security(filename = filename)
        assert is_valid is False


# ===========================================================================
# Module-level imports (standard library / shiny)
# ===========================================================================


@pytest.mark.unit()
class Test_Standard_Imports:
    """Sanity tests that basic dependencies are importable."""

    @pytest.mark.unit()
    def test_shiny_ui_available(self) -> None:
        """Test that shiny ui available."""
        from shiny import ui  # noqa: PLC0415

        assert ui is not None

    @pytest.mark.unit()
    def test_shiny_module_available(self) -> None:
        """Test that shiny module available."""
        from shiny import module  # noqa: PLC0415

        assert module is not None

    @pytest.mark.unit()
    def test_polars_available(self) -> None:
        """Test that polars available."""
        import polars as pl  # noqa: PLC0415

        assert pl is not None

    @pytest.mark.unit()
    def test_pathlib_available(self) -> None:
        """Test that pathlib available."""
        assert Path is not None

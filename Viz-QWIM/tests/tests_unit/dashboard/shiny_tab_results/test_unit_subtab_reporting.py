"""Unit tests for subtab_reporting module.

Tests cover:
    - Module constants and security configuration
    - Feature-availability flag types
    - Module-level utility functions:
        - ``sanitize_filename_for_security``
        - ``create_secure_temp_directory``
        - ``cleanup_temp_files``
    - Callable Shiny UI / server exports

Author:
    QWIM Development Team

Version:
    0.1.0
"""

from __future__ import annotations

import builtins
import importlib
import os
import re
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

_logger = get_logger(name = __name__)

# ---------------------------------------------------------------------------
# Import guards
# ---------------------------------------------------------------------------

try:
    import src.dashboard.shiny_tab_results.subtab_reporting as _mod

    SUBTAB_REPORTING_AVAILABLE = True
except ImportError as exc:
    _mod = None  # type: ignore[assignment]
    SUBTAB_REPORTING_AVAILABLE = False
    _logger.warning(f"subtab_reporting import failed: {exc}")

try:
    from src.dashboard.shiny_tab_results.subtab_reporting import (
        subtab_reporting_server,
        subtab_reporting_ui,
    )

    CALLABLES_AVAILABLE = True
except ImportError as exc:
    CALLABLES_AVAILABLE = False
    _logger.warning(f"subtab_reporting callables not importable: {exc}")

try:
    from src.dashboard.shiny_tab_results.subtab_reporting import (
        ALLOWED_FILENAME_PATTERN,
        FORBIDDEN_FILENAME_PARTS,
        MAX_FILENAME_LENGTH,
    )

    CONSTANTS_AVAILABLE = True
except ImportError as exc:
    CONSTANTS_AVAILABLE = False
    _logger.warning(f"subtab_reporting constants not importable: {exc}")

try:
    from src.dashboard.shiny_tab_results.subtab_reporting import (
        sanitize_filename_for_security,
    )

    SANITIZE_AVAILABLE = True
except (ImportError, AttributeError) as exc:
    SANITIZE_AVAILABLE = False
    _logger.warning(f"sanitize_filename_for_security not importable: {exc}")

try:
    from src.dashboard.shiny_tab_results.subtab_reporting import (
        _compile_typst_report_to_pdf_QWIM,
        cleanup_temp_files,
        create_secure_temp_directory,
    )

    TEMP_UTILS_AVAILABLE = True
except (ImportError, AttributeError) as exc:
    TEMP_UTILS_AVAILABLE = False
    _logger.warning(f"temp utility functions not importable: {exc}")


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


# ===========================================================================
# Module structure and docstring
# ===========================================================================


@pytest.mark.unit()
@pytest.mark.skipif(not SUBTAB_REPORTING_AVAILABLE, reason="subtab_reporting not importable")
class Test_SubTab_Reporting_Module_Structure:
    """Tests for module-level structure of subtab_reporting."""

    @pytest.mark.unit()
    def test_module_has_docstring(self) -> None:
        """Module must have a non-empty docstring."""
        assert _mod is not None
        assert _mod.__doc__ is not None
        assert len(_mod.__doc__.strip()) > 0

    @pytest.mark.unit()
    def test_docstring_mentions_reporting(self) -> None:
        """Docstring should reference reporting or PDF generation."""
        assert _mod is not None
        assert _mod.__doc__ is not None
        doc_lower = _mod.__doc__.lower()
        assert any(kw in doc_lower for kw in ("report", "pdf", "typst", "result"))

    @pytest.mark.unit()
    def test_available_flags_are_booleans(self) -> None:
        """REPORT_QWIM_AVAILABLE, TYPST_AVAILABLE, DATA_UTILS_AVAILABLE must be booleans."""
        assert _mod is not None
        for flag_name in ("REPORT_QWIM_AVAILABLE", "TYPST_AVAILABLE", "DATA_UTILS_AVAILABLE"):
            value = getattr(_mod, flag_name, None)
            assert value is not None, f"Missing flag: {flag_name}"
            assert isinstance(value, bool), f"{flag_name} should be bool, got {type(value)}"

    @pytest.mark.unit()
    def test_module_exposes_sanitize_function(self) -> None:
        """sanitize_filename_for_security must be importable at module level."""
        assert _mod is not None
        assert hasattr(_mod, "sanitize_filename_for_security")
        assert callable(_mod.sanitize_filename_for_security)

    @pytest.mark.unit()
    def test_module_exposes_temp_directory_helpers(self) -> None:
        """create_secure_temp_directory and cleanup_temp_files must be at module level."""
        assert _mod is not None
        assert hasattr(_mod, "create_secure_temp_directory")
        assert hasattr(_mod, "cleanup_temp_files")
        assert callable(_mod.create_secure_temp_directory)
        assert callable(_mod.cleanup_temp_files)


# ===========================================================================
# Security constants
# ===========================================================================


@pytest.mark.unit()
@pytest.mark.skipif(not CONSTANTS_AVAILABLE, reason="constants not importable")
class Test_Security_Constants:
    """Tests for module-level security constants."""

    @pytest.mark.unit()
    def test_max_filename_length_is_positive_int(self) -> None:
        """MAX_FILENAME_LENGTH must be a positive integer."""
        assert isinstance(MAX_FILENAME_LENGTH, int)
        assert MAX_FILENAME_LENGTH > 0

    @pytest.mark.unit()
    def test_max_filename_length_reasonable(self) -> None:
        """MAX_FILENAME_LENGTH should be between 50 and 500 to be practical."""
        assert 50 <= MAX_FILENAME_LENGTH <= 500

    @pytest.mark.unit()
    def test_forbidden_filename_parts_is_list(self) -> None:
        """FORBIDDEN_FILENAME_PARTS must be a non-empty list of strings."""
        assert isinstance(FORBIDDEN_FILENAME_PARTS, list)
        assert len(FORBIDDEN_FILENAME_PARTS) > 0
        for part in FORBIDDEN_FILENAME_PARTS:
            assert isinstance(part, str), f"Expected str, got {type(part)}: {part!r}"

    @pytest.mark.unit()
    def test_forbidden_parts_includes_path_traversal(self) -> None:
        """'..' must be in FORBIDDEN_FILENAME_PARTS (path traversal defense)."""
        assert ".." in FORBIDDEN_FILENAME_PARTS

    @pytest.mark.unit()
    def test_forbidden_parts_includes_backslash(self) -> None:
        r"""'\\' must be in FORBIDDEN_FILENAME_PARTS (Windows path injection)."""
        assert "\\" in FORBIDDEN_FILENAME_PARTS

    @pytest.mark.unit()
    def test_allowed_pattern_is_compiled_regex(self) -> None:
        """ALLOWED_FILENAME_PATTERN must be a compiled regex."""
        assert isinstance(ALLOWED_FILENAME_PATTERN, re.Pattern)

    @pytest.mark.unit()
    def test_allowed_pattern_accepts_valid_filenames(self) -> None:
        """ALLOWED_FILENAME_PATTERN must match well-formed PDF filenames."""
        valid_names = [
            "Report_2024.pdf",
            "QWIM Report 2024.pdf",
            "Client-Portfolio(v2).pdf",
            "annual.report.pdf",
        ]
        for name in valid_names:
            assert ALLOWED_FILENAME_PATTERN.match(name), f"Pattern should match: {name!r}"

    @pytest.mark.unit()
    def test_allowed_pattern_rejects_path_traversal(self) -> None:
        """ALLOWED_FILENAME_PATTERN must not match filenames with '..'."""
        assert ALLOWED_FILENAME_PATTERN.match("../../etc/passwd.pdf") is None

    @pytest.mark.unit()
    def test_windows_reserved_names_forbidden(self) -> None:
        """Windows device names (CON, PRN, AUX, NUL) must be in forbidden list."""
        windows_reserved = ["CON", "PRN", "AUX", "NUL"]
        for name in windows_reserved:
            assert name in FORBIDDEN_FILENAME_PARTS, f"{name} missing from FORBIDDEN_FILENAME_PARTS"


@pytest.mark.unit()
@pytest.mark.skipif(not SUBTAB_REPORTING_AVAILABLE, reason="subtab_reporting not importable")
class Test_PDF_Progress_Int_Coercion:
    """Tests for the module-level PDF progress integer coercion helper."""

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        ("raw_value", "default_value", "expected_value"),
        [
            (True, 12, 12),
            (5, 0, 5),
            ("bad", 7, 7),
        ],
        ids=["bool_uses_default", "int_preserved", "invalid_uses_default"],
    )
    def Test_Coerce_PDF_Progress_Int_Uses_Expected_Fallbacks(
        self,
        raw_value: object,
        default_value: int,
        expected_value: int,
    ) -> None:
        """PDF progress coercion should preserve valid integers and reject booleans."""
        from src.dashboard.shiny_tab_results.subtab_reporting import (
            _coerce_pdf_progress_int_or_default,
        )

        result_value = _coerce_pdf_progress_int_or_default(raw_value = raw_value, default_value = default_value)

        assert result_value == expected_value


@pytest.mark.unit()
@pytest.mark.skipif(not SUBTAB_REPORTING_AVAILABLE, reason="subtab_reporting not importable")
class Test_Typst_Currency_Formatting:
    """Tests for the module-level Typst currency formatter."""

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        ("raw_value", "expected_text"),
        [
            (True, "\\$0"),
            (1234, "\\$1,234"),
            ("bad", "\\$0"),
        ],
        ids=["bool_uses_default", "numeric_formats_currency", "invalid_uses_default"],
    )
    def Test_Format_Currency_For_Typst_Uses_Expected_Fallbacks(
        self,
        raw_value: object,
        expected_text: str,
    ) -> None:
        """Typst currency formatting should preserve numerics and reject booleans."""
        from src.dashboard.shiny_tab_results.subtab_reporting import _format_currency_for_typst

        result_text = _format_currency_for_typst(amount = raw_value)

        assert result_text == expected_text


@pytest.mark.unit()
@pytest.mark.skipif(not SUBTAB_REPORTING_AVAILABLE, reason="subtab_reporting not importable")
class Test_Reporting_Flag_Coercion:
    """Tests for the module-level reporting include-flag helper."""

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        ("raw_value", "default_value", "expected_value"),
        [
            (True, False, True),
            (False, True, False),
            ("bad", True, True),
            ("bad", False, False),
            (None, True, True),
        ],
        ids=[
            "true_preserved",
            "false_preserved",
            "invalid_uses_true_default",
            "invalid_uses_false_default",
            "none_uses_default",
        ],
    )
    def Test_Coerce_Reporting_Flag_Uses_Expected_Defaults(
        self,
        raw_value: object,
        default_value: bool,
        expected_value: bool,
    ) -> None:
        """Reporting flag coercion should preserve booleans and reject truthy non-bools."""
        from src.dashboard.shiny_tab_results.subtab_reporting import _coerce_reporting_flag_or_default

        result_value = _coerce_reporting_flag_or_default(raw_value = raw_value, default_value = default_value)

        assert result_value is expected_value


# ===========================================================================
# sanitize_filename_for_security
# ===========================================================================


@pytest.mark.unit()
@pytest.mark.skipif(not SANITIZE_AVAILABLE, reason="sanitize_filename_for_security not available")
class Test_Sanitize_Filename_For_Security:
    """Comprehensive tests for ``sanitize_filename_for_security``.

    The function signature is:
        ``sanitize_filename_for_security(filename: str) -> tuple[bool, str, str]``

    Return value: ``(is_valid, sanitized_filename, error_message)``
    """

    # --- return-type contract ---

    @pytest.mark.unit()
    def test_return_type_always_tuple_of_three(self) -> None:
        """Return must always be a 3-tuple regardless of input."""
        for filename in ["valid.pdf", "", "a" * 300 + ".pdf", "bad/../path.pdf"]:
            result = sanitize_filename_for_security(filename = filename)
            assert isinstance(result, tuple), f"Expected tuple for input {filename!r}"
            assert len(result) == 3, f"Expected 3-tuple for input {filename!r}"

    @pytest.mark.unit()
    def test_first_element_is_bool(self) -> None:
        """First element (is_valid) must always be bool."""
        is_valid, _, _ = sanitize_filename_for_security(filename = "Report.pdf")
        assert isinstance(is_valid, bool)

    @pytest.mark.unit()
    def test_second_element_is_str(self) -> None:
        """Second element (sanitized_filename) must always be str."""
        _, sanitized, _ = sanitize_filename_for_security(filename = "Report.pdf")
        assert isinstance(sanitized, str)

    @pytest.mark.unit()
    def test_third_element_is_str(self) -> None:
        """Third element (error_message) must always be str."""
        _, _, message = sanitize_filename_for_security(filename = "Report.pdf")
        assert isinstance(message, str)

    # --- valid inputs ---

    @pytest.mark.unit()
    def test_valid_pdf_filename_accepted(self) -> None:
        """A conforming PDF filename must be accepted with is_valid=True."""
        is_valid, sanitized, _ = sanitize_filename_for_security(filename = "QWIM_Report_2024.pdf")
        assert is_valid is True
        assert sanitized != ""
        assert sanitized.lower().endswith(".pdf")

    @pytest.mark.unit()
    def test_valid_filename_sanitized_name_is_returned(self) -> None:
        """Sanitized name for a valid filename should equal or resemble the original."""
        is_valid, sanitized, _ = sanitize_filename_for_security(filename = "Annual Report 2024.pdf")
        assert is_valid is True
        assert "Annual" in sanitized or "annual" in sanitized.lower()

    @pytest.mark.parametrize(
        "valid_name",
        [
            "Report_2024.pdf",
            "QWIM Report 2024.pdf",
            "Client-Portfolio(v2).pdf",
            "Annual.Summary.pdf",
        ],
    )
    @pytest.mark.unit()
    def test_various_valid_filenames(self, valid_name: str) -> None:
        """Parameterized check that well-formed PDF filenames are accepted."""
        is_valid, sanitized, _ = sanitize_filename_for_security(filename = valid_name)
        assert is_valid is True, f"Expected acceptance for: {valid_name!r}"
        assert sanitized != ""

    # --- rejection cases ---

    @pytest.mark.unit()
    def test_empty_string_rejected(self) -> None:
        """Empty filename must be rejected."""
        is_valid, sanitized, message = sanitize_filename_for_security(filename = "")
        assert is_valid is False
        assert sanitized == ""
        assert len(message) > 0

    @pytest.mark.unit()
    def test_none_input_rejected_gracefully(self) -> None:
        """None input is handled via short-circuit and rejected without exception."""
        is_valid, sanitized, _ = sanitize_filename_for_security(filename = None)  # type: ignore[arg-type]
        assert is_valid is False
        assert isinstance(sanitized, str)

    @pytest.mark.unit()
    def test_whitespace_only_rejected(self) -> None:
        """Whitespace-only filename must be rejected."""
        is_valid, _, message = sanitize_filename_for_security(filename = "   ")
        assert is_valid is False
        assert "empty" in message.lower()

    @pytest.mark.unit()
    def test_too_long_filename_rejected(self) -> None:
        """Filenames over MAX_FILENAME_LENGTH characters must be rejected, not truncated."""
        long_name = "x" * (MAX_FILENAME_LENGTH + 10) + ".pdf"
        is_valid, sanitized, message = sanitize_filename_for_security(filename = long_name)
        assert is_valid is False
        assert sanitized == ""
        assert "long" in message.lower()

    @pytest.mark.unit()
    def test_too_short_filename_rejected(self) -> None:
        """Filename under 5 characters must be rejected."""
        is_valid, _, _ = sanitize_filename_for_security(filename = "a.p")
        assert is_valid is False

    @pytest.mark.unit()
    def test_non_pdf_extension_rejected(self) -> None:
        """Filenames not ending in .pdf must be rejected."""
        for ext in [".docx", ".txt", ".xlsx", ".png", ""]:
            name = f"Report{ext}"
            is_valid, _, message = sanitize_filename_for_security(filename = name)
            assert is_valid is False, f"Expected rejection for extension {ext!r}"
            # message should mention pdf
            assert "pdf" in message.lower()

    @pytest.mark.parametrize(
        "path_traversal",
        [
            "../../etc/passwd.pdf",
            "../sibling.pdf",
            "./local.pdf",
            "reports/../config.pdf",
        ],
    )
    @pytest.mark.unit()
    def test_path_traversal_rejected(self, path_traversal: str) -> None:
        """Path traversal patterns in filenames must be rejected."""
        is_valid, sanitized, _ = sanitize_filename_for_security(filename = path_traversal)
        assert is_valid is False
        assert sanitized == ""

    @pytest.mark.parametrize(
        "forbidden_char",
        ["$", "%", "|", "*", "?", "<", ">", "~"],
    )
    @pytest.mark.unit()
    def test_forbidden_special_chars_rejected(self, forbidden_char: str) -> None:
        """Filenames with forbidden special characters must be rejected."""
        filename = f"Report{forbidden_char}2024.pdf"
        is_valid, _, _ = sanitize_filename_for_security(filename = filename)
        assert is_valid is False, f"Expected rejection for char {forbidden_char!r}"

    @pytest.mark.unit()
    def test_starting_with_dot_rejected(self) -> None:
        """Filenames starting with '.' must be rejected."""
        is_valid, _, _ = sanitize_filename_for_security(filename = ".hidden_report.pdf")
        assert is_valid is False

    @pytest.mark.unit()
    def test_starting_with_hyphen_rejected(self) -> None:
        """Filenames starting with '-' must be rejected."""
        is_valid, _, _ = sanitize_filename_for_security(filename = "-bad_filename.pdf")
        assert is_valid is False

    @pytest.mark.unit()
    def test_double_dots_in_name_rejected(self) -> None:
        """Filenames with '..' anywhere must be rejected."""
        is_valid, _, _ = sanitize_filename_for_security(filename = "report..pdf")
        assert is_valid is False

    @pytest.mark.parametrize(
        "windows_device",
        ["CON.pdf", "PRN.pdf", "AUX.pdf", "NUL.pdf"],
    )
    @pytest.mark.unit()
    def test_windows_reserved_device_names_rejected(self, windows_device: str) -> None:
        """Windows reserved device names must be rejected."""
        is_valid, _, _ = sanitize_filename_for_security(filename = windows_device)
        assert is_valid is False

    # --- message content when rejected ---

    @pytest.mark.unit()
    def test_rejection_message_is_non_empty(self) -> None:
        """When rejected, error_message must describe why."""
        is_valid, _, message = sanitize_filename_for_security(filename = "")
        assert is_valid is False
        assert len(message) > 0

    @pytest.mark.unit()
    def test_acceptance_message_mentions_valid(self) -> None:
        """When accepted, message should confirm validity."""
        is_valid, _, message = sanitize_filename_for_security(filename = "QWIM_Report.pdf")
        assert is_valid is True
        assert "valid" in message.lower() or "secure" in message.lower()


# ===========================================================================
# create_secure_temp_directory
# ===========================================================================


@pytest.mark.unit()
@pytest.mark.skipif(not TEMP_UTILS_AVAILABLE, reason="temp utils not importable")
class Test_Create_Secure_Temp_Directory:
    """Tests for ``create_secure_temp_directory``."""

    @pytest.mark.unit()
    def test_returns_string(self) -> None:
        """Must return a str path."""
        result = create_secure_temp_directory()
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.unit()
    def test_directory_exists(self) -> None:
        """Returned path must point to an existing directory."""
        temp_dir = create_secure_temp_directory()
        assert os.path.exists(temp_dir)
        assert os.path.isdir(temp_dir)
        # Cleanup
        cleanup_temp_files(temp_directory = temp_dir)

    @pytest.mark.unit()
    def test_directory_is_writable(self) -> None:
        """Returned directory must be writable."""
        temp_dir = create_secure_temp_directory()
        assert os.access(temp_dir, os.W_OK)
        cleanup_temp_files(temp_directory = temp_dir)

    @pytest.mark.unit()
    def test_prefix_pattern(self) -> None:
        """Returned path should use the 'qwim_reports_' prefix or be a valid fallback."""
        temp_dir = create_secure_temp_directory()
        # Either our custom prefix or a valid system temp dir
        is_qwim_dir = "qwim_reports_" in os.path.basename(temp_dir)
        is_system_temp = temp_dir.startswith(tempfile.gettempdir())
        assert is_qwim_dir or is_system_temp
        cleanup_temp_files(temp_directory = temp_dir)

    @pytest.mark.unit()
    def test_each_call_produces_different_directory(self) -> None:
        """Each call should create a unique directory (no collision)."""
        dir1 = create_secure_temp_directory()
        dir2 = create_secure_temp_directory()
        try:
            # Both should exist; they should be different paths
            assert os.path.exists(dir1)
            assert os.path.exists(dir2)
            assert dir1 != dir2
        finally:
            cleanup_temp_files(temp_directory = dir1)
            cleanup_temp_files(temp_directory = dir2)


# ===========================================================================
# cleanup_temp_files
# ===========================================================================


@pytest.mark.unit()
@pytest.mark.skipif(not TEMP_UTILS_AVAILABLE, reason="temp utils not importable")
class Test_Cleanup_Temp_Files:
    """Tests for ``cleanup_temp_files``."""

    @pytest.mark.unit()
    def test_removes_qwim_temp_directory(self) -> None:
        """A qwim_reports_ directory must be removed after cleanup."""
        temp_dir = create_secure_temp_directory()
        assert os.path.exists(temp_dir)
        cleanup_temp_files(temp_directory = temp_dir)
        assert not os.path.exists(temp_dir)

    @pytest.mark.unit()
    def test_does_not_raise_on_empty_string(self) -> None:
        """Passing empty string must not raise an exception (early-return guard)."""
        try:
            cleanup_temp_files(temp_directory = "")
        except Exception as exc:
            pytest.fail(f"cleanup_temp_files('') raised unexpectedly: {exc}")

    @pytest.mark.unit()
    def test_does_not_raise_on_nonexistent_path(self) -> None:
        """Passing a path that does not exist must not raise an exception."""
        nonexistent = os.path.join(tempfile.gettempdir(), "qwim_reports_nonexistent_xyz")
        try:
            cleanup_temp_files(temp_directory = nonexistent)
        except Exception as exc:
            pytest.fail(f"cleanup_temp_files(nonexistent) raised unexpectedly: {exc}")

    @pytest.mark.unit()
    def test_skips_non_temp_directory(self, tmp_path: Path) -> None:
        """Directories outside the system temp dir without 'qwim_reports' must be skipped.

        We patch ``tempfile.gettempdir`` so the check treats ``tmp_path`` as if
        it were outside the system temp tree, simulating a non-temp directory.
        """
        safe_dir = tmp_path / "safe_project_dir"
        safe_dir.mkdir()
        sentinel = safe_dir / "sentinel.txt"
        sentinel.write_text("do not delete")

        # Make gettempdir return an unrelated path so safe_dir appears "outside temp"
        with patch(
            "src.dashboard.shiny_tab_results.subtab_reporting.tempfile.gettempdir",
            return_value="/not_a_real_temp_dir",
        ):
            cleanup_temp_files(temp_directory = str(safe_dir))

        # The sentinel file should still exist (directory was skipped)
        assert sentinel.exists()

    @pytest.mark.unit()
    def test_removes_files_inside_temp_directory(self) -> None:
        """Files inside the qwim temp directory are also removed."""
        temp_dir = create_secure_temp_directory()
        # Create a file inside
        test_file = os.path.join(temp_dir, "test_output.pdf")
        with open(test_file, "w") as f:
            f.write("test content")
        assert os.path.exists(test_file)

        cleanup_temp_files(temp_directory = temp_dir)
        assert not os.path.exists(temp_dir)
        assert not os.path.exists(test_file)


@pytest.mark.unit()
@pytest.mark.skipif(not TEMP_UTILS_AVAILABLE, reason="temp utils not importable")
class Test_Typst_Runtime_Helper:
    """Tests for the module-level Typst runtime helper."""

    @pytest.mark.unit()
    def test_missing_typst_source_returns_controlled_failure(self, tmp_path: Path) -> None:
        """Missing Typst source files must return a controlled failure tuple."""
        success, message = _compile_typst_report_to_pdf_QWIM(
            typst_file_path = tmp_path / "missing.typ",
            output_pdf_path = tmp_path / "report.pdf",
        )

        assert success is False
        assert "not found" in message.lower()

    @pytest.mark.unit()
    def test_runtime_unavailable_returns_controlled_failure(self, tmp_path: Path) -> None:
        """Unavailable Typst runtime must return a controlled failure tuple."""
        typst_file = tmp_path / "report.typ"
        typst_file.write_text("= Demo", encoding="utf-8")

        with patch.object(_mod, "TYPST_AVAILABLE", False):
            success, message = _compile_typst_report_to_pdf_QWIM(
                typst_file_path = typst_file,
                output_pdf_path = tmp_path / "report.pdf",
            )

        assert success is False
        assert "runtime not available" in message.lower()

    @pytest.mark.unit()
    def test_helper_delegates_to_shared_typst_utility(self, tmp_path: Path) -> None:
        """The helper must delegate compilation to compile_typst_document_to_pdf_QWIM."""
        typst_file = tmp_path / "report.typ"
        typst_file.write_text("= Demo", encoding="utf-8")
        output_pdf = tmp_path / "report.pdf"

        with (
            patch.object(_mod, "TYPST_AVAILABLE", True),
            patch.object(_mod, "compile_typst_document_to_pdf_QWIM", return_value=(True, "ok")) as mock_compile,
        ):
            success, message = _compile_typst_report_to_pdf_QWIM(
                typst_file_path = typst_file,
                output_pdf_path = output_pdf,
            )

        assert success is True
        assert message == "ok"
        mock_compile.assert_called_once_with(
            typst_file_path=typst_file,
            output_pdf_path=output_pdf,
            _typst_module=_mod._TYPST_MODULE,
        )

    @pytest.mark.unit()
    def test_helper_wraps_unexpected_compilation_exception(self, tmp_path: Path) -> None:
        """Unexpected Typst failures must be wrapped in a controlled error tuple."""
        typst_file = tmp_path / "report.typ"
        typst_file.write_text("= Demo", encoding="utf-8")
        output_pdf = tmp_path / "report.pdf"

        with (
            patch.object(_mod, "TYPST_AVAILABLE", True),
            patch.object(
                _mod,
                "compile_typst_document_to_pdf_QWIM",
                side_effect=RuntimeError("boom"),
            ),
        ):
            success, message = _compile_typst_report_to_pdf_QWIM(
                typst_file_path = typst_file,
                output_pdf_path = output_pdf,
            )

        assert success is False
        assert "compilation error" in message.lower()
        assert "boom" in message


@pytest.mark.unit()
@pytest.mark.skipif(not SUBTAB_REPORTING_AVAILABLE, reason="subtab_reporting not importable")
class Test_Subtab_Reporting_Import_Time_Typst_Runtime:
    """Reload-based tests for Typst runtime discovery at import time."""

    @pytest.mark.unit()
    def test_cli_only_runtime_marks_typst_as_available(self) -> None:
        """A discovered Typst CLI path should keep Typst support enabled without the module."""
        assert _mod is not None
        fake_cli_path = str(Path(tempfile.gettempdir()) / "typst.exe")
        original_import = builtins.__import__

        def _import_without_typst(name: str, *args: Any, **kwargs: Any) -> Any:
            if name == "typst":
                raise ImportError("forced missing typst for test")
            return original_import(name, *args, **kwargs)

        try:
            with (
                patch(
                    "src.utils.typst_utils.resolve_typst_executable_path_QWIM",
                    return_value=fake_cli_path,
                ),
                patch("builtins.__import__", side_effect=_import_without_typst),
            ):
                importlib.reload(_mod)

            assert _mod._TYPST_MODULE is None
            assert _mod._TYPST_CLI_PATH == fake_cli_path
            assert _mod.TYPST_AVAILABLE is True
        finally:
            importlib.reload(_mod)


# ===========================================================================
# Shiny callable exports
# ===========================================================================


@pytest.mark.unit()
@pytest.mark.skipif(not CALLABLES_AVAILABLE, reason="subtab_reporting callables not importable")
class Test_SubTab_Reporting_Callables:
    """Tests for the Shiny-decorated callable exports."""

    @pytest.mark.unit()
    def test_subtab_reporting_ui_is_callable(self) -> None:
        """subtab_reporting_ui must be callable (Shiny @module.ui decorated)."""
        assert callable(subtab_reporting_ui)

    @pytest.mark.unit()
    def test_subtab_reporting_server_is_callable(self) -> None:
        """subtab_reporting_server must be callable (Shiny @module.server decorated)."""
        assert callable(subtab_reporting_server)

    @pytest.mark.unit()
    def test_subtab_reporting_ui_has_docstring(self) -> None:
        """subtab_reporting_ui must have a non-empty docstring on the underlying function."""
        # Shiny's @module.ui does not copy __doc__ to the wrapper; the original
        # function is stored as the first closure cell.
        closure = getattr(subtab_reporting_ui, "__closure__", None)
        assert closure is not None and len(closure) > 0, (
            "subtab_reporting_ui has no closure — cannot locate original function"
        )
        original_fn = closure[0].cell_contents
        doc = getattr(original_fn, "__doc__", None)
        assert doc is not None and len(doc.strip()) > 0

    @pytest.mark.unit()
    def test_subtab_reporting_server_has_docstring(self) -> None:
        """subtab_reporting_server must have a non-empty docstring on the underlying function."""
        # Shiny's @module.server does not copy __doc__ to the wrapper; the original
        # function is stored as the first closure cell.
        closure = getattr(subtab_reporting_server, "__closure__", None)
        assert closure is not None and len(closure) > 0, (
            "subtab_reporting_server has no closure — cannot locate original function"
        )
        original_fn = closure[0].cell_contents
        doc = getattr(original_fn, "__doc__", None)
        assert doc is not None and len(doc.strip()) > 0


# ===========================================================================
# Import / standard library sanity
# ===========================================================================


@pytest.mark.unit()
class Test_Standard_Imports_SubTab_Reporting:
    """Sanity checks that dependencies used by subtab_reporting are importable."""

    @pytest.mark.unit()
    def test_shiny_importable(self) -> None:
        """Test that shiny importable."""
        from shiny import module, ui  # noqa: PLC0415

        assert module is not None
        assert ui is not None

    @pytest.mark.unit()
    def test_re_importable(self) -> None:
        """Test that re importable."""
        import re as _re  # noqa: PLC0415

        assert _re is not None

    @pytest.mark.unit()
    def test_pathlib_importable(self) -> None:
        """Test that pathlib importable."""
        assert Path is not None

    @pytest.mark.unit()
    def test_tempfile_importable(self) -> None:
        """Test that tempfile importable."""
        import tempfile as _tmp  # noqa: PLC0415

        assert _tmp is not None


# ===========================================================================
# Bug-fix regression: copy_typst_dependencies_to_temp_directory copies .typ
# ===========================================================================


@pytest.mark.unit()
class Test_Copy_Typst_Dependencies_Includes_Typ_Files:
    """Regression tests for the Typst compilation bug.

    ``report_QWIM.typ`` uses ``#import`` statements to pull in utility
    modules (``utils_reporting.typ``, ``utils_colors.typ``, etc.) via
    relative paths.  When the template is copied to an ephemeral temp
    directory those utility files must also be present; otherwise Typst
    raises a "file not found" error.

    The fix adds ``"*.typ"`` to the ``Dependencies_To_Copy`` list inside
    ``copy_typst_dependencies_to_temp_directory``.
    """

    _SOURCE_PATH = Path("src/dashboard/shiny_tab_results/subtab_reporting.py")

    @pytest.mark.unit()
    def test_source_includes_typ_wildcard_in_dependencies(self) -> None:
        """Dependencies_To_Copy must include the '*.typ' wildcard pattern."""
        source = self._SOURCE_PATH.read_text(encoding="utf-8")
        assert '"*.typ"' in source, (
            '"*.typ" must appear in Dependencies_To_Copy so that utility '
            ".typ files are copied to the Typst temp directory."
        )

    @pytest.mark.unit()
    def test_source_has_copy_typst_dependencies_function(self) -> None:
        """copy_typst_dependencies_to_temp_directory must exist in the server."""
        source = self._SOURCE_PATH.read_text(encoding="utf-8")
        assert "copy_typst_dependencies_to_temp_directory" in source

    @pytest.mark.unit()
    def test_reporting_dir_contains_required_typ_files(self) -> None:
        """The reporting directory must contain all five utility .typ files."""
        reporting_dir = Path("src/dashboard/reporting")
        required = {
            "utils_reporting.typ",
            "utils_colors.typ",
            "utils_fonts.typ",
            "utils_table.typ",
            "utils_formatting.typ",
        }
        present = {f.name for f in reporting_dir.glob("*.typ")}
        missing = required - present
        assert not missing, f"Missing utility .typ files in reporting/: {missing}"

    @pytest.mark.unit()
    def test_copy_typ_files_to_temp_dir(self) -> None:
        """*.typ wildcard must copy utility files to a temp directory correctly."""
        import glob
        import shutil
        import tempfile

        template_dir = Path("src/dashboard/reporting")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            # Replicate only the *.typ portion of the copy logic
            pattern = str(template_dir / "*.typ")
            for src_file in glob.glob(pattern):
                if Path(src_file).is_file():
                    shutil.copy2(src_file, tmp_path / Path(src_file).name)
            copied = {f.name for f in tmp_path.glob("*.typ")}
            assert "utils_reporting.typ" in copied
            assert "utils_colors.typ" in copied
            assert "report_QWIM.typ" in copied


@pytest.mark.unit()
class Test_Subtab_Reporting_Typst_Runtime_Source:
    """Source-level tests for Typst runtime delegation."""

    _SOURCE_PATH = Path("src/dashboard/shiny_tab_results/subtab_reporting.py")

    @pytest.mark.unit()
    def test_source_imports_shared_typst_runtime_helpers(self) -> None:
        """subtab_reporting must import the shared Typst runtime helpers."""
        source = self._SOURCE_PATH.read_text(encoding="utf-8")
        assert "compile_typst_document_to_pdf_QWIM" in source
        assert "resolve_typst_executable_path_QWIM" in source

    @pytest.mark.unit()
    def test_source_tracks_cli_path_for_typst_runtime(self) -> None:
        """TYPST_AVAILABLE must consider either module or CLI availability."""
        source = self._SOURCE_PATH.read_text(encoding="utf-8")
        assert "_TYPST_CLI_PATH = resolve_typst_executable_path_QWIM()" in source
        assert "TYPST_AVAILABLE = _TYPST_MODULE is not None or _TYPST_CLI_PATH is not None" in source

    @pytest.mark.unit()
    def test_compile_helper_delegates_to_shared_typst_utility(self) -> None:
        """The nested compile helper must delegate to the shared Typst utility."""
        source = self._SOURCE_PATH.read_text(encoding="utf-8")
        assert "def _compile_typst_report_to_pdf_QWIM(" in source
        assert "return _compile_typst_report_to_pdf_QWIM(" in source
        assert "Typst runtime not available for compilation" in source

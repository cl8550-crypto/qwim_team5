"""Behave step definitions for typst_utils feature.

Covers:
  - resolve_typst_executable_path_QWIM
  - build_typst_compile_command_QWIM
  - compile_typst_document_to_pdf_QWIM

Author:         QWIM Development Team
Version:        0.1.0
Last Modified:  2026-05-29
"""

from __future__ import annotations

import io
import sys
import tempfile

from pathlib import Path
from types import SimpleNamespace

from behave import given, then, when

# ---------------------------------------------------------------------------
# Project root on sys.path
# ---------------------------------------------------------------------------
_PROJECT_ROOT: Path = Path(__file__).resolve().parents[4]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# ---------------------------------------------------------------------------
# sys.stderr patch for exception_custom.py compatibility
# ---------------------------------------------------------------------------
if not hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Module-level import guard
# ---------------------------------------------------------------------------
MODULE_IMPORT_AVAILABLE: bool = True
_import_error_message: str = ""

try:
    from src.utils.typst_utils import (
        build_typst_compile_command_QWIM,
        compile_typst_document_to_pdf_QWIM,
        resolve_typst_executable_path_QWIM,
    )
except Exception as _exc:
    MODULE_IMPORT_AVAILABLE = False
    _import_error_message = str(_exc)


def _require_imports() -> None:
    """Require imports."""
    if not MODULE_IMPORT_AVAILABLE:
        raise RuntimeError(
            f"typst_utils could not be imported: {_import_error_message}"
        )


def _build_paths() -> tuple[Path, Path, Path]:
    """Create temporary typst input, output, and executable paths."""
    tmp_dir = Path(tempfile.mkdtemp())
    input_path = tmp_dir / "report.typ"
    output_path = tmp_dir / "report.pdf"
    executable_path = tmp_dir / "typst.exe"
    return input_path, output_path, executable_path


def _raise_binding_failure(*_args: object, **_kwargs: object) -> None:
    """Raise the canonical binding failure used in acceptance tests."""
    raise RuntimeError("binding failure")


def _raise_missing_cli(*_args: object, **_kwargs: object) -> None:
    """Raise the canonical CLI-not-found failure used in acceptance tests."""
    raise FileNotFoundError


@given("typst utility helpers are importable")
def step_given_typst_utils_importable(context) -> None:
    """Require typst_utils imports and initialize context state."""
    _require_imports()
    context.typst_command = None
    context.typst_result = None
    context.typst_executable_path = None
    context.expected_executable_path = None
    context.typst_input_path = None
    context.typst_output_path = None


@when("I resolve the typst executable path with an unavailable lookup")
def step_resolve_typst_path_missing(context) -> None:
    """Resolve Typst when lookup returns no executable."""
    _require_imports()
    context.typst_executable_path = resolve_typst_executable_path_QWIM(
        _which_func=lambda _item_name: None,
    )


@when("I build the typst compile command with an explicit executable path")
def step_build_typst_command_explicit(context) -> None:
    """Build Typst compile command with a resolved executable path."""
    _require_imports()
    input_path, output_path, executable_path = _build_paths()
    input_path.write_text("= Behave Typst", encoding="utf-8")
    executable_path.write_text("", encoding="utf-8")
    context.typst_input_path = input_path
    context.typst_output_path = output_path
    context.expected_executable_path = executable_path
    context.typst_command = build_typst_compile_command_QWIM(
        typst_executable_path = executable_path,
        typst_file_path = input_path,
        output_pdf_path = output_path,
    )


@when("I build the typst compile command without a resolved executable path")
def step_build_typst_command_bare(context) -> None:
    """Build Typst compile command with bare typst fallback."""
    _require_imports()
    input_path, output_path, _ = _build_paths()
    input_path.write_text("= Behave Typst", encoding="utf-8")
    context.typst_input_path = input_path
    context.typst_output_path = output_path
    context.typst_command = build_typst_compile_command_QWIM(
        typst_executable_path = None,
        typst_file_path = input_path,
        output_pdf_path = output_path,
    )


@when("I compile a typst document through the injected Python binding")
def step_compile_typst_binding_success(context) -> None:
    """Compile a Typst file using the injected Python binding seam."""
    _require_imports()
    input_path, output_path, _ = _build_paths()
    input_path.write_text("= Behave Typst", encoding="utf-8")

    def _mock_compile(*_args: object, **_kwargs: object) -> None:
        output_path.write_bytes(b"%PDF-1.4 behave")

    context.typst_result = compile_typst_document_to_pdf_QWIM(
        typst_file_path = input_path,
        output_pdf_path = output_path,
        _typst_module=SimpleNamespace(compile=_mock_compile),
    )


@when("I compile a missing typst source document")
def step_compile_typst_missing_source(context) -> None:
    """Compile a missing Typst input path to exercise not-found handling."""
    _require_imports()
    input_path, output_path, _ = _build_paths()
    context.typst_result = compile_typst_document_to_pdf_QWIM(
        typst_file_path = input_path,
        output_pdf_path = output_path,
    )


@when("I compile a typst document after a binding failure and missing CLI")
def step_compile_typst_binding_failure_then_missing_cli(context) -> None:
    """Compile a Typst file with binding failure and missing CLI fallback."""
    _require_imports()
    input_path, output_path, _ = _build_paths()
    input_path.write_text("= Behave Typst", encoding="utf-8")
    context.typst_result = compile_typst_document_to_pdf_QWIM(
        typst_file_path = input_path,
        output_pdf_path = output_path,
        _typst_module=SimpleNamespace(compile=_raise_binding_failure),
        _subprocess_run=_raise_missing_cli,
    )


@then("the resolved typst executable path should be absent")
def step_then_typst_path_absent(context) -> None:
    """Assert Typst executable resolution returned None."""
    assert context.typst_executable_path is None


@then("the typst compile command should start with the explicit executable path")
def step_then_typst_command_explicit(context) -> None:
    """Assert Typst command starts with the explicit executable path."""
    assert context.typst_command is not None
    assert context.expected_executable_path is not None
    assert context.typst_command[0] == str(context.expected_executable_path)


@then("the typst compile command should start with the bare typst executable")
def step_then_typst_command_bare(context) -> None:
    """Assert Typst command starts with the bare typst executable."""
    assert context.typst_command is not None
    assert context.typst_command[0] == "typst"


@then("the typst compile command should include compile input and output arguments")
def step_then_typst_command_arguments(context) -> None:
    """Assert Typst command contains compile plus input and output paths."""
    assert context.typst_command is not None
    assert context.typst_input_path is not None
    assert context.typst_output_path is not None
    assert context.typst_command[1:] == [
        "compile",
        str(context.typst_input_path),
        str(context.typst_output_path),
    ]


@then("the typst compilation should succeed with a compiled PDF message")
def step_then_typst_compile_success(context) -> None:
    """Assert Typst compilation succeeded with the standard success message."""
    assert context.typst_result is not None
    success_flag, status_message = context.typst_result
    assert success_flag is True
    assert "compiled successfully" in status_message.lower()


@then("the typst compilation should fail with a source not found message")
def step_then_typst_compile_missing_source(context) -> None:
    """Assert Typst compilation failed because the source file was missing."""
    assert context.typst_result is not None
    success_flag, status_message = context.typst_result
    assert success_flag is False
    assert "not found" in status_message.lower()


@then("the typst compilation should fail mentioning the binding failure and missing CLI")
def step_then_typst_compile_binding_and_cli_failure(context) -> None:
    """Assert Typst compilation surfaced both binding and CLI fallback failures."""
    assert context.typst_result is not None
    success_flag, status_message = context.typst_result
    assert success_flag is False
    assert "binding failure" in status_message
    assert "typst cli not found" in status_message.lower()
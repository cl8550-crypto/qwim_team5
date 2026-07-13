"""Robot Framework keyword library for typst_utils tests.

Keyword wrappers for:
- resolve_typst_executable_path_QWIM: missing executable handling
- build_typst_compile_command_QWIM: explicit and fallback command construction
- compile_typst_document_to_pdf_QWIM: success and failure result reporting

Author:
    QWIM Development Team

Version:
    0.1.0

Last Modified:
    2026-05-29
"""

from __future__ import annotations

import io
import sys
import tempfile

from pathlib import Path
from types import SimpleNamespace

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path
# ---------------------------------------------------------------------------
_PROJECT_ROOT: Path = Path(__file__).resolve().parents[3]
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
    import logging as _logging

    _logger = _logging.getLogger(__name__)
except ImportError as _exc:
    MODULE_IMPORT_AVAILABLE = False
    _import_error_message = str(_exc)
    import logging as _logging

    _logger = _logging.getLogger(__name__)
    _logger.warning("Import failed — keywords will raise on use: %s", _exc)


def _require_imports() -> None:
    """Raise RuntimeError when source modules could not be imported."""
    if not MODULE_IMPORT_AVAILABLE:
        raise RuntimeError(f"typst_utils could not be imported: {_import_error_message}")


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


def module_is_importable() -> bool:
    """Return True if typst_utils can be imported."""
    return MODULE_IMPORT_AVAILABLE


def typst_executable_resolution_returns_none() -> None:
    """Assert executable resolution returns None when lookup fails."""
    _require_imports()
    result = resolve_typst_executable_path_QWIM(_which_func=lambda _item_name: None)
    assert result is None, f"Expected None, got {result!r}"


def typst_compile_command_uses_explicit_executable_path() -> None:
    """Assert command construction preserves an explicit executable path."""
    _require_imports()
    input_path, output_path, executable_path = _build_paths()
    input_path.write_text("= Robot Typst", encoding="utf-8")
    executable_path.write_text("", encoding="utf-8")
    command_vector = build_typst_compile_command_QWIM(
        typst_executable_path = executable_path,
        typst_file_path = input_path,
        output_pdf_path = output_path,
    )
    assert command_vector == [
        str(executable_path),
        "compile",
        str(input_path),
        str(output_path),
    ]


def typst_compile_command_falls_back_to_bare_executable() -> None:
    """Assert command construction falls back to the bare typst executable."""
    _require_imports()
    input_path, output_path, _ = _build_paths()
    input_path.write_text("= Robot Typst", encoding="utf-8")
    command_vector = build_typst_compile_command_QWIM(
        typst_executable_path = None,
        typst_file_path = input_path,
        output_pdf_path = output_path,
    )
    assert command_vector == [
        "typst",
        "compile",
        str(input_path),
        str(output_path),
    ]


def typst_python_binding_compilation_succeeds() -> None:
    """Assert injected Python binding compilation returns success."""
    _require_imports()
    input_path, output_path, _ = _build_paths()
    input_path.write_text("= Robot Typst", encoding="utf-8")

    def _mock_compile(*_args: object, **_kwargs: object) -> None:
        output_path.write_bytes(b"%PDF-1.4 robot")

    success_flag, status_message = compile_typst_document_to_pdf_QWIM(
        typst_file_path = input_path,
        output_pdf_path = output_path,
        _typst_module=SimpleNamespace(compile=_mock_compile),
    )
    assert success_flag is True
    assert "compiled successfully" in status_message.lower()


def typst_missing_source_returns_failure() -> None:
    """Assert missing Typst source input returns the not-found failure."""
    _require_imports()
    input_path, output_path, _ = _build_paths()
    success_flag, status_message = compile_typst_document_to_pdf_QWIM(
        typst_file_path = input_path,
        output_pdf_path = output_path,
    )
    assert success_flag is False
    assert "not found" in status_message.lower()


def typst_binding_failure_and_missing_cli_returns_failure() -> None:
    """Assert binding failure plus missing CLI yields the combined failure message."""
    _require_imports()
    input_path, output_path, _ = _build_paths()
    input_path.write_text("= Robot Typst", encoding="utf-8")
    success_flag, status_message = compile_typst_document_to_pdf_QWIM(
        typst_file_path = input_path,
        output_pdf_path = output_path,
        _typst_module=SimpleNamespace(compile=_raise_binding_failure),
        _subprocess_run=_raise_missing_cli,
    )
    assert success_flag is False
    assert "binding failure" in status_message
    assert "typst cli not found" in status_message.lower()
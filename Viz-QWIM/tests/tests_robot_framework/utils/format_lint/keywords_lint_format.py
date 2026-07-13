"""Robot Framework keyword library for lint_format tests.

Keyword wrappers for:
- run_command: return type and success code for a simple Python command
- lint_and_format_file: non-existent path validation
- lint_and_format_directory: non-existent / non-dir path validation

Author:
    QWIM Development Team

Version:
    0.1.0

Last Modified:
    2026-05-27
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path
# ---------------------------------------------------------------------------
_PROJECT_ROOT: Path = Path(__file__).resolve().parents[5]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Module-level import guard
# ---------------------------------------------------------------------------
MODULE_IMPORT_AVAILABLE: bool = True
_import_error_message: str = ""

try:
    from src.utils.format_lint.lint_format import (
        lint_and_format_directory,
        lint_and_format_file,
        run_command,
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
        raise RuntimeError(
            f"lint_format could not be imported: {_import_error_message}"
        )


# ===========================================================================
# Module import keyword
# ===========================================================================


def module_is_importable() -> bool:
    """Return True if the lint_format module can be imported."""
    return MODULE_IMPORT_AVAILABLE


# ===========================================================================
# run_command keywords
# ===========================================================================


def run_command_returns_integer() -> None:
    """Assert that run_command returns an integer for a simple Python command."""
    _require_imports()

    result = run_command(command = [sys.executable, "-c", "print('hello')"])

    assert isinstance(result, int), f"Expected int, got {type(result)}: {result}"


def run_command_echo_returns_zero() -> None:
    """Assert that a successful Python command returns 0."""
    _require_imports()

    result = run_command(command = [sys.executable, "-c", "print('hello')"])

    assert result == 0, f"Expected 0 for echo command, got {result}"


# ===========================================================================
# lint_and_format_file keywords
# ===========================================================================


def lint_file_nonexistent_returns_one() -> None:
    """Assert that lint_and_format_file returns 1 for a non-existent path."""
    _require_imports()
    missing = str(Path(tempfile.mkdtemp()) / "does_not_exist.py")

    result = lint_and_format_file(file_path = missing)

    assert result == 1, f"Expected 1 for missing file, got {result}"


def lint_file_returns_integer() -> None:
    """Assert that lint_and_format_file always returns an int."""
    _require_imports()
    missing = str(Path(tempfile.mkdtemp()) / "missing.py")

    result = lint_and_format_file(file_path = missing)

    assert isinstance(result, int), f"Expected int, got {type(result)}: {result}"


# ===========================================================================
# lint_and_format_directory keywords
# ===========================================================================


def lint_directory_nonexistent_returns_one() -> None:
    """Assert that lint_and_format_directory returns 1 for a non-existent directory."""
    _require_imports()
    missing = str(Path(tempfile.mkdtemp()) / "no_such_dir")

    result = lint_and_format_directory(directory_path = missing)

    assert result == 1, f"Expected 1 for missing directory, got {result}"


def lint_directory_file_path_returns_one() -> None:
    """Assert that lint_and_format_directory returns 1 when path is a file."""
    _require_imports()
    tmp = Path(tempfile.mkdtemp())
    py_file = tmp / "sample.py"
    py_file.write_text("x = 1\n", encoding="utf-8")

    result = lint_and_format_directory(directory_path = str(py_file))

    assert result == 1, f"Expected 1 for file-as-directory, got {result}"


def lint_directory_returns_integer() -> None:
    """Assert that lint_and_format_directory always returns an int."""
    _require_imports()
    missing = str(Path(tempfile.mkdtemp()) / "no_such_dir")

    result = lint_and_format_directory(directory_path = missing)

    assert isinstance(result, int), f"Expected int, got {type(result)}: {result}"

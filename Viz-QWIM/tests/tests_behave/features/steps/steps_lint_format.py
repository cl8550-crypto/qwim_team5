"""Behave step definitions for lint_format feature.

Covers:
    - run_command: return type and value for a simple Python command
  - lint_and_format_file: return code for non-existent paths
  - lint_and_format_directory: return code for non-existent / non-dir paths

Author:         QWIM Development Team
Version:        0.1.0
Last Modified:  2026-05-27
"""

from __future__ import annotations

import io
import sys
import tempfile
from pathlib import Path

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
    from src.utils.format_lint.lint_format import (
        lint_and_format_directory,
        lint_and_format_file,
        run_command,
    )
except Exception as _exc:
    MODULE_IMPORT_AVAILABLE = False
    _import_error_message = str(_exc)


def _require_imports() -> None:
    """Raise RuntimeError when source modules could not be imported."""
    if not MODULE_IMPORT_AVAILABLE:
        raise RuntimeError(
            f"lint_format could not be imported: {_import_error_message}"
        )


# ===========================================================================
# Given steps
# ===========================================================================


@given("lint_format modules are importable")
def step_modules_importable(context):
    """Verify the module can be imported."""
    _require_imports()


@given("a temporary Python file exists")
def step_tmp_py_file(context):
    """Create a temporary Python file and store path in context."""
    _require_imports()
    tmp = Path(tempfile.mkdtemp())
    py_file = tmp / "sample.py"
    py_file.write_text("x = 1\n", encoding="utf-8")
    context.tmp_py_file = str(py_file)


# ===========================================================================
# When steps
# ===========================================================================


@when('I run the command "echo hello"')
@when("I run a simple Python command")
def step_run_simple_python_command(context):
    """Run a simple Python command through the command helper."""
    _require_imports()
    context.return_code = run_command(command = [sys.executable, "-c", "print('hello')"])


@when("I lint_and_format_file a path that does not exist")
def step_lint_file_missing(context):
    """Run lint_and_format_file on a non-existent path."""
    _require_imports()
    missing = str(Path(tempfile.mkdtemp()) / "does_not_exist.py")
    context.return_code = lint_and_format_file(file_path = missing)


@when("I lint_and_format_directory a path that does not exist")
def step_lint_dir_missing(context):
    """Run lint_and_format_directory on a non-existent path."""
    _require_imports()
    missing = str(Path(tempfile.mkdtemp()) / "no_such_dir")
    context.return_code = lint_and_format_directory(directory_path = missing)


@when("I lint_and_format_directory that file path")
def step_lint_dir_is_file(context):
    """Run lint_and_format_directory on a file path (not a directory)."""
    _require_imports()
    context.return_code = lint_and_format_directory(directory_path = context.tmp_py_file)


# ===========================================================================
# Then steps
# ===========================================================================


@then("the return code is an integer")
def step_return_code_is_int(context):
    """Assert return code is an integer."""
    assert isinstance(context.return_code, int), (
        f"Expected int, got {type(context.return_code)}: {context.return_code}"
    )


@then("the return code is zero")
def step_return_code_zero(context):
    """Assert return code is 0."""
    assert context.return_code == 0, f"Expected 0, got {context.return_code}"


@then("the return code is 1")
def step_return_code_one(context):
    """Assert return code is 1."""
    assert context.return_code == 1, f"Expected 1, got {context.return_code}"

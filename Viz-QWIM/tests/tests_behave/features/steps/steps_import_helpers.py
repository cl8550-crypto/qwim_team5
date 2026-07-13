"""Behave steps for _import_helpers feature."""

from __future__ import annotations

import io
import sys
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
    from src.utils.data_utils._import_helpers import try_import_module
except Exception as _exc:
    MODULE_IMPORT_AVAILABLE = False
    _import_error_message = str(_exc)


def _require_imports() -> None:
    """Raise RuntimeError when source modules could not be imported."""
    if not MODULE_IMPORT_AVAILABLE:
        raise RuntimeError(
            f"_import_helpers could not be imported: {_import_error_message}"
        )


@given("import_helpers modules are importable")
def step_modules_importable(context):
    """Verify the import helper module can be imported."""
    _require_imports()


@when('I try_import_module with module name "os"')
def step_try_import_os(context):
    """Import a known standard-library module."""
    _require_imports()
    context.result = try_import_module(module_name = "os")
    context.raised = None


@when("I try_import_module with a missing module name")
def step_try_import_missing(context):
    """Import a known-missing module name."""
    _require_imports()
    context.result = try_import_module(module_name = "_qwim_missing_module_xyz_9876")
    context.raised = None


@when('I try_import_module with whitespace around module name "sys"')
def step_try_import_whitespace_sys(context):
    """Import a valid module name with surrounding whitespace."""
    _require_imports()
    context.result = try_import_module(module_name = "  sys  ")
    context.raised = None


@when("I try_import_module with a blank module name")
def step_try_import_blank_name(context):
    """Call try_import_module with a blank module name."""
    _require_imports()
    context.result = None
    context.raised = None
    try:
        context.result = try_import_module(module_name = "   ")
    except ValueError as exc:
        context.raised = exc


@when("I try_import_module with a non-string module name")
def step_try_import_non_string_name(context):
    """Call try_import_module with a non-string module name."""
    _require_imports()
    context.result = None
    context.raised = None
    try:
        context.result = try_import_module(module_name = 123)  # type: ignore[arg-type]
    except TypeError as exc:
        context.raised = exc


@when("I try_import_module with a non-callable importer")
def step_try_import_non_callable_importer(context):
    """Call try_import_module with a non-callable importer."""
    _require_imports()
    context.result = None
    context.raised = None
    try:
        context.result = try_import_module(module_name = "os", _importer="bad")  # type: ignore[arg-type]
    except TypeError as exc:
        context.raised = exc


@then('the result is a module named "{module_name}"')
def step_result_is_named_module(context, module_name):
    """Assert a successful module import with exact module name."""
    assert context.result is not None, "Expected a module object, got None"
    assert context.result.__name__ == module_name, (
        f"Expected module name {module_name!r}, got {context.result.__name__!r}"
    )


@then("the import result is None")
def step_result_is_none(context):
    """Assert import helper returned None."""
    assert context.result is None, f"Expected None, got {context.result!r}"


@then("an import_helpers ValueError is raised")
def step_value_error_raised(context):
    """Assert ValueError was raised by the previous step."""
    assert isinstance(context.raised, ValueError), (
        f"Expected ValueError, got {type(context.raised)}: {context.raised}"
    )


@then("an import_helpers TypeError is raised")
def step_type_error_raised(context):
    """Assert TypeError was raised by the previous step."""
    assert isinstance(context.raised, TypeError), (
        f"Expected TypeError, got {type(context.raised)}: {context.raised}"
    )
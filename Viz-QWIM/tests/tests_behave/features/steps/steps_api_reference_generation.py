"""Behave step definitions for api_reference_generation feature.

Covers:
  - discover_python_files: discovery, exclusions, sorting
  - path_to_module_name: dotted-name conversion
  - module_name_to_doc_path: .md path construction, prefix handling
  - check_docstring_sections: missing-section detection

Author:         QWIM Development Team
Version:        0.1.0
Last Modified:  2026-05-27
"""

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
    from src.utils.docs_utils.api_reference_generation import (
        check_docstring_sections,
        discover_python_files,
        module_name_to_doc_path,
        path_to_module_name,
    )
except Exception as _exc:
    MODULE_IMPORT_AVAILABLE = False
    _import_error_message = str(_exc)


def _require_imports() -> None:
    """Raise RuntimeError when source modules could not be imported."""
    if not MODULE_IMPORT_AVAILABLE:
        raise RuntimeError(
            f"api_reference_generation could not be imported: {_import_error_message}"
        )


# ===========================================================================
# Given steps
# ===========================================================================


@given("api_reference_generation modules are importable")
def step_modules_importable(context):
    """Verify the module can be imported."""
    _require_imports()


@given('a temporary directory with Python files "mod_a.py" and "mod_b.py"')
def step_tmp_dir_two_py(context):
    """Create a temp dir with two .py files."""
    _require_imports()
    tmp = Path(context.config.userdata.get("tmp_base", "/tmp")) / "behave_api_ref_1"
    tmp.mkdir(parents=True, exist_ok=True)
    (tmp / "mod_a.py").write_text("x = 1", encoding="utf-8")
    (tmp / "mod_b.py").write_text("y = 2", encoding="utf-8")
    context.tmp_dir = tmp


@given('a temporary directory containing "__init__.py" and "real.py"')
def step_tmp_dir_init_and_real(context):
    """Create a temp dir with an __init__.py and a real module."""
    _require_imports()
    import tempfile

    tmp = Path(tempfile.mkdtemp())
    (tmp / "__init__.py").write_text("", encoding="utf-8")
    (tmp / "real.py").write_text("x = 1", encoding="utf-8")
    context.tmp_dir = tmp


@given('a temporary directory with a "__pycache__/mod.py" nested file')
def step_tmp_dir_with_pycache(context):
    """Create a temp dir with a file inside __pycache__."""
    _require_imports()
    import tempfile

    tmp = Path(tempfile.mkdtemp())
    pycache = tmp / "__pycache__"
    pycache.mkdir()
    (pycache / "mod.py").write_text("x = 1", encoding="utf-8")
    (tmp / "visible.py").write_text("x = 1", encoding="utf-8")
    context.tmp_dir = tmp


@given('a source root with file "src/utils/helper.py"')
def step_tmp_source_root(context):
    """Create a temp source root with a nested .py file."""
    _require_imports()
    import tempfile

    tmp = Path(tempfile.mkdtemp())
    nested = tmp / "src" / "utils"
    nested.mkdir(parents=True)
    (nested / "helper.py").write_text("", encoding="utf-8")
    context.source_root = tmp
    context.py_file = nested / "helper.py"


# ===========================================================================
# When steps
# ===========================================================================


@when("I call discover_python_files on that directory")
def step_call_discover(context):
    """Run discover_python_files on context.tmp_dir."""
    _require_imports()
    context.result = discover_python_files(root_directory = context.tmp_dir)


@when("I call discover_python_files with include_init_files True")
def step_call_discover_include_init(context):
    """Run discover_python_files with include_init_files=True."""
    _require_imports()
    context.result = discover_python_files(root_directory = context.tmp_dir, include_init_files=True)


@when("I call discover_python_files on a path that does not exist")
def step_call_discover_missing(context):
    """Run discover_python_files on a non-existent path."""
    _require_imports()
    import tempfile

    missing = Path(tempfile.mkdtemp()) / "no_such_dir"
    context.result = discover_python_files(root_directory = missing)


@when('I call path_to_module_name for "helper.py" relative to the source root')
def step_call_path_to_module_name(context):
    """Run path_to_module_name."""
    _require_imports()
    context.result = path_to_module_name(file_path = context.py_file, source_root = context.source_root)


@when('I call module_name_to_doc_path with module "src.utils.helper"')
def step_call_module_to_doc_default(context):
    """Run module_name_to_doc_path with default prefix."""
    _require_imports()
    context.result = module_name_to_doc_path(module_name = "src.utils.helper")


@when('I call module_name_to_doc_path with module "src.utils.helper" and prefix "reference"')
def step_call_module_to_doc_custom_prefix(context):
    """Run module_name_to_doc_path with custom prefix."""
    _require_imports()
    context.result = module_name_to_doc_path(module_name = "src.utils.helper", api_prefix="reference")


@when(
    'I call module_name_to_doc_path with module "src.utils.helper" and invalid prefix "bad/prefix"'
)
def step_call_module_to_doc_invalid_prefix(context):
    """Run module_name_to_doc_path with an invalid prefix and capture ValueError."""
    _require_imports()
    context.result = None
    context.raised = None
    try:
        context.result = module_name_to_doc_path(module_name = "src.utils.helper", api_prefix="bad/prefix")
    except ValueError as exc:
        context.raised = exc


@when(
    'I check sections for a docstring containing "Parameters" and "Returns" sections'
    " with has_params True and has_return True"
)
def step_check_sections_full(context):
    """Run check_docstring_sections with full docstring."""
    _require_imports()
    docstring = (
        "Summary line.\n\nParameters\n----------\n    x : int\n\nReturns\n-------\n    int"
    )
    context.result = check_docstring_sections(
        docstring = docstring, has_params=True, has_return_annotation=True
    )


@when("I check sections for a plain summary docstring with has_params True and has_return False")
def step_check_sections_summary_only(context):
    """Run check_docstring_sections with summary-only docstring."""
    _require_imports()
    context.result = check_docstring_sections(
        docstring = "Summary only.", has_params=True, has_return_annotation=False
    )


@when("I check sections for any docstring with has_params False and has_return False")
def step_check_sections_both_false(context):
    """Run check_docstring_sections with both flags False."""
    _require_imports()
    context.result = check_docstring_sections(
        docstring = "Some text.", has_params=False, has_return_annotation=False
    )


# ===========================================================================
# Then steps
# ===========================================================================


@then("the result is a non-empty sorted list of Path objects")
def step_result_sorted_nonempty_paths(context):
    """Assert result is a non-empty sorted list of Path objects."""
    result = context.result
    assert isinstance(result, list)
    assert len(result) > 0
    assert result == sorted(result)
    for item in result:
        assert isinstance(item, Path)


@then('"{filename}" is not in the result')
def step_filename_not_in_result(context, filename):
    """Assert filename is absent from result."""
    names = [p.name for p in context.result]
    assert filename not in names, f"Expected {filename!r} absent, found in {names}"


@then('"{filename}" is in the result')
def step_filename_in_result(context, filename):
    """Assert filename is present in result."""
    names = [p.name for p in context.result]
    assert filename in names, f"Expected {filename!r} present, not found in {names}"


@then('no path containing "__pycache__" is in the result')
def step_no_pycache_in_result(context):
    """Assert no result path contains __pycache__."""
    for p in context.result:
        assert "__pycache__" not in str(p), f"Found pycache path: {p}"


@then("the result is an empty list")
def step_result_is_empty_list(context):
    """Assert result is an empty list."""
    assert context.result == [], f"Expected empty list, got {context.result}"


@then("the result is a dot-separated module name string without path separators")
def step_result_is_dotted_module_name(context):
    """Assert result is a dotted string with no OS separators."""
    result = context.result
    assert isinstance(result, str)
    assert len(result) > 0
    assert "/" not in result
    assert "\\" not in result


@then('the result contains neither "/" nor "\\"')
def step_result_no_separators(context):
    """Assert result contains no forward or back slashes."""
    assert "/" not in context.result
    assert "\\" not in context.result


@then('the result ends with ".md"')
def step_result_ends_md(context):
    """Assert result ends with .md."""
    assert str(context.result).endswith(".md"), f"Expected .md suffix, got: {context.result}"


@then('the result starts with "api/"')
def step_result_starts_api(context):
    """Assert result starts with api/."""
    assert str(context.result).startswith("api/"), f"Expected api/ prefix, got: {context.result}"


@then('the result starts with "reference/"')
def step_result_starts_reference(context):
    """Assert result starts with reference/."""
    assert str(context.result).startswith("reference/"), (
        f"Expected reference/ prefix, got: {context.result}"
    )


@then('"{key}" is False')
def step_key_is_false(context, key):
    """Assert result dict key is False."""
    assert context.result[key] is False, f"Expected {key!r} to be False, got {context.result[key]}"


@then('"{key}" is True')
def step_key_is_true(context, key):
    """Assert result dict key is True."""
    assert context.result[key] is True, f"Expected {key!r} to be True, got {context.result[key]}"


@then("an api_reference ValueError is raised")
def step_value_error_raised(context):
    """Assert that ValueError was raised in the previous step."""
    assert isinstance(context.raised, ValueError), (
        f"Expected ValueError, got {type(context.raised)}: {context.raised}"
    )

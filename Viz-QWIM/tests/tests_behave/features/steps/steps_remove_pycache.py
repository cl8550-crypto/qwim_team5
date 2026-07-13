"""Behave step definitions for remove_pycache feature.

Covers:
  - clean_pycache: basic removal, dry-run, multiple targets
  - ValueError validation for mutually-exclusive arguments

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
    from src.utils.files_folders.remove_pycache import clean_pycache
except Exception as _exc:
    MODULE_IMPORT_AVAILABLE = False
    _import_error_message = str(_exc)


def _require_imports() -> None:
    """Raise RuntimeError when source modules could not be imported."""
    if not MODULE_IMPORT_AVAILABLE:
        raise RuntimeError(
            f"remove_pycache could not be imported: {_import_error_message}"
        )


def _make_tmp_with_pycache() -> Path:
    """Return a new temp dir containing one __pycache__ directory."""
    tmp = Path(tempfile.mkdtemp())
    pycache = tmp / "pkg" / "__pycache__"
    pycache.mkdir(parents=True)
    (pycache / "mod.cpython-313.pyc").write_bytes(b"")
    return tmp


# ===========================================================================
# Given steps
# ===========================================================================


@given("remove_pycache modules are importable")
def step_modules_importable(context):
    """Verify the module can be imported."""
    _require_imports()


@given('a temporary directory with "__pycache__" directories')
def step_tmp_with_multi_pycache(context):
    """Create a temp dir with two __pycache__ dirs."""
    _require_imports()
    tmp = Path(tempfile.mkdtemp())
    for idx in range(2):
        pkg = tmp / f"pkg_{idx}" / "__pycache__"
        pkg.mkdir(parents=True)
        (pkg / f"mod_{idx}.pyc").write_bytes(b"")
    context.tmp_dir = tmp


@given('a temporary directory with one "__pycache__" directory')
def step_tmp_with_one_pycache(context):
    """Create a temp dir with one __pycache__ dir."""
    _require_imports()
    context.tmp_dir = _make_tmp_with_pycache()


@given("a temporary directory with no pycache artifacts")
def step_tmp_empty(context):
    """Create a temp dir with no pycache artifacts."""
    _require_imports()
    tmp = Path(tempfile.mkdtemp())
    (tmp / "module.py").write_text("x = 1\n", encoding="utf-8")
    context.tmp_dir = tmp


@given('two temporary directories each with a "__pycache__" directory')
def step_two_tmp_with_pycache(context):
    """Create two temp dirs each with a __pycache__ dir."""
    _require_imports()
    context.root_a = _make_tmp_with_pycache()
    context.root_b = _make_tmp_with_pycache()


# ===========================================================================
# When steps
# ===========================================================================


@when("I call clean_pycache on that directory")
def step_call_clean(context):
    """Run clean_pycache on context.tmp_dir."""
    _require_imports()
    context.result = clean_pycache(target_dir = context.tmp_dir)
    context.raised = None


@when("I call clean_pycache with dry_run True")
def step_call_clean_dry_run(context):
    """Run clean_pycache with dry_run=True on context.tmp_dir."""
    _require_imports()
    context.result = clean_pycache(target_dir = context.tmp_dir, dry_run=True)
    context.raised = None


@when("I call clean_pycache with target_dirs pointing to both roots and dry_run True")
def step_call_clean_multi_dirs(context):
    """Run clean_pycache with target_dirs=[root_a, root_b]."""
    _require_imports()
    context.result = clean_pycache(
        target_dirs=[context.root_a, context.root_b], dry_run=True
    )
    context.raised = None


@when("I call clean_pycache with both target_dir and target_dirs set")
def step_call_both_args(context):
    """Run clean_pycache with both target_dir and target_dirs set."""
    _require_imports()
    tmp = Path(tempfile.mkdtemp())
    context.raised = None
    try:
        clean_pycache(target_dir=tmp, target_dirs=[tmp])
    except ValueError as exc:
        context.raised = exc


@when("I call clean_pycache with no target arguments")
def step_call_no_args(context):
    """Run clean_pycache with no positional or keyword target."""
    _require_imports()
    context.raised = None
    try:
        clean_pycache()
    except ValueError as exc:
        context.raised = exc


@when("I call clean_pycache on a path that does not exist")
def step_call_missing_target(context):
    """Run clean_pycache against a missing directory path."""
    _require_imports()
    context.raised = None
    missing_root = Path(tempfile.mkdtemp()) / "missing_root"
    try:
        clean_pycache(target_dir = missing_root)
    except FileNotFoundError as exc:
        context.raised = exc


# ===========================================================================
# Then steps
# ===========================================================================


@then('no "__pycache__" directories remain')
def step_no_pycache_remain(context):
    """Assert all __pycache__ dirs were removed."""
    remaining = list(context.tmp_dir.rglob("__pycache__"))
    assert remaining == [], f"Found remaining __pycache__ dirs: {remaining}"


@then("the result is a non-empty list of Path objects")
def step_result_nonempty_paths(context):
    """Assert result is a non-empty list of Path objects."""
    result = context.result
    assert isinstance(result, list)
    assert len(result) > 0
    for item in result:
        assert isinstance(item, Path), f"Expected Path, got {type(item)}"


@then("the clean result is an empty list")
def step_result_empty(context):
    """Assert result is an empty list."""
    assert context.result == [], f"Expected empty list, got {context.result}"


@then('the "__pycache__" directory still exists')
def step_pycache_still_exists(context):
    """Assert __pycache__ is still present after dry run."""
    pycache_dirs = list(context.tmp_dir.rglob("__pycache__"))
    assert len(pycache_dirs) > 0, "Expected __pycache__ dir to still exist after dry run"


@then("the result contains paths from both root directories")
def step_result_from_both_roots(context):
    """Assert result contains at least one path from each root."""
    result_strs = [str(p) for p in context.result]
    root_a_str = str(context.root_a)
    root_b_str = str(context.root_b)
    assert any(root_a_str in s for s in result_strs), (
        f"No path from root_a={root_a_str} found in {result_strs}"
    )
    assert any(root_b_str in s for s in result_strs), (
        f"No path from root_b={root_b_str} found in {result_strs}"
    )


@then("a ValueError is raised")
def step_value_error_raised(context):
    """Assert a ValueError was raised during the When step."""
    assert isinstance(context.raised, ValueError), (
        f"Expected ValueError, got {type(context.raised)}: {context.raised}"
    )


@then("a FileNotFoundError is raised")
def step_file_not_found_error_raised(context):
    """Assert a FileNotFoundError was raised during the When step."""
    assert isinstance(context.raised, FileNotFoundError), (
        f"Expected FileNotFoundError, got {type(context.raised)}: {context.raised}"
    )

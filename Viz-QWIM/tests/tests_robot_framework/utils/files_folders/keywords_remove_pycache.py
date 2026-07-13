"""Robot Framework keyword library for remove_pycache tests.

Keyword wrappers for:
- clean_pycache: basic removal, dry-run, multiple-dir, validation

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
    from src.utils.files_folders.remove_pycache import clean_pycache
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
            f"remove_pycache could not be imported: {_import_error_message}"
        )


def _make_tmp_with_pycache() -> Path:
    """Create and return a temp dir containing one __pycache__ directory."""
    tmp = Path(tempfile.mkdtemp())
    pycache = tmp / "pkg" / "__pycache__"
    pycache.mkdir(parents=True)
    (pycache / "mod.cpython-313.pyc").write_bytes(b"")
    return tmp


# ===========================================================================
# Module import keyword
# ===========================================================================


def module_is_importable() -> bool:
    """Return True if the remove_pycache module can be imported."""
    return MODULE_IMPORT_AVAILABLE


# ===========================================================================
# Removal keywords
# ===========================================================================


def clean_pycache_removes_all_dirs() -> None:
    """Assert that clean_pycache removes all __pycache__ directories."""
    _require_imports()
    tmp = _make_tmp_with_pycache()

    clean_pycache(target_dir = tmp)

    remaining = list(tmp.rglob("__pycache__"))
    assert remaining == [], f"Expected all __pycache__ removed, found: {remaining}"


def clean_pycache_returns_removed_paths() -> None:
    """Assert that clean_pycache returns a non-empty list of Path objects."""
    _require_imports()
    tmp = _make_tmp_with_pycache()

    result = clean_pycache(target_dir = tmp)

    assert isinstance(result, list), f"Expected list, got {type(result)}"
    assert len(result) > 0, "Expected at least one removed path"
    for item in result:
        assert isinstance(item, Path), f"Expected Path, got {type(item)}"


def clean_pycache_empty_dir_returns_empty_list() -> None:
    """Assert that clean_pycache on an empty dir returns an empty list."""
    _require_imports()
    tmp = Path(tempfile.mkdtemp())
    (tmp / "module.py").write_text("x = 1\n", encoding="utf-8")

    result = clean_pycache(target_dir = tmp)

    assert result == [], f"Expected empty list, got {result}"


# ===========================================================================
# Dry-run keywords
# ===========================================================================


def clean_pycache_dry_run_does_not_delete() -> None:
    """Assert that dry_run=True leaves __pycache__ dirs intact."""
    _require_imports()
    tmp = _make_tmp_with_pycache()

    clean_pycache(target_dir = tmp, dry_run=True)

    remaining = list(tmp.rglob("__pycache__"))
    assert len(remaining) > 0, "__pycache__ dir was deleted in dry-run mode"


def clean_pycache_dry_run_returns_candidates() -> None:
    """Assert that dry_run=True returns non-empty candidate list."""
    _require_imports()
    tmp = _make_tmp_with_pycache()

    result = clean_pycache(target_dir = tmp, dry_run=True)

    assert isinstance(result, list)
    assert len(result) > 0, "Expected candidate paths in dry-run result"


# ===========================================================================
# Multiple-directory keywords
# ===========================================================================


def clean_pycache_multiple_dirs_collects_all() -> None:
    """Assert that target_dirs collects paths from all roots."""
    _require_imports()
    root_a = _make_tmp_with_pycache()
    root_b = _make_tmp_with_pycache()

    result = clean_pycache(target_dirs=[root_a, root_b], dry_run=True)

    result_strs = [str(p) for p in result]
    assert any(str(root_a) in s for s in result_strs), (
        f"No path from root_a found in: {result_strs}"
    )
    assert any(str(root_b) in s for s in result_strs), (
        f"No path from root_b found in: {result_strs}"
    )


# ===========================================================================
# Validation keywords
# ===========================================================================


def clean_pycache_both_args_raises_value_error() -> None:
    """Assert that passing both target_dir and target_dirs raises ValueError."""
    _require_imports()
    tmp = Path(tempfile.mkdtemp())

    try:
        clean_pycache(target_dir=tmp, target_dirs=[tmp])
    except ValueError:
        return

    raise AssertionError("Expected ValueError was not raised")


def clean_pycache_no_args_raises_value_error() -> None:
    """Assert that calling clean_pycache with no targets raises ValueError."""
    _require_imports()

    try:
        clean_pycache()
    except ValueError:
        return

    raise AssertionError("Expected ValueError was not raised")


def clean_pycache_missing_target_raises_file_not_found_error() -> None:
    """Assert that missing target directories raise FileNotFoundError."""
    _require_imports()
    missing_root = Path(tempfile.mkdtemp()) / "missing_root"

    try:
        clean_pycache(target_dir = missing_root)
    except FileNotFoundError:
        return

    raise AssertionError("Expected FileNotFoundError was not raised")

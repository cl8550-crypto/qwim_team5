"""Robot Framework keyword library for platform_utils tests."""

from __future__ import annotations

import sys
from collections import namedtuple
from pathlib import Path
from types import SimpleNamespace

# ---------------------------------------------------------------------------
# Project root on sys.path
# ---------------------------------------------------------------------------
_PROJECT_ROOT: Path = Path(__file__).resolve().parents[4]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Module-level import guard
# ---------------------------------------------------------------------------
MODULE_IMPORT_AVAILABLE: bool = True
_import_error_message: str = ""

try:
    from src.utils.custom_exceptions_errors_loggers.platform_utils import (
        get_platform,
        is_linux,
        is_macos,
        is_windows,
        seed_uname_cache_for_windows,
    )
    import logging as _logging

    _logger_kw = _logging.getLogger(__name__)
except Exception as _exc:
    MODULE_IMPORT_AVAILABLE = False
    _import_error_message = str(_exc)
    import logging as _logging

    _logger_kw = _logging.getLogger(__name__)
    _logger_kw.warning("Import failed — keywords will raise on use: %s", _exc)


def _require_imports() -> None:
    """Raise RuntimeError when source modules could not be imported."""
    if not MODULE_IMPORT_AVAILABLE:
        raise RuntimeError(
            f"platform_utils source module could not be imported: {_import_error_message}"
        )


def _make_fake_platform_module(*, uname_cache=None):
    """Return a lightweight stand-in for the platform module."""
    fake_uname = namedtuple(
        "Fake_Uname", ["system", "node", "release", "version", "machine"]
    )
    return SimpleNamespace(_uname_cache=uname_cache, uname_result=fake_uname)


def module_is_importable() -> bool:
    """Return True when platform_utils can be imported."""
    return MODULE_IMPORT_AVAILABLE


def get_platform_normalizes_linux_seed() -> bool:
    """Return True when whitespace-wrapped Linux seeds normalize correctly."""
    _require_imports()
    return get_platform(_sys_platform="  linux  ") == "linux"


def linux_seed_sets_only_linux_predicate() -> bool:
    """Return True when a Linux seed only satisfies the Linux predicate."""
    _require_imports()
    return (
        is_windows(_sys_platform="linux") is False
        and is_linux(_sys_platform="linux") is True
        and is_macos(_sys_platform="linux") is False
    )


def blank_seed_raises_value_error() -> None:
    """Assert blank platform seeds raise ValueError."""
    _require_imports()
    try:
        get_platform(_sys_platform="   ")
    except ValueError:
        return

    raise AssertionError("Expected ValueError was not raised")


def non_string_seed_raises_type_error() -> None:
    """Assert non-string platform seeds raise TypeError."""
    _require_imports()
    try:
        get_platform(_sys_platform=123)  # type: ignore[arg-type]
    except TypeError:
        return

    raise AssertionError("Expected TypeError was not raised")


def windows_cache_seed_maps_x86() -> None:
    """Assert Windows uname cache seeding maps X86 to x86."""
    _require_imports()
    fake_platform = _make_fake_platform_module()
    result = seed_uname_cache_for_windows(
        _sys_platform="win32",
        _environ={"PROCESSOR_ARCHITECTURE": "X86", "COMPUTERNAME": "PC1"},
        _platform_module=fake_platform,
    )
    assert result == "x86", f"Expected 'x86', got {result!r}"
    assert fake_platform._uname_cache.machine == "x86", (
        f"Expected cached machine 'x86', got {fake_platform._uname_cache.machine!r}"
    )


def non_windows_cache_seed_is_no_op() -> None:
    """Assert non-Windows uname cache seeding remains a no-op."""
    _require_imports()
    fake_platform = _make_fake_platform_module()
    result = seed_uname_cache_for_windows(
        _sys_platform="darwin",
        _platform_module=fake_platform,
    )
    assert result is None, f"Expected None, got {result!r}"
    assert fake_platform._uname_cache is None, (
        f"Expected no cache seed, got {fake_platform._uname_cache!r}"
    )
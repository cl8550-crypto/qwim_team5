"""Robot Framework keyword library for _import_helpers tests."""

from __future__ import annotations

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path
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
    from src.utils.data_utils._import_helpers import try_import_module
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
            f"_import_helpers could not be imported: {_import_error_message}"
        )


def module_is_importable() -> bool:
    """Return True if _import_helpers module can be imported."""
    return MODULE_IMPORT_AVAILABLE


def try_import_standard_module_returns_module(module_name: str = "os") -> None:
    """Assert importing a standard module returns a module object."""
    _require_imports()
    result = try_import_module(module_name = str(module_name))
    assert result is not None, f"Expected module object, got None for {module_name!r}"
    assert result.__name__ == str(module_name), (
        f"Expected module name {module_name!r}, got {result.__name__!r}"
    )


def try_import_missing_module_returns_none() -> None:
    """Assert missing modules return None."""
    _require_imports()
    result = try_import_module(module_name = "_qwim_missing_module_xyz_9876")
    assert result is None, f"Expected None for missing module, got {result!r}"


def try_import_whitespace_name_is_normalized() -> None:
    """Assert surrounding whitespace is normalized before import."""
    _require_imports()
    result = try_import_module(module_name = "  sys  ")
    assert result is not None, "Expected module object for normalized whitespace name"
    assert result.__name__ == "sys", f"Expected 'sys', got {result.__name__!r}"


def try_import_blank_module_name_raises_value_error() -> None:
    """Assert blank module names raise ValueError."""
    _require_imports()
    try:
        try_import_module(module_name = "   ")
    except ValueError:
        return

    raise AssertionError("Expected ValueError was not raised")


def try_import_non_string_module_name_raises_type_error() -> None:
    """Assert non-string module names raise TypeError."""
    _require_imports()
    try:
        try_import_module(module_name = 123)  # type: ignore[arg-type]
    except TypeError:
        return

    raise AssertionError("Expected TypeError was not raised")


def try_import_non_callable_importer_raises_type_error() -> None:
    """Assert non-callable importer values raise TypeError."""
    _require_imports()
    try:
        try_import_module(module_name = "os", _importer="bad")  # type: ignore[arg-type]
    except TypeError:
        return

    raise AssertionError("Expected TypeError was not raised")
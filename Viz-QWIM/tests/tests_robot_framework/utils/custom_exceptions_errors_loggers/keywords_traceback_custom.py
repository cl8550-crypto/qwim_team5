"""Robot Framework keyword library for traceback_custom tests."""

from __future__ import annotations

import sys
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
    from src.utils.custom_exceptions_errors_loggers import traceback_custom as tc
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
            f"traceback_custom source module could not be imported: {_import_error_message}"
        )


def module_is_importable() -> bool:
    """Return True when traceback_custom can be imported."""
    return MODULE_IMPORT_AVAILABLE


def compact_format_without_traceback_returns_exception_line() -> bool:
    """Return True when compact formatting without a traceback stays deterministic."""
    _require_imports()
    return (
        tc.Format_Traceback_Compact(exc_type = ValueError, exc_value = ValueError("robot compact"), exc_tb = None)
        == "ValueError: robot compact"
    )


def negative_context_lines_raise_value_error() -> None:
    """Assert negative context widths raise ValueError."""
    _require_imports()
    try:
        tc.Format_Traceback_Context(exc_type = ValueError, exc_value = ValueError("robot"), exc_tb = None, context_lines=-1)
    except ValueError:
        return

    raise AssertionError("Expected ValueError was not raised")


def blank_project_root_raises_value_error() -> None:
    """Assert blank project-root overrides raise ValueError."""
    _require_imports()
    try:
        tc.Extract_Relevant_Frames(exc_tb = object(), project_root="   ")
    except ValueError:
        return

    raise AssertionError("Expected ValueError was not raised")


def non_string_project_root_raises_type_error() -> None:
    """Assert non-string project-root overrides raise TypeError."""
    _require_imports()
    try:
        tc.Extract_Relevant_Frames(exc_tb = object(), project_root=123)  # type: ignore[arg-type]
    except TypeError:
        return

    raise AssertionError("Expected TypeError was not raised")


def normalized_project_root_filters_matching_frames() -> bool:
    """Return True when whitespace-trimmed project roots keep only matching frames."""
    _require_imports()
    project_root = str(Path(__file__).resolve().parent)
    matching_frame = SimpleNamespace(filename=str(Path(project_root) / "inside.py"))
    non_matching_frame = SimpleNamespace(filename="Z:/outside.py")

    original_extract_tb = tc.traceback.extract_tb
    tc.traceback.extract_tb = lambda _exc_tb: [matching_frame, non_matching_frame]
    try:
        relevant_frames = tc.Extract_Relevant_Frames(
            exc_tb = object(),
            project_root=f"  {project_root}  ",
        )
    finally:
        tc.traceback.extract_tb = original_extract_tb

    return relevant_frames == [matching_frame]
"""Robot Framework keyword library for logger_custom tests.

Provides thin Python keyword wrappers testing:
  - get_logger factory
  - Config_Logging Pydantic model
  - Filter functions (filter_audit_events, filter_error_level)
  - Format sinks (format_sink_JSON, format_sink_human_readable)
  - log_function_call decorator factory
  - Performance_Timer context manager

Author:         QWIM Development Team
Version:        0.1.0
Last Modified:  2026-05-27
"""

from __future__ import annotations

import datetime
import json
import os
import time
from pathlib import Path
import sys
from unittest.mock import patch

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
    from src.utils.custom_exceptions_errors_loggers.logger_custom import (
        Config_Logging,
        Performance_Timer,
        _subtab_console_rules,
        _resolve_log_dir_runtime,
        filter_audit_events,
        filter_console_dynamic,
        filter_error_level,
        format_sink_JSON,
        format_sink_human_readable,
        get_logger,
        log_function_call,
        set_console_level_for_subtab,
    )
    import logging as _logging
    _logger_kw = _logging.getLogger(__name__)
except Exception as _exc:  # noqa: BLE001
    MODULE_IMPORT_AVAILABLE = False
    _import_error_message = str(_exc)
    import logging as _logging
    _logger_kw = _logging.getLogger(__name__)
    _logger_kw.warning("Import failed — keywords will raise on use: %s", _exc)


def _require_imports() -> None:
    """Raise RuntimeError when source modules could not be imported."""
    if not MODULE_IMPORT_AVAILABLE:
        raise RuntimeError(
            f"logger_custom source modules could not be imported: {_import_error_message}"
        )


# ---------------------------------------------------------------------------
# Helper — minimal loguru-like record dict
# ---------------------------------------------------------------------------

def _make_record(
    level_name: str = "INFO",
    level_no: int = 20,
    extra: dict | None = None,
    logger_name: str = "test.logger",
) -> dict:
    """Return a minimal record dict compatible with loguru filter/format functions."""
    return {
        "elapsed": datetime.timedelta(seconds=1),
        "exception": None,
        "extra": extra or {},
        "file": type("_F", (), {"name": "test.py", "path": "/test.py"})(),
        "function": "test_func",
        "level": type("_L", (), {"name": level_name, "no": level_no, "icon": "i"})(),
        "line": 1,
        "message": "test message",
        "module": "test_module",
        "name": logger_name,
        "process": type("_P", (), {"id": 1, "name": "Main"})(),
        "thread": type("_T", (), {"id": 1, "name": "MainThread"})(),
        "time": datetime.datetime.now(tz=datetime.timezone.utc),
    }


# ---------------------------------------------------------------------------
# Keywords — get_logger
# ---------------------------------------------------------------------------


def Get_Logger_Returns_Logger_Object(module_name: str = "test_module") -> bool:
    """Return True when get_logger returns a Logger-like object with a debug method.

    Robot keyword: ``Get Logger Returns Logger Object    module_name``
    """
    _require_imports()
    lg = get_logger(name = module_name)
    return hasattr(lg, "debug")


def Get_Logger_Name_Contains_Module(module_name: str = "my_module") -> bool:
    """Return True when the logger name contains *module_name*.

    Robot keyword: ``Get Logger Name Contains Module    module_name``
    """
    _require_imports()
    lg = get_logger(name = module_name)
    return module_name in str(lg)


# ---------------------------------------------------------------------------
# Keywords — Config_Logging
# ---------------------------------------------------------------------------


def Config_Logging_Default_Log_Level() -> str:
    """Return the default log_level value from Config_Logging.

    Robot keyword: ``Config Logging Default Log Level``
    """
    _require_imports()
    cfg = Config_Logging()
    return cfg.log_level


def Config_Logging_Custom_Level_Stored(level: str) -> str:
    """Return the log_level stored when Config_Logging is created with *level*.

    Robot keyword: ``Config Logging Custom Level Stored    DEBUG``
    """
    _require_imports()
    cfg = Config_Logging(log_level=level)
    return cfg.log_level


def Config_Logging_Rejects_Invalid_Level(invalid: str) -> bool:
    """Return True when Config_Logging raises ValidationError for *invalid* level.

    Robot keyword: ``Config Logging Rejects Invalid Level    NONSENSE``
    """
    _require_imports()
    try:
        from pydantic import ValidationError
        Config_Logging(log_level=invalid)
        return False
    except Exception:
        return True


# ---------------------------------------------------------------------------
# Keywords — filter functions
# ---------------------------------------------------------------------------


def Filter_Audit_Events_Passes_Event_Type_Record() -> bool:
    """Return True when filter_audit_events returns True for a record with event_type in extra.

    Robot keyword: ``Filter Audit Events Passes Event Type Record``
    """
    _require_imports()
    record = _make_record(extra={"event_type": "audit"})
    return filter_audit_events(record = record)


def Filter_Audit_Events_Rejects_Plain_Record() -> bool:
    """Return True when filter_audit_events returns False for a plain record.

    Robot keyword: ``Filter Audit Events Rejects Plain Record``
    """
    _require_imports()
    record = _make_record(extra={})
    return not filter_audit_events(record = record)


def Filter_Error_Level_Passes_Error_Record() -> bool:
    """Return True when filter_error_level returns True for level 40 (ERROR).

    Robot keyword: ``Filter Error Level Passes Error Record``
    """
    _require_imports()
    record = _make_record(level_name="ERROR", level_no=40)
    return filter_error_level(record = record)


def Filter_Error_Level_Rejects_Info_Record() -> bool:
    """Return True when filter_error_level returns False for level 20 (INFO).

    Robot keyword: ``Filter Error Level Rejects Info Record``
    """
    _require_imports()
    record = _make_record(level_name="INFO", level_no=20)
    return not filter_error_level(record = record)


def Most_Specific_Console_Prefix_Allows_Debug_Record() -> bool:
    """Return True when the most specific matching prefix allows DEBUG output."""
    _require_imports()
    broader_prefix = "src.dashboard"
    specific_prefix = "src.dashboard.shiny_tab_portfolios.subtab_portfolios_comparison"
    module_name = f"{specific_prefix}.helper"
    _subtab_console_rules.clear()
    try:
        set_console_level_for_subtab(_subtab_key = "dashboard", module_prefix = broader_prefix, level_key = "info")
        set_console_level_for_subtab(_subtab_key = "portfolio_comparison", module_prefix = specific_prefix, level_key = "debug")
        record = _make_record(
            level_name="DEBUG",
            level_no=10,
            extra={"name": module_name},
            logger_name=module_name,
        )
        return filter_console_dynamic(record = record)
    finally:
        _subtab_console_rules.clear()


def Most_Specific_Console_Prefix_Blocks_Info_Record() -> bool:
    """Return True when the most specific DEBUG-only prefix blocks INFO output."""
    _require_imports()
    broader_prefix = "src.dashboard"
    specific_prefix = "src.dashboard.shiny_tab_portfolios.subtab_portfolios_comparison"
    module_name = f"{specific_prefix}.helper"
    _subtab_console_rules.clear()
    try:
        set_console_level_for_subtab(_subtab_key = "dashboard", module_prefix = broader_prefix, level_key = "info")
        set_console_level_for_subtab(_subtab_key = "portfolio_comparison", module_prefix = specific_prefix, level_key = "debug")
        record = _make_record(
            level_name="INFO",
            level_no=20,
            extra={"name": module_name},
            logger_name=module_name,
        )
        return not filter_console_dynamic(record = record)
    finally:
        _subtab_console_rules.clear()


# ---------------------------------------------------------------------------
# Keywords — format sinks
# ---------------------------------------------------------------------------


def Format_Sink_JSON_Returns_Valid_JSON() -> bool:
    """Return True when format_sink_JSON produces parseable JSON.

    Robot keyword: ``Format Sink JSON Returns Valid JSON``
    """
    _require_imports()
    record = _make_record()
    try:
        result = format_sink_JSON(record = record)
        json.loads(result)
        return True
    except (json.JSONDecodeError, TypeError):
        return False


def Format_Sink_Human_Readable_Returns_String() -> bool:
    """Return True when format_sink_human_readable produces a non-empty string.

    Robot keyword: ``Format Sink Human Readable Returns String``
    """
    _require_imports()
    record = _make_record()
    result = format_sink_human_readable(record = record)
    return isinstance(result, str) and len(result) > 0


# ---------------------------------------------------------------------------
# Keywords — log_function_call
# ---------------------------------------------------------------------------


def Log_Function_Call_Returns_Correct_Value() -> int:
    """Return the value of a decorated function that returns 42.

    Robot keyword: ``Log Function Call Returns Correct Value``
    """
    _require_imports()

    @log_function_call()
    def _returns_42() -> int:
        return 42

    return _returns_42()


def Log_Function_Call_Propagates_Exception() -> bool:
    """Return True when a decorated function's ValueError is propagated.

    Robot keyword: ``Log Function Call Propagates Exception``
    """
    _require_imports()

    @log_function_call()
    def _raises() -> None:
        raise ValueError("Propagated error")

    try:
        _raises()
        return False
    except ValueError:
        return True


# ---------------------------------------------------------------------------
# Keywords — Performance_Timer
# ---------------------------------------------------------------------------


def Performance_Timer_Elapsed_Is_Non_Negative_Float() -> float:
    """Run Performance_Timer and return elapsed_ms converted to seconds.

    Robot keyword: ``Performance Timer Elapsed Is Non Negative Float``
    """
    _require_imports()
    with Performance_Timer(operation_name="rf_test") as timer:
        time.sleep(0)
    return timer.elapsed_ms / 1000.0


def Resolve_String_Default_Log_Dir_For_Windows_Worker(
    worker_id: str = "gw9",
) -> str:
    """Return the normalized runtime log-dir path for a Windows pytest worker."""
    _require_imports()
    with patch(
        "src.utils.custom_exceptions_errors_loggers._logger_handlers.sys.platform",
        "win32",
    ):
        with patch.dict(os.environ, {"PYTEST_XDIST_WORKER": worker_id}, clear=False):
            result = _resolve_log_dir_runtime(log_dir = "logs")

    return result.as_posix()


def Blank_Log_Dir_Raises_Value_Error() -> None:
    """Assert blank string log dirs raise ValueError."""
    _require_imports()
    try:
        _resolve_log_dir_runtime(log_dir = "   ")
    except ValueError:
        return

    raise AssertionError("Expected ValueError was not raised")


# ---------------------------------------------------------------------------
# Generic assertion helpers
# ---------------------------------------------------------------------------


def Boolean_Should_Be_True(value: bool) -> None:
    """Assert *value* is True.

    Robot keyword: ``Boolean Should Be True    ${value}``
    """
    if not value:
        raise AssertionError(f"Expected True, got {value!r}")


def Integer_Should_Equal(actual: int, expected: int) -> None:
    """Assert *actual* == *expected*.

    Robot keyword: ``Integer Should Equal    ${actual}    ${expected}``
    """
    if int(actual) != int(expected):
        raise AssertionError(f"Expected {expected}, got {actual}")


def Float_Should_Be_Non_Negative(value: float) -> None:
    """Assert *value* >= 0.0.

    Robot keyword: ``Float Should Be Non Negative    ${value}``
    """
    if float(value) < 0.0:
        raise AssertionError(f"Expected non-negative float, got {value!r}")


def String_Should_Equal(actual: str, expected: str) -> None:
    """Assert *actual* == *expected*.

    Robot keyword: ``String Should Equal    ${actual}    ${expected}``
    """
    if str(actual) != str(expected):
        raise AssertionError(f"Expected {expected!r}, got {actual!r}")

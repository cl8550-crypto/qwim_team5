"""Behave step definitions for logger_custom feature.

Covers:
  - get_logger — basic functionality and distinct instances
  - Config_Logging — Pydantic validation (valid and invalid log levels)
  - Filter functions (filter_audit_events, filter_error_level)
  - Format functions (format_sink_JSON, format_sink_human_readable)
  - log_function_call decorator (return value, exception propagation)
  - Performance_Timer context manager

Author:         QWIM Development Team
Version:        0.1.0
Last Modified:  2026-05-27
"""

from __future__ import annotations

import io
import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import patch

from behave import given, then, when

# ---------------------------------------------------------------------------
# Project root on sys.path
# ---------------------------------------------------------------------------
_PROJECT_ROOT: Path = Path(__file__).resolve().parents[4]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# ---------------------------------------------------------------------------
# sys.stderr patch
# ---------------------------------------------------------------------------
if not hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Module-level import guard
# ---------------------------------------------------------------------------
MODULE_IMPORT_AVAILABLE: bool = True
_import_error_message: str = ""

try:
    from pydantic import ValidationError

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
except Exception as _exc:
    MODULE_IMPORT_AVAILABLE = False
    _import_error_message = str(_exc)
    ValidationError = Exception  # type: ignore[assignment,misc]


def _require_imports() -> None:
    """Raise RuntimeError when source modules could not be imported."""
    if not MODULE_IMPORT_AVAILABLE:
        raise RuntimeError(
            f"logger_custom modules could not be imported: {_import_error_message}"
        )


def _make_record(
    *,
    message: str = "test",
    level_name: str = "INFO",
    level_no: int = 20,
    extra: dict | None = None,
    logger_name: str = "test.logger",
) -> dict:
    """Build a minimal loguru-compatible record dict for filter/format tests."""
    import datetime

    return {
        "elapsed": datetime.timedelta(seconds=1),
        "exception": None,
        "extra": extra or {},
        "file": type("_F", (), {"name": "test.py", "path": "test.py"})(),
        "function": "test_function",
        "level": type("_L", (), {"name": level_name, "no": level_no, "icon": "ℹ"})(),
        "line": 1,
        "message": message,
        "module": "test_module",
        "name": logger_name,
        "process": type("_P", (), {"id": 1, "name": "MainProcess"})(),
        "thread": type("_T", (), {"id": 1, "name": "MainThread"})(),
        "time": datetime.datetime.now(tz=datetime.timezone.utc),
    }


# ===========================================================================
# Given steps
# ===========================================================================


@given("the logger_custom module is importable")
def step_given_logger_custom_importable(context) -> None:
    """Verify logger_custom loaded successfully."""
    _require_imports()
    _subtab_console_rules.clear()
    context.logger_a = None
    context.logger_b = None
    context.log_config = None
    context.filter_result = None
    context.format_result = None
    context.record = None
    context.validation_error_raised = False


# ===========================================================================
# When steps — get_logger
# ===========================================================================


@when('I call get_logger with name "{name}"')
def step_call_get_logger(context, name: str) -> None:
    """Call get_logger and store the result."""
    _require_imports()
    logger = get_logger(name = name)
    if context.logger_a is None:
        context.logger_a = logger
    else:
        context.logger_b = logger


# ===========================================================================
# When steps — Config_Logging
# ===========================================================================


@when('I construct a Config_Logging with log_level "{level}"')
def step_construct_config_logging(context, level: str) -> None:
    """Construct a Config_Logging object and capture any ValidationError."""
    _require_imports()
    try:
        context.log_config = Config_Logging(log_level=level)
        context.validation_error_raised = False
    except (ValueError, ValidationError):
        context.validation_error_raised = True
        context.log_config = None


# ===========================================================================
# When steps — filter functions
# ===========================================================================


@when('I create a log record with extra tag "{tag}"')
def step_create_record_with_tag(context, tag: str) -> None:
    """Create a log record whose extra dict contains the given tag."""
    _require_imports()
    if tag == "AUDIT":
        # filter_audit_events checks for "event_type" key in extra
        context.record = _make_record(extra={"event_type": "audit"})
    else:
        context.record = _make_record(extra={})


@when("I apply filter_audit_events to it")
def step_apply_filter_audit(context) -> None:
    """Apply filter_audit_events and store the result."""
    _require_imports()
    context.filter_result = filter_audit_events(record = context.record)


@when('I create a log record at level "{level}"')
def step_create_record_at_level(context, level: str) -> None:
    """Create a log record at the specified level."""
    _require_imports()
    level_map = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50}
    level_no = level_map.get(level.upper(), 20)
    context.record = _make_record(level_name=level.upper(), level_no=level_no)


@when("I apply filter_error_level to it")
def step_apply_filter_error_level(context) -> None:
    """Apply filter_error_level and store the result."""
    _require_imports()
    context.filter_result = filter_error_level(record = context.record)


@when(
    'I register logger console rules "{broader_prefix}" as "{broader_level}" and "{specific_prefix}" as "{specific_level}"'
)
def step_register_logger_console_rules(
    context,
    broader_prefix: str,
    broader_level: str,
    specific_prefix: str,
    specific_level: str,
) -> None:
    """Register overlapping console rules for the current scenario."""
    _require_imports()
    _subtab_console_rules.clear()
    set_console_level_for_subtab(_subtab_key = "dashboard", module_prefix = broader_prefix, level_key = broader_level)
    set_console_level_for_subtab(_subtab_key = "subtab", module_prefix = specific_prefix, level_key = specific_level)


@when('I apply filter_console_dynamic to a "{level}" log record for module "{module_name}"')
def step_apply_filter_console_dynamic(
    context,
    level: str,
    module_name: str,
) -> None:
    """Apply filter_console_dynamic to a record for the specified module."""
    _require_imports()
    level_map = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50}
    level_name = level.upper()
    context.record = _make_record(
        level_name=level_name,
        level_no=level_map[level_name],
        extra={"name": module_name},
        logger_name=module_name,
    )
    context.filter_result = filter_console_dynamic(record = context.record)


# ===========================================================================
# When steps — format functions
# ===========================================================================


@when('I format a log record with message "{message}" using format_sink_JSON')
def step_format_record_json(context, message: str) -> None:
    """Format a record with format_sink_JSON."""
    _require_imports()
    record = _make_record(message=message)
    context.format_result = format_sink_JSON(record = record)


@when('I format a log record with message "{message}" using format_sink_human_readable')
def step_format_record_human(context, message: str) -> None:
    """Format a record with format_sink_human_readable."""
    _require_imports()
    record = _make_record(message=message)
    context.format_result = format_sink_human_readable(record = record)


# ===========================================================================
# When steps — log_function_call decorator
# ===========================================================================


@when("I apply log_function_call to a function that returns 42")
def step_apply_log_function_call_returns_42(context) -> None:
    """Decorate a function that returns 42."""
    _require_imports()

    @log_function_call()
    def _returns_42() -> int:
        return 42

    context.decorated_func = _returns_42
    context.expected_return = 42


@when("I call that decorated function")
def step_call_decorated_function(context) -> None:
    """Call the decorated function and store its return value."""
    context.actual_return = context.decorated_func()


@when("I apply log_function_call to a function that raises ValueError")
def step_apply_log_function_call_raises(context) -> None:
    """Decorate a function that raises ValueError."""
    _require_imports()

    @log_function_call()
    def _raises_value_error() -> None:
        raise ValueError("Propagated error")

    context.raising_func = _raises_value_error


# ===========================================================================
# When steps — Performance_Timer
# ===========================================================================


@when("I use Performance_Timer as a context manager")
def step_use_performance_timer(context) -> None:
    """Run Performance_Timer and capture elapsed_ms."""
    _require_imports()
    with Performance_Timer(operation_name="behave_test") as timer:
        time.sleep(0)  # zero-length sleep for determinism
    context.elapsed = timer.elapsed_ms / 1000.0  # convert ms → seconds


@when(
    'I resolve logger runtime log dir from string default "{log_dir_name}" for worker "{worker_id}" on Windows'
)
def step_resolve_logger_runtime_log_dir_for_worker(
    context,
    log_dir_name: str,
    worker_id: str,
) -> None:
    """Resolve the runtime log directory for a Windows pytest worker."""
    _require_imports()
    with patch(
        "src.utils.custom_exceptions_errors_loggers._logger_handlers.sys.platform",
        "win32",
    ):
        with patch.dict(os.environ, {"PYTEST_XDIST_WORKER": worker_id}, clear=False):
            context.runtime_log_dir = _resolve_log_dir_runtime(log_dir = log_dir_name)
    context.raised = None


@when("I resolve logger runtime log dir from a blank string")
def step_resolve_logger_runtime_log_dir_blank_string(context) -> None:
    """Resolve the runtime log directory for a blank string input."""
    _require_imports()
    context.runtime_log_dir = None
    context.raised = None
    try:
        context.runtime_log_dir = _resolve_log_dir_runtime(log_dir = "   ")
    except ValueError as exc:
        context.raised = exc


# ===========================================================================
# Then steps
# ===========================================================================


@then("the returned logger should be non-null")
def step_logger_non_null(context) -> None:
    """Assert logger_a is not None."""
    assert context.logger_a is not None, "get_logger returned None"


@then("the two loggers should be different objects")
def step_loggers_are_different(context) -> None:
    """Assert the two loggers are distinct."""
    assert context.logger_a is not context.logger_b, (
        "Expected two distinct logger instances"
    )


@then('the config log_level should be "{expected}"')
def step_config_log_level(context, expected: str) -> None:
    """Assert Config_Logging.log_level equals expected."""
    assert context.log_config is not None, "Config_Logging construction failed"
    assert context.log_config.log_level == expected, (
        f"Expected log_level={expected!r}, got {context.log_config.log_level!r}"
    )


@then("a validation error should be raised")
def step_validation_error_raised(context) -> None:
    """Assert that constructing Config_Logging raised a validation error."""
    assert context.validation_error_raised, (
        "Expected a ValidationError to be raised for an invalid log level"
    )


@then("the filter result should be True")
def step_filter_true(context) -> None:
    """Assert the stored filter result is True."""
    assert context.filter_result is True, (
        f"Expected filter result True, got {context.filter_result!r}"
    )


@then("the filter result should be False")
def step_filter_false(context) -> None:
    """Assert the stored filter result is False."""
    assert context.filter_result is False, (
        f"Expected filter result False, got {context.filter_result!r}"
    )


@then("the formatted output should be valid JSON")
def step_formatted_json_valid(context) -> None:
    """Assert format_result is valid JSON."""
    try:
        json.loads(context.format_result)
    except (json.JSONDecodeError, TypeError) as exc:
        raise AssertionError(
            f"format_sink_JSON did not produce valid JSON: {exc}"
        ) from exc


@then("the formatted output should be a non-empty string")
def step_formatted_non_empty(context) -> None:
    """Assert format_result is a non-empty string."""
    assert isinstance(context.format_result, str) and len(context.format_result) > 0, (
        f"Expected non-empty string, got {context.format_result!r}"
    )


@then("the return value should be 42")
def step_return_value_42(context) -> None:
    """Assert the decorated function returned 42."""
    assert context.actual_return == 42, (
        f"Expected 42, got {context.actual_return!r}"
    )


@then("calling the decorated function should re-raise ValueError")
def step_raises_value_error(context) -> None:
    """Assert the decorated function re-raises ValueError."""
    raised = False
    try:
        context.raising_func()
    except ValueError:
        raised = True
    assert raised, "Expected ValueError to be re-raised by decorated function"


@then("elapsed_seconds should be a non-negative float")
def step_elapsed_non_negative(context) -> None:
    """Assert elapsed_seconds is a non-negative float."""
    assert isinstance(context.elapsed, float), (
        f"Expected float elapsed_seconds, got {type(context.elapsed)}"
    )
    assert context.elapsed >= 0.0, (
        f"Expected non-negative elapsed_seconds, got {context.elapsed}"
    )


@then('the logger runtime log dir should be "{expected_path}"')
def step_logger_runtime_log_dir_equals(context, expected_path: str) -> None:
    """Assert the resolved runtime log dir matches the expected path."""
    assert context.runtime_log_dir is not None, "Expected a resolved runtime log dir"
    normalized_runtime_log_dir = str(context.runtime_log_dir).replace("\\", "/")
    assert normalized_runtime_log_dir == expected_path, (
        f"Expected runtime log dir {expected_path!r}, got {normalized_runtime_log_dir!r}"
    )


@then("a logger_custom ValueError should be raised")
def step_logger_custom_value_error_raised(context) -> None:
    """Assert the previous logger_custom step raised ValueError."""
    assert isinstance(context.raised, ValueError), (
        f"Expected ValueError, got {type(context.raised)}: {context.raised}"
    )

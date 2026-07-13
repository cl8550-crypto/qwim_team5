"""Log formatters, filters, and configuration for QWIM Projects.

This private module provides Pydantic configuration, JSON serialization
utilities, human-readable sink formatters, and filter functions for
log routing.  It also manages the per-subtab console filter state.

All public symbols are re-exported by the parent façade module
:mod:`src.utils.custom_exceptions_errors_loggers.logger_custom`.

Do **not** import directly from this module; always import from
``logger_custom``.
"""

from __future__ import annotations

import json

from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, ParamSpec, TypeVar

from pydantic import BaseModel, ConfigDict

from ._exception_types_lightweight import SENSITIVE_FIELDS


# ==============================================================================
# Type Aliases (Python 3.12+)
# ==============================================================================

type Log_Record_Dict = dict[str, Any]
type Log_Filter_Func = Callable[[Log_Record_Dict], bool]
type Log_Format_Func = Callable[[Log_Record_Dict], str]

P = ParamSpec("P")
R = TypeVar("R")


# ==============================================================================
# Constants
# ==============================================================================

DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_DIR = Path("logs")
DEFAULT_ROTATION_SIZE = "100 MB"
DEFAULT_RETENTION_DAYS_APPLICATION = "90 days"
DEFAULT_RETENTION_DAYS_AUDIT = "2555 days"  # ~7 years for regulatory compliance
DEFAULT_RETENTION_DAYS_ERROR = "365 days"  # 1 year
DEFAULT_RETENTION_DAYS_PERFORMANCE = "30 days"

# Log file names
LOG_FILE_APPLICATION = "application.log"
LOG_FILE_AUDIT = "audit.log"
LOG_FILE_ERROR = "error.log"
LOG_FILE_PERFORMANCE = "performance.log"
LOG_FILE_DEBUG = "debug.log"

# Log level thresholds (loguru uses numeric values)
LOG_LEVEL_DEBUG = 10
LOG_LEVEL_INFO = 20
LOG_LEVEL_WARNING = 30
LOG_LEVEL_ERROR = 40
MASKED_LOG_VALUE = "***MASKED***"
MAX_LOG_SANITIZE_DEPTH = 6


# ==============================================================================
# Configuration Model
# ==============================================================================

# Valid choices are encoded as ``Literal`` types so Pydantic rejects invalid
# values with a structured ``ValidationError`` at construction time.
LOG_LEVEL_CHOICES = ("TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL")
ENVIRONMENT_CHOICES = ("development", "staging", "production")


class Config_Logging(BaseModel):
    """Pydantic configuration model for logging setup.

    Validation is performed at construction time: invalid ``log_level`` or
    ``environment`` values and any unknown keyword arguments raise
    :class:`pydantic.ValidationError`.

    Attributes
    ----------
    log_level : str
        Minimum log level (TRACE, DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL).
    environment : str
        Deployment environment (development, staging, production).
    log_dir : Path
        Directory for log files.
    enable_console : bool
        Whether to log to console.
    enable_JSON : bool
        Whether to use JSON format for file logs.
    rotation_size : str
        Size threshold for log rotation.
    """

    model_config = ConfigDict(extra="forbid")

    log_level: Literal[LOG_LEVEL_CHOICES] = DEFAULT_LOG_LEVEL  # type: ignore[valid-type]
    environment: Literal[ENVIRONMENT_CHOICES] = "development"  # type: ignore[valid-type]
    log_dir: Path = DEFAULT_LOG_DIR
    enable_console: bool = True
    enable_JSON: bool = True
    rotation_size: str = DEFAULT_ROTATION_SIZE


# ==============================================================================
# JSON Serialization Utilities
# ==============================================================================


def _is_sensitive_key(*, key: Any) -> bool:
    """Return whether a key name should be masked in structured logs.

    Parameters
    ----------
    key : Any
        Mapping key to inspect.

    Returns
    -------
    bool
        ``True`` when the key text matches a configured sensitive field.
    """
    key_lower = str(key).lower()
    return any(sensitive_field in key_lower for sensitive_field in SENSITIVE_FIELDS)


def _sanitize_for_logging(
    *, value: Any, depth_remaining: int, seen_object_ids: set[int]) -> Any:
    """Recursively sanitize values before attaching them to structured logs.

    Parameters
    ----------
    value : Any
        Value to sanitize.
    depth_remaining : int
        Remaining recursion budget.
    seen_object_ids : set[int]
        Identities already visited in the current traversal.

    Returns
    -------
    Any
        Sanitized value suitable for JSON serialization.
    """
    if depth_remaining < 0:
        return str(value)

    if value is None or isinstance(value, (str, int, float, bool, datetime, Path)):
        return value

    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")

    object_id = id(value)
    if object_id in seen_object_ids:
        return "<cycle>"

    if isinstance(value, Mapping):
        seen_object_ids.add(object_id)
        sanitized_mapping = {
            key: MASKED_LOG_VALUE
            if _is_sensitive_key(key = key)
            else _sanitize_for_logging(
                value = item_value,
                depth_remaining = depth_remaining - 1,
                seen_object_ids = seen_object_ids,
            )
            for key, item_value in value.items()
        }
        seen_object_ids.discard(object_id)
        return sanitized_mapping

    if isinstance(value, list):
        seen_object_ids.add(object_id)
        sanitized_list = [
            _sanitize_for_logging(
                value = item_value,
                depth_remaining = depth_remaining - 1,
                seen_object_ids = seen_object_ids,
            )
            for item_value in value
        ]
        seen_object_ids.discard(object_id)
        return sanitized_list

    if isinstance(value, tuple):
        seen_object_ids.add(object_id)
        sanitized_tuple = tuple(
            _sanitize_for_logging(
                value = item_value,
                depth_remaining = depth_remaining - 1,
                seen_object_ids = seen_object_ids,
            )
            for item_value in value
        )
        seen_object_ids.discard(object_id)
        return sanitized_tuple

    if isinstance(value, (set, frozenset)):
        seen_object_ids.add(object_id)
        sanitized_set = [
            _sanitize_for_logging(
                value = item_value,
                depth_remaining = depth_remaining - 1,
                seen_object_ids = seen_object_ids,
            )
            for item_value in value
        ]
        seen_object_ids.discard(object_id)
        return sanitized_set

    if hasattr(value, "__dict__"):
        seen_object_ids.add(object_id)
        sanitized_object = _sanitize_for_logging(
            value = vars(value),
            depth_remaining = depth_remaining - 1,
            seen_object_ids = seen_object_ids,
        )
        seen_object_ids.discard(object_id)
        return sanitized_object

    return str(value)


def sanitize_for_logging(
    *, value: Any, max_depth: int = MAX_LOG_SANITIZE_DEPTH) -> Any:
    """Return a sanitized copy of a value for structured logging.

    Parameters
    ----------
    value : Any
        Value that may contain nested secrets.
    max_depth : int
        Maximum recursion depth used for nested containers. Boolean values use
        the default recursion path.

    Returns
    -------
    Any
        Sanitized value with sensitive mapping keys masked.
    """
    if isinstance(max_depth, bool):
        max_depth = MAX_LOG_SANITIZE_DEPTH

    return _sanitize_for_logging(
        value = value,
        depth_remaining = max_depth,
        seen_object_ids = set(),
    )


def serialize_for_JSON(*, obj: Any) -> Any:
    """Serialize objects for JSON output.

    Parameters
    ----------
    obj : Any
        Object to serialize.

    Returns
    -------
    Any
        JSON-serializable representation of the object.
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, bytes):
        return obj.decode("utf-8", errors="replace")
    if hasattr(obj, "__dict__"):
        return sanitize_for_logging(value = vars(obj))
    return str(obj)


def format_record_as_JSON(record: dict) -> str:
    """Format a loguru record as JSON string.

    Parameters
    ----------
    record : dict
        Loguru record dictionary.

    Returns
    -------
    str
        JSON-formatted log string.
    """
    # Extract timestamp with UTC
    timestamp = record["time"].astimezone(UTC).isoformat()

    # Build base log entry
    log_entry = {
        "timestamp": timestamp,
        "level": record["level"].name,
        "logger": record["name"] or "root",
        "module": record["module"],
        "function": record["function"],
        "line": record["line"],
        "message": record["message"],
    }

    # Add thread/process info for debugging
    if record["level"].no >= LOG_LEVEL_DEBUG:  # DEBUG level or higher
        log_entry["thread_id"] = record["thread"].id
        log_entry["thread_name"] = record["thread"].name
        log_entry["process_id"] = record["process"].id
        log_entry["process_name"] = record["process"].name

    # Add exception info if present
    if record["exception"] is not None:
        log_entry["exception"] = {
            "type": record["exception"].type.__name__ if record["exception"].type else None,
            "value": str(record["exception"].value) if record["exception"].value else None,
            "traceback": record["exception"].traceback or None,
        }

    # Add extra fields from logger.bind() or extra dict
    extra = record.get("extra", {})
    if extra:
        for key, value in extra.items():
            if key not in log_entry:
                log_entry[key] = sanitize_for_logging(value = value)

    return json.dumps(log_entry, default=serialize_for_JSON)


def format_sink_JSON(record: dict) -> str:
    """Sink format function for JSON output.

    Parameters
    ----------
    record : dict
        Loguru record dictionary.

    Returns
    -------
    str
        Formatted JSON string with newline.
    """
    return format_record_as_JSON(record = record) + "\n"


def format_sink_human_readable(record: dict) -> str:
    """Sink format function for human-readable console output.

    Parameters
    ----------
    record : dict
        Loguru record dictionary.

    Returns
    -------
    str
        Human-readable formatted string.
    """
    timestamp = record["time"].strftime("%Y-%m-%d %H:%M:%S")
    level = record["level"].name
    module = record["module"]
    function = record["function"]
    line = record["line"]
    message = record["message"]

    # Escape angle brackets to prevent loguru colorizer from parsing them as color tags
    module = module.replace("<", "\\<").replace(">", "\\>")
    function = function.replace("<", "\\<").replace(">", "\\>")
    message = message.replace("<", "\\<").replace(">", "\\>")

    return f"{timestamp} | {level:<8} | {module}:{function}:{line} | {message}\n"


# ==============================================================================
# Filter Functions for Log Routing
# ==============================================================================


def filter_audit_events(record: dict) -> bool:
    """Filter for audit trail events only.

    Parameters
    ----------
    record : dict
        Loguru record dictionary.

    Returns
    -------
    bool
        True if record is an audit event.
    """
    extra = record.get("extra", {})
    return "event_type" in extra


def filter_performance_events(record: dict) -> bool:
    """Filter for performance metrics events only.

    Parameters
    ----------
    record : dict
        Loguru record dictionary.

    Returns
    -------
    bool
        True if record contains performance metrics.
    """
    extra = record.get("extra", {})
    return "execution_time_ms" in extra


def filter_error_level(record: dict) -> bool:
    """Filter for ERROR level and above.

    Parameters
    ----------
    record : dict
        Loguru record dictionary.

    Returns
    -------
    bool
        True if record is ERROR or CRITICAL level.
    """
    return record["level"].no >= LOG_LEVEL_ERROR  # ERROR = 40, CRITICAL = 50


def filter_console_dynamic(record: dict) -> bool:
    """Console sink filter that gates DEBUG/INFO output per-subtab.

    WARNING and above always pass through unconditionally.  For DEBUG
    and INFO messages, the record is allowed only when its logger name
    (dotted module path) starts with a prefix registered via
    :func:`set_console_level_for_subtab` **and** the log level matches
    the rule for that prefix.

    Level semantics
    ---------------
    ``"debug"``      — pass DEBUG-only messages (level 10).
    ``"info"``       — pass INFO-only messages (level 20).
    ``"info_debug"`` — pass both DEBUG and INFO messages (levels 10-20).

    When multiple registered prefixes match the same logger name, the
    longest matching prefix wins so specific subtab rules override broader
    dashboard defaults.

    Parameters
    ----------
    record : dict
        Loguru record dictionary.

    Returns
    -------
    bool
        ``True`` if the record should be written to the console sink.
    """
    level_no: int = record["level"].no
    # WARNING (30), ERROR (40), CRITICAL (50) always pass through
    if level_no >= LOG_LEVEL_WARNING:
        return True
    # DEBUG (10) and INFO (20): apply the most specific per-subtab rule
    module_name: str = record["extra"].get("name") or record.get("name") or ""
    matching_level_key = None
    matching_prefix_length = -1
    for prefix, level_key in _subtab_console_rules.items():
        if module_name.startswith(prefix) and len(prefix) > matching_prefix_length:
            matching_level_key = level_key
            matching_prefix_length = len(prefix)

    if matching_level_key == "debug":
        return level_no == LOG_LEVEL_DEBUG
    if matching_level_key == "info":
        return level_no == LOG_LEVEL_INFO
    if matching_level_key == "info_debug":
        return level_no <= LOG_LEVEL_INFO  # DEBUG and INFO both <= 20
    return False


# ---------------------------------------------------------------------------
# Per-subtab console filter state
# ---------------------------------------------------------------------------
# Maps dotted module-path prefix -> active level key for that subtab.
# Managed exclusively by :func:`set_console_level_for_subtab`.
_subtab_console_rules: dict[str, str] = {}


def set_console_level_for_subtab(
    *, _subtab_key: str, module_prefix: str, level_key: str) -> None:
    """Register or clear a per-subtab console logging rule.

    Called from :mod:`subtab_computation` whenever the user changes the
    **Logger Display** dropdown in the Developer / Debug Options table.
    The change takes effect immediately for all subsequent log calls
    because :func:`filter_console_dynamic` reads ``_subtab_console_rules``
    at call time — no logger restart is required.

    Parameters
    ----------
    _subtab_key : str
        Human-readable identifier for traceability
        (e.g. ``"portfolio_comparison"``).  Not used for filtering.
    module_prefix : str
        Dotted module path prefix that owns this subtab's log records
        (e.g.
        ``"src.dashboard.shiny_tab_portfolios.subtab_portfolios_comparison"``).
    level_key : str
        One of ``"no_display"``, ``"debug"``, ``"info"``,
        ``"info_debug"``.
        Passing ``"no_display"`` removes the prefix from active rules,
        silencing that subtab's DEBUG/INFO console output.

    Returns
    -------
    None
    """
    import sys
    print(f"[DIAG] set_console_level_for_subtab: _subtab_key={_subtab_key}, module_prefix={module_prefix}, level_key={level_key}", file=sys.stderr, flush=True)
    if level_key == "no_display":
        _subtab_console_rules.pop(module_prefix, None)
    else:
        _subtab_console_rules[module_prefix] = level_key
        print(f"[DIAG] Registered rule: {module_prefix} -> {level_key}", file=sys.stderr, flush=True)


# ==============================================================================
# Module Exports
# ==============================================================================

__all__ = [
    "DEFAULT_LOG_DIR",
    "DEFAULT_LOG_LEVEL",
    "DEFAULT_RETENTION_DAYS_APPLICATION",
    "DEFAULT_RETENTION_DAYS_AUDIT",
    "DEFAULT_RETENTION_DAYS_ERROR",
    "DEFAULT_RETENTION_DAYS_PERFORMANCE",
    "DEFAULT_ROTATION_SIZE",
    "LOG_FILE_APPLICATION",
    "LOG_FILE_AUDIT",
    "LOG_FILE_DEBUG",
    "LOG_FILE_ERROR",
    "LOG_FILE_PERFORMANCE",
    "LOG_LEVEL_DEBUG",
    "LOG_LEVEL_ERROR",
    "LOG_LEVEL_INFO",
    "LOG_LEVEL_WARNING",
    "MASKED_LOG_VALUE",
    "MAX_LOG_SANITIZE_DEPTH",
    "Config_Logging",
    "Log_Filter_Func",
    "Log_Format_Func",
    "Log_Record_Dict",
    "P",
    "R",
    "_subtab_console_rules",
    "filter_audit_events",
    "filter_console_dynamic",
    "filter_error_level",
    "filter_performance_events",
    "format_record_as_JSON",
    "format_sink_JSON",
    "format_sink_human_readable",
    "sanitize_for_logging",
    "serialize_for_JSON",
    "set_console_level_for_subtab",
]

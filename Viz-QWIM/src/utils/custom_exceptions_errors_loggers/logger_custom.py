"""Custom Logger Module.

This module configures logging to meet regulatory requirements for financial applications.

Features
--------
- Structured logging with timestamps using loguru
- Multiple log files by severity and purpose
- Automatic rotation with retention policies
- Audit trail capabilities for compliance

The module uses loguru and loggerplusplus instead of Python's built-in logging
to provide more powerful and flexible logging capabilities.

Classes
-------
Formatter_Structured_JSON
    JSON formatter for structured logging with audit trail support.
Audit_Logger
    Specialized logger for audit trail events with compliance support.

Functions
---------
setup_logging
    Configure application-wide logging with multiple handlers.
get_logger
    Get a configured logger instance.
log_calculation
    Log financial calculations for audit trail.
log_data_access
    Log data access operations for compliance.

Example
-------
>>> from src.utils.custom_exceptions_errors_loggers.logger_custom import setup_logging, get_logger
>>> setup_logging(log_level="INFO", environment="production")
>>> logger = get_logger(__name__)
>>> logger.info("Application started")

Notes
-----
This module must be initialized once at application startup before any logging occurs.
All timestamps are in UTC for consistency across deployments.

Author: PRPB Dashboard Team
Version: 1.1.0
Last Updated: 2026-02-09
"""

from __future__ import annotations

from ._logger_decorators import (
    log_function_call,
)

# ---------------------------------------------------------------------------
# Facade imports -- all public symbols re-exported from private sub-modules.
# Callers always import from this module; never import from the private ones.
# ---------------------------------------------------------------------------
from ._logger_formatters import (
    DEFAULT_LOG_DIR,
    DEFAULT_LOG_LEVEL,
    DEFAULT_RETENTION_DAYS_APPLICATION,
    DEFAULT_RETENTION_DAYS_AUDIT,
    DEFAULT_RETENTION_DAYS_ERROR,
    DEFAULT_RETENTION_DAYS_PERFORMANCE,
    DEFAULT_ROTATION_SIZE,
    LOG_FILE_APPLICATION,
    LOG_FILE_AUDIT,
    LOG_FILE_DEBUG,
    LOG_FILE_ERROR,
    LOG_FILE_PERFORMANCE,
    LOG_LEVEL_DEBUG,
    LOG_LEVEL_ERROR,
    LOG_LEVEL_INFO,
    LOG_LEVEL_WARNING,
    Config_Logging,
    Log_Filter_Func,
    Log_Format_Func,
    Log_Record_Dict,
    _subtab_console_rules,
    filter_audit_events,
    filter_console_dynamic,
    filter_error_level,
    filter_performance_events,
    format_record_as_JSON,
    format_sink_human_readable,
    format_sink_JSON,
    sanitize_for_logging,
    serialize_for_JSON,
    set_console_level_for_subtab,
)
from ._logger_handlers import (
    Audit_Logger,
    Performance_Timer,
    _resolve_log_dir_runtime,
    get_logger,
    log_performance,
    setup_logging,
)


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
    "Audit_Logger",
    "Config_Logging",
    "Log_Filter_Func",
    "Log_Format_Func",
    "Log_Record_Dict",
    "Performance_Timer",
    "_resolve_log_dir_runtime",
    "_subtab_console_rules",
    "filter_audit_events",
    "filter_console_dynamic",
    "filter_error_level",
    "filter_performance_events",
    "format_record_as_JSON",
    "format_sink_JSON",
    "format_sink_human_readable",
    "get_logger",
    "log_function_call",
    "log_performance",
    "sanitize_for_logging",
    "serialize_for_JSON",
    "set_console_level_for_subtab",
    "setup_logging",
]

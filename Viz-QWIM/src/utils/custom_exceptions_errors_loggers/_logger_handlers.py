"""Logger handlers, setup, and audit classes for QWIM Projects.

This private module provides the logger configuration (setup_logging),
the :func:`get_logger` factory, :class:`Audit_Logger`, the
:func:`log_performance` helper, and :class:`Performance_Timer`.

All public symbols are re-exported by the parent façade module
:mod:`src.utils.custom_exceptions_errors_loggers.logger_custom`.

Do **not** import directly from this module; always import from
``logger_custom``.
"""

from __future__ import annotations

import contextlib
import os
import sys
import time
import types

import attrs
from pathlib import Path
from typing import TYPE_CHECKING, Any, Self, cast

from loguru import logger


if TYPE_CHECKING:
    from loguru import Logger

from ._logger_formatters import (
    DEFAULT_LOG_DIR,
    DEFAULT_LOG_LEVEL,
    DEFAULT_RETENTION_DAYS_APPLICATION,
    DEFAULT_RETENTION_DAYS_AUDIT,
    DEFAULT_RETENTION_DAYS_ERROR,
    DEFAULT_RETENTION_DAYS_PERFORMANCE,
    LOG_FILE_APPLICATION,
    LOG_FILE_AUDIT,
    LOG_FILE_DEBUG,
    LOG_FILE_ERROR,
    LOG_FILE_PERFORMANCE,
    Config_Logging,
    filter_audit_events,
    filter_console_dynamic,
    filter_error_level,
    filter_performance_events,
    format_sink_human_readable,
    sanitize_for_logging,
)


# ==============================================================================
# Global State
# ==============================================================================

# Flag to track if logging has been configured
_logging_configured = False


# ==============================================================================
# Runtime Log Directory Resolution
# ==============================================================================


def _normalize_log_dir_path_QWIM(*, log_dir: Path | str) -> Path:
    """Validate and normalize a log-directory input."""
    if isinstance(log_dir, Path):
        return log_dir

    if not isinstance(log_dir, str):
        raise TypeError("log_dir must be a pathlib.Path or string")

    normalized_log_dir = log_dir.strip()
    if normalized_log_dir == "":
        raise ValueError("log_dir must be a non-empty path when provided")

    return Path(normalized_log_dir)


def _resolve_log_dir_runtime(*, log_dir: Path | str) -> Path:
    """Return the runtime log directory for the current process context.

    On Windows, parallel pytest worker processes can collide when the implicit
    default ``logs/`` directory is shared across workers and one process tries
    to rotate a file another process still has open.  When pytest worker
    markers are present, the default log directory is isolated per worker under
    ``logs/pytest/<worker_id>``.

    Explicit caller-provided log directories are preserved unchanged. String
    paths are normalized to :class:`pathlib.Path` before the default-directory
    comparison so default ``"logs"`` inputs follow the same runtime isolation
    rules as ``Path("logs")``.
    """
    normalized_log_dir = _normalize_log_dir_path_QWIM(log_dir = log_dir)

    if normalized_log_dir != DEFAULT_LOG_DIR:
        return normalized_log_dir

    worker_id = os.getenv("PYTEST_XDIST_WORKER")
    current_test = os.getenv("PYTEST_CURRENT_TEST")
    if sys.platform != "win32" or (worker_id is None and current_test is None):
        return normalized_log_dir

    runtime_process_key = worker_id or f"pid_{os.getpid()}"
    return normalized_log_dir / "pytest" / runtime_process_key


# ==============================================================================
# Logging Setup
# ==============================================================================


def setup_logging(
    *, log_level: str = DEFAULT_LOG_LEVEL, environment: str = "development", log_dir: Path | str | None = None, enable_console: bool = True, enable_JSON: bool = True) -> None:
    """Configure application-wide logging using loguru.

    This function must be called once at application startup before any
    logging occurs. It configures multiple log handlers with appropriate
    rotation and retention policies.

    Parameters
    ----------
    log_level : str
        Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        Default is "INFO".
    environment : str
        Deployment environment (development, staging, production).
        Default is "development".
    log_dir : pathlib.Path | str, optional
        Directory for log files. Default is ``./logs/``.
    enable_console : bool
        Whether to log to console.
    enable_JSON : bool
        Whether to use JSON format for file logs. Default is True.

    Returns
    -------
    None

    Raises
    ------
    ValueError
        If log_level or environment values are invalid.

    Example
    -------
    >>> setup_logging(log_level="INFO", environment="production")
    >>> logger = get_logger(__name__)
    >>> logger.info("Application started")

    Notes
    -----
    Log files created:

    - application.log: All logs (INFO and above), 90 days retention
    - audit.log: Audit events only, 7 years retention (regulatory compliance)
    - error.log: ERROR and CRITICAL only, 1 year retention
    - performance.log: Performance metrics, 30 days retention
    - debug.log: DEBUG level (development only), 7 days retention
    """
    global _logging_configured

    # Validate configuration
    if log_dir is None:
        log_dir = DEFAULT_LOG_DIR

    log_dir = _resolve_log_dir_runtime(log_dir = log_dir)

    config = Config_Logging(
        log_level=log_level.upper(),
        environment=environment.lower(),
        log_dir=log_dir,
        enable_console=enable_console,
        enable_JSON=enable_JSON,
    )

    # Create logs directory
    config.log_dir.mkdir(parents=True, exist_ok=True)

    # Create archive subdirectory
    archive_dir = config.log_dir / "archive"
    archive_dir.mkdir(exist_ok=True)

    # Remove default logger handler
    logger.remove()

    # 1. Application log - All logs (INFO and above)
    logger.add(
        config.log_dir / LOG_FILE_APPLICATION,
        level="INFO",
        format=format_sink_human_readable,  # type: ignore[arg-type]
        serialize=config.enable_JSON,
        rotation=config.rotation_size,
        retention=DEFAULT_RETENTION_DAYS_APPLICATION,
        compression="gz",
        encoding="utf-8",
        enqueue=True,
        watch=True,
        colorize=False,
        backtrace=True,
        diagnose=True,
    )

    # 2. Audit log - INFO level for compliance tracking (filtered)
    logger.add(
        config.log_dir / LOG_FILE_AUDIT,
        level="INFO",
        format=format_sink_human_readable,  # type: ignore[arg-type]
        serialize=True,  # Always JSON for audit (native serialization)
        rotation="1 day",
        retention=DEFAULT_RETENTION_DAYS_AUDIT,
        compression="gz",
        encoding="utf-8",
        enqueue=True,
        watch=True,
        colorize=False,
        filter=filter_audit_events,  # type: ignore[arg-type]
        backtrace=True,
    )

    # 3. Error log - ERROR and above only
    logger.add(
        config.log_dir / LOG_FILE_ERROR,
        level="ERROR",
        format=format_sink_human_readable,  # type: ignore[arg-type]
        serialize=config.enable_JSON,
        rotation=config.rotation_size,
        retention=DEFAULT_RETENTION_DAYS_ERROR,
        compression="gz",
        encoding="utf-8",
        enqueue=True,
        watch=True,
        colorize=False,
        filter=filter_error_level,  # type: ignore[arg-type]
        backtrace=True,
        diagnose=True,
    )

    # 4. Performance log - Performance metrics only
    cast(Any, logger).add(
        cast(Any, config.log_dir / LOG_FILE_PERFORMANCE),
        level="DEBUG",
        format=format_sink_human_readable,  # type: ignore[arg-type]
        serialize=True,  # Always JSON for performance metrics
        rotation=config.rotation_size,
        retention=DEFAULT_RETENTION_DAYS_PERFORMANCE,
        compression="gz",
        encoding="utf-8",
        enqueue=True,
        watch=True,
        colorize=False,
        filter=filter_performance_events,  # type: ignore[arg-type]
    )

    # 5. Debug log (development only)
    if config.environment == "development":
        logger.add(
            config.log_dir / LOG_FILE_DEBUG,
            level="DEBUG",
            format=format_sink_human_readable,  # type: ignore[arg-type]
            serialize=config.enable_JSON,
            rotation=config.rotation_size,
            retention="7 days",
            compression="gz",
            encoding="utf-8",
            enqueue=True,
            watch=True,
            colorize=False,
            backtrace=True,
            diagnose=True,
        )

    # 6. Console handler (for development or when enabled)
    if config.enable_console:
        use_colorize = True
        if sys.platform == "win32":  # pragma: no branch
            use_colorize = False
            if hasattr(sys.stderr, "reconfigure"):  # pragma: no branch
                with contextlib.suppress(Exception):
                    sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

        cast(Any, logger).add(
            cast(Any, sys.stderr),
            level="DEBUG",
            filter=filter_console_dynamic,  # type: ignore[arg-type]
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>",
            colorize=use_colorize,
            enqueue=True,
        )

    _logging_configured = True

    # Log startup
    logger.bind(
        event_type="SYSTEM_STARTUP",
        data=sanitize_for_logging(
            value = {
                "log_level": config.log_level,
                "environment": config.environment,
                "log_dir": str(config.log_dir),
                "console_enabled": config.enable_console,
                "JSON_enabled": config.enable_JSON,
            },
        ),
    ).info("Logging configured successfully")


def get_logger(*, name: str) -> Logger:
    """Get a logger instance bound with the given name.

    Parameters
    ----------
    name : str
        Logger name (typically __name__).

    Returns
    -------
    Logger
        Configured loguru logger instance bound with the name.

    Raises
    ------
    RuntimeError
        If setup_logging() has not been called.

    Example
    -------
    >>> app_logger = get_logger(__name__)
    >>> app_logger.info("Processing started")
    """
    if not _logging_configured:
        # Auto-configure with defaults if not configured
        setup_logging()

    return logger.bind(name=name)


# ==============================================================================
# Audit Logger Class
# ==============================================================================


@attrs.define(kw_only=True)
class Audit_Logger:
    """Specialized logger for audit trail events.

    This class provides convenience methods for logging events that require
    audit trails for compliance purposes in financial applications.

    Parameters
    ----------
    logger_name : str
        Name to identify this logger instance.

    Attributes
    ----------
    logger_name : str
        The name of the logger.
    _logger : Logger
        The bound loguru logger instance.

    Example
    -------
    >>> audit = Audit_Logger(logger_name="portfolio_module")
    >>> audit.log_calculation(
    ...     operation="Option Pricing",
    ...     inputs={"spot": 100, "strike": 105},
    ...     result=3.45,
    ...     execution_time_ms=12.5,
    ...     user_id="analyst_001",
    ... )
    """

    logger_name: str = attrs.field()
    _logger: Logger = attrs.field(init=False, repr=False)

    def __attrs_post_init__(self) -> None:
        """Initialize the bound logger after attrs initialization."""
        self._logger = get_logger(name = self.logger_name)

    def log_calculation(
        self, *, operation: str, inputs: dict[str, Any], result: Any, execution_time_ms: float, user_id: str | None = None, session_id: str | None = None) -> None:
        """Log a financial calculation for audit trail.

        Parameters
        ----------
        operation : str
            Name of the calculation (e.g., "Black-Scholes Pricing").
        inputs : dict[str, Any]
            Input parameters used in calculation.
        result : Any
            Calculation result.
        execution_time_ms : float
            Execution time in milliseconds.
        user_id : str, optional
            User identifier performing the calculation.
        session_id : str, optional
            Session identifier for tracking.

        Returns
        -------
        None

        Example
        -------
        >>> audit.log_calculation(
        ...     operation="Portfolio Return",
        ...     inputs={"weights": [0.6, 0.4], "returns": [0.05, 0.03]},
        ...     result=0.042,
        ...     execution_time_ms=5.2,
        ...     user_id="analyst_001",
        ... )
        """
        self._logger.bind(
            event_type="CALCULATION",
            user_id=user_id or "system",
            session_id=session_id,
            execution_time_ms=execution_time_ms,
            data=sanitize_for_logging(
                value = {
                    "operation": operation,
                    "inputs": inputs,
                    "result": result,
                },
            ),
        ).info("Calculation completed: %s", operation)

    def log_data_access(
        self, *, source: str, operation: str, record_count: int, user_id: str | None = None, session_id: str | None = None, details: dict[str, Any] | None = None) -> None:
        """Log data access for audit trail.

        Parameters
        ----------
        source : str
            Data source (file path, database, API endpoint).
        operation : str
            Type of operation (READ, WRITE, DELETE, UPDATE).
        record_count : int
            Number of records accessed.
        user_id : str, optional
            User identifier performing the operation.
        session_id : str, optional
            Session identifier for tracking.
        details : dict[str, Any], optional
            Additional details about the operation.

        Returns
        -------
        None

        Example
        -------
        >>> audit.log_data_access(
        ...     source="inputs/raw/data_ETFs.csv",
        ...     operation="READ",
        ...     record_count=252,
        ...     user_id="analyst_001",
        ... )
        """
        self._logger.bind(
            event_type="DATA_ACCESS",
            user_id=user_id or "system",
            session_id=session_id,
            data=sanitize_for_logging(
                value = {
                    "source": source,
                    "operation": operation,
                    "record_count": record_count,
                    "details": details or {},
                },
            ),
        ).info("Data access: %s from %s", operation, source)

    def log_parameter_change(
        self, *, parameter_name: str, old_value: Any, new_value: Any, user_id: str | None = None, session_id: str | None = None, reason: str | None = None) -> None:
        """Log parameter or configuration change for audit trail.

        Parameters
        ----------
        parameter_name : str
            Name of the parameter changed.
        old_value : Any
            Previous value.
        new_value : Any
            New value.
        user_id : str, optional
            User identifier making the change.
        session_id : str, optional
            Session identifier for tracking.
        reason : str, optional
            Reason for the change.

        Returns
        -------
        None

        Example
        -------
        >>> audit.log_parameter_change(
        ...     parameter_name="risk_free_rate",
        ...     old_value=0.02,
        ...     new_value=0.025,
        ...     user_id="admin_001",
        ...     reason="Updated to reflect market conditions",
        ... )
        """
        self._logger.bind(
            event_type="PARAMETER_CHANGE",
            user_id=user_id or "system",
            session_id=session_id,
            data=sanitize_for_logging(
                value = {
                    "parameter": parameter_name,
                    "old_value": old_value,
                    "new_value": new_value,
                    "reason": reason,
                },
            ),
        ).warning("Parameter changed: %s", parameter_name)

    def log_user_action(
        self, *, action: str, resource: str, user_id: str, session_id: str | None = None, details: dict[str, Any] | None = None, success: bool = True) -> None:
        """Log user action for audit trail.

        Parameters
        ----------
        action : str
            Action performed (e.g., "LOGIN", "LOGOUT", "VIEW", "EXPORT").
        resource : str
            Resource affected by the action.
        user_id : str
            User identifier performing the action.
        session_id : str, optional
            Session identifier for tracking.
        details : dict[str, Any], optional
            Additional details about the action.
        success : bool
            Whether the action was successful.

        Returns
        -------
        None

        Example
        -------
        >>> audit.log_user_action(
        ...     action="EXPORT",
        ...     resource="portfolio_report.pdf",
        ...     user_id="analyst_001",
        ...     details={"format": "PDF", "pages": 15},
        ... )
        """
        log_data = {
            "action": action,
            "resource": resource,
            "success": success,
            "details": details or {},
        }

        bound_logger = self._logger.bind(
            event_type="USER_ACTION",
            user_id=user_id,
            session_id=session_id,
            data=sanitize_for_logging(value = log_data),
        )

        if success:
            bound_logger.info("User action: %s on %s", action, resource)
        else:
            bound_logger.warning("User action failed: %s on %s", action, resource)

    def log_system_event(
        self, *, event_name: str, details: dict[str, Any] | None = None, severity: str = "INFO") -> None:
        """Log system event for monitoring.

        Parameters
        ----------
        event_name : str
            Name of the system event.
        details : dict[str, Any], optional
            Additional event details.
        severity : str
            Log severity level (DEBUG, INFO, WARNING, ERROR, CRITICAL).

        Returns
        -------
        None

        Example
        -------
        >>> audit.log_system_event(
        ...     event_name="CACHE_CLEARED",
        ...     details={"cache_size_mb": 256},
        ...     severity="INFO",
        ... )
        """
        bound_logger = self._logger.bind(
            event_type="SYSTEM_EVENT",
            data=sanitize_for_logging(
                value = {
                    "event_name": event_name,
                    "details": details or {},
                },
            ),
        )

        log_method = getattr(bound_logger, severity.lower(), bound_logger.info)
        log_method("System event: %s", event_name)


# ==============================================================================
# Performance Logging Utilities
# ==============================================================================


def log_performance(
    *, operation_name: str, execution_time_ms: float, details: dict[str, Any] | None = None, logger_instance: Logger | None = None) -> None:
    """Log performance metrics for an operation.

    Parameters
    ----------
    operation_name : str
        Name of the operation being measured.
    execution_time_ms : float
        Execution time in milliseconds.
    details : dict[str, Any], optional
        Additional performance details.
    logger_instance : Logger, optional
        Logger instance to use. If None, uses default logger.

    Returns
    -------
    None

    Example
    -------
    >>> start = time.perf_counter()
    >>> # ... perform operation ...
    >>> elapsed = (time.perf_counter() - start) * 1000
    >>> log_performance("portfolio_calculation", elapsed)
    """
    log = logger_instance or logger

    log.bind(
        event_type="PERFORMANCE",
        execution_time_ms=execution_time_ms,
        data=sanitize_for_logging(
            value = {
                "operation": operation_name,
                "details": details or {},
            },
        ),
    ).debug("Performance: %s completed in %.2fms", operation_name, execution_time_ms)


class Performance_Timer:
    """Context manager for timing operations with automatic logging.

    Parameters
    ----------
    operation_name : str
        Name of the operation being timed.
    logger_instance : Logger, optional
        Logger instance to use.
    log_start : bool
        Whether to log when timing starts.
    details : dict[str, Any], optional
        Additional details to include in logs.

    Example
    -------
    >>> with Performance_Timer("portfolio_optimization") as timer:
    ...     result = optimize_portfolio(weights)
    >>> print(f"Optimization took {timer.elapsed_ms:.2f}ms")
    """

    def __init__(
        self,
        operation_name: str,
        logger_instance: Logger | None = None,
        log_start: bool = False,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the performance timer."""
        self.operation_name = operation_name
        self._logger = logger_instance or logger
        self.log_start = log_start
        self.details = details or {}
        self.start_time: float = 0.0
        self.end_time: float = 0.0
        self.elapsed_ms: float = 0.0

    def __enter__(self) -> Self:
        """Start the timer."""
        self.start_time = time.perf_counter()

        if self.log_start:
            self._logger.bind(
                event_type="PERFORMANCE_START",
                data=sanitize_for_logging(
                    value = {
                        "operation": self.operation_name,
                        "details": self.details,
                    },
                ),
            ).debug("Performance: Starting %s", self.operation_name)

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        """Stop the timer and log the result."""
        self.end_time = time.perf_counter()
        self.elapsed_ms = (self.end_time - self.start_time) * 1000

        log_data = {
            "operation": self.operation_name,
            "details": self.details,
            "success": exc_type is None,
        }

        if exc_type is not None:
            log_data["error_type"] = exc_type.__name__

        self._logger.bind(
            event_type="PERFORMANCE",
            execution_time_ms=self.elapsed_ms,
            data=sanitize_for_logging(value = log_data),
        ).debug("Performance: %s completed in %.2fms", self.operation_name, self.elapsed_ms)


# ==============================================================================
# Module Exports
# ==============================================================================

__all__ = [
    "Audit_Logger",
    "Performance_Timer",
    "_resolve_log_dir_runtime",
    "get_logger",
    "log_performance",
    "setup_logging",
]

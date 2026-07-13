"""log_function_call decorator for QWIM Projects.

This private module provides the :func:`log_function_call` decorator which
wraps any function with structured logging, optional audit-trail tagging,
and execution-time measurement.

All public symbols are re-exported by the parent façade module
:mod:`src.utils.custom_exceptions_errors_loggers.logger_custom`.

Do **not** import directly from this module; always import from
``logger_custom``.
"""

from __future__ import annotations

import time

from collections.abc import Callable
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from loguru import logger

from ._logger_formatters import sanitize_for_logging


P = ParamSpec("P")
R = TypeVar("R")


# ==============================================================================
# Decorator
# ==============================================================================


def log_function_call(
    *, log_args: bool = True, log_result: bool = False, log_performance: bool = True, audit_event_type: str | None = None) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorate a function to automatically log its calls.

    Parameters
    ----------
    log_args : bool
        Whether to log function arguments.
    log_result : bool
        Whether to log function return value.
    log_performance : bool
        Whether to log execution time.
    audit_event_type : str, optional
        If provided, logs as audit event with this type.

    Returns
    -------
    Callable[[Callable[P, R]], Callable[P, R]]
        Decorator that wraps functions with logging.

    Example
    -------
    >>> @log_function_call(audit_event_type="CALCULATION")
    ... def calculate_returns(portfolio_weights, prices):
    ...     # ... calculation logic ...
    ...     return returns
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        """Wrap *func* to inject structured logging context on each call."""

        @wraps(func)
        def wrapper(
            *args: P.args,
            **kwargs: P.kwargs,
        ) -> R:
            """Call the original function with structured logging around it."""
            func_name = func.__name__  # ty: ignore[unresolved-attribute]
            module_name = func.__module__

            # Prepare log data
            log_data: dict[str, Any] = {
                "function": func_name,
                "module": module_name,
            }

            if log_args:
                # Sanitize args (avoid logging sensitive data)
                log_data["args_count"] = len(args)
                log_data["kwargs_keys"] = list(kwargs.keys())

            start_time = time.perf_counter()

            try:
                result = func(*args, **kwargs)
                execution_time_ms = (time.perf_counter() - start_time) * 1000

                # Build bound logger
                bound_logger = logger.bind(
                    execution_time_ms=execution_time_ms if log_performance else None,
                    data=sanitize_for_logging(value = log_data),
                )

                if audit_event_type:
                    bound_logger = bound_logger.bind(event_type=audit_event_type)

                if log_result and result is not None:
                    log_data["result_type"] = type(result).__name__

                bound_logger.debug(
                    "Function %s completed in %.2fms",
                    func_name,
                    execution_time_ms,
                )

                return result

            except Exception as exc:
                execution_time_ms = (time.perf_counter() - start_time) * 1000
                log_data["error_type"] = type(exc).__name__
                log_data["error_message"] = str(exc)

                logger.bind(
                    event_type="FUNCTION_ERROR" if audit_event_type else None,
                    execution_time_ms=execution_time_ms,
                    data=sanitize_for_logging(value = log_data),
                ).error("Function %s failed: %s", func_name, exc)

                raise

        return wrapper

    return decorator


# ==============================================================================
# Module Exports
# ==============================================================================

__all__ = [
    "log_function_call",
]

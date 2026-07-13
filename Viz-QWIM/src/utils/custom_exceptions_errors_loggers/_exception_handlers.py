"""Domain exception classes, global handlers, and context managers.

This private module contains:

- All 17 domain ``Exception_*`` classes (inheriting from
  :class:`~._exception_core.Exception_Custom`)
- The :func:`Global_Exception_Handler` and install/restore helpers
- The :func:`Capture_Exception` context manager
- The :func:`Handle_Exceptions` decorator

All public symbols are re-exported by the parent façade module
:mod:`src.utils.custom_exceptions_errors_loggers.exception_custom`.

Do **not** import directly from this module; always import from
``exception_custom``.
"""

from __future__ import annotations

import os
import sys

from collections.abc import Callable, Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, ParamSpec, TypeVar

from ._exception_core import Exception_Custom
from ._exception_types_lightweight import (
    Exception_Format,
    Exception_Severity,
    _Mask_Sensitive_Data,
    _Truncate_Value,
)


# ==============================================================================
# Domain-Specific Exception Classes
# ==============================================================================


class Exception_Validation_Input(Exception_Custom):
    """Exception raised when input validation fails.

    Use this for validating user inputs, parameters, or data formats.

    Parameters
    ----------
    message : str
        Validation error message.
    field_name : str | None
        Name of the invalid field.
    expected_type : type | None
        Expected type for the field.
    actual_value : Any | None
        Actual value that failed validation.
    **kwargs : Any
        Additional Exception_Custom parameters.

    Examples
    --------
    >>> raise Exception_Validation_Input(
    ...     "Invalid portfolio weight",
    ...     field_name="weight",
    ...     expected_type=float,
    ...     actual_value="not_a_number",
    ... )
    """

    def __init__(
        self,
        message: str,
        field_name: str | None = None,
        expected_type: type | None = None,
        actual_value: Any = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the exception with *message* and optional validation context."""
        context = kwargs.pop("context", {})
        if field_name:
            context["field_name"] = field_name
        if expected_type:
            context["expected_type"] = (
                expected_type.__name__ if isinstance(expected_type, type) else str(expected_type)
            )
        if actual_value is not None:
            context["actual_value"] = _Truncate_Value(value = actual_value)
        super().__init__(message, context=context, **kwargs)


class Exception_Configuration(Exception_Custom):
    """Exception raised for configuration-related errors.

    Use this for missing or invalid configuration settings.

    Parameters
    ----------
    message : str
        Configuration error message.
    config_key : str | None
        Configuration key that caused the error.
    config_file : str | Path | None
        Configuration file path.
    **kwargs : Any
        Additional Exception_Custom parameters.
    """

    def __init__(
        self,
        message: str,
        config_key: str | None = None,
        config_file: str | Path | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the exception with *message* and optional configuration context."""
        context = kwargs.pop("context", {})
        if config_key:
            context["config_key"] = config_key
        if config_file:
            context["config_file"] = str(config_file)
        super().__init__(message, context=context, **kwargs)


class Exception_Data_Not_Found(Exception_Custom):
    """Exception raised when required data is missing.

    Use this for missing files, database records, or API responses.

    Parameters
    ----------
    message : str
        Error message describing missing data.
    data_type : str | None
        Type of data that was not found.
    identifier : str | None
        Identifier used to search for data.
    source : str | None
        Data source (file path, database, API, etc.).
    **kwargs : Any
        Additional Exception_Custom parameters.
    """

    def __init__(
        self,
        message: str,
        data_type: str | None = None,
        identifier: str | None = None,
        source: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the exception with *message* and optional missing-data context."""
        context = kwargs.pop("context", {})
        if data_type:
            context["data_type"] = data_type
        if identifier:
            context["identifier"] = identifier
        if source:
            context["source"] = source
        super().__init__(message, context=context, **kwargs)


class Exception_Calculation(Exception_Custom):
    """Exception raised for calculation or computation failures.

    Use this for mathematical errors, algorithm failures, or numerical issues.

    Parameters
    ----------
    message : str
        Calculation error message.
    operation : str | None
        Name of the calculation operation.
    inputs : dict[str, Any] | None
        Input values that caused the failure.
    **kwargs : Any
        Additional Exception_Custom parameters.
    """

    def __init__(
        self,
        message: str,
        operation: str | None = None,
        inputs: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the exception with *message* and optional calculation context."""
        context = kwargs.pop("context", {})
        if operation:
            context["operation"] = operation
        if inputs:
            context["inputs"] = _Mask_Sensitive_Data(data = inputs)
        super().__init__(message, context=context, **kwargs)


class Exception_Portfolio(Exception_Custom):
    """Exception raised for portfolio-related errors.

    Use this for portfolio validation, optimization, or rebalancing failures.

    Parameters
    ----------
    message : str
        Portfolio error message.
    portfolio_id : str | None
        Portfolio identifier.
    portfolio_name : str | None
        Portfolio name.
    operation : str | None
        Operation that failed.
    **kwargs : Any
        Additional Exception_Custom parameters.
    """

    def __init__(
        self,
        message: str,
        portfolio_id: str | None = None,
        portfolio_name: str | None = None,
        operation: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the exception with *message* and optional portfolio context."""
        context = kwargs.pop("context", {})
        if portfolio_id:
            context["portfolio_id"] = portfolio_id
        if portfolio_name:
            context["portfolio_name"] = portfolio_name
        if operation:
            context["operation"] = operation
        super().__init__(message, context=context, **kwargs)


class Exception_Client(Exception_Custom):
    """Exception raised for client data errors.

    Use this for client validation, missing client data, or client operations.

    Parameters
    ----------
    message : str
        Client error message.
    client_id : str | None
        Client identifier.
    client_type : str | None
        Type of client (PRIMARY, PARTNER, etc.).
    **kwargs : Any
        Additional Exception_Custom parameters.
    """

    def __init__(
        self,
        message: str,
        client_id: str | None = None,
        client_type: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the exception with *message* and optional client context."""
        context = kwargs.pop("context", {})
        if client_id:
            context["client_id"] = client_id
        if client_type:
            context["client_type"] = client_type
        super().__init__(message, context=context, **kwargs)


class Exception_Database(Exception_Custom):
    """Exception raised for database operation failures.

    Use this for connection errors, query failures, or transaction issues.

    Parameters
    ----------
    message : str
        Database error message.
    database_name : str | None
        Name of the database.
    operation : str | None
        Database operation (SELECT, INSERT, UPDATE, DELETE).
    table_name : str | None
        Table involved in the operation.
    query : str | None
        Query that failed (will be truncated).
    **kwargs : Any
        Additional Exception_Custom parameters.
    """

    def __init__(
        self,
        message: str,
        database_name: str | None = None,
        operation: str | None = None,
        table_name: str | None = None,
        query: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the exception with *message* and optional database context."""
        context = kwargs.pop("context", {})
        if database_name:
            context["database_name"] = database_name
        if operation:
            context["operation"] = operation
        if table_name:
            context["table_name"] = table_name
        if query:
            context["query"] = _Truncate_Value(value = query, max_length = 200)
        super().__init__(message, context=context, **kwargs)


class Exception_API(Exception_Custom):
    """Exception raised for API communication failures.

    Use this for HTTP errors, API timeouts, or response parsing failures.

    Parameters
    ----------
    message : str
        API error message.
    endpoint : str | None
        API endpoint URL.
    method : str | None
        HTTP method (GET, POST, PUT, DELETE).
    status_code : int | None
        HTTP status code.
    response_body : str | None
        Response body (will be truncated).
    **kwargs : Any
        Additional Exception_Custom parameters.
    """

    def __init__(
        self,
        message: str,
        endpoint: str | None = None,
        method: str | None = None,
        status_code: int | None = None,
        response_body: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the exception with *message* and optional API context."""
        context = kwargs.pop("context", {})
        if endpoint:
            context["endpoint"] = endpoint
        if method:
            context["method"] = method
        if status_code:
            context["status_code"] = status_code
        if response_body:
            context["response_body"] = _Truncate_Value(value = response_body, max_length = 500)
        super().__init__(message, context=context, **kwargs)


class Exception_Authentication(Exception_Custom):
    """Exception raised for authentication failures.

    Use this for login failures, invalid credentials, or session issues.

    Parameters
    ----------
    message : str
        Authentication error message.
    user_id : str | None
        User identifier (will NOT include credentials).
    auth_method : str | None
        Authentication method used.
    **kwargs : Any
        Additional Exception_Custom parameters.
    """

    def __init__(
        self,
        message: str,
        user_id: str | None = None,
        auth_method: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the exception with *message* and optional authentication context."""
        context = kwargs.pop("context", {})
        if user_id:
            context["user_id"] = user_id
        if auth_method:
            context["auth_method"] = auth_method
        super().__init__(
            message,
            severity=Exception_Severity.WARNING,  # type: ignore[arg-type]
            context=context,
            **kwargs,
        )


class Exception_Authorization(Exception_Custom):
    """Exception raised for authorization/permission failures.

    Use this for access denied, insufficient permissions, or role violations.

    Parameters
    ----------
    message : str
        Authorization error message.
    user_id : str | None
        User identifier.
    required_permission : str | None
        Permission that was required.
    resource : str | None
        Resource that access was denied to.
    **kwargs : Any
        Additional Exception_Custom parameters.
    """

    def __init__(
        self,
        message: str,
        user_id: str | None = None,
        required_permission: str | None = None,
        resource: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the exception with *message* and optional authorization context."""
        context = kwargs.pop("context", {})
        if user_id:
            context["user_id"] = user_id
        if required_permission:
            context["required_permission"] = required_permission
        if resource:
            context["resource"] = resource
        super().__init__(
            message,
            severity=Exception_Severity.WARNING,  # type: ignore[arg-type]
            context=context,
            **kwargs,
        )


class Exception_File_Operation(Exception_Custom):
    """Exception raised for file I/O failures.

    Use this for file read/write errors, permission issues, or format problems.

    Parameters
    ----------
    message : str
        File operation error message.
    file_path : str | Path | None
        Path to the file.
    operation : str | None
        File operation (read, write, delete, etc.).
    **kwargs : Any
        Additional Exception_Custom parameters.
    """

    def __init__(
        self,
        message: str,
        file_path: str | Path | None = None,
        operation: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the exception with *message* and optional file-operation context."""
        context = kwargs.pop("context", {})
        if file_path:
            context["file_path"] = str(file_path)
        if operation:
            context["operation"] = operation
        super().__init__(message, context=context, **kwargs)


class Exception_Timeout(Exception_Custom):
    """Exception raised when operations exceed time limits.

    Use this for operation timeouts, deadline exceeded, or slow responses.

    Parameters
    ----------
    message : str
        Timeout error message.
    operation : str | None
        Operation that timed out.
    timeout_seconds : float | None
        Timeout limit in seconds.
    elapsed_seconds : float | None
        Actual elapsed time.
    **kwargs : Any
        Additional Exception_Custom parameters.
    """

    def __init__(
        self,
        message: str,
        operation: str | None = None,
        timeout_seconds: float | None = None,
        elapsed_seconds: float | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the exception with *message* and optional timeout context."""
        context = kwargs.pop("context", {})
        if operation:
            context["operation"] = operation
        if timeout_seconds is not None:
            context["timeout_seconds"] = timeout_seconds
        if elapsed_seconds is not None:
            context["elapsed_seconds"] = elapsed_seconds
        super().__init__(message, context=context, **kwargs)


class Exception_Invalid_Input(Exception_Custom):
    """Exception raised when input is invalid or malformed.

    Use this for general input validation failures beyond type checking.

    Parameters
    ----------
    message : str
        Error message describing the invalid input.
    input_name : str | None
        Name of the invalid input parameter.
    expected_format : str | None
        Description of expected input format.
    actual_value : Any | None
        The actual value that was provided.
    **kwargs : Any
        Additional Exception_Custom parameters.

    Examples
    --------
    >>> raise Exception_Invalid_Input(
    ...     "Portfolio weights must sum to 1.0",
    ...     input_name="weights",
    ...     expected_format="dict[str, float] summing to 1.0",
    ...     actual_value={"AAPL": 0.5, "MSFT": 0.3},
    ... )
    """

    def __init__(
        self,
        message: str,
        input_name: str | None = None,
        expected_format: str | None = None,
        actual_value: Any = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the exception with *message* and optional invalid-input context."""
        context = kwargs.pop("context", {})
        if input_name:
            context["input_name"] = input_name
        if expected_format:
            context["expected_format"] = expected_format
        if actual_value is not None:
            context["actual_value"] = _Truncate_Value(value = actual_value)
        super().__init__(message, context=context, **kwargs)


class Exception_Not_Found(Exception_Custom):
    """Exception raised when a requested resource or entity is not found.

    General-purpose not-found exception for any type of missing resource.

    Parameters
    ----------
    message : str
        Error message describing what was not found.
    resource_type : str | None
        Type of resource that was not found.
    resource_id : str | None
        Identifier of the missing resource.
    search_criteria : dict[str, Any] | None
        Criteria used to search for the resource.
    **kwargs : Any
        Additional Exception_Custom parameters.

    Examples
    --------
    >>> raise Exception_Not_Found(
    ...     "Portfolio not found",
    ...     resource_type="Portfolio",
    ...     resource_id="PORT_001",
    ... )
    """

    def __init__(
        self,
        message: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
        search_criteria: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the exception with *message* and optional not-found context."""
        context = kwargs.pop("context", {})
        if resource_type:
            context["resource_type"] = resource_type
        if resource_id:
            context["resource_id"] = resource_id
        if search_criteria:
            context["search_criteria"] = _Mask_Sensitive_Data(data = search_criteria)
        super().__init__(message, context=context, **kwargs)


class Exception_Security_Violation(Exception_Custom):
    """Exception raised for security policy violations.

    Use this for path traversal attempts, injection attacks, or policy breaches.

    Parameters
    ----------
    message : str
        Security violation description.
    violation_type : str | None
        Type of security violation (path_traversal, injection, policy_breach).
    resource : str | None
        Resource involved in the violation.
    user_id : str | None
        User who triggered the violation.
    **kwargs : Any
        Additional Exception_Custom parameters.

    Examples
    --------
    >>> raise Exception_Security_Violation(
    ...     "Path traversal attempt detected",
    ...     violation_type="path_traversal",
    ...     resource="../../../etc/passwd",
    ... )
    """

    def __init__(
        self,
        message: str,
        violation_type: str | None = None,
        resource: str | None = None,
        user_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the exception with *message* and optional security-violation context."""
        context = kwargs.pop("context", {})
        if violation_type:
            context["violation_type"] = violation_type
        if resource:
            context["resource"] = resource
        if user_id:
            context["user_id"] = user_id
        super().__init__(
            message,
            severity=Exception_Severity.CRITICAL,  # type: ignore[arg-type]
            context=context,
            **kwargs,
        )


class Exception_Insufficient_Holdings(Exception_Custom):
    """Exception raised when portfolio has insufficient holdings for operation.

    Use this for sell/transfer operations that exceed available holdings.

    Parameters
    ----------
    message : str
        Error message describing the insufficiency.
    ticker : str | None
        Ticker symbol of the asset.
    required_quantity : float | None
        Quantity required for the operation.
    available_quantity : float | None
        Quantity currently available.
    operation : str | None
        Operation that was attempted.
    **kwargs : Any
        Additional Exception_Custom parameters.

    Examples
    --------
    >>> raise Exception_Insufficient_Holdings(
    ...     "Insufficient AAPL holdings for sell order",
    ...     ticker="AAPL",
    ...     required_quantity=100.0,
    ...     available_quantity=50.0,
    ...     operation="sell",
    ... )
    """

    def __init__(
        self,
        message: str,
        ticker: str | None = None,
        required_quantity: float | None = None,
        available_quantity: float | None = None,
        operation: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the exception with *message* and optional holdings context."""
        context = kwargs.pop("context", {})
        if ticker:
            context["ticker"] = ticker
        if required_quantity is not None:
            context["required_quantity"] = required_quantity
        if available_quantity is not None:
            context["available_quantity"] = available_quantity
        if operation:
            context["operation"] = operation
        super().__init__(message, context=context, **kwargs)


class Exception_Invalid_Transaction(Exception_Custom):
    """Exception raised when a transaction is invalid or cannot be executed.

    Use this for transaction validation failures or business rule violations.

    Parameters
    ----------
    message : str
        Error message describing why transaction is invalid.
    transaction_type : str | None
        Type of transaction (buy, sell, transfer, rebalance).
    transaction_id : str | None
        Unique identifier for the transaction.
    reason : str | None
        Specific reason for invalidation.
    **kwargs : Any
        Additional Exception_Custom parameters.

    Examples
    --------
    >>> raise Exception_Invalid_Transaction(
    ...     "Cannot execute sell order: market closed",
    ...     transaction_type="sell",
    ...     reason="market_closed",
    ... )
    """

    def __init__(
        self,
        message: str,
        transaction_type: str | None = None,
        transaction_id: str | None = None,
        reason: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the exception with *message* and optional transaction context."""
        context = kwargs.pop("context", {})
        if transaction_type:
            context["transaction_type"] = transaction_type
        if transaction_id:
            context["transaction_id"] = transaction_id
        if reason:
            context["reason"] = reason
        super().__init__(message, context=context, **kwargs)


# ==============================================================================
# Exception Aliases (for convenience and backward compatibility)
# ==============================================================================

# Alias for validation-related exceptions per coding standards
Exception_Validation = Exception_Validation_Input


# ==============================================================================
# Global Exception Handler Utilities
# ==============================================================================

_ORIGINAL_EXCEPTHOOK = sys.excepthook


def Global_Exception_Handler(
    *, exc_type: type[BaseException], exc_value: BaseException, exc_traceback: Any) -> None:
    """Global exception handler using Exception_Custom.

    Parameters
    ----------
    exc_type : type[BaseException]
        Exception class.
    exc_value : BaseException
        Exception instance.
    exc_traceback : Any
        Traceback object.
    """
    # Wrap standard exceptions
    if not isinstance(exc_value, Exception_Custom):
        # Determine format from environment
        env_fmt = os.environ.get("QWIM_EXCEPTION_FORMAT", "RICH_TRACEBACK")
        try:
            fmt = Exception_Format[env_fmt]  # type: ignore[index]
        except KeyError:
            fmt = Exception_Format.RICH_TRACEBACK

        # Ensure we wrap standard exceptions properly
        if isinstance(exc_value, Exception):
            exc = Exception_Custom.From_Exception(exception = exc_value, exception_format=fmt)
        else:
            # For BaseException (SystemExit, etc), just use standard hook
            _ORIGINAL_EXCEPTHOOK(exc_type, exc_value, exc_traceback)
            return
    else:
        exc = exc_value

    # Log to audit/error log using logger_custom
    try:
        from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

        logger = get_logger(name = "global_handler")
        # Log as CRITICAL since it's unhandled
        logger.opt(exception=(exc_type, exc_value, exc_traceback)).critical(
            f"Uncaught exception: {exc_value}",
        )
    except Exception as log_exc:
        # Fallback if logging fails
        sys.stderr.write(f"[Global_Exception_Handler] Logging failed: {log_exc}\n")

    # Print using rich format if supported, otherwise standard
    if exc.Exception_Format_Value in {Exception_Format.RICH_TRACEBACK, Exception_Format.FULL}:
        exc.Print_Rich()
    else:
        sys.stderr.write(f"{exc}\n")


def Install_Exception_Handler() -> None:
    """Install global exception handler."""
    global _ORIGINAL_EXCEPTHOOK

    if sys.excepthook is Global_Exception_Handler:
        return

    _ORIGINAL_EXCEPTHOOK = sys.excepthook
    sys.excepthook = Global_Exception_Handler


def Restore_Exception_Handler() -> None:
    """Restore original exception handler."""
    sys.excepthook = _ORIGINAL_EXCEPTHOOK


# ==============================================================================
# Context Managers & Decorators
# ==============================================================================

T = TypeVar("T")
P = ParamSpec("P")


@contextmanager
def Capture_Exception(
    *, context: dict[str, Any] | None = None, reraise: bool = True, log_severity: Exception_Severity | None = None) -> Generator[None, None, None]:
    """Context manager to capture and wrap exceptions.

    Parameters
    ----------
    context : dict[str, Any] | None
        Additional context to add to exceptions.
    reraise : bool
        Whether to reraise the exception (wrapped).
    log_severity : Exception_Severity | None
        Override severity level.

    Yields
    ------
    None
    """
    try:
        yield
    except Exception as e:
        if isinstance(e, Exception_Custom):
            if context:
                e._user_context.update(context)
            if log_severity:
                e._severity = log_severity
            if reraise:
                raise
        else:
            wrapped = Exception_Custom.From_Exception(
                exception = e,
                context=context,
                severity=log_severity or Exception_Severity.ERROR,
            )
            if reraise:
                raise wrapped from e


def Handle_Exceptions(
    *, context: dict[str, Any] | None = None, severity: Exception_Severity | None = None) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator to handle exceptions in functions.

    Parameters
    ----------
    context : dict[str, Any] | None
        Static context data.
    severity : Exception_Severity | None
        Severity level for captured exceptions.

    Returns
    -------
    Callable
        Decorated function.
    """

    def Decorator(func: Callable[P, T]) -> Callable[P, T]:
        """Wrap *func* to convert unhandled exceptions into Exception_Custom."""
        from functools import wraps

        @wraps(func)
        def Wrapper(
            *args: P.args,
            **kwargs: P.kwargs,
        ) -> T:
            """Call the original function and re-raise exceptions as Exception_Custom."""
            try:
                return func(*args, **kwargs)
            except Exception as e:
                ctx = context or {}
                # Ensure context is a copy
                ctx = ctx.copy()

                if isinstance(e, Exception_Custom):
                    e._user_context.update(ctx)
                    if severity:
                        e._severity = severity
                    raise

                wrapped = Exception_Custom.From_Exception(
                    exception = e,
                    context=ctx,
                    severity=severity or Exception_Severity.ERROR,
                )
                raise wrapped from e

        return Wrapper

    return Decorator


# ==============================================================================
# Module Exports
# ==============================================================================

__all__ = [
    "Exception_API",
    "Exception_Authentication",
    "Exception_Authorization",
    "Exception_Calculation",
    "Exception_Client",
    "Exception_Configuration",
    "Exception_Data_Not_Found",
    "Exception_Database",
    "Exception_File_Operation",
    "Exception_Insufficient_Holdings",
    "Exception_Invalid_Input",
    "Exception_Invalid_Transaction",
    "Exception_Not_Found",
    "Exception_Portfolio",
    "Exception_Security_Violation",
    "Exception_Timeout",
    "Exception_Validation",
    "Exception_Validation_Input",
    "Capture_Exception",
    "Global_Exception_Handler",
    "Handle_Exceptions",
    "Install_Exception_Handler",
    "Restore_Exception_Handler",
]

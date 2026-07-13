"""Lightweight exception base types for QWIM projects.

This private module contains the foundational exception infrastructure:
platform patches, constants, enumerations, data-classes, helper functions,
and the root ``Exception_QWIM_Error`` hierarchy with four lightweight typed subclasses.

All public symbols are re-exported by the parent façade module
:mod:`src.utils.custom_exceptions_errors_loggers.exception_custom`.

Do **not** import directly from this module; always import from
``exception_custom``.
"""

from __future__ import annotations

import contextlib
import io
import linecache
import sys
import threading

import attrs
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from aenum import Enum, auto
from rich.console import Console


if TYPE_CHECKING:
    from types import TracebackType


# ==============================================================================
# Platform Utilities — UTF-8 on Windows
# ==============================================================================

if sys.platform == "win32":  # pragma: no branch
    # Ensure all standard streams use UTF-8
    if hasattr(sys.stdout, "reconfigure"):  # pragma: no branch
        with contextlib.suppress(Exception):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    if hasattr(sys.stderr, "reconfigure"):  # pragma: no branch
        with contextlib.suppress(Exception):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    if hasattr(sys.stdin, "reconfigure"):  # pragma: no branch
        with contextlib.suppress(Exception):  # pragma: no cover
            sys.stdin.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]  # pragma: no cover


# ==============================================================================
# UTF-8 Console Monkey Patch for Windows
# ==============================================================================

# Monkey patch rich.console.Console to always use UTF-8 on Windows.
# This ensures tbhandler and any other code using rich will not encounter
# UnicodeEncodeError with special characters like ❱, ✓, etc.
if sys.platform == "win32":  # pragma: no branch
    # Store original Console.__init__
    _original_console_init = Console.__init__

    def _patched_console_init(
        self: Console,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Patched Console.__init__ that forces UTF-8 encoding on Windows."""
        # If file/stderr not specified, wrap stderr with UTF-8
        if "file" not in kwargs and not any(arg == sys.stderr for arg in args):  # pragma: no branch
            # Create UTF-8 wrapper for stderr
            kwargs["file"] = io.TextIOWrapper(  # pragma: no cover
                sys.stderr.buffer,  # pragma: no cover
                encoding="utf-8",  # pragma: no cover
                errors="replace",  # pragma: no cover
                line_buffering=True,  # pragma: no cover
            )  # pragma: no cover
        # Set legacy_windows to False for better Unicode support
        kwargs.setdefault("legacy_windows", False)
        # Call original init
        _original_console_init(self, *args, **kwargs)

    # Apply monkey patch
    Console.__init__ = _patched_console_init


# ==============================================================================
# Type Aliases (Python 3.12+)
# ==============================================================================

type Exception_Context_Dict = dict[str, Any]
type Exception_Frame_List = list["Exception_Frame"]
type Sensitive_Field_Set = frozenset[str]


# ==============================================================================
# Constants
# ==============================================================================

# Thread lock for safe exception handling
_EXCEPTION_LOCK = threading.RLock()

# Default console for rich output with UTF-8 encoding
# Force UTF-8 to prevent UnicodeEncodeError with special characters like ❱
# Guard against environments (e.g. Robot Framework) that replace sys.stderr
# with a StringIO which has no .buffer attribute.
if hasattr(sys.stderr, "buffer"):
    _stderr_utf8 = io.TextIOWrapper(
        sys.stderr.buffer,
        encoding="utf-8",
        errors="replace",
        line_buffering=True,
    )
else:
    _stderr_utf8 = sys.stderr  # type: ignore[assignment]
_CONSOLE = Console(file=_stderr_utf8, force_terminal=True, legacy_windows=False)

# Maximum frames to display in traceback
MAX_TRACEBACK_FRAMES = 20

# Maximum variable string length before truncation
MAX_VARIABLE_LENGTH = 500

# Sensitive field names to mask in output
SENSITIVE_FIELDS = frozenset(
    {
        "password",
        "secret",
        "token",
        "api_key",
        "apikey",
        "api_secret",
        "private_key",
        "credentials",
        "ssn",
        "social_security",
        "credit_card",
        "card_number",
        "cvv",
        "pin",
    },
)


# ==============================================================================
# Enums
# ==============================================================================


class Exception_Format(Enum):  # type: ignore[misc]
    """Error output format modes.

    Per project coding standards, exception-related enums use Exception_ prefix.

    Attributes
    ----------
    SIMPLE : auto
        Basic error message only.
    STANDARD : auto
        Standard Python traceback format.
    RICH_TRACEBACK : auto
        Rich formatted traceback with colors and syntax highlighting.
    VARIABLES : auto
        Traceback with local variable values displayed.
    JSON : auto
        JSON-formatted error for structured logging.
    TABLE : auto
        Rich table format for console display.
    FULL : auto
        Combines rich traceback with variables and context.
    """

    SIMPLE = auto()
    STANDARD = auto()
    RICH_TRACEBACK = auto()
    VARIABLES = auto()
    JSON = auto()
    TABLE = auto()
    FULL = auto()


class Exception_Severity(Enum):  # type: ignore[misc]
    """Error severity levels.

    Per project coding standards, exception-related enums use Exception_ prefix.

    Attributes
    ----------
    DEBUG : auto
        Debug-level error for development.
    INFO : auto
        Informational error.
    WARNING : auto
        Warning-level error.
    ERROR : auto
        Error-level (default).
    CRITICAL : auto
        Critical error requiring immediate attention.
    """

    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


# ==============================================================================
# Data Classes
# ==============================================================================


@attrs.define(kw_only=True, frozen=True)
class Exception_Frame:
    """Represents a single frame in the error traceback.

    Per project coding standards, exception-related classes use Exception_ prefix.

    Attributes
    ----------
    filename : str
        Source file path.
    function : str
        Function name where error occurred.
    line_number : int
        Line number in source file.
    code_context : str
        Source code line at error location.
    local_variables : dict[str, Any]
        Local variables at error location.
    module : str
        Module name.
    """

    filename: str = attrs.field()
    function: str = attrs.field()
    line_number: int = attrs.field()
    code_context: str = attrs.field()
    local_variables: dict[str, Any] = attrs.field(factory=dict)
    module: str = attrs.field(default="")


@attrs.define(kw_only=True)
class Exception_Context:
    """Captures comprehensive error context information.

    Per project coding standards, exception-related classes use Exception_ prefix.

    Attributes
    ----------
    timestamp : datetime
        UTC timestamp when error occurred.
    exception_type : str
        Error class name.
    message : str
        Error message.
    filename : str
        Source file where error originated.
    function : str
        Function where error originated.
    line_number : int
        Line number where error originated.
    code_context : str
        Source code at error location.
    frames : list[Exception_Frame]
        Stack frames leading to error.
    thread_id : int
        Thread ID where error occurred.
    thread_name : str
        Thread name where error occurred.
    process_id : int
        Process ID.
    user_context : dict[str, Any]
        User-provided context data.
    severity : Exception_Severity
        Error severity level.
    exception_id : str
        Unique error identifier.
    """

    timestamp: datetime = attrs.field(factory=lambda: datetime.now(UTC))
    exception_type: str = attrs.field(default="")
    message: str = attrs.field(default="")
    filename: str = attrs.field(default="")
    function: str = attrs.field(default="")
    line_number: int = attrs.field(default=0)
    code_context: str = attrs.field(default="")
    frames: list[Exception_Frame] = attrs.field(factory=list)
    thread_id: int = attrs.field(default=0)
    thread_name: str = attrs.field(default="")
    process_id: int = attrs.field(default=0)
    user_context: dict[str, Any] = attrs.field(factory=dict)
    severity: Exception_Severity = attrs.field(default=Exception_Severity.ERROR)  # type: ignore[assignment]
    exception_id: str = attrs.field(default="")

    def __attrs_post_init__(self) -> None:
        """Initialize computed fields after creation."""
        import os

        if not self.thread_id:
            self.thread_id = threading.current_thread().ident or 0
        if not self.thread_name:
            self.thread_name = threading.current_thread().name
        if not self.process_id:
            self.process_id = os.getpid()
        if not self.exception_id:
            self.exception_id = f"EXC_{self.timestamp.strftime('%Y%m%d%H%M%S%f')}"


# ==============================================================================
# Helper Functions
# ==============================================================================


def _Mask_Sensitive_Data(*, data: dict[Any, Any]) -> dict[Any, Any]:
    """Mask sensitive data in dictionary values.

    Parameters
    ----------
    data : dict[Any, Any]
        Dictionary potentially containing sensitive data, including non-string keys.

    Returns
    -------
    dict[Any, Any]
        Dictionary with sensitive values masked.
    """
    masked: dict[Any, Any] = {}
    for key, value in data.items():
        key_lower = str(key).lower()
        if any(sensitive in key_lower for sensitive in SENSITIVE_FIELDS):
            masked[key] = "***MASKED***"
        elif isinstance(value, dict):
            masked[key] = _Mask_Sensitive_Data(data = value)
        else:
            masked[key] = value
    return masked


def _Truncate_Value(
    *, value: Any, max_length: int = MAX_VARIABLE_LENGTH) -> str:
    """Truncate value representation if too long.

    Parameters
    ----------
    value : Any
        Value to represent as string.
    max_length : int
        Maximum string length before truncation.

    Returns
    -------
    str
        Truncated string representation.
    """
    try:
        str_value = repr(value)
        if len(str_value) > max_length:
            return str_value[: max_length - 3] + "..."
        return str_value
    except Exception:
        return "<unrepresentable>"


def _Serialize_For_JSON(obj: Any) -> Any:
    """Serialize object for JSON output.

    Parameters
    ----------
    obj : Any
        Object to serialize.

    Returns
    -------
    Any
        JSON-serializable representation.
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, bytes):
        return obj.decode("utf-8", errors="replace")
    if isinstance(obj, Enum):
        return obj.name  # type: ignore[attr-defined]
    if isinstance(obj, Exception):
        return str(obj)
    if hasattr(obj, "__dict__"):
        return {k: _Serialize_For_JSON(obj = v) for k, v in obj.__dict__.items()}
    return str(obj)


def _Extract_Frames_From_Traceback(
    *, tb: TracebackType | None, max_frames: int = MAX_TRACEBACK_FRAMES) -> list[Exception_Frame]:
    """Extract detailed frame information from traceback.

    Parameters
    ----------
    tb : TracebackType | None
        Python traceback object.
    max_frames : int
        Maximum number of frames to extract.

    Returns
    -------
    list[Exception_Frame]
        List of exception frames with context.
    """
    frames = []
    frame_count = 0

    while tb is not None and frame_count < max_frames:
        frame = tb.tb_frame
        lineno = tb.tb_lineno
        filename = frame.f_code.co_filename
        function = frame.f_code.co_name
        module = frame.f_globals.get("__name__", "")

        # Get code context
        code_context = linecache.getline(filename, lineno).strip()

        # Extract local variables (mask sensitive data)
        local_vars = {}
        try:
            for var_name, var_value in frame.f_locals.items():
                if not var_name.startswith("_"):
                    local_vars[var_name] = _Truncate_Value(value = var_value)
            local_vars = _Mask_Sensitive_Data(data = local_vars)
        except Exception as exc:  # pragma: no cover  # reason: defensive stderr fallback, unreachable in normal execution
            sys.stderr.write(
                f"[exception_custom] Failed to extract locals in frame: {exc}\n",
            )

        frames.append(
            Exception_Frame(
                filename=filename,
                function=function,
                line_number=lineno,
                code_context=code_context,
                local_variables=local_vars,
                module=module,
            ),
        )

        tb = tb.tb_next
        frame_count += 1

    return frames


# ==============================================================================
# Root Exception
# ==============================================================================


class Exception_QWIM_Error(Exception):
    """Root exception for all QWIM project errors.

    All domain exceptions in this project inherit from ``Exception_QWIM_Error`` so
    callers can catch *any* project error with a single
    ``except Exception_QWIM_Error``
    clause without also catching unrelated stdlib errors.

    Parameters
    ----------
    message : str
        Human-readable error description.
    detail : dict[str, Any] | None
        Structured context passed at the raise site (optional).

    Examples
    --------
    >>> try:
    ...     raise Exception_Data_Validation_Error("weight must be in [0, 1]")
    ... except Exception_QWIM_Error as exc:
    ...     print(exc)  # caught by root handler
    """

    def __init__(self, message: str, *, detail: dict[str, Any] | None = None) -> None:
        """Initialise Exception_QWIM_Error with *message* and optional *detail* dict."""
        super().__init__(message)
        self.detail: dict[str, Any] = detail or {}


# ==============================================================================
# Lightweight typed subclasses of Exception_QWIM_Error
# (use these in inner-layer code that does not need the rich-traceback machinery)
# ==============================================================================


class Exception_Data_Validation_Error(Exception_QWIM_Error):
    """Raised when data fails a validation check at a system boundary.

    Use in place of bare ``ValueError`` when the offending value came from
    an external caller (Shiny input, HTTP body, CSV row, etc.).

    Parameters
    ----------
    message : str
        Description of the validation failure.
    field : str | None
        Name of the invalid field / column.
    value : object | None
        The rejected value (safe to log).
    detail : dict[str, Any] | None
        Additional structured context.

    Examples
    --------
    >>> raise Exception_Data_Validation_Error(
    ...     "portfolio weight must be in [0, 1]",
    ...     field="weight_equity",
    ...     value=1.5,
    ... )
    """

    def __init__(
        self,
        message: str,
        *,
        field: str | None = None,
        value: object | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        """Initialise with *message*, optional *field*, *value*, and *detail*."""
        ctx: dict[str, Any] = dict(detail or {})
        if field is not None:
            ctx["field"] = field
        if value is not None:
            ctx["value"] = value
        super().__init__(message, detail=ctx)
        self.field = field
        self.value = value


class Exception_Config_Error(Exception_QWIM_Error):
    """Raised when application configuration is missing or invalid.

    Use in place of bare ``KeyError`` / ``ValueError`` when a required
    configuration key is absent or has a wrong type/value.

    Parameters
    ----------
    message : str
        Description of the configuration problem.
    key : str | None
        The missing or invalid configuration key.
    detail : dict[str, Any] | None
        Additional structured context.

    Examples
    --------
    >>> raise Exception_Config_Error(
    ...     "QWIM_LOG_DIR must be set",
    ...     key="QWIM_LOG_DIR",
    ... )
    """

    def __init__(
        self,
        message: str,
        *,
        key: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        """Initialise with *message*, optional *key*, and *detail*."""
        ctx: dict[str, Any] = dict(detail or {})
        if key is not None:
            ctx["key"] = key
        super().__init__(message, detail=ctx)
        self.key = key


class Exception_External_Service_Error(Exception_QWIM_Error):
    """Raised when an external service (HTTP, yfinance, database) fails.

    Use to wrap transient / permanent failures from third-party services so
    callers do not need to import library-specific exception types.

    Parameters
    ----------
    message : str
        Description of the service failure.
    service : str | None
        Name of the failing service (e.g. ``"yfinance"``, ``"database"``).
    status_code : int | None
        HTTP status code, if applicable.
    detail : dict[str, Any] | None
        Additional structured context.

    Examples
    --------
    >>> raise Exception_External_Service_Error(
    ...     "Yahoo Finance download timed out",
    ...     service="yfinance",
    ... )
    """

    def __init__(
        self,
        message: str,
        *,
        service: str | None = None,
        status_code: int | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        """Initialise with *message*, optional *service*, *status_code*, and *detail*."""
        ctx: dict[str, Any] = dict(detail or {})
        if service is not None:
            ctx["service"] = service
        if status_code is not None:
            ctx["status_code"] = status_code
        super().__init__(message, detail=ctx)
        self.service = service
        self.status_code = status_code


class Exception_Serialization_Error(Exception_QWIM_Error):
    """Raised when msgspec / JSON / parquet serialization or deserialization fails.

    Use in place of bare ``TypeError`` / ``ValueError`` at encode/decode
    boundaries (e.g. ``msgspec.json.encode``, ``pl.read_parquet``).

    Parameters
    ----------
    message : str
        Description of the serialization failure.
    codec : str | None
        Codec name (e.g. ``"json"``, ``"msgpack"``, ``"parquet"``).
    detail : dict[str, Any] | None
        Additional structured context.

    Examples
    --------
    >>> raise Exception_Serialization_Error(
    ...     "cannot encode NaN as JSON",
    ...     codec="json",
    ... )
    """

    def __init__(
        self,
        message: str,
        *,
        codec: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        """Initialise with *message*, optional *codec*, and *detail*."""
        ctx: dict[str, Any] = dict(detail or {})
        if codec is not None:
            ctx["codec"] = codec
        super().__init__(message, detail=ctx)
        self.codec = codec


# ==============================================================================
# Module Exports
# ==============================================================================

__all__ = [
    "MAX_TRACEBACK_FRAMES",
    "MAX_VARIABLE_LENGTH",
    "SENSITIVE_FIELDS",
    "_CONSOLE",
    "_EXCEPTION_LOCK",
    "Exception_Config_Error",
    "Exception_Context",
    "Exception_Context_Dict",
    "Exception_Data_Validation_Error",
    "Exception_External_Service_Error",
    "Exception_Format",
    "Exception_Frame",
    "Exception_Frame_List",
    "Exception_QWIM_Error",
    "Exception_Serialization_Error",
    "Exception_Severity",
    "Sensitive_Field_Set",
    "_Extract_Frames_From_Traceback",
    "_Mask_Sensitive_Data",
    "_Serialize_For_JSON",
    "_Truncate_Value",
]

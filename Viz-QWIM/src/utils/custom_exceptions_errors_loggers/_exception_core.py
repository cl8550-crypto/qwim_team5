"""Exception_Custom — rich-traceback core exception class.

This private module implements :class:`Exception_Custom`, the enhanced
exception class with rich formatting, automatic context capture, and
multiple output formats.

All public symbols are re-exported by the parent façade module
:mod:`src.utils.custom_exceptions_errors_loggers.exception_custom`.

Do **not** import directly from this module; always import from
``exception_custom``.
"""

from __future__ import annotations

import inspect
import json
import linecache
import os
import sys

from io import StringIO
from typing import TYPE_CHECKING, Any, ClassVar, Self

from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from traceback_with_variables import iter_exc_lines

from ._exception_types_lightweight import (
    _CONSOLE,
    _EXCEPTION_LOCK,
    MAX_TRACEBACK_FRAMES,
    Exception_Context,
    Exception_Format,
    Exception_Frame,
    Exception_QWIM_Error,
    Exception_Severity,
    _Extract_Frames_From_Traceback,
    _Mask_Sensitive_Data,
    _Serialize_For_JSON,
    _Truncate_Value,
)


if TYPE_CHECKING:
    from rich.console import Console


# ==============================================================================
# Exception_Custom factory helper (for ProcessPoolExecutor pickling)
# ==============================================================================


def _Reconstruct_Exception(
    cls: type, message: str, exception_format: Exception_Format, severity: Exception_Severity, user_context: dict[str, Any] | None, suppress_traceback: bool) -> Exception_Custom:
    """Factory for unpickling :class:`Exception_Custom` and its subclasses.

    Bypasses subclass ``__init__`` (which may have incompatible
    positional-arg signatures) by using ``object.__new__`` + direct
    attribute assignment.  This ensures that custom exceptions raised
    inside :class:`ProcessPoolExecutor` workers can be sent back to the
    parent process without ``TypeError`` while preserving the base
    ``Exception_QWIM_Error.detail`` contract expected by normal instances.
    """
    obj = Exception.__new__(cls, message)
    Exception_QWIM_Error.__init__(obj, message)
    obj._message = message
    obj._exception_format = exception_format
    obj._severity = severity
    obj._user_context = user_context or {}
    obj._cause = None
    obj._suppress_traceback = suppress_traceback
    obj._exception_context = None
    return obj


# ==============================================================================
# Main Exception Class
# ==============================================================================


class Exception_Custom(Exception_QWIM_Error):
    """Enhanced base exception class with rich traceback support.

    This exception class provides comprehensive error reporting with multiple
    output formats, automatic context capture, and thread-safe operation.

    Parameters
    ----------
    message : str
        Primary exception message.
    exception_format : Exception_Format
        Output format mode (default: STANDARD).
    severity : Exception_Severity
        Exception severity level (default: ERROR).
    context : dict[str, Any] | None
        Additional context data to include.
    cause : Exception | None
        Original exception that caused this one.
    suppress_traceback : bool
        Whether to suppress traceback output (default: False).

    Attributes
    ----------
    exception_context : Exception_Context
        Captured exception context information.
    exception_format : Exception_Format
        Current output format mode.

    Class Attributes
    ----------------
    default_format : Exception_Format
        Default format for all instances.
    enable_variable_capture : bool
        Whether to capture local variables.
    console : Console
        Rich console for output.

    Examples
    --------
    >>> # Simple usage
    >>> raise Exception_Custom("Something went wrong")

    >>> # With rich traceback
    >>> raise Exception_Custom(
    ...     "Calculation failed",
    ...     exception_format=Exception_Format.RICH_TRACEBACK,
    ...     context={"operation": "portfolio_optimization"},
    ... )

    >>> # Get JSON representation
    >>> try:
    ...     risky_operation()
    ... except Exception as e:
    ...     exc = Exception_Custom.From_Exception(e)
    ...     print(exc.To_JSON())
    """

    # Class-level configuration
    default_format: ClassVar[Exception_Format] = Exception_Format.STANDARD  # type: ignore[assignment]
    enable_variable_capture: ClassVar[bool] = True
    console: ClassVar[Console] = _CONSOLE

    def __init__(
        self,
        message: str,
        *args: Any,
        exception_format: Exception_Format | None = None,
        severity: Exception_Severity = Exception_Severity.ERROR,  # type: ignore[assignment]
        context: dict[str, Any] | None = None,
        cause: Exception | None = None,
        suppress_traceback: bool = False,
    ) -> None:
        """Initialize enhanced exception with context capture."""
        super().__init__(message, *args)

        self._message = message

        # Determine output format
        if exception_format is not None:
            self._exception_format = exception_format
        else:
            # Check environment variable for default format override
            env_fmt = os.environ.get("QWIM_EXCEPTION_FORMAT")
            if env_fmt and env_fmt in Exception_Format.__members__:
                self._exception_format = Exception_Format[env_fmt]  # type: ignore[index]
            else:
                self._exception_format = self.default_format

        self._severity = severity
        self._user_context = context or {}
        self._cause = cause
        self._suppress_traceback = suppress_traceback
        self._exception_context: Exception_Context | None = None

        # Capture context automatically
        with _EXCEPTION_LOCK:
            self._Capture_Context()

        # Set __cause__ for exception chaining
        if cause is not None:
            self.__cause__ = cause

    def _Capture_Context(self) -> None:
        """Capture exception context from current execution state."""
        # Get current exception info
        exc_type, exc_value, exc_tb = sys.exc_info()

        # If no active exception, use inspection to get caller info
        if exc_tb is None:
            # Get caller frame (skip __init__ and _capture_context)
            frame = inspect.currentframe()
            if frame is not None:  # pragma: no branch
                # Walk up the stack to find the actual caller
                # Base depth: 2 (_capture_context, __init__)
                depth = 2
                # If this is a subclass instantiating via its own __init__, skip one more
                if self.__class__.__name__ != "Exception_Custom":
                    depth = 3

                for _ in range(depth):  # Skip internal frames
                    if frame.f_back is not None:  # pragma: no branch
                        frame = frame.f_back

                filename = frame.f_code.co_filename
                function = frame.f_code.co_name
                line_number = frame.f_lineno
                code_context = linecache.getline(filename, line_number).strip()

                # Capture stack frames from this point
                captured_frames = []
                current_frame = frame
                frame_count = 0

                while current_frame is not None and frame_count < MAX_TRACEBACK_FRAMES:
                    try:
                        f_locals = {}
                        if self.enable_variable_capture:
                            for k, v in current_frame.f_locals.items():
                                if not k.startswith("_"):
                                    f_locals[k] = _Truncate_Value(value = v)
                            f_locals = _Mask_Sensitive_Data(data = f_locals)

                        f_code = current_frame.f_code
                        captured_frames.append(
                            Exception_Frame(
                                filename=f_code.co_filename,
                                function=f_code.co_name,
                                line_number=current_frame.f_lineno,
                                code_context=linecache.getline(
                                    f_code.co_filename,
                                    current_frame.f_lineno,
                                ).strip(),
                                local_variables=f_locals,
                                module=current_frame.f_globals.get("__name__", ""),
                            ),
                        )
                    except Exception as exc:  # pragma: no cover  # reason: defensive stderr fallback, unreachable in normal execution
                        sys.stderr.write(
                            f"[exception_custom] Failed to capture frame: {exc}\n",
                        )

                    current_frame = current_frame.f_back
                    frame_count += 1

                self._exception_context = Exception_Context(
                    exception_type=self.__class__.__name__,
                    message=self._message,
                    filename=filename,
                    function=function,
                    line_number=line_number,
                    code_context=code_context,
                    frames=captured_frames,
                    user_context=_Mask_Sensitive_Data(data = self._user_context),
                    severity=self._severity,
                )
        else:
            # Extract frames from actual traceback
            frames = _Extract_Frames_From_Traceback(tb = exc_tb)

            # Get origin frame info
            origin_frame = frames[0] if frames else None

            self._exception_context = Exception_Context(
                exception_type=exc_type.__name__ if exc_type else self.__class__.__name__,
                message=str(exc_value) if exc_value else self._message,
                filename=origin_frame.filename if origin_frame else "",
                function=origin_frame.function if origin_frame else "",
                line_number=origin_frame.line_number if origin_frame else 0,
                code_context=origin_frame.code_context if origin_frame else "",
                frames=frames,
                user_context=_Mask_Sensitive_Data(data = self._user_context),
                severity=self._severity,
            )

    @classmethod
    def From_Exception(
        cls, *, exception: Exception, exception_format: Exception_Format | None = None, context: dict[str, Any] | None = None, severity: Exception_Severity = Exception_Severity.ERROR) -> Self:
        """Create Exception_Custom from an existing exception.

        Parameters
        ----------
        exception : Exception
            Original exception to wrap.
        exception_format : Exception_Format | None
            Output format mode.
        context : dict[str, Any] | None
            Additional context data.
        severity : Exception_Severity
            Exception severity level.

        Returns
        -------
        Self
            New Exception_Custom instance wrapping the original.
        """
        return cls(
            message=str(exception),
            exception_format=exception_format,
            cause=exception,
            context=context,
            severity=severity,
        )

    @property
    def Message(self) -> str:
        """Get exception message.

        Returns
        -------
        str
            The exception message.
        """
        return self._message

    @property
    def Severity(self) -> Exception_Severity:
        """Get exception severity level.

        Returns
        -------
        Exception_Severity
            The severity level.
        """
        return self._severity

    @property
    def Exception_Context(self) -> Exception_Context:
        """Get captured exception context."""
        if self._exception_context is None:
            self._Capture_Context()
        assert self._exception_context is not None, (
            "Exception context must be set after _capture_context()"
        )
        return self._exception_context

    @property
    def Exception_Format_Value(self) -> Exception_Format:
        """Get current exception format."""
        return self._exception_format

    @Exception_Format_Value.setter
    def Exception_Format_Value(
        self,
        value: Exception_Format,
    ) -> None:
        """Set exception format."""
        self._exception_format = value

    def __str__(self) -> str:
        """Return formatted exception string based on current format."""
        if self._suppress_traceback:
            return self._message

        if self._exception_format == Exception_Format.SIMPLE:
            return self._Format_Simple()
        if self._exception_format == Exception_Format.JSON:
            return self.To_JSON()
        if self._exception_format in {
            Exception_Format.RICH_TRACEBACK,
            Exception_Format.TABLE,
            Exception_Format.FULL,
        }:
            # Rich formats should use Print_Rich() for proper display.
            return self._Format_Simple()

        return self._Format_Standard()

    def __repr__(self) -> str:
        """Return detailed representation with literal message characters."""
        return (
            f"{self.__class__.__name__}("
            f"message='{self._message}', "
            f"format={self._exception_format.name}, "
            f"severity={self._severity.name})"
        )

    def __reduce__(self) -> tuple[Any, ...]:
        """Support for pickling (serialization).

        Uses a factory function to bypass subclass ``__init__`` signatures,
        which differ from the base class and would cause ``TypeError`` on
        unpickling (e.g. inside :class:`ProcessPoolExecutor` workers).

        Returns
        -------
        tuple
            Reduce tuple for reconstruction via :func:`_Reconstruct_Exception`.
        """
        return (
            _Reconstruct_Exception,
            (
                self.__class__,
                self._message,
                self._exception_format,
                self._severity,
                self._user_context,
                self._suppress_traceback,
            ),
        )

    def Log(
        self, *, logger: Any | None = None, level: str | None = None) -> None:
        """Log this exception using a provided logger or default custom logger.

        Parameters
        ----------
        logger : Any | None
            Logger instance. If None, uses
            src.utils.custom_exceptions_errors_loggers.logger_custom.get_logger.
        level : str | None
            Log level (e.g., "ERROR", "WARNING"). If None, uses exception severity.
        """
        log_level = level or self._severity.name
        message = str(self)

        # Default to custom logger if none provided
        if logger is None:
            try:
                from src.utils.custom_exceptions_errors_loggers.logger_custom import (
                    get_logger,
                )

                # Try to use filename from context as logger name
                name = self.Exception_Context.filename or "exception_custom"
                logger = get_logger(name = name)
            except (ImportError, RuntimeError):
                # Fallback if logger_custom not available or setup
                sys.stderr.write(f"[{log_level}] {message}\n")
                return

        if hasattr(logger, "opt"):  # Loguru (from logger_custom)
            # Use opt(exception=self) to include structured traceback info
            # This leverages loguru's backtrace/diagnose features
            logger.opt(exception=self).log(log_level, message)
        elif hasattr(logger, "log"):  # Standard logging fallback
            import logging

            level_mapping = {
                "DEBUG": logging.DEBUG,
                "INFO": logging.INFO,
                "WARNING": logging.WARNING,
                "ERROR": logging.ERROR,
                "CRITICAL": logging.CRITICAL,
            }
            lvl = level_mapping.get(log_level.upper(), logging.ERROR)
            logger.log(lvl, message, exc_info=True)
        else:
            # Simple print fallback
            sys.stderr.write(f"[{log_level}] {message}\n")

    def _Format_Simple(self) -> str:
        """Format exception as simple message.

        Returns
        -------
        str
            Simple exception message.
        """
        ctx = self.Exception_Context
        return f"{ctx.exception_type}: {self._message}"

    def _Format_Standard(self) -> str:
        """Format exception with standard Python traceback style.

        Returns
        -------
        str
            Standard formatted traceback.
        """
        ctx = self.Exception_Context
        lines = ["Traceback (most recent call last):"]

        for frame in ctx.frames:
            lines.append(
                f'  File "{frame.filename}", line {frame.line_number}, in {frame.function}',
            )
            if frame.code_context:
                lines.append(f"    {frame.code_context}")

        lines.append(f"{ctx.exception_type}: {self._message}")

        if ctx.user_context:
            lines.append("\nContext:")
            for key, value in ctx.user_context.items():
                lines.append(f"  {key}: {value}")

        return "\n".join(lines)

    def To_JSON(
        self, *, indent: int = 2) -> str:
        """Convert exception to JSON string.

        Parameters
        ----------
        indent : int
            JSON indentation level (default: 2). Boolean values use the
            default indentation path.

        Returns
        -------
        str
            JSON-formatted exception.
        """
        if isinstance(indent, bool):
            indent = 2

        ctx = self.Exception_Context
        data = {
            "exception_id": ctx.exception_id,
            "timestamp": ctx.timestamp.isoformat(),
            "exception_type": ctx.exception_type,
            "message": self._message,
            "severity": ctx.severity.name,
            "location": {
                "filename": ctx.filename,
                "function": ctx.function,
                "line_number": ctx.line_number,
                "code_context": ctx.code_context,
            },
            "thread": {
                "id": ctx.thread_id,
                "name": ctx.thread_name,
            },
            "process_id": ctx.process_id,
            "context": ctx.user_context,
            "frames": [
                {
                    "filename": f.filename,
                    "function": f.function,
                    "line_number": f.line_number,
                    "code_context": f.code_context,
                    "module": f.module,
                    "variables": f.local_variables if self.enable_variable_capture else {},
                }
                for f in ctx.frames
            ],
        }

        if self._cause is not None:
            data["caused_by"] = {
                "type": type(self._cause).__name__,
                "message": str(self._cause),
            }

        return json.dumps(data, default=_Serialize_For_JSON, indent=indent)

    def To_Dict(self) -> dict[str, Any]:
        """Convert exception to dictionary.

        Returns
        -------
        dict[str, Any]
            Dictionary representation of exception.
        """
        return json.loads(self.To_JSON())

    def Print_Rich(
        self, *, console: Console | None = None) -> None:
        """Print rich formatted traceback to console.

        Parameters
        ----------
        console : Console | None
            Rich console to use (default: class console).
        """
        console = console or self.console
        ctx = self.Exception_Context

        with _EXCEPTION_LOCK:
            if self._exception_format == Exception_Format.TABLE:
                self._Print_Table(console = console, ctx = ctx)
            elif self._exception_format == Exception_Format.FULL:
                self._Print_Full(console = console, ctx = ctx)
            else:
                self._Print_Rich_Traceback(console = console, ctx = ctx)

    def _Print_Rich_Traceback(
        self, *, console: Console, ctx: Exception_Context) -> None:
        """Print rich-formatted traceback.

        Parameters
        ----------
        console : Console
            Rich console for output.
        ctx : Exception_Context
            Exception context information.
        """
        # Create header panel
        header = Text()
        header.append(f"⚠️  {ctx.exception_type}", style="bold red")
        header.append(f"\n{self._message}", style="white")

        console.print(Panel(header, title="Exception", border_style="red"))

        # Print location info
        location_table = Table(show_header=False, box=None)
        location_table.add_row("📁 File:", ctx.filename)
        location_table.add_row("📍 Function:", ctx.function)
        location_table.add_row("📌 Line:", str(ctx.line_number))
        location_table.add_row("🕐 Time:", ctx.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"))
        console.print(location_table)

        # Print code context with syntax highlighting
        if ctx.code_context:
            console.print("\n[bold]Code Context:[/bold]")
            syntax = Syntax(
                ctx.code_context,
                "python",
                theme="monokai",
                line_numbers=True,
                start_line=ctx.line_number,
            )
            console.print(syntax)

        # Print user context if available
        if ctx.user_context:
            console.print("\n[bold]Context Data:[/bold]")
            context_table = Table(show_header=True, header_style="bold cyan")
            context_table.add_column("Key")
            context_table.add_column("Value")
            for key, value in ctx.user_context.items():
                context_table.add_row(str(key), str(value))
            console.print(context_table)

        # Print stack frames if available
        if ctx.frames and len(ctx.frames) > 1:
            console.print("\n[bold]Stack Trace:[/bold]")
            for i, frame in enumerate(ctx.frames):
                console.print(
                    f"  [dim]#{i + 1}[/dim] {frame.function} "
                    f"[dim]({frame.filename}:{frame.line_number})[/dim]",
                )

    def _Print_Table(
        self, *, console: Console, ctx: Exception_Context) -> None:
        """Print exception as rich table.

        Parameters
        ----------
        console : Console
            Rich console for output.
        ctx : Exception_Context
            Exception context information.
        """
        table = Table(
            title=f"Exception: {ctx.exception_type}",
            show_header=True,
            header_style="bold red",
        )
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Exception ID", ctx.exception_id)
        table.add_row("Timestamp", ctx.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"))
        table.add_row("Severity", ctx.severity.name)
        table.add_row("Message", self._message)
        table.add_row("File", ctx.filename)
        table.add_row("Function", ctx.function)
        table.add_row("Line", str(ctx.line_number))
        table.add_row("Thread", f"{ctx.thread_name} ({ctx.thread_id})")
        table.add_row("Process ID", str(ctx.process_id))

        if ctx.user_context:
            table.add_row("Context", json.dumps(ctx.user_context, indent=2))

        console.print(table)

    def _Print_Full(
        self, *, console: Console, ctx: Exception_Context) -> None:
        """Print full exception with variables.

        Parameters
        ----------
        console : Console
            Rich console for output.
        ctx : Exception_Context
            Exception context information.
        """
        # Print rich traceback first
        self._Print_Rich_Traceback(console = console, ctx = ctx)

        # Print variables from each frame
        if self.enable_variable_capture and ctx.frames:
            console.print("\n[bold magenta]Local Variables by Frame:[/bold magenta]")
            for i, frame in enumerate(ctx.frames):
                if frame.local_variables:
                    var_table = Table(
                        title=f"Frame #{i + 1}: {frame.function}",
                        show_header=True,
                    )
                    var_table.add_column("Variable", style="green")
                    var_table.add_column("Value", style="white")
                    for var_name, var_value in frame.local_variables.items():
                        var_table.add_row(var_name, str(var_value))
                    console.print(var_table)

        # Print traceback with variables using traceback_with_variables
        if self.__cause__ is not None:
            console.print("\n[bold yellow]Traceback with Variables:[/bold yellow]")
            try:
                output = StringIO()
                for line in iter_exc_lines(self.__cause__):
                    output.write(line + "\n")
                console.print(output.getvalue())
            except Exception as exc:  # pragma: no cover  # reason: defensive stderr fallback, unreachable in normal execution
                sys.stderr.write(
                    f"[exception_custom] Failed to render traceback-with-variables: {exc}\n",
                )

    def Get_Traceback_String(self) -> str:
        """Get traceback as string using traceback-with-variables.

        Returns
        -------
        str
            Formatted traceback string with variables.
        """
        output = StringIO()
        if self.__cause__ is not None:
            for line in iter_exc_lines(self.__cause__):
                output.write(line + "\n")
        else:
            output.write(self._Format_Standard())
        return output.getvalue()

    @classmethod
    def Install_Rich_Traceback(
        cls,
        **kwargs: Any,
    ) -> None:
        """Install rich traceback handler globally.

        Parameters
        ----------
        **kwargs : Any
            Arguments passed to rich.traceback.install().
        """
        from rich.traceback import install

        install(
            console=cls.console,
            show_locals=cls.enable_variable_capture,
            **kwargs,
        )


# ==============================================================================
# Module Exports
# ==============================================================================

__all__ = [
    "Exception_Custom",
    "_Reconstruct_Exception",
]

"""Traceback customization module.

This module provides custom traceback formatting and handling utilities
for QWIM project exceptions.

Functions
---------
Format_Traceback_Compact
    Format a traceback into a compact, single-line-per-frame string.
Format_Traceback_Context
    Format a traceback with surrounding source context lines.
Extract_Relevant_Frames
    Extract only project-relevant frames from a traceback.
"""

from __future__ import annotations

import traceback

from pathlib import Path
from types import TracebackType

from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name = __name__)

# Project root for filtering frames to project-relevant ones
_PROJECT_ROOT = str(Path(__file__).resolve().parents[3])


def _Validate_Context_Lines_QWIM(*, context_lines: int) -> int:
    """Validate and normalize the traceback context window size.

    Parameters
    ----------
    context_lines : int
        Number of source context lines to show before and after the failing
        line.

    Returns
    -------
    int
        Validated non-negative context line count.

    Raises
    ------
    TypeError
        Raised when ``context_lines`` is not an integer.
    ValueError
        Raised when ``context_lines`` is negative.
    """
    if isinstance(context_lines, bool) or not isinstance(context_lines, int):
        raise TypeError("context_lines must be an integer")

    if context_lines < 0:
        raise ValueError("context_lines must be non-negative")

    return context_lines


def _Resolve_Project_Root_QWIM(*, project_root: str | None) -> str:
    """Validate and normalize the optional project-root override.

    Parameters
    ----------
    project_root : str | None
        Optional project-root override used to filter traceback frames.

    Returns
    -------
    str
        Normalized project-root string.

    Raises
    ------
    TypeError
        Raised when ``project_root`` is neither ``None`` nor a string.
    ValueError
        Raised when ``project_root`` is blank after trimming whitespace.
    """
    if project_root is None:
        return _PROJECT_ROOT

    if not isinstance(project_root, str):
        raise TypeError("project_root must be a string or None")

    normalized_root = project_root.strip()
    if normalized_root == "":
        raise ValueError("project_root must be a non-empty string when provided")

    return normalized_root


def Format_Traceback_Compact(
    *, exc_type: type[BaseException], exc_value: BaseException, exc_tb: TracebackType | None) -> str:
    """Format a traceback into a compact string with one line per frame.

    Parameters
    ----------
    exc_type : type[BaseException]
        The exception class.
    exc_value : BaseException
        The exception instance.
    exc_tb : TracebackType | None
        The traceback object, or None if unavailable.

    Returns
    -------
    str
        Compact traceback string with one line per frame, ending with the
        exception type and message.

    Examples
    --------
    >>> try:
    ...     raise ValueError("bad value")
    ... except ValueError:
    ...     text = Format_Traceback_Compact(*sys.exc_info())
    >>> "ValueError: bad value" in text
    True
    """
    if exc_tb is None:
        return f"{exc_type.__name__}: {exc_value}"

    frames = traceback.extract_tb(exc_tb)
    lines: list[str] = [
        f"  {frame.filename}:{frame.lineno} in {frame.name} -> {frame.line}" for frame in frames
    ]
    lines.append(f"{exc_type.__name__}: {exc_value}")
    return "\n".join(lines)


def Format_Traceback_Context(
    *, exc_type: type[BaseException], exc_value: BaseException, exc_tb: TracebackType | None, context_lines: int = 3) -> str:
    """Format a traceback with surrounding source-code context.

    Parameters
    ----------
    exc_type : type[BaseException]
        The exception class.
    exc_value : BaseException
        The exception instance.
    exc_tb : TracebackType | None
        The traceback object.
    context_lines : int, optional
        Number of context lines to show before and after the error line,
        by default 3.

    Returns
    -------
    str
        Formatted traceback string with source context.

    Examples
    --------
    >>> try:
    ...     raise RuntimeError("test")
    ... except RuntimeError:
    ...     text = Format_Traceback_Context(*sys.exc_info(), context_lines=2)
    >>> "RuntimeError: test" in text
    True
    """
    validated_context_lines = _Validate_Context_Lines_QWIM(context_lines = context_lines)

    if exc_tb is None:
        return f"{exc_type.__name__}: {exc_value}"

    frames = traceback.extract_tb(exc_tb)
    output_parts: list[str] = []

    for frame in frames:
        line_number = frame.lineno
        output_parts.append(
            f'\n  File "{frame.filename}", line {line_number}, in {frame.name}',
        )

        if line_number is None:
            output_parts.append(f"    {frame.line}")
            continue

        source_path = Path(frame.filename)
        if source_path.is_file():
            try:
                all_lines = source_path.read_text(encoding="utf-8").splitlines()
                start_line = max(0, line_number - validated_context_lines - 1)
                end_line = min(len(all_lines), line_number + validated_context_lines)

                for line_num in range(start_line, end_line):
                    marker = " >> " if line_num == line_number - 1 else "    "
                    output_parts.append(
                        f"    {marker}{line_num + 1:4d} | {all_lines[line_num]}",
                    )
            except OSError:
                output_parts.append(f"    {frame.line}")
        else:
            output_parts.append(f"    {frame.line}")

    output_parts.append(f"\n{exc_type.__name__}: {exc_value}")
    return "\n".join(output_parts)


def Extract_Relevant_Frames(
    *, exc_tb: TracebackType | None, project_root: str | None = None) -> list[traceback.FrameSummary]:
    """Extract only project-relevant frames from a traceback.

    Filters out frames from standard library and third-party packages,
    keeping only frames whose source files reside under the project root.

    Parameters
    ----------
    exc_tb : TracebackType | None
        The traceback object.
    project_root : str | None, optional
        Root path to filter frames by. Defaults to the detected project root.

    Returns
    -------
    list[traceback.FrameSummary]
        List of frames originating from project source files.

    Examples
    --------
    >>> try:
    ...     raise KeyError("missing")
    ... except KeyError:
    ...     frames = Extract_Relevant_Frames(sys.exc_info()[2])
    >>> all("traceback_custom" in f.filename for f in frames)
    True
    """
    if exc_tb is None:
        return []

    root = _Resolve_Project_Root_QWIM(project_root = project_root)
    all_frames = traceback.extract_tb(exc_tb)

    return [frame for frame in all_frames if frame.filename.startswith(root)]


__all__ = [
    "Extract_Relevant_Frames",
    "Format_Traceback_Compact",
    "Format_Traceback_Context",
]

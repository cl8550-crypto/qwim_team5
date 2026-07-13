"""Typst compilation utilities for QWIM reporting workflows.

This module centralizes Typst executable resolution, command construction,
and PDF compilation so reporting code can share one cross-platform boundary.
The public API preserves the repository's current tuple-based success/error
contract instead of raising raw subprocess errors at the call site.
"""

from __future__ import annotations

import shutil
import subprocess

from pathlib import Path
from time import perf_counter
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from collections.abc import Callable

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Not_Found,
    Exception_Timeout,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


DEFAULT_TYPST_TIMEOUT_SECONDS = 120

_logger = get_logger(name = __name__)


def _resolve_typst_timeout_seconds_QWIM(*, timeout_seconds: int) -> int:
    """Return a safe Typst timeout while keeping booleans on the default path."""
    if isinstance(timeout_seconds, bool):
        return DEFAULT_TYPST_TIMEOUT_SECONDS
    return timeout_seconds


def _validate_output_pdf_QWIM(
    *, output_pdf_path: Path) -> tuple[bool, str]:
    """Validate that a compiled PDF exists and is non-empty.

    Parameters
    ----------
    output_pdf_path : pathlib.Path
        Output path expected to contain the compiled PDF.

    Returns
    -------
    tuple[bool, str]
        Success flag and status message.
    """
    if not output_pdf_path.exists():
        return False, "Compilation appeared to succeed but PDF not found"

    file_size = output_pdf_path.stat().st_size
    if file_size == 0:
        return False, "Compiled PDF is empty (0 bytes)"

    return True, f"Typst PDF compiled successfully ({file_size:,} bytes)"


def resolve_typst_executable_path_QWIM(
    *, typst_executable_name: str = "typst", _which_func: Callable[[str], str | None] | None = None) -> Path | None:
    """Resolve the Typst executable path when available.

    Parameters
    ----------
    typst_executable_name : str
        Executable name to resolve, typically ``"typst"``.
    _which_func : collections.abc.Callable[[str], str | None] | None
        Optional test seam for executable lookup. Defaults to ``shutil.which``.

    Returns
    -------
    pathlib.Path | None
        Resolved executable path, or ``None`` when Typst is not discoverable.
    """
    which_func = _which_func if _which_func is not None else shutil.which
    executable_text = which_func(typst_executable_name)
    if executable_text is None:
        return None
    return Path(executable_text).expanduser().resolve()


def build_typst_compile_command_QWIM(
    *, typst_executable_path: Path | None, typst_file_path: Path, output_pdf_path: Path) -> list[str]:
    """Build the Typst CLI compile command.

    Parameters
    ----------
    typst_executable_path : pathlib.Path | None
        Resolved Typst executable path when available.
    typst_file_path : pathlib.Path
        Input Typst source file path.
    output_pdf_path : pathlib.Path
        Output PDF path.

    Returns
    -------
    list[str]
        Command vector passed directly to ``subprocess.run``.

    Notes
    -----
    When ``typst_executable_path`` is ``None`` the command falls back to the
    bare ``typst`` executable name so the operating system can still resolve
    it from ``PATH`` at launch time.
    """
    executable_text = "typst"
    if typst_executable_path is not None:
        executable_text = str(typst_executable_path)

    return [
        executable_text,
        "compile",
        str(typst_file_path),
        str(output_pdf_path),
    ]


def compile_typst_document_to_pdf_QWIM(
    *, typst_file_path: Path, output_pdf_path: Path, timeout_seconds: int = DEFAULT_TYPST_TIMEOUT_SECONDS, _typst_module: Any | None = None, _which_func: Callable[[str], str | None] | None = None, _subprocess_run: Callable[..., Any] | None = None) -> tuple[bool, str]:
    """Compile a Typst source document to PDF.

    Parameters
    ----------
    typst_file_path : pathlib.Path
        Input Typst source file.
    output_pdf_path : pathlib.Path
        Destination PDF path.
    timeout_seconds : int
        Timeout for CLI compilation fallback.
    _typst_module : Any | None
        Optional injected Typst Python module for tests.
    _which_func : collections.abc.Callable[[str], str | None] | None
        Optional injected executable resolver for tests.
    _subprocess_run : collections.abc.Callable[..., Any] | None
        Optional injected ``subprocess.run`` replacement for tests.

    Returns
    -------
    tuple[bool, str]
        ``(success, message)`` describing the compilation outcome.

    Notes
    -----
    The function tries the Typst Python bindings first and then falls back to
    the CLI path. This preserves compatibility across local Windows setups and
    Linux deployment targets where one backend may be present without the other.
    """
    timeout_seconds = _resolve_typst_timeout_seconds_QWIM(timeout_seconds = timeout_seconds)

    try:
        if not typst_file_path.exists():
            raise Exception_Not_Found(f"Typst source file not found: {typst_file_path}")

        output_pdf_path.parent.mkdir(parents=True, exist_ok=True)

        compile_error_text = ""
        typst_module = _typst_module

        if typst_module is None:
            try:
                typst_module = __import__("typst")
            except ImportError:
                typst_module = None

        if typst_module is not None:
            try:
                time_start = perf_counter()
                typst_module.compile(str(typst_file_path), output=str(output_pdf_path))
                elapsed_seconds = perf_counter() - time_start
                _logger.info(
                    "Typst Python binding compiled %s in %.3f seconds",
                    typst_file_path,
                    elapsed_seconds,
                )
                return _validate_output_pdf_QWIM(output_pdf_path = output_pdf_path)
            except Exception as typst_package_error:  # noqa: BLE001
                compile_error_text = str(typst_package_error)
                _logger.warning(
                    "Typst Python binding failed for %s: %s",
                    typst_file_path,
                    typst_package_error,
                )

        typst_executable_path = resolve_typst_executable_path_QWIM(
            _which_func=_which_func,
        )
        typst_command = build_typst_compile_command_QWIM(
            typst_executable_path = typst_executable_path,
            typst_file_path = typst_file_path,
            output_pdf_path = output_pdf_path,
        )
        subprocess_run = _subprocess_run if _subprocess_run is not None else subprocess.run

        try:
            time_start = perf_counter()
            result = subprocess_run(
                typst_command,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
            elapsed_seconds = perf_counter() - time_start
            _logger.info(
                "Typst CLI compiled %s in %.3f seconds",
                typst_file_path,
                elapsed_seconds,
            )
        except subprocess.TimeoutExpired:
            timeout_error = Exception_Timeout(
                f"Typst compilation timed out after {timeout_seconds} seconds",
            )
            _logger.warning("%s", timeout_error)
            return False, str(timeout_error)
        except FileNotFoundError:
            not_found_message = (
                "typst CLI not found. Install via `pip install typst` or "
                "download from https://typst.app"
            )
            if compile_error_text:
                return False, f"Typst compilation failed: {compile_error_text}. {not_found_message}"
            return False, f"Typst compilation failed: {not_found_message}"

        if result.returncode != 0:
            compile_error_text = result.stderr or result.stdout or "Unknown Typst CLI failure"
            return False, f"Typst compilation failed: {compile_error_text}"

        return _validate_output_pdf_QWIM(output_pdf_path = output_pdf_path)

    except Exception_Not_Found as not_found_error:
        return False, str(not_found_error)
    except Exception as compilation_error:  # noqa: BLE001
        _logger.warning(
            "Unexpected Typst compilation error for %s: %s",
            typst_file_path,
            compilation_error,
        )
        return False, f"Unexpected error during Typst compilation: {compilation_error}"

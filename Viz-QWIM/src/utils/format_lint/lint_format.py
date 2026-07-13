"""Linting and formatting utilities for Python files using Ruff.

This module provides a small command-execution boundary for linting and
formatting Python files or directories with Ruff. Internal Ruff calls are
built as explicit argv lists so path handling remains safe across Windows
and Linux environments and does not rely on ``shell=True``.
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys

from collections.abc import Sequence
from pathlib import Path

from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name = __name__)
RUFF_EXECUTABLE = "ruff"


def _normalize_command_arguments_QWIM(
    *, command: str | Sequence[str | Path]) -> list[str]:
    """Normalize a command specification into a subprocess argv list.

    Parameters
    ----------
    command : str | collections.abc.Sequence[str | pathlib.Path]
        Command specification. Strings are tokenized with ``shlex.split`` for
        backward compatibility. Sequences are converted to strings directly.

    Returns
    -------
    list[str]
        Normalized argv list suitable for ``subprocess.run``.

    Raises
    ------
    ValueError
        If the command is empty or contains empty arguments.
    TypeError
        If *command* is neither a string nor a sequence.
    """
    if isinstance(command, str):
        command_text = command.strip()
        if not command_text:
            raise ValueError("Command cannot be empty")
        command_arguments = shlex.split(
            command_text,
            posix=sys.platform != "win32",
        )
    elif isinstance(command, Sequence):
        command_arguments = [str(item_part) for item_part in command]
    else:
        raise TypeError("Command must be a string or sequence of arguments")

    if not command_arguments:
        raise ValueError("Command cannot be empty")

    if any(not item_argument for item_argument in command_arguments):
        raise ValueError("Command arguments cannot be empty")

    return command_arguments


def _build_ruff_command_QWIM(
    action_name: str,
    target_path: Path,
    *command_options: str,
) -> list[str]:
    """Build a Ruff command as an argv list.

    Parameters
    ----------
    action_name : str
        Ruff action name. Supported values are ``"check"`` and ``"format"``.
    target_path : pathlib.Path
        File or directory passed to Ruff.
    *command_options : str
        Additional Ruff options such as ``"--fix"``.

    Returns
    -------
    list[str]
        Ruff argv list.

    Raises
    ------
    ValueError
        If *action_name* is not a supported Ruff action.
    """
    valid_actions = {"check", "format"}
    if action_name not in valid_actions:
        raise ValueError(f"Unsupported Ruff action: {action_name}")

    return [RUFF_EXECUTABLE, action_name, *command_options, str(target_path)]


def _run_ruff_pipeline_QWIM(
    *, target_path: Path) -> int:
    """Run the standard Ruff lint-and-format pipeline for one target.

    Parameters
    ----------
    target_path : pathlib.Path
        File or directory to process.

    Returns
    -------
    int
        Return code from the final ``ruff check`` command.
    """
    target_label = str(target_path)

    _logger.info("Step 1: Checking for issues in {}", target_label)
    run_command(command = _build_ruff_command_QWIM("check", target_path))

    _logger.info("Step 2: Fixing automatically fixable issues in {}", target_label)
    run_command(command = _build_ruff_command_QWIM("check", target_path, "--fix"))

    _logger.info("Step 3: Formatting {}", target_label)
    run_command(command = _build_ruff_command_QWIM("format", target_path))

    _logger.info("Step 4: Final check for remaining issues in {}", target_label)
    final_code = run_command(command = _build_ruff_command_QWIM("check", target_path))

    _logger.info("Linting and formatting completed!")
    return final_code


def run_command(
    *, command: str | Sequence[str | Path]) -> int:
    """Run a command and log its output.

    Parameters
    ----------
    command : str | collections.abc.Sequence[str | pathlib.Path]
        Command specification. Strings are supported for backward
        compatibility, but explicit argv sequences are preferred.

    Returns
    -------
    int
        The return code from the command execution.
    """
    try:
        normalized_command = _normalize_command_arguments_QWIM(command = command)
    except (TypeError, ValueError) as command_error:
        _logger.error("Invalid command specification: {}", command_error)
        return 1

    try:
        result = subprocess.run(
            normalized_command,
            shell=False,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as command_error:
        _logger.error(
            "Command execution failed for {}: {}",
            normalized_command[0],
            command_error,
        )
        return 1

    stdout_text = result.stdout.strip()
    stderr_text = result.stderr.strip()

    if stdout_text:
        _logger.info(stdout_text)
    if stderr_text:
        _logger.error(stderr_text)

    return int(result.returncode)


def lint_and_format_file(
    *, file_path: str | Path) -> int:
    """Run Ruff linting and formatting on a single file.

    Parameters
    ----------
    file_path : str | pathlib.Path
        Path to the Python file to lint and format.

    Returns
    -------
    int
        Final return code (0 if all checks pass).

    Notes
    -----
    This function performs the following steps:
    1. Check for issues using ruff check
    2. Auto-fix issues that can be fixed automatically
    3. Format the file using ruff format
    4. Run a final check for remaining issues
    """
    # Validate file path
    path = Path(file_path)
    if not path.exists():
        _logger.error("Error: File not found: {}", file_path)
        return 1

    if path.suffix != ".py":
        _logger.warning("{} is not a Python file.", file_path)

    return _run_ruff_pipeline_QWIM(target_path = path)


def lint_and_format_directory(
    *, directory_path: str | Path, recursive: bool = True) -> int:
    """Run Ruff linting and formatting on a directory.

    Parameters
    ----------
    directory_path : str | pathlib.Path
        Path to the directory containing Python files.
    recursive : bool, optional
        Whether to process subdirectories recursively. Default is True.

    Returns
    -------
    int
        Final return code (0 if all checks pass).
    """
    # Validate directory path
    path = Path(directory_path)
    if not path.exists():
        _logger.error("Error: Directory not found: {}", directory_path)
        return 1

    if not path.is_dir():
        _logger.error("{} is not a directory.", directory_path)
        return 1

    return _run_ruff_pipeline_QWIM(target_path = path)


def main(
    target_path: str | Path | None = None) -> None:
    """Entry point for linting and formatting utility.

    Parameters
    ----------
    target_path : str | pathlib.Path, optional
        Path to file or directory to lint. If None, uses command-line arguments
        or defaults to the current directory.

    Notes
    -----
    When run from command line, accepts the following arguments:
        - path: Path to file or directory (optional, defaults to current directory)
        - --file, -f: Treat path as a single file
        - --directory, -d: Treat path as a directory (default)

    Examples
    --------
    Command line usage:

    .. code-block:: bash

        # Lint entire src directory
        python lint_format.py src/

        # Lint a single file
        python lint_format.py -f src/utils/utils_portfolio.py

        # Lint current directory
        python lint_format.py
    """
    if target_path is not None:
        # Called programmatically
        path = Path(target_path)
        if path.is_file():
            lint_and_format_file(file_path = str(path))
        else:
            lint_and_format_directory(directory_path = str(path))
        return

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Run Ruff linting and formatting on Python files.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to file or directory (default: current directory)",
    )
    parser.add_argument(
        "--file",
        "-f",
        action="store_true",
        help="Treat path as a single file",
    )
    parser.add_argument(
        "--directory",
        "-d",
        action="store_true",
        help="Treat path as a directory (default behavior)",
    )

    args = parser.parse_args()

    path = Path(args.path)

    if args.file or path.is_file():
        lint_and_format_file(file_path = str(path))
    else:
        lint_and_format_directory(directory_path = str(path))


if __name__ == "__main__":  # pragma: no cover
    main()

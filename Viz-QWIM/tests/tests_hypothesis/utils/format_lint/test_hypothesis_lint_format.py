"""Hypothesis (property-based) tests for lint_format module.

Tests cover pure-function invariants for the public API:
- ``run_command``: always returns an integer (including for trivial commands)
- ``lint_and_format_file``: returns 1 for non-existent paths, int otherwise
- ``lint_and_format_directory``: returns 1 for non-existent paths, int otherwise

Key invariants tested:
- ``run_command`` always returns an ``int``
- Non-existent file/directory path → return code is always ``1``
- Valid command → return code is an ``int``
- ``recursive`` parameter accepted without error
"""

from __future__ import annotations

import tempfile
from pathlib import Path
import sys

import pytest

from hypothesis import given, settings
from hypothesis import strategies as st


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Run_Command
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Run_Command:
    """Property-based tests for run_command."""

    @pytest.mark.unit()
    @given(
        output_text=st.from_regex(r"[a-zA-Z0-9_]{1,20}", fullmatch=True)
    )
    @settings(max_examples=20)
    def Test_run_command_returns_int(self, output_text: str) -> None:
        """run_command always returns an integer."""
        from src.utils.format_lint.lint_format import run_command

        result = run_command(command = [sys.executable, "-c", f"print('{output_text}')"])

        assert isinstance(result, int)

    @pytest.mark.unit()
    @given(
        output_text=st.from_regex(r"[a-zA-Z0-9_]{1,20}", fullmatch=True)
    )
    @settings(max_examples=20)
    def Test_successful_echo_returns_zero(self, output_text: str) -> None:
        """A simple Python command returns 0."""
        from src.utils.format_lint.lint_format import run_command

        result = run_command(command = [sys.executable, "-c", f"print('{output_text}')"])

        assert result == 0

    @pytest.mark.unit()
    @given(
        output_text=st.from_regex(r"[a-zA-Z0-9_]{1,20}", fullmatch=True)
    )
    @settings(max_examples=5)
    def Test_return_code_is_non_negative(self, output_text: str) -> None:
        """Return code from run_command is always >= 0."""
        from src.utils.format_lint.lint_format import run_command

        result = run_command(command = [sys.executable, "-c", f"print('{output_text}')"])

        assert result >= 0


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Lint_And_Format_File
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Lint_And_Format_File:
    """Property-based tests for lint_and_format_file."""

    @pytest.mark.unit()
    @given(
        name=st.from_regex(r"[a-z][a-z0-9_]{0,10}", fullmatch=True)
    )
    @settings(max_examples=20)
    def Test_nonexistent_file_returns_one(self, tmp_path: Path, name: str) -> None:
        """lint_and_format_file returns 1 for a non-existent file path."""
        from src.utils.format_lint.lint_format import lint_and_format_file

        missing = str(tmp_path / f"{name}_does_not_exist.py")

        result = lint_and_format_file(file_path = missing)

        assert result == 1

    @pytest.mark.unit()
    @given(
        name=st.from_regex(r"[a-z][a-z0-9_]{0,10}", fullmatch=True)
    )
    @settings(max_examples=20)
    def Test_returns_integer_for_nonexistent(self, tmp_path: Path, name: str) -> None:
        """lint_and_format_file always returns an int."""
        from src.utils.format_lint.lint_format import lint_and_format_file

        missing = str(tmp_path / f"{name}_x.py")

        result = lint_and_format_file(file_path = missing)

        assert isinstance(result, int)


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Lint_And_Format_Directory
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Lint_And_Format_Directory:
    """Property-based tests for lint_and_format_directory."""

    @pytest.mark.unit()
    @given(
        name=st.from_regex(r"[a-z][a-z0-9_]{0,10}", fullmatch=True)
    )
    @settings(max_examples=20)
    def Test_nonexistent_dir_returns_one(self, tmp_path: Path, name: str) -> None:
        """lint_and_format_directory returns 1 for a non-existent directory."""
        from src.utils.format_lint.lint_format import lint_and_format_directory

        missing = str(tmp_path / f"{name}_does_not_exist_dir")

        result = lint_and_format_directory(directory_path = missing)

        assert result == 1

    @pytest.mark.unit()
    @given(recursive=st.booleans())
    @settings(max_examples=10)
    def Test_recursive_param_accepted(self, tmp_path: Path, recursive: bool) -> None:
        """lint_and_format_directory accepts recursive param without error."""
        from src.utils.format_lint.lint_format import lint_and_format_directory

        missing = str(tmp_path / "no_such_subdir")

        result = lint_and_format_directory(directory_path = missing, recursive=recursive)

        assert isinstance(result, int)

    @pytest.mark.unit()
    @given(
        name=st.from_regex(r"[a-z][a-z0-9_]{0,10}", fullmatch=True)
    )
    @settings(max_examples=20)
    def Test_file_path_as_directory_returns_one(self, tmp_path: Path, name: str) -> None:
        """lint_and_format_directory returns 1 when path is a file, not a dir."""
        from src.utils.format_lint.lint_format import lint_and_format_directory

        py_file = tmp_path / f"{name}.py"
        py_file.write_text("x = 1\n", encoding="utf-8")

        result = lint_and_format_directory(directory_path = str(py_file))

        assert result == 1

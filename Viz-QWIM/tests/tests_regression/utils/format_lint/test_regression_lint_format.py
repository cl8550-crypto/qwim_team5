"""Regression tests for lint_format command vectors.

These baselines lock in the explicit Ruff argv construction and four-step
pipeline order so later refactors do not silently drift back to shell-built
strings or regress on Windows paths with spaces.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import call, patch

import pytest

from src.utils.format_lint.lint_format import (
    _build_ruff_command_QWIM,
    lint_and_format_file,
)


class Class_Test_Regression_Lint_Format:
    """Regression baselines for lint_format command construction."""

    @pytest.mark.regression()
    def Test_Ruff_Command_Vector_Baseline(self, tmp_path: Path) -> None:
        """The Ruff command vector must keep the target path as the final token."""
        target_path = tmp_path / "folder with spaces" / "sample.py"

        command_vector = _build_ruff_command_QWIM(
            "check",
            target_path,
            "--fix",
        )

        assert command_vector == [
            "ruff",
            "check",
            "--fix",
            str(target_path),
        ]

    @pytest.mark.regression()
    def Test_File_Pipeline_Order_Baseline(self, tmp_path: Path) -> None:
        """The file pipeline must retain its four-command Ruff order."""
        target_directory = tmp_path / "folder with spaces"
        target_directory.mkdir()
        target_path = target_directory / "sample.py"
        target_path.write_text("x = 1\n", encoding="utf-8")

        with patch(
            "src.utils.format_lint.lint_format.run_command",
            return_value=0,
        ) as mock_run:
            lint_and_format_file(file_path = target_path)

        assert mock_run.call_args_list == [
            call(command=["ruff", "check", str(target_path)]),
            call(command=["ruff", "check", "--fix", str(target_path)]),
            call(command=["ruff", "format", str(target_path)]),
            call(command=["ruff", "check", str(target_path)]),
        ]
"""Regression tests for Typst utility helpers.

These baselines lock in the command-vector shape and user-facing validation
messages for the Typst compilation boundary so later refactors do not silently
change cross-platform subprocess behavior.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.utils.typst_utils import (
    build_typst_compile_command_QWIM,
    compile_typst_document_to_pdf_QWIM,
)


class Class_Test_Regression_Typst_Utils:
    """Regression baselines for Typst command construction and messages."""

    @pytest.mark.regression()
    def Test_Bare_Command_Vector_Baseline(self, tmp_path: Path) -> None:
        """The fallback command vector must remain stable when no path is resolved."""
        input_path = tmp_path / "report.typ"
        output_path = tmp_path / "report.pdf"

        command_vector = build_typst_compile_command_QWIM(
            typst_executable_path = None,
            typst_file_path = input_path,
            output_pdf_path = output_path,
        )

        assert command_vector == [
            "typst",
            "compile",
            str(input_path),
            str(output_path),
        ]

    @pytest.mark.regression()
    def Test_Resolved_Command_Vector_Baseline(self, tmp_path: Path) -> None:
        """A resolved executable path must remain the first command element."""
        executable_path = tmp_path / "typst.exe"
        input_path = tmp_path / "report.typ"
        output_path = tmp_path / "report.pdf"

        command_vector = build_typst_compile_command_QWIM(
            typst_executable_path = executable_path,
            typst_file_path = input_path,
            output_pdf_path = output_path,
        )

        assert command_vector == [
            str(executable_path),
            "compile",
            str(input_path),
            str(output_path),
        ]

    @pytest.mark.regression()
    def Test_Missing_Output_Message_Baseline(self, tmp_path: Path) -> None:
        """Successful backend return without an output PDF must keep its message."""
        input_path = tmp_path / "report.typ"
        output_path = tmp_path / "report.pdf"
        input_path.write_text("= Regression", encoding="utf-8")
        failing_module = SimpleNamespace(
            compile=MagicMock(side_effect=RuntimeError("force cli fallback")),
        )

        success_flag, status_message = compile_typst_document_to_pdf_QWIM(
            typst_file_path = input_path,
            output_pdf_path = output_path,
            _typst_module=failing_module,
            _subprocess_run=MagicMock(
                return_value=MagicMock(returncode=0, stdout="", stderr="")
            ),
        )

        assert success_flag is False
        assert status_message == "Compilation appeared to succeed but PDF not found"
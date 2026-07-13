"""Integration tests for Typst utility helpers.

These tests use the real filesystem while stubbing the external Typst runtime.
They verify that the utility boundary behaves correctly when asked to compile
temporary Typst sources into temporary PDF outputs.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.utils.typst_utils import (
    compile_typst_document_to_pdf_QWIM,
    resolve_typst_executable_path_QWIM,
)


class Class_Test_Integration_Typst_Utils:
    """Integration tests for Typst utility workflows."""

    @pytest.mark.integration()
    def Test_Python_Module_Path_Writes_Real_Output_File(self, tmp_path: Path) -> None:
        """Injected Typst module should create a real PDF on the filesystem."""
        input_path = tmp_path / "report.typ"
        output_path = tmp_path / "report.pdf"
        input_path.write_text("= Integration", encoding="utf-8")

        def _mock_compile(*_args: object, **_kwargs: object) -> None:
            output_path.write_bytes(b"%PDF-1.4 integration")

        success_flag, status_message = compile_typst_document_to_pdf_QWIM(
            typst_file_path = input_path,
            output_pdf_path = output_path,
            _typst_module=SimpleNamespace(compile=_mock_compile),
        )

        assert success_flag is True
        assert output_path.exists()
        assert output_path.stat().st_size > 0
        assert "compiled successfully" in status_message.lower()

    @pytest.mark.integration()
    def Test_Cli_Path_Uses_Resolved_Executable_When_Available(self, tmp_path: Path) -> None:
        """CLI fallback should receive the resolved executable path when found."""
        input_path = tmp_path / "report.typ"
        output_path = tmp_path / "report.pdf"
        executable_path = tmp_path / "typst"
        input_path.write_text("= Integration", encoding="utf-8")
        executable_path.write_text("", encoding="utf-8")
        failing_module = SimpleNamespace(
            compile=MagicMock(side_effect=RuntimeError("force cli fallback")),
        )

        observed_command_vector: list[str] = []

        def _mock_subprocess_run(command_vector: list[str], **_kwargs: object) -> MagicMock:
            observed_command_vector.extend(command_vector)
            output_path.write_bytes(b"%PDF-1.4 cli integration")
            return MagicMock(returncode=0, stdout="", stderr="")

        resolved_path = resolve_typst_executable_path_QWIM(
            _which_func=lambda _item_name: str(executable_path),
        )
        success_flag, status_message = compile_typst_document_to_pdf_QWIM(
            typst_file_path = input_path,
            output_pdf_path = output_path,
            _typst_module=failing_module,
            _which_func=lambda _item_name: str(executable_path),
            _subprocess_run=_mock_subprocess_run,
        )

        assert success_flag is True
        assert observed_command_vector[0] == str(resolved_path)
        assert observed_command_vector[1:] == [
            "compile",
            str(input_path),
            str(output_path),
        ]
        assert "compiled successfully" in status_message.lower()
"""Unit tests for Typst utility helpers.

These tests focus on the small cross-platform boundary in
``src.utils.typst_utils`` so command construction and fallback behavior remain
stable even when the real Typst runtime is unavailable.
"""

from __future__ import annotations

import builtins
import subprocess

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.utils.typst_utils import (
    DEFAULT_TYPST_TIMEOUT_SECONDS,
    build_typst_compile_command_QWIM,
    compile_typst_document_to_pdf_QWIM,
    resolve_typst_executable_path_QWIM,
)


class Class_Test_Resolve_Typst_Executable_Path_QWIM:
    """Unit tests for Typst executable resolution."""

    @pytest.mark.unit()
    def Test_Returns_None_When_Executable_Is_Not_Found(self) -> None:
        """Executable resolution should return ``None`` when lookup fails."""
        result = resolve_typst_executable_path_QWIM(
            _which_func=lambda _item_name: None,
        )
        assert result is None

    @pytest.mark.unit()
    def Test_Returns_Resolved_Path_When_Executable_Is_Found(self, tmp_path: Path) -> None:
        """Executable resolution should normalize discovered paths."""
        executable_path = tmp_path / "typst.exe"
        executable_path.write_text("", encoding="utf-8")

        result = resolve_typst_executable_path_QWIM(
            _which_func=lambda _item_name: str(executable_path),
        )

        assert result == executable_path.resolve()


class Class_Test_Build_Typst_Compile_Command_QWIM:
    """Unit tests for Typst command construction."""

    @pytest.mark.unit()
    def Test_Uses_Resolved_Executable_When_Present(self, tmp_path: Path) -> None:
        """Command should start with the resolved executable path when given."""
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

    @pytest.mark.unit()
    def Test_Falls_Back_To_Bare_Typst_Command_When_Path_Missing(self, tmp_path: Path) -> None:
        """Command should fall back to ``typst`` when no path is resolved."""
        input_path = tmp_path / "report.typ"
        output_path = tmp_path / "report.pdf"

        command_vector = build_typst_compile_command_QWIM(
            typst_executable_path = None,
            typst_file_path = input_path,
            output_pdf_path = output_path,
        )

        assert command_vector[0] == "typst"
        assert command_vector[1:] == ["compile", str(input_path), str(output_path)]


class Class_Test_Compile_Typst_Document_To_PDF_QWIM:
    """Unit tests for Typst compilation fallback behavior."""

    @pytest.mark.unit()
    def Test_Missing_Source_File_Returns_Failure(self, tmp_path: Path) -> None:
        """Missing Typst input should return failure with a helpful message."""
        success_flag, status_message = compile_typst_document_to_pdf_QWIM(
            typst_file_path = tmp_path / "missing.typ",
            output_pdf_path = tmp_path / "report.pdf",
        )

        assert success_flag is False
        assert "not found" in status_message.lower()

    @pytest.mark.unit()
    def Test_Python_Module_Success_Returns_Success(self, tmp_path: Path) -> None:
        """Python binding success should skip CLI fallback and return success."""
        input_path = tmp_path / "report.typ"
        output_path = tmp_path / "report.pdf"
        input_path.write_text("= Test", encoding="utf-8")

        def _mock_compile(*_args: object, **_kwargs: object) -> None:
            output_path.write_bytes(b"%PDF-1.4 test")

        success_flag, status_message = compile_typst_document_to_pdf_QWIM(
            typst_file_path = input_path,
            output_pdf_path = output_path,
            _typst_module=SimpleNamespace(compile=_mock_compile),
        )

        assert success_flag is True
        assert "compiled successfully" in status_message.lower()

    @pytest.mark.unit()
    def Test_Python_Module_Error_Then_Cli_Not_Found_Returns_Failure(self, tmp_path: Path) -> None:
        """Python binding failure should fall back and surface CLI-not-found details."""
        input_path = tmp_path / "report.typ"
        output_path = tmp_path / "report.pdf"
        input_path.write_text("= Test", encoding="utf-8")

        failing_module = SimpleNamespace(
            compile=MagicMock(side_effect=RuntimeError("binding failure")),
        )

        success_flag, status_message = compile_typst_document_to_pdf_QWIM(
            typst_file_path = input_path,
            output_pdf_path = output_path,
            _typst_module=failing_module,
            _subprocess_run=MagicMock(side_effect=FileNotFoundError),
        )

        assert success_flag is False
        assert "binding failure" in status_message
        assert "typst cli not found" in status_message.lower()

    @pytest.mark.unit()
    def Test_Cli_Success_Returns_Success(self, tmp_path: Path) -> None:
        """CLI fallback should return success when it creates a non-empty PDF."""
        input_path = tmp_path / "report.typ"
        output_path = tmp_path / "report.pdf"
        input_path.write_text("= Test", encoding="utf-8")
        failing_module = SimpleNamespace(
            compile=MagicMock(side_effect=RuntimeError("force cli fallback")),
        )

        def _mock_subprocess_run(*args: object, **kwargs: object) -> MagicMock:
            output_path.write_bytes(b"%PDF-1.4 cli")
            return MagicMock(returncode=0, stdout="", stderr="")

        success_flag, status_message = compile_typst_document_to_pdf_QWIM(
            typst_file_path = input_path,
            output_pdf_path = output_path,
            _typst_module=failing_module,
            _which_func=lambda _item_name: str(tmp_path / "typst"),
            _subprocess_run=_mock_subprocess_run,
        )

        assert success_flag is True
        assert "compiled successfully" in status_message.lower()

    @pytest.mark.unit()
    def Test_Cli_Timeout_Returns_Failure(self, tmp_path: Path) -> None:
        """CLI timeout should return a timeout failure message."""
        input_path = tmp_path / "report.typ"
        output_path = tmp_path / "report.pdf"
        input_path.write_text("= Test", encoding="utf-8")
        failing_module = SimpleNamespace(
            compile=MagicMock(side_effect=RuntimeError("force cli fallback")),
        )

        success_flag, status_message = compile_typst_document_to_pdf_QWIM(
            typst_file_path = input_path,
            output_pdf_path = output_path,
            _typst_module=failing_module,
            _subprocess_run=MagicMock(
                side_effect=subprocess.TimeoutExpired("typst", 120)
            ),
        )

        assert success_flag is False
        assert "timed out" in status_message.lower()

    @pytest.mark.unit()
    def Test_Boolean_Timeout_Uses_Default_Timeout_Path(self, tmp_path: Path) -> None:
        """Boolean timeout values should use the established default timeout."""
        input_path = tmp_path / "report.typ"
        output_path = tmp_path / "report.pdf"
        input_path.write_text("= Test", encoding="utf-8")
        failing_module = SimpleNamespace(
            compile=MagicMock(side_effect=RuntimeError("force cli fallback")),
        )
        timeout_values: list[object] = []

        def _mock_subprocess_run(*args: object, **kwargs: object) -> MagicMock:
            timeout_values.append(kwargs.get("timeout"))
            output_path.write_bytes(b"%PDF-1.4 cli")
            return MagicMock(returncode=0, stdout="", stderr="")

        success_flag, status_message = compile_typst_document_to_pdf_QWIM(
            typst_file_path = input_path,
            output_pdf_path = output_path,
            timeout_seconds=True,
            _typst_module=failing_module,
            _subprocess_run=_mock_subprocess_run,
        )

        assert success_flag is True
        assert "compiled successfully" in status_message.lower()
        assert timeout_values == [DEFAULT_TYPST_TIMEOUT_SECONDS]

    @pytest.mark.unit()
    def Test_Cli_Nonzero_Returncode_Returns_Failure(self, tmp_path: Path) -> None:
        """CLI non-zero exit should propagate stderr or stdout in the message."""
        input_path = tmp_path / "report.typ"
        output_path = tmp_path / "report.pdf"
        input_path.write_text("= Test", encoding="utf-8")
        failing_module = SimpleNamespace(
            compile=MagicMock(side_effect=RuntimeError("force cli fallback")),
        )

        success_flag, status_message = compile_typst_document_to_pdf_QWIM(
            typst_file_path = input_path,
            output_pdf_path = output_path,
            _typst_module=failing_module,
            _subprocess_run=MagicMock(
                return_value=MagicMock(returncode=1, stdout="", stderr="cli failure")
            ),
        )

        assert success_flag is False
        assert "cli failure" in status_message

    @pytest.mark.unit()
    def Test_Cli_Success_Without_Output_Returns_Failure(self, tmp_path: Path) -> None:
        """CLI success without a PDF should return a validation failure."""
        input_path = tmp_path / "report.typ"
        output_path = tmp_path / "report.pdf"
        input_path.write_text("= Test", encoding="utf-8")
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

    @pytest.mark.unit()
    def Test_Cli_Zero_Byte_Output_Returns_Failure(self, tmp_path: Path) -> None:
        """Zero-byte CLI output should fail validation."""
        input_path = tmp_path / "report.typ"
        output_path = tmp_path / "report.pdf"
        input_path.write_text("= Test", encoding="utf-8")
        failing_module = SimpleNamespace(
            compile=MagicMock(side_effect=RuntimeError("force cli fallback")),
        )

        def _mock_subprocess_run(*args: object, **kwargs: object) -> MagicMock:
            output_path.write_bytes(b"")
            return MagicMock(returncode=0, stdout="", stderr="")

        success_flag, status_message = compile_typst_document_to_pdf_QWIM(
            typst_file_path = input_path,
            output_pdf_path = output_path,
            _typst_module=failing_module,
            _subprocess_run=_mock_subprocess_run,
        )

        assert success_flag is False
        assert "empty" in status_message.lower()

    @pytest.mark.unit()
    def Test_Auto_Import_Failure_Falls_Back_To_Cli(self, tmp_path: Path, monkeypatch) -> None:
        """Missing Typst import should fall back to the CLI path."""
        input_path = tmp_path / "report.typ"
        output_path = tmp_path / "report.pdf"
        input_path.write_text("= Test", encoding="utf-8")

        original_import = builtins.__import__

        def _mock_import(name: str, *args: object, **kwargs: object):
            if name == "typst":
                raise ImportError("typst missing")
            return original_import(name, *args, **kwargs)

        def _mock_subprocess_run(*args: object, **kwargs: object) -> MagicMock:
            output_path.write_bytes(b"%PDF-1.4 cli fallback")
            return MagicMock(returncode=0, stdout="", stderr="")

        monkeypatch.setattr(builtins, "__import__", _mock_import)

        success_flag, status_message = compile_typst_document_to_pdf_QWIM(
            typst_file_path = input_path,
            output_pdf_path = output_path,
            _subprocess_run=_mock_subprocess_run,
        )

        assert success_flag is True
        assert "compiled successfully" in status_message.lower()

    @pytest.mark.unit()
    def Test_Cli_Not_Found_Without_Binding_Error_Returns_Failure(
        self,
        tmp_path: Path,
        monkeypatch,
    ) -> None:
        """CLI-not-found fallback should still return a helpful failure without binding errors."""
        input_path = tmp_path / "report.typ"
        output_path = tmp_path / "report.pdf"
        input_path.write_text("= Test", encoding="utf-8")

        original_import = builtins.__import__

        def _mock_import(name: str, *args: object, **kwargs: object):
            if name == "typst":
                raise ImportError("typst missing")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", _mock_import)

        success_flag, status_message = compile_typst_document_to_pdf_QWIM(
            typst_file_path = input_path,
            output_pdf_path = output_path,
            _subprocess_run=MagicMock(side_effect=FileNotFoundError),
        )

        assert success_flag is False
        assert status_message.startswith("Typst compilation failed: typst CLI not found")

    @pytest.mark.unit()
    def Test_Unexpected_Setup_Error_Returns_Failure(self, tmp_path: Path, monkeypatch) -> None:
        """Unexpected setup errors should return the wrapped failure message."""
        input_path = tmp_path / "report.typ"
        output_path = tmp_path / "report.pdf"
        input_path.write_text("= Test", encoding="utf-8")

        def _raise_mkdir_failure(self, *args: object, **kwargs: object) -> None:
            raise RuntimeError("mkdir failure")

        monkeypatch.setattr(Path, "mkdir", _raise_mkdir_failure)

        success_flag, status_message = compile_typst_document_to_pdf_QWIM(
            typst_file_path = input_path,
            output_pdf_path = output_path,
            _typst_module=SimpleNamespace(compile=MagicMock()),
        )

        assert success_flag is False
        assert "unexpected error during typst compilation" in status_message.lower()
        assert "mkdir failure" in status_message
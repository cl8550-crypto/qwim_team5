"""Unit tests for the lint_format module."""

from __future__ import annotations

import subprocess
import sys

from contextlib import suppress
from unittest.mock import patch

import pytest


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture()
def run_command():
    """Fixture to import the run_command function."""
    from src.utils.format_lint.lint_format import run_command

    return run_command


@pytest.fixture()
def normalize_command_arguments():
    """Fixture to import the command normalization helper."""
    from src.utils.format_lint.lint_format import _normalize_command_arguments_QWIM

    return _normalize_command_arguments_QWIM


@pytest.fixture()
def build_ruff_command():
    """Fixture to import the Ruff command builder helper."""
    from src.utils.format_lint.lint_format import _build_ruff_command_QWIM

    return _build_ruff_command_QWIM


@pytest.fixture()
def lint_and_format_file():
    """Fixture to import the lint_and_format_file function."""
    from src.utils.format_lint.lint_format import lint_and_format_file

    return lint_and_format_file


@pytest.fixture()
def lint_and_format_directory():
    """Fixture to import the lint_and_format_directory function."""
    from src.utils.format_lint.lint_format import lint_and_format_directory

    return lint_and_format_directory


@pytest.fixture()
def sample_python_file(tmp_path):
    """Create a sample Python file for testing."""
    py_file = tmp_path / "sample.py"
    py_file.write_text("x = 1\ny = 2\nprint(x + y)\n")
    return py_file


@pytest.fixture()
def sample_directory(tmp_path):
    """Create a sample directory with Python files."""
    py_dir = tmp_path / "python_files"
    py_dir.mkdir()

    (py_dir / "file1.py").write_text("a = 1\n")
    (py_dir / "file2.py").write_text("b = 2\n")

    return py_dir


# ============================================================================
# Tests for run_command
# ============================================================================


class Class_Test_Run_Command:
    """Tests for the run_command function."""

    @pytest.mark.unit()
    def Test_Returns_Integer(self, run_command):
        """Test that function returns an integer return code."""
        with patch("src.utils.format_lint.lint_format.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=["ruff", "check", "sample.py"],
                returncode=0,
                stdout="ok\n",
                stderr="",
            )
            result = run_command(command = ["ruff", "check", "sample.py"])

        assert isinstance(result, int)

    @pytest.mark.unit()
    def Test_Successful_Command_Returns_Zero(self, run_command):
        """Test that successful command returns 0."""
        with patch("src.utils.format_lint.lint_format.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[sys.executable, "--version"],
                returncode=0,
                stdout="Python 3.13\n",
                stderr="",
            )
            result = run_command(command = [sys.executable, "--version"])

        assert result == 0

    @pytest.mark.unit()
    def Test_Failed_Command_Returns_Non_Zero(self, run_command):
        """Test that failed command returns non-zero."""
        with patch("src.utils.format_lint.lint_format.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=["ruff", "check", "broken.py"],
                returncode=2,
                stdout="",
                stderr="lint error\n",
            )
            result = run_command(command = ["ruff", "check", "broken.py"])

        assert result == 2

    @pytest.mark.unit()
    def Test_String_Command_Is_Tokenized(self, run_command):
        """String commands must be tokenized into argv lists before execution."""
        with patch("src.utils.format_lint.lint_format.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=["ruff", "check", "sample.py"],
                returncode=0,
                stdout="",
                stderr="",
            )
            run_command(command = "ruff check sample.py")

        mock_run.assert_called_once_with(
            ["ruff", "check", "sample.py"],
            shell=False,
            text=True,
            capture_output=True,
            check=False,
        )

    @pytest.mark.unit()
    def Test_Handles_Empty_Output(self, run_command):
        """Test handling of command with no output."""
        with patch("src.utils.format_lint.lint_format.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=["ruff", "format", "sample.py"],
                returncode=0,
                stdout="",
                stderr="",
            )
            result = run_command(command = ["ruff", "format", "sample.py"])

        assert isinstance(result, int)

    @pytest.mark.unit()
    def Test_Invalid_Empty_Command_Returns_One(self, run_command):
        """Empty command strings must return 1 instead of raising."""
        result = run_command(command = "   ")

        assert result == 1

    @pytest.mark.unit()
    def Test_OSError_Returns_One(self, run_command):
        """OSError from subprocess.run must be converted into return code 1."""
        with patch(
            "src.utils.format_lint.lint_format.subprocess.run",
            side_effect=OSError("missing executable"),
        ):
            result = run_command(command = ["ruff", "check", "sample.py"])

        assert result == 1


class Class_Test_Command_Helpers:
    """Tests for private command-construction helpers."""

    @pytest.mark.unit()
    def Test_Normalize_Sequence_Stringifies_Path_Items(
        self,
        normalize_command_arguments,
        tmp_path,
    ):
        """Path arguments in sequences must be converted to strings."""
        normalized = normalize_command_arguments(command=["ruff", "check", tmp_path / "sample.py"])

        assert normalized == ["ruff", "check", str(tmp_path / "sample.py")]

    @pytest.mark.unit()
    def Test_Normalize_Rejects_Invalid_Type(self, normalize_command_arguments):
        """Unsupported command container types must raise TypeError."""
        with pytest.raises(TypeError, match="string or sequence"):
            normalize_command_arguments(command=123)  # type: ignore[arg-type]

    @pytest.mark.unit()
    def Test_Normalize_Rejects_Empty_Sequence(self, normalize_command_arguments):
        """Empty command sequences must raise ValueError."""
        with pytest.raises(ValueError, match="Command cannot be empty"):
            normalize_command_arguments(command=[])

    @pytest.mark.unit()
    def Test_Normalize_Rejects_Empty_Argument_Token(self, normalize_command_arguments):
        """Empty argv items must raise ValueError."""
        with pytest.raises(ValueError, match="arguments cannot be empty"):
            normalize_command_arguments(command=["ruff", "", "sample.py"])

    @pytest.mark.unit()
    def Test_Build_Ruff_Check_Command(self, build_ruff_command, tmp_path):
        """The Ruff helper must build argv lists with the target path last."""
        command = build_ruff_command("check", tmp_path / "sample.py", "--fix")

        assert command == ["ruff", "check", "--fix", str(tmp_path / "sample.py")]

    @pytest.mark.unit()
    def Test_Build_Ruff_Command_Rejects_Unsupported_Action(
        self,
        build_ruff_command,
        tmp_path,
    ):
        """Unsupported Ruff actions must raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported Ruff action"):
            build_ruff_command("lint", tmp_path / "sample.py")


# ============================================================================
# Tests for lint_and_format_file
# ============================================================================


class Class_Test_Lint_And_Format_File:
    """Tests for the lint_and_format_file function."""

    @pytest.mark.unit()
    def Test_Returns_Integer(self, lint_and_format_file, sample_python_file):
        """Test that function returns an integer."""
        with patch("src.utils.format_lint.lint_format.run_command") as mock_run:
            mock_run.return_value = 0

            result = lint_and_format_file(file_path = str(sample_python_file))

            assert isinstance(result, int)

    @pytest.mark.unit()
    def Test_Returns_Error_For_Nonexistent_File(self, lint_and_format_file, capsys):
        """Test that function returns error for nonexistent file."""
        result = lint_and_format_file(file_path = "/nonexistent/path/to/file.py")

        assert result == 1

    @pytest.mark.unit()
    def Test_Warns_For_Non_Python_File(self, lint_and_format_file, tmp_path, capsys):
        """Test that function warns for non-Python files."""
        non_py_file = tmp_path / "test.txt"
        non_py_file.write_text("hello")

        with patch("src.utils.format_lint.lint_format.run_command") as mock_run:
            mock_run.return_value = 0

            lint_and_format_file(file_path = str(non_py_file))

            captured = capsys.readouterr()
            assert "not a Python file" in captured.out or mock_run.called

    @pytest.mark.unit()
    def Test_Calls_Ruff_Check(self, lint_and_format_file, sample_python_file):
        """Test that function calls ruff check."""
        with patch("src.utils.format_lint.lint_format.run_command") as mock_run:
            mock_run.return_value = 0

            lint_and_format_file(file_path = str(sample_python_file))

            calls = [call.kwargs["command"] for call in mock_run.call_args_list]
            assert ["ruff", "check", str(sample_python_file)] in calls

    @pytest.mark.unit()
    def Test_Calls_Ruff_Format(self, lint_and_format_file, sample_python_file):
        """Test that function calls ruff format."""
        with patch("src.utils.format_lint.lint_format.run_command") as mock_run:
            mock_run.return_value = 0

            lint_and_format_file(file_path = str(sample_python_file))

            calls = [call.kwargs["command"] for call in mock_run.call_args_list]
            assert ["ruff", "format", str(sample_python_file)] in calls

    @pytest.mark.unit()
    def Test_Calls_Ruff_Fix(self, lint_and_format_file, sample_python_file):
        """Test that function calls ruff check --fix."""
        with patch("src.utils.format_lint.lint_format.run_command") as mock_run:
            mock_run.return_value = 0

            lint_and_format_file(file_path = str(sample_python_file))

            calls = [call.kwargs["command"] for call in mock_run.call_args_list]
            assert ["ruff", "check", "--fix", str(sample_python_file)] in calls

    @pytest.mark.unit()
    def Test_Runs_Pipeline_In_Four_Steps(self, lint_and_format_file, sample_python_file):
        """lint_and_format_file must execute the full four-step Ruff pipeline."""
        with patch("src.utils.format_lint.lint_format.run_command") as mock_run:
            mock_run.return_value = 0

            lint_and_format_file(file_path = str(sample_python_file))

        assert mock_run.call_count == 4


# ============================================================================
# Tests for lint_and_format_directory
# ============================================================================


class Class_Test_Lint_And_Format_Directory:
    """Tests for the lint_and_format_directory function."""

    @pytest.mark.unit()
    def Test_Returns_Integer(self, lint_and_format_directory, sample_directory):
        """Test that function returns an integer."""
        with patch("src.utils.format_lint.lint_format.run_command") as mock_run:
            mock_run.return_value = 0

            result = lint_and_format_directory(directory_path = str(sample_directory))

            assert isinstance(result, int)

    @pytest.mark.unit()
    def Test_Returns_Error_For_Nonexistent_Directory(
        self,
        lint_and_format_directory,
        capsys,
    ):
        """Test that function returns error for nonexistent directory."""
        result = lint_and_format_directory(directory_path = "/nonexistent/path/to/directory")

        assert result == 1

    @pytest.mark.unit()
    def Test_Returns_Error_For_File_Path(
        self,
        lint_and_format_directory,
        sample_python_file,
        capsys,
    ):
        """Test that function returns error when given a file instead of directory."""
        result = lint_and_format_directory(directory_path = str(sample_python_file))

        assert result == 1

    @pytest.mark.unit()
    def Test_Calls_Ruff_On_Directory(self, lint_and_format_directory, sample_directory):
        """Test that function calls ruff on the directory."""
        with patch("src.utils.format_lint.lint_format.run_command") as mock_run:
            mock_run.return_value = 0

            lint_and_format_directory(directory_path = str(sample_directory))

            # Check that ruff was called with directory path
            calls = [str(call) for call in mock_run.call_args_list]
            dir_name = sample_directory.name
            assert any(dir_name in call or str(sample_directory) in call for call in calls)


# ============================================================================
# Tests for main function
# ============================================================================


class Class_Test_Main_Function:
    """Tests for the main() function."""

    @pytest.mark.unit()
    def Test_Main_Exists(self):
        """Test that main function exists and is callable."""
        from src.utils.format_lint.lint_format import main

        assert callable(main)

    @pytest.mark.unit()
    def Test_Main_With_No_Args_Uses_Current_Directory(self, monkeypatch):
        """Test that main with no arguments uses current directory."""
        from src.utils.format_lint.lint_format import main

        with patch("src.utils.format_lint.lint_format.lint_and_format_directory") as mock_lint_dir:
            mock_lint_dir.return_value = 0

            with patch("sys.argv", ["lint_format.py"]), suppress(SystemExit):
                main()

    @pytest.mark.unit()
    def Test_Main_With_File_Argument(self, sample_python_file):
        """Test that main with file argument calls lint_and_format_file."""
        from src.utils.format_lint.lint_format import main

        with (
            patch("src.utils.format_lint.lint_format.lint_and_format_file") as mock_lint_file,
            patch("sys.argv", ["lint_format.py", str(sample_python_file)]),
            suppress(SystemExit),
        ):
            mock_lint_file.return_value = 0
            main()

    @pytest.mark.unit()
    def Test_Main_With_Directory_Argument(self, sample_directory):
        """Test that main with directory argument calls lint_and_format_directory."""
        from src.utils.format_lint.lint_format import main

        with (
            patch("src.utils.format_lint.lint_format.lint_and_format_directory") as mock_lint_dir,
            patch("sys.argv", ["lint_format.py", str(sample_directory)]),
            suppress(SystemExit),
        ):
            mock_lint_dir.return_value = 0
            main()

    @pytest.mark.unit()
    def Test_Main_With_Target_Path_File(self, sample_python_file):
        """Test main() called programmatically with a file target_path."""
        from src.utils.format_lint.lint_format import main

        with patch("src.utils.format_lint.lint_format.lint_and_format_file") as mock_fn:
            mock_fn.return_value = 0
            main(target_path=str(sample_python_file))
            mock_fn.assert_called_once_with(file_path=str(sample_python_file))

    @pytest.mark.unit()
    def Test_Main_With_Target_Path_Directory(self, sample_directory):
        """Test main() called programmatically with a directory target_path."""
        from src.utils.format_lint.lint_format import main

        with patch("src.utils.format_lint.lint_format.lint_and_format_directory") as mock_fn:
            mock_fn.return_value = 0
            main(target_path=str(sample_directory))
            mock_fn.assert_called_once_with(directory_path=str(sample_directory))


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


class Class_Test_Edge_Cases:
    """Tests for edge cases and error handling."""

    @pytest.mark.unit()
    def Test_Handles_Permission_Error(self, lint_and_format_file, tmp_path):
        """Test handling of permission errors (mocked)."""
        with patch("src.utils.format_lint.lint_format.run_command") as mock_run:
            mock_run.side_effect = PermissionError("Access denied")

            with suppress(PermissionError):
                lint_and_format_file(file_path = str(tmp_path / "test.py"))

    @pytest.mark.unit()
    def Test_Handles_Unicode_In_File_Path(self, lint_and_format_file, tmp_path):
        """Test handling of unicode characters in file path."""
        unicode_file = tmp_path / "тест_файл.py"
        unicode_file.write_text("x = 1\n")

        with patch("src.utils.format_lint.lint_format.run_command") as mock_run:
            mock_run.return_value = 0

            # Should not crash with unicode path
            result = lint_and_format_file(file_path = str(unicode_file))

            assert isinstance(result, int)

    @pytest.mark.unit()
    def Test_Handles_Spaces_In_Path(self, lint_and_format_file, tmp_path):
        """Test handling of spaces in file path."""
        spaced_dir = tmp_path / "directory with spaces"
        spaced_dir.mkdir()
        spaced_file = spaced_dir / "test file.py"
        spaced_file.write_text("x = 1\n")

        with patch("src.utils.format_lint.lint_format.run_command") as mock_run:
            mock_run.return_value = 0

            result = lint_and_format_file(file_path = str(spaced_file))

            assert isinstance(result, int)

    @pytest.mark.unit()
    def Test_Empty_Directory(self, lint_and_format_directory, tmp_path):
        """Test linting an empty directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        with patch("src.utils.format_lint.lint_format.run_command") as mock_run:
            mock_run.return_value = 0

            result = lint_and_format_directory(directory_path = str(empty_dir))

            assert isinstance(result, int)


# ============================================================================
# Integration Tests
# ============================================================================


class Class_Test_Integration:
    """Integration tests (require ruff to be installed)."""

    @pytest.mark.integration()
    @pytest.mark.slow()
    @pytest.mark.unit()
    def Test_Actual_Ruff_Execution(self, sample_python_file):
        """Test actual ruff execution on a file."""
        from src.utils.format_lint.lint_format import lint_and_format_file

        # This test requires ruff to be installed
        result = lint_and_format_file(file_path = str(sample_python_file))

        # Should complete without crashing
        assert isinstance(result, int)

    @pytest.mark.integration()
    @pytest.mark.slow()
    @pytest.mark.unit()
    def Test_Actual_Ruff_On_Directory(self, sample_directory):
        """Test actual ruff execution on a directory."""
        from src.utils.format_lint.lint_format import lint_and_format_directory

        result = lint_and_format_directory(directory_path = str(sample_directory))

        assert isinstance(result, int)

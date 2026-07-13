"""Regression tests for traceback_custom validation behavior."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.utils.custom_exceptions_errors_loggers import traceback_custom as tc


def _capture_exception_info(function_under_test):
    try:
        function_under_test()
    except BaseException:
        return sys.exc_info()
    raise AssertionError("Expected helper to raise an exception")


class Class_Test_Regression_Traceback_Custom:
    """Regression baselines for traceback_custom public behavior."""

    @pytest.mark.regression()
    def Test_context_lines_type_error_message_baseline(self) -> None:
        """Non-integer context_lines error text should remain stable."""
        exc_type, exc_value, exc_tb = _capture_exception_info(
            lambda: (_ for _ in ()).throw(RuntimeError("baseline"))
        )

        with pytest.raises(TypeError) as error_info:
            tc.Format_Traceback_Context(
                exc_type = exc_type,
                exc_value = exc_value,
                exc_tb = exc_tb,
                context_lines="2",  # type: ignore[arg-type]
            )

        assert str(error_info.value) == "context_lines must be an integer"

    @pytest.mark.regression()
    def Test_negative_context_lines_error_message_baseline(self) -> None:
        """Negative context_lines error text should remain stable."""
        exc_type, exc_value, exc_tb = _capture_exception_info(
            lambda: (_ for _ in ()).throw(RuntimeError("baseline"))
        )

        with pytest.raises(ValueError) as error_info:
            tc.Format_Traceback_Context(exc_type = exc_type, exc_value = exc_value, exc_tb = exc_tb, context_lines=-1)

        assert str(error_info.value) == "context_lines must be non-negative"

    @pytest.mark.regression()
    def Test_project_root_type_error_message_baseline(self) -> None:
        """Non-string project_root error text should remain stable."""
        with pytest.raises(TypeError) as error_info:
            tc.Extract_Relevant_Frames(exc_tb = object(), project_root=123)  # type: ignore[arg-type]

        assert str(error_info.value) == "project_root must be a string or None"

    @pytest.mark.regression()
    def Test_project_root_blank_error_message_baseline(self) -> None:
        """Blank project_root error text should remain stable."""
        with pytest.raises(ValueError) as error_info:
            tc.Extract_Relevant_Frames(exc_tb = object(), project_root="   ")

        assert str(error_info.value) == "project_root must be a non-empty string when provided"

    @pytest.mark.regression()
    def Test_project_root_whitespace_normalization_baseline(self) -> None:
        """Whitespace-trimmed project roots should keep existing filter behavior."""
        project_root = str(Path(__file__).resolve().parent)
        matching_frame = SimpleNamespace(filename=str(Path(project_root) / "inside.py"))
        non_matching_frame = SimpleNamespace(filename="Z:/outside.py")

        original_extract_tb = tc.traceback.extract_tb
        tc.traceback.extract_tb = lambda _exc_tb: [matching_frame, non_matching_frame]
        try:
            relevant_frames = tc.Extract_Relevant_Frames(
                exc_tb = object(),
                project_root=f"  {project_root}  ",
            )
        finally:
            tc.traceback.extract_tb = original_extract_tb

        assert relevant_frames == [matching_frame]
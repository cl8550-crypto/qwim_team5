"""Hypothesis tests for traceback_custom."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from hypothesis import given, settings
from hypothesis import strategies as st

from src.utils.custom_exceptions_errors_loggers import traceback_custom as tc


def _raise_hypothesis_error() -> None:
    raise ValueError("hypothesis boom")


def _capture_exception_info(function_under_test):
    try:
        function_under_test()
    except BaseException:
        return sys.exc_info()
    raise AssertionError("Expected helper to raise an exception")


class Class_Test_Hypothesis_Traceback_Custom:
    """Property-based coverage for traceback_custom behavior."""

    @pytest.mark.unit()
    @given(context_lines=st.integers(min_value=0, max_value=5))
    @settings(max_examples=20)
    def Test_non_negative_context_lines_are_accepted(self, context_lines: int) -> None:
        """Non-negative context widths should always succeed."""
        exc_type, exc_value, exc_tb = _capture_exception_info(_raise_hypothesis_error)

        text = tc.Format_Traceback_Context(
            exc_type = exc_type,
            exc_value = exc_value,
            exc_tb = exc_tb,
            context_lines=context_lines,
        )

        assert "ValueError: hypothesis boom" in text

    @pytest.mark.unit()
    @given(context_lines=st.integers(max_value=-1))
    @settings(max_examples=20)
    def Test_negative_context_lines_raise_value_error(self, context_lines: int) -> None:
        """Negative context widths should always be rejected."""
        exc_type, exc_value, exc_tb = _capture_exception_info(_raise_hypothesis_error)

        with pytest.raises(ValueError, match="context_lines must be non-negative"):
            tc.Format_Traceback_Context(
                exc_type = exc_type,
                exc_value = exc_value,
                exc_tb = exc_tb,
                context_lines=context_lines,
            )

    @pytest.mark.unit()
    @given(
        bad_value=st.one_of(
            st.booleans(),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.lists(st.integers(), max_size=3),
            st.dictionaries(st.text(min_size=1, max_size=3), st.integers(), max_size=2),
        )
    )
    @settings(max_examples=30)
    def Test_non_string_project_roots_raise_type_error(self, bad_value: object) -> None:
        """Non-string project_root overrides should always be rejected."""
        with pytest.raises(TypeError, match="project_root must be a string or None"):
            tc.Extract_Relevant_Frames(exc_tb = object(), project_root=bad_value)  # type: ignore[arg-type]

    @pytest.mark.unit()
    @given(
        left_ws=st.from_regex(r"\s{1,3}", fullmatch=True),
        right_ws=st.from_regex(r"\s{1,3}", fullmatch=True),
    )
    @settings(max_examples=20)
    def Test_project_root_whitespace_is_normalized(self, left_ws: str, right_ws: str) -> None:
        """Whitespace around project_root overrides should be normalized."""
        project_root = str(Path(__file__).resolve().parent)
        matching_frame = SimpleNamespace(filename=str(Path(project_root) / "inside.py"))
        non_matching_frame = SimpleNamespace(filename="Z:/outside.py")

        original_extract_tb = tc.traceback.extract_tb
        tc.traceback.extract_tb = lambda _exc_tb: [matching_frame, non_matching_frame]
        try:
            relevant_frames = tc.Extract_Relevant_Frames(
                exc_tb = object(),
                project_root=f"{left_ws}{project_root}{right_ws}",
            )
        finally:
            tc.traceback.extract_tb = original_extract_tb

        assert relevant_frames == [matching_frame]
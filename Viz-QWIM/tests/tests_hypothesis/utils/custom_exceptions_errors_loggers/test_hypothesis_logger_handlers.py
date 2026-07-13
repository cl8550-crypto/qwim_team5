"""Hypothesis tests for _logger_handlers log-dir normalization."""

from __future__ import annotations

import os

from pathlib import Path
from unittest.mock import patch

import pytest

from hypothesis import given, settings
from hypothesis import strategies as st

from src.utils.custom_exceptions_errors_loggers._logger_handlers import (
    _resolve_log_dir_runtime,
)


class Class_Test_Hypothesis_Logger_Handlers:
    """Property-based coverage for runtime log-dir normalization."""

    @pytest.mark.unit()
    @given(
        left_ws=st.from_regex(r"\s{0,3}", fullmatch=True),
        right_ws=st.from_regex(r"\s{0,3}", fullmatch=True),
        worker_id=st.sampled_from(["gw0", "gw3", "gw9"]),
    )
    @settings(max_examples=30)
    def Test_string_default_log_dir_is_normalized_and_isolated_on_windows(
        self,
        left_ws: str,
        right_ws: str,
        worker_id: str,
    ) -> None:
        """Whitespace-wrapped default string paths should isolate like Path defaults."""
        with patch(
            "src.utils.custom_exceptions_errors_loggers._logger_handlers.sys.platform",
            "win32",
        ):
            with patch.dict(os.environ, {"PYTEST_XDIST_WORKER": worker_id}, clear=False):
                result = _resolve_log_dir_runtime(log_dir = f"{left_ws}logs{right_ws}")

        assert result == Path("logs") / "pytest" / worker_id

    @pytest.mark.unit()
    @given(blank_log_dir=st.sampled_from(["", " ", "\t", "\n", "  \t  "]))
    @settings(max_examples=20)
    def Test_blank_string_log_dirs_raise_value_error(self, blank_log_dir: str) -> None:
        """Blank string log dirs should always be rejected."""
        with pytest.raises(ValueError, match="non-empty path"):
            _resolve_log_dir_runtime(log_dir = blank_log_dir)

    @pytest.mark.unit()
    @given(
        log_dir_name=st.from_regex(r"[A-Za-z0-9_-]{1,12}", fullmatch=True).filter(
            lambda value: value != "logs"
        )
    )
    @settings(max_examples=25)
    def Test_explicit_string_log_dirs_remain_unchanged_for_workers(
        self,
        log_dir_name: str,
    ) -> None:
        """Explicit string directories should not be rewritten to worker paths."""
        with patch(
            "src.utils.custom_exceptions_errors_loggers._logger_handlers.sys.platform",
            "win32",
        ):
            with patch.dict(os.environ, {"PYTEST_XDIST_WORKER": "gw4"}, clear=False):
                result = _resolve_log_dir_runtime(log_dir = log_dir_name)

        assert result == Path(log_dir_name)
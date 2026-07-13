"""Regression tests for _logger_handlers runtime log-dir behavior."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.utils.custom_exceptions_errors_loggers._logger_handlers import (
    _resolve_log_dir_runtime,
)


class Class_Test_Regression_Logger_Handlers:
    """Regression baselines for log-dir normalization and validation."""

    @pytest.mark.regression()
    def Test_blank_string_log_dir_error_message_baseline(self) -> None:
        """Blank log-dir ValueError text should remain stable."""
        with pytest.raises(ValueError) as error_info:
            _resolve_log_dir_runtime(log_dir = "   ")

        assert str(error_info.value) == "log_dir must be a non-empty path when provided"

    @pytest.mark.regression()
    def Test_non_pathlike_log_dir_error_message_baseline(self) -> None:
        """Non-pathlike log-dir TypeError text should remain stable."""
        with pytest.raises(TypeError) as error_info:
            _resolve_log_dir_runtime(log_dir = 123)  # type: ignore[arg-type]

        assert str(error_info.value) == "log_dir must be a pathlib.Path or string"

    @pytest.mark.regression()
    def Test_string_default_log_dir_runtime_path_baseline(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """String default log-dir worker isolation should keep its path shape."""
        monkeypatch.setattr(
            "src.utils.custom_exceptions_errors_loggers._logger_handlers.sys.platform",
            "win32",
        )
        monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw11")

        result = _resolve_log_dir_runtime(log_dir = "logs")

        assert result == Path("logs") / "pytest" / "gw11"
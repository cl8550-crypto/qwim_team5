"""Integration tests for _logger_handlers runtime log-dir behavior."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from loguru import logger

from src.utils.custom_exceptions_errors_loggers._logger_handlers import (
    _resolve_log_dir_runtime,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import (
    LOG_FILE_APPLICATION,
    get_logger,
    setup_logging,
)


@pytest.fixture(autouse=True)
def fixture_cleanup_logger_handlers() -> None:
    """Reset loguru handlers after each integration test."""
    yield
    logger.remove()


class Class_Test_Integration_Logger_Handlers:
    """Integration coverage for runtime log-dir normalization behavior."""

    @pytest.mark.integration()
    def Test_setup_logging_with_string_default_dir_uses_worker_specific_runtime_path(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """String default log dirs should write under the worker-specific path."""
        monkeypatch.setattr(
            "src.utils.custom_exceptions_errors_loggers._logger_handlers.sys.platform",
            "win32",
        )
        monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw10")
        monkeypatch.chdir(tmp_path)

        setup_logging(log_dir="logs", enable_console=False)

        test_logger = get_logger(name = __name__)
        test_logger.info("integration runtime log dir")

        runtime_log_dir = tmp_path / "logs" / "pytest" / "gw10"
        assert runtime_log_dir.exists()
        assert (runtime_log_dir / LOG_FILE_APPLICATION).exists()

    @pytest.mark.integration()
    def Test_resolve_log_dir_runtime_uses_pid_fallback_when_current_test_exists(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """When only PYTEST_CURRENT_TEST exists, the pid fallback should be used."""
        monkeypatch.setattr(
            "src.utils.custom_exceptions_errors_loggers._logger_handlers.sys.platform",
            "win32",
        )
        monkeypatch.delenv("PYTEST_XDIST_WORKER", raising=False)
        monkeypatch.setenv("PYTEST_CURRENT_TEST", "tests/test_logger.py::test_case")

        with patch(
            "src.utils.custom_exceptions_errors_loggers._logger_handlers.os.getpid",
            return_value=43210,
        ):
            result = _resolve_log_dir_runtime(log_dir = "logs")

        assert result == Path("logs") / "pytest" / "pid_43210"

    @pytest.mark.integration()
    def Test_setup_logging_rejects_blank_string_log_dir(self) -> None:
        """Blank string log dirs should be rejected before configuration proceeds."""
        with pytest.raises(ValueError, match="non-empty path"):
            setup_logging(log_dir="   ", enable_console=False)
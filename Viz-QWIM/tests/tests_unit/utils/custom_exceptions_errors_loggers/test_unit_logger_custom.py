"""Unit tests for logger_custom module.

This module contains comprehensive unit tests for the custom logging functionality
including configuration validation, audit logging, performance tracking, and
log formatting.

Test Categories
---------------
- Configuration validation (Pydantic models)
- Logger setup and initialization
- Audit logging methods
- Performance tracking
- JSON serialization and formatting
- Filter functions
- Decorator functionality
- Error handling and edge cases

Author: QWIM Dashboard Team
Version: 1.0.0
Last Updated: 2026-02-01
"""

from __future__ import annotations

import json
import time

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from loguru import logger
from pydantic import ValidationError

# Import module under test
from src.utils.custom_exceptions_errors_loggers.logger_custom import (
    LOG_FILE_APPLICATION,
    LOG_FILE_AUDIT,
    LOG_FILE_DEBUG,
    LOG_FILE_ERROR,
    LOG_FILE_PERFORMANCE,
    LOG_LEVEL_DEBUG,
    LOG_LEVEL_INFO,
    LOG_LEVEL_WARNING,
    Audit_Logger,
    Config_Logging,
    Performance_Timer,
    _subtab_console_rules,
    _resolve_log_dir_runtime,
    filter_audit_events,
    filter_console_dynamic,
    filter_error_level,
    filter_performance_events,
    format_record_as_JSON,
    format_sink_human_readable,
    format_sink_JSON,
    get_logger,
    log_function_call,
    log_performance,
    sanitize_for_logging,
    serialize_for_JSON,
    set_console_level_for_subtab,
    setup_logging,
)


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture()
def temp_log_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for log files.

    Parameters
    ----------
    tmp_path : Path
        Pytest temporary directory fixture.

    Returns
    -------
    Path
        Path to temporary log directory.
    """
    log_dir = tmp_path / "logs"
    log_dir.mkdir(exist_ok=True)
    return log_dir


@pytest.fixture(autouse=True)
def cleanup_logger() -> None:
    """Clean up logger handlers after each test.

    This fixture automatically runs after each test to remove all
    logger handlers and reset the logger state.

    Returns
    -------
    None
    """
    yield
    # Remove all handlers
    logger.remove()


@pytest.fixture()
def sample_log_record() -> dict[str, Any]:
    """Create a sample log record for testing.

    Returns
    -------
    dict[str, Any]
        Sample log record with typical structure.
    """
    return {
        "time": datetime.now(UTC),
        "level": type("Level", (), {"name": "INFO", "no": 20})(),
        "name": "test_module",
        "module": "test_module",
        "function": "test_function",
        "line": 42,
        "message": "Test message",
        "exception": None,
        "extra": {},
        "thread": type("Thread", (), {"id": 12345, "name": "MainThread"})(),
        "process": type("Process", (), {"id": 99999, "name": "MainProcess"})(),
    }


@pytest.fixture()
def sample_audit_logger(temp_log_dir: Path) -> Audit_Logger:
    """Create a sample audit logger for testing.

    Parameters
    ----------
    temp_log_dir : Path
        Temporary log directory.

    Returns
    -------
    Audit_Logger
        Configured audit logger instance.
    """
    setup_logging(log_dir=temp_log_dir, enable_console=False)
    return Audit_Logger(logger_name="test_audit")


# ==============================================================================
# Test Configuration Validation
# ==============================================================================


@pytest.mark.unit()
class Class_Test_Config_Logging_Validation:
    """Test suite for Config_Logging Pydantic model validation."""

    @pytest.mark.unit()
    def Test_create_config_with_valid_defaults(self) -> None:
        """Test creating configuration with valid default values."""
        config = Config_Logging()

        assert config.log_level == "INFO"
        assert config.environment == "development"
        assert config.log_dir == Path("logs")
        assert config.enable_console is True
        assert config.enable_JSON is True

    @pytest.mark.parametrize(
        "log_level",
        ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )
    @pytest.mark.unit()
    def Test_create_config_with_valid_log_levels(self, log_level: str) -> None:
        """Test creating configuration with all valid log levels.

        Parameters
        ----------
        log_level : str
            Log level to test.
        """
        config = Config_Logging(log_level=log_level)
        assert config.log_level == log_level

    @pytest.mark.unit()
    def Test_create_config_with_invalid_log_level(self) -> None:
        """Test that invalid log levels raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Config_Logging(log_level="INVALID")

        error = exc_info.value
        assert "log_level" in str(error)

    @pytest.mark.parametrize(
        "environment",
        ["development", "staging", "production"],
    )
    @pytest.mark.unit()
    def Test_create_config_with_valid_environments(self, environment: str) -> None:
        """Test creating configuration with all valid environments.

        Parameters
        ----------
        environment : str
            Environment to test.
        """
        config = Config_Logging(environment=environment)
        assert config.environment == environment

    @pytest.mark.unit()
    def Test_create_config_with_invalid_environment(self) -> None:
        """Test that invalid environments raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Config_Logging(environment="invalid_env")

        error = exc_info.value
        assert "environment" in str(error)

    @pytest.mark.unit()
    def Test_create_config_with_custom_log_dir(self, tmp_path: Path) -> None:
        """Test creating configuration with custom log directory.

        Parameters
        ----------
        tmp_path : Path
            Temporary directory path.
        """
        custom_dir = tmp_path / "custom_logs"
        config = Config_Logging(log_dir=custom_dir)

        assert config.log_dir == custom_dir

    @pytest.mark.unit()
    def Test_create_config_with_all_custom_values(self, tmp_path: Path) -> None:
        """Test creating configuration with all custom values.

        Parameters
        ----------
        tmp_path : Path
            Temporary directory path.
        """
        config = Config_Logging(
            log_level="DEBUG",
            environment="production",
            log_dir=tmp_path / "logs",
            enable_console=False,
            enable_JSON=True,
            rotation_size="50 MB",
        )

        assert config.log_level == "DEBUG"
        assert config.environment == "production"
        assert config.log_dir == tmp_path / "logs"
        assert config.enable_console is False
        assert config.enable_JSON is True
        assert config.rotation_size == "50 MB"

    @pytest.mark.unit()
    def Test_create_config_rejects_extra_fields(self) -> None:
        """Test that unknown configuration fields raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Config_Logging(unknown_field=True)

        assert "unknown_field" in str(exc_info.value)


# ==============================================================================
# Test Serialization Functions
# ==============================================================================


@pytest.mark.unit()
class Class_Test_Serialization_Functions:
    """Test suite for JSON serialization utility functions."""

    @pytest.mark.unit()
    def Test_serialize_datetime(self) -> None:
        """Test serializing datetime objects."""
        dt = datetime(2024, 1, 15, 10, 30, 45)
        result = serialize_for_JSON(obj = dt)

        assert isinstance(result, str)
        assert "2024-01-15" in result

    @pytest.mark.unit()
    def Test_serialize_path(self, tmp_path: Path) -> None:
        """Test serializing Path objects.

        Parameters
        ----------
        tmp_path : Path
            Temporary path.
        """
        result = serialize_for_JSON(obj = tmp_path)

        assert isinstance(result, str)
        assert "tmp" in result.lower() or "temp" in result.lower()

    @pytest.mark.unit()
    def Test_serialize_bytes(self) -> None:
        """Test serializing bytes objects."""
        data = b"test data"
        result = serialize_for_JSON(obj = data)

        assert isinstance(result, str)
        assert result == "test data"

    @pytest.mark.unit()
    def Test_serialize_object_with_dict(self) -> None:
        """Test serializing objects with __dict__ attribute."""

        class Test_Obj:
            """Tests for Obj."""
            def __init__(self) -> None:
                """Init."""
                self.name = "test"
                self.value = 42

        obj = Test_Obj()
        result = serialize_for_JSON(obj = obj)

        assert isinstance(result, dict)
        assert result["name"] == "test"
        assert result["value"] == 42

    @pytest.mark.unit()
    def Test_serialize_primitive_types(self) -> None:
        """Test serializing primitive types (fallback to str)."""
        result_int = serialize_for_JSON(obj = 42)
        result_float = serialize_for_JSON(obj = 3.14)
        result_str = serialize_for_JSON(obj = "hello")

        assert result_int == "42"
        assert result_float == "3.14"
        assert result_str == "hello"

    @pytest.mark.unit()
    def Test_sanitize_for_logging_handles_bytes_and_depth_limit(self) -> None:
        """Test log sanitization for bytes and exhausted depth budget."""

        class Value_With_String:
            """Simple value with deterministic string conversion."""

            def __str__(self) -> str:
                """Return a deterministic string representation."""
                return "depth-limited"

        assert sanitize_for_logging(value = b"binary-data") == "binary-data"
        assert sanitize_for_logging(value = Value_With_String(), max_depth=-1) == "depth-limited"

    @pytest.mark.unit()
    @pytest.mark.parametrize("value_max_depth", [True, False], ids=["true", "false"])
    def Test_sanitize_for_logging_boolean_depth_uses_default_path(
        self,
        value_max_depth: bool,
    ) -> None:
        """Boolean max_depth values should use the established default recursion."""
        value_nested = {"outer": {"inner": {"api_key": "secret"}}}

        result_bool_depth = sanitize_for_logging(
            value = value_nested,
            max_depth=value_max_depth,
        )
        result_default_depth = sanitize_for_logging(value = value_nested)

        assert result_bool_depth == result_default_depth
        assert result_bool_depth["outer"]["inner"]["api_key"] == "***MASKED***"

    @pytest.mark.unit()
    def Test_sanitize_for_logging_handles_cycles_and_iterables(self) -> None:
        """Test log sanitization for cycles, tuples, and set-like inputs."""
        value_cycle: list[Any] = []
        value_cycle.append(value_cycle)

        result = sanitize_for_logging(
            value = {
                "items": value_cycle,
                "tuple_data": (1, {"api_key": "secret"}),
                "set_data": {"alpha", "beta"},
                "frozen_data": frozenset({"gamma"}),
            },
        )

        assert result["items"] == ["<cycle>"]
        assert result["tuple_data"] == (1, {"api_key": "***MASKED***"})
        assert sorted(result["set_data"]) == ["alpha", "beta"]
        assert result["frozen_data"] == ["gamma"]

    @pytest.mark.unit()
    def Test_sanitize_for_logging_handles_objects_with_dict(self) -> None:
        """Test log sanitization for objects exposing ``__dict__``."""

        class Sample_Object:
            """Simple object used to exercise ``__dict__`` sanitization."""

            def __init__(self) -> None:
                """Create an object with masked and unmasked attributes."""
                self.password = "hidden"
                self.visible = "shown"

        result = sanitize_for_logging(value = Sample_Object())

        assert result == {"password": "***MASKED***", "visible": "shown"}

    @pytest.mark.unit()
    def Test_sanitize_for_logging_falls_back_to_string(self) -> None:
        """Test log sanitization falls back to ``str`` for slot-only objects."""

        class Slot_Only_Object:
            """Simple object without ``__dict__`` to force string fallback."""

            __slots__ = ()

            def __str__(self) -> str:
                """Return a deterministic string representation."""
                return "slot-only"

        assert sanitize_for_logging(value = Slot_Only_Object()) == "slot-only"


@pytest.mark.unit()
class Class_Test_Format_Functions:
    """Test suite for log formatting functions."""

    @pytest.mark.unit()
    def Test_format_record_as_json_basic(self, sample_log_record: dict) -> None:
        """Test basic JSON formatting of log records.

        Parameters
        ----------
        sample_log_record : dict
            Sample log record fixture.
        """
        result = format_record_as_JSON(record = sample_log_record)
        parsed = json.loads(result)

        assert "timestamp" in parsed
        assert parsed["level"] == "INFO"
        assert parsed["module"] == "test_module"
        assert parsed["function"] == "test_function"
        assert parsed["line"] == 42
        assert parsed["message"] == "Test message"

    @pytest.mark.unit()
    def Test_format_record_as_json_with_exception(
        self,
        sample_log_record: dict,
    ) -> None:
        """Test JSON formatting with exception information.

        Parameters
        ----------
        sample_log_record : dict
            Sample log record fixture.
        """
        # Create exception info
        exc_type = ValueError
        exc_value = ValueError("Test error")

        sample_log_record["exception"] = type(
            "Exception",
            (),
            {
                "type": exc_type,
                "value": exc_value,
                "traceback": "Traceback info...",
            },
        )()

        result = format_record_as_JSON(record = sample_log_record)
        parsed = json.loads(result)

        assert "exception" in parsed
        assert parsed["exception"]["type"] == "ValueError"
        assert "Test error" in parsed["exception"]["value"]

    @pytest.mark.unit()
    def Test_format_record_as_json_with_extra_fields(
        self,
        sample_log_record: dict,
    ) -> None:
        """Test JSON formatting with extra fields.

        Parameters
        ----------
        sample_log_record : dict
            Sample log record fixture.
        """
        sample_log_record["extra"] = {
            "user_id": "analyst_001",
            "session_id": "sess_12345",
            "event_type": "CALCULATION",
        }

        result = format_record_as_JSON(record = sample_log_record)
        parsed = json.loads(result)

        assert parsed["user_id"] == "analyst_001"
        assert parsed["session_id"] == "sess_12345"
        assert parsed["event_type"] == "CALCULATION"

    @pytest.mark.unit()
    def Test_format_record_as_json_masks_nested_sensitive_extra_fields(
        self,
        sample_log_record: dict,
    ) -> None:
        """Test JSON formatting masks nested sensitive extra fields.

        Parameters
        ----------
        sample_log_record : dict
            Sample log record fixture.
        """
        sample_log_record["extra"] = {
            "data": {
                "api_key": "secret_value",
                "details": {
                    "password": "hidden_value",
                    "public": "visible",
                },
            },
        }

        result = format_record_as_JSON(record = sample_log_record)
        parsed = json.loads(result)

        assert parsed["data"]["api_key"] == "***MASKED***"
        assert parsed["data"]["details"]["password"] == "***MASKED***"
        assert parsed["data"]["details"]["public"] == "visible"
        assert "secret_value" not in result
        assert "hidden_value" not in result

    @pytest.mark.unit()
    def Test_format_record_debug_level_includes_thread_info(
        self,
        sample_log_record: dict,
    ) -> None:
        """Test that DEBUG level records include thread/process info.

        Parameters
        ----------
        sample_log_record : dict
            Sample log record fixture.
        """
        # Set to DEBUG level
        sample_log_record["level"] = type("Level", (), {"name": "DEBUG", "no": 10})()

        result = format_record_as_JSON(record = sample_log_record)
        parsed = json.loads(result)

        assert "thread_id" in parsed
        assert "thread_name" in parsed
        assert "process_id" in parsed
        assert "process_name" in parsed

    @pytest.mark.unit()
    def Test_format_sink_json(self, sample_log_record: dict) -> None:
        """Test sink JSON formatting adds newline.

        Parameters
        ----------
        sample_log_record : dict
            Sample log record fixture.
        """
        result = format_sink_JSON(record = sample_log_record)

        assert result.endswith("\n")
        # Remove newline and verify it's valid JSON
        json.loads(result.strip())

    @pytest.mark.unit()
    def Test_format_sink_human_readable(self, sample_log_record: dict) -> None:
        """Test human-readable formatting.

        Parameters
        ----------
        sample_log_record : dict
            Sample log record fixture.
        """
        result = format_sink_human_readable(record = sample_log_record)

        assert "INFO" in result
        assert "test_module" in result
        assert "test_function" in result
        assert "42" in result
        assert "Test message" in result
        assert result.endswith("\n")


# ==============================================================================
# Test Filter Functions
# ==============================================================================


@pytest.mark.unit()
class Class_Test_Filter_Functions:
    """Test suite for log filter functions."""

    @pytest.mark.unit()
    def Test_filter_audit_events_with_event_type(
        self,
        sample_log_record: dict,
    ) -> None:
        """Test audit event filter accepts records with event_type.

        Parameters
        ----------
        sample_log_record : dict
            Sample log record fixture.
        """
        sample_log_record["extra"]["event_type"] = "CALCULATION"

        assert filter_audit_events(record = sample_log_record) is True

    @pytest.mark.unit()
    def Test_filter_audit_events_without_event_type(
        self,
        sample_log_record: dict,
    ) -> None:
        """Test audit event filter rejects records without event_type.

        Parameters
        ----------
        sample_log_record : dict
            Sample log record fixture.
        """
        assert filter_audit_events(record = sample_log_record) is False

    @pytest.mark.unit()
    def Test_filter_performance_events_with_execution_time(
        self,
        sample_log_record: dict,
    ) -> None:
        """Test performance filter accepts records with execution_time_ms.

        Parameters
        ----------
        sample_log_record : dict
            Sample log record fixture.
        """
        sample_log_record["extra"]["execution_time_ms"] = 123.45

        assert filter_performance_events(record = sample_log_record) is True

    @pytest.mark.unit()
    def Test_filter_performance_events_without_execution_time(
        self,
        sample_log_record: dict,
    ) -> None:
        """Test performance filter rejects records without execution_time_ms.

        Parameters
        ----------
        sample_log_record : dict
            Sample log record fixture.
        """
        assert filter_performance_events(record = sample_log_record) is False

    @pytest.mark.parametrize(
        ("level_no", "expected"),
        [
            (10, False),  # DEBUG
            (20, False),  # INFO
            (30, False),  # WARNING
            (40, True),  # ERROR
            (50, True),  # CRITICAL
        ],
    )
    @pytest.mark.unit()
    def Test_filter_error_level(
        self,
        sample_log_record: dict,
        level_no: int,
        expected: bool,
    ) -> None:
        """Test error level filter for different log levels.

        Parameters
        ----------
        sample_log_record : dict
            Sample log record fixture.
        level_no : int
            Log level number to test.
        expected : bool
            Expected filter result.
        """
        sample_log_record["level"] = type("Level", (), {"no": level_no})()

        assert filter_error_level(record = sample_log_record) is expected


# ==============================================================================
# Test Logger Setup and Get Logger
# ==============================================================================


@pytest.mark.unit()
class Class_Test_Logger_Setup:
    """Test suite for logger setup and configuration."""

    @pytest.mark.unit()
    def Test_setup_logging_creates_log_directory(self, temp_log_dir: Path) -> None:
        """Test that setup_logging creates the log directory.

        Parameters
        ----------
        temp_log_dir : Path
            Temporary log directory fixture.
        """
        log_dir = temp_log_dir / "test_logs"
        setup_logging(log_dir=log_dir, enable_console=False)

        assert log_dir.exists()
        assert log_dir.is_dir()

    @pytest.mark.unit()
    def Test_setup_logging_creates_archive_directory(
        self,
        temp_log_dir: Path,
    ) -> None:
        """Test that setup_logging creates archive subdirectory.

        Parameters
        ----------
        temp_log_dir : Path
            Temporary log directory fixture.
        """
        setup_logging(log_dir=temp_log_dir, enable_console=False)
        archive_dir = temp_log_dir / "archive"

        assert archive_dir.exists()
        assert archive_dir.is_dir()

    @pytest.mark.parametrize(
        "log_level",
        ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )
    @pytest.mark.unit()
    def Test_setup_logging_with_different_levels(
        self,
        temp_log_dir: Path,
        log_level: str,
    ) -> None:
        """Test setup_logging with different log levels.

        Parameters
        ----------
        temp_log_dir : Path
            Temporary log directory fixture.
        log_level : str
            Log level to test.
        """
        setup_logging(
            log_level=log_level,
            log_dir=temp_log_dir,
            enable_console=False,
        )

        # Log a test message
        test_logger = get_logger(name = __name__)
        test_logger.info("Test message")

        # Verify application log file was created
        app_log = temp_log_dir / LOG_FILE_APPLICATION
        assert app_log.exists()

    @pytest.mark.unit()
    def Test_setup_logging_development_environment(
        self,
        temp_log_dir: Path,
    ) -> None:
        """Test setup_logging in development environment.

        Parameters
        ----------
        temp_log_dir : Path
            Temporary log directory fixture.
        """
        setup_logging(
            environment="development",
            log_dir=temp_log_dir,
            enable_console=False,
        )

        test_logger = get_logger(name = __name__)
        test_logger.debug("Debug message")

        # Development should create debug log
        debug_log = temp_log_dir / LOG_FILE_DEBUG
        assert debug_log.exists()

    @pytest.mark.unit()
    def Test_setup_logging_production_environment(
        self,
        temp_log_dir: Path,
    ) -> None:
        """Test setup_logging in production environment.

        Parameters
        ----------
        temp_log_dir : Path
            Temporary log directory fixture.
        """
        setup_logging(
            environment="production",
            log_dir=temp_log_dir,
            enable_console=False,
        )

        test_logger = get_logger(name = __name__)
        test_logger.info("Info message")

        # Production should not create debug log
        debug_log = temp_log_dir / LOG_FILE_DEBUG
        assert not debug_log.exists()

    @pytest.mark.unit()
    def Test_resolve_log_dir_runtime_isolates_default_dir_for_pytest_worker(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Default logs should be isolated per pytest worker on Windows."""
        monkeypatch.setattr(
            "src.utils.custom_exceptions_errors_loggers._logger_handlers.sys.platform",
            "win32",
        )
        monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw5")

        runtime_log_dir = _resolve_log_dir_runtime(log_dir = Path("logs"))

        assert runtime_log_dir == Path("logs") / "pytest" / "gw5"

    @pytest.mark.unit()
    def Test_resolve_log_dir_runtime_normalizes_string_default_dir_for_pytest_worker(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """String default log dirs should isolate the same as Path defaults."""
        monkeypatch.setattr(
            "src.utils.custom_exceptions_errors_loggers._logger_handlers.sys.platform",
            "win32",
        )
        monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw6")

        runtime_log_dir = _resolve_log_dir_runtime(log_dir = "logs")

        assert runtime_log_dir == Path("logs") / "pytest" / "gw6"

    @pytest.mark.unit()
    def Test_resolve_log_dir_runtime_rejects_blank_string_log_dir(self) -> None:
        """Blank string log dirs should be rejected explicitly."""
        with pytest.raises(ValueError, match="log_dir must be a non-empty path when provided"):
            _resolve_log_dir_runtime(log_dir = "   ")

    @pytest.mark.unit()
    def Test_resolve_log_dir_runtime_rejects_non_pathlike_log_dir(self) -> None:
        """Non-pathlike log dirs should be rejected explicitly."""
        with pytest.raises(TypeError, match="log_dir must be a pathlib.Path or string"):
            _resolve_log_dir_runtime(log_dir = 123)  # type: ignore[arg-type]

    @pytest.mark.unit()
    def Test_resolve_log_dir_runtime_keeps_explicit_dir_for_pytest_worker(
        self,
        monkeypatch: pytest.MonkeyPatch,
        temp_log_dir: Path,
    ) -> None:
        """Explicit log directories should remain unchanged under pytest workers."""
        monkeypatch.setattr(
            "src.utils.custom_exceptions_errors_loggers._logger_handlers.sys.platform",
            "win32",
        )
        monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw2")

        runtime_log_dir = _resolve_log_dir_runtime(log_dir = temp_log_dir)

        assert runtime_log_dir == temp_log_dir

    @pytest.mark.unit()
    def Test_setup_logging_writes_default_logs_under_pytest_worker_directory(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Implicit default logging should write to the worker-specific test directory."""
        monkeypatch.setattr(
            "src.utils.custom_exceptions_errors_loggers._logger_handlers.sys.platform",
            "win32",
        )
        monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw7")
        monkeypatch.chdir(tmp_path)

        setup_logging(enable_console=False)

        test_logger = get_logger(name = __name__)
        test_logger.info("Worker-specific default log message")
        time.sleep(0.1)

        app_log = tmp_path / "logs" / "pytest" / "gw7" / LOG_FILE_APPLICATION
        assert app_log.exists()

    @pytest.mark.unit()
    def Test_setup_logging_writes_string_default_logs_under_pytest_worker_directory(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """String default log dirs should isolate under the worker-specific test directory."""
        monkeypatch.setattr(
            "src.utils.custom_exceptions_errors_loggers._logger_handlers.sys.platform",
            "win32",
        )
        monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw8")
        monkeypatch.chdir(tmp_path)

        setup_logging(log_dir="logs", enable_console=False)

        test_logger = get_logger(name = __name__)
        test_logger.info("Worker-specific string default log message")
        time.sleep(0.1)

        app_log = tmp_path / "logs" / "pytest" / "gw8" / LOG_FILE_APPLICATION
        assert app_log.exists()

    @pytest.mark.unit()
    def Test_get_logger_auto_configures(self) -> None:
        """Test that get_logger auto-configures if not set up."""
        # This should trigger auto-configuration
        test_logger = get_logger(name = "test_module")

        assert test_logger is not None

    @pytest.mark.unit()
    def Test_get_logger_returns_bound_logger(self, temp_log_dir: Path) -> None:
        """Test that get_logger returns a bound logger with name.

        Parameters
        ----------
        temp_log_dir : Path
            Temporary log directory fixture.
        """
        setup_logging(log_dir=temp_log_dir, enable_console=False)
        test_logger = get_logger(name = "test_module")

        # Log a message
        test_logger.info("Test message")

        # Verify log file was created
        app_log = temp_log_dir / LOG_FILE_APPLICATION
        assert app_log.exists()


# ==============================================================================
# Test Audit Logger
# ==============================================================================


@pytest.mark.unit()
class Class_Test_Audit_Logger:
    """Test suite for Audit_Logger class."""

    @pytest.mark.unit()
    def Test_create_audit_logger(self, sample_audit_logger: Audit_Logger) -> None:
        """Test creating an audit logger instance.

        Parameters
        ----------
        sample_audit_logger : Audit_Logger
            Audit logger fixture.
        """
        assert sample_audit_logger.logger_name == "test_audit"
        assert sample_audit_logger._logger is not None

    @pytest.mark.unit()
    def Test_log_calculation(
        self,
        sample_audit_logger: Audit_Logger,
        temp_log_dir: Path,
    ) -> None:
        """Test logging a calculation event.

        Parameters
        ----------
        sample_audit_logger : Audit_Logger
            Audit logger fixture.
        temp_log_dir : Path
            Temporary log directory.
        """
        sample_audit_logger.log_calculation(
            operation="Portfolio_Return",
            inputs={"weights": [0.6, 0.4], "returns": [0.05, 0.03]},
            result=0.042,
            execution_time_ms=12.5,
            user_id="analyst_001",
            session_id="sess_123",
        )

        # Wait for log file to be written
        time.sleep(0.1)

        # Verify audit log was created
        audit_log = temp_log_dir / LOG_FILE_AUDIT
        assert audit_log.exists()

        # Read and verify content
        content = audit_log.read_text(encoding="utf-8")
        assert "Portfolio_Return" in content
        assert "analyst_001" in content

    @pytest.mark.unit()
    def Test_log_calculation_without_optional_params(
        self,
        sample_audit_logger: Audit_Logger,
    ) -> None:
        """Test logging calculation without optional parameters.

        Parameters
        ----------
        sample_audit_logger : Audit_Logger
            Audit logger fixture.
        """
        # Should not raise any exceptions
        sample_audit_logger.log_calculation(
            operation="Simple_Calculation",
            inputs={"a": 1, "b": 2},
            result=3,
            execution_time_ms=5.0,
        )

    @pytest.mark.unit()
    def Test_log_calculation_masks_sensitive_inputs(
        self,
        sample_audit_logger: Audit_Logger,
        temp_log_dir: Path,
    ) -> None:
        """Test audit calculation logs mask nested sensitive payload values.

        Parameters
        ----------
        sample_audit_logger : Audit_Logger
            Audit logger fixture.
        temp_log_dir : Path
            Temporary log directory.
        """
        sample_audit_logger.log_calculation(
            operation="Masked_Calculation",
            inputs={"api_key": "secret_value", "amount": 10},
            result={"token": "result_secret", "score": 1.0},
            execution_time_ms=1.0,
        )

        time.sleep(0.1)

        audit_log = temp_log_dir / LOG_FILE_AUDIT
        content = audit_log.read_text(encoding="utf-8")

        assert "***MASKED***" in content
        assert "secret_value" not in content
        assert "result_secret" not in content

    @pytest.mark.unit()
    def Test_log_data_access(
        self,
        sample_audit_logger: Audit_Logger,
        temp_log_dir: Path,
    ) -> None:
        """Test logging data access event.

        Parameters
        ----------
        sample_audit_logger : Audit_Logger
            Audit logger fixture.
        temp_log_dir : Path
            Temporary log directory.
        """
        sample_audit_logger.log_data_access(
            source="inputs/raw/data_ETFs.csv",
            operation="READ",
            record_count=252,
            user_id="analyst_001",
            session_id="sess_123",
            details={"file_size_mb": 2.5},
        )

        time.sleep(0.1)

        audit_log = temp_log_dir / LOG_FILE_AUDIT
        content = audit_log.read_text(encoding="utf-8")

        assert "data_ETFs.csv" in content
        assert "READ" in content
        assert "252" in content

    @pytest.mark.unit()
    def Test_log_parameter_change(
        self,
        sample_audit_logger: Audit_Logger,
        temp_log_dir: Path,
    ) -> None:
        """Test logging parameter change event.

        Parameters
        ----------
        sample_audit_logger : Audit_Logger
            Audit logger fixture.
        temp_log_dir : Path
            Temporary log directory.
        """
        sample_audit_logger.log_parameter_change(
            parameter_name="risk_free_rate",
            old_value=0.02,
            new_value=0.025,
            user_id="admin_001",
            reason="Updated to reflect market conditions",
        )

        time.sleep(0.1)

        audit_log = temp_log_dir / LOG_FILE_AUDIT
        content = audit_log.read_text(encoding="utf-8")

        assert "risk_free_rate" in content
        assert "0.02" in content or "0.025" in content

    @pytest.mark.unit()
    def Test_log_user_action_success(
        self,
        sample_audit_logger: Audit_Logger,
        temp_log_dir: Path,
    ) -> None:
        """Test logging successful user action.

        Parameters
        ----------
        sample_audit_logger : Audit_Logger
            Audit logger fixture.
        temp_log_dir : Path
            Temporary log directory.
        """
        sample_audit_logger.log_user_action(
            action="EXPORT",
            resource="portfolio_report.pdf",
            user_id="analyst_001",
            success=True,
            details={"format": "PDF", "pages": 15},
        )

        time.sleep(0.1)

        audit_log = temp_log_dir / LOG_FILE_AUDIT
        content = audit_log.read_text(encoding="utf-8")

        assert "EXPORT" in content
        assert "portfolio_report.pdf" in content

    @pytest.mark.unit()
    def Test_log_user_action_failure(
        self,
        sample_audit_logger: Audit_Logger,
        temp_log_dir: Path,
    ) -> None:
        """Test logging failed user action.

        Parameters
        ----------
        sample_audit_logger : Audit_Logger
            Audit logger fixture.
        temp_log_dir : Path
            Temporary log directory.
        """
        sample_audit_logger.log_user_action(
            action="DELETE",
            resource="client_data.csv",
            user_id="analyst_001",
            success=False,
            details={"error": "Permission denied"},
        )

        time.sleep(0.1)

        audit_log = temp_log_dir / LOG_FILE_AUDIT
        content = audit_log.read_text(encoding="utf-8")

        assert "DELETE" in content
        assert "client_data.csv" in content

    @pytest.mark.parametrize(
        "severity",
        ["INFO", "WARNING", "ERROR"],
    )
    @pytest.mark.unit()
    def Test_log_system_event(
        self,
        sample_audit_logger: Audit_Logger,
        severity: str,
    ) -> None:
        """Test logging system events with different severities.

        Parameters
        ----------
        sample_audit_logger : Audit_Logger
            Audit logger fixture.
        severity : str
            Log severity to test.
        """
        sample_audit_logger.log_system_event(
            event_name="CACHE_CLEARED",
            details={"cache_size_mb": 256},
            severity=severity,
        )
        # Should not raise exceptions


# ==============================================================================
# Test Performance Logging
# ==============================================================================


@pytest.mark.unit()
class Class_Test_Performance_Logging:
    """Test suite for performance logging utilities."""

    @pytest.mark.unit()
    def Test_log_performance_basic(self, temp_log_dir: Path) -> None:
        """Test basic performance logging.

        Parameters
        ----------
        temp_log_dir : Path
            Temporary log directory.
        """
        setup_logging(log_dir=temp_log_dir, enable_console=False)

        log_performance(
            operation_name="test_operation",
            execution_time_ms=123.45,
            details={"rows_processed": 1000},
        )

        time.sleep(0.1)

        perf_log = temp_log_dir / LOG_FILE_PERFORMANCE
        assert perf_log.exists()

    @pytest.mark.unit()
    def Test_log_performance_with_custom_logger(
        self,
        temp_log_dir: Path,
    ) -> None:
        """Test performance logging with custom logger instance.

        Parameters
        ----------
        temp_log_dir : Path
            Temporary log directory.
        """
        setup_logging(log_dir=temp_log_dir, enable_console=False)
        custom_logger = get_logger(name = "custom_perf")

        log_performance(
            operation_name="custom_operation",
            execution_time_ms=50.0,
            logger_instance=custom_logger,
        )

    @pytest.mark.unit()
    def Test_performance_timer_context_manager(
        self,
        temp_log_dir: Path,
    ) -> None:
        """Test Performance_Timer as context manager.

        Parameters
        ----------
        temp_log_dir : Path
            Temporary log directory.
        """
        setup_logging(log_dir=temp_log_dir, enable_console=False)

        with Performance_Timer("test_operation") as timer:
            time.sleep(0.01)  # Simulate work

        assert timer.elapsed_ms > 0
        assert timer.start_time > 0
        assert timer.end_time > timer.start_time

    @pytest.mark.unit()
    def Test_performance_timer_with_log_start(
        self,
        temp_log_dir: Path,
    ) -> None:
        """Test Performance_Timer with log_start enabled.

        Parameters
        ----------
        temp_log_dir : Path
            Temporary log directory.
        """
        setup_logging(log_dir=temp_log_dir, enable_console=False)

        with Performance_Timer("test_operation", log_start=True) as timer:
            time.sleep(0.01)

        assert timer.elapsed_ms > 0

    @pytest.mark.unit()
    def Test_performance_timer_with_exception(
        self,
        temp_log_dir: Path,
    ) -> None:
        """Test Performance_Timer handles exceptions gracefully.

        Parameters
        ----------
        temp_log_dir : Path
            Temporary log directory.
        """
        setup_logging(log_dir=temp_log_dir, enable_console=False)

        with pytest.raises(ValueError), Performance_Timer("test_operation") as timer:
            msg = "Test exception"
            raise ValueError(msg)

        # Timer should still have recorded time
        assert timer.elapsed_ms > 0

    @pytest.mark.unit()
    def Test_performance_timer_details(self, temp_log_dir: Path) -> None:
        """Test Performance_Timer with custom details.

        Parameters
        ----------
        temp_log_dir : Path
            Temporary log directory.
        """
        setup_logging(log_dir=temp_log_dir, enable_console=False)

        with Performance_Timer(
            "test_operation",
            details={"input_size": 1000, "algorithm": "quicksort"},
        ) as timer:
            time.sleep(0.01)

        assert timer.elapsed_ms > 0
        assert timer.details["input_size"] == 1000


# ==============================================================================
# Test Decorator
# ==============================================================================


@pytest.mark.unit()
class Class_Test_Log_Function_Call_Decorator:
    """Test suite for log_function_call decorator."""

    @pytest.mark.unit()
    def Test_decorator_basic_usage(self, temp_log_dir: Path) -> None:
        """Test basic decorator usage.

        Parameters
        ----------
        temp_log_dir : Path
            Temporary log directory.
        """
        setup_logging(log_dir=temp_log_dir, enable_console=False)

        @log_function_call()
        @pytest.mark.unit()
        def inner_function(a: int, b: int) -> int:
            """Test function."""
            return a + b

        result = inner_function(5, 3)
        assert result == 8

    @pytest.mark.unit()
    def Test_decorator_logs_performance(self, temp_log_dir: Path) -> None:
        """Test decorator logs performance metrics.

        Parameters
        ----------
        temp_log_dir : Path
            Temporary log directory.
        """
        setup_logging(log_dir=temp_log_dir, enable_console=False)

        @log_function_call(log_performance=True)
        def slow_function() -> str:
            """Slow function for testing."""
            time.sleep(0.01)
            return "done"

        result = slow_function()
        assert result == "done"

    @pytest.mark.unit()
    def Test_decorator_with_exception(self, temp_log_dir: Path) -> None:
        """Test decorator handles exceptions.

        Parameters
        ----------
        temp_log_dir : Path
            Temporary log directory.
        """
        setup_logging(log_dir=temp_log_dir, enable_console=False)

        @log_function_call()
        def failing_function() -> None:
            """Function that raises exception."""
            msg = "Test error"
            raise ValueError(msg)

        with pytest.raises(ValueError):
            failing_function()

    @pytest.mark.unit()
    def Test_decorator_preserves_function_metadata(self) -> None:
        """Test decorator preserves function name and docstring."""

        @log_function_call()
        def documented_function() -> str:
            """This is a documented function."""
            return "result"

        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is a documented function."

    @pytest.mark.unit()
    def Test_decorator_with_audit_event_type(self, temp_log_dir: Path) -> None:
        """Test decorator with audit event type.

        Parameters
        ----------
        temp_log_dir : Path
            Temporary log directory.
        """
        setup_logging(log_dir=temp_log_dir, enable_console=False)

        @log_function_call(audit_event_type="CALCULATION")
        def calculation_function(x: float, y: float) -> float:
            """Calculate sum."""
            return x + y

        result = calculation_function(10.5, 20.3)
        assert result == pytest.approx(30.8)

    @pytest.mark.unit()
    def Test_decorator_log_args_disabled(self, temp_log_dir: Path) -> None:
        """Test decorator with log_args disabled.

        Parameters
        ----------
        temp_log_dir : Path
            Temporary log directory.
        """
        setup_logging(log_dir=temp_log_dir, enable_console=False)

        @log_function_call(log_args=False)
        def function_with_sensitive_args(password: str) -> bool:
            """Function with sensitive arguments."""
            return len(password) > 8

        result = function_with_sensitive_args("secret123")
        assert result is True


# ==============================================================================
# Integration Tests
# ==============================================================================


@pytest.mark.integration()
class Class_Test_Logger_Integration:
    """Integration tests for complete logging workflows."""

    @pytest.mark.unit()
    def Test_complete_audit_workflow(self, temp_log_dir: Path) -> None:
        """Test complete audit logging workflow.

        Parameters
        ----------
        temp_log_dir : Path
            Temporary log directory.
        """
        # Setup
        setup_logging(
            log_level="DEBUG",
            environment="production",
            log_dir=temp_log_dir,
            enable_console=False,
        )

        # Create audit logger
        audit = Audit_Logger(logger_name="integration_test")

        # Log various events
        audit.log_calculation(
            operation="Portfolio_Optimization",
            inputs={"assets": ["AAPL", "MSFT", "GOOG"]},
            result={"weights": [0.4, 0.3, 0.3]},
            execution_time_ms=156.7,
            user_id="analyst_001",
        )

        audit.log_data_access(
            source="database/portfolio_data",
            operation="READ",
            record_count=500,
            user_id="analyst_001",
        )

        audit.log_user_action(
            action="EXPORT",
            resource="portfolio_report.xlsx",
            user_id="analyst_001",
            success=True,
        )

        time.sleep(0.2)

        # Verify audit log exists and contains events
        audit_log = temp_log_dir / LOG_FILE_AUDIT
        assert audit_log.exists()

        content = audit_log.read_text(encoding="utf-8")
        assert "Portfolio_Optimization" in content
        assert "analyst_001" in content
        assert "portfolio_data" in content

    @pytest.mark.unit()
    def Test_multiple_log_files_created(self, temp_log_dir: Path) -> None:
        """Test that multiple log files are created as expected.

        Parameters
        ----------
        temp_log_dir : Path
            Temporary log directory.
        """
        setup_logging(
            log_level="DEBUG",
            environment="development",
            log_dir=temp_log_dir,
            enable_console=False,
        )

        test_logger = get_logger(name = __name__)
        audit = Audit_Logger(logger_name="test")

        # Generate various log entries
        test_logger.debug("Debug message")
        test_logger.info("Info message")
        test_logger.error("Error message")

        audit.log_calculation(
            operation="Test",
            inputs={},
            result=None,
            execution_time_ms=10.0,
        )

        with Performance_Timer("test_op"):
            time.sleep(0.01)

        time.sleep(0.2)

        # Verify multiple log files exist
        assert (temp_log_dir / LOG_FILE_APPLICATION).exists()
        assert (temp_log_dir / LOG_FILE_AUDIT).exists()
        assert (temp_log_dir / LOG_FILE_ERROR).exists()
        assert (temp_log_dir / LOG_FILE_PERFORMANCE).exists()
        assert (temp_log_dir / LOG_FILE_DEBUG).exists()

    @pytest.mark.unit()
    def Test_json_log_format_is_valid(self, temp_log_dir: Path) -> None:
        """Test that JSON log entries are valid JSON.

        Parameters
        ----------
        temp_log_dir : Path
            Temporary log directory.
        """
        setup_logging(
            log_level="INFO",
            log_dir=temp_log_dir,
            enable_console=False,
            enable_JSON=True,
        )

        test_logger = get_logger(name = __name__)
        test_logger.info("Test JSON message")

        time.sleep(0.1)

        # Read application log
        app_log = temp_log_dir / LOG_FILE_APPLICATION
        content = app_log.read_text(encoding="utf-8")

        # Each line should be valid JSON
        # Note: loguru's native serialize=True produces a different structure
        # with 'record' and 'text' fields, not the custom format
        for line in content.strip().split("\n"):
            if line:
                parsed = json.loads(line)
                # Loguru's native JSON structure
                assert "record" in parsed
                assert "text" in parsed
                # Verify record contains expected fields
                assert "level" in parsed["record"]
                assert "message" in parsed["record"]


# ==============================================================================
# Edge Cases and Error Handling
# ==============================================================================


@pytest.mark.unit()
class Class_Test_Edge_Cases:
    """Test suite for edge cases and error handling."""

    @pytest.mark.unit()
    def Test_serialize_none_value(self) -> None:
        """Test serializing None value."""
        result = serialize_for_JSON(obj = None)
        assert result == "None"

    @pytest.mark.unit()
    def Test_serialize_empty_dict(self) -> None:
        """Test serializing empty dictionary."""
        result = serialize_for_JSON(obj = {})
        assert result == "{}"

    @pytest.mark.unit()
    def Test_serialize_nested_objects(self) -> None:
        """Test serializing nested objects."""
        data = {
            "timestamp": datetime.now(UTC),
            "path": Path("/tmp/test"),
            "nested": {"value": 42},
        }

        result = serialize_for_JSON(obj = data)
        assert isinstance(result, str)

    @pytest.mark.unit()
    def Test_audit_logger_with_none_values(
        self,
        sample_audit_logger: Audit_Logger,
    ) -> None:
        """Test audit logger handles None values gracefully.

        Parameters
        ----------
        sample_audit_logger : Audit_Logger
            Audit logger fixture.
        """
        # Should not raise exceptions with None values
        sample_audit_logger.log_calculation(
            operation="Test",
            inputs={},
            result=None,
            execution_time_ms=0.0,
            user_id=None,
            session_id=None,
        )

    @pytest.mark.unit()
    def Test_performance_timer_zero_duration(self, temp_log_dir: Path) -> None:
        """Test Performance_Timer with near-zero duration.

        Parameters
        ----------
        temp_log_dir : Path
            Temporary log directory.
        """
        setup_logging(log_dir=temp_log_dir, enable_console=False)

        with Performance_Timer("instant_op") as timer:
            pass  # No work

        # Should still record some time
        assert timer.elapsed_ms >= 0

    @pytest.mark.unit()
    def Test_logger_with_unicode_messages(self, temp_log_dir: Path) -> None:
        """Test logger handles Unicode characters correctly.

        Parameters
        ----------
        temp_log_dir : Path
            Temporary log directory.
        """
        setup_logging(log_dir=temp_log_dir, enable_console=False)

        test_logger = get_logger(name = __name__)
        test_logger.info("Test with Ã©mojis: ðŸš€ ðŸ“Š ðŸ’°")

        time.sleep(0.1)

        app_log = temp_log_dir / LOG_FILE_APPLICATION
        assert app_log.exists()


# ==============================================================================
# Run Tests
# ==============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])


# ==============================================================================
# Test filter_console_dynamic
# ==============================================================================


def _make_record(
    level_no: int,
    level_name: str,
    module_name: str,
    use_extra_name: bool = True,
) -> dict:
    """Build a minimal loguru-style record dict for filter testing.

    Parameters
    ----------
    level_no : int
        Numeric log level.
    level_name : str
        String level name (e.g. ``"DEBUG"``).
    module_name : str
        Dotted module path for the logger name.
    use_extra_name : bool
        When True the name is placed in ``record["extra"]["name"]``;
        otherwise only ``record["name"]`` is set (simulates direct loguru use).

    Returns
    -------
    dict
        Synthetic record compatible with :func:`filter_console_dynamic`.
    """
    extra: dict = {"name": module_name} if use_extra_name else {}
    return {
        "level": type("Level", (), {"no": level_no, "name": level_name})(),
        "name": module_name,
        "extra": extra,
    }


@pytest.fixture(autouse=True)
def reset_subtab_console_rules() -> None:
    """Clear _subtab_console_rules before and after every test.

    Returns
    -------
    None
    """
    _subtab_console_rules.clear()
    yield
    _subtab_console_rules.clear()


@pytest.mark.unit()
class Class_Test_Filter_Console_Dynamic:
    """Tests for filter_console_dynamic."""

    _PREFIX = "src.dashboard.shiny_tab_portfolios.subtab_portfolios_comparison"

    @pytest.mark.unit()
    def Test_warning_always_passes_when_no_rules(self) -> None:
        """WARNING passes even when no subtab rules are registered."""
        record = _make_record(LOG_LEVEL_WARNING, "WARNING", "any.module")
        assert filter_console_dynamic(record = record) is True

    @pytest.mark.unit()
    def Test_error_always_passes_when_no_rules(self) -> None:
        """ERROR passes even when no subtab rules are registered."""
        record = _make_record(40, "ERROR", "any.module")
        assert filter_console_dynamic(record = record) is True

    @pytest.mark.unit()
    def Test_debug_blocked_when_no_rules(self) -> None:
        """DEBUG is blocked when no subtab rules are registered."""
        record = _make_record(LOG_LEVEL_DEBUG, "DEBUG", "any.module")
        assert filter_console_dynamic(record = record) is False

    @pytest.mark.unit()
    def Test_info_blocked_when_no_rules(self) -> None:
        """INFO is blocked when no subtab rules are registered."""
        record = _make_record(LOG_LEVEL_INFO, "INFO", "any.module")
        assert filter_console_dynamic(record = record) is False

    @pytest.mark.unit()
    def Test_debug_rule_passes_debug_only(self) -> None:
        """``"debug"`` rule passes DEBUG but not INFO."""
        _subtab_console_rules[self._PREFIX] = "debug"
        debug_rec = _make_record(LOG_LEVEL_DEBUG, "DEBUG", self._PREFIX)
        info_rec = _make_record(LOG_LEVEL_INFO, "INFO", self._PREFIX)
        assert filter_console_dynamic(record = debug_rec) is True
        assert filter_console_dynamic(record = info_rec) is False

    @pytest.mark.unit()
    def Test_info_rule_passes_info_only(self) -> None:
        """``"info"`` rule passes INFO but not DEBUG."""
        _subtab_console_rules[self._PREFIX] = "info"
        debug_rec = _make_record(LOG_LEVEL_DEBUG, "DEBUG", self._PREFIX)
        info_rec = _make_record(LOG_LEVEL_INFO, "INFO", self._PREFIX)
        assert filter_console_dynamic(record = debug_rec) is False
        assert filter_console_dynamic(record = info_rec) is True

    @pytest.mark.unit()
    def Test_info_debug_rule_passes_both(self) -> None:
        """``"info_debug"`` rule passes both DEBUG and INFO."""
        _subtab_console_rules[self._PREFIX] = "info_debug"
        debug_rec = _make_record(LOG_LEVEL_DEBUG, "DEBUG", self._PREFIX)
        info_rec = _make_record(LOG_LEVEL_INFO, "INFO", self._PREFIX)
        assert filter_console_dynamic(record = debug_rec) is True
        assert filter_console_dynamic(record = info_rec) is True

    @pytest.mark.unit()
    def Test_unregistered_module_blocked_even_when_other_prefix_active(self) -> None:
        """Module not in any rule is blocked even when other rules exist."""
        _subtab_console_rules[self._PREFIX] = "debug"
        record = _make_record(LOG_LEVEL_DEBUG, "DEBUG", "src.dashboard.shiny_utils.reactives_access")
        assert filter_console_dynamic(record = record) is False

    @pytest.mark.unit()
    def Test_prefix_matching_is_startswith(self) -> None:
        """Filter matches sub-modules via startswith on the registered prefix."""
        _subtab_console_rules[self._PREFIX] = "info_debug"
        sub_module = self._PREFIX + ".some_helper"
        record = _make_record(LOG_LEVEL_DEBUG, "DEBUG", sub_module)
        assert filter_console_dynamic(record = record) is True

    @pytest.mark.unit()
    def Test_most_specific_prefix_wins_when_rules_overlap(self) -> None:
        """A more specific prefix must override a broader matching prefix."""
        broader_prefix = "src.dashboard"
        specific_prefix = self._PREFIX
        module_name = specific_prefix + ".some_helper"

        _subtab_console_rules[broader_prefix] = "info"
        _subtab_console_rules[specific_prefix] = "debug"

        debug_record = _make_record(LOG_LEVEL_DEBUG, "DEBUG", module_name)
        info_record = _make_record(LOG_LEVEL_INFO, "INFO", module_name)

        assert filter_console_dynamic(record = debug_record) is True
        assert filter_console_dynamic(record = info_record) is False

    @pytest.mark.unit()
    def Test_direct_loguru_name_field_used_when_extra_name_absent(self) -> None:
        """Filter falls back to record["name"] when extra["name"] is missing."""
        _subtab_console_rules[self._PREFIX] = "info"
        record = _make_record(LOG_LEVEL_INFO, "INFO", self._PREFIX, use_extra_name=False)
        assert filter_console_dynamic(record = record) is True

    @pytest.mark.unit()
    def Test_warning_passes_regardless_of_rule(self) -> None:
        """WARNING passes even when no rule is set for its module."""
        # No rule for this module â€” WARNING must still pass
        record = _make_record(LOG_LEVEL_WARNING, "WARNING", self._PREFIX)
        assert filter_console_dynamic(record = record) is True

    @pytest.mark.unit()
    def Test_new_constants_are_correct_values(self) -> None:
        """LOG_LEVEL_INFO == 20 and LOG_LEVEL_WARNING == 30."""
        assert LOG_LEVEL_INFO == 20
        assert LOG_LEVEL_WARNING == 30


# ==============================================================================
# Test set_console_level_for_subtab
# ==============================================================================


@pytest.mark.unit()
class Class_Test_Set_Console_Level_For_Subtab:
    """Tests for set_console_level_for_subtab."""

    _KEY = "portfolio_comparison"
    _PREFIX = "src.dashboard.shiny_tab_portfolios.subtab_portfolios_comparison"

    @pytest.mark.unit()
    def Test_registers_debug_rule(self) -> None:
        """Calling with ``"debug"`` inserts the prefix into active rules."""
        set_console_level_for_subtab(_subtab_key = self._KEY, module_prefix = self._PREFIX, level_key = "debug")
        assert _subtab_console_rules.get(self._PREFIX) == "debug"

    @pytest.mark.unit()
    def Test_registers_info_rule(self) -> None:
        """Calling with ``"info"`` inserts the prefix with value ``"info"``."""
        set_console_level_for_subtab(_subtab_key = self._KEY, module_prefix = self._PREFIX, level_key = "info")
        assert _subtab_console_rules.get(self._PREFIX) == "info"

    @pytest.mark.unit()
    def Test_registers_info_debug_rule(self) -> None:
        """Calling with ``"info_debug"`` inserts the prefix correctly."""
        set_console_level_for_subtab(_subtab_key = self._KEY, module_prefix = self._PREFIX, level_key = "info_debug")
        assert _subtab_console_rules.get(self._PREFIX) == "info_debug"

    @pytest.mark.unit()
    def Test_no_display_removes_existing_rule(self) -> None:
        """``"no_display"`` removes a previously registered prefix."""
        _subtab_console_rules[self._PREFIX] = "debug"
        set_console_level_for_subtab(_subtab_key = self._KEY, module_prefix = self._PREFIX, level_key = "no_display")
        assert self._PREFIX not in _subtab_console_rules

    @pytest.mark.unit()
    def Test_no_display_is_noop_when_not_registered(self) -> None:
        """``"no_display"`` on an absent prefix does not raise."""
        set_console_level_for_subtab(_subtab_key = self._KEY, module_prefix = self._PREFIX, level_key = "no_display")
        assert self._PREFIX not in _subtab_console_rules

    @pytest.mark.unit()
    def Test_overwrite_existing_rule(self) -> None:
        """Setting a new level for an already-registered prefix overwrites it."""
        set_console_level_for_subtab(_subtab_key = self._KEY, module_prefix = self._PREFIX, level_key = "debug")
        set_console_level_for_subtab(_subtab_key = self._KEY, module_prefix = self._PREFIX, level_key = "info")
        assert _subtab_console_rules.get(self._PREFIX) == "info"

    @pytest.mark.unit()
    def Test_independent_subtabs_stored_separately(self) -> None:
        """Rules for different subtab prefixes are stored independently."""
        sim_prefix = "src.dashboard.shiny_tab_results.subtab_simulation"
        set_console_level_for_subtab(_subtab_key = self._KEY, module_prefix = self._PREFIX, level_key = "debug")
        set_console_level_for_subtab(_subtab_key = "simulation", module_prefix = sim_prefix, level_key = "info")
        assert _subtab_console_rules[self._PREFIX] == "debug"
        assert _subtab_console_rules[sim_prefix] == "info"

    @pytest.mark.unit()
    def Test_filter_reflects_change_immediately(self) -> None:
        """After set_console_level_for_subtab the filter reflects the new rule."""
        record = _make_record(LOG_LEVEL_DEBUG, "DEBUG", self._PREFIX)
        assert filter_console_dynamic(record = record) is False  # silent by default
        set_console_level_for_subtab(_subtab_key = self._KEY, module_prefix = self._PREFIX, level_key = "debug")
        assert filter_console_dynamic(record = record) is True  # now visible
        set_console_level_for_subtab(_subtab_key = self._KEY, module_prefix = self._PREFIX, level_key = "no_display")
        assert filter_console_dynamic(record = record) is False  # silent again


# ==============================================================================
# Branch coverage additions
# ==============================================================================


@pytest.mark.unit()
class Class_Test_Format_Record_Trace_Level:
    """format_record_as_JSON with TRACE-level record (level.no < LOG_LEVEL_DEBUG)."""

    @pytest.mark.unit()
    def Test_trace_level_omits_thread_process_info(self) -> None:
        """TRACE (level.no=5) skips the thread/process block."""
        from src.utils.custom_exceptions_errors_loggers.logger_custom import (
            format_record_as_JSON,
        )
        from datetime import UTC, datetime

        record = {
            "time": datetime.now(UTC),
            "level": type("Level", (), {"name": "TRACE", "no": 5})(),
            "name": "trace_module",
            "module": "trace_module",
            "function": "trace_fn",
            "line": 1,
            "message": "trace message",
            "exception": None,
            "extra": {},
            "thread": type("Thread", (), {"id": 1, "name": "main"})(),
            "process": type("Process", (), {"id": 2, "name": "main"})(),
        }
        import json as _json
        parsed = _json.loads(format_record_as_JSON(record = record))
        assert "thread_id" not in parsed
        assert "thread_name" not in parsed
        assert "process_id" not in parsed

    @pytest.mark.unit()
    def Test_extra_key_already_in_log_entry_is_skipped(self) -> None:
        """Extra key already present in log_entry is NOT overwritten (False branch)."""
        from src.utils.custom_exceptions_errors_loggers.logger_custom import (
            format_record_as_JSON,
        )
        from datetime import UTC, datetime
        import json as _json

        record = {
            "time": datetime.now(UTC),
            "level": type("Level", (), {"name": "INFO", "no": 20})(),
            "name": "mod",
            "module": "mod",
            "function": "fn",
            "line": 1,
            "message": "original message",
            "exception": None,
            # "message" is already a key in log_entry â†’ if key not in log_entry: False
            "extra": {"message": "OVERWRITE_ATTEMPT", "new_key": "new_val"},
            "thread": type("Thread", (), {"id": 1, "name": "main"})(),
            "process": type("Process", (), {"id": 2, "name": "main"})(),
        }
        parsed = _json.loads(format_record_as_JSON(record = record))
        # "message" should retain its original value (not overwritten)
        assert parsed["message"] == "original message"
        # "new_key" was not in log_entry so it should be added
        assert parsed["new_key"] == "new_val"

    @pytest.mark.unit()
    def Test_exception_type_none_and_value_none(self) -> None:
        """Exception block with type=None and value=None uses None branches."""
        from src.utils.custom_exceptions_errors_loggers.logger_custom import (
            format_record_as_JSON,
        )
        from datetime import UTC, datetime
        import json as _json

        record = {
            "time": datetime.now(UTC),
            "level": type("Level", (), {"name": "ERROR", "no": 40})(),
            "name": "mod",
            "module": "mod",
            "function": "fn",
            "line": 1,
            "message": "error msg",
            "exception": type("ExcInfo", (), {"type": None, "value": None, "traceback": None})(),
            "extra": {},
            "thread": type("Thread", (), {"id": 1, "name": "main"})(),
            "process": type("Process", (), {"id": 2, "name": "main"})(),
        }
        parsed = _json.loads(format_record_as_JSON(record = record))
        assert parsed["exception"]["type"] is None
        assert parsed["exception"]["value"] is None
        assert parsed["exception"]["traceback"] is None


@pytest.mark.unit()
class Class_Test_Filter_Console_Dynamic_Unknown_Level_Key:
    """filter_console_dynamic with an unrecognised level_key falls through."""

    @pytest.mark.unit()
    def Test_unknown_level_key_returns_false(self) -> None:
        """A matching prefix with an unknown level_key falls through and returns False."""
        from src.utils.custom_exceptions_errors_loggers.logger_custom import (
            _subtab_console_rules,
            filter_console_dynamic,
            LOG_LEVEL_DEBUG,
        )

        prefix = "src.dashboard.unknown_subtab"
        _subtab_console_rules[prefix] = "unknown_key"
        try:
            record = _make_record(LOG_LEVEL_DEBUG, "DEBUG", prefix)
            result = filter_console_dynamic(record = record)
            assert result is False
        finally:
            _subtab_console_rules.pop(prefix, None)


@pytest.mark.unit()
class Class_Test_Setup_Logging_No_Log_Dir:
    """setup_logging() without log_dir triggers the log_dir = DEFAULT_LOG_DIR branch."""

    @pytest.mark.unit()
    def Test_setup_logging_uses_default_log_dir_when_none(self, tmp_path: Path) -> None:
        """setup_logging with log_dir=None falls back to DEFAULT_LOG_DIR path."""
        import src.utils.custom_exceptions_errors_loggers._logger_handlers as handlers_mod
        import src.utils.custom_exceptions_errors_loggers.logger_custom as mod
        from src.utils.custom_exceptions_errors_loggers.logger_custom import (
            DEFAULT_LOG_DIR,
            setup_logging,
        )

        # Redirect DEFAULT_LOG_DIR to tmp_path so we don't litter the project
        original_default = mod.DEFAULT_LOG_DIR
        original_handlers_default = handlers_mod.DEFAULT_LOG_DIR
        mod.DEFAULT_LOG_DIR = tmp_path / "default_logs"
        handlers_mod.DEFAULT_LOG_DIR = tmp_path / "default_logs"
        try:
            setup_logging(log_dir=None, enable_console=False)
            assert (tmp_path / "default_logs").exists()
        finally:
            mod.DEFAULT_LOG_DIR = original_default
            handlers_mod.DEFAULT_LOG_DIR = original_handlers_default
            logger.remove()


@pytest.mark.unit()
class Class_Test_Setup_Logging_Console_Enabled:
    """setup_logging(enable_console=True) exercises the console handler block."""

    @pytest.mark.unit()
    def Test_setup_logging_with_console_enabled(self, tmp_path: Path) -> None:
        """Console handler is added when enable_console=True."""
        from src.utils.custom_exceptions_errors_loggers.logger_custom import setup_logging

        # Should not raise on Windows (colorize is disabled automatically)
        setup_logging(
            log_dir=tmp_path / "con_logs",
            enable_console=True,
        )
        test_logger = get_logger(name = "con_test")
        test_logger.warning("console test warning")  # warning always passes filter


@pytest.mark.unit()
class Class_Test_Get_Logger_Auto_Configure:
    """get_logger triggers auto-configure when _logging_configured is False."""

    @pytest.mark.unit()
    def Test_get_logger_auto_configures_when_flag_false(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """If _logging_configured is False, get_logger calls setup_logging()."""
        import src.utils.custom_exceptions_errors_loggers._logger_handlers as handlers_mod
        import src.utils.custom_exceptions_errors_loggers.logger_custom as mod
        from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

        original_default = mod.DEFAULT_LOG_DIR
        mod.DEFAULT_LOG_DIR = tmp_path / "auto_logs"
        monkeypatch.setattr(handlers_mod, "_logging_configured", False)
        try:
            lg = get_logger(name = "auto_test")
            assert lg is not None
            assert handlers_mod._logging_configured is True
        finally:
            mod.DEFAULT_LOG_DIR = original_default


@pytest.mark.unit()
class Class_Test_Log_Function_Call_Log_Result:
    """log_function_call with log_result=True covers the result_type branch."""

    @pytest.mark.unit()
    def Test_log_result_true_adds_result_type(self, tmp_path: Path) -> None:
        """With log_result=True and non-None return, result_type is captured."""
        from src.utils.custom_exceptions_errors_loggers.logger_custom import (
            log_function_call,
            setup_logging,
        )

        setup_logging(log_dir=tmp_path / "res_logs", enable_console=False)

        @log_function_call(log_result=True)
        def _fn() -> str:
            return "done"

        result = _fn()
        assert result == "done"

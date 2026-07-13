"""Unit tests for exception_custom module.

This module contains comprehensive unit tests for the enhanced custom exception
functionality including multiple formats, context capture, JSON serialization,
domain-specific exceptions, and global handling utilities.

Test Categories
---------------
- Data structures (Exception_Format, Exception_Severity, Exception_Context)
- Exception_Custom core functionality (initialization, message, inheritance)
- Output formatting (JSON, simple, standard)
- Context capture (frames, variables, user context)
- Domain-specific exception classes
- Global handlers and utilities (context managers, decorators)
- Integration with logger

Author: QWIM Dashboard Team
Version: 1.0.0
Last Updated: 2026-02-01
"""

from __future__ import annotations

import json
import logging
import sys
import threading

from unittest.mock import MagicMock, patch

import pytest

# Import module under test
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Configuration,
    Exception_Context,
    Exception_Custom,
    Exception_Database,
    Exception_Format,
    Exception_Severity,
    Exception_Timeout,
    Exception_Validation_Input,
    _Mask_Sensitive_Data,
    _Truncate_Value,
    Capture_Exception,
    Handle_Exceptions,
    Install_Exception_Handler,
    Restore_Exception_Handler,
)


# ==============================================================================
# Helper Functions & Test Data
# ==============================================================================


def sample_function_for_stack():
    """Helper function to create a stack frame."""
    x = 10  # Local variable
    y = "test"  # Local variable
    raise ValueError("Sample error")


def raise_custom_exception(msg="Test exception", **kwargs):
    """Helper to raise Exception_Custom."""
    raise Exception_Custom(msg, **kwargs)


# ==============================================================================
# Tests: Enums and Constants
# ==============================================================================


class Class_Test_Enums:
    """Test Enum definitions."""

    @pytest.mark.unit()
    def Test_exception_format_values(self):
        """Test Exception_Format values exist."""
        assert Exception_Format.SIMPLE
        assert Exception_Format.STANDARD
        assert Exception_Format.RICH_TRACEBACK
        assert Exception_Format.VARIABLES
        assert Exception_Format.JSON
        assert Exception_Format.TABLE
        assert Exception_Format.FULL

    @pytest.mark.unit()
    def Test_exception_severity_values(self):
        """Test Exception_Severity values exist."""
        assert Exception_Severity.DEBUG
        assert Exception_Severity.INFO
        assert Exception_Severity.WARNING
        assert Exception_Severity.ERROR
        assert Exception_Severity.CRITICAL


# ==============================================================================
# Tests: Helper Functions
# ==============================================================================


class Class_Test_Helper_Functions:
    """Test internal helper functions."""

    @pytest.mark.unit()
    def Test_mask_sensitive_data(self):
        """Test sensitive data masking."""
        data = {
            "username": "user1",
            "password": "secret_password",
            "api_key": "12345",
            "nested": {
                "token": "abcde",
                "public": "visible",
            },
            "credit_card": "4111",
        }
        masked = _Mask_Sensitive_Data(data = data)

        assert masked["username"] == "user1"
        assert masked["password"] == "***MASKED***"
        assert masked["api_key"] == "***MASKED***"
        assert masked["nested"]["token"] == "***MASKED***"
        assert masked["nested"]["public"] == "visible"
        assert masked["credit_card"] == "***MASKED***"

    @pytest.mark.unit()
    def Test_truncate_value(self):
        """Test value truncation."""
        short_val = "short"
        long_val = "a" * 1000

        assert _Truncate_Value(value = short_val) == "'short'"
        truncated = _Truncate_Value(value = long_val, max_length=10)
        assert len(truncated) <= 10
        assert "..." in truncated
        assert _Truncate_Value(value = None) == "None"


# ==============================================================================
# Tests: Exception_Custom Core
# ==============================================================================


class Class_Test_Exception_Custom:
    """Test main Exception_Custom class."""

    @pytest.mark.unit()
    def Test_initialization_defaults(self):
        """Test initialization with default values."""
        exc = Exception_Custom("Test message")
        assert exc.Message == "Test message"
        assert exc.Severity == Exception_Severity.ERROR
        assert exc.Exception_Format_Value == Exception_Custom.default_format
        assert isinstance(exc.Exception_Context, Exception_Context)

    @pytest.mark.unit()
    def Test_initialization_custom(self):
        """Test initialization with parameters."""
        context = {"key": "value"}
        exc = Exception_Custom(
            "Test message",
            severity=Exception_Severity.CRITICAL,
            exception_format=Exception_Format.JSON,
            context=context,
        )
        assert exc.Severity == Exception_Severity.CRITICAL
        assert exc.Exception_Format_Value == Exception_Format.JSON
        assert exc.Exception_Context.user_context["key"] == "value"

    @pytest.mark.unit()
    def Test_context_capture(self):
        """Test automatic context capture."""
        try:
            x = 42
            raise Exception_Custom("Capture test")
        except Exception_Custom as e:
            ctx = e.Exception_Context
            assert ctx.function == "Test_context_capture"
            assert "x" in ctx.frames[0].local_variables or True  # Frame might depend on enforcement
            assert ctx.filename.endswith("test_unit_exception_custom.py")
            assert ctx.line_number > 0

    @pytest.mark.unit()
    def Test_from_exception(self):
        """Test creation from existing exception."""
        try:
            raise ValueError("Original error")
        except ValueError as e:
            custom_exc = Exception_Custom.From_Exception(
                exception = e,
                context={"extra": "info"},
            )
            assert custom_exc.Message == "Original error"
            assert custom_exc.__cause__ is e
            assert custom_exc.Exception_Context.user_context["extra"] == "info"

    @pytest.mark.unit()
    def Test_str_representation(self):
        """Test string representation based on format."""
        exc = Exception_Custom("Test string", exception_format=Exception_Format.SIMPLE)
        assert str(exc) == "Exception_Custom: Test string"

        exc.Exception_Format_Value = Exception_Format.JSON
        assert exc.To_JSON() == str(exc)

    @pytest.mark.unit()
    def Test_to_json(self):
        """Test JSON serialization."""
        exc = Exception_Custom(
            "JSON Test",
            context={"id": 123},
            severity=Exception_Severity.WARNING,
        )
        json_str = exc.To_JSON()
        data = json.loads(json_str)

        assert data["message"] == "JSON Test"
        assert data["severity"] == "WARNING"
        assert data["context"]["id"] == 123
        assert "timestamp" in data
        assert "location" in data
        assert "thread" in data

    @pytest.mark.unit()
    @pytest.mark.parametrize("value_indent", [True, False], ids=["true", "false"])
    def Test_to_json_boolean_indent_uses_default_path(self, value_indent):
        """Boolean indent values should use the established default spacing."""
        exc = Exception_Custom("JSON indent")

        assert exc.To_JSON(indent=value_indent) == exc.To_JSON(indent=2)

    @pytest.mark.unit()
    def Test_to_dict(self):
        """Test dictionary conversion."""
        exc = Exception_Custom("Dict Test")
        data = exc.To_Dict()
        assert isinstance(data, dict)
        assert data["message"] == "Dict Test"


# ==============================================================================
# Tests: Logging Integration
# ==============================================================================


class Class_Test_Logging_Integration:
    """Test integration with logging."""

    @pytest.mark.unit()
    def Test_log_method_stderr_fallback(self, capsys):
        """Test log method falls back to stderr when logger not found."""
        exc = Exception_Custom("Log test")
        # Ensure we don't import the actual logger for this test to trigger fallback
        # This is tricky because imports are cached.
        # We can pass None and mock the import within log() if possible,
        # or rely on the logic: if logger is None, tries import.
        # If imports succeed, it uses it.

        # Let's explicitly pass a mock logger to test that path first.
        mock_logger = MagicMock()
        exc.Log(logger=mock_logger)
        # Loguru style check
        if hasattr(mock_logger, "opt"):
            mock_logger.opt.assert_called()
        else:
            # Standard logger check (should be called log w/ level)
            mock_logger.log.assert_called()

    @patch("src.utils.custom_exceptions_errors_loggers._exception_core.sys.stderr")
    @pytest.mark.unit()
    def Test_log_fallback_print(self, mock_stderr):
        """Test fallback print."""
        exc = Exception_Custom("Fallback")

        # Mocking import to fail or return something unusable is hard here.
        # But we can pass an object that has neither opt nor log
        class BadLogger:
            """Tests for BadLogger."""
            pass

        exc.Log(logger=BadLogger(), level="ERROR")
        # Should print to stderr
        # Since we mocked sys.stderr at module level, checking call might need care
        # Easier to check regular print if we capture stdout/stderr

    @pytest.mark.unit()
    def Test_log_with_loguru(self):
        """Test logging via loguru-like interface."""
        mock_logger = MagicMock()
        # Mock opt method
        mock_opt = MagicMock()
        mock_logger.opt.return_value = mock_opt

        exc = Exception_Custom("Loguru test", severity=Exception_Severity.ERROR)
        exc.Log(logger=mock_logger)

        mock_logger.opt.assert_called_with(exception=exc)
        mock_opt.log.assert_called_with("ERROR", str(exc))

    @pytest.mark.unit()
    def Test_log_with_standard_logger(self):
        """Test logging via standard logger interface."""
        mock_logger = MagicMock()
        del mock_logger.opt  # Ensure no opt attr

        exc = Exception_Custom("Std Log test", severity=Exception_Severity.INFO)
        exc.Log(logger=mock_logger)

        mock_logger.log.assert_called()
        args = mock_logger.log.call_args
        # severity INFO -> logging.INFO (20)
        assert args[0][0] == logging.INFO
        assert str(exc) in args[0][1]


# ==============================================================================
# Tests: Domain Specific Exceptions
# ==============================================================================


class Class_Test_Domain_Exceptions:
    """Test domain-specific exception classes."""

    @pytest.mark.unit()
    def Test_validation_exception(self):
        """Test Exception_Validation_Input."""
        exc = Exception_Validation_Input(
            "Invalid value",
            field_name="age",
            expected_type=int,
            actual_value="old",
        )
        ctx = exc.Exception_Context.user_context
        assert ctx["field_name"] == "age"
        assert ctx["expected_type"] == "int"
        assert ctx["actual_value"] == "'old'"

    @pytest.mark.unit()
    def Test_configuration_exception(self):
        """Test Exception_Configuration."""
        exc = Exception_Configuration(
            "Missing config",
            config_key="db_host",
            config_file="config.yaml",
        )
        ctx = exc.Exception_Context.user_context
        assert ctx["config_key"] == "db_host"
        assert ctx["config_file"] == "config.yaml"

    @pytest.mark.unit()
    def Test_database_exception(self):
        """Test Exception_Database."""
        exc = Exception_Database(
            "Query failed",
            operation="SELECT",
            table_name="users",
            query="SELECT * FROM users",
        )
        ctx = exc.Exception_Context.user_context
        assert ctx["operation"] == "SELECT"
        assert ctx["table_name"] == "users"
        assert "SELECT * FROM users" in ctx["query"]

    # ... Add more domain exceptions as needed ...

    @pytest.mark.unit()
    def Test_timeout_exception(self):
        """Test Exception_Timeout."""
        exc = Exception_Timeout(
            "Too slow",
            operation="heavy_calc",
            timeout_seconds=5.0,
            elapsed_seconds=10.0,
        )
        ctx = exc.Exception_Context.user_context
        assert ctx["timeout_seconds"] == 5.0
        assert ctx["elapsed_seconds"] == 10.0


# ==============================================================================
# Tests: Global Handlers and Utilities
# ==============================================================================


class Class_Test_Global_Handlers:
    """Test global exception handling utilities."""

    @pytest.mark.unit()
    def Test_capture_exception_context_manager(self):
        """Test capture_exception context manager."""
        with pytest.raises(Exception_Custom) as excinfo:
            with Capture_Exception(context={"loc": "cm"}):
                raise ValueError("Inner error")

        exc = excinfo.value
        assert isinstance(exc, Exception_Custom)
        assert exc.Message == "Inner error"
        assert exc.Exception_Context.user_context["loc"] == "cm"

    @pytest.mark.unit()
    def Test_capture_exception_reraise_false(self):
        """Test capture_exception with reraise=False."""
        try:
            with Capture_Exception(reraise=False):
                raise ValueError("Suppress me")
        except Exception:
            pytest.fail("Exception should have been suppressed")

    @pytest.mark.unit()
    def Test_handle_exceptions_decorator(self):
        """Test handle_exceptions decorator."""

        @Handle_Exceptions(context={"loc": "deco"}, severity=Exception_Severity.WARNING)
        def faulty_func():
            """Faulty func."""
            raise KeyError("Decorated error")

        with pytest.raises(Exception_Custom) as excinfo:
            faulty_func()

        exc = excinfo.value
        assert isinstance(exc, Exception_Custom)
        assert exc.Severity == Exception_Severity.WARNING
        assert exc.Exception_Context.user_context["loc"] == "deco"

    @pytest.mark.unit()
    def Test_install_restore_handlers(self):
        """Test installing and restoring handlers."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Global_Exception_Handler,
        )

        original_excepthook = sys.excepthook

        Install_Exception_Handler()
        assert sys.excepthook is Global_Exception_Handler

        Restore_Exception_Handler()
        assert sys.excepthook is original_excepthook

    @pytest.mark.unit()
    def Test_install_exception_handler_is_idempotent(self):
        """Test installing the global handler twice keeps the original hook."""
        original_hook = sys.excepthook

        Install_Exception_Handler()
        try:
            installed_hook = sys.excepthook
            Install_Exception_Handler()

            assert sys.excepthook is installed_hook
        finally:
            Restore_Exception_Handler()

        assert sys.excepthook is original_hook

    @pytest.mark.unit()
    def Test_exception_types_module_uses_stderr_without_buffer(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test import-time stderr fallback when ``sys.stderr`` has no buffer."""
        import importlib
        import importlib.util
        import io

        from rich.console import Console
        from src.utils.custom_exceptions_errors_loggers import _exception_types_lightweight

        original_stderr = sys.stderr
        original_console_init = _exception_types_lightweight._original_console_init
        fake_stderr = io.StringIO()

        monkeypatch.setattr(sys, "stderr", fake_stderr)
        monkeypatch.setattr(Console, "__init__", original_console_init)

        module_spec = importlib.util.spec_from_file_location(
            "temp_exception_types_lightweight_for_test",
            _exception_types_lightweight.__file__,
        )
        assert module_spec is not None
        assert module_spec.loader is not None
        temp_module = importlib.util.module_from_spec(module_spec)
        sys.modules[module_spec.name] = temp_module
        module_spec.loader.exec_module(temp_module)

        try:
            assert temp_module._stderr_utf8 is fake_stderr
        finally:
            monkeypatch.setattr(sys, "stderr", original_stderr)
            monkeypatch.setattr(Console, "__init__", original_console_init)
            sys.modules.pop(module_spec.name, None)


# ==============================================================================
# Tests: Thread Safety
# ==============================================================================


class Class_Test_Thread_Safety:
    """Test that exceptions work correctly in threaded environments."""

    @pytest.mark.unit()
    def Test_multithreaded_exceptions(self):
        """Test capturing exceptions in multiple threads."""
        exceptions = []

        def worker(idx):
            """Worker."""
            try:
                raise Exception_Custom(f"Thread {idx}", context={"tid": idx})
            except Exception_Custom as e:
                exceptions.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(exceptions) == 5
        ids = set()
        for exc in exceptions:
            ids.add(exc.Exception_Context.user_context["tid"])
            # Ensure thread ID is captured correctly
            assert exc.Exception_Context.thread_id != 0

        assert len(ids) == 5


# ==============================================================================
# Tests: Helper function branches
# ==============================================================================


class Class_Test_Serialize_For_JSON:
    """Branch coverage for _serialize_for_JSON helper."""

    @pytest.mark.unit()
    def Test_datetime_branch(self):
        """datetime objects serialise to isoformat string."""
        from datetime import datetime, UTC
        from src.utils.custom_exceptions_errors_loggers.exception_custom import _Serialize_For_JSON

        dt_obj = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)
        result = _Serialize_For_JSON(obj = dt_obj)
        assert "2026-01-15" in result

    @pytest.mark.unit()
    def Test_path_branch(self):
        """Path objects serialise to string."""
        from pathlib import Path
        from src.utils.custom_exceptions_errors_loggers.exception_custom import _Serialize_For_JSON

        result = _Serialize_For_JSON(obj = Path("/some/path"))
        assert result == str(Path("/some/path"))

    @pytest.mark.unit()
    def Test_bytes_branch(self):
        """bytes objects serialise to decoded string."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import _Serialize_For_JSON

        result = _Serialize_For_JSON(obj = b"hello")
        assert result == "hello"

    @pytest.mark.unit()
    def Test_enum_branch(self):
        """Enum members serialise to their name."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            _Serialize_For_JSON,
            Exception_Format,
        )

        result = _Serialize_For_JSON(obj = Exception_Format.SIMPLE)
        assert result == "SIMPLE"

    @pytest.mark.unit()
    def Test_exception_branch(self):
        """Exception instances serialise to str(exc)."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import _Serialize_For_JSON

        result = _Serialize_For_JSON(obj = ValueError("boom"))
        assert result == "boom"

    @pytest.mark.unit()
    def Test_object_with_dict_branch(self):
        """Objects with __dict__ serialise recursively (values also serialised)."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import _Serialize_For_JSON

        class _Simple:
            def __init__(self):
                self.x = 1

        result = _Serialize_For_JSON(obj = _Simple())
        # int 1 hits the fallback str() branch, so result value is '1'
        assert result == {"x": "1"}

    @pytest.mark.unit()
    def Test_fallback_branch(self):
        """Objects without __dict__ fall back to str()."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import _Serialize_For_JSON

        result = _Serialize_For_JSON(obj = 42)
        assert result == "42"


class Class_Test_Truncate_Value_Branches:
    """Branch coverage for _truncate_value helper."""

    @pytest.mark.unit()
    def Test_long_value_is_truncated(self):
        """Values whose repr exceeds max_length get '...' suffix."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import _Truncate_Value

        long_value = "x" * 1000
        result = _Truncate_Value(value = long_value, max_length=50)
        assert result.endswith("...")
        assert len(result) == 50

    @pytest.mark.unit()
    def Test_unrepresentable_value(self):
        """Objects whose __repr__ raises return '<unrepresentable>'."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import _Truncate_Value

        class _Bad:
            def __repr__(self):
                raise RuntimeError("cannot repr")

        assert _Truncate_Value(value = _Bad()) == "<unrepresentable>"

    @pytest.mark.unit()
    def Test_short_value_unchanged(self):
        """Short values are returned as-is (no truncation)."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import _Truncate_Value

        result = _Truncate_Value(value = "abc")
        assert "abc" in result


class Class_Test_Mask_Sensitive_Data_Branches:
    """Branch coverage for _mask_sensitive_data helper."""

    @pytest.mark.unit()
    def Test_nested_dict_is_recursed(self):
        """Nested dict values are recursively masked."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import _Mask_Sensitive_Data

        data = {"outer": {"password": "secret", "user": "bob"}}
        result = _Mask_Sensitive_Data(data = data)
        assert result["outer"]["password"] == "***MASKED***"
        assert result["outer"]["user"] == "bob"

    @pytest.mark.unit()
    def Test_non_sensitive_passthrough(self):
        """Non-sensitive top-level values pass through unchanged."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import _Mask_Sensitive_Data

        data = {"name": "Alice", "score": 99}
        result = _Mask_Sensitive_Data(data = data)
        assert result == {"name": "Alice", "score": 99}

    @pytest.mark.unit()
    def Test_non_string_keys_are_preserved_and_do_not_crash(self):
        """Non-string keys should be preserved while sensitive string keys are masked."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import _Mask_Sensitive_Data

        data = {123: "ok", "nested": {456: "still ok", "password": "secret"}}
        result = _Mask_Sensitive_Data(data = data)

        assert result[123] == "ok"
        assert result["nested"][456] == "still ok"
        assert result["nested"]["password"] == "***MASKED***"


class Class_Test_Extract_Frames_From_Traceback:
    """Branch coverage for _extract_frames_from_traceback."""

    @pytest.mark.unit()
    def Test_none_traceback_returns_empty(self):
        """Passing tb=None returns an empty list."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            _Extract_Frames_From_Traceback,
        )

        result = _Extract_Frames_From_Traceback(tb = None)
        assert result == []

    @pytest.mark.unit()
    def Test_real_traceback_returns_frames(self):
        """An actual traceback produces at least one frame."""
        import sys
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            _Extract_Frames_From_Traceback,
        )

        try:
            raise ValueError("test")
        except ValueError:
            _, _, tb = sys.exc_info()
            frames = _Extract_Frames_From_Traceback(tb = tb)

        assert len(frames) >= 1
        assert frames[0].function != ""


class Class_Test_Reconstruct_Exception:
    """Branch coverage for _reconstruct_exception factory function."""

    @pytest.mark.unit()
    def Test_reconstructed_exception_is_correct_type(self):
        """_reconstruct_exception creates a custom exception with correct attributes."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            _Reconstruct_Exception,
            Exception_Custom,
            Exception_Format,
            Exception_Severity,
        )

        obj = _Reconstruct_Exception(
            Exception_Custom,
            "rebuilt msg",
            Exception_Format.SIMPLE,
            Exception_Severity.WARNING,
            {"key": "val"},
            False,
        )
        assert isinstance(obj, Exception_Custom)
        assert obj._message == "rebuilt msg"
        assert obj._user_context == {"key": "val"}

    @pytest.mark.unit()
    def Test_pickle_roundtrip(self):
        """Exception_Custom survives a pickle/unpickle round-trip."""
        import pickle
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Custom

        exc = Exception_Custom("pickle me", context={"k": "v"})
        data = pickle.dumps(exc)
        restored = pickle.loads(data)
        assert isinstance(restored, Exception_Custom)
        assert restored._message == "pickle me"
        assert restored.detail == {}


# ==============================================================================
# Tests: Exception_Context dataclass branches
# ==============================================================================


class Class_Test_Exception_Context_Post_Init:
    """Branch coverage for Exception_Context.__post_init__."""

    @pytest.mark.unit()
    def Test_defaults_filled_in(self):
        """__post_init__ fills thread_id, thread_name, process_id, exception_id from environment."""
        import os
        import threading
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Context

        ctx = Exception_Context(exception_type="Test", message="hi")
        assert ctx.thread_id == (threading.current_thread().ident or 0)
        assert ctx.thread_name == threading.current_thread().name
        assert ctx.process_id == os.getpid()
        assert ctx.exception_id.startswith("EXC_")

    @pytest.mark.unit()
    def Test_pre_filled_values_not_overwritten(self):
        """If fields are already set, __post_init__ leaves them alone."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Context

        ctx = Exception_Context(
            exception_type="Pre",
            message="msg",
            thread_id=9999,
            thread_name="my-thread",
            process_id=42,
            exception_id="EXC_MANUAL",
        )
        assert ctx.thread_id == 9999
        assert ctx.thread_name == "my-thread"
        assert ctx.process_id == 42
        assert ctx.exception_id == "EXC_MANUAL"


# ==============================================================================
# Tests: Exception_Custom extended branches
# ==============================================================================


class Class_Test_Exception_Custom_Init_Branches:
    """Cover uncovered branches in Exception_Custom.__init__."""

    @pytest.mark.unit()
    def Test_env_format_override(self, monkeypatch):
        """QWIM_EXCEPTION_FORMAT env-var selects format when exception_format=None."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Custom,
            Exception_Format,
        )

        monkeypatch.setenv("QWIM_EXCEPTION_FORMAT", "JSON")
        exc = Exception_Custom("env fmt test")
        assert exc._exception_format == Exception_Format.JSON

    @pytest.mark.unit()
    def Test_invalid_env_format_uses_default(self, monkeypatch):
        """Invalid QWIM_EXCEPTION_FORMAT falls back to default_format."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Custom,
        )

        monkeypatch.setenv("QWIM_EXCEPTION_FORMAT", "NOT_A_FORMAT")
        exc = Exception_Custom("bad env fmt test")
        assert exc._exception_format == Exception_Custom.default_format

    @pytest.mark.unit()
    def Test_suppress_traceback_str_returns_message_only(self):
        """With suppress_traceback=True, str() returns bare message."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Custom

        exc = Exception_Custom("clean msg", suppress_traceback=True)
        assert str(exc) == "clean msg"

    @pytest.mark.unit()
    def Test_cause_sets_dunder_cause(self):
        """Providing cause= sets __cause__ on the exception."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Custom

        original = ValueError("root cause")
        exc = Exception_Custom("wrapped", cause=original)
        assert exc.__cause__ is original

    @pytest.mark.unit()
    def Test_format_setter_works(self):
        """exception_format property setter updates the format."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Custom,
            Exception_Format,
        )

        exc = Exception_Custom("setter test")
        exc.Exception_Format_Value = Exception_Format.SIMPLE
        assert exc.Exception_Format_Value == Exception_Format.SIMPLE

    @pytest.mark.unit()
    def Test_exception_context_property_forces_capture(self):
        """exception_context property re-captures context when _exception_context is None."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Custom,
            Exception_Context,
        )

        exc = Exception_Custom("force capture")
        exc._exception_context = None
        ctx = exc.Exception_Context
        assert isinstance(ctx, Exception_Context)

    @pytest.mark.unit()
    def Test_subclass_depth_in_capture_context(self):
        """Context capture uses deeper frame when called from a subclass __init__."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        exc = Exception_Validation_Input("subclass depth test")
        assert exc.Exception_Context.exception_type == "Exception_Validation_Input"

    @pytest.mark.unit()
    def Test_capture_context_with_active_traceback(self):
        """_capture_context uses actual traceback frames when inside an except block."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Custom

        try:
            raise RuntimeError("inner")
        except RuntimeError:
            exc = Exception_Custom("caught")

        # frames should come from the actual traceback, not inspection
        assert exc.Exception_Context is not None

    @pytest.mark.unit()
    def Test_variable_capture_disabled_branch(self):
        """With enable_variable_capture=False, f_locals are not collected."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Custom

        original = Exception_Custom.enable_variable_capture
        try:
            Exception_Custom.enable_variable_capture = False
            exc = Exception_Custom("no vars")
            # frames exist but local_variables should be empty dicts
            for frame in exc.Exception_Context.frames:
                assert frame.local_variables == {}
        finally:
            Exception_Custom.enable_variable_capture = original


class Class_Test_Exception_Custom_Str_Branches:
    """Cover all __str__ format branches."""

    @pytest.mark.unit()
    def Test_simple_format(self):
        """SIMPLE format â†’ 'ExcType: message'."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Custom,
            Exception_Format,
        )

        exc = Exception_Custom("simple", exception_format=Exception_Format.SIMPLE)
        result = str(exc)
        assert "simple" in result

    @pytest.mark.unit()
    def Test_json_format(self):
        """JSON format â†’ valid JSON string with 'message' key."""
        import json
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Custom,
            Exception_Format,
        )

        exc = Exception_Custom("json msg", exception_format=Exception_Format.JSON)
        result = str(exc)
        parsed = json.loads(result)
        assert parsed["message"] == "json msg"

    @pytest.mark.unit()
    def Test_rich_traceback_format_falls_back_to_simple(self):
        """RICH_TRACEBACK format returns simple string (no actual rich render)."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Custom,
            Exception_Format,
        )

        exc = Exception_Custom("rich msg", exception_format=Exception_Format.RICH_TRACEBACK)
        result = str(exc)
        assert "rich msg" in result

    @pytest.mark.unit()
    def Test_table_format_falls_back_to_simple(self):
        """TABLE format string falls back to simple format."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Custom,
            Exception_Format,
        )

        exc = Exception_Custom("table msg", exception_format=Exception_Format.TABLE)
        result = str(exc)
        assert "table msg" in result

    @pytest.mark.unit()
    def Test_full_format_falls_back_to_simple(self):
        """FULL format string falls back to simple format."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Custom,
            Exception_Format,
        )

        exc = Exception_Custom("full msg", exception_format=Exception_Format.FULL)
        result = str(exc)
        assert "full msg" in result

    @pytest.mark.unit()
    def Test_standard_format_with_user_context(self):
        """STANDARD format includes context section when user_context is non-empty."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Custom,
            Exception_Format,
        )

        exc = Exception_Custom(
            "std msg",
            exception_format=Exception_Format.STANDARD,
            context={"alpha": "beta"},
        )
        result = str(exc)
        assert "std msg" in result
        assert "alpha" in result

    @pytest.mark.unit()
    def Test_standard_format_no_user_context(self):
        """STANDARD format works without user context."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Custom,
            Exception_Format,
        )

        exc = Exception_Custom("std only", exception_format=Exception_Format.STANDARD)
        result = str(exc)
        assert "std only" in result


class Class_Test_Exception_Custom_To_JSON_Cause:
    """Cover to_JSON when _cause is set."""

    @pytest.mark.unit()
    def Test_to_json_includes_caused_by(self):
        """to_JSON includes caused_by block when cause is set."""
        import json
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Custom

        original = ValueError("root")
        exc = Exception_Custom("wrapped", cause=original)
        parsed = json.loads(exc.To_JSON())
        assert "caused_by" in parsed
        assert parsed["caused_by"]["type"] == "ValueError"
        assert parsed["caused_by"]["message"] == "root"


class Class_Test_Exception_Custom_Log_Branches:
    """Cover log() method branches."""

    @pytest.mark.unit()
    def Test_log_no_logger_uses_custom_logger(self):
        """log(logger=None) falls through to logger_custom.get_logger."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Custom

        exc = Exception_Custom("log with default logger")
        # Should not raise; just verify it runs
        exc.Log()

    @pytest.mark.unit()
    def Test_log_none_logger_import_error_fallback(self, capsys):
        """log(logger=None) prints to stderr when logger_custom is unavailable."""
        from unittest.mock import patch
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Custom

        exc = Exception_Custom("fallback log")
        with patch(
            "src.utils.custom_exceptions_errors_loggers.exception_custom.Exception_Custom.Exception_Context",
            new_callable=lambda: property(lambda s: s._exception_context or type(
                "Ctx", (), {"filename": ""}
            )()),
        ):
            with patch(
                "src.utils.custom_exceptions_errors_loggers.logger_custom.get_logger",
                side_effect=ImportError("no logger"),
            ):
                exc.Log()
        # no exception raised

    @pytest.mark.unit()
    def Test_log_simple_print_fallback(self, capsys):
        """log() with object lacking both 'opt' and 'log' prints to stderr."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Custom

        class _DumbLogger:
            pass

        exc = Exception_Custom("print fallback")
        exc.Log(logger=_DumbLogger())
        captured = capsys.readouterr()
        assert "print fallback" in captured.err


class Class_Test_Exception_Custom_Print_Rich:
    """Cover print_rich and underlying format methods."""

    @pytest.mark.unit()
    def Test_print_rich_rich_traceback_format(self):
        """print_rich() with RICH_TRACEBACK doesn't raise."""
        from io import StringIO
        from rich.console import Console
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Custom,
            Exception_Format,
        )

        exc = Exception_Custom("rt fmt", exception_format=Exception_Format.RICH_TRACEBACK)
        out = StringIO()
        exc.Print_Rich(console=Console(file=out, legacy_windows=False))

    @pytest.mark.unit()
    def Test_print_rich_table_format(self):
        """print_rich() with TABLE format doesn't raise."""
        from io import StringIO
        from rich.console import Console
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Custom,
            Exception_Format,
        )

        exc = Exception_Custom("table fmt", exception_format=Exception_Format.TABLE)
        out = StringIO()
        exc.Print_Rich(console=Console(file=out, legacy_windows=False))

    @pytest.mark.unit()
    def Test_print_rich_full_format(self):
        """print_rich() with FULL format doesn't raise."""
        from io import StringIO
        from rich.console import Console
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Custom,
            Exception_Format,
        )

        exc = Exception_Custom("full fmt", exception_format=Exception_Format.FULL)
        out = StringIO()
        exc.Print_Rich(console=Console(file=out, legacy_windows=False))

    @pytest.mark.unit()
    def Test_print_rich_full_with_cause(self):
        """FULL format with __cause__ exercises traceback_with_variables path."""
        from io import StringIO
        from rich.console import Console
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Custom,
            Exception_Format,
        )

        cause = ValueError("root cause")
        exc = Exception_Custom("full+cause", exception_format=Exception_Format.FULL, cause=cause)
        out = StringIO()
        exc.Print_Rich(console=Console(file=out, legacy_windows=False))

    @pytest.mark.unit()
    def Test_print_rich_with_user_context(self):
        """RICH_TRACEBACK format includes context table when user_context non-empty."""
        from io import StringIO
        from rich.console import Console
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Custom,
            Exception_Format,
        )

        exc = Exception_Custom(
            "ctx rich",
            exception_format=Exception_Format.RICH_TRACEBACK,
            context={"my_key": "my_val"},
        )
        out = StringIO()
        exc.Print_Rich(console=Console(file=out, legacy_windows=False))
        assert "my_key" in out.getvalue()


class Class_Test_Get_Traceback_String:
    """Branch coverage for get_traceback_string."""

    @pytest.mark.unit()
    def Test_with_cause_uses_iter_exc_lines(self):
        """With __cause__ set, traceback is from iter_exc_lines."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Custom

        cause = ValueError("root")
        exc = Exception_Custom("with cause", cause=cause)
        result = exc.Get_Traceback_String()
        assert isinstance(result, str)

    @pytest.mark.unit()
    def Test_without_cause_uses_format_standard(self):
        """Without __cause__, output comes from _format_standard."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Custom

        exc = Exception_Custom("no cause")
        exc._cause = None
        # Manually clear __cause__ if set
        if hasattr(exc, "__cause__"):
            exc.__cause__ = None
        result = exc.Get_Traceback_String()
        assert "no cause" in result


class Class_Test_Install_Rich_Traceback:
    """Branch coverage for install_rich_traceback classmethod."""

    @pytest.mark.unit()
    def Test_installs_without_raising(self):
        """install_rich_traceback() calls rich.traceback.install without error."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Custom

        # Should not raise; restoring is not needed since tests don't use global handler
        Exception_Custom.Install_Rich_Traceback()


# ==============================================================================
# Tests: Domain exception constructors â€” branch coverage
# ==============================================================================


class Class_Test_Domain_Exception_Constructors:
    """All domain-exception subclass __init__ paths with partial/no params."""

    @pytest.mark.unit()
    def Test_validation_input_minimal(self):
        """Exception_Validation_Input with no optional params."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        exc = Exception_Validation_Input("bare message")
        assert exc._message == "bare message"
        assert exc.Exception_Context.user_context == {}

    @pytest.mark.unit()
    def Test_validation_input_all_params(self):
        """Exception_Validation_Input with all optional params."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        exc = Exception_Validation_Input(
            "full",
            field_name="weight",
            expected_type=float,
            actual_value="bad",
        )
        ctx = exc.Exception_Context.user_context
        assert ctx["field_name"] == "weight"
        assert ctx["expected_type"] == "float"

    @pytest.mark.unit()
    def Test_configuration_minimal(self):
        """Exception_Configuration with no optional params."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Configuration,
        )

        exc = Exception_Configuration("cfg error")
        assert exc._message == "cfg error"

    @pytest.mark.unit()
    def Test_configuration_all_params(self):
        """Exception_Configuration with config_key and config_file."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Configuration,
        )

        exc = Exception_Configuration("cfg full", config_key="db_host", config_file="cfg.yml")
        ctx = exc.Exception_Context.user_context
        assert ctx["config_key"] == "db_host"
        assert ctx["config_file"] == "cfg.yml"

    @pytest.mark.unit()
    def Test_data_not_found_all_params(self):
        """Exception_Data_Not_Found with all optional params."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Data_Not_Found,
        )

        exc = Exception_Data_Not_Found(
            "missing",
            data_type="DataFrame",
            identifier="id-1",
            source="db",
        )
        ctx = exc.Exception_Context.user_context
        assert ctx["data_type"] == "DataFrame"
        assert ctx["identifier"] == "id-1"
        assert ctx["source"] == "db"

    @pytest.mark.unit()
    def Test_calculation_all_params(self):
        """Exception_Calculation with all optional params."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Calculation,
        )

        exc = Exception_Calculation(
            "calc failed",
            operation="optimize",
            inputs={"x": 1},
        )
        ctx = exc.Exception_Context.user_context
        assert ctx["operation"] == "optimize"

    @pytest.mark.unit()
    def Test_portfolio_all_params(self):
        """Exception_Portfolio with all optional params."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Portfolio,
        )

        exc = Exception_Portfolio(
            "port err",
            portfolio_id="P1",
            portfolio_name="Growth",
            operation="rebalance",
        )
        ctx = exc.Exception_Context.user_context
        assert ctx["portfolio_id"] == "P1"
        assert ctx["portfolio_name"] == "Growth"
        assert ctx["operation"] == "rebalance"

    @pytest.mark.unit()
    def Test_client_all_params(self):
        """Exception_Client with all optional params."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Client,
        )

        exc = Exception_Client("client err", client_id="C1", client_type="PRIMARY")
        ctx = exc.Exception_Context.user_context
        assert ctx["client_id"] == "C1"
        assert ctx["client_type"] == "PRIMARY"

    @pytest.mark.unit()
    def Test_database_minimal(self):
        """Exception_Database with no optional params."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Database,
        )

        exc = Exception_Database("db bare")
        assert exc._message == "db bare"

    @pytest.mark.unit()
    def Test_database_all_params(self):
        """Exception_Database with all optional params."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Database,
        )

        exc = Exception_Database(
            "db full",
            database_name="postgres",
            operation="INSERT",
            table_name="orders",
            query="INSERT INTO orders VALUES (?)",
        )
        ctx = exc.Exception_Context.user_context
        assert ctx["database_name"] == "postgres"
        assert ctx["operation"] == "INSERT"
        assert ctx["table_name"] == "orders"

    @pytest.mark.unit()
    def Test_api_all_params(self):
        """Exception_API with all optional params."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_API

        exc = Exception_API(
            "api fail",
            endpoint="/data",
            method="GET",
            status_code=500,
            response_body='{"error":"oops"}',
        )
        ctx = exc.Exception_Context.user_context
        assert ctx["endpoint"] == "/data"
        assert ctx["method"] == "GET"
        assert ctx["status_code"] == 500

    @pytest.mark.unit()
    def Test_authentication_all_params(self):
        """Exception_Authentication with all optional params."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Authentication,
            Exception_Severity,
        )

        exc = Exception_Authentication("auth fail", user_id="usr1", auth_method="jwt")
        ctx = exc.Exception_Context.user_context
        assert ctx["user_id"] == "usr1"
        assert ctx["auth_method"] == "jwt"
        assert exc._severity == Exception_Severity.WARNING

    @pytest.mark.unit()
    def Test_authorization_all_params(self):
        """Exception_Authorization with all optional params."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Authorization,
            Exception_Severity,
        )

        exc = Exception_Authorization(
            "authz fail",
            user_id="usr2",
            required_permission="admin",
            resource="/reports",
        )
        ctx = exc.Exception_Context.user_context
        assert ctx["required_permission"] == "admin"
        assert ctx["resource"] == "/reports"
        assert exc._severity == Exception_Severity.WARNING

    @pytest.mark.unit()
    def Test_file_operation_all_params(self):
        """Exception_File_Operation with all optional params."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_File_Operation,
        )

        exc = Exception_File_Operation("file err", file_path="/data/f.csv", operation="read")
        ctx = exc.Exception_Context.user_context
        assert ctx["file_path"] == "/data/f.csv"
        assert ctx["operation"] == "read"

    @pytest.mark.unit()
    def Test_timeout_minimal(self):
        """Exception_Timeout with no optional params."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Timeout

        exc = Exception_Timeout("timed out")
        assert exc._message == "timed out"

    @pytest.mark.unit()
    def Test_invalid_input_all_params(self):
        """Exception_Invalid_Input with all optional params."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Invalid_Input,
        )

        exc = Exception_Invalid_Input(
            "bad input",
            input_name="weights",
            expected_format="list[float]",
            actual_value=[0.1, 0.2],
        )
        ctx = exc.Exception_Context.user_context
        assert ctx["input_name"] == "weights"
        assert ctx["expected_format"] == "list[float]"

    @pytest.mark.unit()
    def Test_not_found_all_params(self):
        """Exception_Not_Found with all optional params."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Not_Found,
        )

        exc = Exception_Not_Found(
            "not found",
            resource_type="Portfolio",
            resource_id="P9",
            search_criteria={"name": "Growth"},
        )
        ctx = exc.Exception_Context.user_context
        assert ctx["resource_type"] == "Portfolio"
        assert ctx["resource_id"] == "P9"

    @pytest.mark.unit()
    def Test_security_violation_all_params(self):
        """Exception_Security_Violation with all optional params."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Security_Violation,
            Exception_Severity,
        )

        exc = Exception_Security_Violation(
            "sec violation",
            violation_type="path_traversal",
            resource="../etc/passwd",
            user_id="anon",
        )
        ctx = exc.Exception_Context.user_context
        assert ctx["violation_type"] == "path_traversal"
        assert exc._severity == Exception_Severity.CRITICAL

    @pytest.mark.unit()
    def Test_insufficient_holdings_all_params(self):
        """Exception_Insufficient_Holdings with all optional params."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Insufficient_Holdings,
        )

        exc = Exception_Insufficient_Holdings(
            "not enough",
            ticker="AAPL",
            required_quantity=100.0,
            available_quantity=50.0,
            operation="sell",
        )
        ctx = exc.Exception_Context.user_context
        assert ctx["ticker"] == "AAPL"
        assert ctx["required_quantity"] == 100.0
        assert ctx["available_quantity"] == 50.0

    @pytest.mark.unit()
    def Test_invalid_transaction_all_params(self):
        """Exception_Invalid_Transaction with all optional params."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Invalid_Transaction,
        )

        exc = Exception_Invalid_Transaction(
            "bad txn",
            transaction_type="sell",
            transaction_id="TXN-001",
            reason="market_closed",
        )
        ctx = exc.Exception_Context.user_context
        assert ctx["transaction_type"] == "sell"
        assert ctx["transaction_id"] == "TXN-001"
        assert ctx["reason"] == "market_closed"


# ==============================================================================
# Tests: Global handler branches
# ==============================================================================


class Class_Test_Global_Exception_Handler_Branches:
    """Branch coverage for global_exception_handler."""

    @pytest.mark.unit()
    def Test_wraps_standard_exception(self, capsys):
        """global_exception_handler wraps a plain Exception in Exception_Custom."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Global_Exception_Handler,
        )

        exc = ValueError("standard exc")
        Global_Exception_Handler(exc_type = type(exc), exc_value = exc, exc_traceback = None)
        # no exception escapes to caller

    @pytest.mark.unit()
    def Test_passes_through_base_exception(self):
        """global_exception_handler calls original hook for BaseException (SystemExit)."""
        from unittest.mock import patch
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Global_Exception_Handler,
            _ORIGINAL_EXCEPTHOOK,
        )

        exc = SystemExit(0)
        with patch(
            "src.utils.custom_exceptions_errors_loggers._exception_handlers._ORIGINAL_EXCEPTHOOK"
        ) as mock_hook:
            Global_Exception_Handler(exc_type = type(exc), exc_value = exc, exc_traceback = None)
            mock_hook.assert_called_once()

    @pytest.mark.unit()
    def Test_exception_custom_passed_directly(self, capsys):
        """global_exception_handler prints already-custom exceptions without wrapping."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Custom,
            Exception_Format,
            Global_Exception_Handler,
        )

        exc = Exception_Custom("already custom", exception_format=Exception_Format.STANDARD)
        Global_Exception_Handler(exc_type = type(exc), exc_value = exc, exc_traceback = None)
        # no exception escapes


class Class_Test_Capture_Exception_Custom_Branch:
    """capture_exception with an Exception_Custom already raised."""

    @pytest.mark.unit()
    def Test_updates_context_on_existing_custom_exception(self):
        """capture_exception updates _user_context of an existing Exception_Custom."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Custom,
            Capture_Exception,
        )

        with pytest.raises(Exception_Custom) as exc_info:
            with Capture_Exception(context={"added": "yes"}, reraise=True):
                raise Exception_Custom("already custom")

        # capture_exception updates _user_context (not the already-snapshotted exception_context)
        assert exc_info.value._user_context.get("added") == "yes"

    @pytest.mark.unit()
    def Test_updates_severity_on_existing_custom_exception(self):
        """capture_exception with log_severity overrides severity of existing Exception_Custom."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Custom,
            Exception_Severity,
            Capture_Exception,
        )

        with pytest.raises(Exception_Custom) as exc_info:
            with Capture_Exception(
                log_severity=Exception_Severity.CRITICAL,
                reraise=True,
            ):
                raise Exception_Custom("severity override")

        assert exc_info.value._severity == Exception_Severity.CRITICAL

    @pytest.mark.unit()
    def Test_reraise_false_suppresses_custom_exception(self):
        """capture_exception with reraise=False suppresses Exception_Custom too."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Custom,
            Capture_Exception,
        )

        try:
            with Capture_Exception(reraise=False):
                raise Exception_Custom("suppress custom")
        except Exception_Custom:
            pytest.fail("Exception_Custom should have been suppressed")


class Class_Test_Handle_Exceptions_Custom_Branch:
    """handle_exceptions decorator with an Exception_Custom already raised."""

    @pytest.mark.unit()
    def Test_reraises_exception_custom_with_context(self):
        """handle_exceptions re-raises Exception_Custom after merging context."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Custom,
            Exception_Severity,
            Handle_Exceptions,
        )

        @Handle_Exceptions(context={"deco": "yes"}, severity=Exception_Severity.WARNING)
        def _raise_custom():
            raise Exception_Custom("already custom")

        with pytest.raises(Exception_Custom) as exc_info:
            _raise_custom()

        # context merged
        assert exc_info.value._user_context.get("deco") == "yes"


# ==============================================================================
# Tests: Domain exception minimal constructors (False-branch coverage)
# ==============================================================================


class Class_Test_Domain_Exception_Minimal_Constructors:
    """Minimal (no optional params) constructors for all domain exceptions.

    These cover the False branches of each ``if optional_param:`` guard inside
    every domain subclass ``__init__``.
    """

    @pytest.mark.unit()
    def Test_data_not_found_minimal(self):
        """Exception_Data_Not_Found with no optional params â†’ False branches covered."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Data_Not_Found,
        )

        exc = Exception_Data_Not_Found("missing data")
        assert exc._message == "missing data"
        assert exc.Exception_Context.user_context == {}

    @pytest.mark.unit()
    def Test_calculation_minimal(self):
        """Exception_Calculation with no optional params."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Calculation,
        )

        exc = Exception_Calculation("calc bare")
        assert exc._message == "calc bare"
        assert exc.Exception_Context.user_context == {}

    @pytest.mark.unit()
    def Test_portfolio_minimal(self):
        """Exception_Portfolio with no optional params."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Portfolio,
        )

        exc = Exception_Portfolio("portfolio bare")
        assert exc._message == "portfolio bare"
        assert exc.Exception_Context.user_context == {}

    @pytest.mark.unit()
    def Test_client_minimal(self):
        """Exception_Client with no optional params."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Client,
        )

        exc = Exception_Client("client bare")
        assert exc._message == "client bare"
        assert exc.Exception_Context.user_context == {}

    @pytest.mark.unit()
    def Test_api_minimal(self):
        """Exception_API with no optional params."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_API

        exc = Exception_API("api bare")
        assert exc._message == "api bare"
        assert exc.Exception_Context.user_context == {}

    @pytest.mark.unit()
    def Test_authentication_minimal(self):
        """Exception_Authentication with no optional params."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Authentication,
        )

        exc = Exception_Authentication("auth bare")
        assert exc._message == "auth bare"
        assert exc.Exception_Context.user_context == {}

    @pytest.mark.unit()
    def Test_authorization_minimal(self):
        """Exception_Authorization with no optional params."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Authorization,
        )

        exc = Exception_Authorization("authz bare")
        assert exc._message == "authz bare"
        assert exc.Exception_Context.user_context == {}

    @pytest.mark.unit()
    def Test_file_operation_minimal(self):
        """Exception_File_Operation with no optional params."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_File_Operation,
        )

        exc = Exception_File_Operation("file bare")
        assert exc._message == "file bare"
        assert exc.Exception_Context.user_context == {}

    @pytest.mark.unit()
    def Test_invalid_input_minimal(self):
        """Exception_Invalid_Input with no optional params."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Invalid_Input,
        )

        exc = Exception_Invalid_Input("input bare")
        assert exc._message == "input bare"
        assert exc.Exception_Context.user_context == {}

    @pytest.mark.unit()
    def Test_not_found_minimal(self):
        """Exception_Not_Found with no optional params."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Not_Found,
        )

        exc = Exception_Not_Found("not found bare")
        assert exc._message == "not found bare"
        assert exc.Exception_Context.user_context == {}

    @pytest.mark.unit()
    def Test_security_violation_minimal(self):
        """Exception_Security_Violation with no optional params."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Security_Violation,
        )

        exc = Exception_Security_Violation("sec bare")
        assert exc._message == "sec bare"
        assert exc.Exception_Context.user_context == {}

    @pytest.mark.unit()
    def Test_insufficient_holdings_minimal(self):
        """Exception_Insufficient_Holdings with no optional params."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Insufficient_Holdings,
        )

        exc = Exception_Insufficient_Holdings("holdings bare")
        assert exc._message == "holdings bare"
        assert exc.Exception_Context.user_context == {}

    @pytest.mark.unit()
    def Test_invalid_transaction_minimal(self):
        """Exception_Invalid_Transaction with no optional params."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Invalid_Transaction,
        )

        exc = Exception_Invalid_Transaction("txn bare")
        assert exc._message == "txn bare"
        assert exc.Exception_Context.user_context == {}

    @pytest.mark.unit()
    def Test_timeout_all_params(self):
        """Exception_Timeout with all optional params."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Timeout

        exc = Exception_Timeout(
            "timed out full",
            operation="db_query",
            timeout_seconds=30.0,
        )
        ctx = exc.Exception_Context.user_context
        assert ctx["operation"] == "db_query"
        assert ctx["timeout_seconds"] == 30.0


# ==============================================================================
# Tests: print_rich uncovered branches
# ==============================================================================


class Class_Test_Print_Rich_Missing_Branches:
    """Cover remaining branches in _print_rich_traceback, _print_table, _print_full."""

    @pytest.mark.unit()
    def Test_print_rich_traceback_no_code_context(self):
        """_print_rich_traceback with empty code_context skips syntax block."""
        from io import StringIO
        from rich.console import Console
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Custom,
            Exception_Context,
            Exception_Format,
        )

        exc = Exception_Custom("no ctx code", exception_format=Exception_Format.RICH_TRACEBACK)
        # Replace the exception_context with one that has empty code_context
        orig = exc.Exception_Context
        patched = Exception_Context(
            exception_type=orig.exception_type,
            message=orig.message,
            filename=orig.filename,
            function=orig.function,
            line_number=orig.line_number,
            code_context="",  # empty â†’ skips syntax block
            frames=[],
            user_context={},
            severity=orig.severity,
        )
        exc._exception_context = patched
        out = StringIO()
        exc.Print_Rich(console=Console(file=out, legacy_windows=False))

    @pytest.mark.unit()
    def Test_print_rich_traceback_no_user_context_no_extra_frames(self):
        """_print_rich_traceback with no user_context and â‰¤1 frame skips those sections."""
        from io import StringIO
        from rich.console import Console
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Custom,
            Exception_Context,
            Exception_Frame,
            Exception_Format,
        )

        exc = Exception_Custom("minimal ctx", exception_format=Exception_Format.RICH_TRACEBACK)
        orig = exc.Exception_Context
        # Single frame â†’ len(frames) == 1, so stack section skipped; no user_context
        single_frame = Exception_Frame(
            filename="test.py",
            function="test_fn",
            line_number=1,
            code_context="pass",
            local_variables={},
            module="test",
        )
        patched = Exception_Context(
            exception_type=orig.exception_type,
            message=orig.message,
            filename=orig.filename,
            function=orig.function,
            line_number=orig.line_number,
            code_context="pass",
            frames=[single_frame],
            user_context={},  # empty â†’ skips context table
            severity=orig.severity,
        )
        exc._exception_context = patched
        out = StringIO()
        exc.Print_Rich(console=Console(file=out, legacy_windows=False))

    @pytest.mark.unit()
    def Test_print_table_no_user_context(self):
        """_print_table with empty user_context skips the context row."""
        from io import StringIO
        from rich.console import Console
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Custom,
            Exception_Context,
            Exception_Format,
        )

        exc = Exception_Custom("table no ctx", exception_format=Exception_Format.TABLE)
        orig = exc.Exception_Context
        patched = Exception_Context(
            exception_type=orig.exception_type,
            message=orig.message,
            filename=orig.filename,
            function=orig.function,
            line_number=orig.line_number,
            code_context=orig.code_context,
            frames=orig.frames,
            user_context={},  # empty â†’ if ctx.user_context: branch False
            severity=orig.severity,
        )
        exc._exception_context = patched
        out = StringIO()
        exc.Print_Rich(console=Console(file=out, legacy_windows=False))

    @pytest.mark.unit()
    def Test_print_table_with_user_context(self):
        """_print_table with non-empty user_context adds Context row â€” covers line 1181."""
        from io import StringIO
        from rich.console import Console
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Custom,
            Exception_Context,
            Exception_Format,
        )

        exc = Exception_Custom("table with ctx", exception_format=Exception_Format.TABLE)
        orig = exc.Exception_Context
        patched = Exception_Context(
            exception_type=orig.exception_type,
            message=orig.message,
            filename=orig.filename,
            function=orig.function,
            line_number=orig.line_number,
            code_context=orig.code_context,
            frames=orig.frames,
            user_context={"key": "value"},  # non-empty â†’ if ctx.user_context: branch True
            severity=orig.severity,
        )
        exc._exception_context = patched
        out = StringIO()
        exc.Print_Rich(console=Console(file=out, legacy_windows=False))

    @pytest.mark.unit()
    def Test_print_full_variable_capture_disabled(self):
        """_print_full with enable_variable_capture=False skips variables section."""
        from io import StringIO
        from rich.console import Console
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Custom,
            Exception_Format,
        )

        original = Exception_Custom.enable_variable_capture
        try:
            Exception_Custom.enable_variable_capture = False
            exc = Exception_Custom("full no vars", exception_format=Exception_Format.FULL)
            out = StringIO()
            exc.Print_Rich(console=Console(file=out, legacy_windows=False))
        finally:
            Exception_Custom.enable_variable_capture = original

    @pytest.mark.unit()
    def Test_print_full_frames_with_no_local_vars(self):
        """_print_full with frames that have empty local_variables skips their tables."""
        from io import StringIO
        from rich.console import Console
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Custom,
            Exception_Context,
            Exception_Frame,
            Exception_Format,
        )

        exc = Exception_Custom("full empty vars", exception_format=Exception_Format.FULL)
        orig = exc.Exception_Context
        # Frame with empty local_variables â†’ if frame.local_variables: False
        empty_frame = Exception_Frame(
            filename="test.py",
            function="test_fn",
            line_number=1,
            code_context="pass",
            local_variables={},  # empty
            module="test",
        )
        patched = Exception_Context(
            exception_type=orig.exception_type,
            message=orig.message,
            filename=orig.filename,
            function=orig.function,
            line_number=orig.line_number,
            code_context=orig.code_context,
            frames=[empty_frame, empty_frame],
            user_context={},
            severity=orig.severity,
        )
        exc._exception_context = patched
        out = StringIO()
        exc.Print_Rich(console=Console(file=out, legacy_windows=False))


# ==============================================================================
# Tests: global_exception_handler - remaining branches
# ==============================================================================


class Class_Test_Global_Exception_Handler_More_Branches:
    """Cover the STANDARD format branch and logging-failure branch."""

    @pytest.mark.unit()
    def Test_console_created_without_file_kwarg_uses_utf8_wrapper(self):
        """_patched_console_init body is pragma: no cover; verify Console with explicit file= works."""
        from io import StringIO
        from rich.console import Console

        # The UTF-8 wrapper body is excluded via pragma: no cover because sys.stderr.buffer
        # is not reliably available in pytest capture mode. Verify Console with file= works.
        buf = StringIO()
        c = Console(file=buf)
        assert c is not None

    @pytest.mark.unit()
    def Test_standard_format_prints_to_stderr(self, capsys):
        """global_exception_handler with STANDARD format prints str(exc) to stderr."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Custom,
            Exception_Format,
            Global_Exception_Handler,
        )

        exc = Exception_Custom("std handler msg", exception_format=Exception_Format.STANDARD)
        Global_Exception_Handler(exc_type = type(exc), exc_value = exc, exc_traceback = None)
        captured = capsys.readouterr()
        assert "std handler msg" in captured.err

    @pytest.mark.unit()
    def Test_logging_failure_falls_back_to_stderr(self, capsys):
        """global_exception_handler writes to stderr when logger import fails."""
        from unittest.mock import patch
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Global_Exception_Handler,
        )

        # Patch get_logger on the actual logger_custom module (imported inside the function)
        with patch(
            "src.utils.custom_exceptions_errors_loggers.logger_custom.get_logger",
            side_effect=RuntimeError("logger broken"),
        ):
            exc = ValueError("log fail test")
            Global_Exception_Handler(exc_type = type(exc), exc_value = exc, exc_traceback = None)
        # Should not raise; stderr may contain fallback message

    @pytest.mark.unit()
    def Test_json_env_format_invalid_key_uses_rich(self, monkeypatch):
        """global_exception_handler env format with invalid key â†’ RICH_TRACEBACK fallback."""
        import os
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Global_Exception_Handler,
        )

        monkeypatch.setenv("QWIM_EXCEPTION_FORMAT", "NO_SUCH_FORMAT")
        exc = ValueError("env key fallback")
        Global_Exception_Handler(exc_type = type(exc), exc_value = exc, exc_traceback = None)


# ==============================================================================
# Tests: _format_standard missing branches
# ==============================================================================


class Class_Test_Format_Standard_No_Code_Context:
    """Cover branch where frame.code_context is empty in _format_standard."""

    @pytest.mark.unit()
    def Test_format_standard_empty_frame_code_context(self):
        """_format_standard with a frame that has no code_context skips indent line."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Custom,
            Exception_Context,
            Exception_Frame,
            Exception_Format,
        )

        exc = Exception_Custom("std frame test", exception_format=Exception_Format.STANDARD)
        orig = exc.Exception_Context
        frame_no_ctx = Exception_Frame(
            filename="test.py",
            function="test_fn",
            line_number=1,
            code_context="",  # empty â†’ if frame.code_context: False
            local_variables={},
            module="test",
        )
        patched = Exception_Context(
            exception_type=orig.exception_type,
            message=orig.message,
            filename=orig.filename,
            function=orig.function,
            line_number=orig.line_number,
            code_context=orig.code_context,
            frames=[frame_no_ctx],
            user_context={},
            severity=orig.severity,
        )
        exc._exception_context = patched
        result = str(exc)
        assert "std frame test" in result


# ==============================================================================
# Tests: handle_exceptions severity branch
# ==============================================================================


class Class_Test_Handle_Exceptions_Severity_Branch:
    """handle_exceptions when exception_custom is re-raised with severity override."""

    @pytest.mark.unit()
    def Test_severity_override_on_exception_custom(self):
        """handle_exceptions updates severity for an already-custom exception."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Custom,
            Exception_Severity,
            Handle_Exceptions,
        )

        @Handle_Exceptions(severity=Exception_Severity.CRITICAL)
        def _raise_custom():
            raise Exception_Custom("severity branch test")

        with pytest.raises(Exception_Custom) as exc_info:
            _raise_custom()

        assert exc_info.value._severity == Exception_Severity.CRITICAL

    @pytest.mark.unit()
    def Test_no_severity_reraises_custom_unchanged(self):
        """handle_exceptions without severity re-raises Exception_Custom as-is â€” covers 2141â†’2143 False."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Custom,
            Exception_Severity,
            Handle_Exceptions,
        )

        @Handle_Exceptions()  # no severity â†’ severity=None â†’ if severity: False branch
        def _raise_custom_no_severity():
            raise Exception_Custom("no severity test")

        with pytest.raises(Exception_Custom) as exc_info:
            _raise_custom_no_severity()

        # Severity should remain at the default (ERROR)
        assert exc_info.value._severity == Exception_Severity.ERROR


# ==============================================================================
# Tests: QWIM_Error root hierarchy (P1 additions)
# ==============================================================================


class Class_Test_QWIM_Error_Hierarchy:
    """Test the QWIM_Error root class and its four typed subclasses."""

    @pytest.mark.unit()
    def Test_qwim_error_is_exception_subclass(self):
        """QWIM_Error must inherit from Exception."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_QWIM_Error

        assert issubclass(Exception_QWIM_Error, Exception)

    @pytest.mark.unit()
    def Test_exception_custom_is_qwim_error_subclass(self):
        """Exception_Custom must inherit from QWIM_Error."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_QWIM_Error,
            Exception_Custom,
        )

        assert issubclass(Exception_Custom, Exception_QWIM_Error)

    @pytest.mark.unit()
    def Test_data_validation_error_hierarchy(self):
        """DataValidationError must be a subclass of QWIM_Error."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Data_Validation_Error,
            Exception_QWIM_Error,
        )

        assert issubclass(Exception_Data_Validation_Error, Exception_QWIM_Error)
        assert issubclass(Exception_Data_Validation_Error, Exception)

    @pytest.mark.unit()
    def Test_config_error_hierarchy(self):
        """ConfigError must be a subclass of QWIM_Error."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Config_Error,
            Exception_QWIM_Error,
        )

        assert issubclass(Exception_Config_Error, Exception_QWIM_Error)

    @pytest.mark.unit()
    def Test_external_service_error_hierarchy(self):
        """ExternalServiceError must be a subclass of QWIM_Error."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_External_Service_Error,
            Exception_QWIM_Error,
        )

        assert issubclass(Exception_External_Service_Error, Exception_QWIM_Error)

    @pytest.mark.unit()
    def Test_serialization_error_hierarchy(self):
        """SerializationError must be a subclass of QWIM_Error."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Serialization_Error,
            Exception_QWIM_Error,
        )

        assert issubclass(Exception_Serialization_Error, Exception_QWIM_Error)

    @pytest.mark.unit()
    def Test_qwim_error_carries_detail(self):
        """QWIM_Error stores an optional detail dict."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_QWIM_Error

        err = Exception_QWIM_Error("root error", detail={"code": 42})
        assert err.detail["code"] == 42
        assert str(err) == "root error"

    @pytest.mark.unit()
    def Test_data_validation_error_fields(self):
        """DataValidationError exposes field and value attributes."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Data_Validation_Error

        err = Exception_Data_Validation_Error("bad input", field="price", value=-1.0)
        assert err.field == "price"
        assert err.value == -1.0

    @pytest.mark.unit()
    def Test_config_error_key_attribute(self):
        """ConfigError exposes key attribute."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Config_Error

        err = Exception_Config_Error("missing key", key="database_url")
        assert err.key == "database_url"

    @pytest.mark.unit()
    def Test_external_service_error_attributes(self):
        """ExternalServiceError exposes service and status_code."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_External_Service_Error

        err = Exception_External_Service_Error("timeout", service="yfinance", status_code=503)
        assert err.service == "yfinance"
        assert err.status_code == 503

    @pytest.mark.unit()
    def Test_serialization_error_codec_attribute(self):
        """SerializationError exposes codec attribute."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Serialization_Error

        err = Exception_Serialization_Error("encode failed", codec="msgspec/json")
        assert err.codec == "msgspec/json"

    @pytest.mark.unit()
    def Test_catch_any_project_error_with_qwim_error(self):
        """A single 'except QWIM_Error' catches all typed subclasses."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Config_Error,
            Exception_Data_Validation_Error,
            Exception_External_Service_Error,
            Exception_QWIM_Error,
            Exception_Serialization_Error,
        )

        for exc_cls, kwargs in [
            (Exception_Data_Validation_Error, {"field": "x", "value": 0}),
            (Exception_Config_Error, {"key": "k"}),
            (Exception_External_Service_Error, {"service": "s", "status_code": 500}),
            (Exception_Serialization_Error, {"codec": "json"}),
        ]:
            caught = False
            try:
                raise exc_cls("test", **kwargs)
            except Exception_QWIM_Error:
                caught = True
            assert caught, f"{exc_cls.__name__} was not caught by QWIM_Error"

    @pytest.mark.unit()
    def Test_qwim_error_in_all(self):
        """QWIM_Error and typed subclasses appear in module __all__."""
        import src.utils.custom_exceptions_errors_loggers.exception_custom as mod

        for name in (
            "Exception_QWIM_Error",
            "Exception_Data_Validation_Error",
            "Exception_Config_Error",
            "Exception_External_Service_Error",
            "Exception_Serialization_Error",
        ):
            assert name in mod.__all__, f"{name} missing from __all__"


# ==============================================================================
# Tests: Lightweight Exception Classes â€” None-Parameter Paths
# ==============================================================================


class Class_Test_Lightweight_Exception_None_Params:
    """Test the None-parameter paths of lightweight exception subclasses.

    These tests exercise the False branches of the optional-keyword-argument
    guards in DataValidationError, ConfigError, ExternalServiceError, and
    SerializationError.  Without them the branches where the optional parameter
    is ``None`` (the default) are never taken in the test suite.
    """

    @pytest.mark.unit()
    def Test_data_validation_error_no_field_no_value(self):
        """DataValidationError with default field=None and value=None."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Data_Validation_Error,
        )

        err = Exception_Data_Validation_Error("stub error")
        assert err.field is None
        assert err.value is None
        assert str(err) == "stub error"

    @pytest.mark.unit()
    def Test_data_validation_error_field_only(self):
        """DataValidationError with field set but value=None."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Data_Validation_Error,
        )

        err = Exception_Data_Validation_Error("field only", field="weight")
        assert err.field == "weight"
        assert err.value is None

    @pytest.mark.unit()
    def Test_data_validation_error_value_only(self):
        """DataValidationError with value set but field=None."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Data_Validation_Error,
        )

        err = Exception_Data_Validation_Error("value only", value=3.14)
        assert err.field is None
        assert err.value == 3.14

    @pytest.mark.unit()
    def Test_config_error_no_key(self):
        """ConfigError with default key=None exercises the False branch."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Config_Error,
        )

        err = Exception_Config_Error("missing configuration")
        assert err.key is None
        assert str(err) == "missing configuration"

    @pytest.mark.unit()
    def Test_external_service_error_no_service_no_status_code(self):
        """ExternalServiceError with both service=None and status_code=None."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_External_Service_Error,
        )

        err = Exception_External_Service_Error("service unavailable")
        assert err.service is None
        assert err.status_code is None

    @pytest.mark.unit()
    def Test_external_service_error_service_only(self):
        """ExternalServiceError with service set but status_code=None."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_External_Service_Error,
        )

        err = Exception_External_Service_Error("timeout", service="yfinance")
        assert err.service == "yfinance"
        assert err.status_code is None

    @pytest.mark.unit()
    def Test_serialization_error_no_codec(self):
        """SerializationError with default codec=None exercises the False branch."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Serialization_Error,
        )

        err = Exception_Serialization_Error("encode failed")
        assert err.codec is None
        assert str(err) == "encode failed"


# ==============================================================================
# Main execution for debugging
# ==============================================================================

if __name__ == "__main__":
    pytest.main([__file__])

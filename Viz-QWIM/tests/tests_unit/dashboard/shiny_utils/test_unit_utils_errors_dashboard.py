"""Unit tests for utils_errors_dashboard module.

Tests deprecated exception aliases and the is_silent_exception helper:
- Error_Silent_Initialization (+ SilentInitializationException alias)
- Error_Dashboard_Initialization (+ DashboardInitializationError alias)
- Error_Data_Loading (+ DataLoadingError alias)
- Error_Module_Initialization (+ ModuleInitializationError alias)
- Error_Validation
- Error_Configuration
- is_silent_exception
"""

from __future__ import annotations

import pytest


# ============================================================================
# Error_Silent_Initialization
# ============================================================================


@pytest.mark.unit()
class Test_Error_Silent_Initialization:
    """Tests for Error_Silent_Initialization deprecated exception."""

    @pytest.mark.unit()
    def test_raises_as_exception(self):
        """Error_Silent_Initialization can be raised and caught."""
        from src.dashboard.shiny_utils.utils_errors_dashboard import Error_Silent_Initialization

        with pytest.raises(Error_Silent_Initialization):
            raise Error_Silent_Initialization("test silent error")

    @pytest.mark.unit()
    def test_emits_deprecation_warning(self):
        """Instantiating Error_Silent_Initialization emits DeprecationWarning."""
        from src.dashboard.shiny_utils.utils_errors_dashboard import Error_Silent_Initialization

        with pytest.warns(DeprecationWarning, match="deprecated"):
            Error_Silent_Initialization("deprecated")

    @pytest.mark.unit()
    def test_default_empty_message(self):
        """Can be raised with no message (uses default empty string)."""
        from src.dashboard.shiny_utils.utils_errors_dashboard import Error_Silent_Initialization

        with pytest.warns(DeprecationWarning, match="deprecated"):
            exc = Error_Silent_Initialization()

        assert exc is not None

    @pytest.mark.unit()
    def test_is_exception(self):
        """Error_Silent_Initialization is a subclass of Exception."""
        from src.dashboard.shiny_utils.utils_errors_dashboard import Error_Silent_Initialization

        with pytest.warns(DeprecationWarning, match="deprecated"):
            exc = Error_Silent_Initialization("msg")

        assert isinstance(exc, Exception)

    @pytest.mark.unit()
    def test_silent_initialization_exception_alias(self):
        """SilentInitializationException is the same class as Error_Silent_Initialization."""
        from src.dashboard.shiny_utils.utils_errors_dashboard import (
            Error_Silent_Initialization,
            SilentInitializationException,
        )

        assert SilentInitializationException is Error_Silent_Initialization

    @pytest.mark.unit()
    def test_caught_by_alias(self):
        """Exception raised as Error_Silent_Initialization is caught by alias."""
        from src.dashboard.shiny_utils.utils_errors_dashboard import (
            Error_Silent_Initialization,
            SilentInitializationException,
        )

        with pytest.warns(DeprecationWarning, match="deprecated"), pytest.raises(SilentInitializationException):
            raise Error_Silent_Initialization("via alias")


# ============================================================================
# Error_Dashboard_Initialization
# ============================================================================


@pytest.mark.unit()
class Test_Error_Dashboard_Initialization:
    """Tests for Error_Dashboard_Initialization deprecated exception."""

    @pytest.mark.unit()
    def test_raises_as_exception(self):
        """Error_Dashboard_Initialization can be raised and caught."""
        from src.dashboard.shiny_utils.utils_errors_dashboard import (
            Error_Dashboard_Initialization,
        )

        with pytest.warns(DeprecationWarning, match="deprecated"), pytest.raises(Error_Dashboard_Initialization):
            raise Error_Dashboard_Initialization("init failed")

    @pytest.mark.unit()
    def test_emits_deprecation_warning(self):
        """Instantiating emits DeprecationWarning."""
        from src.dashboard.shiny_utils.utils_errors_dashboard import (
            Error_Dashboard_Initialization,
        )

        with pytest.warns(DeprecationWarning, match="deprecated"):
            Error_Dashboard_Initialization("warn test")

    @pytest.mark.unit()
    def test_dashboard_initialization_error_alias(self):
        """DashboardInitializationError alias points to same class."""
        from src.dashboard.shiny_utils.utils_errors_dashboard import (
            DashboardInitializationError,
            Error_Dashboard_Initialization,
        )

        assert DashboardInitializationError is Error_Dashboard_Initialization


# ============================================================================
# Error_Data_Loading
# ============================================================================


@pytest.mark.unit()
class Test_Error_Data_Loading:
    """Tests for Error_Data_Loading deprecated exception."""

    @pytest.mark.unit()
    def test_raises_as_exception(self):
        """Error_Data_Loading can be raised and caught."""
        from src.dashboard.shiny_utils.utils_errors_dashboard import Error_Data_Loading

        with pytest.warns(DeprecationWarning, match="deprecated"), pytest.raises(Error_Data_Loading):
            raise Error_Data_Loading("file not found")

    @pytest.mark.unit()
    def test_emits_deprecation_warning(self):
        """Instantiating emits DeprecationWarning."""
        from src.dashboard.shiny_utils.utils_errors_dashboard import Error_Data_Loading

        with pytest.warns(DeprecationWarning, match="deprecated"):
            Error_Data_Loading()

    @pytest.mark.unit()
    def test_data_loading_error_alias(self):
        """DataLoadingError alias points to same class."""
        from src.dashboard.shiny_utils.utils_errors_dashboard import (
            DataLoadingError,
            Error_Data_Loading,
        )

        assert DataLoadingError is Error_Data_Loading


# ============================================================================
# Error_Module_Initialization
# ============================================================================


@pytest.mark.unit()
class Test_Error_Module_Initialization:
    """Tests for Error_Module_Initialization deprecated exception."""

    @pytest.mark.unit()
    def test_raises_as_exception(self):
        """Error_Module_Initialization can be raised and caught."""
        from src.dashboard.shiny_utils.utils_errors_dashboard import (
            Error_Module_Initialization,
        )

        with pytest.warns(DeprecationWarning, match="deprecated"), pytest.raises(Error_Module_Initialization):
            raise Error_Module_Initialization("module init failed")

    @pytest.mark.unit()
    def test_emits_deprecation_warning(self):
        """Instantiating emits DeprecationWarning."""
        from src.dashboard.shiny_utils.utils_errors_dashboard import (
            Error_Module_Initialization,
        )

        with pytest.warns(DeprecationWarning, match="deprecated"):
            Error_Module_Initialization()

    @pytest.mark.unit()
    def test_module_initialization_error_alias(self):
        """ModuleInitializationError alias points to same class."""
        from src.dashboard.shiny_utils.utils_errors_dashboard import (
            Error_Module_Initialization,
            ModuleInitializationError,
        )

        assert ModuleInitializationError is Error_Module_Initialization


# ============================================================================
# Error_Validation
# ============================================================================


@pytest.mark.unit()
class Test_Error_Validation:
    """Tests for Error_Validation deprecated exception."""

    @pytest.mark.unit()
    def test_raises_as_exception(self):
        """Error_Validation can be raised and caught."""
        from src.dashboard.shiny_utils.utils_errors_dashboard import Error_Validation

        with pytest.warns(DeprecationWarning, match="deprecated"), pytest.raises(Error_Validation):
            raise Error_Validation("bad input")

    @pytest.mark.unit()
    def test_emits_deprecation_warning(self):
        """Instantiating emits DeprecationWarning."""
        from src.dashboard.shiny_utils.utils_errors_dashboard import Error_Validation

        with pytest.warns(DeprecationWarning, match="deprecated"):
            Error_Validation("test")


# ============================================================================
# Error_Configuration
# ============================================================================


@pytest.mark.unit()
class Test_Error_Configuration:
    """Tests for Error_Configuration deprecated exception."""

    @pytest.mark.unit()
    def test_raises_as_exception(self):
        """Error_Configuration can be raised and caught."""
        from src.dashboard.shiny_utils.utils_errors_dashboard import Error_Configuration

        with pytest.warns(DeprecationWarning, match="deprecated"), pytest.raises(Error_Configuration):
            raise Error_Configuration("bad config")

    @pytest.mark.unit()
    def test_emits_deprecation_warning(self):
        """Instantiating emits DeprecationWarning."""
        from src.dashboard.shiny_utils.utils_errors_dashboard import Error_Configuration

        with pytest.warns(DeprecationWarning, match="deprecated"):
            Error_Configuration()


# ============================================================================
# is_silent_exception
# ============================================================================


@pytest.mark.unit()
class Test_Is_Silent_Exception:
    """Tests for the is_silent_exception helper function."""

    @pytest.mark.unit()
    def test_error_silent_initialization_returns_true(self):
        """Error_Silent_Initialization is recognised as silent."""
        import warnings

        from src.dashboard.shiny_utils.utils_errors_dashboard import (
            Error_Silent_Initialization,
            is_silent_exception,
        )

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            exc = Error_Silent_Initialization("silent")

        assert is_silent_exception(exception = exc) is True

    @pytest.mark.unit()
    def test_attribute_error_returns_true(self):
        """AttributeError is treated as a silent exception (reactive init pattern)."""
        from src.dashboard.shiny_utils.utils_errors_dashboard import is_silent_exception

        exc = AttributeError("reactive not initialised")

        assert is_silent_exception(exception = exc) is True

    @pytest.mark.unit()
    def test_value_error_returns_false(self):
        """ValueError is NOT a silent exception."""
        from src.dashboard.shiny_utils.utils_errors_dashboard import is_silent_exception

        exc = ValueError("not silent")

        assert is_silent_exception(exception = exc) is False

    @pytest.mark.unit()
    def test_runtime_error_returns_false(self):
        """RuntimeError is NOT a silent exception."""
        from src.dashboard.shiny_utils.utils_errors_dashboard import is_silent_exception

        exc = RuntimeError("crash")

        assert is_silent_exception(exception = exc) is False

    @pytest.mark.unit()
    def test_exception_custom_with_debug_severity_returns_true(self):
        """Exception_Custom with DEBUG severity is treated as silent."""
        from src.dashboard.shiny_utils.utils_errors_dashboard import is_silent_exception
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Custom,
            Exception_Severity,
        )

        exc = Exception_Custom("debug level", severity=Exception_Severity.DEBUG)

        assert is_silent_exception(exception = exc) is True

    @pytest.mark.unit()
    def test_exception_custom_with_error_severity_returns_false(self):
        """Exception_Custom with ERROR severity is NOT silent."""
        from src.dashboard.shiny_utils.utils_errors_dashboard import is_silent_exception
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Custom,
            Exception_Severity,
        )

        exc = Exception_Custom("error level", severity=Exception_Severity.ERROR)

        assert is_silent_exception(exception = exc) is False

    @pytest.mark.unit()
    def test_plain_exception_returns_false(self):
        """Generic Exception is NOT a silent exception."""
        from src.dashboard.shiny_utils.utils_errors_dashboard import is_silent_exception

        exc = Exception("generic")

        assert is_silent_exception(exception = exc) is False


# ============================================================================
# Regression tests
# ============================================================================


@pytest.mark.regression()
class Test_Utils_Errors_Dashboard_Regression:
    """Regression tests for stable behaviors in utils_errors_dashboard."""

    @pytest.mark.unit()
    def test_all_deprecated_classes_are_exceptions(self):
        """Every exported exception class is an Exception subclass."""
        import warnings

        from src.dashboard.shiny_utils.utils_errors_dashboard import (
            Error_Configuration,
            Error_Dashboard_Initialization,
            Error_Data_Loading,
            Error_Module_Initialization,
            Error_Silent_Initialization,
            Error_Validation,
        )

        classes = [
            Error_Silent_Initialization,
            Error_Dashboard_Initialization,
            Error_Data_Loading,
            Error_Module_Initialization,
            Error_Validation,
            Error_Configuration,
        ]

        for cls in classes:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                instance = cls("test")
            assert isinstance(instance, Exception), f"{cls.__name__} must be an Exception"

    @pytest.mark.unit()
    def test_all_deprecated_classes_emit_deprecation_warning(self):
        """Every exported exception class emits DeprecationWarning on instantiation."""

        from src.dashboard.shiny_utils.utils_errors_dashboard import (
            Error_Configuration,
            Error_Dashboard_Initialization,
            Error_Data_Loading,
            Error_Module_Initialization,
            Error_Silent_Initialization,
            Error_Validation,
        )

        classes = [
            Error_Silent_Initialization,
            Error_Dashboard_Initialization,
            Error_Data_Loading,
            Error_Module_Initialization,
            Error_Validation,
            Error_Configuration,
        ]

        for cls in classes:
            with pytest.warns(DeprecationWarning, match="deprecated"):
                cls("regression test")

    @pytest.mark.unit()
    def test_is_silent_exception_never_raises(self):
        """is_silent_exception must never raise â€” always returns bool."""
        from src.dashboard.shiny_utils.utils_errors_dashboard import is_silent_exception

        test_exceptions = [
            Exception("generic"),
            ValueError("value"),
            AttributeError("attr"),
            RuntimeError("runtime"),
            TypeError("type"),
        ]

        for exc in test_exceptions:
            result = is_silent_exception(exception = exc)
            assert isinstance(result, bool), f"Expected bool for {type(exc).__name__}"


"""
Unit Tests for Dashboard Error Classes
======================================

This module contains comprehensive unit tests for the utils_errors module,
which provides custom exception classes for the QWIM Dashboard.

Test Coverage:
    - Error_Silent_Initialization exception class
    - Error_Dashboard_Initialization exception class
    - Error_Data_Loading exception class
    - Error_Module_Initialization exception class
    - Error_Validation exception class
    - Error_Configuration exception class
    - Backward compatibility aliases
    - is_silent_exception helper function

Testing Approach:
    - Tests exception creation and message handling
    - Tests exception inheritance
    - Tests backward compatibility with old names
    - Tests helper functions
"""

import pytest


# ============================================================================
# Tests for Error_Silent_Initialization
# ============================================================================


@pytest.mark.unit()
class Test_Error_Silent_Initialization:
    """Test cases for Error_Silent_Initialization exception."""

    @pytest.mark.unit()
    def test_can_be_raised(self):
        """Test that exception can be raised."""
        from src.dashboard.shiny_utils.utils_errors import Error_Silent_Initialization

        with pytest.raises(Error_Silent_Initialization):
            raise Error_Silent_Initialization("Test message")

    @pytest.mark.unit()
    def test_preserves_message(self):
        """Test that exception preserves message."""
        from src.dashboard.shiny_utils.utils_errors import Error_Silent_Initialization

        try:
            raise Error_Silent_Initialization("Test error message")
        except Error_Silent_Initialization as e:
            assert "Test error message" in str(e)

    @pytest.mark.unit()
    def test_inherits_from_exception(self):
        """Test that exception inherits from Exception."""
        from src.dashboard.shiny_utils.utils_errors import Error_Silent_Initialization

        assert issubclass(Error_Silent_Initialization, Exception)

    @pytest.mark.unit()
    def test_backward_compatibility_alias(self):
        """Test backward compatibility with SilentInitializationException."""
        from src.dashboard.shiny_utils.utils_errors import (
            Error_Silent_Initialization,
            SilentInitializationException,
        )

        assert SilentInitializationException is Error_Silent_Initialization


# ============================================================================
# Tests for Error_Dashboard_Initialization
# ============================================================================


@pytest.mark.unit()
class Test_Error_Dashboard_Initialization:
    """Test cases for Error_Dashboard_Initialization exception."""

    @pytest.mark.unit()
    def test_can_be_raised(self):
        """Test that exception can be raised."""
        from src.dashboard.shiny_utils.utils_errors import Error_Dashboard_Initialization

        with pytest.raises(Error_Dashboard_Initialization):
            raise Error_Dashboard_Initialization("Dashboard init failed")

    @pytest.mark.unit()
    def test_preserves_message(self):
        """Test that exception preserves message."""
        from src.dashboard.shiny_utils.utils_errors import Error_Dashboard_Initialization

        try:
            raise Error_Dashboard_Initialization("Critical failure")
        except Error_Dashboard_Initialization as e:
            assert "Critical failure" in str(e)

    @pytest.mark.unit()
    def test_inherits_from_exception(self):
        """Test that exception inherits from Exception."""
        from src.dashboard.shiny_utils.utils_errors import Error_Dashboard_Initialization

        assert issubclass(Error_Dashboard_Initialization, Exception)

    @pytest.mark.unit()
    def test_backward_compatibility_alias(self):
        """Test backward compatibility with DashboardInitializationError."""
        from src.dashboard.shiny_utils.utils_errors import (
            DashboardInitializationError,
            Error_Dashboard_Initialization,
        )

        assert DashboardInitializationError is Error_Dashboard_Initialization


# ============================================================================
# Tests for Error_Data_Loading
# ============================================================================


@pytest.mark.unit()
class Test_Error_Data_Loading:
    """Test cases for Error_Data_Loading exception."""

    @pytest.mark.unit()
    def test_can_be_raised(self):
        """Test that exception can be raised."""
        from src.dashboard.shiny_utils.utils_errors import Error_Data_Loading

        with pytest.raises(Error_Data_Loading):
            raise Error_Data_Loading("Data file not found")

    @pytest.mark.unit()
    def test_preserves_message(self):
        """Test that exception preserves message."""
        from src.dashboard.shiny_utils.utils_errors import Error_Data_Loading

        try:
            raise Error_Data_Loading("File path: /data/test.csv")
        except Error_Data_Loading as e:
            assert "/data/test.csv" in str(e)

    @pytest.mark.unit()
    def test_inherits_from_exception(self):
        """Test that exception inherits from Exception."""
        from src.dashboard.shiny_utils.utils_errors import Error_Data_Loading

        assert issubclass(Error_Data_Loading, Exception)

    @pytest.mark.unit()
    def test_backward_compatibility_alias(self):
        """Test backward compatibility with DataLoadingError."""
        from src.dashboard.shiny_utils.utils_errors import DataLoadingError, Error_Data_Loading

        assert DataLoadingError is Error_Data_Loading


# ============================================================================
# Tests for Error_Module_Initialization
# ============================================================================


@pytest.mark.unit()
class Test_Error_Module_Initialization:
    """Test cases for Error_Module_Initialization exception."""

    @pytest.mark.unit()
    def test_can_be_raised(self):
        """Test that exception can be raised."""
        from src.dashboard.shiny_utils.utils_errors import Error_Module_Initialization

        with pytest.raises(Error_Module_Initialization):
            raise Error_Module_Initialization("Module failed")

    @pytest.mark.unit()
    def test_preserves_message(self):
        """Test that exception preserves message."""
        from src.dashboard.shiny_utils.utils_errors import Error_Module_Initialization

        try:
            raise Error_Module_Initialization("Portfolio tab init failed")
        except Error_Module_Initialization as e:
            assert "Portfolio tab" in str(e)

    @pytest.mark.unit()
    def test_inherits_from_exception(self):
        """Test that exception inherits from Exception."""
        from src.dashboard.shiny_utils.utils_errors import Error_Module_Initialization

        assert issubclass(Error_Module_Initialization, Exception)

    @pytest.mark.unit()
    def test_backward_compatibility_alias(self):
        """Test backward compatibility with ModuleInitializationError."""
        from src.dashboard.shiny_utils.utils_errors import (
            Error_Module_Initialization,
            ModuleInitializationError,
        )

        assert ModuleInitializationError is Error_Module_Initialization


# ============================================================================
# Tests for Error_Validation
# ============================================================================


@pytest.mark.unit()
class Test_Error_Validation:
    """Test cases for Error_Validation exception."""

    @pytest.mark.unit()
    def test_can_be_raised(self):
        """Test that exception can be raised."""
        from src.dashboard.shiny_utils.utils_errors import Error_Validation

        with pytest.raises(Error_Validation):
            raise Error_Validation("Validation failed")

    @pytest.mark.unit()
    def test_preserves_message(self):
        """Test that exception preserves message."""
        from src.dashboard.shiny_utils.utils_errors import Error_Validation

        try:
            raise Error_Validation("Weights must sum to 1.0")
        except Error_Validation as e:
            assert "sum to 1.0" in str(e)

    @pytest.mark.unit()
    def test_inherits_from_exception(self):
        """Test that exception inherits from Exception."""
        from src.dashboard.shiny_utils.utils_errors import Error_Validation

        assert issubclass(Error_Validation, Exception)


# ============================================================================
# Tests for Error_Configuration
# ============================================================================


@pytest.mark.unit()
class Test_Error_Configuration:
    """Test cases for Error_Configuration exception."""

    @pytest.mark.unit()
    def test_can_be_raised(self):
        """Test that exception can be raised."""
        from src.dashboard.shiny_utils.utils_errors import Error_Configuration

        with pytest.raises(Error_Configuration):
            raise Error_Configuration("Config error")

    @pytest.mark.unit()
    def test_preserves_message(self):
        """Test that exception preserves message."""
        from src.dashboard.shiny_utils.utils_errors import Error_Configuration

        try:
            raise Error_Configuration("Missing API key")
        except Error_Configuration as e:
            assert "API key" in str(e)

    @pytest.mark.unit()
    def test_inherits_from_exception(self):
        """Test that exception inherits from Exception."""
        from src.dashboard.shiny_utils.utils_errors import Error_Configuration

        assert issubclass(Error_Configuration, Exception)


# ============================================================================
# Tests for is_silent_exception
# ============================================================================


@pytest.mark.unit()
class Test_Is_Silent_Exception:
    """Test cases for is_silent_exception helper function."""

    @pytest.mark.unit()
    def test_returns_true_for_silent_exception(self):
        """Test returns True for Error_Silent_Initialization."""
        from src.dashboard.shiny_utils.utils_errors import (
            Error_Silent_Initialization,
            is_silent_exception,
        )

        exc = Error_Silent_Initialization("Test")
        result = is_silent_exception(exception = exc)

        assert result is True

    @pytest.mark.unit()
    def test_returns_false_for_other_exceptions(self):
        """Test returns False for non-silent exceptions."""
        from src.dashboard.shiny_utils.utils_errors import (
            Error_Dashboard_Initialization,
            is_silent_exception,
        )

        exc = Error_Dashboard_Initialization("Test")
        result = is_silent_exception(exception = exc)

        assert result is False

    @pytest.mark.unit()
    def test_returns_false_for_standard_exception(self):
        """Test returns False for standard Exception."""
        from src.dashboard.shiny_utils.utils_errors import is_silent_exception

        exc = ValueError("Test")
        result = is_silent_exception(exception = exc)

        assert result is False

    @pytest.mark.unit()
    def test_returns_true_for_backward_compat_alias(self):
        """Test returns True for backward compatibility alias."""
        from src.dashboard.shiny_utils.utils_errors import (
            SilentInitializationException,
            is_silent_exception,
        )

        exc = SilentInitializationException("Test")
        result = is_silent_exception(exception = exc)

        assert result is True


# ============================================================================
# Tests for Exception Catching Patterns
# ============================================================================


@pytest.mark.unit()
class Test_Exception_Catching_Patterns:
    """Test common exception catching patterns."""

    @pytest.mark.unit()
    def test_catch_all_custom_exceptions(self):
        """Test that all custom exceptions can be caught as Exception."""
        from src.dashboard.shiny_utils.utils_errors import (
            Error_Configuration,
            Error_Dashboard_Initialization,
            Error_Data_Loading,
            Error_Module_Initialization,
            Error_Silent_Initialization,
            Error_Validation,
        )

        exceptions = [
            Error_Silent_Initialization("test"),
            Error_Dashboard_Initialization("test"),
            Error_Data_Loading("test"),
            Error_Module_Initialization("test"),
            Error_Validation("test"),
            Error_Configuration("test"),
        ]

        for exc in exceptions:
            try:
                raise exc
            except Exception as caught:
                assert "test" in str(caught)

    @pytest.mark.unit()
    def test_specific_catch_does_not_catch_others(self):
        """Test that catching specific exception doesn't catch others."""
        from src.dashboard.shiny_utils.utils_errors import Error_Data_Loading, Error_Validation

        caught_correct = False
        caught_wrong = False

        try:
            raise Error_Data_Loading("data error")
        except Error_Validation:
            caught_wrong = True
        except Error_Data_Loading:
            caught_correct = True

        assert caught_correct is True
        assert caught_wrong is False

"""Hypothesis (property-based) tests for utils_errors_dashboard module.

Tests property invariants for:
- Deprecated exception class wrappers (DeprecationWarning emission)
- is_silent_exception
- Inheritance chain of each deprecated class
"""

from __future__ import annotations

import warnings

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.dashboard.shiny_utils.utils_errors_dashboard import (
    Error_Configuration,
    Error_Dashboard_Initialization,
    Error_Data_Loading,
    Error_Module_Initialization,
    Error_Silent_Initialization,
    Error_Validation,
    is_silent_exception,
)


# ---------------------------------------------------------------------------
# Reusable strategies
# ---------------------------------------------------------------------------

_st_message = st.text(min_size=1, max_size=100)


# ===========================================================================
# Class_Test_Hypothesis_Error_Dashboard_Classes
# ===========================================================================


class Class_Test_Hypothesis_Error_Dashboard_Classes:
    """Property tests for the deprecated exception wrapper classes."""

    @pytest.mark.unit()
    @given(msg=_st_message)
    @settings(max_examples=200)
    def Test_error_silent_initialization_emits_deprecation_warning(
        self,
        msg: str,
    ) -> None:
        """Instantiating Error_Silent_Initialization must emit DeprecationWarning."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            exc = Error_Silent_Initialization(msg)
            assert any(issubclass(warn.category, DeprecationWarning) for warn in caught)

    @pytest.mark.unit()
    @given(msg=_st_message)
    @settings(max_examples=200)
    def Test_error_dashboard_initialization_emits_deprecation_warning(
        self,
        msg: str,
    ) -> None:
        """Instantiating Error_Dashboard_Initialization must emit DeprecationWarning."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            _exc = Error_Dashboard_Initialization(msg)
            assert any(issubclass(warn.category, DeprecationWarning) for warn in caught)

    @pytest.mark.unit()
    @given(msg=_st_message)
    @settings(max_examples=200)
    def Test_error_data_loading_emits_deprecation_warning(
        self,
        msg: str,
    ) -> None:
        """Instantiating Error_Data_Loading must emit DeprecationWarning."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            _exc = Error_Data_Loading(msg)
            assert any(issubclass(warn.category, DeprecationWarning) for warn in caught)

    @pytest.mark.unit()
    @given(msg=_st_message)
    @settings(max_examples=200)
    def Test_error_module_initialization_emits_deprecation_warning(
        self,
        msg: str,
    ) -> None:
        """Instantiating Error_Module_Initialization must emit DeprecationWarning."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            _exc = Error_Module_Initialization(msg)
            assert any(issubclass(warn.category, DeprecationWarning) for warn in caught)

    @pytest.mark.unit()
    @given(msg=_st_message)
    @settings(max_examples=200)
    def Test_error_validation_emits_deprecation_warning(
        self,
        msg: str,
    ) -> None:
        """Instantiating Error_Validation must emit DeprecationWarning."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            _exc = Error_Validation(msg)
            assert any(issubclass(warn.category, DeprecationWarning) for warn in caught)

    @pytest.mark.unit()
    @given(msg=_st_message)
    @settings(max_examples=200)
    def Test_error_configuration_emits_deprecation_warning(
        self,
        msg: str,
    ) -> None:
        """Instantiating Error_Configuration must emit DeprecationWarning."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            _exc = Error_Configuration(msg)
            assert any(issubclass(warn.category, DeprecationWarning) for warn in caught)

    @pytest.mark.unit()
    @given(msg=_st_message)
    @settings(max_examples=200)
    def Test_all_deprecated_exceptions_are_exceptions(
        self,
        msg: str,
    ) -> None:
        """All deprecated exception classes must inherit from BaseException."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            for cls in (
                Error_Silent_Initialization,
                Error_Dashboard_Initialization,
                Error_Data_Loading,
                Error_Module_Initialization,
                Error_Validation,
                Error_Configuration,
            ):
                exc = cls(msg)
                assert isinstance(exc, BaseException)

    @pytest.mark.unit()
    @given(msg=_st_message)
    @settings(max_examples=200)
    def Test_error_message_is_preserved(
        self,
        msg: str,
    ) -> None:
        """The message passed to each class must be retrievable from str(exc)."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            for cls in (
                Error_Dashboard_Initialization,
                Error_Data_Loading,
                Error_Module_Initialization,
                Error_Validation,
                Error_Configuration,
            ):
                exc = cls(msg)
                assert msg in str(exc)


# ===========================================================================
# Class_Test_Hypothesis_Is_Silent_Exception
# ===========================================================================


class Class_Test_Hypothesis_Is_Silent_Exception:
    """Property tests for is_silent_exception."""

    @pytest.mark.unit()
    @given(msg=_st_message)
    @settings(max_examples=200)
    def Test_error_silent_initialization_is_silent(
        self,
        msg: str,
    ) -> None:
        """Error_Silent_Initialization must be recognized as silent."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            exc = Error_Silent_Initialization(msg)
        assert is_silent_exception(exception=exc) is True

    @pytest.mark.unit()
    @given(msg=_st_message)
    @settings(max_examples=200)
    def Test_generic_value_error_is_not_silent(
        self,
        msg: str,
    ) -> None:
        """A plain ValueError must NOT be recognized as silent."""
        exc = ValueError(msg)
        assert is_silent_exception(exception=exc) is False

    @pytest.mark.unit()
    @given(msg=_st_message)
    @settings(max_examples=200)
    def Test_error_dashboard_initialization_is_not_silent(
        self,
        msg: str,
    ) -> None:
        """Error_Dashboard_Initialization must NOT be recognized as silent."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            exc = Error_Dashboard_Initialization(msg)
        assert is_silent_exception(exception=exc) is False

    @pytest.mark.unit()
    def Test_none_input_does_not_crash(self) -> None:
        """is_silent_exception(None) must not raise — must return a bool."""
        result = is_silent_exception(exception=None)  # type: ignore[arg-type]
        assert isinstance(result, bool)

    @pytest.mark.unit()
    @given(
        non_exc=st.one_of(
            st.integers(),
            st.text(min_size=0, max_size=20),
        )
    )
    @settings(max_examples=200)
    def Test_non_exception_input_returns_false(
        self,
        non_exc: object,
    ) -> None:
        """Non-exception input must return False (no crash)."""
        result = is_silent_exception(exception=non_exc)  # type: ignore[arg-type]
        assert result is False

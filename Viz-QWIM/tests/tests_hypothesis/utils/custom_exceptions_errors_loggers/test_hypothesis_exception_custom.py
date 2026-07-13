"""Hypothesis (property-based) tests for custom exception classes.

Tests cover:
- ``Exception_Format`` and ``Exception_Severity`` enum invariants
- ``Exception_Custom`` construction — message stored, severity stored
- ``Exception_Custom.From_Exception`` factory method
- ``Exception_Custom.To_Dict`` round-trip invariant
- ``Exception_Custom.__repr__`` contains class name and message
- Domain-specific subclasses: ``Exception_Validation_Input``, ``Exception_Calculation``,
  ``Exception_Configuration``, ``Exception_Data_Not_Found``
- Subclasses are subclass of ``Exception_Custom`` and ``Exception``
"""

from __future__ import annotations

import json

import pytest

from hypothesis import given, settings
from hypothesis import strategies as st

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Calculation,
    Exception_Configuration,
    Exception_Custom,
    Exception_Data_Not_Found,
    Exception_Format,
    Exception_Severity,
    Exception_Validation_Input,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MESSAGES = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",)),
    min_size=1,
    max_size=200,
)


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Exception_Format_Enum
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Exception_Format_Enum:
    """Tests for Exception_Format enum."""

    @pytest.mark.unit()
    @given(idx_fmt=st.sampled_from(list(Exception_Format)))
    @settings(max_examples=200)
    def Test_all_members_have_truthy_name(self, idx_fmt: Exception_Format) -> None:
        """Every Exception_Format member has a non-empty name."""
        assert isinstance(idx_fmt.name, str)
        assert len(idx_fmt.name) > 0

    @pytest.mark.unit()
    def Test_simple_member_exists(self) -> None:
        """Exception_Format.SIMPLE is present."""
        assert Exception_Format.SIMPLE in list(Exception_Format)

    @pytest.mark.unit()
    def Test_json_member_exists(self) -> None:
        """Exception_Format.JSON is present."""
        assert Exception_Format.JSON in list(Exception_Format)


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Exception_Severity_Enum
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Exception_Severity_Enum:
    """Tests for Exception_Severity enum."""

    @pytest.mark.unit()
    @given(idx_sev=st.sampled_from(list(Exception_Severity)))
    @settings(max_examples=200)
    def Test_all_members_have_truthy_name(self, idx_sev: Exception_Severity) -> None:
        """Every Exception_Severity member has a non-empty name."""
        assert isinstance(idx_sev.name, str)
        assert len(idx_sev.name) > 0

    @pytest.mark.unit()
    def Test_error_member_exists(self) -> None:
        """Exception_Severity.ERROR is present."""
        assert Exception_Severity.ERROR in list(Exception_Severity)

    @pytest.mark.unit()
    def Test_critical_member_exists(self) -> None:
        """Exception_Severity.CRITICAL is present."""
        assert Exception_Severity.CRITICAL in list(Exception_Severity)


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Exception_Custom_Construction
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Exception_Custom_Construction:
    """Tests for Exception_Custom construction invariants."""

    @pytest.mark.unit()
    @given(msg=_MESSAGES)
    @settings(max_examples=200)
    def Test_message_property_returns_input(self, msg: str) -> None:
        """message property returns exactly the string passed to __init__."""
        exc = Exception_Custom(message=msg)
        assert exc.Message == msg

    @pytest.mark.unit()
    @given(
        msg=_MESSAGES,
        idx_sev=st.sampled_from(list(Exception_Severity)),
    )
    @settings(max_examples=200)
    def Test_severity_property_returns_input(
        self,
        msg: str,
        idx_sev: Exception_Severity,
    ) -> None:
        """severity property returns the severity passed to __init__."""
        exc = Exception_Custom(message=msg, severity=idx_sev)
        assert exc.Severity == idx_sev

    @pytest.mark.unit()
    @given(msg=_MESSAGES)
    @settings(max_examples=200)
    def Test_is_instance_of_exception(self, msg: str) -> None:
        """Exception_Custom is a subclass of Exception."""
        exc = Exception_Custom(message=msg)
        assert isinstance(exc, Exception)

    @pytest.mark.unit()
    @given(msg=_MESSAGES)
    @settings(max_examples=200)
    def Test_repr_contains_class_name_and_message(self, msg: str) -> None:
        """__repr__ contains the class name and message."""
        exc = Exception_Custom(message=msg)
        rep = repr(exc)
        assert "Exception_Custom" in rep
        assert msg in rep

    @pytest.mark.unit()
    @given(msg=_MESSAGES)
    @settings(max_examples=200)
    def Test_format_simple_suppresses_traceback_lines(self, msg: str) -> None:
        """suppress_traceback=True makes str(exc) equal to just the message."""
        exc = Exception_Custom(
            message=msg,
            exception_format=Exception_Format.SIMPLE,
            suppress_traceback=True,
        )
        assert str(exc) == msg

    @pytest.mark.unit()
    @given(
        msg=_MESSAGES,
        context_val=st.text(min_size=1, max_size=50),
    )
    @settings(max_examples=200)
    def Test_to_dict_message_matches(
        self,
        msg: str,
        context_val: str,
    ) -> None:
        """To_Dict() returns a dict with the correct 'message' field."""
        exc = Exception_Custom(message=msg, context={"key": context_val})
        result = exc.To_Dict()
        assert isinstance(result, dict)
        assert result["message"] == msg

    @pytest.mark.unit()
    @given(msg=_MESSAGES)
    @settings(max_examples=200)
    def Test_to_json_is_valid_json(self, msg: str) -> None:
        """To_JSON() always returns valid JSON."""
        exc = Exception_Custom(message=msg)
        json_str = exc.To_JSON()
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)

    @pytest.mark.unit()
    @given(msg=_MESSAGES)
    @settings(max_examples=200)
    def Test_exception_context_has_non_empty_exception_id(self, msg: str) -> None:
        """Exception_Context.exception_id is always non-empty."""
        exc = Exception_Custom(message=msg)
        assert len(exc.Exception_Context.exception_id) > 0

    @pytest.mark.unit()
    @given(msg=_MESSAGES)
    @settings(max_examples=200)
    def Test_exception_context_exception_type_is_string(self, msg: str) -> None:
        """Exception_Context.exception_type is a non-empty string."""
        exc = Exception_Custom(message=msg)
        assert isinstance(exc.Exception_Context.exception_type, str)
        assert len(exc.Exception_Context.exception_type) > 0


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Exception_Custom_From_Exception
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Exception_Custom_From_Exception:
    """Tests for Exception_Custom.From_Exception factory."""

    @pytest.mark.unit()
    @given(msg=_MESSAGES)
    @settings(max_examples=200)
    def Test_from_exception_wraps_message(self, msg: str) -> None:
        """From_Exception preserves the original exception message."""
        orig = ValueError(msg)
        exc = Exception_Custom.From_Exception(exception = orig)
        assert exc.Message == msg

    @pytest.mark.unit()
    @given(msg=_MESSAGES)
    @settings(max_examples=200)
    def Test_from_exception_sets_cause(self, msg: str) -> None:
        """From_Exception sets __cause__ to the original exception."""
        orig = RuntimeError(msg)
        exc = Exception_Custom.From_Exception(exception = orig)
        assert exc.__cause__ is orig

    @pytest.mark.unit()
    @given(msg=_MESSAGES)
    @settings(max_examples=200)
    def Test_from_exception_returns_exception_custom_instance(self, msg: str) -> None:
        """From_Exception returns an Exception_Custom instance."""
        orig = TypeError(msg)
        exc = Exception_Custom.From_Exception(exception = orig)
        assert isinstance(exc, Exception_Custom)


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Exception_Validation_Input
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Exception_Validation_Input:
    """Tests for Exception_Validation_Input."""

    @pytest.mark.unit()
    @given(msg=_MESSAGES)
    @settings(max_examples=200)
    def Test_is_subclass_of_exception_custom(self, msg: str) -> None:
        """Exception_Validation_Input is a subclass of Exception_Custom."""
        exc = Exception_Validation_Input(msg)
        assert isinstance(exc, Exception_Custom)

    @pytest.mark.unit()
    @given(msg=_MESSAGES)
    @settings(max_examples=200)
    def Test_message_stored_correctly(self, msg: str) -> None:
        """message property returns the passed message."""
        exc = Exception_Validation_Input(msg)
        assert exc.Message == msg

    @pytest.mark.unit()
    @given(
        msg=_MESSAGES,
        field=st.text(min_size=1, max_size=50),
    )
    @settings(max_examples=200)
    def Test_field_name_appears_in_context(
        self,
        msg: str,
        field: str,
    ) -> None:
        """field_name appears in To_Dict()['context'] when provided."""
        exc = Exception_Validation_Input(msg, field_name=field)
        result = exc.To_Dict()
        assert result["context"].get("field_name") == field

    @pytest.mark.unit()
    @given(msg=_MESSAGES)
    @settings(max_examples=200)
    def Test_can_be_raised_and_caught(self, msg: str) -> None:
        """Exception_Validation_Input can be raised and caught as Exception."""
        with pytest.raises(Exception_Validation_Input):
            raise Exception_Validation_Input(msg)


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Exception_Calculation
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Exception_Calculation:
    """Tests for Exception_Calculation."""

    @pytest.mark.unit()
    @given(msg=_MESSAGES)
    @settings(max_examples=200)
    def Test_is_subclass_of_exception_custom(self, msg: str) -> None:
        """Exception_Calculation is a subclass of Exception_Custom."""
        exc = Exception_Calculation(msg)
        assert isinstance(exc, Exception_Custom)

    @pytest.mark.unit()
    @given(msg=_MESSAGES)
    @settings(max_examples=200)
    def Test_can_be_raised_and_caught(self, msg: str) -> None:
        """Exception_Calculation can be raised and caught."""
        with pytest.raises(Exception_Calculation):
            raise Exception_Calculation(msg)

    @pytest.mark.unit()
    @given(
        msg=_MESSAGES,
        operation=st.text(min_size=1, max_size=50),
    )
    @settings(max_examples=200)
    def Test_operation_appears_in_context(
        self,
        msg: str,
        operation: str,
    ) -> None:
        """operation appears in To_Dict()['context'] when provided."""
        exc = Exception_Calculation(msg, operation=operation)
        result = exc.To_Dict()
        assert result["context"].get("operation") == operation


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Exception_Configuration
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Exception_Configuration:
    """Tests for Exception_Configuration."""

    @pytest.mark.unit()
    @given(msg=_MESSAGES)
    @settings(max_examples=200)
    def Test_is_subclass_of_exception_custom(self, msg: str) -> None:
        """Exception_Configuration is a subclass of Exception_Custom."""
        exc = Exception_Configuration(msg)
        assert isinstance(exc, Exception_Custom)

    @pytest.mark.unit()
    @given(
        msg=_MESSAGES,
        key=st.text(min_size=1, max_size=50),
    )
    @settings(max_examples=200)
    def Test_config_key_in_context(
        self,
        msg: str,
        key: str,
    ) -> None:
        """config_key appears in To_Dict()['context'] when provided."""
        exc = Exception_Configuration(msg, config_key=key)
        result = exc.To_Dict()
        assert result["context"].get("config_key") == key


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Exception_Data_Not_Found
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Exception_Data_Not_Found:
    """Tests for Exception_Data_Not_Found."""

    @pytest.mark.unit()
    @given(msg=_MESSAGES)
    @settings(max_examples=200)
    def Test_is_subclass_of_exception_custom(self, msg: str) -> None:
        """Exception_Data_Not_Found is a subclass of Exception_Custom."""
        exc = Exception_Data_Not_Found(msg)
        assert isinstance(exc, Exception_Custom)

    @pytest.mark.unit()
    @given(
        msg=_MESSAGES,
        data_type=st.text(min_size=1, max_size=50),
    )
    @settings(max_examples=200)
    def Test_data_type_in_context(
        self,
        msg: str,
        data_type: str,
    ) -> None:
        """data_type appears in To_Dict()['context'] when provided."""
        exc = Exception_Data_Not_Found(msg, data_type=data_type)
        result = exc.To_Dict()
        assert result["context"].get("data_type") == data_type

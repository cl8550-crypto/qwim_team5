"""Hypothesis property-based tests for clients_QWIM.utils_client sub-modules.

Covers the pure-Python helpers in:
    - ``_client_formatters``   : numeric parsing, phone normalisation, trademark symbols
    - ``_client_validators``   : field-choice and numeric-range validation

Properties tested
-----------------
* ``_safe_numeric`` always returns a float; never raises.
* ``_parse_whole_dollar_amount`` is None-safe and rejects floats with cents.
* ``_safe_whole_dollar_numeric`` is always a non-negative float for valid inputs.
* ``_normalize_phone_number_US`` round-trips a 10-digit sequence to ``NNN-NNN-NNNN``.
* ``validate_extracted_client_data`` returns a 2-tuple (bool, list) for any dict.
* ``build_checkbox_fields_by_section`` always returns a dict of sets.
* ``_validate_choice_field`` only appends a warning when the value is not in the list.
* ``_validate_numeric_range`` only appends a warning when the value is out of range.

Author:     QWIM Development Team
Version:    1.0.0
"""

from __future__ import annotations

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from src.clients_QWIM.utils_client import (
    _is_currency_field_name,
    _normalize_phone_number_US,
    _normalize_text_trademark_symbols,
    _parse_whole_dollar_amount,
    _safe_numeric,
    _safe_whole_dollar_numeric,
    _validate_choice_field,
    _validate_numeric_range,
    build_checkbox_fields_by_section,
    validate_extracted_client_data,
)


# ---------------------------------------------------------------------------
# Shared strategies
# ---------------------------------------------------------------------------

_strategy_any_value = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-10_000_000, max_value=10_000_000),
    st.floats(allow_nan=False, allow_infinity=False, min_value=-1e9, max_value=1e9),
    st.text(max_size=40),
)

_strategy_dollar_integer = st.integers(min_value=0, max_value=9_999_999)

_strategy_nonempty_ascii = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
    min_size=1,
    max_size=20,
)

_strategy_ten_digits = st.from_regex(r"\d{10}", fullmatch=True)

_strategy_valid_choices = st.lists(
    _strategy_nonempty_ascii,
    min_size=1,
    max_size=10,
)


# ===========================================================================
# _safe_numeric
# ===========================================================================


class Class_Test_Hypothesis_Safe_Numeric:
    """Property tests for ``_safe_numeric``."""

    @pytest.mark.unit()
    @given(value=_strategy_any_value)
    @settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_always_returns_float(self, value: object) -> None:
        """``_safe_numeric`` always returns a float, never raises."""
        result = _safe_numeric(value = value)
        assert isinstance(result, float)

    @pytest.mark.unit()
    @given(value=_strategy_any_value, default=st.floats(allow_nan=False, allow_infinity=False))
    @settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_respects_default_for_none_or_empty(
        self,
        value: object,
        default: float,
    ) -> None:
        """``_safe_numeric`` returns *default* for ``None`` or empty string."""
        if value is None or value == "":
            assert _safe_numeric(value = value, default=default) == default

    @pytest.mark.unit()
    @given(amount=_strategy_dollar_integer)
    @settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_integer_roundtrips(self, amount: int) -> None:
        """``_safe_numeric`` on a plain integer string returns the same float."""
        result = _safe_numeric(value = str(amount))
        assert result == float(amount)

    @pytest.mark.unit()
    @given(amount=_strategy_dollar_integer)
    @settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_strips_dollar_sign(self, amount: int) -> None:
        """``_safe_numeric`` on ``$NNN`` returns the numeric value."""
        result = _safe_numeric(value = f"${amount}")
        assert result == float(amount)


# ===========================================================================
# _parse_whole_dollar_amount
# ===========================================================================


class Class_Test_Hypothesis_Parse_Whole_Dollar_Amount:
    """Property tests for ``_parse_whole_dollar_amount``."""

    @pytest.mark.unit()
    @given(value=_strategy_any_value)
    @settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_never_raises(self, value: object) -> None:
        """``_parse_whole_dollar_amount`` never raises for any input."""
        result = _parse_whole_dollar_amount(value = value)
        assert result is None or isinstance(result, int)

    @pytest.mark.unit()
    @given(amount=_strategy_dollar_integer)
    @settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_integer_input_roundtrips(self, amount: int) -> None:
        """``_parse_whole_dollar_amount`` on a non-negative integer returns same value."""
        assert _parse_whole_dollar_amount(value = amount) == amount

    @pytest.mark.unit()
    @given(amount=_strategy_dollar_integer)
    @settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_integer_float_roundtrips(self, amount: int) -> None:
        """``_parse_whole_dollar_amount`` on a float with .0 fraction returns int."""
        result = _parse_whole_dollar_amount(value = float(amount))
        assert result == amount

    @pytest.mark.unit()
    @given(
        integer_part=_strategy_dollar_integer,
        frac=st.integers(min_value=1, max_value=99),
    )
    @settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_float_with_cents_returns_none(
        self,
        integer_part: int,
        frac: int,
    ) -> None:
        """``_parse_whole_dollar_amount`` on a float with non-zero cents returns None."""
        value_float = float(integer_part) + frac / 100.0
        assert _parse_whole_dollar_amount(value = value_float) is None

    @pytest.mark.unit()
    @given(value=st.none())
    @settings(max_examples=10, deadline=None)
    def Test_none_returns_none(self, value: None) -> None:
        """``_parse_whole_dollar_amount(None)`` returns None."""
        assert _parse_whole_dollar_amount(value = value) is None

    @pytest.mark.unit()
    @given(value=st.booleans())
    @settings(max_examples=10, deadline=None)
    def Test_bool_returns_none(self, value: bool) -> None:
        """``_parse_whole_dollar_amount`` on a bool always returns None."""
        assert _parse_whole_dollar_amount(value = value) is None


# ===========================================================================
# _safe_whole_dollar_numeric
# ===========================================================================


class Class_Test_Hypothesis_Safe_Whole_Dollar_Numeric:
    """Property tests for ``_safe_whole_dollar_numeric``."""

    @pytest.mark.unit()
    @given(value=_strategy_any_value)
    @settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_always_returns_float(self, value: object) -> None:
        """``_safe_whole_dollar_numeric`` always returns a float."""
        result = _safe_whole_dollar_numeric(value = value)
        assert isinstance(result, float)

    @pytest.mark.unit()
    @given(amount=_strategy_dollar_integer)
    @settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_non_negative_for_valid_whole_dollars(self, amount: int) -> None:
        """``_safe_whole_dollar_numeric`` is non-negative for valid whole-dollar integers."""
        result = _safe_whole_dollar_numeric(value = amount)
        assert result >= 0.0


# ===========================================================================
# _normalize_phone_number_US
# ===========================================================================


class Class_Test_Hypothesis_Normalize_Phone_Number_US:
    """Property tests for ``_normalize_phone_number_US``."""

    @pytest.mark.unit()
    @given(digits=_strategy_ten_digits)
    @settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_ten_digit_sequence_formats_correctly(self, digits: str) -> None:
        """A bare 10-digit string normalises to ``NNN-NNN-NNNN``."""
        result = _normalize_phone_number_US(value_text = digits)
        assert result == f"{digits[0:3]}-{digits[3:6]}-{digits[6:10]}"

    @pytest.mark.unit()
    @given(digits=_strategy_ten_digits)
    @settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_eleven_digit_1_prefix_strips_country_code(self, digits: str) -> None:
        """An 11-digit string starting with '1' strips the country code."""
        input_str = "1" + digits
        result = _normalize_phone_number_US(value_text = input_str)
        assert result == f"{digits[0:3]}-{digits[3:6]}-{digits[6:10]}"

    @pytest.mark.unit()
    @given(digits=_strategy_ten_digits)
    @settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_hyphenated_input_normalises(self, digits: str) -> None:
        """A string already formatted as NNN-NNN-NNNN normalises correctly."""
        formatted = f"{digits[0:3]}-{digits[3:6]}-{digits[6:10]}"
        result = _normalize_phone_number_US(value_text = formatted)
        assert result == formatted

    @pytest.mark.unit()
    @given(text=st.text(max_size=5))
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_short_input_returns_stripped_original(self, text: str) -> None:
        """A string with fewer than 10 digits returns the stripped original."""
        # Only test when digit count < 10
        digit_count = sum(c.isdigit() for c in text)
        if digit_count < 10:
            result = _normalize_phone_number_US(value_text = text)
            assert result == text.strip()


# ===========================================================================
# _normalize_text_trademark_symbols
# ===========================================================================


class Class_Test_Hypothesis_Normalize_Text_Trademark_Symbols:
    """Property tests for ``_normalize_text_trademark_symbols``."""

    @pytest.mark.unit()
    @given(text=st.text(max_size=80))
    @settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_always_returns_string(self, text: str) -> None:
        """``_normalize_text_trademark_symbols`` always returns a string."""
        result = _normalize_text_trademark_symbols(value_text = text)
        assert isinstance(result, str)

    @pytest.mark.unit()
    @given(text=st.text(max_size=80))
    @settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_idempotent_on_clean_text(self, text: str) -> None:
        """Applying normalisation twice yields the same result as once."""
        first = _normalize_text_trademark_symbols(value_text = text)
        second = _normalize_text_trademark_symbols(value_text = first)
        assert first == second

    @pytest.mark.unit()
    def Test_sm_marker_replaced_by_unicode(self) -> None:
        """ASCII ``(SM)`` is replaced by ``℠``."""
        assert _normalize_text_trademark_symbols(value_text = "Service(SM)") == "Service℠"

    @pytest.mark.unit()
    def Test_tm_marker_replaced_by_unicode(self) -> None:
        """ASCII ``(TM)`` is replaced by ``™``."""
        assert _normalize_text_trademark_symbols(value_text = "Brand(TM)") == "Brand™"

    @pytest.mark.unit()
    def Test_r_marker_replaced_by_unicode(self) -> None:
        """ASCII ``(R)`` is replaced by ``®``."""
        assert _normalize_text_trademark_symbols(value_text = "Product(R)") == "Product®"


# ===========================================================================
# _is_currency_field_name
# ===========================================================================


class Class_Test_Hypothesis_Is_Currency_Field_Name:
    """Property tests for ``_is_currency_field_name``."""

    @pytest.mark.unit()
    @given(name=st.text(max_size=60))
    @settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_always_returns_bool(self, name: str) -> None:
        """``_is_currency_field_name`` always returns a bool."""
        result = _is_currency_field_name(field_name = name)
        assert isinstance(result, bool)

    @pytest.mark.unit()
    @given(
        part_a=_strategy_nonempty_ascii,
        part_b=_strategy_nonempty_ascii,
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_two_part_names_always_false(
        self,
        part_a: str,
        part_b: str,
    ) -> None:
        """Names with only two dot-separated parts always return False."""
        name = f"{part_a}.{part_b}"
        assert _is_currency_field_name(field_name = name) is False

    @pytest.mark.unit()
    @given(name=_strategy_nonempty_ascii)
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_no_dot_names_always_false(self, name: str) -> None:
        """Names without a dot always return False."""
        assert _is_currency_field_name(field_name = name) is False


# ===========================================================================
# build_checkbox_fields_by_section
# ===========================================================================


class Class_Test_Hypothesis_Build_Checkbox_Fields_By_Section:
    """Property tests for ``build_checkbox_fields_by_section``."""

    @pytest.mark.unit()
    def Test_returns_dict(self) -> None:
        """``build_checkbox_fields_by_section`` returns a dict."""
        result = build_checkbox_fields_by_section()
        assert isinstance(result, dict)

    @pytest.mark.unit()
    def Test_all_values_are_sets(self) -> None:
        """Every value in the returned dict is a set."""
        result = build_checkbox_fields_by_section()
        for section_title, field_set in result.items():
            assert isinstance(field_set, set), f"Section '{section_title}' value is not a set"

    @pytest.mark.unit()
    def Test_all_keys_are_strings(self) -> None:
        """Every key in the returned dict is a string."""
        result = build_checkbox_fields_by_section()
        for section_title in result:
            assert isinstance(section_title, str)

    @pytest.mark.unit()
    def Test_is_deterministic(self) -> None:
        """``build_checkbox_fields_by_section`` returns the same result on repeated calls."""
        assert build_checkbox_fields_by_section() == build_checkbox_fields_by_section()


# ===========================================================================
# _validate_choice_field
# ===========================================================================


class Class_Test_Hypothesis_Validate_Choice_Field:
    """Property tests for ``_validate_choice_field``."""

    @pytest.mark.unit()
    @given(
        choices=_strategy_valid_choices,
        value=_strategy_nonempty_ascii,
    )
    @settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_valid_value_produces_no_warning(
        self,
        choices: list[str],
        value: str,
    ) -> None:
        """A value that is in *choices* (case-insensitive) produces no warning."""
        section = {"field": value.lower()}
        warnings_list: list[str] = []
        lower_choices = [c.lower() for c in choices]
        if value.lower() in lower_choices:
            _validate_choice_field(section = section, field_key = "field", valid_choices = choices, client_role = "client_primary", warnings_list = warnings_list)
            assert len(warnings_list) == 0

    @pytest.mark.unit()
    @given(choices=_strategy_valid_choices)
    @settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_none_value_produces_no_warning(self, choices: list[str]) -> None:
        """A None field value produces no warning."""
        section: dict = {"field": None}
        warnings_list: list[str] = []
        _validate_choice_field(section = section, field_key = "field", valid_choices = choices, client_role = "client_primary", warnings_list = warnings_list)
        assert len(warnings_list) == 0

    @pytest.mark.unit()
    @given(choices=_strategy_valid_choices)
    @settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_empty_string_produces_no_warning(self, choices: list[str]) -> None:
        """An empty string field value produces no warning."""
        section: dict = {"field": ""}
        warnings_list: list[str] = []
        _validate_choice_field(section = section, field_key = "field", valid_choices = choices, client_role = "client_primary", warnings_list = warnings_list)
        assert len(warnings_list) == 0

    @pytest.mark.unit()
    @given(choices=_strategy_valid_choices)
    @settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_invalid_value_produces_exactly_one_warning(self, choices: list[str]) -> None:
        """A value definitely not in *choices* appends exactly one warning."""
        section: dict = {"field": "ZZZNOTINLIST999"}
        lower_choices = [c.lower() for c in choices]
        if "zzznotinlist999" not in lower_choices:
            warnings_list: list[str] = []
            _validate_choice_field(section = section, field_key = "field", valid_choices = choices, client_role = "client_primary", warnings_list = warnings_list)
            assert len(warnings_list) == 1


# ===========================================================================
# _validate_numeric_range
# ===========================================================================


class Class_Test_Hypothesis_Validate_Numeric_Range:
    """Property tests for ``_validate_numeric_range``."""

    @pytest.mark.unit()
    @given(
        min_val=st.floats(min_value=0, max_value=50, allow_nan=False, allow_infinity=False),
        max_val=st.floats(min_value=51, max_value=200, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_none_value_produces_no_warning(
        self,
        min_val: float,
        max_val: float,
    ) -> None:
        """A None field value produces no warning."""
        section: dict = {"field": None}
        warnings_list: list[str] = []
        _validate_numeric_range(section = section, field_key = "field", min_val = min_val, max_val = max_val, client_role = "client_primary", warnings_list = warnings_list)
        assert len(warnings_list) == 0

    @pytest.mark.unit()
    @given(
        min_val=st.floats(min_value=0, max_value=50, allow_nan=False, allow_infinity=False),
        max_val=st.floats(min_value=51, max_value=200, allow_nan=False, allow_infinity=False),
        in_range_val=st.floats(min_value=0, max_value=50, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_in_range_value_produces_no_warning(
        self,
        min_val: float,
        max_val: float,
        in_range_val: float,
    ) -> None:
        """A value in [min_val, max_val] produces no warning."""
        value = min_val + (in_range_val / 100.0) * (max_val - min_val)
        section: dict = {"field": str(value)}
        warnings_list: list[str] = []
        _validate_numeric_range(section = section, field_key = "field", min_val = min_val, max_val = max_val, client_role = "client_primary", warnings_list = warnings_list)
        assert len(warnings_list) == 0

    @pytest.mark.unit()
    @given(
        min_val=st.floats(min_value=10, max_value=50, allow_nan=False, allow_infinity=False),
        max_val=st.floats(min_value=51, max_value=200, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_below_min_produces_warning(
        self,
        min_val: float,
        max_val: float,
    ) -> None:
        """A value below min_val produces a warning."""
        value = min_val - 1.0
        section: dict = {"field": str(value)}
        warnings_list: list[str] = []
        _validate_numeric_range(section = section, field_key = "field", min_val = min_val, max_val = max_val, client_role = "client_primary", warnings_list = warnings_list)
        assert len(warnings_list) == 1

    @pytest.mark.unit()
    @given(
        min_val=st.floats(min_value=0, max_value=50, allow_nan=False, allow_infinity=False),
        max_val=st.floats(min_value=51, max_value=200, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_above_max_produces_warning(
        self,
        min_val: float,
        max_val: float,
    ) -> None:
        """A value above max_val produces a warning."""
        value = max_val + 1.0
        section: dict = {"field": str(value)}
        warnings_list: list[str] = []
        _validate_numeric_range(section = section, field_key = "field", min_val = min_val, max_val = max_val, client_role = "client_primary", warnings_list = warnings_list)
        assert len(warnings_list) == 1

    @pytest.mark.unit()
    @given(
        min_val=st.floats(min_value=0, max_value=50, allow_nan=False, allow_infinity=False),
        max_val=st.floats(min_value=51, max_value=200, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_non_numeric_produces_warning(
        self,
        min_val: float,
        max_val: float,
    ) -> None:
        """A non-numeric string produces exactly one warning."""
        section: dict = {"field": "not_a_number"}
        warnings_list: list[str] = []
        _validate_numeric_range(section = section, field_key = "field", min_val = min_val, max_val = max_val, client_role = "client_primary", warnings_list = warnings_list)
        assert len(warnings_list) == 1


# ===========================================================================
# validate_extracted_client_data
# ===========================================================================


class Class_Test_Hypothesis_Validate_Extracted_Client_Data:
    """Property tests for ``validate_extracted_client_data``."""

    @pytest.mark.unit()
    @given(extracted=st.dictionaries(st.text(max_size=20), st.none(), max_size=3))
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_always_returns_tuple_for_any_dict(
        self,
        extracted: dict,
    ) -> None:
        """``validate_extracted_client_data`` returns a 2-tuple for any dict."""
        result = validate_extracted_client_data(extracted_data = extracted)
        assert isinstance(result, tuple)
        assert len(result) == 2
        is_valid, warnings_list = result
        assert isinstance(is_valid, bool)
        assert isinstance(warnings_list, list)

    @pytest.mark.unit()
    @given(extracted=st.dictionaries(st.text(max_size=20), st.none(), max_size=3))
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_is_valid_matches_empty_warnings(
        self,
        extracted: dict,
    ) -> None:
        """is_valid == True iff warnings is empty."""
        is_valid, warnings_list = validate_extracted_client_data(extracted_data = extracted)
        assert is_valid == (len(warnings_list) == 0)

    @pytest.mark.unit()
    def Test_empty_dict_is_valid(self) -> None:
        """An empty extracted dict has no fields to fail — it is valid."""
        is_valid, warnings_list = validate_extracted_client_data(extracted_data = {})
        assert is_valid is True
        assert warnings_list == []

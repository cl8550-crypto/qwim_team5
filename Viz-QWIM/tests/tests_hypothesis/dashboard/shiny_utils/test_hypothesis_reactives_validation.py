"""Hypothesis (property-based) tests for reactives_validation module.

Tests property invariants for:
- validate_data_utils_parameter
- validate_reactives_shiny_structure
- validate_reactive_key_access
- validate_category_name
- REQUIRED_CATEGORIES constant
"""

from __future__ import annotations

from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.dashboard.shiny_utils.reactives_validation import (
    REQUIRED_CATEGORIES,
    validate_category_name,
    validate_data_utils_parameter,
    validate_reactive_key_access,
    validate_reactives_shiny_structure,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_valid_reactives() -> dict[str, Any]:
    """Build a minimal valid reactives_shiny dictionary."""
    return {category: {} for category in REQUIRED_CATEGORIES}


_st_nonempty_str = st.text(
    alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd")),
    min_size=1,
    max_size=30,
)

_st_category_name = st.sampled_from(REQUIRED_CATEGORIES)


# ===========================================================================
# Class_Test_Hypothesis_Validate_Category_Name
# ===========================================================================


class Class_Test_Hypothesis_Validate_Category_Name:
    """Property tests for validate_category_name."""

    @pytest.mark.unit()
    @given(name=_st_nonempty_str)
    @settings(max_examples=200)
    def Test_arbitrary_string_returns_false_if_not_required(
        self,
        name: str,
    ) -> None:
        """Arbitrary non-empty strings not in REQUIRED_CATEGORIES return (False, non-empty msg)."""
        if name in REQUIRED_CATEGORIES:
            return
        assume_not_blank = name.strip()
        if not assume_not_blank:
            return
        is_valid, msg = validate_category_name(category_name=name)
        assert is_valid is False
        assert isinstance(msg, str)
        assert len(msg) > 0

    @pytest.mark.unit()
    @given(
        blank=st.one_of(
            st.just(""),
            st.just("   "),
            st.just("\t"),
            st.just("\n"),
        )
    )
    @settings(max_examples=200)
    def Test_empty_or_whitespace_returns_false(
        self,
        blank: str,
    ) -> None:
        """Empty or whitespace-only strings must return (False, non-empty error message)."""
        is_valid, msg = validate_category_name(category_name=blank)
        assert is_valid is False
        assert isinstance(msg, str)
        assert len(msg) > 0

    @pytest.mark.unit()
    @given(
        non_str=st.one_of(
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.lists(st.integers(), min_size=0, max_size=3),
        )
    )
    @settings(max_examples=200)
    def Test_non_string_returns_false(
        self,
        non_str: Any,
    ) -> None:
        """Non-string inputs must return (False, non-empty error message)."""
        is_valid, msg = validate_category_name(category_name=non_str)
        assert is_valid is False
        assert len(msg) > 0

    @pytest.mark.unit()
    def Test_none_returns_false(self) -> None:
        """None must return (False, non-empty error message)."""
        is_valid, msg = validate_category_name(category_name=None)
        assert is_valid is False
        assert len(msg) > 0

    @pytest.mark.unit()
    @given(name=_st_category_name)
    @settings(max_examples=200)
    def Test_required_category_names_are_valid(
        self,
        name: str,
    ) -> None:
        """Every REQUIRED_CATEGORIES entry must pass validate_category_name."""
        is_valid, _ = validate_category_name(category_name=name)
        assert is_valid is True


# ===========================================================================
# Class_Test_Hypothesis_Validate_Data_Utils_Parameter
# ===========================================================================


class Class_Test_Hypothesis_Validate_Data_Utils_Parameter:
    """Property tests for validate_data_utils_parameter."""

    @pytest.mark.unit()
    @given(
        data_utils=st.dictionaries(
            keys=_st_nonempty_str,
            values=st.one_of(st.integers(), st.text(min_size=0, max_size=20)),
            min_size=0,
            max_size=5,
        )
    )
    @settings(max_examples=200)
    def Test_dict_returns_true(
        self,
        data_utils: dict,
    ) -> None:
        """Any dict input must return (True, '')."""
        is_valid, msg = validate_data_utils_parameter(data_utils=data_utils)
        assert is_valid is True
        assert msg == ""

    @pytest.mark.unit()
    def Test_none_returns_false(self) -> None:
        """None must return (False, non-empty message)."""
        is_valid, msg = validate_data_utils_parameter(data_utils=None)
        assert is_valid is False
        assert len(msg) > 0

    @pytest.mark.unit()
    @given(
        non_dict=st.one_of(
            st.text(min_size=0, max_size=20),
            st.integers(),
            st.lists(st.integers(), min_size=0, max_size=3),
        )
    )
    @settings(max_examples=200)
    def Test_non_dict_returns_false(
        self,
        non_dict: Any,
    ) -> None:
        """Non-dict, non-None inputs must return (False, message)."""
        is_valid, msg = validate_data_utils_parameter(data_utils=non_dict)
        assert is_valid is False
        assert len(msg) > 0


# ===========================================================================
# Class_Test_Hypothesis_Validate_Reactives_Shiny_Structure
# ===========================================================================


class Class_Test_Hypothesis_Validate_Reactives_Shiny_Structure:
    """Property tests for validate_reactives_shiny_structure."""

    @pytest.mark.unit()
    def Test_valid_structure_returns_true(self) -> None:
        """A dictionary with all required category keys must return (True, '')."""
        reactives = _build_valid_reactives()
        is_valid, msg = validate_reactives_shiny_structure(reactives_shiny=reactives)
        assert is_valid is True
        assert msg == ""

    @pytest.mark.unit()
    def Test_none_returns_false(self) -> None:
        """None must return (False, message)."""
        is_valid, msg = validate_reactives_shiny_structure(reactives_shiny=None)
        assert is_valid is False
        assert len(msg) > 0

    @pytest.mark.unit()
    @given(
        non_dict=st.one_of(
            st.text(min_size=0, max_size=10),
            st.integers(),
            st.lists(st.integers(), max_size=3),
        )
    )
    @settings(max_examples=200)
    def Test_non_dict_returns_false(
        self,
        non_dict: Any,
    ) -> None:
        """Non-dict inputs must return (False, message)."""
        is_valid, _ = validate_reactives_shiny_structure(reactives_shiny=non_dict)
        assert is_valid is False

    @pytest.mark.unit()
    @given(
        missing_key=st.sampled_from(
            [cat for cat in REQUIRED_CATEGORIES if cat != "Advisor_Info"]
        )
    )
    @settings(max_examples=200)
    def Test_missing_required_category_returns_false(
        self,
        missing_key: str,
    ) -> None:
        """Removing any required category (except Advisor_Info) must return (False, message)."""
        reactives = _build_valid_reactives()
        del reactives[missing_key]
        is_valid, msg = validate_reactives_shiny_structure(reactives_shiny=reactives)
        assert is_valid is False
        assert len(msg) > 0

    @pytest.mark.unit()
    @given(
        bad_category=st.sampled_from(
            [cat for cat in REQUIRED_CATEGORIES if cat != "Advisor_Info"]
        )
    )
    @settings(max_examples=200)
    def Test_non_dict_category_value_returns_false(
        self,
        bad_category: str,
    ) -> None:
        """A required category with a non-dict value must return (False, message)."""
        reactives = _build_valid_reactives()
        reactives[bad_category] = "not_a_dict"  # type: ignore[assignment]
        is_valid, msg = validate_reactives_shiny_structure(reactives_shiny=reactives)
        assert is_valid is False
        assert len(msg) > 0


# ===========================================================================
# Class_Test_Hypothesis_Validate_Reactive_Key_Access
# ===========================================================================


class Class_Test_Hypothesis_Validate_Reactive_Key_Access:
    """Property tests for validate_reactive_key_access."""

    @pytest.mark.unit()
    @given(
        key=_st_nonempty_str,
        extra_keys=st.lists(_st_nonempty_str, min_size=0, max_size=3),
    )
    @settings(max_examples=200)
    def Test_present_key_returns_true(
        self,
        key: str,
        extra_keys: list[str],
    ) -> None:
        """A key that exists in the category dict must return (True, '')."""
        if not key.strip():
            return
        category_dict = {key: "value"}
        for extra_key in extra_keys:
            if extra_key.strip():
                category_dict[extra_key] = "extra"
        is_valid, msg = validate_reactive_key_access(
            category_dict=category_dict,
            key_name=key,
            category_name="Test_Category",
        )
        assert is_valid is True
        assert msg == ""

    @pytest.mark.unit()
    @given(key=_st_nonempty_str)
    @settings(max_examples=200)
    def Test_missing_key_returns_false(
        self,
        key: str,
    ) -> None:
        """A key that does NOT exist must return (False, message)."""
        if not key.strip():
            return
        category_dict = {"other_key": "value"}
        if key in category_dict:
            return  # Skip coincidence
        is_valid, msg = validate_reactive_key_access(
            category_dict=category_dict,
            key_name=key,
            category_name="Test_Category",
        )
        assert is_valid is False
        assert len(msg) > 0

    @pytest.mark.unit()
    def Test_none_category_dict_returns_false(self) -> None:
        """None category_dict must return (False, message)."""
        is_valid, msg = validate_reactive_key_access(
            category_dict=None,
            key_name="some_key",
            category_name="Test_Category",
        )
        assert is_valid is False

    @pytest.mark.unit()
    def Test_none_key_name_returns_false(self) -> None:
        """None key_name must return (False, message)."""
        is_valid, msg = validate_reactive_key_access(
            category_dict={"key": "val"},
            key_name=None,
            category_name="Test_Category",
        )
        assert is_valid is False

    @pytest.mark.unit()
    @given(
        blank=st.one_of(st.just(""), st.just("  "), st.just("\t"))
    )
    @settings(max_examples=200)
    def Test_empty_key_name_returns_false(
        self,
        blank: str,
    ) -> None:
        """Empty or whitespace-only key_name must return (False, message)."""
        is_valid, msg = validate_reactive_key_access(
            category_dict={"key": "val"},
            key_name=blank,
            category_name="Test_Category",
        )
        assert is_valid is False

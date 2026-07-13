"""Hypothesis (property-based) tests for utils_reporting module.

Tests property invariants for:
- validate_data_clients_in_reactives
- validate_client_level_name
- validate_client_data_category_name
- VALID_CLIENT_LEVELS, VALID_CLIENT_DATA_CATEGORIES_* constants
"""

from __future__ import annotations

from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.dashboard.shiny_utils.utils_reporting import (
    VALID_CLIENT_DATA_CATEGORIES_COMBINED,
    VALID_CLIENT_DATA_CATEGORIES_PER_CLIENT,
    VALID_CLIENT_LEVELS,
    validate_client_data_category_name,
    validate_client_level_name,
    validate_data_clients_in_reactives,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ALL_VALID_CATEGORIES = VALID_CLIENT_DATA_CATEGORIES_PER_CLIENT | VALID_CLIENT_DATA_CATEGORIES_COMBINED

_REQUIRED_DATA_CLIENTS_SUB_LEVELS = ["Client_Primary", "Client_Partner", "Clients_Combined"]


def _build_valid_reactives() -> dict[str, Any]:
    """Build a minimal valid reactives_shiny dict with Data_Clients structure."""
    return {
        "Data_Clients": {
            "Single_Or_Couple": "Single",
            "Client_Primary": {},
            "Client_Partner": {},
            "Clients_Combined": {},
        }
    }


_st_nonempty_str = st.text(
    alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd"), whitelist_characters=("_",)),
    min_size=1,
    max_size=25,
).filter(lambda val: val.strip())

_st_valid_client_level = st.sampled_from(sorted(VALID_CLIENT_LEVELS))
_st_valid_category_per_client = st.sampled_from(sorted(VALID_CLIENT_DATA_CATEGORIES_PER_CLIENT))
_st_valid_category_combined = st.sampled_from(sorted(VALID_CLIENT_DATA_CATEGORIES_COMBINED))


# ===========================================================================
# Class_Test_Hypothesis_Validate_Data_Clients_In_Reactives
# ===========================================================================


class Class_Test_Hypothesis_Validate_Data_Clients_In_Reactives:
    """Property tests for validate_data_clients_in_reactives."""

    @pytest.mark.unit()
    def Test_valid_structure_returns_true(self) -> None:
        """Valid reactives with all required keys must return (True, '')."""
        reactives = _build_valid_reactives()
        is_valid, msg = validate_data_clients_in_reactives(reactives_shiny=reactives)
        assert is_valid is True
        assert msg == ""

    @pytest.mark.unit()
    def Test_none_returns_false(self) -> None:
        """None must return (False, non-empty message)."""
        is_valid, msg = validate_data_clients_in_reactives(reactives_shiny=None)
        assert is_valid is False
        assert len(msg) > 0

    @pytest.mark.unit()
    @given(
        non_dict=st.one_of(
            st.integers(),
            st.text(min_size=0, max_size=10),
            st.lists(st.integers(), min_size=0, max_size=3),
        )
    )
    @settings(max_examples=200)
    def Test_non_dict_returns_false(
        self,
        non_dict: Any,
    ) -> None:
        """Non-dict reactives must return (False, message)."""
        is_valid, _ = validate_data_clients_in_reactives(reactives_shiny=non_dict)
        assert is_valid is False

    @pytest.mark.unit()
    def Test_missing_data_clients_key_returns_false(self) -> None:
        """Dict without 'Data_Clients' key must return (False, message)."""
        reactives = {"Other_Key": {}}
        is_valid, msg = validate_data_clients_in_reactives(reactives_shiny=reactives)
        assert is_valid is False
        assert len(msg) > 0

    @pytest.mark.unit()
    @given(
        missing_sub=st.sampled_from(_REQUIRED_DATA_CLIENTS_SUB_LEVELS),
    )
    @settings(max_examples=200)
    def Test_missing_sub_level_returns_false(
        self,
        missing_sub: str,
    ) -> None:
        """Removing any required sub-level from Data_Clients must return (False, message)."""
        reactives = _build_valid_reactives()
        del reactives["Data_Clients"][missing_sub]
        is_valid, msg = validate_data_clients_in_reactives(reactives_shiny=reactives)
        assert is_valid is False
        assert len(msg) > 0

    @pytest.mark.unit()
    @given(
        bad_sub=st.sampled_from(_REQUIRED_DATA_CLIENTS_SUB_LEVELS),
    )
    @settings(max_examples=200)
    def Test_non_dict_sub_level_returns_false(
        self,
        bad_sub: str,
    ) -> None:
        """A required sub-level with non-dict value must return (False, message)."""
        reactives = _build_valid_reactives()
        reactives["Data_Clients"][bad_sub] = "not_a_dict"  # type: ignore[assignment]
        is_valid, msg = validate_data_clients_in_reactives(reactives_shiny=reactives)
        assert is_valid is False
        assert len(msg) > 0

    @pytest.mark.unit()
    def Test_missing_single_or_couple_key_returns_false(self) -> None:
        """Missing 'Single_Or_Couple' key must return (False, message)."""
        reactives = _build_valid_reactives()
        del reactives["Data_Clients"]["Single_Or_Couple"]
        is_valid, msg = validate_data_clients_in_reactives(reactives_shiny=reactives)
        assert is_valid is False
        assert len(msg) > 0


# ===========================================================================
# Class_Test_Hypothesis_Validate_Client_Level_Name
# ===========================================================================


class Class_Test_Hypothesis_Validate_Client_Level_Name:
    """Property tests for validate_client_level_name."""

    @pytest.mark.unit()
    @given(level=_st_valid_client_level)
    @settings(max_examples=200)
    def Test_valid_level_returns_true(
        self,
        level: str,
    ) -> None:
        """Every member of VALID_CLIENT_LEVELS must return (True, '')."""
        is_valid, msg = validate_client_level_name(client_level=level)
        assert is_valid is True
        assert msg == ""

    @pytest.mark.unit()
    def Test_none_returns_false(self) -> None:
        """None must return (False, message)."""
        is_valid, msg = validate_client_level_name(client_level=None)
        assert is_valid is False
        assert len(msg) > 0

    @pytest.mark.unit()
    @given(
        blank=st.one_of(st.just(""), st.just("   "), st.just("\t")),
    )
    @settings(max_examples=200)
    def Test_empty_string_returns_false(
        self,
        blank: str,
    ) -> None:
        """Empty or whitespace strings must return (False, message)."""
        is_valid, msg = validate_client_level_name(client_level=blank)
        assert is_valid is False
        assert len(msg) > 0

    @pytest.mark.unit()
    @given(
        bad_level=_st_nonempty_str.filter(lambda val: val not in VALID_CLIENT_LEVELS)
    )
    @settings(max_examples=200)
    def Test_invalid_level_name_returns_false(
        self,
        bad_level: str,
    ) -> None:
        """Any string not in VALID_CLIENT_LEVELS must return (False, message)."""
        is_valid, msg = validate_client_level_name(client_level=bad_level)
        assert is_valid is False
        assert len(msg) > 0

    @pytest.mark.unit()
    @given(
        non_str=st.one_of(
            st.integers(),
            st.lists(st.integers(), min_size=0, max_size=2),
        )
    )
    @settings(max_examples=200)
    def Test_non_string_returns_false(
        self,
        non_str: Any,
    ) -> None:
        """Non-string inputs must return (False, message)."""
        is_valid, _ = validate_client_level_name(client_level=non_str)
        assert is_valid is False


# ===========================================================================
# Class_Test_Hypothesis_Validate_Client_Data_Category_Name
# ===========================================================================


class Class_Test_Hypothesis_Validate_Client_Data_Category_Name:
    """Property tests for validate_client_data_category_name."""

    @pytest.mark.unit()
    @given(
        category=_st_valid_category_per_client,
        level=st.sampled_from(["Client_Primary", "Client_Partner"]),
    )
    @settings(max_examples=200)
    def Test_per_client_category_valid_for_individual_levels(
        self,
        category: str,
        level: str,
    ) -> None:
        """Any category from VALID_CLIENT_DATA_CATEGORIES_PER_CLIENT must be valid for individual levels."""
        is_valid, msg = validate_client_data_category_name(
            data_category=category,
            client_level=level,
        )
        assert is_valid is True
        assert msg == ""

    @pytest.mark.unit()
    @given(category=_st_valid_category_combined)
    @settings(max_examples=200)
    def Test_combined_category_valid_for_clients_combined(
        self,
        category: str,
    ) -> None:
        """Any category from VALID_CLIENT_DATA_CATEGORIES_COMBINED must be valid for Clients_Combined."""
        is_valid, msg = validate_client_data_category_name(
            data_category=category,
            client_level="Clients_Combined",
        )
        assert is_valid is True
        assert msg == ""

    @pytest.mark.unit()
    def Test_personal_info_invalid_for_clients_combined(self) -> None:
        """'Personal_Info' must NOT be valid for Clients_Combined."""
        is_valid, msg = validate_client_data_category_name(
            data_category="Personal_Info",
            client_level="Clients_Combined",
        )
        assert is_valid is False
        assert len(msg) > 0

    @pytest.mark.unit()
    def Test_none_category_returns_false(self) -> None:
        """None data_category must return (False, message)."""
        is_valid, msg = validate_client_data_category_name(data_category=None)
        assert is_valid is False
        assert len(msg) > 0

    @pytest.mark.unit()
    @given(
        blank=st.one_of(st.just(""), st.just("   ")),
    )
    @settings(max_examples=200)
    def Test_empty_category_returns_false(
        self,
        blank: str,
    ) -> None:
        """Empty or whitespace data_category must return (False, message)."""
        is_valid, _ = validate_client_data_category_name(data_category=blank)
        assert is_valid is False

    @pytest.mark.unit()
    @given(
        bad_category=_st_nonempty_str.filter(lambda val: val not in _ALL_VALID_CATEGORIES)
    )
    @settings(max_examples=200)
    def Test_unknown_category_returns_false_for_individual_levels(
        self,
        bad_category: str,
    ) -> None:
        """A category not in any valid set must return (False, message)."""
        is_valid, _ = validate_client_data_category_name(
            data_category=bad_category,
            client_level="Client_Primary",
        )
        assert is_valid is False

    @pytest.mark.unit()
    def Test_valid_category_without_client_level_returns_true(self) -> None:
        """A valid category with no client_level=None uses the full set and must return True."""
        for cat in _ALL_VALID_CATEGORIES:
            is_valid, msg = validate_client_data_category_name(
                data_category=cat,
                client_level=None,
            )
            assert is_valid is True, f"Expected True for category '{cat}', got: {msg}"

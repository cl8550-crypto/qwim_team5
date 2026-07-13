"""Hypothesis (property-based) tests for src.num_methods.scenarios.scenarios_base.

Tests cover:
- ``Scenario_Data_Type`` enum — membership and string values
- ``Frequency_Time_Series`` enum — membership and integer values
- ``Scenarios_Base`` constructor validation — exercised via
  ``Scenarios_Distribution`` (the abstract base cannot be instantiated
  directly).
"""

from __future__ import annotations

import pytest

from hypothesis import given, settings
from hypothesis import strategies as st


try:
    from src.num_methods.scenarios.scenarios_base import (
        Frequency_Time_Series,
        Scenario_Data_Type,
    )
    from src.num_methods.scenarios.scenarios_distrib import Scenarios_Distribution

    MODULE_IMPORT_AVAILABLE = True
except ImportError:
    MODULE_IMPORT_AVAILABLE = False


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Scenario_Data_Type_Enum
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Scenario_Data_Type_Enum:
    """Tests for the Scenario_Data_Type enum."""

    @pytest.mark.unit()
    @given(member=st.sampled_from(list(Scenario_Data_Type)) if MODULE_IMPORT_AVAILABLE else st.none())
    @settings(max_examples=20)
    def Test_every_member_has_non_empty_string_value(self, member: Scenario_Data_Type) -> None:
        """Every Scenario_Data_Type member has a non-empty string value."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not importable")
        assert isinstance(member.value, str)
        assert len(member.value) > 0

    @pytest.mark.unit()
    def Test_all_four_data_types_present(self) -> None:
        """All four documented data types are present."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not importable")
        expected = {"PRICE", "RETURN_ARITHMETIC", "RETURN_LOG", "INDEX_LEVEL"}
        actual = {m.name for m in Scenario_Data_Type}
        assert expected == actual

    @pytest.mark.unit()
    @given(member=st.sampled_from(list(Scenario_Data_Type)) if MODULE_IMPORT_AVAILABLE else st.none())
    @settings(max_examples=20)
    def Test_value_is_unique_per_member(self, member: Scenario_Data_Type) -> None:
        """Each Scenario_Data_Type value uniquely identifies a member."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not importable")
        found = [m for m in Scenario_Data_Type if m.value == member.value]
        assert len(found) == 1


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Frequency_Time_Series_Enum
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Frequency_Time_Series_Enum:
    """Tests for the Frequency_Time_Series enum."""

    @pytest.mark.unit()
    @given(member=st.sampled_from(list(Frequency_Time_Series)) if MODULE_IMPORT_AVAILABLE else st.none())
    @settings(max_examples=10)
    def Test_every_member_has_positive_int_value(self, member: Frequency_Time_Series) -> None:
        """Every Frequency_Time_Series member has a positive integer value."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not importable")
        assert isinstance(member.value, int)
        assert member.value > 0

    @pytest.mark.unit()
    def Test_all_five_frequencies_present(self) -> None:
        """All five documented frequencies are present."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not importable")
        expected = {"DAILY", "WEEKLY", "MONTHLY", "QUARTERLY", "ANNUAL"}
        actual = {m.name for m in Frequency_Time_Series}
        assert expected == actual

    @pytest.mark.unit()
    def Test_daily_is_252(self) -> None:
        """DAILY frequency value is 252 (trading days per year)."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not importable")
        assert Frequency_Time_Series.DAILY.value == 252

    @pytest.mark.unit()
    @given(member=st.sampled_from(list(Frequency_Time_Series)) if MODULE_IMPORT_AVAILABLE else st.none())
    @settings(max_examples=10)
    def Test_value_is_unique_per_member(self, member: Frequency_Time_Series) -> None:
        """Each Frequency_Time_Series value uniquely identifies a member."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not importable")
        found = [m for m in Frequency_Time_Series if m.value == member.value]
        assert len(found) == 1


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Scenarios_Base_Validation
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Scenarios_Base_Validation:
    """Tests for Scenarios_Base constructor validation via Scenarios_Distribution.

    Scenarios_Base is abstract; its validation logic is reached through
    any concrete subclass.
    """

    @pytest.mark.unit()
    @given(num_components=st.integers(min_value=1, max_value=5))
    @settings(max_examples=20)
    def Test_valid_construction_stores_num_components(self, num_components: int) -> None:
        """Constructor with K unique names stores m_num_components == K."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not importable")
        names = [f"Asset_{i}" for i in range(num_components)]
        scenario = Scenarios_Distribution(names_components=names, num_days=5)
        assert scenario.m_num_components == num_components

    @pytest.mark.unit()
    @given(num_components=st.integers(min_value=1, max_value=5))
    @settings(max_examples=20)
    def Test_valid_construction_stores_component_names(self, num_components: int) -> None:
        """Constructor stores component names as a list equal to input."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not importable")
        names = [f"Comp_{i}" for i in range(num_components)]
        scenario = Scenarios_Distribution(names_components=names, num_days=5)
        assert scenario.m_names_components == names

    @pytest.mark.unit()
    def Test_empty_names_raises_validation_error(self) -> None:
        """Empty names_components raises Exception_Validation_Input."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not importable")
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )
        with pytest.raises(Exception_Validation_Input):
            Scenarios_Distribution(names_components=[], num_days=5)

    @pytest.mark.unit()
    def Test_duplicate_names_raises_validation_error(self) -> None:
        """Duplicate component names raise Exception_Validation_Input."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not importable")
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )
        with pytest.raises(Exception_Validation_Input):
            Scenarios_Distribution(names_components=["A", "A", "B"], num_days=5)

    @pytest.mark.unit()
    @given(num_scenarios=st.integers(min_value=1, max_value=10))
    @settings(max_examples=15)
    def Test_valid_num_scenarios_is_stored(self, num_scenarios: int) -> None:
        """Valid positive num_scenarios is stored as m_num_scenarios."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not importable")
        scenario = Scenarios_Distribution(
            names_components=["X", "Y"],
            num_scenarios=num_scenarios,
            num_days=5,
        )
        assert scenario.m_num_scenarios == num_scenarios

    @pytest.mark.unit()
    def Test_zero_num_scenarios_raises_validation_error(self) -> None:
        """num_scenarios=0 raises Exception_Validation_Input."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not importable")
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )
        with pytest.raises(Exception_Validation_Input):
            Scenarios_Distribution(names_components=["X", "Y"], num_scenarios=0, num_days=5)

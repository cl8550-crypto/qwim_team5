"""Hypothesis (property-based) tests for utils_data_financial Enum classes.

Tests cover invariants for all three Enum classes:
- ``Expected_Returns_Estimator_Type``: membership, classmethod lists, coverage
- ``Prior_Estimator_Type``: membership, classmethod lists, coverage
- ``Distribution_Estimator_Type``: membership, classmethod lists, coverage

Key invariants tested:
- Every enum member has a truthy string name and value
- Every member returned by any classmethod is a valid enum member
- No classmethod list contains duplicates
- Union of all category classmethods covers all enum members
"""

from __future__ import annotations

import pytest

from hypothesis import given, settings
from hypothesis import strategies as st

from src.utils.data_utils.utils_data_financial import (
    Distribution_Estimator_Type,
    Expected_Returns_Estimator_Type,
    Prior_Estimator_Type,
)


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Expected_Returns_Estimator_Type
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Expected_Returns_Estimator_Type:
    """Property-based tests for Expected_Returns_Estimator_Type enum."""

    @pytest.mark.unit()
    @given(member=st.sampled_from(list(Expected_Returns_Estimator_Type)))
    @settings(max_examples=100)
    def Test_member_has_truthy_name_and_value(
        self, member: Expected_Returns_Estimator_Type
    ) -> None:
        """Every member has a non-empty string name and value."""
        assert isinstance(member.name, str)
        assert len(member.name) > 0
        assert isinstance(member.value, str)
        assert len(member.value) > 0

    @pytest.mark.unit()
    @given(member=st.sampled_from(list(Expected_Returns_Estimator_Type)))
    @settings(max_examples=100)
    def Test_member_name_equals_value(
        self, member: Expected_Returns_Estimator_Type
    ) -> None:
        """Every member's name equals its value (UPPERCASE convention)."""
        assert member.name == member.value

    @pytest.mark.unit()
    def Test_get_historical_methods_are_valid_members(self) -> None:
        """get_historical_methods returns only valid enum members."""
        all_members = set(Expected_Returns_Estimator_Type)
        for m in Expected_Returns_Estimator_Type.get_historical_methods():
            assert m in all_members

    @pytest.mark.unit()
    def Test_get_historical_methods_no_duplicates(self) -> None:
        """get_historical_methods contains no duplicate members."""
        methods = Expected_Returns_Estimator_Type.get_historical_methods()
        assert len(methods) == len(set(methods))

    @pytest.mark.unit()
    def Test_get_model_based_methods_are_valid_members(self) -> None:
        """get_model_based_methods returns only valid enum members."""
        all_members = set(Expected_Returns_Estimator_Type)
        for m in Expected_Returns_Estimator_Type.get_model_based_methods():
            assert m in all_members

    @pytest.mark.unit()
    def Test_get_model_based_methods_no_duplicates(self) -> None:
        """get_model_based_methods contains no duplicate members."""
        methods = Expected_Returns_Estimator_Type.get_model_based_methods()
        assert len(methods) == len(set(methods))

    @pytest.mark.unit()
    def Test_get_distribution_based_methods_are_valid_members(self) -> None:
        """get_distribution_based_methods returns only valid enum members."""
        all_members = set(Expected_Returns_Estimator_Type)
        for m in Expected_Returns_Estimator_Type.get_distribution_based_methods():
            assert m in all_members

    @pytest.mark.unit()
    def Test_get_robust_methods_are_valid_members(self) -> None:
        """get_robust_methods returns only valid enum members."""
        all_members = set(Expected_Returns_Estimator_Type)
        for m in Expected_Returns_Estimator_Type.get_robust_methods():
            assert m in all_members

    @pytest.mark.unit()
    def Test_all_categories_cover_all_members(self) -> None:
        """Union of all category lists covers all enum members."""
        all_members = set(Expected_Returns_Estimator_Type)
        covered = (
            set(Expected_Returns_Estimator_Type.get_historical_methods())
            | set(Expected_Returns_Estimator_Type.get_model_based_methods())
            | set(Expected_Returns_Estimator_Type.get_distribution_based_methods())
        )
        assert all_members == covered

    @pytest.mark.unit()
    @given(member=st.sampled_from(list(Expected_Returns_Estimator_Type)))
    @settings(max_examples=100)
    def Test_member_in_at_least_one_category(
        self, member: Expected_Returns_Estimator_Type
    ) -> None:
        """Every enum member appears in at least one category classmethod."""
        all_categories = (
            Expected_Returns_Estimator_Type.get_historical_methods()
            + Expected_Returns_Estimator_Type.get_model_based_methods()
            + Expected_Returns_Estimator_Type.get_distribution_based_methods()
        )
        assert member in all_categories


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Prior_Estimator_Type
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Prior_Estimator_Type:
    """Property-based tests for Prior_Estimator_Type enum."""

    @pytest.mark.unit()
    @given(member=st.sampled_from(list(Prior_Estimator_Type)))
    @settings(max_examples=100)
    def Test_member_has_truthy_name_and_value(
        self, member: Prior_Estimator_Type
    ) -> None:
        """Every member has a non-empty string name and value."""
        assert isinstance(member.name, str)
        assert len(member.name) > 0
        assert isinstance(member.value, str)
        assert len(member.value) > 0

    @pytest.mark.unit()
    @given(member=st.sampled_from(list(Prior_Estimator_Type)))
    @settings(max_examples=100)
    def Test_member_name_equals_value(
        self, member: Prior_Estimator_Type
    ) -> None:
        """Every member's name equals its value (UPPERCASE convention)."""
        assert member.name == member.value

    @pytest.mark.unit()
    def Test_get_data_driven_are_valid_members(self) -> None:
        """get_data_driven returns only valid enum members."""
        all_members = set(Prior_Estimator_Type)
        for m in Prior_Estimator_Type.get_data_driven():
            assert m in all_members

    @pytest.mark.unit()
    def Test_get_equilibrium_based_are_valid_members(self) -> None:
        """get_equilibrium_based returns only valid enum members."""
        all_members = set(Prior_Estimator_Type)
        for m in Prior_Estimator_Type.get_equilibrium_based():
            assert m in all_members

    @pytest.mark.unit()
    def Test_get_factor_based_are_valid_members(self) -> None:
        """get_factor_based returns only valid enum members."""
        all_members = set(Prior_Estimator_Type)
        for m in Prior_Estimator_Type.get_factor_based():
            assert m in all_members

    @pytest.mark.unit()
    def Test_get_scenario_based_no_duplicates(self) -> None:
        """get_scenario_based contains no duplicate members."""
        methods = Prior_Estimator_Type.get_scenario_based()
        assert len(methods) == len(set(methods))

    @pytest.mark.unit()
    def Test_get_probabilistic_are_valid_members(self) -> None:
        """get_probabilistic returns only valid enum members."""
        all_members = set(Prior_Estimator_Type)
        for m in Prior_Estimator_Type.get_probabilistic():
            assert m in all_members

    @pytest.mark.unit()
    def Test_get_bayesian_methods_are_valid_members(self) -> None:
        """get_bayesian_methods returns only valid enum members."""
        all_members = set(Prior_Estimator_Type)
        for m in Prior_Estimator_Type.get_bayesian_methods():
            assert m in all_members

    @pytest.mark.unit()
    def Test_get_view_incorporation_methods_are_valid_members(self) -> None:
        """get_view_incorporation_methods returns only valid enum members."""
        all_members = set(Prior_Estimator_Type)
        for m in Prior_Estimator_Type.get_view_incorporation_methods():
            assert m in all_members

    @pytest.mark.unit()
    def Test_all_categories_cover_all_members(self) -> None:
        """Union of all non-overlapping category lists covers all members."""
        all_members = set(Prior_Estimator_Type)
        covered = (
            set(Prior_Estimator_Type.get_data_driven())
            | set(Prior_Estimator_Type.get_equilibrium_based())
            | set(Prior_Estimator_Type.get_factor_based())
            | set(Prior_Estimator_Type.get_scenario_based())
            | set(Prior_Estimator_Type.get_probabilistic())
        )
        assert all_members == covered

    @pytest.mark.unit()
    @given(member=st.sampled_from(list(Prior_Estimator_Type)))
    @settings(max_examples=100)
    def Test_member_in_at_least_one_primary_category(
        self, member: Prior_Estimator_Type
    ) -> None:
        """Every enum member appears in at least one primary category classmethod."""
        all_primary = (
            Prior_Estimator_Type.get_data_driven()
            + Prior_Estimator_Type.get_equilibrium_based()
            + Prior_Estimator_Type.get_factor_based()
            + Prior_Estimator_Type.get_scenario_based()
            + Prior_Estimator_Type.get_probabilistic()
        )
        assert member in all_primary


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Distribution_Estimator_Type
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Distribution_Estimator_Type:
    """Property-based tests for Distribution_Estimator_Type enum."""

    @pytest.mark.unit()
    @given(member=st.sampled_from(list(Distribution_Estimator_Type)))
    @settings(max_examples=100)
    def Test_member_has_truthy_name_and_value(
        self, member: Distribution_Estimator_Type
    ) -> None:
        """Every member has a non-empty string name and value."""
        assert isinstance(member.name, str)
        assert len(member.name) > 0
        assert isinstance(member.value, str)
        assert len(member.value) > 0

    @pytest.mark.unit()
    @given(member=st.sampled_from(list(Distribution_Estimator_Type)))
    @settings(max_examples=100)
    def Test_member_name_equals_value(
        self, member: Distribution_Estimator_Type
    ) -> None:
        """Every member's name equals its value (UPPERCASE convention)."""
        assert member.name == member.value

    @pytest.mark.unit()
    def Test_get_univariate_are_valid_members(self) -> None:
        """get_univariate returns only valid enum members."""
        all_members = set(Distribution_Estimator_Type)
        for m in Distribution_Estimator_Type.get_univariate():
            assert m in all_members

    @pytest.mark.unit()
    def Test_get_univariate_no_duplicates(self) -> None:
        """get_univariate contains no duplicate members."""
        methods = Distribution_Estimator_Type.get_univariate()
        assert len(methods) == len(set(methods))

    @pytest.mark.unit()
    def Test_get_bivariate_copulas_are_valid_members(self) -> None:
        """get_bivariate_copulas returns only valid enum members."""
        all_members = set(Distribution_Estimator_Type)
        for m in Distribution_Estimator_Type.get_bivariate_copulas():
            assert m in all_members

    @pytest.mark.unit()
    def Test_get_bivariate_copulas_no_duplicates(self) -> None:
        """get_bivariate_copulas contains no duplicate members."""
        methods = Distribution_Estimator_Type.get_bivariate_copulas()
        assert len(methods) == len(set(methods))

    @pytest.mark.unit()
    def Test_get_multivariate_copulas_are_valid_members(self) -> None:
        """get_multivariate_copulas returns only valid enum members."""
        all_members = set(Distribution_Estimator_Type)
        for m in Distribution_Estimator_Type.get_multivariate_copulas():
            assert m in all_members

    @pytest.mark.unit()
    def Test_get_simulation_ready_are_valid_members(self) -> None:
        """get_simulation_ready returns only valid enum members."""
        all_members = set(Distribution_Estimator_Type)
        for m in Distribution_Estimator_Type.get_simulation_ready():
            assert m in all_members

    @pytest.mark.unit()
    def Test_get_tail_dependent_copulas_are_valid_members(self) -> None:
        """get_tail_dependent_copulas returns only valid enum members."""
        all_members = set(Distribution_Estimator_Type)
        for m in Distribution_Estimator_Type.get_tail_dependent_copulas():
            assert m in all_members

    @pytest.mark.unit()
    def Test_get_archimedean_copulas_are_valid_members(self) -> None:
        """get_archimedean_copulas returns only valid enum members."""
        all_members = set(Distribution_Estimator_Type)
        for m in Distribution_Estimator_Type.get_archimedean_copulas():
            assert m in all_members

    @pytest.mark.unit()
    @given(member=st.sampled_from(list(Distribution_Estimator_Type)))
    @settings(max_examples=100)
    def Test_member_in_at_least_one_top_level_category(
        self, member: Distribution_Estimator_Type
    ) -> None:
        """Every member appears in univariate, bivariate, or multivariate category."""
        all_categories = (
            Distribution_Estimator_Type.get_univariate()
            + Distribution_Estimator_Type.get_bivariate_copulas()
            + Distribution_Estimator_Type.get_multivariate_copulas()
        )
        assert member in all_categories

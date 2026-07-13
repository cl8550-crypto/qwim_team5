"""Integration tests for utils_data_financial enum workflows."""

from __future__ import annotations

import pytest

from src.utils.data_utils.utils_data_financial import (
    Distribution_Estimator_Type,
    Expected_Returns_Estimator_Type,
    Prior_Estimator_Type,
)


class Class_Test_Integration_Utils_Data_Financial:
    """Integration tests for public enum-group relationships."""

    @pytest.mark.integration()
    def Test_Expected_Returns_Robust_Methods_Are_Supported_By_Primary_Groups(self) -> None:
        """Robust expected-return methods stay within the historical/model groups."""
        primary_groups = set(Expected_Returns_Estimator_Type.get_historical_methods()) | set(
            Expected_Returns_Estimator_Type.get_model_based_methods()
        )
        robust_methods = set(Expected_Returns_Estimator_Type.get_robust_methods())

        assert robust_methods <= primary_groups
        assert Expected_Returns_Estimator_Type.FROM_DISTRIBUTION not in robust_methods

    @pytest.mark.integration()
    def Test_Prior_Bayesian_And_View_Incorporation_Methods_Stay_Aligned(self) -> None:
        """Bayesian priors remain aligned with the view-incorporation surface."""
        bayesian_methods = Prior_Estimator_Type.get_bayesian_methods()
        view_methods = Prior_Estimator_Type.get_view_incorporation_methods()
        primary_groups = set(Prior_Estimator_Type.get_data_driven())
        primary_groups |= set(Prior_Estimator_Type.get_equilibrium_based())
        primary_groups |= set(Prior_Estimator_Type.get_factor_based())
        primary_groups |= set(Prior_Estimator_Type.get_scenario_based())
        primary_groups |= set(Prior_Estimator_Type.get_probabilistic())

        assert bayesian_methods == view_methods
        assert set(bayesian_methods) <= primary_groups

    @pytest.mark.integration()
    def Test_Distribution_Simulation_Ready_Members_Map_To_Public_Distribution_Groups(self) -> None:
        """Simulation-ready estimators remain sourced from univariate or copula groups."""
        supported_members = set(Distribution_Estimator_Type.get_univariate()) | set(
            Distribution_Estimator_Type.get_all_copulas()
        )
        simulation_ready = set(Distribution_Estimator_Type.get_simulation_ready())

        assert simulation_ready <= supported_members
        assert (
            Distribution_Estimator_Type.COPULA_MULTIVARIATE_VINE_CONDITIONAL_SAMPLING
            in simulation_ready
        )
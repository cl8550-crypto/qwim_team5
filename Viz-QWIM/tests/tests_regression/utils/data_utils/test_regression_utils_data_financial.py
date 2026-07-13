"""Regression baselines for utils_data_financial enum-group ordering."""

from __future__ import annotations

import pytest

from src.utils.data_utils.utils_data_financial import (
    Distribution_Estimator_Type,
    Expected_Returns_Estimator_Type,
    Prior_Estimator_Type,
)


class Class_Test_Regression_Utils_Data_Financial:
    """Regression baselines for stable enum group composition and ordering."""

    @pytest.mark.regression()
    def Test_Expected_Returns_Group_Order_Baseline(self) -> None:
        """Expected-returns grouping order remains stable."""
        assert Expected_Returns_Estimator_Type.get_historical_methods() == [
            Expected_Returns_Estimator_Type.EMPIRICAL,
            Expected_Returns_Estimator_Type.EXPONENTIALLY_WEIGHTED,
        ]
        assert Expected_Returns_Estimator_Type.get_model_based_methods() == [
            Expected_Returns_Estimator_Type.EQUILIBRIUM,
            Expected_Returns_Estimator_Type.SHRINKAGE,
        ]
        assert Expected_Returns_Estimator_Type.get_distribution_based_methods() == [
            Expected_Returns_Estimator_Type.FROM_DISTRIBUTION,
        ]

    @pytest.mark.regression()
    def Test_Prior_Group_Order_Baseline(self) -> None:
        """Scenario, probabilistic, and Bayesian prior group ordering remains stable."""
        assert Prior_Estimator_Type.get_scenario_based() == [
            Prior_Estimator_Type.SYNTHETIC_DATA_STRESS_TEST,
            Prior_Estimator_Type.SYNTHETIC_DATA_FACTOR_STRESS_TEST,
        ]
        assert Prior_Estimator_Type.get_probabilistic() == [
            Prior_Estimator_Type.ENTROPY_POOLING,
            Prior_Estimator_Type.OPINION_POOLING,
        ]
        assert Prior_Estimator_Type.get_bayesian_methods() == [
            Prior_Estimator_Type.BLACK_LITTERMAN,
            Prior_Estimator_Type.ENTROPY_POOLING,
            Prior_Estimator_Type.OPINION_POOLING,
        ]

    @pytest.mark.regression()
    def Test_Distribution_Group_Order_Baseline(self) -> None:
        """Copula and simulation-ready ordering remains stable."""
        assert Distribution_Estimator_Type.get_all_copulas() == [
            Distribution_Estimator_Type.COPULA_BIVARIATE_GAUSSIAN,
            Distribution_Estimator_Type.COPULA_BIVARIATE_STUDENT_T,
            Distribution_Estimator_Type.COPULA_BIVARIATE_CLAYTON,
            Distribution_Estimator_Type.COPULA_BIVARIATE_GUMBEL,
            Distribution_Estimator_Type.COPULA_BIVARIATE_JOE,
            Distribution_Estimator_Type.COPULA_BIVARIATE_INDEPENDENT,
            Distribution_Estimator_Type.COPULA_MULTIVARIATE_VINE_REGULAR,
            Distribution_Estimator_Type.COPULA_MULTIVARIATE_VINE_CENTERED,
            Distribution_Estimator_Type.COPULA_MULTIVARIATE_VINE_CLUSTERED,
            Distribution_Estimator_Type.COPULA_MULTIVARIATE_VINE_CONDITIONAL_SAMPLING,
        ]
        assert Distribution_Estimator_Type.get_simulation_ready() == [
            Distribution_Estimator_Type.UNIVARIATE_GAUSSIAN,
            Distribution_Estimator_Type.UNIVARIATE_STUDENT_T,
            Distribution_Estimator_Type.COPULA_BIVARIATE_GAUSSIAN,
            Distribution_Estimator_Type.COPULA_BIVARIATE_STUDENT_T,
            Distribution_Estimator_Type.COPULA_MULTIVARIATE_VINE_CONDITIONAL_SAMPLING,
        ]
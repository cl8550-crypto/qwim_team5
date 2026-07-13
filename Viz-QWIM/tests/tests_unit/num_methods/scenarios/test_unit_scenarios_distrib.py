"""Focused unit tests for vectorized lognormal scenario helpers.

Notes
-----
These tests cover the pure helper introduced for lognormal parameter
mapping in ``src.num_methods.scenarios.scenarios_distrib``.
"""

from __future__ import annotations

import numpy as np
import pytest

from src.num_methods.scenarios.scenarios_distrib import (
    Distribution_Type,
    Scenarios_Distribution,
    _calc_lognormal_normal_parameters,
)
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Calculation,
    Exception_Validation_Input,
)


class Class_Test_Lognormal_Normal_Parameters:
    """Unit tests for the vectorized lognormal parameter helper."""

    @pytest.mark.unit()
    def Test_Helper_Matches_Scalar_Mapping(self) -> None:
        """Vectorized helper matches the original scalar mapping.

        Returns
        -------
        None
            The assertions verify the helper output against the scalar
            formula on a small deterministic input.
        """
        # Arrange
        mean_returns = np.array([1.10, 1.05], dtype=np.float64)
        covariance_matrix = np.array(
            [[0.04, 0.01], [0.01, 0.03]],
            dtype=np.float64,
        )

        sigma_expected = np.empty_like(covariance_matrix)
        for idx_row in range(covariance_matrix.shape[0]):
            for idx_col in range(covariance_matrix.shape[1]):
                ratio_value = covariance_matrix[idx_row, idx_col] / (
                    mean_returns[idx_row] * mean_returns[idx_col]
                )
                sigma_expected[idx_row, idx_col] = np.log(1.0 + ratio_value)
        mu_expected = np.log(mean_returns) - 0.5 * np.diag(sigma_expected)

        # Act
        mu_actual, sigma_actual = _calc_lognormal_normal_parameters(
            mean_returns=mean_returns,
            covariance_matrix=covariance_matrix,
        )

        # Assert
        np.testing.assert_allclose(mu_actual, mu_expected, atol=1e-15, rtol=0.0)
        np.testing.assert_allclose(sigma_actual, sigma_expected, atol=1e-15, rtol=0.0)

    @pytest.mark.unit()
    def Test_Helper_Raises_On_Non_Positive_Mean(self) -> None:
        """Non-positive arithmetic means are rejected before mapping.

        Returns
        -------
        None
            The assertion verifies the expected validation exception.
        """
        # Arrange
        mean_returns = np.array([1.10, 0.0], dtype=np.float64)
        covariance_matrix = np.array(
            [[0.04, 0.01], [0.01, 0.03]],
            dtype=np.float64,
        )

        # Act / Assert
        with pytest.raises(Exception_Validation_Input):
            _calc_lognormal_normal_parameters(
                mean_returns=mean_returns,
                covariance_matrix=covariance_matrix,
            )

    @pytest.mark.unit()
    def Test_Helper_Raises_On_Invalid_Lognormal_Ratio(self) -> None:
        """Invalid covariance-to-lognormal mappings raise a calculation error.

        Returns
        -------
        None
            The assertion verifies the expected calculation exception.
        """
        # Arrange
        mean_returns = np.array([1.0, 1.0], dtype=np.float64)
        covariance_matrix = np.array(
            [[0.01, -1.10], [-1.10, 0.01]],
            dtype=np.float64,
        )

        # Act / Assert
        with pytest.raises(Exception_Calculation):
            _calc_lognormal_normal_parameters(
                mean_returns=mean_returns,
                covariance_matrix=covariance_matrix,
            )


class Class_Test_Scenarios_Distribution_Lognormal:
    """Focused lognormal scenario generation regression guards."""

    @pytest.mark.unit()
    def Test_Generate_Lognormal_Produces_Positive_Samples(self) -> None:
        """Lognormal generation keeps output strictly positive.

        Returns
        -------
        None
            The assertions verify the generated frame shape and sample positivity.
        """
        # Arrange
        scenario = Scenarios_Distribution(
            names_components=["Stock", "Bond"],
            distribution_type=Distribution_Type.LOGNORMAL,
            mean_returns=np.array([1.02, 1.01], dtype=np.float64),
            covariance_matrix=np.array(
                [[0.02, 0.005], [0.005, 0.01]],
                dtype=np.float64,
            ),
            num_days=12,
            random_seed=42,
        )

        # Act
        result = scenario.generate()

        # Assert
        assert result.shape == (12, 3)
        assert np.all(result.select(["Stock", "Bond"]).to_numpy() > 0.0)
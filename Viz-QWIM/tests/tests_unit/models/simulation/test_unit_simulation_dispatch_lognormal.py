"""Focused unit tests for lognormal simulation tensor generation.

Notes
-----
These tests isolate the lognormal path exposed via
``src.models.simulation.simulation_dispatch`` so the shared vectorized
mapping remains covered without expanding the large legacy test module.
"""

from __future__ import annotations

import numpy as np
import pytest

from src.models.simulation.simulation_dispatch import (
    _make_rng,
    generate_random_returns_tensor,
)
from src.num_methods.scenarios.scenarios_distrib import Distribution_Type
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Calculation,
)


class Class_Test_Generate_Random_Returns_Tensor_Lognormal:
    """Focused unit tests for the lognormal tensor-generation branch."""

    @pytest.mark.unit()
    def Test_Same_Seed_Produces_Identical_Tensor(self) -> None:
        """Same RNG seed produces identical lognormal tensors.

        Returns
        -------
        None
            The assertions verify deterministic tensor generation.
        """
        # Arrange
        kwargs = {
            "num_days": 7,
            "num_scenarios": 12,
            "num_components": 2,
            "distribution_type": Distribution_Type.LOGNORMAL,
            "mean_returns": np.array([1.002, 1.001], dtype=np.float64),
            "cov_matrix": np.array(
                [[0.0004, 0.0001], [0.0001, 0.0003]],
                dtype=np.float64,
            ),
            "dof": 5.0,
        }

        # Act
        tensor_first = generate_random_returns_tensor(
            **kwargs,
            rng=_make_rng(rng_type = "pcg64", seed = 123),
        )
        tensor_second = generate_random_returns_tensor(
            **kwargs,
            rng=_make_rng(rng_type = "pcg64", seed = 123),
        )

        # Assert
        np.testing.assert_array_equal(tensor_first, tensor_second)

    @pytest.mark.unit()
    def Test_Returns_Stay_Above_Minus_One(self) -> None:
        """Lognormal-return tensors remain strictly above -1.0.

        Returns
        -------
        None
            The assertion verifies the hard lower bound implied by
            ``exp(normal_sample) - 1``.
        """
        # Arrange
        rng = _make_rng(rng_type = "pcg64", seed = 7)

        # Act
        tensor = generate_random_returns_tensor(
            num_days=5,
            num_scenarios=8,
            num_components=2,
            distribution_type=Distribution_Type.LOGNORMAL,
            mean_returns=np.array([1.001, 1.003], dtype=np.float64),
            cov_matrix=np.array(
                [[0.0004, 0.0001], [0.0001, 0.0002]],
                dtype=np.float64,
            ),
            dof=5.0,
            rng=rng,
        )

        # Assert
        assert np.all(tensor > -1.0)

    @pytest.mark.unit()
    def Test_Invalid_Lognormal_Mapping_Raises_Calculation_Error(self) -> None:
        """Invalid covariance mapping raises the project calculation error.

        Returns
        -------
        None
            The assertion verifies the failure path for a non-positive
            lognormal mapping argument.
        """
        # Arrange
        rng = _make_rng(rng_type = "pcg64", seed = 0)

        # Act / Assert
        with pytest.raises(Exception_Calculation):
            generate_random_returns_tensor(
                num_days=3,
                num_scenarios=4,
                num_components=2,
                distribution_type=Distribution_Type.LOGNORMAL,
                mean_returns=np.array([1.0, 1.0], dtype=np.float64),
                cov_matrix=np.array(
                    [[0.0001, -1.1], [-1.1, 0.0001]],
                    dtype=np.float64,
                ),
                dof=5.0,
                rng=rng,
            )
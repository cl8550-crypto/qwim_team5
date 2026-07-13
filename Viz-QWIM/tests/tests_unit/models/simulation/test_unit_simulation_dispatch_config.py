"""Focused unit tests for simulation-dispatch configuration validation.

Notes
-----
The public simulation-dispatch facade re-exports
``Simulation_Run_Config`` from ``_sim_config``. These tests keep the
validation contract local without extending the large legacy unit file.
"""

from __future__ import annotations

import datetime as dt

import numpy as np
import pytest
from pydantic import ValidationError

from src.models.simulation.simulation_dispatch import Simulation_Run_Config
from src.num_methods.scenarios.scenarios_distrib import Distribution_Type


class Class_Test_Simulation_Run_Config_Validation:
    """Focused validation tests for ``Simulation_Run_Config``."""

    @pytest.mark.unit()
    def Test_Unexpected_Field_Is_Rejected(self) -> None:
        """Unexpected keyword arguments are rejected by the config model.

        Returns
        -------
        None
            The assertion verifies the Pydantic validation boundary.
        """
        # Arrange / Act / Assert
        with pytest.raises(ValidationError):
            Simulation_Run_Config(
                names_components=["Asset_A", "Asset_B"],
                weights=np.array([0.5, 0.5]),
                distribution_type=Distribution_Type.NORMAL,
                mean_returns=np.array([0.0003, 0.0002]),
                covariance_matrix=np.array(
                    [[0.0004, 0.0001], [0.0001, 0.0003]],
                ),
                initial_value=100.0,
                num_scenarios=50,
                num_days=5,
                start_date=dt.date(2026, 1, 2),
                random_seed=42,
                degrees_of_freedom=5.0,
                rng_type="pcg64",
                unexpected_setting=True,
            )
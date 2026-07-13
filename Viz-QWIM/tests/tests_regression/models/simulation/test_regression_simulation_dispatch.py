"""Regression tests for the multi-backend simulation dispatch module.

These tests reuse the canonical seeded Normal-distribution baseline already
stored for ``Simulation_Standard``. The dispatch layer's ``standard`` backend
must remain numerically identical to that historical baseline, and every
parallel backend must remain bit-identical to the ``standard`` dispatch run.
"""

from __future__ import annotations

import numpy as np
import polars as pl
import pytest

from src.models.simulation.simulation_dispatch import (
    COMPUTATION_TYPES_SIMULATION,
    Simulation_Run_Config,
    dispatch_simulation_run,
)
from src.num_methods.scenarios.scenarios_distrib import Distribution_Type
from tests.tests_regression.models.simulation.conftest import (
    ASSETS,
    COV_MATRIX,
    EQUAL_WEIGHTS,
    INITIAL_VALUE,
    MEAN_RETURNS,
    NUM_DAYS,
    NUM_SCENARIOS,
    RANDOM_SEED,
    START_DATE,
    load_baseline,
)


def _build_config_simulation_run_regression_dispatch() -> Simulation_Run_Config:
    """Return the canonical dispatch config aligned with regression baselines."""
    return Simulation_Run_Config(
        names_components=ASSETS,
        weights=EQUAL_WEIGHTS,
        distribution_type=Distribution_Type.NORMAL,  # type: ignore[reportArgumentType]
        mean_returns=MEAN_RETURNS,
        covariance_matrix=COV_MATRIX,
        initial_value=INITIAL_VALUE,
        num_scenarios=NUM_SCENARIOS,
        num_days=NUM_DAYS,
        start_date=START_DATE,
        random_seed=RANDOM_SEED,
        degrees_of_freedom=5.0,
        rng_type="pcg64",
    )


def _assert_results_dispatch_match_baseline(
    results_df_current: pl.DataFrame,
    baseline_name: str,
) -> None:
    """Assert an exact match against a stored Parquet baseline."""
    results_df_baseline = load_baseline(baseline_name)

    assert results_df_current.columns == results_df_baseline.columns
    assert results_df_current.schema == results_df_baseline.schema
    assert results_df_current.shape == results_df_baseline.shape
    assert results_df_current["Date"].to_list() == results_df_baseline["Date"].to_list()

    columns_scenario = [
        column_name
        for column_name in results_df_baseline.columns
        if column_name.startswith("Scenario_")
    ]
    for column_name in columns_scenario:
        np.testing.assert_array_equal(
            results_df_current[column_name].to_numpy(),
            results_df_baseline[column_name].to_numpy(),
            err_msg=f"Dispatch regression mismatch in {column_name}",
        )


@pytest.fixture(scope="module")
def config_simulation_run_dispatch() -> Simulation_Run_Config:
    """Return a fixed dispatch config used across all regression tests."""
    return _build_config_simulation_run_regression_dispatch()


@pytest.fixture(scope="module")
def results_df_dispatch_standard(
    config_simulation_run_dispatch: Simulation_Run_Config,
) -> pl.DataFrame:
    """Run the standard dispatch backend once for reuse in backend checks."""
    results_df_dispatch, elapsed_seconds = dispatch_simulation_run(
        computation_type = "standard",
        config = config_simulation_run_dispatch,
    )
    assert elapsed_seconds >= 0.0
    return results_df_dispatch


@pytest.mark.regression()
class Class_Test_Regression_Simulation_Dispatch:
    """Regression coverage for dispatch baseline stability and backend parity."""

    def Test_Regression_Dispatch_Standard_Matches_Canonical_Baseline(
        self,
        results_df_dispatch_standard: pl.DataFrame,
    ) -> None:
        """The standard backend must match the canonical seeded Normal baseline."""
        _assert_results_dispatch_match_baseline(
            results_df_dispatch_standard,
            "sim_normal_full_results",
        )

    @pytest.mark.parametrize(
        "backend",
        COMPUTATION_TYPES_SIMULATION[1:],
    )
    def Test_Regression_Dispatch_Backend_Matches_Standard(
        self,
        config_simulation_run_dispatch: Simulation_Run_Config,
        results_df_dispatch_standard: pl.DataFrame,
        backend: str,
    ) -> None:
        """Each non-standard backend must remain bit-identical to standard."""
        results_df_backend, elapsed_seconds = dispatch_simulation_run(
            computation_type = backend,
            config = config_simulation_run_dispatch,
        )

        assert elapsed_seconds >= 0.0
        assert results_df_backend.columns == results_df_dispatch_standard.columns
        assert results_df_backend.schema == results_df_dispatch_standard.schema
        assert results_df_backend["Date"].to_list() == results_df_dispatch_standard["Date"].to_list()

        columns_scenario = [
            column_name
            for column_name in results_df_dispatch_standard.columns
            if column_name.startswith("Scenario_")
        ]
        for column_name in columns_scenario:
            np.testing.assert_array_equal(
                results_df_backend[column_name].to_numpy(),
                results_df_dispatch_standard[column_name].to_numpy(),
                err_msg=(
                    f"Backend {backend} diverged from standard in {column_name}"
                ),
            )
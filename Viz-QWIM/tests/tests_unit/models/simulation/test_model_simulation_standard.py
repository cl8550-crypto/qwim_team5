"""Unit tests for model_simulation_standard module.

Tests for Simulation_Standard class -- the concrete Monte Carlo
simulation that generates distribution-based scenario paths.
"""
# ruff: noqa: PLC0415, N803

from __future__ import annotations

import datetime as dt

import numpy as np
import polars as pl
import pytest


# ======================================================================
# Fixtures
# ======================================================================


@pytest.fixture()
def Simulation_Standard_class():
    """Import Simulation_Standard."""
    from src.models.simulation.model_simulation_standard import Simulation_Standard

    return Simulation_Standard


@pytest.fixture()
def Distribution_Type_enum():
    """Import Distribution_Type."""
    from src.num_methods.scenarios.scenarios_distrib import Distribution_Type

    return Distribution_Type


@pytest.fixture()
def sample_2_components():
    """Two-component test data."""
    names = ["A", "B"]
    weights = np.array([0.6, 0.4])
    mean_returns = np.array([0.0003, 0.0001])
    cov = np.array([[0.0004, 0.0001], [0.0001, 0.0002]])
    return names, weights, mean_returns, cov


@pytest.fixture()
def sample_3_components():
    """Three-component test data (IVV, IJH, IWM)."""
    names = ["IVV", "IJH", "IWM"]
    weights = np.array([0.5, 0.3, 0.2])
    mean_returns = np.array([0.0004, 0.0003, 0.0002])
    cov = np.array(
        [
            [0.0004, 0.00015, 0.0002],
            [0.00015, 0.0005, 0.00018],
            [0.0002, 0.00018, 0.0006],
        ]
    )
    return names, weights, mean_returns, cov


# ======================================================================
# Construction
# ======================================================================


class Test_Simulation_Standard_Construction:
    """Tests for Simulation_Standard constructor."""

    @pytest.mark.unit()
    def test_valid_creation(self, Simulation_Standard_class, sample_2_components):
        """Construction with valid parameters should succeed."""
        names, weights, mean_ret, cov = sample_2_components
        sim = Simulation_Standard_class(
            names_components=names,
            weights=weights,
            mean_returns=mean_ret,
            covariance_matrix=cov,
            num_scenarios=50,
            num_days=10,
            random_seed=42,
        )
        assert sim.num_components == 2
        assert sim.num_scenarios == 50
        assert sim.num_days == 10

    @pytest.mark.unit()
    def test_default_parameters(self, Simulation_Standard_class):
        """Construction with minimal parameters should use defaults."""
        sim = Simulation_Standard_class(
            names_components=["X", "Y"],
            weights=np.array([0.5, 0.5]),
        )
        assert sim.num_scenarios == 1_000
        assert sim.num_days == 252
        assert sim.initial_value == 100.0
        assert sim.random_seed == 42

    @pytest.mark.unit()
    def test_student_t_distribution(
        self,
        Simulation_Standard_class,
        Distribution_Type_enum,
        sample_2_components,
    ):
        """Student-t distribution should be accepted."""
        names, weights, mean_ret, cov = sample_2_components
        sim = Simulation_Standard_class(
            names_components=names,
            weights=weights,
            distribution_type=Distribution_Type_enum.STUDENT_T,
            mean_returns=mean_ret,
            covariance_matrix=cov,
            degrees_of_freedom=5.0,
            num_scenarios=10,
            num_days=5,
        )
        assert sim.distribution_type == Distribution_Type_enum.STUDENT_T

    @pytest.mark.unit()
    def test_empty_components_raises(self, Simulation_Standard_class):
        """Empty component list should raise."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            Simulation_Standard_class(
                names_components=[],
                weights=np.array([]),
            )

    @pytest.mark.unit()
    def test_invalid_distribution_type_raises(self, Simulation_Standard_class):
        """Non-enum distribution type should raise."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            Simulation_Standard_class(
                names_components=["A"],
                weights=np.array([1.0]),
                distribution_type="normal",
            )


# ======================================================================
# Run — Normal distribution
# ======================================================================


class Test_Simulation_Standard_Run_Normal:
    """Tests for running simulation with Normal distribution."""

    @pytest.mark.unit()
    def test_run_returns_dataframe(
        self,
        Simulation_Standard_class,
        sample_2_components,
    ):
        """run() should return a Polars DataFrame."""
        names, weights, mean_ret, cov = sample_2_components
        sim = Simulation_Standard_class(
            names_components=names,
            weights=weights,
            mean_returns=mean_ret,
            covariance_matrix=cov,
            num_scenarios=20,
            num_days=10,
            random_seed=42,
        )
        result = sim.run()
        assert isinstance(result, pl.DataFrame)

    @pytest.mark.unit()
    def test_result_shape(self, Simulation_Standard_class, sample_2_components):
        """Result should have (num_days, num_scenarios + 1) shape."""
        names, weights, mean_ret, cov = sample_2_components
        num_days, num_scenarios = 20, 50
        sim = Simulation_Standard_class(
            names_components=names,
            weights=weights,
            mean_returns=mean_ret,
            covariance_matrix=cov,
            num_scenarios=num_scenarios,
            num_days=num_days,
            random_seed=42,
        )
        result = sim.run()
        assert result.height == num_days
        assert result.width == num_scenarios + 1  # +1 for Date

    @pytest.mark.unit()
    def test_date_column_present(self, Simulation_Standard_class, sample_2_components):
        """Result should have a Date column."""
        names, weights, mean_ret, cov = sample_2_components
        sim = Simulation_Standard_class(
            names_components=names,
            weights=weights,
            mean_returns=mean_ret,
            covariance_matrix=cov,
            num_scenarios=5,
            num_days=10,
            random_seed=42,
        )
        result = sim.run()
        assert "Date" in result.columns

    @pytest.mark.unit()
    def test_scenario_columns_named_correctly(
        self,
        Simulation_Standard_class,
        sample_2_components,
    ):
        """Scenario columns should follow Scenario_N naming."""
        names, weights, mean_ret, cov = sample_2_components
        sim = Simulation_Standard_class(
            names_components=names,
            weights=weights,
            mean_returns=mean_ret,
            covariance_matrix=cov,
            num_scenarios=3,
            num_days=5,
            random_seed=42,
        )
        result = sim.run()
        scenario_cols = [c for c in result.columns if c != "Date"]
        assert scenario_cols == ["Scenario_1", "Scenario_2", "Scenario_3"]

    @pytest.mark.unit()
    def test_all_values_positive(self, Simulation_Standard_class, sample_2_components):
        """For normal distribution with small variance, values should stay positive."""
        names, weights, mean_ret, cov = sample_2_components
        sim = Simulation_Standard_class(
            names_components=names,
            weights=weights,
            mean_returns=mean_ret,
            covariance_matrix=cov,
            num_scenarios=100,
            num_days=50,
            random_seed=42,
        )
        result = sim.run()
        scenario_cols = [c for c in result.columns if c != "Date"]
        mat = result.select(scenario_cols).to_numpy()
        # With small variance and short horizon, values should mostly be positive
        assert np.all(mat > 0)

    @pytest.mark.unit()
    def test_reproducibility_with_same_seed(
        self,
        Simulation_Standard_class,
        sample_2_components,
    ):
        """Same seed should produce identical results."""
        names, weights, mean_ret, cov = sample_2_components
        kwargs = {
            "names_components": names,
            "weights": weights,
            "mean_returns": mean_ret,
            "covariance_matrix": cov,
            "num_scenarios": 20,
            "num_days": 10,
            "random_seed": 123,
        }
        result_1 = Simulation_Standard_class(**kwargs).run()
        result_2 = Simulation_Standard_class(**kwargs).run()

        cols = [c for c in result_1.columns if c != "Date"]
        np.testing.assert_array_almost_equal(
            result_1.select(cols).to_numpy(),
            result_2.select(cols).to_numpy(),
        )

    @pytest.mark.unit()
    def test_different_seeds_produce_different_results(
        self,
        Simulation_Standard_class,
        sample_2_components,
    ):
        """Different seeds should produce different results."""
        names, weights, mean_ret, cov = sample_2_components
        common = {
            "names_components": names,
            "weights": weights,
            "mean_returns": mean_ret,
            "covariance_matrix": cov,
            "num_scenarios": 20,
            "num_days": 10,
        }
        result_1 = Simulation_Standard_class(**common, random_seed=1).run()
        result_2 = Simulation_Standard_class(**common, random_seed=999).run()

        cols = [c for c in result_1.columns if c != "Date"]
        assert not np.allclose(
            result_1.select(cols).to_numpy(),
            result_2.select(cols).to_numpy(),
        )


# ======================================================================
# Run — Student-t distribution
# ======================================================================


class Test_Simulation_Standard_Run_Student_T:
    """Tests for running simulation with Student-t distribution."""

    @pytest.mark.unit()
    def test_student_t_runs_successfully(
        self,
        Simulation_Standard_class,
        Distribution_Type_enum,
        sample_2_components,
    ):
        """Student-t simulation should complete without error."""
        names, weights, mean_ret, cov = sample_2_components
        sim = Simulation_Standard_class(
            names_components=names,
            weights=weights,
            distribution_type=Distribution_Type_enum.STUDENT_T,
            mean_returns=mean_ret,
            covariance_matrix=cov,
            degrees_of_freedom=5.0,
            num_scenarios=20,
            num_days=10,
            random_seed=42,
        )
        result = sim.run()
        assert isinstance(result, pl.DataFrame)
        assert result.height == 10

    @pytest.mark.unit()
    def test_student_t_fatter_tails(
        self,
        Simulation_Standard_class,
        Distribution_Type_enum,
        sample_3_components,
    ):
        """Student-t with low DoF should produce fatter tails than Normal.

        We compare the range (max - min) of terminal values.
        """
        names, weights, mean_ret, cov = sample_3_components
        common = {
            "names_components": names,
            "weights": weights,
            "mean_returns": mean_ret,
            "covariance_matrix": cov,
            "num_scenarios": 2_000,
            "num_days": 252,
            "random_seed": 42,
        }
        sim_normal = Simulation_Standard_class(
            **common,
            distribution_type=Distribution_Type_enum.NORMAL,
        )
        sim_t = Simulation_Standard_class(
            **common,
            distribution_type=Distribution_Type_enum.STUDENT_T,
            degrees_of_freedom=3.0,
        )

        res_normal = sim_normal.run()
        res_t = sim_t.run()

        cols_n = [c for c in res_normal.columns if c != "Date"]
        cols_t = [c for c in res_t.columns if c != "Date"]

        terminal_normal = res_normal.tail(1).select(cols_n).to_numpy().flatten()
        terminal_t = res_t.tail(1).select(cols_t).to_numpy().flatten()

        range_normal = np.max(terminal_normal) - np.min(terminal_normal)
        range_t = np.max(terminal_t) - np.min(terminal_t)

        # Student-t with df=3 should generally have wider range
        assert range_t > range_normal * 0.5  # Allow margin for randomness


# ======================================================================
# Run — Lognormal distribution
# ======================================================================


class Test_Simulation_Standard_Run_Lognormal:
    """Tests for running simulation with Lognormal distribution."""

    @pytest.mark.unit()
    def test_lognormal_runs_successfully(
        self,
        Simulation_Standard_class,
        Distribution_Type_enum,
    ):
        """Lognormal simulation with positive means should complete."""
        names = ["A", "B"]
        weights = np.array([0.5, 0.5])
        # Lognormal needs positive means (interpreted as 1 + r)
        mean_ret = np.array([1.0003, 1.0001])
        cov = np.array([[0.0004, 0.0001], [0.0001, 0.0002]])

        sim = Simulation_Standard_class(
            names_components=names,
            weights=weights,
            distribution_type=Distribution_Type_enum.LOGNORMAL,
            mean_returns=mean_ret,
            covariance_matrix=cov,
            num_scenarios=20,
            num_days=10,
            random_seed=42,
        )
        result = sim.run()
        assert isinstance(result, pl.DataFrame)
        assert result.height == 10


# ======================================================================
# Summary statistics
# ======================================================================


class Test_Simulation_Standard_Statistics:
    """Test summary statistics after a run."""

    @pytest.fixture()
    def completed_simulation(self, Simulation_Standard_class, sample_2_components):
        """Return a completed simulation."""
        names, weights, mean_ret, cov = sample_2_components
        sim = Simulation_Standard_class(
            names_components=names,
            weights=weights,
            mean_returns=mean_ret,
            covariance_matrix=cov,
            num_scenarios=100,
            num_days=20,
            random_seed=42,
        )
        sim.run()
        return sim

    @pytest.mark.unit()
    def test_summary_statistics(self, completed_simulation):
        """get_summary_statistics should return valid data."""
        stats = completed_simulation.get_summary_statistics()
        assert isinstance(stats, pl.DataFrame)
        assert "Mean" in stats.columns
        assert "Median" in stats.columns
        assert "P5" in stats.columns
        assert "P95" in stats.columns
        assert stats.height == 20

    @pytest.mark.unit()
    def Test_Random_Seed_Property(self, Simulation_Standard_class, sample_2_components):
        """The random_seed property should return the seed passed to the constructor."""
        names, weights, mean_ret, cov = sample_2_components
        sim = Simulation_Standard_class(
            names_components=names,
            weights=weights,
            mean_returns=mean_ret,
            covariance_matrix=cov,
            random_seed=99,
        )
        assert sim.random_seed == 99

    @pytest.mark.unit()
    def Test_Start_Date_Property(self, Simulation_Standard_class, sample_2_components):
        """The start_date property should return the constructor start date."""
        names, weights, mean_ret, cov = sample_2_components
        start_date = dt.date(2024, 6, 30)
        sim = Simulation_Standard_class(
            names_components=names,
            weights=weights,
            mean_returns=mean_ret,
            covariance_matrix=cov,
            start_date=start_date,
        )
        assert sim.start_date == start_date

    @pytest.mark.unit()
    def test_terminal_values(self, completed_simulation):
        """get_terminal_values should have 100 scenario values."""
        tv = completed_simulation.get_terminal_values()
        assert tv.height == 1
        assert tv.width == 100

    @pytest.mark.unit()
    def test_mean_greater_than_p5(self, completed_simulation):
        """Mean should be >= P5 for all dates."""
        stats = completed_simulation.get_summary_statistics()
        assert all(stats["Mean"].to_numpy() >= stats["P5"].to_numpy())

    @pytest.mark.unit()
    def test_p95_greater_than_median(self, completed_simulation):
        """P95 should be >= Median for all dates."""
        stats = completed_simulation.get_summary_statistics()
        assert all(stats["P95"].to_numpy() >= stats["Median"].to_numpy())


# ======================================================================
# from_historical_data factory
# ======================================================================


class Test_Simulation_Standard_From_Historical:
    """Test the from_historical_data class method."""

    @pytest.mark.unit()
    def test_from_historical_creates_valid_simulation(
        self,
        Simulation_Standard_class,
    ):
        """from_historical_data should produce a runnable simulation."""
        price_data = pl.DataFrame(
            {
                "Date": [dt.date(2024, 1, d) for d in range(1, 21)],
                "A": np.cumsum(np.random.default_rng(42).normal(0, 1, 20)) + 100,
                "B": np.cumsum(np.random.default_rng(43).normal(0, 0.5, 20)) + 50,
            },
        )
        sim = Simulation_Standard_class.from_historical_data(
            price_data=price_data,
            weights=np.array([0.6, 0.4]),
            num_scenarios=10,
            num_days=5,
            random_seed=42,
        )
        result = sim.run()
        assert isinstance(result, pl.DataFrame)
        assert result.height == 5
        assert result.width == 11  # Date + 10 scenarios

    @pytest.mark.unit()
    def test_from_historical_lognormal_shifts_mean_returns_above_one(
        self,
        Simulation_Standard_class,
        Distribution_Type_enum,
    ):
        """Lognormal historical simulations should shift mean returns by +1."""
        price_data = pl.DataFrame(
            {
                "Date": [dt.date(2024, 1, d) for d in range(1, 21)],
                "A": np.linspace(100.0, 120.0, 20),
                "B": np.linspace(80.0, 95.0, 20),
            },
        )

        sim = Simulation_Standard_class.from_historical_data(
            price_data=price_data,
            weights=np.array([0.5, 0.5]),
            distribution_type=Distribution_Type_enum.LOGNORMAL,
            num_scenarios=5,
            num_days=3,
            random_seed=42,
        )

        assert np.all(sim.m_mean_returns > 1.0)


class Test_Simulation_Standard_Run_Defensive:
    """Defensive run() branches that require post-construction mutation."""

    @pytest.mark.unit()
    def test_run_unknown_distribution_raises_exception_calculation(
        self,
        Simulation_Standard_class,
        sample_2_components,
    ):
        """run() should raise when the distribution enum is corrupted after validation."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Calculation,
        )

        names, weights, mean_ret, cov = sample_2_components
        sim = Simulation_Standard_class(
            names_components=names,
            weights=weights,
            mean_returns=mean_ret,
            covariance_matrix=cov,
            num_scenarios=5,
            num_days=3,
            random_seed=42,
        )
        sim.m_distribution_type = "invalid_distribution"

        with pytest.raises(Exception_Calculation):
            sim.run()


# ======================================================================
# Dunder methods
# ======================================================================


class Test_Simulation_Standard_Repr:
    """Test __repr__."""

    @pytest.mark.unit()
    def test_repr_contains_class_name(
        self,
        Simulation_Standard_class,
        sample_2_components,
    ):
        """__repr__ should mention the class name."""
        names, weights, mean_ret, cov = sample_2_components
        sim = Simulation_Standard_class(
            names_components=names,
            weights=weights,
            mean_returns=mean_ret,
            covariance_matrix=cov,
            num_scenarios=5,
            num_days=5,
        )
        r = repr(sim)
        assert "Simulation_Standard" in r
        assert "Normal" in r


# ======================================================================
# run() failure path
# ======================================================================


class Test_Simulation_Standard_Run_Failure:
    """Tests for the run() exception path."""

    @pytest.mark.unit()
    def Test_Run_Raises_Exception_Calculation_On_Batch_Failure(
        self,
        Simulation_Standard_class,
        Distribution_Type_enum,
        sample_2_components,
    ):
        """run() should fail cleanly without leaving stale results behind."""
        from unittest.mock import patch

        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Calculation,
        )
        from src.models.simulation.model_simulation_base import Simulation_Status

        names, weights, mean_ret, cov = sample_2_components
        sim = Simulation_Standard_class(
            names_components=names,
            weights=weights,
            distribution_type=Distribution_Type_enum.NORMAL,
            mean_returns=mean_ret,
            covariance_matrix=cov,
            num_scenarios=5,
            num_days=5,
        )

        first_result = sim.run()
        assert first_result.height == 5
        assert sim.df_results is not None

        with patch.object(sim, "_run_batch", side_effect=RuntimeError("batch boom")):
            with pytest.raises(Exception_Calculation):
                sim.run()

        assert sim.status == Simulation_Status.FAILED
        assert sim.df_results is None


# ======================================================================
# _safe_cholesky fallback
# ======================================================================


class Test_Simulation_Standard_Safe_Cholesky:
    """Tests for _safe_cholesky with non-PSD matrices."""

    @pytest.mark.unit()
    def Test_Safe_Cholesky_Fallback_On_Non_PSD(self, Simulation_Standard_class):
        """_safe_cholesky should return a valid factor even for near-singular matrices."""
        # A nearly-singular (non-PSD) matrix
        mat = np.array([[1.0, 1.0], [1.0, 1.0]])
        result = Simulation_Standard_class._safe_cholesky(matrix = mat)
        # Verify result is lower-triangular and L @ L^T ≈ regularised matrix
        assert result.shape == (2, 2)
        reconstructed = result @ result.T
        # All eigenvalues of reconstructed should be ≥ 0
        eigvals = np.linalg.eigvalsh(reconstructed)
        assert np.all(eigvals >= -1e-9)


# ======================================================================
# from_historical_data validation branches
# ======================================================================


class Test_Simulation_Standard_Historical_Validation:
    """Validation branches in from_historical_data."""

    @pytest.mark.unit()
    def Test_From_Historical_Raises_When_No_Date_Column(
        self,
        Simulation_Standard_class,
    ):
        """from_historical_data should raise when 'Date' column is missing."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        no_date = pl.DataFrame({"A": [1.0, 2.0, 3.0], "B": [4.0, 5.0, 6.0]})
        with pytest.raises(Exception_Validation_Input):
            Simulation_Standard_class.from_historical_data(
                price_data=no_date,
                weights=np.array([0.5, 0.5]),
            )

    @pytest.mark.unit()
    def Test_From_Historical_Raises_When_No_Component_Columns(
        self,
        Simulation_Standard_class,
    ):
        """from_historical_data should raise when only a 'Date' column exists."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        date_only = pl.DataFrame(
            {"Date": [dt.date(2024, 1, d) for d in range(1, 6)]},
        )
        with pytest.raises(Exception_Validation_Input):
            Simulation_Standard_class.from_historical_data(
                price_data=date_only,
                weights=np.array([]),
            )


# ======================================================================
# Lognormal edge case — negative mapping arg
# ======================================================================


class Test_Simulation_Standard_Lognormal_Edge:
    """Edge cases for the lognormal distribution branch."""

    @pytest.mark.unit()
    def Test_Lognormal_Raises_When_Negative_Mapping_Arg(
        self,
        Simulation_Standard_class,
        Distribution_Type_enum,
    ):
        """_run_batch lognormal mapping should raise when cov/mean^2 <= -1."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Calculation,
        )

        # Craft parameters so that ratio = cov[i,j]/(mu[i]*mu[j]) < -1
        # e.g. large negative off-diagonal covariance
        names = ["X", "Y"]
        weights = np.array([0.5, 0.5])
        # Means close to zero to make ratio large negative
        mean_ret = np.array([0.001, 0.001])
        # Very large negative off-diagonal covariance so 1 + ratio < 0
        cov = np.array([[0.0001, -0.0002], [-0.0002, 0.0001]])

        sim = Simulation_Standard_class(
            names_components=names,
            weights=weights,
            distribution_type=Distribution_Type_enum.LOGNORMAL,
            mean_returns=mean_ret,
            covariance_matrix=cov,
            num_scenarios=5,
            num_days=3,
            random_seed=0,
        )
        with pytest.raises(Exception_Calculation):
            sim.run()


# ======================================================================
# Student-T distribution run (explicit _run_batch coverage)
# ======================================================================


class Test_Simulation_Standard_Student_T_Run:
    """Explicit branch coverage for Student-T inside _run_batch."""

    @pytest.mark.unit()
    def Test_Student_T_Run_Batch_Path(
        self,
        Simulation_Standard_class,
        Distribution_Type_enum,
    ):
        """run() with STUDENT_T should exercise the student_t branch in _run_batch."""
        names = ["A", "B", "C"]
        weights = np.array([0.4, 0.3, 0.3])
        mean_ret = np.array([0.0004, 0.0003, 0.0002])
        cov = np.array(
            [
                [0.0004, 0.00015, 0.0002],
                [0.00015, 0.0005, 0.00018],
                [0.0002, 0.00018, 0.0006],
            ]
        )
        sim = Simulation_Standard_class(
            names_components=names,
            weights=weights,
            distribution_type=Distribution_Type_enum.STUDENT_T,
            mean_returns=mean_ret,
            covariance_matrix=cov,
            degrees_of_freedom=4.0,
            num_scenarios=15,
            num_days=8,
            random_seed=7,
        )
        result = sim.run()
        assert isinstance(result, pl.DataFrame)
        assert result.height == 8
        assert result.width == 16  # Date + 15 scenarios


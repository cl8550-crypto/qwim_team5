"""Hypothesis-based tests for simulation sub-modules.

Covers:
- ``_sim_config.Simulation_Run_Config``: field validation
- ``_sim_math._safe_cholesky``: PSD fallback
- ``_sim_math._make_rng``: known BitGenerator types
- ``_sim_math.compute_chunk_indices``: range correctness
- ``_sim_math.compute_portfolio_paths_from_returns_tensor``: shape / value
"""

from __future__ import annotations

import datetime as dt

import numpy as np
import pytest

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from src.models.simulation._sim_config import Simulation_Run_Config
from src.models.simulation._sim_math import (
    _make_rng,
    _safe_cholesky,
    compute_chunk_indices,
    compute_portfolio_paths_from_returns_tensor,
    generate_random_returns_tensor,
)
from src.num_methods.scenarios.scenarios_distrib import Distribution_Type
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _random_pd_matrix(k: int, rng: np.random.Generator) -> np.ndarray:
    """Return a random k×k positive-definite matrix."""
    a = rng.standard_normal((k, k))
    return a @ a.T + np.eye(k) * 0.1


def _default_config(n_assets: int = 2, seed: int = 42) -> Simulation_Run_Config:
    """Return a minimal valid config with *n_assets* components."""
    rng = np.random.default_rng(seed)
    weights = np.ones(n_assets) / n_assets
    cov = _random_pd_matrix(n_assets, rng)
    means = rng.uniform(0.0005, 0.002, n_assets)
    return Simulation_Run_Config(
        names_components=[f"C{i}" for i in range(n_assets)],
        weights=weights,
        distribution_type=Distribution_Type.NORMAL,
        mean_returns=means,
        covariance_matrix=cov,
        num_scenarios=10,
        num_days=20,
        random_seed=seed,
    )


# ===========================================================================
# Tests for Simulation_Run_Config
# ===========================================================================


class Class_Test_Simulation_Run_Config:
    """Hypothesis tests for Simulation_Run_Config construction."""

    @pytest.mark.unit()
    def Test_Default_Values_Applied(self) -> None:
        """Default fields are applied correctly."""
        cfg = _default_config()
        assert cfg.num_scenarios == 10
        assert cfg.num_days == 20
        assert cfg.random_seed == 42
        assert cfg.rng_type == "pcg64"
        assert cfg.initial_value == pytest.approx(100.0)
        assert cfg.degrees_of_freedom == pytest.approx(5.0)

    @pytest.mark.unit()
    def Test_Start_Date_Auto_Set(self) -> None:
        """start_date is auto-set to today if not provided."""
        cfg = _default_config()
        assert isinstance(cfg.start_date, dt.date)
        assert cfg.start_date >= dt.date(2020, 1, 1)

    @pytest.mark.unit()
    def Test_Explicit_Start_Date(self) -> None:
        """Explicit start_date is preserved."""
        d = dt.date(2023, 6, 15)
        cfg = Simulation_Run_Config(
            names_components=["A"],
            weights=np.array([1.0]),
            distribution_type=Distribution_Type.NORMAL,
            mean_returns=np.array([0.001]),
            covariance_matrix=np.array([[0.01]]),
            start_date=d,
        )
        assert cfg.start_date == d

    @pytest.mark.unit()
    @given(
        n=st.integers(min_value=1, max_value=10),
        seed=st.integers(min_value=0, max_value=2**31 - 1),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    def Test_Valid_Config_Constructs(self, n: int, seed: int) -> None:
        """Any valid parameter set constructs a Simulation_Run_Config."""
        cfg = _default_config(n, seed)
        assert len(cfg.names_components) == n
        assert cfg.weights.shape == (n,)

    @pytest.mark.unit()
    def Test_Arbitrary_Types_Allowed(self) -> None:
        """np.ndarray fields are accepted (arbitrary_types_allowed=True)."""
        cfg = _default_config()
        assert isinstance(cfg.weights, np.ndarray)
        assert isinstance(cfg.mean_returns, np.ndarray)
        assert isinstance(cfg.covariance_matrix, np.ndarray)


# ===========================================================================
# Tests for _safe_cholesky
# ===========================================================================


class Class_Test_Safe_Cholesky:
    """Tests for _safe_cholesky."""

    @pytest.mark.unit()
    @given(k=st.integers(min_value=1, max_value=8))
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    def Test_Returns_Lower_Triangular_For_PD_Matrix(self, k: int) -> None:
        """_safe_cholesky returns a lower-triangular matrix for PD input."""
        rng = np.random.default_rng(k)
        m = _random_pd_matrix(k, rng)
        L = _safe_cholesky(matrix = m)
        assert L.shape == (k, k)
        # L @ L.T should reconstruct m
        recon = L @ L.T
        assert np.allclose(recon, m, atol=1e-9)

    @pytest.mark.unit()
    def Test_Fallback_For_Near_Singular_Matrix(self) -> None:
        """_safe_cholesky does not raise for a near-singular PSD matrix."""
        # Rank-1 PSD: nearly singular
        v = np.array([1.0, 0.5, 0.25])
        m = np.outer(v, v)
        L = _safe_cholesky(matrix = m)
        assert L.shape == (3, 3)

    @pytest.mark.unit()
    def Test_Identity_Matrix(self) -> None:
        """Cholesky of identity is identity."""
        L = _safe_cholesky(matrix = np.eye(3))
        assert np.allclose(L, np.eye(3), atol=1e-12)


# ===========================================================================
# Tests for _make_rng
# ===========================================================================


class Class_Test_Make_Rng:
    """Tests for _make_rng."""

    @pytest.mark.unit()
    @given(
        rng_type=st.sampled_from(["pcg64", "mt19937", "philox", "sfc64"]),
        seed=st.integers(min_value=0, max_value=2**31 - 1),
    )
    @settings(max_examples=200)
    def Test_Known_Types_Return_Generator(self, rng_type: str, seed: int) -> None:
        """All four BitGenerator types return a numpy Generator."""
        rng = _make_rng(rng_type = rng_type, seed = seed)
        assert isinstance(rng, np.random.Generator)

    @pytest.mark.unit()
    def Test_Unknown_Type_Raises_Validation_Error(self) -> None:
        """Unknown rng_type values must raise validation errors."""
        with pytest.raises(Exception_Validation_Input, match="rng_type"):
            _make_rng(rng_type = "unknown_type", seed = 0)

    @pytest.mark.unit()
    @given(seed=st.integers(min_value=0, max_value=2**31 - 1))
    @settings(max_examples=200)
    def Test_Same_Seed_Same_Output(self, seed: int) -> None:
        """Same seed produces identical first draw."""
        rng1 = _make_rng(rng_type = "pcg64", seed = seed)
        rng2 = _make_rng(rng_type = "pcg64", seed = seed)
        assert np.array_equal(
            rng1.standard_normal(10),
            rng2.standard_normal(10),
        )


# ===========================================================================
# Tests for compute_chunk_indices
# ===========================================================================


class Class_Test_Compute_Chunk_Indices:
    """Hypothesis tests for compute_chunk_indices."""

    @pytest.mark.unit()
    @given(
        n=st.integers(min_value=1, max_value=1000),
        k=st.integers(min_value=1, max_value=50),
    )
    @settings(max_examples=300, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    def Test_Indices_Cover_All_Scenarios(self, n: int, k: int) -> None:
        """Concatenated ranges cover exactly [0, n)."""
        indices = compute_chunk_indices(num_scenarios = n, num_chunks = k)
        all_indices: list[int] = []
        for s, e in indices:
            all_indices.extend(range(s, e))
        assert all_indices == list(range(n))

    @pytest.mark.unit()
    @given(
        n=st.integers(min_value=1, max_value=500),
        k=st.integers(min_value=1, max_value=50),
    )
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    def Test_Chunk_Count_Bounded_By_Scenarios(self, n: int, k: int) -> None:
        """Number of chunks <= min(n, k)."""
        indices = compute_chunk_indices(num_scenarios = n, num_chunks = k)
        assert len(indices) <= min(n, k)

    @pytest.mark.unit()
    def Test_Zero_Chunks_Raises(self) -> None:
        """num_chunks < 1 raises Exception_Validation_Input."""
        with pytest.raises(Exception_Validation_Input, match="num_chunks"):
            compute_chunk_indices(num_scenarios = 10, num_chunks = 0)

    @pytest.mark.unit()
    def Test_Single_Chunk(self) -> None:
        """One chunk covers entire range."""
        indices = compute_chunk_indices(num_scenarios = 100, num_chunks = 1)
        assert indices == [(0, 100)]

    @pytest.mark.unit()
    def Test_Chunk_Per_Scenario(self) -> None:
        """k >= n gives exactly one chunk per scenario."""
        n = 5
        indices = compute_chunk_indices(num_scenarios = n, num_chunks = 100)
        assert len(indices) == n
        for i, (s, e) in enumerate(indices):
            assert e - s == 1


# ===========================================================================
# Tests for compute_portfolio_paths_from_returns_tensor
# ===========================================================================


class Class_Test_Compute_Portfolio_Paths:
    """Hypothesis tests for compute_portfolio_paths_from_returns_tensor."""

    @pytest.mark.unit()
    @given(
        T=st.integers(min_value=1, max_value=50),
        N=st.integers(min_value=1, max_value=20),
        K=st.integers(min_value=1, max_value=5),
    )
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    def Test_Output_Shape(self, T: int, N: int, K: int) -> None:
        """Output shape is (T, N)."""
        rng = np.random.default_rng(0)
        tensor = rng.uniform(-0.01, 0.01, (T, N, K))
        weights = np.ones(K) / K
        paths = compute_portfolio_paths_from_returns_tensor(returns_tensor = tensor, weights = weights, initial_value = 100.0)
        assert paths.shape == (T, N)

    @pytest.mark.unit()
    def Test_Zero_Returns_Constant_Path(self) -> None:
        """Zero returns produce paths equal to initial_value at every step."""
        T, N, K = 10, 5, 3
        tensor = np.zeros((T, N, K))
        weights = np.ones(K) / K
        paths = compute_portfolio_paths_from_returns_tensor(returns_tensor = tensor, weights = weights, initial_value = 1000.0)
        assert np.allclose(paths, 1000.0)

    @pytest.mark.unit()
    @given(iv=st.floats(min_value=1.0, max_value=1e9, allow_nan=False, allow_infinity=False))
    @settings(max_examples=200)
    def Test_Paths_Proportional_To_Initial_Value(self, iv: float) -> None:
        """Multiplying initial_value by a factor scales all paths by same factor."""
        T, N, K = 5, 4, 2
        rng = np.random.default_rng(99)
        tensor = rng.uniform(-0.005, 0.005, (T, N, K))
        weights = np.array([0.6, 0.4])
        p1 = compute_portfolio_paths_from_returns_tensor(returns_tensor = tensor, weights = weights, initial_value = iv)
        p2 = compute_portfolio_paths_from_returns_tensor(returns_tensor = tensor, weights = weights, initial_value = 1.0)
        assert np.allclose(p1, p2 * iv, rtol=1e-12)


# ===========================================================================
# Tests for generate_random_returns_tensor
# ===========================================================================


class Class_Test_Generate_Returns_Tensor:
    """Tests for generate_random_returns_tensor (Normal distribution only)."""

    @pytest.mark.unit()
    @given(
        T=st.integers(min_value=1, max_value=30),
        N=st.integers(min_value=1, max_value=10),
        K=st.integers(min_value=1, max_value=4),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    def Test_Normal_Output_Shape(self, T: int, N: int, K: int) -> None:
        """generate_random_returns_tensor returns shape (T, N, K) for Normal."""
        rng_gen = np.random.default_rng(0)
        mean = rng_gen.uniform(0.0001, 0.002, K)
        cov = _random_pd_matrix(K, rng_gen)
        rng = _make_rng(rng_type = "pcg64", seed = 0)
        tensor = generate_random_returns_tensor(
            num_days = T, num_scenarios = N, num_components = K, distribution_type = Distribution_Type.NORMAL, mean_returns = mean, cov_matrix = cov, dof = 5.0, rng = rng
        )
        assert tensor.shape == (T, N, K)

    @pytest.mark.unit()
    def Test_Unsupported_Distribution_Raises(self) -> None:
        """Unsupported distribution type raises Exception_Validation_Input."""
        with pytest.raises(Exception_Validation_Input, match="Unsupported distribution"):
            generate_random_returns_tensor(
                num_days = 5, num_scenarios = 3, num_components = 2, distribution_type = "UNKNOWN_DIST", mean_returns = np.zeros(2), cov_matrix = np.eye(2), dof = 5.0,  # type: ignore[arg-type]
                rng = _make_rng(rng_type = "pcg64", seed = 0),
            )

    @pytest.mark.unit()
    @given(seed=st.integers(min_value=0, max_value=2**31 - 1))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    def Test_Determinism(self, seed: int) -> None:
        """Same seed produces identical tensor."""
        K = 2
        rng_gen = np.random.default_rng(99)
        mean = rng_gen.uniform(0.0001, 0.002, K)
        cov = _random_pd_matrix(K, rng_gen)
        rng1 = _make_rng(rng_type = "pcg64", seed = seed)
        rng2 = _make_rng(rng_type = "pcg64", seed = seed)
        t1 = generate_random_returns_tensor(num_days = 10, num_scenarios = 5, num_components = K, distribution_type = Distribution_Type.NORMAL, mean_returns = mean, cov_matrix = cov, dof = 5.0, rng = rng1)
        t2 = generate_random_returns_tensor(num_days = 10, num_scenarios = 5, num_components = K, distribution_type = Distribution_Type.NORMAL, mean_returns = mean, cov_matrix = cov, dof = 5.0, rng = rng2)
        assert np.array_equal(t1, t2)

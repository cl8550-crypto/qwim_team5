"""Pure mathematical helpers for Monte Carlo simulation.

Extracted from ``simulation_dispatch`` to keep each file under 1000 LOC.
All public names are re-exported via ``simulation_dispatch``.

Notes
-----
Functions are defined at module level so they are picklable by joblib.
"""

from __future__ import annotations

import datetime as dt

import numpy as np
import polars as pl

from src.num_methods.rng import create_rng_QWIM
from src.num_methods.scenarios.scenarios_distrib import (
    Distribution_Type,
    _calc_lognormal_normal_parameters,
)
from src.models.simulation._sim_config import SUPPORTED_RNG_TYPES_SIMULATION
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Calculation,
    Exception_Validation_Input,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name = __name__)


# ---------------------------------------------------------------------------
# Low-level numeric helpers
# ---------------------------------------------------------------------------


def _safe_cholesky(*, matrix: np.ndarray) -> np.ndarray:
    """Cholesky with PSD fallback — standalone version for use with joblib."""
    try:
        return np.linalg.cholesky(matrix)
    except np.linalg.LinAlgError:
        eigvals, eigvecs = np.linalg.eigh(matrix)
        eigvals = np.maximum(eigvals, 1e-10)
        psd = eigvecs @ np.diag(eigvals) @ eigvecs.T
        return np.linalg.cholesky(psd)


def _make_rng(*, rng_type: str, seed: int) -> np.random.Generator:
    """Create a NumPy Generator with the specified BitGenerator."""
    return create_rng_QWIM(
        rng_type = rng_type,
        seed = seed,
        supported_rng_types=SUPPORTED_RNG_TYPES_SIMULATION,
    )


# ---------------------------------------------------------------------------
# Tensor generation
# ---------------------------------------------------------------------------


def generate_random_returns_tensor(
    *, num_days: int, num_scenarios: int, num_components: int, distribution_type: Distribution_Type, mean_returns: np.ndarray, cov_matrix: np.ndarray, dof: float, rng: np.random.Generator) -> np.ndarray:
    """Generate a 3-D returns tensor using the specified distribution.

    Parameters
    ----------
    num_days : int
        Simulation horizon *T*.
    num_scenarios : int
        Number of paths *N*.
    num_components : int
        Portfolio components *K*.
    distribution_type : Distribution_Type
        Return-distribution family.
    mean_returns : np.ndarray
        Shape ``(K,)``.
    cov_matrix : np.ndarray
        Shape ``(K, K)``.
    dof : float
        Degrees of freedom (Student-*t* only).
    rng : np.random.Generator
        Pre-seeded generator — caller controls reproducibility.

    Returns
    -------
    np.ndarray
        Returns tensor of shape ``(T, N, K)``.

    Raises
    ------
    Exception_Validation_Input
        For unsupported distribution types.
    Exception_Calculation
        If the lognormal covariance mapping fails (non-positive argument).
    """
    T, N, K = num_days, num_scenarios, num_components

    if distribution_type == Distribution_Type.NORMAL:
        mat_chol = _safe_cholesky(matrix = cov_matrix)
        raw = rng.standard_normal((T, N, K))
        returns_3d: np.ndarray = raw @ mat_chol.T + mean_returns

    elif distribution_type == Distribution_Type.LOGNORMAL:
        mu_ln, sigma_ln = _calc_lognormal_normal_parameters(
            mean_returns=mean_returns,
            covariance_matrix=cov_matrix,
        )
        mat_chol_ln = _safe_cholesky(matrix = sigma_ln)
        raw = rng.standard_normal((T, N, K))
        normal_samples = raw @ mat_chol_ln.T + mu_ln
        returns_3d = np.exp(normal_samples) - 1.0

    elif distribution_type == Distribution_Type.STUDENT_T:
        nu = dof
        scale = (nu - 2.0) / nu * cov_matrix
        mat_chol_t = _safe_cholesky(matrix = scale)
        raw = rng.standard_normal((T, N, K))
        chi2 = rng.chisquare(df=nu, size=(T, N))
        scaling = np.sqrt(chi2 / nu)[..., np.newaxis]  # (T, N, 1)
        returns_3d = mean_returns + (raw @ mat_chol_t.T) / scaling

    else:
        raise Exception_Validation_Input(
            f"Unsupported distribution type: {distribution_type!r}",
            field_name="distribution_type",
            expected_type=Distribution_Type,
            actual_value=distribution_type,
        )

    return returns_3d


def compute_portfolio_paths_from_returns_tensor(
    *, returns_tensor: np.ndarray, weights: np.ndarray, initial_value: float) -> np.ndarray:
    """Compute compounded portfolio-value paths from a returns tensor.

    Parameters
    ----------
    returns_tensor : np.ndarray
        Arithmetic returns of shape ``(T, N, K)``.
    weights : np.ndarray
        Static portfolio weights, shape ``(K,)``.
    initial_value : float
        Starting portfolio value.

    Returns
    -------
    np.ndarray
        Portfolio value paths of shape ``(T, N)``.
    """
    portfolio_returns = returns_tensor @ weights  # (T, N)
    growth_factors = 1.0 + portfolio_returns  # (T, N)
    cumulative_growth = np.cumprod(growth_factors, axis=0)  # (T, N)
    return initial_value * cumulative_growth  # (T, N)


def compute_chunk_indices(*, num_scenarios: int, num_chunks: int) -> list[tuple[int, int]]:
    """Split ``[0, num_scenarios)`` into *num_chunks* non-overlapping ranges.

    Remainder scenarios are distributed one-each to the first chunks.

    Parameters
    ----------
    num_scenarios : int
        Total number of scenarios to split.
    num_chunks : int
        Number of desired chunks (clamped to ``num_scenarios``).

    Returns
    -------
    list[tuple[int, int]]
        List of ``(start, end)`` exclusive-end index pairs.

    Raises
    ------
    Exception_Validation_Input
        If ``num_scenarios`` or ``num_chunks`` is invalid.
    """
    if isinstance(num_scenarios, bool) or not isinstance(num_scenarios, int) or num_scenarios < 1:
        raise Exception_Validation_Input(
            "num_scenarios must be a positive integer (> 0)",
            field_name="num_scenarios",
            expected_type=int,
            actual_value=num_scenarios,
        )

    if num_chunks < 1:
        raise Exception_Validation_Input(
            "num_chunks must be >= 1",
            field_name="num_chunks",
            expected_type=int,
            actual_value=num_chunks,
        )
    effective_chunks = min(num_chunks, num_scenarios)
    base = num_scenarios // effective_chunks
    remainder = num_scenarios % effective_chunks
    indices: list[tuple[int, int]] = []
    start = 0
    for idx in range(effective_chunks):
        end = start + base + (1 if idx < remainder else 0)
        indices.append((start, end))
        start = end
    return indices


def compute_simulation_stats(*, results_df: pl.DataFrame) -> pl.DataFrame:
    """Compute cross-scenario summary statistics per time step.

    Mirrors :meth:`Simulation_Base.get_summary_statistics` without
    requiring an instantiated simulation object.

    Parameters
    ----------
    results_df : pl.DataFrame
        DataFrame with ``Date`` column and ``Scenario_1..N`` columns.

    Returns
    -------
    pl.DataFrame
        Columns: ``Date``, ``Mean``, ``Median``, ``Std``,
        ``P5``, ``P25``, ``P75``, ``P95``, ``Min``, ``Max``.
    """
    scenario_cols = [c for c in results_df.columns if c != "Date"]
    mat = results_df.select(scenario_cols).to_numpy()

    return pl.DataFrame({"Date": results_df["Date"]}).with_columns(
        [
            pl.Series("Mean", np.mean(mat, axis=1).tolist()),
            pl.Series("Median", np.median(mat, axis=1).tolist()),
            pl.Series("Std", np.std(mat, axis=1, ddof=1).tolist()),
            pl.Series("P5", np.percentile(mat, 5, axis=1).tolist()),
            pl.Series("P25", np.percentile(mat, 25, axis=1).tolist()),
            pl.Series("P75", np.percentile(mat, 75, axis=1).tolist()),
            pl.Series("P95", np.percentile(mat, 95, axis=1).tolist()),
            pl.Series("Min", np.min(mat, axis=1).tolist()),
            pl.Series("Max", np.max(mat, axis=1).tolist()),
        ],
    )


def _generate_simulation_dates(*, start_date: dt.date, num_days: int) -> list[dt.date]:
    """Generate *num_days* business dates starting from *start_date*."""
    result: list[dt.date] = []
    current = start_date
    while len(result) < num_days:
        if current.weekday() < 5:  # Mon-Fri
            result.append(current)
        current += dt.timedelta(days=1)
    return result

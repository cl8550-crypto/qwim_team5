r"""Multi-backend Monte Carlo simulation dispatch.

This module provides a backend-agnostic interface for running Monte Carlo
portfolio simulations.  The caller selects a *computation type*
(``"standard"``, ``"asyncio"``, ``"asyncio + anyio"``, ``"trio"``,
``"trio + anyio"``, or ``"joblib"``) and the dispatcher generates one
full random-returns tensor from a single seeded parent stream, slices that
tensor into deterministic scenario chunks on the calling thread, then routes
chunk processing through the requested concurrency primitive.

Determinism guarantee
---------------------
Because every backend consumes slices of the same full seeded tensor, all six
backends consume *identical* numeric data and therefore produce
**bit-identical** results for the same seed.  The :math:`\Delta` rows in the
comparison table will therefore always be exactly ``0``.  This intentionally
serves as a regression-equivalence check: a non-zero :math:`\Delta` would
indicate a logic divergence in one of the backend runners.

Chunking strategy
-----------------
The dispatcher uses one shared chunk layout for tensor slicing so every
backend consumes the same seeded scenario data.  The ``"standard"`` backend
processes one canonical full-width chunk sequentially, while the other
backends process deterministic scenario slices through their concurrency
primitive.

Sub-modules
-----------
* ``_sim_config``   — :class:`Simulation_Run_Config` + public constants.
* ``_sim_math``     — pure tensor/stats helpers (picklable for joblib).
* ``_sim_runners``  — per-backend ``_run_chunks_*`` functions.

Author
------
QWIM Team

Version
-------
0.7.0 (2026-05-10)
"""

from __future__ import annotations

import os
import time

from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from collections.abc import Callable

import numpy as np
import polars as pl
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Calculation,
    Exception_Configuration,
    Exception_Validation_Input,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

from ._sim_config import (
    COMPUTATION_TYPES_SIMULATION,
    COMPUTATION_TYPES_SIMULATION_COMPARE,
    DEFAULT_COMPARE_METRICS,
    Simulation_Run_Config,
)
from ._sim_math import (
    _generate_simulation_dates,
    _make_rng,
    _safe_cholesky,
    compute_chunk_indices,
    compute_portfolio_paths_from_returns_tensor,
    compute_simulation_stats,
    generate_random_returns_tensor,
)
from ._sim_runners import (
    _run_callable_in_new_thread,
    _run_chunks_asyncio,
    _run_chunks_asyncio_anyio,
    _run_chunks_joblib,
    _run_chunks_standard,
    _run_chunks_trio,
    _run_chunks_trio_anyio,
)


_logger = get_logger(name = __name__)


# ---------------------------------------------------------------------------
# Backend dispatch table
# (kept in the facade so patch.object(dispatch_mod, "_BACKEND_RUNNERS") works)
# ---------------------------------------------------------------------------

_BACKEND_RUNNERS: dict[
    str,
    Callable[[list[np.ndarray], np.ndarray, float], list[np.ndarray]],
] = {
    "standard": _run_chunks_standard,
    "asyncio": _run_chunks_asyncio,
    "asyncio + anyio": _run_chunks_asyncio_anyio,
    "trio": _run_chunks_trio,
    "trio + anyio": _run_chunks_trio_anyio,
    "joblib": _run_chunks_joblib,
}


# ---------------------------------------------------------------------------
# Pure helpers for chunk resolution and Δ calculations
# ---------------------------------------------------------------------------


def _resolve_num_chunks(
    *, computation_type: str, num_scenarios: int) -> int:
    """Return the number of parallel chunks for the given backend.

    Parameters
    ----------
    computation_type : str
        Backend key.  ``"standard"`` always uses 1 chunk.
    num_scenarios : int
        Total scenarios to split; upper-bounds the chunk count.

    Returns
    -------
    int
        Number of chunks (>= 1).

    Raises
    ------
    Exception_Validation_Input
        If ``num_scenarios`` is not a positive integer.
    """
    if isinstance(num_scenarios, bool) or not isinstance(num_scenarios, int) or num_scenarios < 1:
        raise Exception_Validation_Input(
            "num_scenarios must be a positive integer (> 0)",
            field_name="num_scenarios",
            expected_type=int,
            actual_value=num_scenarios,
        )

    if computation_type == "standard":
        return 1
    return min(num_scenarios, max(1, (os.cpu_count() or 1) - 1))


def _compute_delta_pair(
    *, value_candidate: float | None, value_standard: float | None) -> tuple[str, str]:
    """Compute formatted (Δ_abs, Δ_rel) strings for a single metric.

    Parameters
    ----------
    value_candidate : float or None
        Metric value for the backend being compared.
    value_standard : float or None
        Metric value for the ``"standard"`` benchmark backend.

    Returns
    -------
    tuple[str, str]
        ``(delta_abs_str, delta_rel_str)`` both ``"N/A"`` when either
        input is ``None`` or non-finite.

    Notes
    -----
    Relative difference rule:

    * ``Δ_rel = Δ_abs / |standard|``  when ``|standard| >= 0.01``.
    * ``Δ_rel = Δ_abs``               when ``|standard| < 0.01``
      (avoids division by near-zero).
    """
    if value_standard is None or value_candidate is None:
        return "N/A", "N/A"
    if not np.isfinite(value_standard) or not np.isfinite(value_candidate):
        return "N/A", "N/A"
    abs_diff = abs(value_candidate - value_standard)
    abs_standard = abs(value_standard)
    rel_diff = abs_diff if abs_standard < 0.01 else abs_diff / abs_standard
    return _format_compare_value(value = abs_diff), _format_compare_value(value = rel_diff)


# ---------------------------------------------------------------------------
# Public dispatch API
# ---------------------------------------------------------------------------


def dispatch_simulation_run(
    *, computation_type: str, config: Simulation_Run_Config, progress_callback: Callable[[str], None] | None = None) -> tuple[pl.DataFrame, float]:
    """Run a Monte Carlo simulation using the specified backend.

    Generates the complete random-returns tensor once (deterministic),
    splits it into chunks, routes chunk processing through the chosen
    concurrency backend, then assembles the full results DataFrame.

    Parameters
    ----------
    computation_type : str
        One of :data:`COMPUTATION_TYPES_SIMULATION`.
    config : Simulation_Run_Config
        All simulation parameters.
    progress_callback : callable, optional
        Called with the *computation_type* string just before the
        backend runner is invoked.

    Returns
    -------
    tuple[pl.DataFrame, float]
        ``(results_df, elapsed_seconds)`` where *results_df* has columns
        ``Date``, ``Scenario_1``, …, ``Scenario_N``.

    Raises
    ------
    Exception_Validation_Input
        If *computation_type* is not a recognised backend name.
    Exception_Calculation
        If the backend runner raises an unhandled error.
    Exception_Configuration
        If a required optional library (trio, anyio, joblib) is missing.
    """
    if computation_type not in _BACKEND_RUNNERS:
        raise Exception_Validation_Input(
            f"Unknown computation_type: {computation_type!r}. "
            f"Must be one of {COMPUTATION_TYPES_SIMULATION}",
            field_name="computation_type",
            expected_type=str,
            actual_value=computation_type,
        )

    runner = _BACKEND_RUNNERS[computation_type]
    num_tensor_chunks = _resolve_num_chunks(computation_type = computation_type, num_scenarios = config.num_scenarios)
    chunk_indices = compute_chunk_indices(num_scenarios = config.num_scenarios, num_chunks = num_tensor_chunks)

    # Generate the canonical full tensor once, then slice it deterministically.
    rng_parent = _make_rng(rng_type = config.rng_type, seed = config.random_seed)
    returns_tensor = generate_random_returns_tensor(
        num_days = config.num_days,
        num_scenarios = config.num_scenarios,
        num_components = len(config.names_components),
        distribution_type = config.distribution_type,
        mean_returns = config.mean_returns,
        cov_matrix = config.covariance_matrix,
        dof = config.degrees_of_freedom,
        rng = rng_parent,
    )
    chunk_tensors = [
        returns_tensor[:, idx_start:idx_end, :]
        for idx_start, idx_end in chunk_indices
    ]

    _logger.debug(
        "dispatch_simulation_run: prepared %d chunk tensors from one seeded returns tensor",
        len(chunk_tensors),
    )

    _logger.debug(
        "dispatch_simulation_run: backend=%s chunks=%d scenarios=%d days=%d",
        computation_type,
        num_tensor_chunks,
        config.num_scenarios,
        config.num_days,
    )

    if progress_callback is not None:
        progress_callback(computation_type)

    t_start = time.perf_counter()
    try:
        chunk_results = runner(
            chunk_tensors=chunk_tensors,
            weights=config.weights,
            initial_value=config.initial_value,
        )
    except (Exception_Configuration, Exception_Validation_Input):
        raise
    except Exception as exc:
        raise Exception_Calculation(
            f"Backend '{computation_type}' raised an error: {exc}",
        ) from exc
    elapsed = time.perf_counter() - t_start

    # Concatenate along scenario axis → (T, N)
    portfolio_paths = np.concatenate(chunk_results, axis=1)

    # Build date index
    dates = _generate_simulation_dates(start_date = config.start_date, num_days = config.num_days)

    # Assemble result DataFrame
    data: dict[str, Any] = {"Date": dates}
    for idx_s in range(config.num_scenarios):
        data[f"Scenario_{idx_s + 1}"] = portfolio_paths[:, idx_s].tolist()

    results_df = pl.DataFrame(data).with_columns(pl.col("Date").cast(pl.Date))

    _logger.info(
        "dispatch_simulation_run COMPLETE: backend=%s elapsed=%.3fs scenarios=%d days=%d",
        computation_type,
        elapsed,
        config.num_scenarios,
        config.num_days,
    )
    return results_df, elapsed


def compute_compare_results(
    *, config: Simulation_Run_Config, progress_callback: Callable[[int, str], None] | None = None) -> dict[str, dict[str, Any]]:
    """Run all six backends sequentially and collect comparison data.

    Parameters
    ----------
    config : Simulation_Run_Config
        Simulation parameters shared across all backends.
    progress_callback : callable, optional
        Called with ``(current_index: int, computation_type: str)`` before
        each backend run.  ``current_index`` is 0-based.

    Returns
    -------
    dict[str, dict[str, Any]]
                Keyed by computation-type string. Each entry always contains
                ``"status"`` and ``"elapsed"``. Successful entries also contain
                ``"results_df"`` and ``"stats_df"``. Failed entries contain
                ``"error_type"`` and ``"error_message"``.
    """
    compare_results: dict[str, dict[str, Any]] = {}

    for idx, computation_type in enumerate(COMPUTATION_TYPES_SIMULATION_COMPARE):
        _logger.info(
            "compute_compare_results: running backend %d/%d '%s'",
            idx + 1,
            len(COMPUTATION_TYPES_SIMULATION_COMPARE),
            computation_type,
        )

        if progress_callback is not None:
            progress_callback(idx, computation_type)

        started_at = time.perf_counter()

        try:
            results_df, elapsed = dispatch_simulation_run(computation_type = computation_type, config = config)
            stats_df = compute_simulation_stats(results_df = results_df)

            compare_results[computation_type] = {
                "status": "success",
                "results_df": results_df,
                "stats_df": stats_df,
                "elapsed": elapsed,
                "error_type": None,
                "error_message": None,
            }
        except Exception as exc_error:
            elapsed = time.perf_counter() - started_at
            _logger.exception(
                "compute_compare_results: backend '%s' failed after %.3fs",
                computation_type,
                elapsed,
            )
            compare_results[computation_type] = {
                "status": "error",
                "results_df": None,
                "stats_df": None,
                "elapsed": elapsed,
                "error_type": type(exc_error).__name__,
                "error_message": str(exc_error),
            }

    return compare_results


def _compare_entry_is_successful(*, entry: dict[str, Any] | None) -> bool:
    """Return ``True`` when *entry* contains successful compare output."""
    if not isinstance(entry, dict):
        return False
    if entry.get("status") != "success":
        return False

    results_df = entry.get("results_df")
    stats_df = entry.get("stats_df")
    return isinstance(results_df, pl.DataFrame) and isinstance(stats_df, pl.DataFrame)


def _format_compare_value(*, value: float | None) -> str:
    """Format a compare-table numeric value or return ``N/A``."""
    if value is None or not np.isfinite(value):
        return "N/A"
    return f"{value:.6g}"


def _format_compare_error(*, entry: dict[str, Any] | None) -> str:
    """Return a compact error summary for a failed compare entry."""
    if not isinstance(entry, dict):
        return "Missing compare result"

    error_type = str(entry.get("error_type") or "Unknown_Error")
    error_message = str(entry.get("error_message") or "Unknown compare failure")
    return f"{error_type}: {error_message}"


def _get_terminal_metric(
    *, entry: dict[str, Any], metric: str) -> float:
    """Extract a single metric value from a compare-results entry."""
    if not _compare_entry_is_successful(entry = entry):
        return np.nan

    if metric == "Elapsed time (s)":
        return float(entry["elapsed"])

    results_df: pl.DataFrame = entry["results_df"]
    scenario_cols = [c for c in results_df.columns if c.startswith("Scenario_")]
    terminal_values = results_df.tail(1).select(scenario_cols).to_numpy().flatten()
    initial_value = float(results_df.select(scenario_cols[0]).to_series()[0])

    _metric_fn: dict[str, Callable[[np.ndarray], float]] = {
        "Mean": lambda tv: float(np.mean(tv)),
        "Median": lambda tv: float(np.median(tv)),
        "Std": lambda tv: float(np.std(tv, ddof=1)),
        "P5": lambda tv: float(np.percentile(tv, 5)),
        "P95": lambda tv: float(np.percentile(tv, 95)),
        "Min": lambda tv: float(np.min(tv)),
        "Max": lambda tv: float(np.max(tv)),
        "P25": lambda tv: float(np.percentile(tv, 25)),
        "P75": lambda tv: float(np.percentile(tv, 75)),
        "Prob(Loss)": lambda tv: float(np.mean(tv < initial_value) * 100),
    }

    fn = _metric_fn.get(metric)
    if fn is None:
        return np.nan
    return fn(terminal_values)


def build_compare_summary_table(
    *, compare_results: dict[str, dict[str, Any]], metrics_to_include: list[str] | None = None) -> pl.DataFrame:
    """Build a backend-comparison table with explicit row ordering.

    Row layout
    ----------
    1. **Status** row — ``"OK"`` / ``"FAILED"`` per backend.
    2. **Elapsed time (s)** row — one value row (no Δ sub-rows).
    3. For each numeric metric in *metrics_to_include*:

       * **Value** row — raw terminal metric per backend.
       * **Δ abs** row — absolute difference vs. ``"standard"``.
       * **Δ rel** row — relative difference vs. ``"standard"``.
         When ``|standard_value| < 0.01`` the relative difference equals
         the absolute difference (avoids division by near-zero).

    4. **Error** row — appended **only** when at least one backend failed;
       placed at the very end so successful metric rows are grouped together.

    Parameters
    ----------
    compare_results : dict
        Output of :func:`compute_compare_results`.
    metrics_to_include : list[str], optional
        Which numeric metrics to include (``"Elapsed time (s)"`` is
        ignored if present — it is always handled separately).
        Defaults to :data:`DEFAULT_COMPARE_METRICS`.

    Returns
    -------
    pl.DataFrame
        Columns: ``Metric``, ``standard``, ``asyncio``,
        ``asyncio + anyio``, ``trio``, ``trio + anyio``, ``joblib``.
    """
    if metrics_to_include is None:
        metrics_to_include = DEFAULT_COMPARE_METRICS

    # Elapsed time is always a special single-value row — exclude from the
    # numeric-metric loop to avoid double-rendering.
    metrics_numeric = [m for m in metrics_to_include if m != "Elapsed time (s)"]

    backends = list(COMPUTATION_TYPES_SIMULATION_COMPARE)

    rows: list[dict[str, str]] = []
    standard_entry = compare_results.get("standard")
    standard_available = _compare_entry_is_successful(entry = standard_entry)

    # ------------------------------------------------------------------ row 1
    status_row: dict[str, str] = {"Metric": "Status"}
    has_failed_backend = False

    for backend in backends:
        entry = compare_results.get(backend)
        if _compare_entry_is_successful(entry = entry):
            status_row[backend] = "OK"
        else:
            has_failed_backend = True
            status_row[backend] = "FAILED"

    rows.append(status_row)

    # ------------------------------------------------------------------ row 2
    elapsed_row: dict[str, str] = {"Metric": "Elapsed time (s)"}
    for backend in backends:
        entry = compare_results.get(backend)
        if isinstance(entry, dict):
            elapsed_val = float(entry.get("elapsed") or 0.0)
            elapsed_row[backend] = _format_compare_value(value = elapsed_val)
        else:
            elapsed_row[backend] = "N/A"

    rows.append(elapsed_row)

    # ---------------------------------------------------------- metric triples
    standard_values: dict[str, float | None] = {}
    for metric in metrics_numeric:
        if standard_available and standard_entry is not None:
            standard_values[metric] = _get_terminal_metric(entry = standard_entry, metric = metric)
        else:
            standard_values[metric] = None

    for metric in metrics_numeric:
        std_val = standard_values.get(metric)

        value_row: dict[str, str] = {"Metric": metric}
        abs_row: dict[str, str] = {"Metric": f"{metric} (Δ abs)"}
        rel_row: dict[str, str] = {"Metric": f"{metric} (Δ rel)"}

        for backend in backends:
            entry = compare_results.get(backend)
            if not _compare_entry_is_successful(entry = entry):
                value_row[backend] = "N/A"
                abs_row[backend] = "N/A"
                rel_row[backend] = "N/A"
                continue

            value_val = _get_terminal_metric(entry = entry, metric = metric)
            value_row[backend] = _format_compare_value(value = value_val)

            abs_str, rel_str = _compute_delta_pair(value_candidate = value_val, value_standard = std_val)
            abs_row[backend] = abs_str
            rel_row[backend] = rel_str

        rows.extend([value_row, abs_row, rel_row])

    # -------------------------------------------------------- trailing error row
    if has_failed_backend:
        error_row: dict[str, str] = {"Metric": "Error"}
        for backend in backends:
            entry = compare_results.get(backend)
            if _compare_entry_is_successful(entry = entry):
                error_row[backend] = ""
            else:
                error_row[backend] = _format_compare_error(entry = entry)
        rows.append(error_row)

    return pl.DataFrame(rows)

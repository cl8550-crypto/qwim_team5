# pyright: reportPossiblyUnbound=false
"""Baseline data generation script for simulation regression tests.

Run this script to (re-)generate the Parquet baseline files used by the
regression test suite.  Re-run whenever a deliberate algorithmic change
is made and the new output should become the reference.

Usage
-----
From the project root::

    python tests/regression_data/simulation/generate_baselines.py

Output
------
One Parquet file per simulation configuration, plus a JSON metadata file,
written to the same directory as this script.

Data format
-----------
* **summary_stats** baselines — Parquet with columns
  ``[Date, Mean, Median, Std, P5, P25, P75, P95, Min, Max]``.
* **terminal_values** baselines — Parquet with ``Scenario_1 … Scenario_N``.
* **full_results** baselines — Parquet with ``Date, Scenario_1 … Scenario_N``.
* JSON — metadata: seed, generation date, package versions, input hash.

Notes
-----
* The input parameters (fixed random seed = 42) are the canonical test
  fixture.  Never change the seed or the data generation parameters
  without also regenerating all baselines.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import io
import json
import logging
import sys

from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl  # noqa: TC002


# ---------------------------------------------------------------------------
# Ensure project root is importable
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.models.simulation.model_simulation_standard import (  # noqa: E402
    Simulation_Standard,
)
from src.num_methods.scenarios.scenarios_distrib import (  # noqa: E402
    Distribution_Type,
)


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants — must match conftest.py exactly
# ---------------------------------------------------------------------------
OUTPUT_DIR = Path(__file__).parent
RANDOM_SEED: int = 42
NUM_DAYS: int = 60
NUM_SCENARIOS: int = 50
INITIAL_VALUE: float = 100.0
START_DATE: date = date(2024, 1, 2)
ASSETS: list[str] = ["VTI", "VXUS", "BND", "VNQ", "GLD"]

# Realistic financial parameters
MEAN_RETURNS: np.ndarray = np.array(
    [0.0005, 0.0004, 0.0002, 0.0003, 0.0001],
    dtype=np.float64,
)
VOLATILITIES: np.ndarray = np.array(
    [0.012, 0.014, 0.006, 0.010, 0.008],
    dtype=np.float64,
)
CORRELATION: np.ndarray = np.array(
    [
        [1.00, 0.65, 0.20, 0.40, 0.10],
        [0.65, 1.00, 0.15, 0.35, 0.08],
        [0.20, 0.15, 1.00, 0.25, 0.30],
        [0.40, 0.35, 0.25, 1.00, 0.15],
        [0.10, 0.08, 0.30, 0.15, 1.00],
    ],
    dtype=np.float64,
)
COV_MATRIX: np.ndarray = np.outer(VOLATILITIES, VOLATILITIES) * CORRELATION

EQUAL_WEIGHTS: np.ndarray = np.array(
    [0.20, 0.20, 0.20, 0.20, 0.20],
    dtype=np.float64,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _data_hash(params: dict[str, Any]) -> str:
    """SHA-256 hash of the canonical parameter set for provenance."""
    buf = io.BytesIO()
    buf.write(json.dumps(params, sort_keys=True, default=str).encode("utf-8"))
    return hashlib.sha256(buf.getvalue()).hexdigest()


def _save_parquet(df: pl.DataFrame, filepath: Path) -> None:
    """Save a Polars DataFrame as Parquet."""
    df.write_parquet(filepath)
    logger.info("Saved baseline -> %s", filepath.name)


# ---------------------------------------------------------------------------
# Baseline generators
# ---------------------------------------------------------------------------


def _generate_normal_baselines() -> dict[str, bool]:
    """Generate baselines for Normal-distribution simulation."""
    results: dict[str, bool] = {}

    try:
        sim = Simulation_Standard(
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
            name_simulation="baseline_normal",
        )
        df_results = sim.run()
        df_summary = sim.get_summary_statistics()
        df_terminal = sim.get_terminal_values()

        _save_parquet(df_results, OUTPUT_DIR / "sim_normal_full_results.parquet")
        _save_parquet(df_summary, OUTPUT_DIR / "sim_normal_summary_stats.parquet")
        _save_parquet(df_terminal, OUTPUT_DIR / "sim_normal_terminal_values.parquet")

        results["sim_normal_full_results"] = True
        results["sim_normal_summary_stats"] = True
        results["sim_normal_terminal_values"] = True
    except Exception as exc:  # noqa: BLE001
        logger.error("FAILED normal baselines: %s", exc)
        results["sim_normal_full_results"] = False
        results["sim_normal_summary_stats"] = False
        results["sim_normal_terminal_values"] = False

    return results


def _generate_student_t_baselines() -> dict[str, bool]:
    """Generate baselines for Student-t distribution simulation."""
    results: dict[str, bool] = {}

    try:
        sim = Simulation_Standard(
            names_components=ASSETS,
            weights=EQUAL_WEIGHTS,
            distribution_type=Distribution_Type.STUDENT_T,  # type: ignore[reportArgumentType]
            mean_returns=MEAN_RETURNS,
            covariance_matrix=COV_MATRIX,
            initial_value=INITIAL_VALUE,
            num_scenarios=NUM_SCENARIOS,
            num_days=NUM_DAYS,
            start_date=START_DATE,
            random_seed=RANDOM_SEED,
            degrees_of_freedom=5.0,
            name_simulation="baseline_student_t",
        )
        df_results = sim.run()
        df_summary = sim.get_summary_statistics()
        df_terminal = sim.get_terminal_values()

        _save_parquet(df_results, OUTPUT_DIR / "sim_student_t_full_results.parquet")
        _save_parquet(df_summary, OUTPUT_DIR / "sim_student_t_summary_stats.parquet")
        _save_parquet(df_terminal, OUTPUT_DIR / "sim_student_t_terminal_values.parquet")

        results["sim_student_t_full_results"] = True
        results["sim_student_t_summary_stats"] = True
        results["sim_student_t_terminal_values"] = True
    except Exception as exc:  # noqa: BLE001
        logger.error("FAILED student-t baselines: %s", exc)
        results["sim_student_t_full_results"] = False
        results["sim_student_t_summary_stats"] = False
        results["sim_student_t_terminal_values"] = False

    return results


def _generate_lognormal_baselines() -> dict[str, bool]:
    """Generate baselines for Lognormal-distribution simulation."""
    results: dict[str, bool] = {}

    # Lognormal needs positive means (1 + r format)
    lognormal_means = 1.0 + MEAN_RETURNS

    try:
        sim = Simulation_Standard(
            names_components=ASSETS,
            weights=EQUAL_WEIGHTS,
            distribution_type=Distribution_Type.LOGNORMAL,  # type: ignore[reportArgumentType]
            mean_returns=lognormal_means,
            covariance_matrix=COV_MATRIX,
            initial_value=INITIAL_VALUE,
            num_scenarios=NUM_SCENARIOS,
            num_days=NUM_DAYS,
            start_date=START_DATE,
            random_seed=RANDOM_SEED,
            name_simulation="baseline_lognormal",
        )
        df_results = sim.run()
        df_summary = sim.get_summary_statistics()
        df_terminal = sim.get_terminal_values()

        _save_parquet(df_results, OUTPUT_DIR / "sim_lognormal_full_results.parquet")
        _save_parquet(df_summary, OUTPUT_DIR / "sim_lognormal_summary_stats.parquet")
        _save_parquet(df_terminal, OUTPUT_DIR / "sim_lognormal_terminal_values.parquet")

        results["sim_lognormal_full_results"] = True
        results["sim_lognormal_summary_stats"] = True
        results["sim_lognormal_terminal_values"] = True
    except Exception as exc:  # noqa: BLE001
        logger.error("FAILED lognormal baselines: %s", exc)
        results["sim_lognormal_full_results"] = False
        results["sim_lognormal_summary_stats"] = False
        results["sim_lognormal_terminal_values"] = False

    return results


def _generate_unequal_weights_baselines() -> dict[str, bool]:
    """Generate baselines with unequal portfolio weights."""
    results: dict[str, bool] = {}
    unequal_weights = np.array([0.40, 0.25, 0.15, 0.10, 0.10], dtype=np.float64)

    try:
        sim = Simulation_Standard(
            names_components=ASSETS,
            weights=unequal_weights,
            distribution_type=Distribution_Type.NORMAL,  # type: ignore[reportArgumentType]
            mean_returns=MEAN_RETURNS,
            covariance_matrix=COV_MATRIX,
            initial_value=INITIAL_VALUE,
            num_scenarios=NUM_SCENARIOS,
            num_days=NUM_DAYS,
            start_date=START_DATE,
            random_seed=RANDOM_SEED,
            name_simulation="baseline_unequal_weights",
        )
        df_results = sim.run()
        df_summary = sim.get_summary_statistics()
        df_terminal = sim.get_terminal_values()

        _save_parquet(df_results, OUTPUT_DIR / "sim_unequal_weights_full_results.parquet")
        _save_parquet(df_summary, OUTPUT_DIR / "sim_unequal_weights_summary_stats.parquet")
        _save_parquet(df_terminal, OUTPUT_DIR / "sim_unequal_weights_terminal_values.parquet")

        results["sim_unequal_weights_full_results"] = True
        results["sim_unequal_weights_summary_stats"] = True
        results["sim_unequal_weights_terminal_values"] = True
    except Exception as exc:  # noqa: BLE001
        logger.error("FAILED unequal-weights baselines: %s", exc)
        results["sim_unequal_weights_full_results"] = False
        results["sim_unequal_weights_summary_stats"] = False
        results["sim_unequal_weights_terminal_values"] = False

    return results


def _generate_high_initial_value_baselines() -> dict[str, bool]:
    """Generate baselines with higher initial value (1M)."""
    results: dict[str, bool] = {}

    try:
        sim = Simulation_Standard(
            names_components=ASSETS,
            weights=EQUAL_WEIGHTS,
            distribution_type=Distribution_Type.NORMAL,  # type: ignore[reportArgumentType]
            mean_returns=MEAN_RETURNS,
            covariance_matrix=COV_MATRIX,
            initial_value=1_000_000.0,
            num_scenarios=NUM_SCENARIOS,
            num_days=NUM_DAYS,
            start_date=START_DATE,
            random_seed=RANDOM_SEED,
            name_simulation="baseline_high_initial_value",
        )
        df_results = sim.run()
        df_summary = sim.get_summary_statistics()
        df_terminal = sim.get_terminal_values()

        _save_parquet(df_results, OUTPUT_DIR / "sim_high_value_full_results.parquet")
        _save_parquet(df_summary, OUTPUT_DIR / "sim_high_value_summary_stats.parquet")
        _save_parquet(df_terminal, OUTPUT_DIR / "sim_high_value_terminal_values.parquet")

        results["sim_high_value_full_results"] = True
        results["sim_high_value_summary_stats"] = True
        results["sim_high_value_terminal_values"] = True
    except Exception as exc:  # noqa: BLE001
        logger.error("FAILED high-initial-value baselines: %s", exc)
        results["sim_high_value_full_results"] = False
        results["sim_high_value_summary_stats"] = False
        results["sim_high_value_terminal_values"] = False

    return results


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


def _write_metadata(all_results: dict[str, bool]) -> None:
    """Write JSON metadata documenting how baselines were generated."""
    try:
        polars_version = importlib.metadata.version("polars")
    except importlib.metadata.PackageNotFoundError:
        polars_version = "unknown"

    try:
        numpy_version = importlib.metadata.version("numpy")
    except importlib.metadata.PackageNotFoundError:
        numpy_version = "unknown"

    params_dict: dict[str, Any] = {
        "random_seed": RANDOM_SEED,
        "num_days": NUM_DAYS,
        "num_scenarios": NUM_SCENARIOS,
        "initial_value": INITIAL_VALUE,
        "start_date": str(START_DATE),
        "assets": ASSETS,
        "mean_returns": MEAN_RETURNS.tolist(),
        "covariance_matrix": COV_MATRIX.tolist(),
    }

    metadata: dict[str, Any] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "random_seed": RANDOM_SEED,
        "num_days": NUM_DAYS,
        "num_scenarios": NUM_SCENARIOS,
        "initial_value": INITIAL_VALUE,
        "start_date": str(START_DATE),
        "assets": ASSETS,
        "params_sha256": _data_hash(params_dict),
        "package_versions": {
            "polars": polars_version,
            "numpy": numpy_version,
            "python": sys.version,
        },
        "baselines": {
            name: ("ok" if success else "failed") for name, success in all_results.items()
        },
    }

    metadata_path = OUTPUT_DIR / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    logger.info("Saved metadata -> metadata.json")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> int:
    """Generate all simulation regression baselines."""
    logger.info("=" * 60)
    logger.info("Generating simulation regression baselines")
    logger.info("Output directory: %s", OUTPUT_DIR)
    logger.info("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    normal_results = _generate_normal_baselines()
    student_t_results = _generate_student_t_baselines()
    lognormal_results = _generate_lognormal_baselines()
    unequal_results = _generate_unequal_weights_baselines()
    high_value_results = _generate_high_initial_value_baselines()

    all_results: dict[str, bool] = {
        **normal_results,
        **student_t_results,
        **lognormal_results,
        **unequal_results,
        **high_value_results,
    }

    _write_metadata(all_results)

    total = len(all_results)
    passed = sum(all_results.values())
    failed = total - passed

    logger.info("=" * 60)
    logger.info("Done: %d/%d baselines generated successfully", passed, total)
    if failed:
        logger.warning("%d baselines FAILED -- check errors above", failed)
    logger.info("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

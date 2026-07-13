# pyright: reportArgumentType=false
"""Baseline data generation script for scenarios regression tests.

Run this script to (re-)generate the Parquet baseline files used by the
regression test suite.  Re-run whenever a deliberate algorithmic change
is made and the new output should become the reference.

Usage
-----
From the project root::

    python tests/regression_data/scenarios/generate_baselines.py

Output
------
One Parquet file per scenario configuration, plus a JSON metadata file,
written to the same directory as this script.

Data format
-----------
* **scenarios** baselines — Parquet with ``Date`` + component columns.
* **summary_stats** baselines — Parquet with columns
  ``[component, mean, std, min, max, median, skew, count]``.
* **correlation** baselines — Parquet with ``component`` + component columns.
* **covariance** baselines — Parquet with ``component`` + component columns.
* **returns_to_prices** baselines — Parquet with ``Date`` + component columns.
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
import polars as pl


# ---------------------------------------------------------------------------
# Ensure project root is importable
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.num_methods.scenarios.scenarios_CMA import (  # noqa: E402
    Scenarios_CMA,
)
from src.num_methods.scenarios.scenarios_distrib import (  # noqa: E402
    Distribution_Type,
    Scenarios_Distribution,
)


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants — must match conftest.py exactly
# ---------------------------------------------------------------------------
OUTPUT_DIR = Path(__file__).parent
RANDOM_SEED: int = 42
NUM_DAYS: int = 60
START_DATE: date = date(2024, 1, 2)

# --- Distribution scenario components ---
DISTRIB_COMPONENTS: list[str] = ["US_Equity", "Intl_Equity", "US_Bond", "REIT", "Gold"]

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

# Lognormal means must be strictly positive: use (1 + daily_return)
LOGNORMAL_MEANS: np.ndarray = 1.0 + MEAN_RETURNS

# --- CMA scenario components ---
CMA_ASSET_CLASSES: list[str] = [
    "US Large Cap",
    "International Developed",
    "US Investment Grade Bonds",
    "Real Estate",
]
CMA_EXPECTED_RETURNS_ANNUAL: np.ndarray = np.array(
    [0.08, 0.07, 0.03, 0.06],
    dtype=np.float64,
)
CMA_EXPECTED_VOLS_ANNUAL: np.ndarray = np.array(
    [0.16, 0.18, 0.05, 0.14],
    dtype=np.float64,
)
CMA_CORRELATION: np.ndarray = np.array(
    [
        [1.00, 0.70, 0.10, 0.50],
        [0.70, 1.00, 0.05, 0.40],
        [0.10, 0.05, 1.00, 0.20],
        [0.50, 0.40, 0.20, 1.00],
    ],
    dtype=np.float64,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _hash_inputs(*arrays: np.ndarray) -> str:
    """Deterministic SHA-256 of the NumPy arrays used as inputs."""
    hasher = hashlib.sha256()
    for arr in arrays:
        buf = io.BytesIO()
        np.save(buf, arr)
        hasher.update(buf.getvalue())
    return hasher.hexdigest()


def _save_parquet(df: pl.DataFrame, name: str) -> None:
    """Write a Polars DataFrame as a Parquet file in OUTPUT_DIR."""
    path = OUTPUT_DIR / f"{name}.parquet"
    df.write_parquet(path, compression="zstd", compression_level=3)
    logger.info("Wrote %s  (%d rows x %d cols)", path.name, df.height, df.width)


# ---------------------------------------------------------------------------
# Baseline generators — Scenarios_Distribution
# ---------------------------------------------------------------------------


def _generate_distrib_normal_baselines() -> None:
    """Generate baselines using multivariate Normal distribution."""
    scen = Scenarios_Distribution(
        names_components=DISTRIB_COMPONENTS,
        distribution_type=Distribution_Type.NORMAL,
        mean_returns=MEAN_RETURNS,
        covariance_matrix=COV_MATRIX,
        start_date=START_DATE,
        num_days=NUM_DAYS,
        random_seed=RANDOM_SEED,
        name_scenarios="Normal Regression Baseline",
    )
    df_scenarios = scen.generate()
    _save_parquet(df_scenarios, "distrib_normal_scenarios")

    df_summary = scen.calc_summary_statistics()
    _save_parquet(df_summary, "distrib_normal_summary_stats")

    df_corr = scen.calc_correlation_matrix()
    _save_parquet(df_corr, "distrib_normal_correlation")

    df_cov = scen.calc_covariance_matrix()
    _save_parquet(df_cov, "distrib_normal_covariance")


def _generate_distrib_student_t_baselines() -> None:
    """Generate baselines using multivariate Student-t distribution."""
    scen = Scenarios_Distribution(
        names_components=DISTRIB_COMPONENTS,
        distribution_type=Distribution_Type.STUDENT_T,
        mean_returns=MEAN_RETURNS,
        covariance_matrix=COV_MATRIX,
        degrees_of_freedom=5.0,
        start_date=START_DATE,
        num_days=NUM_DAYS,
        random_seed=RANDOM_SEED,
        name_scenarios="Student-t Regression Baseline",
    )
    df_scenarios = scen.generate()
    _save_parquet(df_scenarios, "distrib_student_t_scenarios")

    df_summary = scen.calc_summary_statistics()
    _save_parquet(df_summary, "distrib_student_t_summary_stats")

    df_corr = scen.calc_correlation_matrix()
    _save_parquet(df_corr, "distrib_student_t_correlation")


def _generate_distrib_lognormal_baselines() -> None:
    """Generate baselines using multivariate lognormal distribution."""
    scen = Scenarios_Distribution(
        names_components=DISTRIB_COMPONENTS,
        distribution_type=Distribution_Type.LOGNORMAL,
        mean_returns=LOGNORMAL_MEANS,
        covariance_matrix=COV_MATRIX,
        start_date=START_DATE,
        num_days=NUM_DAYS,
        random_seed=RANDOM_SEED,
        name_scenarios="Lognormal Regression Baseline",
    )
    df_scenarios = scen.generate()
    _save_parquet(df_scenarios, "distrib_lognormal_scenarios")

    df_summary = scen.calc_summary_statistics()
    _save_parquet(df_summary, "distrib_lognormal_summary_stats")


def _generate_distrib_corr_vols_baselines() -> None:
    """Generate baselines using correlation + volatilities input mode."""
    scen = Scenarios_Distribution.from_correlation_and_volatilities(
        names_components=DISTRIB_COMPONENTS,
        correlation_matrix=CORRELATION,
        volatilities=VOLATILITIES,
        distribution_type=Distribution_Type.NORMAL,
        mean_returns=MEAN_RETURNS,
        start_date=START_DATE,
        num_days=NUM_DAYS,
        random_seed=RANDOM_SEED,
        name_scenarios="Corr+Vols Regression Baseline",
    )
    df_scenarios = scen.generate()
    _save_parquet(df_scenarios, "distrib_corr_vols_scenarios")

    df_summary = scen.calc_summary_statistics()
    _save_parquet(df_summary, "distrib_corr_vols_summary_stats")


def _generate_distrib_returns_to_prices_baselines() -> None:
    """Generate baselines for returns-to-prices conversion."""
    scen = Scenarios_Distribution(
        names_components=DISTRIB_COMPONENTS,
        distribution_type=Distribution_Type.NORMAL,
        mean_returns=MEAN_RETURNS,
        covariance_matrix=COV_MATRIX,
        start_date=START_DATE,
        num_days=NUM_DAYS,
        random_seed=RANDOM_SEED,
        name_scenarios="Returns-to-Prices Baseline",
    )
    scen.generate()

    initial_prices = [100.0, 50.0, 75.0, 80.0, 60.0]
    df_prices = scen.convert_returns_to_prices(initial_prices=initial_prices)
    _save_parquet(df_prices, "distrib_returns_to_prices")


# ---------------------------------------------------------------------------
# Baseline generators — Scenarios_CMA
# ---------------------------------------------------------------------------


def _generate_CMA_baselines() -> None:
    """Generate baselines using CMA scenario generator."""
    scen = Scenarios_CMA(
        names_asset_classes=CMA_ASSET_CLASSES,
        expected_returns_annual=CMA_EXPECTED_RETURNS_ANNUAL,
        expected_vols_annual=CMA_EXPECTED_VOLS_ANNUAL,
        correlation_matrix=CMA_CORRELATION,
        start_date=START_DATE,
        num_days=NUM_DAYS,
        random_seed=RANDOM_SEED,
        name_scenarios="CMA Regression Baseline",
    )
    df_scenarios = scen.generate()
    _save_parquet(df_scenarios, "CMA_scenarios")

    df_summary = scen.calc_summary_statistics()
    _save_parquet(df_summary, "CMA_summary_stats")

    df_corr = scen.calc_correlation_matrix()
    _save_parquet(df_corr, "CMA_correlation")

    df_cov = scen.calc_covariance_matrix()
    _save_parquet(df_cov, "CMA_covariance")

    # Index correspondence table
    df_idx_table = scen.get_index_correspondence_table()
    _save_parquet(df_idx_table, "CMA_index_correspondence")

    # Daily conversions
    daily_ret = scen.calc_daily_expected_returns()
    daily_cov = scen.calc_daily_covariance()
    daily_vol = scen.calc_daily_volatilities()

    df_daily = pl.DataFrame(
        {
            "asset_class": CMA_ASSET_CLASSES,
            "daily_return": daily_ret.tolist(),
            "daily_volatility": daily_vol.tolist(),
        },
    )
    _save_parquet(df_daily, "CMA_daily_params")

    df_daily_cov = pl.DataFrame(
        {
            "asset_class": CMA_ASSET_CLASSES,
            **{ac: daily_cov[:, idx_j].tolist() for idx_j, ac in enumerate(CMA_ASSET_CLASSES)},
        },
    )
    _save_parquet(df_daily_cov, "CMA_daily_covariance")


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


def _write_metadata() -> None:
    """Write JSON metadata for traceability."""
    metadata: dict[str, Any] = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "random_seed": RANDOM_SEED,
        "num_days": NUM_DAYS,
        "start_date": str(START_DATE),
        "distrib_components": DISTRIB_COMPONENTS,
        "CMA_asset_classes": CMA_ASSET_CLASSES,
        "input_hash_distrib": _hash_inputs(MEAN_RETURNS, COV_MATRIX),
        "input_hash_CMA": _hash_inputs(
            CMA_EXPECTED_RETURNS_ANNUAL,
            CMA_EXPECTED_VOLS_ANNUAL,
            CMA_CORRELATION,
        ),
        "package_versions": {
            "numpy": importlib.metadata.version("numpy"),
            "polars": importlib.metadata.version("polars"),
        },
    }
    path = OUTPUT_DIR / "metadata.json"
    path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    logger.info("Wrote %s", path.name)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    """Generate all baselines and metadata.

    Returns
    -------
    int
        ``0`` on success, ``1`` on failure.
    """
    logger.info("Generating scenarios regression baselines …")
    logger.info("Output directory: %s", OUTPUT_DIR)

    try:
        _generate_distrib_normal_baselines()
        _generate_distrib_student_t_baselines()
        _generate_distrib_lognormal_baselines()
        _generate_distrib_corr_vols_baselines()
        _generate_distrib_returns_to_prices_baselines()
        _generate_CMA_baselines()
        _write_metadata()
    except Exception:
        logger.exception("Baseline generation failed")
        return 1

    logger.info("All baselines generated successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

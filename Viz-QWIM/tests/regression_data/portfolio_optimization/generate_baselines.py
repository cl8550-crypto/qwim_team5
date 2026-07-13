# pyright: reportPossiblyUnbound=false
"""Baseline data generation script for portfolio optimization regression tests.

Run this script to (re-)generate the Parquet baseline files used by the regression
test suite.  Re-run whenever a deliberate algorithmic change is made and the new
output should become the reference.

Usage
-----
From the project root:

    python tests/regression_data/portfolio_optimization/generate_baselines.py

Output
------
One Parquet file per optimization method, plus a JSON metadata file, written to
the same directory as this script.

Data format
-----------
* Parquet  — weights DataFrame: columns [Date, asset1, asset2, ...], 1 row.
* JSON     — metadata: seed, generation date, package versions, input data hash.

Notes
-----
* The input returns data (fixed random seed = 42) is the canonical test fixture.
  Never change the seed or the data generation parameters without also regenerating
  all baselines.
* Optimalportfolios wrapper functions are skipped if the underlying package imports
  are broken (known issue: the wrapper uses incorrect function names).
* azapy wrapper functions are included; import failure is handled gracefully.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import io
import json
import logging
import sys

from datetime import UTC, datetime
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

from skfolio.optimization import ObjectiveFunction  # noqa: E402

from src.models.portfolio_optimization.pkg_skfolio import (  # noqa: E402
    calc_skfolio_optimization_basic,
    calc_skfolio_optimization_clustering,
    calc_skfolio_optimization_convex,
    calc_skfolio_optimization_ensemble,
)
from src.models.portfolio_optimization.utils_portfolio_optimization import (  # noqa: E402
    portfolio_optimization_type,
)


# Attempt to import optimalportfolios wrappers — may fail due to stale imports
_OPTIMALPORTFOLIOS_IMPORT_ERROR: str = ""

try:
    from src.models.portfolio_optimization.pkg_optimalportfolios import (
        calc_optimalportfolios_budgeted_risk_contribution,
        calc_optimalportfolios_maximum_cara_gaussian_mixture,
        calc_optimalportfolios_maximum_diversification,
        calc_optimalportfolios_maximum_quadratic_utility,
        calc_optimalportfolios_maximum_sharpe_ratio,
        calc_optimalportfolios_minimum_variance,
        calc_optimalportfolios_tracking_error_minimization,
    )

    OPTIMALPORTFOLIOS_AVAILABLE = True
except ImportError as _err:
    OPTIMALPORTFOLIOS_AVAILABLE = False
    _OPTIMALPORTFOLIOS_IMPORT_ERROR = str(_err)

# Attempt to import azapy wrappers
_AZAPY_IMPORT_ERROR: str = ""

try:
    from src.models.portfolio_optimization.pkg_azapy import (
        calc_azapy_cvar,
        calc_azapy_evar,
        calc_azapy_inverse_volatility,
        calc_azapy_kelly,
        calc_azapy_mad,
        calc_azapy_mean_variance,
    )

    AZAPY_AVAILABLE = True
except ImportError as _err_azapy:
    AZAPY_AVAILABLE = False
    _AZAPY_IMPORT_ERROR = str(_err_azapy)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OUTPUT_DIR = Path(__file__).parent
FIXED_DATE = "2024-01-15"  # Pinned optimization date for reproducibility
RANDOM_SEED = 42
N_DAYS = 252
ASSETS = ["VTI", "VXUS", "BND", "VNQ", "GLD"]


# ---------------------------------------------------------------------------
# Fixed returns fixture (identical to conftest fixture)
# ---------------------------------------------------------------------------


def _build_fixed_returns() -> pl.DataFrame:
    """Build the canonical fixed-seed returns DataFrame.

    Parameters are pinned — do NOT change without regenerating all baselines.
    """
    rng = np.random.default_rng(RANDOM_SEED)

    mean_returns = np.array([0.0005, 0.0004, 0.0002, 0.0003, 0.0001])
    volatilities = np.array([0.012, 0.014, 0.006, 0.010, 0.008])
    correlation = np.array(
        [
            [1.00, 0.65, 0.20, 0.40, 0.10],
            [0.65, 1.00, 0.15, 0.35, 0.08],
            [0.20, 0.15, 1.00, 0.25, 0.30],
            [0.40, 0.35, 0.25, 1.00, 0.15],
            [0.10, 0.08, 0.30, 0.15, 1.00],
        ],
    )
    cov_matrix = np.outer(volatilities, volatilities) * correlation
    returns_array = rng.multivariate_normal(mean_returns, cov_matrix, N_DAYS)

    dates = pl.date_range(
        start=datetime(2023, 1, 2, tzinfo=UTC),
        end=datetime(2024, 6, 30, tzinfo=UTC),
        interval="1d",
        eager=True,
    )[:N_DAYS]

    return pl.DataFrame(
        {
            "Date": dates,
            **{asset: returns_array[:, i].tolist() for i, asset in enumerate(ASSETS)},
        },
    )


def _build_benchmark_returns(returns_data: pl.DataFrame) -> pl.DataFrame:
    """Build a single-column benchmark DataFrame aligned with returns_data."""
    rng = np.random.default_rng(RANDOM_SEED + 1)
    n = len(returns_data)
    bench = rng.normal(0.0003, 0.010, n)
    return pl.DataFrame({"Date": returns_data["Date"], "SPY": bench.tolist()})


def _weights_to_parquet(portfolio_obj, filepath: Path) -> None:
    """Extract weights DataFrame from portfolio_QWIM and save as Parquet."""
    weights_df = portfolio_obj.get_portfolio_weights()
    weights_df.write_parquet(filepath)
    logger.info("Saved baseline → %s", filepath.name)


def _data_hash(returns_data: pl.DataFrame) -> str:
    """Compute SHA-256 hash of the returns data bytes for provenance tracking."""
    buf = io.BytesIO()
    returns_data.write_parquet(buf)
    return hashlib.sha256(buf.getvalue()).hexdigest()


# ---------------------------------------------------------------------------
# Skfolio baseline generators
# ---------------------------------------------------------------------------


def _generate_skfolio_baselines(returns_data: pl.DataFrame) -> dict[str, bool]:
    """Generate all skfolio baseline Parquet files.

    Returns
    -------
    dict mapping baseline name → success bool.
    """
    results: dict[str, bool] = {}

    # ------------------------------------------------------------------
    # Basic methods
    # ------------------------------------------------------------------
    basic_cases = [
        ("skfolio_basic_equal_weighted", portfolio_optimization_type.BASIC_EQUAL_WEIGHTED, {}),
        (
            "skfolio_basic_inverse_volatility",
            portfolio_optimization_type.BASIC_INVERSE_VOLATILITY,
            {},
        ),
        # Random Dirichlet: fix numpy global seed immediately before call for reproducibility
        (
            "skfolio_basic_random_dirichlet",
            portfolio_optimization_type.BASIC_RANDOM_DIRICHLET,
            {"_preseed": True},
        ),
    ]

    for name, opt_type, kwargs in basic_cases:
        try:
            preseed = kwargs.pop("_preseed", False)
            if preseed:
                np.random.seed(RANDOM_SEED)
            portfolio = calc_skfolio_optimization_basic(
                returns_data=returns_data,
                optimization_type=opt_type,
                portfolio_name=name,
                optimization_date=FIXED_DATE,
                **kwargs,
            )
            _weights_to_parquet(portfolio, OUTPUT_DIR / f"{name}.parquet")
            results[name] = True
        except Exception as exc:  # noqa: BLE001
            logger.error("FAILED %s: %s", name, exc)
            results[name] = False

    # ------------------------------------------------------------------
    # Convex methods
    # ------------------------------------------------------------------
    convex_cases = [
        (
            "skfolio_convex_mean_risk_minimize_risk",
            portfolio_optimization_type.CONVEX_MEAN_RISK,
            {"objective_function": ObjectiveFunction.MINIMIZE_RISK},
        ),
        (
            "skfolio_convex_mean_risk_maximize_return",
            portfolio_optimization_type.CONVEX_MEAN_RISK,
            {"objective_function": ObjectiveFunction.MAXIMIZE_RETURN},
        ),
        (
            "skfolio_convex_mean_risk_maximize_ratio",
            portfolio_optimization_type.CONVEX_MEAN_RISK,
            {"objective_function": ObjectiveFunction.MAXIMIZE_RATIO},
        ),
        (
            "skfolio_convex_mean_risk_maximize_utility",
            portfolio_optimization_type.CONVEX_MEAN_RISK,
            {
                "objective_function": ObjectiveFunction.MAXIMIZE_UTILITY,
                "risk_aversion": 1.0,
            },
        ),
        (
            "skfolio_convex_risk_budgeting",
            portfolio_optimization_type.CONVEX_RISK_BUDGETING,
            {},
        ),
        (
            "skfolio_convex_maximum_diversification",
            portfolio_optimization_type.CONVEX_MAXIMUM_DIVERSIFICATION,
            {},
        ),
        (
            "skfolio_convex_distributionally_robust_cvar",
            portfolio_optimization_type.CONVEX_DISTRIBUTIONALLY_ROBUST_CVAR,
            {},
        ),
    ]

    for name, opt_type, kwargs in convex_cases:
        try:
            portfolio = calc_skfolio_optimization_convex(
                returns_data=returns_data,
                optimization_type=opt_type,
                portfolio_name=name,
                optimization_date=FIXED_DATE,
                **kwargs,
            )
            _weights_to_parquet(portfolio, OUTPUT_DIR / f"{name}.parquet")
            results[name] = True
        except Exception as exc:  # noqa: BLE001
            logger.error("FAILED %s: %s", name, exc)
            results[name] = False

    # Benchmark tracking requires benchmark data
    try:
        benchmark_data = _build_benchmark_returns(returns_data)
        portfolio = calc_skfolio_optimization_convex(
            returns_data=returns_data,
            optimization_type=portfolio_optimization_type.CONVEX_BENCHMARK_TRACKING,
            portfolio_name="skfolio_convex_benchmark_tracking",
            optimization_date=FIXED_DATE,
            benchmark_returns=benchmark_data,
        )
        _weights_to_parquet(portfolio, OUTPUT_DIR / "skfolio_convex_benchmark_tracking.parquet")
        results["skfolio_convex_benchmark_tracking"] = True
    except Exception as exc:  # noqa: BLE001
        logger.error("FAILED skfolio_convex_benchmark_tracking: %s", exc)
        results["skfolio_convex_benchmark_tracking"] = False

    # ------------------------------------------------------------------
    # Clustering methods
    # ------------------------------------------------------------------
    clustering_cases = [
        (
            "skfolio_clustering_hrp",
            portfolio_optimization_type.CLUSTERING_HIERARCHICAL_RISK_PARITY,
        ),
        (
            "skfolio_clustering_herc",
            portfolio_optimization_type.CLUSTERING_HIERARCHICAL_EQUAL_RISK_CONTRIBUTION,
        ),
        (
            "skfolio_clustering_schur",
            portfolio_optimization_type.CLUSTERING_SCHUR_COMPLEMENTARY_ALLOCATION,
        ),
        (
            "skfolio_clustering_nested",
            portfolio_optimization_type.CLUSTERING_NESTED,
        ),
    ]

    for name, opt_type in clustering_cases:
        try:
            portfolio = calc_skfolio_optimization_clustering(
                returns_data=returns_data,
                optimization_type=opt_type,
                portfolio_name=name,
                optimization_date=FIXED_DATE,
            )
            _weights_to_parquet(portfolio, OUTPUT_DIR / f"{name}.parquet")
            results[name] = True
        except Exception as exc:  # noqa: BLE001
            logger.error("FAILED %s: %s", name, exc)
            results[name] = False

    # ------------------------------------------------------------------
    # Ensemble methods
    # ------------------------------------------------------------------
    try:
        np.random.seed(RANDOM_SEED)
        portfolio = calc_skfolio_optimization_ensemble(
            returns_data=returns_data,
            optimization_type=portfolio_optimization_type.ENSEMBLE_STACKING,
            portfolio_name="skfolio_ensemble_stacking",
            optimization_date=FIXED_DATE,
        )
        _weights_to_parquet(portfolio, OUTPUT_DIR / "skfolio_ensemble_stacking.parquet")
        results["skfolio_ensemble_stacking"] = True
    except Exception as exc:  # noqa: BLE001
        logger.error("FAILED skfolio_ensemble_stacking: %s", exc)
        results["skfolio_ensemble_stacking"] = False

    return results


# ---------------------------------------------------------------------------
# Optimalportfolios baseline generators  (may be skipped on import error)
# ---------------------------------------------------------------------------


def _generate_optimalportfolios_baselines(returns_data: pl.DataFrame) -> dict[str, bool]:
    """Generate optimalportfolios baseline Parquet files.

    Returns
    -------
    dict mapping baseline name → success bool.
    Immediately returns all-skipped if the package imports are broken.
    """
    if not OPTIMALPORTFOLIOS_AVAILABLE:
        logger.warning(
            "Skipping optimalportfolios baselines — import error: %s",
            _OPTIMALPORTFOLIOS_IMPORT_ERROR,
        )
        return {}

    results: dict[str, bool] = {}

    simple_cases = [
        (
            "optimalportfolios_minimum_variance",
            calc_optimalportfolios_minimum_variance,
            {},
        ),
        (
            "optimalportfolios_maximum_quadratic_utility",
            calc_optimalportfolios_maximum_quadratic_utility,
            {"risk_aversion": 1.0},
        ),
        (
            "optimalportfolios_budgeted_risk_contribution",
            calc_optimalportfolios_budgeted_risk_contribution,
            {},
        ),
        (
            "optimalportfolios_maximum_diversification",
            calc_optimalportfolios_maximum_diversification,
            {},
        ),
        (
            "optimalportfolios_maximum_sharpe_ratio",
            calc_optimalportfolios_maximum_sharpe_ratio,
            {"risk_free_rate": 0.0},
        ),
        (
            "optimalportfolios_maximum_cara_gaussian_mixture",
            calc_optimalportfolios_maximum_cara_gaussian_mixture,
            {"risk_aversion": 1.0, "n_components": 2},
        ),
    ]

    for name, func, kwargs in simple_cases:
        try:
            portfolio = func(
                returns_data=returns_data,
                portfolio_name=name,
                optimization_date=FIXED_DATE,
                **kwargs,
            )
            _weights_to_parquet(portfolio, OUTPUT_DIR / f"{name}.parquet")
            results[name] = True
        except Exception as exc:  # noqa: BLE001
            logger.error("FAILED %s: %s", name, exc)
            results[name] = False

    # Tracking error requires benchmark
    try:
        benchmark_data = _build_benchmark_returns(returns_data)
        portfolio = calc_optimalportfolios_tracking_error_minimization(
            returns_data=returns_data,
            benchmark_returns=benchmark_data,
            portfolio_name="optimalportfolios_tracking_error_minimization",
            optimization_date=FIXED_DATE,
        )
        _weights_to_parquet(
            portfolio,
            OUTPUT_DIR / "optimalportfolios_tracking_error_minimization.parquet",
        )
        results["optimalportfolios_tracking_error_minimization"] = True
    except Exception as exc:  # noqa: BLE001
        logger.error("FAILED optimalportfolios_tracking_error_minimization: %s", exc)
        results["optimalportfolios_tracking_error_minimization"] = False

    return results


# ---------------------------------------------------------------------------
# Azapy baseline generators (may be skipped on import error)
# ---------------------------------------------------------------------------


def _generate_azapy_baselines(returns_data: pl.DataFrame) -> dict[str, bool]:
    """Generate azapy baseline Parquet files.

    Returns
    -------
    dict mapping baseline name → success bool.
    Immediately returns empty if the package imports are broken.
    """
    if not AZAPY_AVAILABLE:
        logger.warning(
            "Skipping azapy baselines — import error: %s",
            _AZAPY_IMPORT_ERROR,
        )
        return {}

    results: dict[str, bool] = {}

    # ------------------------------------------------------------------
    # Mean-Variance baselines
    # ------------------------------------------------------------------
    mv_cases: list[tuple[str, dict[str, Any]]] = [
        ("azapy_mean_variance_min_risk", {"rtype": "MinRisk"}),
        ("azapy_mean_variance_sharpe", {"rtype": "Sharpe"}),
    ]

    for name, kwargs in mv_cases:
        try:
            portfolio = calc_azapy_mean_variance(
                returns_data=returns_data,
                portfolio_name=name,
                optimization_date=FIXED_DATE,
                **kwargs,
            )
            _weights_to_parquet(portfolio, OUTPUT_DIR / f"{name}.parquet")
            results[name] = True
        except Exception as exc:  # noqa: BLE001
            logger.error("FAILED %s: %s", name, exc)
            results[name] = False

    # ------------------------------------------------------------------
    # CVaR baselines
    # ------------------------------------------------------------------
    cvar_cases: list[tuple[str, dict[str, Any]]] = [
        ("azapy_cvar_min_risk", {"alpha": 0.975, "rtype": "MinRisk"}),
        ("azapy_cvar_sharpe", {"alpha": 0.975, "rtype": "Sharpe"}),
    ]

    for name, kwargs in cvar_cases:
        try:
            portfolio = calc_azapy_cvar(
                returns_data=returns_data,
                portfolio_name=name,
                optimization_date=FIXED_DATE,
                **kwargs,
            )
            _weights_to_parquet(portfolio, OUTPUT_DIR / f"{name}.parquet")
            results[name] = True
        except Exception as exc:  # noqa: BLE001
            logger.error("FAILED %s: %s", name, exc)
            results[name] = False

    # ------------------------------------------------------------------
    # MAD baselines
    # ------------------------------------------------------------------
    mad_cases: list[tuple[str, dict[str, Any]]] = [
        ("azapy_mad_min_risk", {"rtype": "MinRisk"}),
        ("azapy_mad_sharpe", {"rtype": "Sharpe"}),
    ]

    for name, kwargs in mad_cases:
        try:
            portfolio = calc_azapy_mad(
                returns_data=returns_data,
                portfolio_name=name,
                optimization_date=FIXED_DATE,
                **kwargs,
            )
            _weights_to_parquet(portfolio, OUTPUT_DIR / f"{name}.parquet")
            results[name] = True
        except Exception as exc:  # noqa: BLE001
            logger.error("FAILED %s: %s", name, exc)
            results[name] = False

    # ------------------------------------------------------------------
    # Inverse Volatility baseline
    # ------------------------------------------------------------------
    try:
        portfolio = calc_azapy_inverse_volatility(
            returns_data=returns_data,
            portfolio_name="azapy_inverse_volatility",
            optimization_date=FIXED_DATE,
        )
        _weights_to_parquet(portfolio, OUTPUT_DIR / "azapy_inverse_volatility.parquet")
        results["azapy_inverse_volatility"] = True
    except Exception as exc:  # noqa: BLE001
        logger.error("FAILED azapy_inverse_volatility: %s", exc)
        results["azapy_inverse_volatility"] = False

    # ------------------------------------------------------------------
    # Kelly Criterion baseline
    # ------------------------------------------------------------------
    try:
        portfolio = calc_azapy_kelly(
            returns_data=returns_data,
            rtype="ExpCone",
            portfolio_name="azapy_kelly_exp_cone",
            optimization_date=FIXED_DATE,
        )
        _weights_to_parquet(portfolio, OUTPUT_DIR / "azapy_kelly_exp_cone.parquet")
        results["azapy_kelly_exp_cone"] = True
    except Exception as exc:  # noqa: BLE001
        logger.error("FAILED azapy_kelly_exp_cone: %s", exc)
        results["azapy_kelly_exp_cone"] = False

    # ------------------------------------------------------------------
    # EVaR baselines
    # ------------------------------------------------------------------
    evar_cases: list[tuple[str, dict[str, Any]]] = [
        ("azapy_evar_min_risk", {"alpha": 0.975, "rtype": "MinRisk"}),
        ("azapy_evar_sharpe", {"alpha": 0.975, "rtype": "Sharpe"}),
    ]

    for name, kwargs in evar_cases:
        try:
            portfolio = calc_azapy_evar(
                returns_data=returns_data,
                portfolio_name=name,
                optimization_date=FIXED_DATE,
                **kwargs,
            )
            _weights_to_parquet(portfolio, OUTPUT_DIR / f"{name}.parquet")
            results[name] = True
        except Exception as exc:  # noqa: BLE001
            logger.error("FAILED %s: %s", name, exc)
            results[name] = False

    return results


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


def _write_metadata(returns_data: pl.DataFrame, all_results: dict[str, bool]) -> None:
    """Write JSON metadata file documenting how baselines were generated."""
    try:
        skfolio_version = importlib.metadata.version("skfolio")
    except importlib.metadata.PackageNotFoundError:
        skfolio_version = "unknown"

    try:
        optimalportfolios_version = importlib.metadata.version("optimalportfolios")
    except importlib.metadata.PackageNotFoundError:
        optimalportfolios_version = "unknown"

    try:
        azapy_version = importlib.metadata.version("azapy")
    except importlib.metadata.PackageNotFoundError:
        azapy_version = "unknown"

    try:
        polars_version = importlib.metadata.version("polars")
    except importlib.metadata.PackageNotFoundError:
        polars_version = "unknown"

    metadata = {
        "generated_at": datetime.now(UTC).isoformat(),
        "random_seed": RANDOM_SEED,
        "fixed_optimization_date": FIXED_DATE,
        "n_days": N_DAYS,
        "assets": ASSETS,
        "returns_data_sha256": _data_hash(returns_data),
        "package_versions": {
            "skfolio": skfolio_version,
            "optimalportfolios": optimalportfolios_version,
            "azapy": azapy_version,
            "polars": polars_version,
            "python": sys.version,
        },
        "baselines": {
            name: ("ok" if success else "failed") for name, success in all_results.items()
        },
        "optimalportfolios_available": OPTIMALPORTFOLIOS_AVAILABLE,
        "azapy_available": AZAPY_AVAILABLE,
    }

    metadata_path = OUTPUT_DIR / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    logger.info("Saved metadata → metadata.json")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> int:
    """Generate all portfolio optimization regression baselines."""
    logger.info("=" * 60)
    logger.info("Generating portfolio optimization regression baselines")
    logger.info("Output directory: %s", OUTPUT_DIR)
    logger.info("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    returns_data = _build_fixed_returns()
    logger.info("Built returns fixture: %d rows x %d assets", N_DAYS, len(ASSETS))

    skfolio_results = _generate_skfolio_baselines(returns_data)
    optimalportfolios_results = _generate_optimalportfolios_baselines(returns_data)
    azapy_results = _generate_azapy_baselines(returns_data)

    all_results = {**skfolio_results, **optimalportfolios_results, **azapy_results}
    _write_metadata(returns_data, all_results)

    total = len(all_results)
    passed = sum(all_results.values())
    failed = total - passed

    logger.info("=" * 60)
    logger.info("Done: %d/%d baselines generated successfully", passed, total)
    if failed:
        logger.warning("%d baselines FAILED — check errors above", failed)
    logger.info("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

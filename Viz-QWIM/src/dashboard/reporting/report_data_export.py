"""Data Export Module for QWIM Report Generation.

Exports dashboard data (client info, portfolio inputs/outputs, simulation
inputs/outputs) to JSON files that the Typst template reads directly via
``json()`` calls. This replaces the legacy ``{{PLACEHOLDER}}`` substitution
approach.

Each public function writes a single JSON file into the appropriate
subdirectory beneath ``src/dashboard/reporting/``:

* ``client_info.json`` — investor personal info, assets, goals, income
* ``inputs_json/*.json`` — user-selected inputs per subtab
* ``outputs_json/*.json`` — computed outputs / metrics per subtab

Dependencies
------------
* polars: DataFrame handling
* json: Serialisation

Notes
-----
All monetary values are stored as floats (not ``Decimal``) in JSON because
Typst does not natively parse ``Decimal``.  Formatting to currency strings
is done inside the Typst template.
"""

from __future__ import annotations

import json

from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

from src.dashboard.reporting._report_data_export_exports import (
    export_all_report_data_impl_QWIM,
    export_client_info_impl_QWIM,
    export_data_clients_json_impl_QWIM,
    export_data_results_json_impl_QWIM,
    export_inputs_goal_parity_impl_QWIM,
    export_inputs_optimalportfolios_optimization_impl_QWIM,
    export_inputs_portfolio_analysis_impl_QWIM,
    export_inputs_portfolio_comparison_impl_QWIM,
    export_inputs_simulation_impl_QWIM,
    export_inputs_skfolio_optimization_impl_QWIM,
    export_inputs_weights_analysis_impl_QWIM,
    export_outputs_goal_parity_impl_QWIM,
    export_outputs_optimalportfolios_optimization_impl_QWIM,
    export_outputs_portfolio_analysis_impl_QWIM,
    export_outputs_portfolio_comparison_impl_QWIM,
    export_outputs_simulation_impl_QWIM,
    export_outputs_skfolio_optimization_impl_QWIM,
    export_outputs_weights_analysis_impl_QWIM,
    export_report_config_impl_QWIM,
    export_report_metadata_impl_QWIM,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name = __name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_REPORTING_DIR = Path(__file__).resolve().parent
_INPUTS_JSON_DIR = _REPORTING_DIR / "inputs_json"
_OUTPUTS_JSON_DIR = _REPORTING_DIR / "outputs_json"

# Project-root paths for sample CSV fallback data
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_RAW_DATA_DIR = _PROJECT_ROOT / "inputs" / "raw"
_PROCESSED_DATA_DIR = _PROJECT_ROOT / "inputs" / "processed"
_SAMPLE_WEIGHTS_CSV = _RAW_DATA_DIR / "sample_portfolio_weights_ETFs.csv"
_SAMPLE_PORTFOLIO_CSV = _PROCESSED_DATA_DIR / "sample_portfolio_values.csv"
_BENCHMARK_PORTFOLIO_CSV = _PROCESSED_DATA_DIR / "benchmark_portfolio_values.csv"

# Financial constants used in metric calculations
_TRADING_DAYS_PER_YEAR: float = 252.0
_RISK_FREE_RATE_ANNUAL: float = 0.02  # 2 % nominal risk-free rate

# ---------------------------------------------------------------------------
# Pre-flight validation
# ---------------------------------------------------------------------------


def validate_report_data_quality() -> dict[str, list[str]]:
    """Check exported JSON files for data quality issues.

    Reads each JSON file in the inputs/outputs directories and checks for:

    * Missing files
    * Empty arrays where data is expected (e.g. ``weight_statistics == []``)
    * All-zero numeric fields in output tables

    Returns
    -------
    dict[str, list[str]]
        Mapping of section name to list of issue descriptions.
        An empty dict means all data is healthy.
    """
    issues: dict[str, list[str]] = {}

    def _check_json(*, path: Path, section_name: str, array_keys: list[str] | None = None) -> None:
        """Validate a JSON file exists, parses correctly, and has non-empty array keys."""
        if not path.exists():
            issues.setdefault(section_name, []).append(f"JSON file missing: {path.name}")
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            issues.setdefault(section_name, []).append(f"Cannot parse {path.name}: {exc}")
            return
        if not isinstance(data, dict) or not data:
            issues.setdefault(section_name, []).append(
                f"{path.name} is empty or not a valid object",
            )
            return
        if array_keys:
            for key in array_keys:
                arr = data.get(key)
                if not isinstance(arr, list) or len(arr) == 0:
                    issues.setdefault(section_name, []).append(
                        f"Table '{key}' in {path.name} is empty — report will show 'No data available'",
                    )

    # Report metadata & client info
    _check_json(path = _REPORTING_DIR / "report_metadata.json", section_name = "Report Metadata")
    _check_json(path = _REPORTING_DIR / "client_info.json", section_name = "Client Information")

    # Outputs with tables
    _check_json(
        path = _OUTPUTS_JSON_DIR / "outputs_weights_analysis.json",
        section_name = "Weights Analysis",
        array_keys=["weight_statistics"],
    )
    _check_json(
        path = _OUTPUTS_JSON_DIR / "outputs_portfolio_analysis.json",
        section_name = "Portfolio Analysis",
        array_keys=["basic_statistics", "performance_metrics"],
    )
    _check_json(
        path = _OUTPUTS_JSON_DIR / "outputs_skfolio_optimization.json",
        section_name = "Skfolio Optimization",
        array_keys=["weights_comparison", "statistics_comparison"],
    )
    # Simulation — check summary_statistics for all-zero
    sim_path = _OUTPUTS_JSON_DIR / "outputs_simulation.json"
    if sim_path.exists():  # pragma: no branch
        try:
            sim_data = json.loads(sim_path.read_text(encoding="utf-8"))
            ss = sim_data.get("summary_statistics", {})
            if isinstance(ss, dict):
                numeric_vals = [
                    v
                    for k, v in ss.items()
                    if isinstance(v, (int, float)) and not isinstance(v, bool) and k != "initial_value"
                ]
                if numeric_vals and all(v == 0 or v == 0.0 for v in numeric_vals):
                    issues.setdefault("Simulation", []).append(
                        "All simulation statistics are zero — simulation may not have been run",
                    )
        except Exception:
            pass

    return issues


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _ensure_dir(*, directory: Path) -> None:
    """Create *directory* if it does not already exist."""
    directory.mkdir(parents=True, exist_ok=True)


def _write_json(*, file_path: Path, data: dict[str, Any]) -> None:
    """Serialise *data* to *file_path* as pretty-printed JSON."""
    _ensure_dir(directory = file_path.parent)
    file_path.write_text(
        json.dumps(data, indent=2, default=str, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    _logger.info("Wrote JSON: %s (%d bytes)", file_path.name, file_path.stat().st_size)


def _read_json_dict(*, file_path: Path) -> dict[str, Any]:
    """Read a JSON object from *file_path*, returning ``{}`` on failure."""
    try:
        raw_data = json.loads(file_path.read_text(encoding="utf-8"))
    except Exception as exc:
        _logger.debug("Could not read JSON from %s: %s", file_path, exc)
        return {}

    if isinstance(raw_data, dict):
        return raw_data

    return {}


def _safe_reactive_get(*, reactive_value: Any) -> Any:
    """Unwrap a Shiny ``reactive.Value`` or return the raw value."""
    if reactive_value is None:
        return None
    if hasattr(reactive_value, "get"):
        try:
            return reactive_value.get()
        except Exception:
            return None
    return reactive_value


def _safe_float(*, value: Any, default: float = 0.0) -> float:
    """Convert *value* to ``float``, returning *default* on failure."""
    if value is None:
        return default
    if isinstance(value, bool):
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def _safe_bool(*, value: Any, default: bool = False) -> bool:
    """Convert *value* to ``bool``, returning *default* for non-booleans."""
    if isinstance(value, bool):
        return value

    return default


def _safe_str(*, value: Any, default: str = "N/A") -> str:
    """Convert *value* to ``str``, returning *default* on failure."""
    if value is None:
        return default
    return str(value)


def _polars_to_records(*, df: pl.DataFrame | None) -> list[dict[str, Any]]:
    """Convert a Polars DataFrame to a list of row-dicts suitable for JSON."""
    if df is None or not isinstance(df, pl.DataFrame) or df.height == 0:
        return []
    return df.to_dicts()


# ---------------------------------------------------------------------------
# Sample-data helpers (used when live dashboard data is unavailable)
# ---------------------------------------------------------------------------


def _load_sample_portfolio_data() -> tuple[pl.DataFrame | None, pl.DataFrame | None]:
    """Load sample portfolio and benchmark value CSVs from *inputs/processed/*.

    Returns
    -------
    tuple[pl.DataFrame | None, pl.DataFrame | None]
        ``(portfolio_values_df, benchmark_values_df)`` — either may be
        ``None`` when the file cannot be read.
    """

    def _load(*, path: Path) -> pl.DataFrame | None:
        """Read a CSV at *path* and return a cleaned DataFrame, or None on failure."""
        try:
            df = pl.read_csv(path)
            # Dates stored as timezone-aware strings: "2012-01-03 00:00:00-05:00"
            df = df.with_columns(
                pl.col("Date").str.slice(0, 10).str.strptime(pl.Date, "%Y-%m-%d").alias("Date"),
            )
            df = df.rename({"Value": "portfolio_value"})
            return df.sort("Date")
        except Exception as exc:
            _logger.debug("Could not load sample data from %s: %s", path, exc)
            return None

    return _load(path = _SAMPLE_PORTFOLIO_CSV), _load(path = _BENCHMARK_PORTFOLIO_CSV)


def _load_sample_weights_data() -> pl.DataFrame | None:
    """Load sample ETF weights from *inputs/raw/sample_portfolio_weights_ETFs.csv*."""
    try:
        weights_df = pl.read_csv(_SAMPLE_WEIGHTS_CSV)
        if "Date" in weights_df.columns:
            weights_df = weights_df.with_columns(
                pl.col("Date").str.slice(0, 10).str.strptime(pl.Date, "%Y-%m-%d").alias("Date"),
            )
        return weights_df.sort("Date") if "Date" in weights_df.columns else weights_df
    except Exception as exc:
        _logger.debug("Could not load sample weights from %s: %s", _SAMPLE_WEIGHTS_CSV, exc)
        return None


def _compute_weight_statistics_from_weights(
    *, weights_df: pl.DataFrame) -> list[dict[str, Any]]:
    """Compute report-ready weight statistics from a sample weights dataframe.

    Boolean component columns are treated as invalid weight data and skipped.
    """
    if weights_df.is_empty():
        return []

    component_columns = [column_name for column_name in weights_df.columns if column_name != "Date"]
    statistics_rows: list[dict[str, Any]] = []

    for component_name in component_columns:
        component_series_raw = weights_df.get_column(component_name).drop_nulls()
        if component_series_raw.len() == 0 or component_series_raw.dtype == pl.Boolean:
            continue

        component_values = (
            component_series_raw.cast(pl.Float64, strict=False)
            .drop_nulls()
        )
        if component_values.len() == 0:
            continue

        std_weight = float(component_values.std()) if component_values.len() > 1 else 0.0
        if np.isnan(std_weight):
            std_weight = 0.0

        statistics_rows.append(
            {
                "component": component_name,
                "current_weight": float(component_values[-1]),
                "mean_weight": float(component_values.mean()),
                "min_weight": float(component_values.min()),
                "max_weight": float(component_values.max()),
                "std_weight": std_weight,
            },
        )

    return statistics_rows


def _safe_portfolio_value_array(
    *, values_df: pl.DataFrame | None) -> np.ndarray | None:
    """Return numeric portfolio values, or ``None`` for invalid inputs."""
    if values_df is None or not isinstance(values_df, pl.DataFrame):
        return None
    if "portfolio_value" not in values_df.columns:
        return None

    portfolio_value_series = values_df.get_column("portfolio_value").drop_nulls()
    if portfolio_value_series.len() < 2 or portfolio_value_series.dtype == pl.Boolean:
        return None

    numeric_portfolio_values = portfolio_value_series.cast(pl.Float64, strict=False).drop_nulls()
    if numeric_portfolio_values.len() < 2:
        return None

    return numeric_portfolio_values.to_numpy()


def _compute_portfolio_metrics_from_values(
    *, pv: pl.DataFrame, bv: pl.DataFrame | None = None, time_period: str = "All") -> dict[str, Any]:
    """Compute portfolio-comparison metrics from Polars DataFrames.

    Parameters
    ----------
    pv : pl.DataFrame
        Portfolio value series – must have ``Date`` and ``portfolio_value`` columns.
    bv : pl.DataFrame | None
        Benchmark value series in the same format.
    time_period : str
        Display label for the analysis period.

    Returns
    -------
    dict[str, Any]
        Flat dictionary of computed metrics (same keys as ``Portfolio_Comparison_Stats``).
    """
    start_date = str(pv["Date"][0]) if "Date" in pv.columns and pv.height > 0 else ""
    end_date = str(pv["Date"][-1]) if "Date" in pv.columns and pv.height > 0 else ""
    total_return = 0.0
    ann_return = 0.0
    ann_vol = 0.0
    max_drawdown = 0.0
    sharpe = 0.0

    result: dict[str, Any] = {
        "time_period": time_period,
        "start_date": start_date,
        "end_date": end_date,
        "viz_type": "normalized",
        "total_return_portfolio": total_return,
        "annualized_return_portfolio": ann_return,
        "volatility_portfolio": ann_vol,
        "max_drawdown_portfolio": max_drawdown,
        "sharpe_ratio_portfolio": sharpe,
        "total_return_benchmark": 0.0,
        "annualized_return_benchmark": 0.0,
        "volatility_benchmark": 0.0,
        "max_drawdown_benchmark": 0.0,
        "sharpe_ratio_benchmark": 0.0,
        "total_return_difference": total_return,
        "annualized_return_difference": ann_return,
        "volatility_difference": ann_vol,
        "max_drawdown_difference": max_drawdown,
        "sharpe_ratio_difference": sharpe,
        "correlation": 0.0,
        "tracking_error": 0.0,
        "information_ratio": 0.0,
    }

    pv_arr = _safe_portfolio_value_array(values_df = pv)
    if pv_arr is None:
        return result

    p_rets = np.diff(pv_arr) / pv_arr[:-1]
    n_days = len(pv_arr)
    n_years = n_days / _TRADING_DAYS_PER_YEAR

    total_return = float((pv_arr[-1] - pv_arr[0]) / pv_arr[0])
    ann_return = float((1 + total_return) ** (1 / n_years) - 1) if n_years > 0 else 0.0
    p_std = float(np.std(p_rets, ddof=1))
    ann_vol = p_std * float(np.sqrt(_TRADING_DAYS_PER_YEAR))

    cum_max = np.maximum.accumulate(pv_arr)
    max_drawdown = float(np.min((pv_arr - cum_max) / cum_max))

    rf_daily = _RISK_FREE_RATE_ANNUAL / _TRADING_DAYS_PER_YEAR
    excess = p_rets - rf_daily
    excess_std = float(np.std(excess, ddof=1))
    sharpe = (
        float(np.mean(excess)) / excess_std * float(np.sqrt(_TRADING_DAYS_PER_YEAR))
        if excess_std > 0
        else 0.0
    )

    result.update(
        {
            "total_return_portfolio": total_return,
            "annualized_return_portfolio": ann_return,
            "volatility_portfolio": ann_vol,
            "max_drawdown_portfolio": max_drawdown,
            "sharpe_ratio_portfolio": sharpe,
            "total_return_difference": total_return,
            "annualized_return_difference": ann_return,
            "volatility_difference": ann_vol,
            "max_drawdown_difference": max_drawdown,
            "sharpe_ratio_difference": sharpe,
        },
    )

    if bv is not None and bv.height >= 2:
        bv_arr = _safe_portfolio_value_array(values_df = bv)
        if bv_arr is not None:
            b_rets = np.diff(bv_arr) / bv_arr[:-1]

            b_total = float((bv_arr[-1] - bv_arr[0]) / bv_arr[0])
            b_ann = float((1 + b_total) ** (1 / n_years) - 1) if n_years > 0 else 0.0
            b_std = float(np.std(b_rets, ddof=1))
            b_vol = b_std * float(np.sqrt(_TRADING_DAYS_PER_YEAR))

            b_cum_max = np.maximum.accumulate(bv_arr)
            b_max_drawdown = float(np.min((bv_arr - b_cum_max) / b_cum_max))

            b_excess = b_rets - rf_daily
            b_excess_std = float(np.std(b_excess, ddof=1))
            b_sharpe = (
                float(np.mean(b_excess)) / b_excess_std * float(np.sqrt(_TRADING_DAYS_PER_YEAR))
                if b_excess_std > 0
                else 0.0
            )

            min_len = min(len(p_rets), len(b_rets))
            if min_len > 1:
                correlation = float(np.corrcoef(p_rets[:min_len], b_rets[:min_len])[0, 1])
                active = p_rets[:min_len] - b_rets[:min_len]
                te_daily = float(np.std(active, ddof=1))
                tracking_error = te_daily * float(np.sqrt(_TRADING_DAYS_PER_YEAR))
                info_ratio = (ann_return - b_ann) / tracking_error if tracking_error > 0 else 0.0
            else:
                correlation = 0.0
                tracking_error = 0.0
                info_ratio = 0.0

            result.update(
                {
                    "total_return_benchmark": b_total,
                    "annualized_return_benchmark": b_ann,
                    "volatility_benchmark": b_vol,
                    "max_drawdown_benchmark": b_max_drawdown,
                    "sharpe_ratio_benchmark": b_sharpe,
                    "total_return_difference": total_return - b_total,
                    "annualized_return_difference": ann_return - b_ann,
                    "volatility_difference": ann_vol - b_vol,
                    "max_drawdown_difference": max_drawdown - b_max_drawdown,
                    "sharpe_ratio_difference": sharpe - b_sharpe,
                    "correlation": correlation,
                    "tracking_error": tracking_error,
                    "information_ratio": info_ratio,
                },
            )

    return result


def _compute_portfolio_analysis_stats_from_values(
    *, pv: pl.DataFrame, bv: pl.DataFrame | None = None) -> dict[str, Any]:
    """Compute basic statistics and risk-adjusted performance metrics.

    Parameters
    ----------
    pv : pl.DataFrame
        Portfolio value series.
    bv : pl.DataFrame | None
        Optional benchmark value series.

    Returns
    -------
    dict[str, Any]
        Dict with ``basic_statistics`` and ``performance_metrics`` lists.
    """
    bm_mean = bm_std = bm_skew = bm_kurt = ""

    basic_statistics = [
        {"metric": "Mean Daily Return", "portfolio": "0.0000%", "benchmark": bm_mean},
        {"metric": "Std Dev Daily Return", "portfolio": "0.0000%", "benchmark": bm_std},
        {"metric": "Skewness", "portfolio": "0.0000", "benchmark": bm_skew},
        {"metric": "Excess Kurtosis", "portfolio": "0.0000", "benchmark": bm_kurt},
    ]

    performance_metrics = [
        {"metric": "Annualised Return", "value": "0.00%"},
        {"metric": "Annualised Volatility", "value": "0.00%"},
        {"metric": "Sharpe Ratio (2 % Rf)", "value": "0.0000"},
        {"metric": "Maximum Drawdown", "value": "0.00%"},
        {"metric": "Analysis Period (yrs)", "value": "0.0"},
    ]

    pv_arr = _safe_portfolio_value_array(values_df = pv)
    if pv_arr is None:
        return {"basic_statistics": basic_statistics, "performance_metrics": performance_metrics}

    p_rets = np.diff(pv_arr) / pv_arr[:-1]
    n = len(p_rets)
    mean_d = float(np.mean(p_rets))
    std_d = float(np.std(p_rets, ddof=1))

    skewness = float(np.mean(((p_rets - mean_d) / std_d) ** 3)) if n > 2 and std_d > 0 else 0.0
    kurtosis = (
        float(np.mean(((p_rets - mean_d) / std_d) ** 4)) - 3.0 if n > 3 and std_d > 0 else 0.0
    )

    if bv is not None and bv.height >= 2:
        bv_arr = _safe_portfolio_value_array(values_df = bv)
        if bv_arr is not None:
            b_rets = np.diff(bv_arr) / bv_arr[:-1]
            bm_mean_d = float(np.mean(b_rets))
            bm_std_d = float(np.std(b_rets, ddof=1))
            nb = len(b_rets)
            bm_mean = f"{bm_mean_d * 100:.4f}%"
            bm_std = f"{bm_std_d * 100:.4f}%"
            bm_skew = (
                f"{float(np.mean(((b_rets - bm_mean_d) / bm_std_d) ** 3)):.4f}"
                if nb > 2 and bm_std_d > 0
                else "0.0000"
            )
            bm_kurt = (
                f"{float(np.mean(((b_rets - bm_mean_d) / bm_std_d) ** 4)) - 3.0:.4f}"
                if nb > 3 and bm_std_d > 0
                else "0.0000"
            )

    basic_statistics = [
        {"metric": "Mean Daily Return", "portfolio": f"{mean_d * 100:.4f}%", "benchmark": bm_mean},
        {"metric": "Std Dev Daily Return", "portfolio": f"{std_d * 100:.4f}%", "benchmark": bm_std},
        {"metric": "Skewness", "portfolio": f"{skewness:.4f}", "benchmark": bm_skew},
        {"metric": "Excess Kurtosis", "portfolio": f"{kurtosis:.4f}", "benchmark": bm_kurt},
    ]

    total_return = float((pv_arr[-1] - pv_arr[0]) / pv_arr[0])
    n_years = len(pv_arr) / _TRADING_DAYS_PER_YEAR
    ann_return = float((1 + total_return) ** (1 / n_years) - 1) if n_years > 0 else 0.0
    ann_vol = std_d * float(np.sqrt(_TRADING_DAYS_PER_YEAR))
    rf_daily = _RISK_FREE_RATE_ANNUAL / _TRADING_DAYS_PER_YEAR
    excess = p_rets - rf_daily
    exc_std = float(np.std(excess, ddof=1))
    sharpe = (
        float(np.mean(excess)) / exc_std * float(np.sqrt(_TRADING_DAYS_PER_YEAR))
        if exc_std > 0
        else 0.0
    )
    cum_max = np.maximum.accumulate(pv_arr)
    max_drawdown = float(np.min((pv_arr - cum_max) / cum_max))

    performance_metrics = [
        {"metric": "Annualised Return", "value": f"{ann_return * 100:.2f}%"},
        {"metric": "Annualised Volatility", "value": f"{ann_vol * 100:.2f}%"},
        {"metric": "Sharpe Ratio (2 % Rf)", "value": f"{sharpe:.4f}"},
        {"metric": "Maximum Drawdown", "value": f"{max_drawdown * 100:.2f}%"},
        {"metric": "Analysis Period (yrs)", "value": f"{n_years:.1f}"},
    ]

    return {"basic_statistics": basic_statistics, "performance_metrics": performance_metrics}


def _compute_simulation_stats_from_values(
    *, pv: pl.DataFrame, num_scenarios: int = 1000, num_days: int = 252, initial_value: float = 100.0, seed: int = 42) -> dict[str, Any]:
    """Run a simple normal Monte Carlo simulation calibrated to historical returns.

    Parameters
    ----------
    pv : pl.DataFrame
        Portfolio value series used to calibrate mean / std of returns.
    num_scenarios : int
        Number of simulation paths.
    num_days : int
        Simulation horizon in trading days.
    initial_value : float
        Starting portfolio value.
    seed : int
        RNG seed for reproducibility.

    Returns
    -------
    dict[str, Any]
        Summary statistics dict matching the ``Simulation_Stats`` schema.
    """
    result = {
        "num_scenarios": num_scenarios,
        "horizon_days": num_days,
        "initial_value": initial_value,
        "mean_terminal_value": 0.0,
        "median_terminal_value": 0.0,
        "std_dev_terminal_value": 0.0,
        "percentile_5": 0.0,
        "percentile_25": 0.0,
        "percentile_75": 0.0,
        "percentile_95": 0.0,
        "min_terminal_value": 0.0,
        "max_terminal_value": 0.0,
        "probability_of_loss": 0.0,
    }

    pv_arr = _safe_portfolio_value_array(values_df = pv)
    if pv_arr is None:
        return result

    rets = np.diff(pv_arr) / pv_arr[:-1]
    mu = float(np.mean(rets))
    sigma = float(np.std(rets, ddof=1))

    rng = np.random.default_rng(seed)
    sim_rets = rng.normal(mu, sigma, size=(num_scenarios, num_days))
    terminal_vals = initial_value * np.prod(1.0 + sim_rets, axis=1)

    result.update(
        {
            "mean_terminal_value": float(np.mean(terminal_vals)),
            "median_terminal_value": float(np.median(terminal_vals)),
            "std_dev_terminal_value": float(np.std(terminal_vals, ddof=1)),
            "percentile_5": float(np.percentile(terminal_vals, 5)),
            "percentile_25": float(np.percentile(terminal_vals, 25)),
            "percentile_75": float(np.percentile(terminal_vals, 75)),
            "percentile_95": float(np.percentile(terminal_vals, 95)),
            "min_terminal_value": float(np.min(terminal_vals)),
            "max_terminal_value": float(np.max(terminal_vals)),
            "probability_of_loss": float(np.mean(terminal_vals < initial_value)),
        },
    )

    return result


# =========================================================================
# 0.  REPORT METADATA
# =========================================================================


def export_report_metadata(
    *, reactives_shiny: dict | None = None) -> Path:
    """Export report metadata to ``report_metadata.json``."""
    return export_report_metadata_impl_QWIM(reactives_shiny = reactives_shiny)


# =========================================================================
# 1.  CLIENT INFO
# =========================================================================


def export_client_info(
    *, reactives_shiny: dict | None) -> Path:
    """Export investor data to ``client_info.json``."""
    return export_client_info_impl_QWIM(reactives_shiny = reactives_shiny)


# =========================================================================
# 2.  PORTFOLIO ANALYSIS — inputs & outputs
# =========================================================================


def export_inputs_portfolio_analysis(
    *, reactives_shiny: dict | None) -> Path:
    """Export Portfolio Analysis inputs to JSON."""
    return export_inputs_portfolio_analysis_impl_QWIM(reactives_shiny = reactives_shiny)


def export_outputs_portfolio_analysis(
    *, reactives_shiny: dict | None) -> Path:
    """Export Portfolio Analysis outputs to JSON."""
    return export_outputs_portfolio_analysis_impl_QWIM(reactives_shiny = reactives_shiny)


# =========================================================================
# 3.  PORTFOLIO COMPARISON — inputs & outputs
# =========================================================================


def export_inputs_portfolio_comparison(
    *, reactives_shiny: dict | None) -> Path:
    """Export Portfolio Comparison inputs to JSON."""
    return export_inputs_portfolio_comparison_impl_QWIM(reactives_shiny = reactives_shiny)


def export_outputs_portfolio_comparison(
    *, reactives_shiny: dict | None) -> Path:
    """Export Portfolio Comparison outputs to JSON."""
    return export_outputs_portfolio_comparison_impl_QWIM(reactives_shiny = reactives_shiny)


# =========================================================================
# 4.  WEIGHTS ANALYSIS — inputs & outputs
# =========================================================================


def export_inputs_weights_analysis(
    *, reactives_shiny: dict | None) -> Path:
    """Export Weights Analysis inputs to JSON."""
    return export_inputs_weights_analysis_impl_QWIM(reactives_shiny = reactives_shiny)


def export_outputs_weights_analysis(
    *, reactives_shiny: dict | None) -> Path:
    """Export Weights Analysis outputs to JSON."""
    return export_outputs_weights_analysis_impl_QWIM(reactives_shiny = reactives_shiny)


# =========================================================================
# 5.  SKFOLIO OPTIMIZATION — inputs & outputs
# =========================================================================


def export_inputs_skfolio_optimization(
    *, reactives_shiny: dict | None) -> Path:
    """Export skfolio Optimization inputs to JSON."""
    return export_inputs_skfolio_optimization_impl_QWIM(reactives_shiny = reactives_shiny)


def export_outputs_skfolio_optimization(
    *, reactives_shiny: dict | None) -> Path:
    """Export skfolio Optimization outputs to JSON."""
    return export_outputs_skfolio_optimization_impl_QWIM(reactives_shiny = reactives_shiny)


# =========================================================================
# 5b.  OPTIMALPORTFOLIOS OPTIMIZATION — inputs & outputs
# =========================================================================


def export_inputs_optimalportfolios_optimization(
    *, reactives_shiny: dict | None) -> Path:
    """Export OptimalPortfolios Optimization inputs to JSON."""
    return export_inputs_optimalportfolios_optimization_impl_QWIM(reactives_shiny = reactives_shiny)


def export_outputs_optimalportfolios_optimization(
    *, reactives_shiny: dict | None) -> Path:
    """Export OptimalPortfolios Optimization outputs to JSON."""
    return export_outputs_optimalportfolios_optimization_impl_QWIM(reactives_shiny = reactives_shiny)


# =========================================================================
# 6.  SIMULATION — inputs & outputs
# =========================================================================


def export_inputs_simulation(
    *, reactives_shiny: dict | None) -> Path:
    """Export Simulation inputs to JSON."""
    return export_inputs_simulation_impl_QWIM(reactives_shiny = reactives_shiny)


def export_outputs_simulation(
    *, reactives_shiny: dict | None) -> Path:
    """Export Simulation outputs to JSON."""
    return export_outputs_simulation_impl_QWIM(reactives_shiny = reactives_shiny)


# =========================================================================
# 7.  GOAL PARITY — inputs & outputs
# =========================================================================


def export_inputs_goal_parity(
    *, reactives_shiny: dict | None) -> Path:
    """Export Goal Parity investor-profile inputs to JSON."""
    return export_inputs_goal_parity_impl_QWIM(reactives_shiny = reactives_shiny)


def export_outputs_goal_parity(
    *, reactives_shiny: dict | None) -> Path:
    """Export Goal Parity strategic/rebalancing outputs to JSON."""
    return export_outputs_goal_parity_impl_QWIM(reactives_shiny = reactives_shiny)


# =========================================================================
# AGGREGATE EXPORT
# =========================================================================


def export_all_report_data(
    *, reactives_shiny: dict | None) -> dict[str, Path]:
    """Export every JSON file required by the Typst report template."""
    return export_all_report_data_impl_QWIM(reactives_shiny = reactives_shiny)


# =========================================================================
# helpers to access reactives
# =========================================================================


def _get_user_inputs(*, reactives_shiny: dict | None) -> dict[str, Any]:
    """Safely extract ``User_Inputs_Shiny`` from reactives dict."""
    if not reactives_shiny or not isinstance(reactives_shiny, dict):
        return {}
    raw = reactives_shiny.get("User_Inputs_Shiny", {})
    return raw if isinstance(raw, dict) else {}


def _get_inner_variables(*, reactives_shiny: dict | None) -> dict[str, Any]:
    """Safely extract ``Inner_Variables_Shiny`` from reactives dict."""
    if not reactives_shiny or not isinstance(reactives_shiny, dict):
        return {}
    raw = reactives_shiny.get("Inner_Variables_Shiny", {})
    return raw if isinstance(raw, dict) else {}


def _get_data_results_value(
    *, reactives_shiny: dict | None, subtab_key: str) -> dict[str, Any]:
    """Read one ``Data_Results`` subtab key as a JSON-serialisable dict.

    Calls :func:`~src.dashboard.shiny_utils.utils_reporting.build_results_data_json_from_reactives`
    and returns a JSON-serialisable dict.  Returns an empty dict on any error
    (including when the subtab value has not yet been populated).

    Parameters
    ----------
    reactives_shiny : dict | None
        Shared reactive state dictionary.
    subtab_key : str
        One of the 10 valid keys in ``Data_Results``
        (e.g. ``"Portfolio_Analysis_Inputs"``).

    Returns
    -------
    dict[str, Any]
        JSON-serialisable dict for the subtab key, or ``{}`` when not yet
        populated or on error.
    """
    if not reactives_shiny or not isinstance(reactives_shiny, dict):
        return {}
    try:
        from src.dashboard.shiny_utils.utils_reporting import (
            build_results_data_json_from_reactives,
        )

        return build_results_data_json_from_reactives(reactives_shiny = reactives_shiny, subtab_key = subtab_key)
    except Exception as exc:
        _logger.debug(
            "_get_data_results_value: could not get '%s' from Data_Results: %s",
            subtab_key,
            exc,
        )
        return {}


# =========================================================================
# Consolidated 3-file export helpers (for Typst R6 pipeline)
# =========================================================================


def export_data_clients_json(
    *, reactives_shiny: dict | None) -> Path:
    """Write ``data_clients.json`` combining client and advisor info."""
    return export_data_clients_json_impl_QWIM(reactives_shiny = reactives_shiny)


def export_data_results_json(
    *, reactives_shiny: dict | None) -> Path:
    """Write ``data_results.json`` combining all analysis inputs and outputs."""
    return export_data_results_json_impl_QWIM(reactives_shiny = reactives_shiny)


def export_report_config(
    *, reactives_shiny: dict | None, section_flags: dict[str, bool], report_title: str = "") -> Path:
    """Write ``report_config.json`` with section enable flags."""
    return export_report_config_impl_QWIM(
        reactives_shiny = reactives_shiny,
        section_flags = section_flags,
        report_title = report_title,
    )

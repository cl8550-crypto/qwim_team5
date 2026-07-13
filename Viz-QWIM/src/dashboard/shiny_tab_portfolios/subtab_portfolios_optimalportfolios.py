"""Portfolio Optimization with OptimalPortfolios Module.

Provides comprehensive portfolio optimization using methods from the OptimalPortfolios Python
package. Mirrors the skfolio subtab architecture with two-method side-by-side comparison.

![Portfolio Analysis](https://img.shields.io/badge/Portfolio-Analysis-blue)
![Python](https://img.shields.io/badge/python-3.12+-green)
![Shiny](https://img.shields.io/badge/shiny-for_python-orange)

## Overview

The OptimalPortfolios Portfolio Optimization module enables users to compare different portfolio
optimization strategies using state-of-the-art methods from the optimalportfolios package.

**Module Information:**
- **Author**: QWIM Development Team
- **Version**: 0.5.1
- **Last Updated**: May 2026
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np

# pandas required by Shiny API — Shiny demands DataFrame input; Polars not accepted here
import pandas as pd
import polars as pl

from shiny import module, reactive, render, ui
from shinywidgets import output_widget, render_widget

from src.dashboard.shiny_utils.utils_reporting import (
    save_portfolio_optimization_optimalportfolios_inputs_to_reactives,
    save_portfolio_optimization_optimalportfolios_outputs_to_reactives,
)
from src.dashboard.shiny_tab_portfolios._subtab_portfolios_optimalportfolios_outputs import (
    build_optimalportfolios_statistics_rows_impl_QWIM,
    compute_optimalportfolios_performance_series_impl_QWIM,
    render_optimalportfolios_performance_plot_impl_QWIM,
    render_optimalportfolios_results_table_impl_QWIM,
    render_optimalportfolios_statistics_table_impl_QWIM,
    render_optimalportfolios_weights_plot_impl_QWIM,
)
from src.models.portfolio_optimization.pkg_optimalportfolios import (
    calc_optimalportfolios_budgeted_risk_contribution,
    calc_optimalportfolios_maximum_cara_gaussian_mixture,
    calc_optimalportfolios_maximum_diversification,
    calc_optimalportfolios_maximum_quadratic_utility,
    calc_optimalportfolios_maximum_sharpe_ratio,
    calc_optimalportfolios_minimum_variance,
    calc_optimalportfolios_tracking_error_minimization,
)
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


qs: Any = None
try:
    import quantstats as qs

    HAS_QUANTSTATS = True
except ImportError:  # pragma: no cover
    HAS_QUANTSTATS = False

_logger = get_logger(name = __name__)

# =============================================================================
# Constants and Configuration
# =============================================================================

OUTPUT_DIR = Path("output")

#: All 7 implemented OptimalPortfolios methods in a flat dict {key: label}
OPTIMALPORTFOLIOS_METHODS: dict[str, str] = {
    "MIN_VARIANCE": "Minimum Variance",
    "MAX_QUADRATIC_UTILITY": "Maximum Quadratic Utility",
    "RISK_PARITY": "Risk Parity (Equal Risk Contribution)",
    "MAX_DIVERSIFICATION": "Maximum Diversification",
    "MAX_SHARPE": "Maximum Sharpe Ratio",
    "MAX_CARA_GMM": "Maximum CARA Utility (Gaussian Mixture)",
    "TRACKING_ERROR_MIN": "Tracking Error Minimization",
}

DEFAULT_METHOD1 = "MIN_VARIANCE"
DEFAULT_METHOD2 = "MAX_SHARPE"
DEFAULT_TIME_PERIOD = "3y"


# =============================================================================
# Pure helper functions (module-level, testable)
# =============================================================================


def resolve_optimalportfolios_method(*, method_value: Any, default_value: str) -> str:
    """Return a valid OptimalPortfolios method key with a deterministic fallback."""
    if isinstance(method_value, str) and method_value in OPTIMALPORTFOLIOS_METHODS:
        return method_value
    return default_value


def resolve_optimalportfolios_risk_aversion(
    *, value: Any, default_value: float = 1.0) -> float:
    """Return a safe positive float for risk aversion."""
    if isinstance(value, bool):
        return default_value

    try:
        v = float(value)
        return v if v > 0 else default_value
    except (TypeError, ValueError):
        return default_value


def resolve_optimalportfolios_risk_free_rate(
    *, value: Any, default_value: float = 0.0) -> float:
    """Return a safe float for risk-free rate."""
    if isinstance(value, bool):
        return default_value

    try:
        return float(value)
    except (TypeError, ValueError):
        return default_value


def resolve_optimalportfolios_n_components(
    *, value: Any, default_value: int = 2) -> int:
    """Return a safe positive integer for GMM components."""
    if isinstance(value, bool):
        return default_value

    try:
        v = int(value)
        return v if v >= 1 else default_value
    except (TypeError, ValueError):
        return default_value


def _normalize_optimalportfolios_method_params(
    *, method_key: str, method_params: dict[str, Any]) -> dict[str, Any]:
    """Normalize report snapshot method params that later feed optimization dispatch."""
    method_params_normalized = dict(method_params)

    if method_key in {"MAX_QUADRATIC_UTILITY", "MAX_CARA_GMM"} and "risk_aversion" in method_params_normalized:
        method_params_normalized["risk_aversion"] = resolve_optimalportfolios_risk_aversion(
            value = method_params_normalized["risk_aversion"],
        )

    if method_key == "MAX_SHARPE" and "risk_free_rate" in method_params_normalized:
        method_params_normalized["risk_free_rate"] = resolve_optimalportfolios_risk_free_rate(
            value = method_params_normalized["risk_free_rate"],
        )

    if method_key == "MAX_CARA_GMM" and "n_components" in method_params_normalized:
        method_params_normalized["n_components"] = resolve_optimalportfolios_n_components(
            value = method_params_normalized["n_components"],
        )

    return method_params_normalized


def build_optimalportfolios_input_snapshot(
    *,
    time_period: Any,
    benchmark_key: Any,
    method1_type: Any,
    method1_params: dict[str, Any],
    method2_type: Any,
    method2_params: dict[str, Any],
) -> dict[str, Any]:
    """Build a report-ready snapshot of the current OptimalPortfolios input selections.

    Numeric optimizer parameters are normalized here so invalid boolean values
    stay on the same defaults used by the dedicated resolver helpers.
    """
    resolved_m1 = resolve_optimalportfolios_method(method_value = method1_type, default_value = DEFAULT_METHOD1)
    resolved_m2 = resolve_optimalportfolios_method(method_value = method2_type, default_value = DEFAULT_METHOD2)
    return {
        "time_period": str(time_period or DEFAULT_TIME_PERIOD),
        "benchmark_key": str(benchmark_key or "Benchmark_Portfolio"),
        "method1": {
            "type": resolved_m1,
            **_normalize_optimalportfolios_method_params(method_key = resolved_m1, method_params = method1_params),
        },
        "method2": {
            "type": resolved_m2,
            **_normalize_optimalportfolios_method_params(method_key = resolved_m2, method_params = method2_params),
        },
    }


def build_optimalportfolios_weights_rows(
    *, portfolio_1: Any, portfolio_2: Any) -> list[dict[str, Any]]:
    """Build report-ready portfolio weight rows for both optimized portfolios."""
    import math

    weights_1 = portfolio_1.get_portfolio_weights()
    weights_2 = portfolio_2.get_portfolio_weights()
    assets = [a for a in weights_1.columns if a != "Date"]

    rows: list[dict[str, Any]] = []
    for asset in assets:
        weight_1_raw = weights_1[asset][0]
        weight_2_raw = weights_2[asset][0]

        if isinstance(weight_1_raw, bool) or isinstance(weight_2_raw, bool):
            continue

        w1 = float(weight_1_raw)
        w2 = float(weight_2_raw)
        if not math.isnan(w1) and not math.isnan(w2):
            rows.append({"asset": asset, "method1": w1, "method2": w2})
    return rows


def build_optimalportfolios_performance_summary(
    *, portfolio_1: Any, portfolio_2: Any, perf_1: pl.DataFrame | None, perf_2: pl.DataFrame | None) -> dict[str, dict[str, Any]]:
    """Build annualized performance metrics for report export."""

    def _stats(*, series: pl.DataFrame | None) -> dict[str, float]:
        """Compute annualised return, volatility, and Sharpe ratio for *series*."""
        if series is None or len(series) < 2:
            return {"annualized_return": 0.0, "volatility": 0.0, "sharpe_ratio": 0.0}

        value_list = series["Value"].to_list()
        if any(isinstance(item_value, bool) for item_value in value_list):
            return {"annualized_return": 0.0, "volatility": 0.0, "sharpe_ratio": 0.0}

        vals = np.array(value_list, dtype=np.float64)
        daily_rets = np.diff(vals) / vals[:-1]
        ann_ret = float((vals[-1] / vals[0]) ** (252.0 / len(daily_rets)) - 1)
        vol = float(np.std(daily_rets, ddof=1) * np.sqrt(252))
        sharpe = float((ann_ret - 0.02) / vol) if vol > 1e-12 else 0.0
        return {"annualized_return": ann_ret, "volatility": vol, "sharpe_ratio": sharpe}

    return {
        "method1": {"label": str(portfolio_1.get_portfolio_name), **_stats(series = perf_1)},
        "method2": {"label": str(portfolio_2.get_portfolio_name), **_stats(series = perf_2)},
    }


def merge_optimalportfolios_output_snapshot(
    *, existing_data: dict[str, Any] | None, data_partial: dict[str, Any]) -> dict[str, Any]:
    """Merge new OptimalPortfolios report data into any existing snapshot."""
    if not isinstance(existing_data, dict):
        existing_data = {}
    return existing_data | data_partial


# =============================================================================
# Module UI
# =============================================================================


@module.ui
def subtab_portfolios_optimalportfolios_ui(
    *, data_utils: dict, data_inputs: dict) -> Any:  # pragma: no cover
    """Create UI for OptimalPortfolios portfolio optimization comparison subtab."""
    # Build benchmark choices from available ETFs
    etf_data = data_inputs.get("Time_Series_ETFs")
    etf_cols = [c for c in etf_data.columns if c != "Date"] if etf_data is not None else []
    benchmark_choices: dict[str, str] = {"Benchmark_Portfolio": "Benchmark Portfolio (default)"}
    for etf in etf_cols:
        benchmark_choices[etf] = etf

    return ui.div(
        ui.h3("Portfolio Optimization with OptimalPortfolios"),
        ui.p(
            "Compare different portfolio optimization strategies using methods from the "
            "optimalportfolios package.",
            class_="text-muted mb-4",
        ),
        ui.layout_sidebar(
            ui.sidebar(
                ui.h5("⚙️ Optimization Configuration", class_="mb-3"),
                # Optimize button — placed above config for immediate access
                ui.input_action_button(
                    "input_ID_tab_portfolios_subtab_optimalportfolios_btn_optimize",
                    "🚀 Run Optimization",
                    class_="btn-primary w-100 mb-2",
                ),
                ui.output_ui(
                    "output_ID_tab_portfolios_subtab_optimalportfolios_status",
                ),
                ui.hr(),
                ui.input_select(
                    "input_ID_tab_portfolios_subtab_optimalportfolios_time_period",
                    "Returns Data Period",
                    {
                        "1y": "Last 1 Year",
                        "3y": "Last 3 Years",
                        "5y": "Last 5 Years",
                        "10y": "Last 10 Years",
                        "all": "All Available Data",
                    },
                    selected="3y",
                ),
                ui.input_select(
                    "input_ID_tab_portfolios_subtab_optimalportfolios_benchmark",
                    "Benchmark (for Tracking Error method)",
                    benchmark_choices,
                    selected="Benchmark_Portfolio",
                ),
                ui.hr(),
                ui.h5("📊 Portfolio 1", class_="mb-3 text-primary"),
                ui.input_select(
                    "input_ID_tab_portfolios_subtab_optimalportfolios_method1_type",
                    "Optimization Method",
                    OPTIMALPORTFOLIOS_METHODS,
                    selected=DEFAULT_METHOD1,
                ),
                ui.output_ui(
                    "output_ID_tab_portfolios_subtab_optimalportfolios_method1_params",
                ),
                ui.hr(),
                ui.h5("📊 Portfolio 2", class_="mb-3 text-success"),
                ui.input_select(
                    "input_ID_tab_portfolios_subtab_optimalportfolios_method2_type",
                    "Optimization Method",
                    OPTIMALPORTFOLIOS_METHODS,
                    selected=DEFAULT_METHOD2,
                ),
                ui.output_ui(
                    "output_ID_tab_portfolios_subtab_optimalportfolios_method2_params",
                ),
                ui.hr(),
                width=370,
                position="left",
            ),
            ui.div(
                ui.card(
                    ui.card_header("Portfolio Weights Comparison"),
                    output_widget(
                        "output_ID_tab_portfolios_subtab_optimalportfolios_plot_weights",
                        height="500px",
                        width="100%",
                    ),
                    full_screen=True,
                    class_="mb-4",
                ),
                ui.card(
                    ui.card_header("Optimization Results"),
                    ui.output_ui(
                        "output_ID_tab_portfolios_subtab_optimalportfolios_results_table",
                    ),
                    class_="mb-4",
                ),
                ui.card(
                    ui.card_header("Portfolio Statistics Comparison"),
                    ui.output_ui(
                        "output_ID_tab_portfolios_subtab_optimalportfolios_statistics_table",
                    ),
                    class_="mb-4",
                ),
                ui.card(
                    ui.card_header("Comparison of Portfolio Performance"),
                    ui.p(
                        "Simulated portfolio value over the selected time period "
                        "using optimized weights applied to historical ETF prices "
                        "(normalized to base = 100).",
                        class_="text-muted small px-3 pt-2",
                    ),
                    output_widget(
                        "output_ID_tab_portfolios_subtab_optimalportfolios_plot_performance",
                        height="500px",
                        width="100%",
                    ),
                    full_screen=True,
                    class_="mb-4",
                ),
                class_="flex-fill",
            ),
        ),
    )


# =============================================================================
# Module Server
# =============================================================================


@module.server
def subtab_portfolios_optimalportfolios_server(  # pragma: no cover
    input: Any,
    output: Any,
    session: Any,
    data_utils: dict,
    data_inputs: dict,
    reactives_shiny: dict,
) -> None:
    """Server logic for OptimalPortfolios portfolio optimization comparison."""
    portfolio1_result: reactive.Value[Any] = reactive.Value(None)
    portfolio2_result: reactive.Value[Any] = reactive.Value(None)
    optimization_error: reactive.Value[str | None] = reactive.Value(None)

    # ------------------------------------------------------------------
    # Helpers for reading possibly-absent dynamic inputs
    # ------------------------------------------------------------------

    def _safe_input(*, input_id: str, default: Any = None) -> Any:
        """Read a dynamic input attribute, returning *default* if absent."""
        try:
            return getattr(input, input_id)()
        except Exception:
            return default

    def _get_method_params(*, method_key: str, slot: str) -> dict[str, Any]:
        """Read dynamic param inputs for a given method and slot (method1|method2)."""
        pfx = f"input_ID_tab_portfolios_subtab_optimalportfolios_{slot}"
        if method_key == "MAX_QUADRATIC_UTILITY":
            return {
                "risk_aversion": resolve_optimalportfolios_risk_aversion(
                    value = _safe_input(input_id = f"{pfx}_risk_aversion", default = 1.0),
                ),
                "is_long_only": bool(_safe_input(input_id = f"{pfx}_long_only", default = True)),
            }
        if method_key == "MAX_SHARPE":
            return {
                "risk_free_rate": resolve_optimalportfolios_risk_free_rate(
                    value = _safe_input(input_id = f"{pfx}_risk_free_rate", default = 0.0),
                ),
                "is_long_only": bool(_safe_input(input_id = f"{pfx}_long_only", default = True)),
            }
        if method_key == "MAX_CARA_GMM":
            return {
                "risk_aversion": resolve_optimalportfolios_risk_aversion(
                    value = _safe_input(input_id = f"{pfx}_risk_aversion", default = 1.0),
                ),
                "n_components": resolve_optimalportfolios_n_components(
                    value = _safe_input(input_id = f"{pfx}_n_components", default = 2),
                ),
                "is_long_only": bool(_safe_input(input_id = f"{pfx}_long_only", default = True)),
            }
        if method_key in ("MIN_VARIANCE", "MAX_DIVERSIFICATION", "TRACKING_ERROR_MIN"):
            return {
                "is_long_only": bool(_safe_input(input_id = f"{pfx}_long_only", default = True)),
            }
        # RISK_PARITY: no extra params needed
        return {}

    def _build_input_snapshot() -> dict[str, Any]:
        """Snapshot current UI inputs into a dict for cache-key comparison."""
        m1 = resolve_optimalportfolios_method(
            method_value = _safe_input(
                input_id = "input_ID_tab_portfolios_subtab_optimalportfolios_method1_type",
                default = DEFAULT_METHOD1,
            ),
            default_value = DEFAULT_METHOD1,
        )
        m2 = resolve_optimalportfolios_method(
            method_value = _safe_input(
                input_id = "input_ID_tab_portfolios_subtab_optimalportfolios_method2_type",
                default = DEFAULT_METHOD2,
            ),
            default_value = DEFAULT_METHOD2,
        )
        return build_optimalportfolios_input_snapshot(
            time_period=_safe_input(
                input_id = "input_ID_tab_portfolios_subtab_optimalportfolios_time_period",
                default = DEFAULT_TIME_PERIOD,
            ),
            benchmark_key=_safe_input(
                input_id = "input_ID_tab_portfolios_subtab_optimalportfolios_benchmark",
                default = "Benchmark_Portfolio",
            ),
            method1_type=m1,
            method1_params=_get_method_params(method_key = m1, slot = "method1"),
            method2_type=m2,
            method2_params=_get_method_params(method_key = m2, slot = "method2"),
        )

    # ------------------------------------------------------------------
    # Dynamic UI: method parameters for Portfolio 1
    # ------------------------------------------------------------------

    @output
    @render.ui
    def output_ID_tab_portfolios_subtab_optimalportfolios_method1_params():
        """Render parameter input widgets for Portfolio 1's optimization method."""
        method = _safe_input(
            input_id = "input_ID_tab_portfolios_subtab_optimalportfolios_method1_type",
            default = DEFAULT_METHOD1,
        )
        return _render_method_params(method_key = method, slot = "method1")

    @output
    @render.ui
    def output_ID_tab_portfolios_subtab_optimalportfolios_method2_params():
        """Render parameter input widgets for Portfolio 2's optimization method."""
        method = _safe_input(
            input_id = "input_ID_tab_portfolios_subtab_optimalportfolios_method2_type",
            default = DEFAULT_METHOD2,
        )
        return _render_method_params(method_key = method, slot = "method2")

    def _render_method_params(*, method_key: str, slot: str) -> Any:
        """Build parameter UI widgets for *method_key* bound to *slot* (method1 or method2)."""
        pfx = f"input_ID_tab_portfolios_subtab_optimalportfolios_{slot}"
        if method_key == "MAX_QUADRATIC_UTILITY":
            return ui.div(
                ui.input_numeric(
                    f"{pfx}_risk_aversion",
                    "Risk Aversion (λ)",
                    value=1.0,
                    min=0.1,
                    max=20.0,
                    step=0.1,
                ),
                ui.input_checkbox(f"{pfx}_long_only", "Long-Only", value=True),
                class_="mt-2",
            )
        if method_key == "MAX_SHARPE":
            return ui.div(
                ui.input_numeric(
                    f"{pfx}_risk_free_rate",
                    "Daily Risk-Free Rate",
                    value=0.0,
                    min=0.0,
                    max=0.01,
                    step=0.0001,
                ),
                ui.input_checkbox(f"{pfx}_long_only", "Long-Only", value=True),
                class_="mt-2",
            )
        if method_key == "MAX_CARA_GMM":
            return ui.div(
                ui.input_numeric(
                    f"{pfx}_risk_aversion",
                    "Risk Aversion (λ)",
                    value=1.0,
                    min=0.1,
                    max=20.0,
                    step=0.1,
                ),
                ui.input_numeric(
                    f"{pfx}_n_components",
                    "GMM Components",
                    value=2,
                    min=1,
                    max=5,
                    step=1,
                ),
                ui.input_checkbox(f"{pfx}_long_only", "Long-Only", value=True),
                class_="mt-2",
            )
        if method_key in ("MIN_VARIANCE", "MAX_DIVERSIFICATION", "TRACKING_ERROR_MIN"):
            return ui.div(
                ui.input_checkbox(f"{pfx}_long_only", "Long-Only", value=True),
                class_="mt-2",
            )
        # RISK_PARITY: no extra params
        return ui.div()

    # ------------------------------------------------------------------
    # Returns data (shared between both portfolios)
    # ------------------------------------------------------------------

    @reactive.Calc
    def get_returns_data():
        """Compute percent-change returns from ETF prices for the selected period."""
        time_period = _safe_input(
            input_id = "input_ID_tab_portfolios_subtab_optimalportfolios_time_period",
            default = DEFAULT_TIME_PERIOD,
        )
        etf_data = data_inputs.get("Time_Series_ETFs")
        if etf_data is None or etf_data.is_empty():
            _logger.warning("ETF time series data not available")
            return None

        data_max_date_raw = etf_data["Date"].max()
        try:
            _ts = pd.Timestamp(data_max_date_raw)
            data_max_anchor = _ts.tz_convert(None) if _ts.tzinfo is not None else _ts
        except Exception:
            data_max_anchor = pd.Timestamp(datetime.now(UTC)).tz_convert(None)

        end_date = data_max_anchor.strftime("%Y-%m-%d")
        if time_period == "1y":
            start_date = (data_max_anchor - timedelta(days=365)).strftime("%Y-%m-%d")
        elif time_period == "3y":
            start_date = (data_max_anchor - timedelta(days=3 * 365)).strftime("%Y-%m-%d")
        elif time_period == "5y":
            start_date = (data_max_anchor - timedelta(days=5 * 365)).strftime("%Y-%m-%d")
        elif time_period == "10y":
            start_date = (data_max_anchor - timedelta(days=10 * 365)).strftime("%Y-%m-%d")
        else:
            start_date = str(etf_data["Date"].min())

        filtered = etf_data.filter(
            (pl.col("Date") >= start_date) & (pl.col("Date") <= end_date),
        )
        if filtered.is_empty():
            return None

        returns_data = filtered.clone()
        for col in returns_data.columns:
            if col != "Date":
                returns_data = returns_data.with_columns(pl.col(col).pct_change().alias(col))
        return returns_data.slice(1, returns_data.height - 1)

    def _get_benchmark_returns(
        *, benchmark_key: str, time_period: str) -> pl.DataFrame | None:
        """Derive benchmark return series for the Tracking Error method."""
        etf_data = data_inputs.get("Time_Series_ETFs")

        # ETF column used directly
        if etf_data is not None and benchmark_key in etf_data.columns:
            returns_df = get_returns_data()
            if returns_df is not None and benchmark_key in returns_df.columns:
                return returns_df.select(["Date", benchmark_key])
            return None

        # Fallback: use Benchmark_Portfolio value series
        bench_df = data_inputs.get("Benchmark_Portfolio")
        if bench_df is None or bench_df.is_empty():
            return None

        data_max_raw = bench_df["Date"].max()
        try:
            _ts = pd.Timestamp(data_max_raw)
            anchor = _ts.tz_convert(None) if _ts.tzinfo is not None else _ts
        except Exception:
            anchor = pd.Timestamp(datetime.now(UTC)).tz_convert(None)

        end_date = anchor.strftime("%Y-%m-%d")
        if time_period == "1y":
            start_date = (anchor - timedelta(days=365)).strftime("%Y-%m-%d")
        elif time_period == "3y":
            start_date = (anchor - timedelta(days=3 * 365)).strftime("%Y-%m-%d")
        elif time_period == "5y":
            start_date = (anchor - timedelta(days=5 * 365)).strftime("%Y-%m-%d")
        elif time_period == "10y":
            start_date = (anchor - timedelta(days=10 * 365)).strftime("%Y-%m-%d")
        else:
            start_date = str(bench_df["Date"].min())

        # Determine value column (may be "Value" or "portfolio_value")
        val_col = next(
            (c for c in bench_df.columns if c.lower() in ("value", "portfolio_value")),
            None,
        )
        if val_col is None:
            return None

        filtered = bench_df.filter(
            (pl.col("Date") >= start_date) & (pl.col("Date") <= end_date),
        ).sort("Date")
        if filtered.height < 2:
            return None

        bench_returns = filtered.select(
            ["Date", pl.col(val_col).pct_change().alias("Benchmark")],
        ).slice(1, filtered.height - 1)
        return bench_returns

    # ------------------------------------------------------------------
    # Core optimization
    # ------------------------------------------------------------------

    def _run_single_optimization(
        *, method_key: str, params: dict[str, Any], returns_data: pl.DataFrame, portfolio_name: str, benchmark_key: str, time_period: str) -> Any:
        """Dispatch to the correct calc_optimalportfolios_* function."""
        is_long_only = bool(params.get("is_long_only", True))

        if method_key == "MIN_VARIANCE":
            return calc_optimalportfolios_minimum_variance(
                returns_data=returns_data,
                portfolio_name=portfolio_name,
                is_long_only=is_long_only,
            )
        if method_key == "MAX_QUADRATIC_UTILITY":
            return calc_optimalportfolios_maximum_quadratic_utility(
                returns_data=returns_data,
                portfolio_name=portfolio_name,
                risk_aversion=float(params.get("risk_aversion", 1.0)),
                is_long_only=is_long_only,
            )
        if method_key == "RISK_PARITY":
            return calc_optimalportfolios_budgeted_risk_contribution(
                returns_data=returns_data,
                portfolio_name=portfolio_name,
            )
        if method_key == "MAX_DIVERSIFICATION":
            return calc_optimalportfolios_maximum_diversification(
                returns_data=returns_data,
                portfolio_name=portfolio_name,
                is_long_only=is_long_only,
            )
        if method_key == "MAX_SHARPE":
            return calc_optimalportfolios_maximum_sharpe_ratio(
                returns_data=returns_data,
                portfolio_name=portfolio_name,
                risk_free_rate=float(params.get("risk_free_rate", 0.0)),
                is_long_only=is_long_only,
            )
        if method_key == "MAX_CARA_GMM":
            return calc_optimalportfolios_maximum_cara_gaussian_mixture(
                returns_data=returns_data,
                portfolio_name=portfolio_name,
                risk_aversion=float(params.get("risk_aversion", 1.0)),
                n_components=int(params.get("n_components", 2)),
                is_long_only=is_long_only,
            )
        if method_key == "TRACKING_ERROR_MIN":
            bench_rets = _get_benchmark_returns(benchmark_key = benchmark_key, time_period = time_period)
            if bench_rets is None:
                raise Exception_Validation_Input(
                    "Benchmark returns unavailable for Tracking Error Minimization. "
                    "Check that the benchmark data source is loaded.",
                )
            # Align lengths
            min_len = min(len(returns_data), len(bench_rets))
            return calc_optimalportfolios_tracking_error_minimization(
                returns_data=returns_data.slice(0, min_len),
                benchmark_returns=bench_rets.slice(0, min_len),
                portfolio_name=portfolio_name,
                is_long_only=is_long_only,
            )
        raise Exception_Validation_Input(f"Unknown OptimalPortfolios method key: {method_key!r}")

    def _execute_optimization() -> bool:  # pragma: no cover
        """Run portfolio optimization for both methods and store results."""
        optimization_error.set(None)
        portfolio1_result.set(None)
        portfolio2_result.set(None)

        snapshot = _build_input_snapshot()
        save_portfolio_optimization_optimalportfolios_inputs_to_reactives(
            reactives_shiny = reactives_shiny,
            data_value = snapshot,
        )

        returns_data = get_returns_data()
        if returns_data is None:
            optimization_error.set("No returns data available for selected period")
            return False

        benchmark_key = snapshot["benchmark_key"]
        time_period = snapshot["time_period"]

        try:
            _logger.info("Optimizing Portfolio 1 (%s)", snapshot["method1"]["type"])
            p1 = _run_single_optimization(
                method_key=snapshot["method1"]["type"],
                params=snapshot["method1"],
                returns_data=returns_data,
                portfolio_name=OPTIMALPORTFOLIOS_METHODS.get(
                    snapshot["method1"]["type"],
                    snapshot["method1"]["type"],
                ),
                benchmark_key=benchmark_key,
                time_period=time_period,
            )
            portfolio1_result.set(p1)
            _logger.info("Portfolio 1 optimization complete")

            _logger.info("Optimizing Portfolio 2 (%s)", snapshot["method2"]["type"])
            p2 = _run_single_optimization(
                method_key=snapshot["method2"]["type"],
                params=snapshot["method2"],
                returns_data=returns_data,
                portfolio_name=OPTIMALPORTFOLIOS_METHODS.get(
                    snapshot["method2"]["type"],
                    snapshot["method2"]["type"],
                ),
                benchmark_key=benchmark_key,
                time_period=time_period,
            )
            portfolio2_result.set(p2)
            _logger.info("Portfolio 2 optimization complete")

            perf1, perf2 = compute_optimalportfolios_performance_series_impl_QWIM(
                portfolio_1 = p1,
                portfolio_2 = p2,
                etf_data = data_inputs.get("Time_Series_ETFs"),
                time_period=_safe_input(
                    input_id = "input_ID_tab_portfolios_subtab_optimalportfolios_time_period",
                    default = DEFAULT_TIME_PERIOD,
                ),
                default_time_period=DEFAULT_TIME_PERIOD,
            )
            _save_output_snapshot(
                data_partial = {
                    "weights_comparison": build_optimalportfolios_weights_rows(portfolio_1 = p1, portfolio_2 = p2),
                    "statistics_comparison": build_optimalportfolios_statistics_rows_impl_QWIM(
                        series_1 = perf1,
                        series_2 = perf2,
                        has_quantstats=HAS_QUANTSTATS,
                        qs_module=qs,
                    ),
                    "performance_summary": build_optimalportfolios_performance_summary(
                        portfolio_1 = p1,
                        portfolio_2 = p2,
                        perf_1 = perf1,
                        perf_2 = perf2,
                    ),
                },
            )
            return True

        except Exception as e:
            error_msg = f"Optimization failed: {e!s}"
            _logger.exception(error_msg)
            optimization_error.set(error_msg)
            return False

    def _save_output_snapshot(*, data_partial: dict[str, Any]) -> None:
        """Merge *data_partial* into the existing output snapshot and persist to reactives."""
        existing: dict[str, Any] = {}
        data_results = reactives_shiny.get("Data_Results", {})
        rv = data_results.get("Portfolio_Optimization_OptimalPortfolios_Outputs")
        if rv is not None and hasattr(rv, "get"):
            try:
                cur = rv.get()
                if isinstance(cur, dict):
                    existing = cur
            except Exception:
                existing = {}
        save_portfolio_optimization_optimalportfolios_outputs_to_reactives(
            reactives_shiny = reactives_shiny,
            data_value = merge_optimalportfolios_output_snapshot(existing_data = existing, data_partial = data_partial),
        )

    # ------------------------------------------------------------------
    # Reactive: trigger optimization
    # ------------------------------------------------------------------

    @reactive.Effect
    @reactive.event(input.input_ID_tab_portfolios_subtab_optimalportfolios_btn_optimize)
    def run_optimization():
        """Execute portfolio optimization for both methods."""  # pragma: no cover
        _execute_optimization()

    # ------------------------------------------------------------------
    # Outputs
    # ------------------------------------------------------------------

    @output
    @render.ui
    def output_ID_tab_portfolios_subtab_optimalportfolios_status():
        """Render the optimization status (success or error message)."""
        error = optimization_error.get()
        if error:
            return ui.div(ui.p(f"❌ {error}", class_="text-danger mt-3 small"))
        p1 = portfolio1_result.get()
        p2 = portfolio2_result.get()
        if p1 is not None and p2 is not None:
            return ui.div(ui.p("✅ Optimization complete!", class_="text-success mt-3 small"))
        return ui.div()

    @output
    @render_widget  # pyright: ignore[reportArgumentType]  # pyrefly: ignore[bad-specialization]
    def output_ID_tab_portfolios_subtab_optimalportfolios_plot_weights():
        """Render bar-chart comparing portfolio weights for both methods."""
        return render_optimalportfolios_weights_plot_impl_QWIM(
            portfolio_1 = portfolio1_result.get(),
            portfolio_2 = portfolio2_result.get(),
            reactives_shiny = reactives_shiny,
        )

    @output
    @render.ui
    def output_ID_tab_portfolios_subtab_optimalportfolios_results_table():
        """Render a side-by-side weight comparison table for both portfolios."""
        return render_optimalportfolios_results_table_impl_QWIM(
            portfolio_1 = portfolio1_result.get(),
            portfolio_2 = portfolio2_result.get(),
        )

    @output
    @render.ui
    def output_ID_tab_portfolios_subtab_optimalportfolios_statistics_table():
        """Render a statistics comparison table for both portfolios."""
        perf1, perf2 = compute_optimalportfolios_performance_series_impl_QWIM(
            portfolio_1 = portfolio1_result.get(),
            portfolio_2 = portfolio2_result.get(),
            etf_data = data_inputs.get("Time_Series_ETFs"),
            time_period=_safe_input(
                input_id = "input_ID_tab_portfolios_subtab_optimalportfolios_time_period",
                default = DEFAULT_TIME_PERIOD,
            ),
            default_time_period=DEFAULT_TIME_PERIOD,
        )
        stats_rows = build_optimalportfolios_statistics_rows_impl_QWIM(
            series_1 = perf1,
            series_2 = perf2,
            has_quantstats=HAS_QUANTSTATS,
            qs_module=qs,
        )
        return render_optimalportfolios_statistics_table_impl_QWIM(
            portfolio_1 = portfolio1_result.get(),
            portfolio_2 = portfolio2_result.get(),
            stats_rows = stats_rows,
        )

    @output
    @render_widget  # pyright: ignore[reportArgumentType]  # pyrefly: ignore[bad-specialization]
    def output_ID_tab_portfolios_subtab_optimalportfolios_plot_performance():
        """Render a line chart comparing the historical performance of both portfolios."""
        perf1, perf2 = compute_optimalportfolios_performance_series_impl_QWIM(
            portfolio_1 = portfolio1_result.get(),
            portfolio_2 = portfolio2_result.get(),
            etf_data = data_inputs.get("Time_Series_ETFs"),
            time_period=_safe_input(
                input_id = "input_ID_tab_portfolios_subtab_optimalportfolios_time_period",
                default = DEFAULT_TIME_PERIOD,
            ),
            default_time_period=DEFAULT_TIME_PERIOD,
        )
        return render_optimalportfolios_performance_plot_impl_QWIM(
            portfolio_1 = portfolio1_result.get(),
            portfolio_2 = portfolio2_result.get(),
            perf_1 = perf1,
            perf_2 = perf2,
            reactives_shiny = reactives_shiny,
        )

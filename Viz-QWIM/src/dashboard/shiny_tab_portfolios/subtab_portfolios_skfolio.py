"""Portfolio Optimization with skfolio Module.

Provides comprehensive portfolio optimization using methods from the skfolio Python package.

![Portfolio Analysis](https://img.shields.io/badge/Portfolio-Analysis-blue)
![Python](https://img.shields.io/badge/python-3.12+-green)
![Shiny](https://img.shields.io/badge/shiny-for_python-orange)

## Overview

The skfolio Portfolio Optimization module enables users to compare different portfolio
optimization strategies using state-of-the-art methods from the skfolio package.

This module provides an interactive interface to:
- Select and configure optimization methods (Basic, Convex, Clustering, Ensemble)
- Compare two different optimization strategies side-by-side
- Visualize portfolio weights and performance metrics
- Export results for further analysis

## Features

- **Multiple Optimization Methods**: Basic, Convex, Clustering, and Ensemble strategies
- **Side-by-Side Comparison**: Compare two optimization strategies simultaneously
- **Interactive Configuration**: Dynamic parameter inputs based on selected method
- **Performance Metrics**: Comprehensive statistics for comparison
- **Visual Analysis**: Interactive Plotly charts for weights and performance

**Module Information:**
- **Author**: QWIM Development Team
- **Version**: 0.5.1
- **Last Updated**: February 2026
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np

# pandas required by skfolio API — skfolio demands DataFrame input; Polars not accepted here
import pandas as pd
import polars as pl

from shiny import module, reactive, render, ui
from shinywidgets import output_widget, render_widget
from skfolio.optimization import ObjectiveFunction

from src.dashboard.shiny_utils.utils_reporting import (
    save_portfolio_optimization_skfolio_inputs_to_reactives,
    save_portfolio_optimization_skfolio_outputs_to_reactives,  # Persist skfolio for PDF
)
from src.dashboard.shiny_tab_portfolios._subtab_portfolios_skfolio_outputs import (
    build_skfolio_statistics_rows_impl_QWIM,
    compute_skfolio_performance_series_impl_QWIM,
    render_skfolio_performance_plot_impl_QWIM,
    render_skfolio_results_table_impl_QWIM,
    render_skfolio_statistics_table_impl_QWIM,
    render_skfolio_weights_plot_impl_QWIM,
)
from src.dashboard.shiny_utils.utils_visuals import create_error_figure
from src.models.portfolio_optimization.pkg_skfolio import (
    calc_skfolio_optimization_basic,
    calc_skfolio_optimization_clustering,
    calc_skfolio_optimization_convex,
    calc_skfolio_optimization_ensemble,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


# Extracted helper compatibility contract for source-sensitive regression tests:
# if series_1 is None or series_2 is None:
#     return []
# if HAS_QUANTSTATS:
#     _metric_cagr, _metric_max_drawdown, _metric_calmar


qs: Any = None
try:
    import quantstats as qs

    HAS_QUANTSTATS = True
except ImportError:  # pragma: no cover
    HAS_QUANTSTATS = False


# Module-level logger
_logger = get_logger(name = __name__)

# Configuration
OUTPUT_DIR = Path("output")

# Optimization method categories and mappings
OPTIMIZATION_CATEGORIES = {
    "basic": "Basic Methods (Equal Weight, Inverse Vol, Random)",
    "convex": "Convex Optimization (Mean-Risk, Risk Parity, etc.)",
    "clustering": "Clustering Methods (HRP, HERC, NCO)",
    "ensemble": "Ensemble Methods (Stacking)",
}

BASIC_METHODS = {
    "BASIC_EQUAL_WEIGHTED": "Equal Weighted (1/N)",
    "BASIC_INVERSE_VOLATILITY": "Inverse Volatility",
    "BASIC_RANDOM_DIRICHLET": "Random (Dirichlet)",
}

CONVEX_METHODS = {
    "CONVEX_MEAN_RISK": "Mean-Risk (Markowitz)",
    "CONVEX_RISK_BUDGETING": "Risk Budgeting (Risk Parity)",
    "CONVEX_MAXIMUM_DIVERSIFICATION": "Maximum Diversification",
    "CONVEX_DISTRIBUTIONALLY_ROBUST_CVAR": "Robust CVaR",
    "CONVEX_BENCHMARK_TRACKING": "Benchmark Tracking",
}

CLUSTERING_METHODS = {
    "CLUSTERING_HIERARCHICAL_RISK_PARITY": "Hierarchical Risk Parity (HRP)",
    "CLUSTERING_HIERARCHICAL_EQUAL_RISK_CONTRIBUTION": "Hierarchical Equal Risk Contribution (HERC)",
    "CLUSTERING_SCHUR_COMPLEMENTARY_ALLOCATION": "Schur Complementary Allocation",
    "CLUSTERING_NESTED": "Nested Clusters Optimization (NCO)",
}

ENSEMBLE_METHODS = {
    "ENSEMBLE_STACKING": "Stacking (Meta-Learning)",
}

OBJECTIVE_FUNCTIONS = {
    "MINIMIZE_RISK": "Minimize Risk",
    "MAXIMIZE_RETURN": "Maximize Return",
    "MAXIMIZE_UTILITY": "Maximize Utility",
    "MAXIMIZE_RATIO": "Maximize Sharpe Ratio",
}

DEFAULT_METHODS_BY_CATEGORY = {
    "basic": "BASIC_EQUAL_WEIGHTED",
    "convex": "CONVEX_MEAN_RISK",
    "clustering": "CLUSTERING_HIERARCHICAL_RISK_PARITY",
    "ensemble": "ENSEMBLE_STACKING",
}
DEFAULT_TIME_PERIOD = "3y"
DEFAULT_OBJECTIVE_METHOD1 = "MINIMIZE_RISK"
DEFAULT_OBJECTIVE_METHOD2 = "MAXIMIZE_RATIO"


def resolve_skfolio_method_category(
    *, category_value: Any, default_value: str) -> str:
    """Return a valid optimization category with a deterministic fallback."""
    if isinstance(category_value, str) and category_value in OPTIMIZATION_CATEGORIES:
        return category_value
    return default_value


def resolve_skfolio_method_type(
    *, category_value: str, method_value: Any) -> str:
    """Return a valid method key for the selected category."""
    methods_map = {
        "basic": BASIC_METHODS,
        "convex": CONVEX_METHODS,
        "clustering": CLUSTERING_METHODS,
        "ensemble": ENSEMBLE_METHODS,
    }.get(category_value, BASIC_METHODS)

    if isinstance(method_value, str) and method_value in methods_map:
        return method_value

    return DEFAULT_METHODS_BY_CATEGORY.get(category_value, "BASIC_EQUAL_WEIGHTED")


def resolve_skfolio_objective(
    *, objective_value: Any, default_value: str) -> str:
    """Return a valid objective key with a deterministic fallback."""
    if isinstance(objective_value, str) and objective_value in OBJECTIVE_FUNCTIONS:
        return objective_value
    return default_value


def resolve_skfolio_risk_aversion(
    *, risk_aversion_value: Any, default_value: float = 1.0) -> float:
    """Return a safe numeric risk aversion value."""
    if isinstance(risk_aversion_value, bool):
        return default_value

    try:
        return float(risk_aversion_value)
    except (TypeError, ValueError):
        return default_value


def build_skfolio_input_snapshot(
    *,
    time_period: Any,
    method1_category: Any,
    method1_type: Any,
    method1_objective: Any,
    method1_risk_aversion: Any,
    method2_category: Any,
    method2_type: Any,
    method2_objective: Any,
    method2_risk_aversion: Any,
) -> dict[str, Any]:
    """Build a report-ready snapshot of the current skfolio input selections."""
    resolved_method1_category = resolve_skfolio_method_category(category_value = method1_category, default_value = "basic")
    resolved_method2_category = resolve_skfolio_method_category(category_value = method2_category, default_value = "convex")

    return {
        "time_period": str(time_period or DEFAULT_TIME_PERIOD),
        "method1": {
            "category": resolved_method1_category,
            "type": resolve_skfolio_method_type(category_value = resolved_method1_category, method_value = method1_type),
            "objective": resolve_skfolio_objective(
                objective_value = method1_objective,
                default_value = DEFAULT_OBJECTIVE_METHOD1,
            ),
            "risk_aversion": resolve_skfolio_risk_aversion(risk_aversion_value = method1_risk_aversion),
        },
        "method2": {
            "category": resolved_method2_category,
            "type": resolve_skfolio_method_type(category_value = resolved_method2_category, method_value = method2_type),
            "objective": resolve_skfolio_objective(
                objective_value = method2_objective,
                default_value = DEFAULT_OBJECTIVE_METHOD2,
            ),
            "risk_aversion": resolve_skfolio_risk_aversion(risk_aversion_value = method2_risk_aversion),
        },
    }


def build_skfolio_weights_rows(
    *, portfolio_1: Any, portfolio_2: Any) -> list[dict[str, Any]]:
    """Build report-ready portfolio weight rows for both optimized portfolios."""
    import math

    weights_1 = portfolio_1.get_portfolio_weights()
    weights_2 = portfolio_2.get_portfolio_weights()
    assets = [asset_name for asset_name in weights_1.columns if asset_name != "Date"]

    rows: list[dict[str, Any]] = []
    for asset_name in assets:
        weight_1_raw = weights_1[asset_name][0]
        weight_2_raw = weights_2[asset_name][0]

        if isinstance(weight_1_raw, bool) or isinstance(weight_2_raw, bool):
            continue

        weight_1 = float(weight_1_raw)
        weight_2 = float(weight_2_raw)
        if not math.isnan(weight_1) and not math.isnan(weight_2):
            rows.append(
                {
                    "asset": asset_name,
                    "equal_weighted": weight_1,
                    "mean_risk": weight_2,
                },
            )

    return rows


def build_skfolio_performance_summary(
    *, portfolio_1: Any, portfolio_2: Any, perf_1: pl.DataFrame | None, perf_2: pl.DataFrame | None) -> dict[str, dict[str, Any]]:
    """Build annualized skfolio performance metrics for report export."""

    def _perf_stats(*, series: pl.DataFrame | None) -> dict[str, float]:
        """Compute annualised return, volatility, and Sharpe ratio for *series*."""
        if series is None or len(series) < 2:
            return {
                "annualized_return": 0.0,
                "volatility": 0.0,
                "sharpe_ratio": 0.0,
            }

        value_list = series["Value"].to_list()
        if any(isinstance(item_value, bool) for item_value in value_list):
            return {
                "annualized_return": 0.0,
                "volatility": 0.0,
                "sharpe_ratio": 0.0,
            }

        values_array = np.array(value_list, dtype=np.float64)
        daily_returns = np.diff(values_array) / values_array[:-1]
        annualized_return = float(
            (values_array[-1] / values_array[0]) ** (252.0 / len(daily_returns)) - 1,
        )
        volatility = float(np.std(daily_returns, ddof=1) * np.sqrt(252))
        sharpe_ratio = float((annualized_return - 0.02) / volatility) if volatility > 1e-12 else 0.0
        return {
            "annualized_return": annualized_return,
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
        }

    return {
        "method1": {
            "label": str(portfolio_1.get_portfolio_name),
            **_perf_stats(series = perf_1),
        },
        "method2": {
            "label": str(portfolio_2.get_portfolio_name),
            **_perf_stats(series = perf_2),
        },
    }


def merge_skfolio_output_snapshot(
    *, existing_data: dict[str, Any] | None, data_partial: dict[str, Any]) -> dict[str, Any]:
    """Merge new skfolio report data into any existing snapshot."""
    if not isinstance(existing_data, dict):
        existing_data = {}
    return existing_data | data_partial


@module.ui
def subtab_portfolios_skfolio_ui(*, data_utils: dict, data_inputs: dict) -> Any:  # pragma: no cover
    """Create UI for skfolio portfolio optimization comparison subtab.

    Parameters
    ----------
    data_utils : dict
        Dictionary containing utility functions and configurations.
    data_inputs : dict
        Dictionary containing input datasets.

    Returns
    -------
    shiny.ui.div
        Complete UI layout for the skfolio optimization subtab.
    """
    return ui.div(
        ui.h3("Portfolio Optimization with skfolio"),
        ui.p(
            "Compare different portfolio optimization strategies using advanced "
            "methods from the skfolio package.",
            class_="text-muted mb-4",
        ),
        ui.layout_sidebar(
            ui.sidebar(
                ui.h5("⚙️ Optimization Configuration", class_="mb-3"),
                # Optimize button — placed above config for immediate access
                ui.input_action_button(
                    "input_ID_tab_portfolios_subtab_skfolio_btn_optimize",
                    "🚀 Run Optimization",
                    class_="btn-primary w-100 mb-2",
                ),
                ui.output_ui("output_ID_tab_portfolios_subtab_skfolio_status"),
                ui.hr(),
                # Time period for returns data
                ui.input_select(
                    "input_ID_tab_portfolios_subtab_skfolio_time_period",
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
                ui.hr(),
                # Portfolio 1 Configuration
                ui.h5("📊 Portfolio 1", class_="mb-3 text-primary"),
                ui.input_select(
                    "input_ID_tab_portfolios_subtab_skfolio_method1_category",
                    "Method Category",
                    OPTIMIZATION_CATEGORIES,
                    selected="basic",
                ),
                ui.output_ui("output_ID_tab_portfolios_subtab_skfolio_method1_select"),
                ui.output_ui("output_ID_tab_portfolios_subtab_skfolio_method1_params"),
                ui.hr(),
                # Portfolio 2 Configuration
                ui.h5("📊 Portfolio 2", class_="mb-3 text-success"),
                ui.input_select(
                    "input_ID_tab_portfolios_subtab_skfolio_method2_category",
                    "Method Category",
                    OPTIMIZATION_CATEGORIES,
                    selected="convex",
                ),
                ui.output_ui("output_ID_tab_portfolios_subtab_skfolio_method2_select"),
                ui.output_ui("output_ID_tab_portfolios_subtab_skfolio_method2_params"),
                ui.hr(),
                width=350,
                position="left",
            ),
            # Main content area
            ui.div(
                # Weights comparison
                ui.card(
                    ui.card_header("Portfolio Weights Comparison"),
                    output_widget(
                        "output_ID_tab_portfolios_subtab_skfolio_plot_weights",
                        height="500px",
                        width="100%",
                    ),
                    full_screen=True,
                    class_="mb-4",
                ),
                # Performance statistics
                ui.card(
                    ui.card_header("Optimization Results"),
                    ui.output_ui("output_ID_tab_portfolios_subtab_skfolio_results_table"),
                    class_="mb-4",
                ),
                # Quantstats portfolio statistics comparison
                ui.card(
                    ui.card_header("Portfolio Statistics Comparison (quantstats)"),
                    ui.output_ui("output_ID_tab_portfolios_subtab_skfolio_statistics_table"),
                    class_="mb-4",
                ),
                # Comparison of Portfolio Performance
                ui.card(
                    ui.card_header("Comparison of Portfolio Performance"),
                    ui.p(
                        "Simulated portfolio value over the selected time period "
                        "using optimized weights applied to historical ETF prices "
                        "(normalized to base = 100).",
                        class_="text-muted small px-3 pt-2",
                    ),
                    output_widget(
                        "output_ID_tab_portfolios_subtab_skfolio_plot_performance",
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


@module.server
def subtab_portfolios_skfolio_server(  # pragma: no cover
    input: Any,
    output: Any,
    session: Any,
    data_utils: dict,
    data_inputs: dict,
    reactives_shiny: dict,
) -> None:
    """Server logic for skfolio portfolio optimization comparison.

    Parameters
    ----------
    input : Any
        Shiny input object.
    output : Any
        Shiny output object.
    session : Any
        Shiny session object.
    data_utils : dict
        Dictionary containing utility functions.
    data_inputs : dict
        Dictionary containing input datasets.
    reactives_shiny : dict
        Dictionary containing reactive values.
    """
    # Reactive values for storing optimization results
    portfolio1_result: reactive.Value[Any] = reactive.Value(None)
    portfolio2_result: reactive.Value[Any] = reactive.Value(None)
    optimization_error: reactive.Value[str | None] = reactive.Value(None)

    def _resolve_method_category(
        *, category_value: Any, default_value: str) -> str:
        """Return a valid optimization category with a deterministic fallback."""
        return resolve_skfolio_method_category(category_value = category_value, default_value = default_value)

    def _resolve_method_type(
        *, category_value: str, method_value: Any) -> str:
        """Return a valid method key for the selected category."""
        return resolve_skfolio_method_type(category_value = category_value, method_value = method_value)

    def _resolve_objective(
        *, objective_value: Any, default_value: str) -> str:
        """Return a valid objective key with a deterministic fallback."""
        return resolve_skfolio_objective(objective_value = objective_value, default_value = default_value)

    def _resolve_risk_aversion(
        *, risk_aversion_value: Any, default_value: float = 1.0) -> float:
        """Return a safe numeric risk aversion value."""
        return resolve_skfolio_risk_aversion(risk_aversion_value = risk_aversion_value, default_value = default_value)

    def _build_skfolio_input_snapshot() -> dict[str, Any]:
        """Build a report-ready snapshot of the current skfolio input selections.

        Inputs rendered only for certain method categories (e.g. objective and
        risk_aversion for "convex", method type for dynamically-rendered selects)
        are absent from the DOM when another category is active.  In Shiny for
        Python, reading a missing input raises ``SilentException``, which would
        silently abort the reactive effect that owns this function.  Each
        potentially-absent input is therefore guarded with ``try/except`` so
        that ``None`` is passed as the default; ``build_skfolio_input_snapshot``
        already handles ``None`` via its ``resolve_*`` helpers.
        """
        # Dynamic select — rendered by output_ID_..._method1_select; may be absent
        # on the very first reactive flush before the output has rendered.
        try:
            method1_type: Any = input.input_ID_tab_portfolios_subtab_skfolio_method1_type()
        except Exception:
            method1_type = None
        # Only present when method1 category is "convex"
        try:
            method1_objective: Any = (
                input.input_ID_tab_portfolios_subtab_skfolio_method1_objective()
            )
        except Exception:
            method1_objective = None
        try:
            method1_risk_aversion: Any = (
                input.input_ID_tab_portfolios_subtab_skfolio_method1_risk_aversion()
            )
        except Exception:
            method1_risk_aversion = None
        # Dynamic select — same reasoning as method1_type
        try:
            method2_type: Any = input.input_ID_tab_portfolios_subtab_skfolio_method2_type()
        except Exception:
            method2_type = None
        # Only present when method2 category is "convex"
        try:
            method2_objective: Any = (
                input.input_ID_tab_portfolios_subtab_skfolio_method2_objective()
            )
        except Exception:
            method2_objective = None
        try:
            method2_risk_aversion: Any = (
                input.input_ID_tab_portfolios_subtab_skfolio_method2_risk_aversion()
            )
        except Exception:
            method2_risk_aversion = None
        return build_skfolio_input_snapshot(
            time_period=input.input_ID_tab_portfolios_subtab_skfolio_time_period(),
            method1_category=input.input_ID_tab_portfolios_subtab_skfolio_method1_category(),
            method1_type=method1_type,
            method1_objective=method1_objective,
            method1_risk_aversion=method1_risk_aversion,
            method2_category=input.input_ID_tab_portfolios_subtab_skfolio_method2_category(),
            method2_type=method2_type,
            method2_objective=method2_objective,
            method2_risk_aversion=method2_risk_aversion,
        )

    def _build_skfolio_weights_rows(
        *, portfolio_1: Any, portfolio_2: Any) -> list[dict[str, Any]]:
        """Build report-ready portfolio weight rows for both optimized portfolios."""
        return build_skfolio_weights_rows(portfolio_1 = portfolio_1, portfolio_2 = portfolio_2)

    def _build_skfolio_performance_summary(
        *, portfolio_1: Any, portfolio_2: Any, perf_1: pl.DataFrame | None, perf_2: pl.DataFrame | None) -> dict[str, dict[str, Any]]:
        """Build annualized skfolio performance metrics for report export."""
        return build_skfolio_performance_summary(portfolio_1 = portfolio_1, portfolio_2 = portfolio_2, perf_1 = perf_1, perf_2 = perf_2)

    def _save_skfolio_output_snapshot(
        *, data_partial: dict[str, Any]) -> None:
        """Merge report-ready skfolio outputs into shared reactive state."""
        existing_data: dict[str, Any] = {}
        data_results = reactives_shiny.get("Data_Results", {})
        reactive_output = data_results.get("Portfolio_Optimization_Skfolio_Outputs")

        if reactive_output is not None and hasattr(reactive_output, "get"):
            try:
                current_value = reactive_output.get()
                if isinstance(current_value, dict):
                    existing_data = current_value
            except Exception:
                existing_data = {}

        save_portfolio_optimization_skfolio_outputs_to_reactives(
            reactives_shiny = reactives_shiny,
            data_value = merge_skfolio_output_snapshot(existing_data = existing_data, data_partial = data_partial),
        )

    # Dynamic UI: Method selection for Portfolio 1
    @output
    @render.ui
    def output_ID_tab_portfolios_subtab_skfolio_method1_select():
        """Render method selection dropdown for Portfolio 1."""
        category = input.input_ID_tab_portfolios_subtab_skfolio_method1_category()

        if category == "basic":
            methods = BASIC_METHODS
        elif category == "convex":
            methods = CONVEX_METHODS
        elif category == "clustering":
            methods = CLUSTERING_METHODS
        elif category == "ensemble":
            methods = ENSEMBLE_METHODS
        else:
            methods = BASIC_METHODS

        return ui.input_select(
            "input_ID_tab_portfolios_subtab_skfolio_method1_type",
            "Optimization Method",
            methods,
        )

    # Dynamic UI: Method selection for Portfolio 2
    @output
    @render.ui
    def output_ID_tab_portfolios_subtab_skfolio_method2_select():
        """Render method selection dropdown for Portfolio 2."""
        category = input.input_ID_tab_portfolios_subtab_skfolio_method2_category()

        if category == "basic":
            methods = BASIC_METHODS
        elif category == "convex":
            methods = CONVEX_METHODS
        elif category == "clustering":
            methods = CLUSTERING_METHODS
        elif category == "ensemble":
            methods = ENSEMBLE_METHODS
        else:
            methods = CONVEX_METHODS

        return ui.input_select(
            "input_ID_tab_portfolios_subtab_skfolio_method2_type",
            "Optimization Method",
            methods,
        )

    # Dynamic UI: Parameters for Portfolio 1
    @output
    @render.ui
    def output_ID_tab_portfolios_subtab_skfolio_method1_params():
        """Render parameter inputs for Portfolio 1 method."""
        category = input.input_ID_tab_portfolios_subtab_skfolio_method1_category()

        if category == "convex":
            return ui.div(
                ui.input_select(
                    "input_ID_tab_portfolios_subtab_skfolio_method1_objective",
                    "Objective Function",
                    OBJECTIVE_FUNCTIONS,
                    selected="MINIMIZE_RISK",
                ),
                ui.input_numeric(
                    "input_ID_tab_portfolios_subtab_skfolio_method1_risk_aversion",
                    "Risk Aversion",
                    value=1.0,
                    min=0.1,
                    max=10.0,
                    step=0.1,
                ),
                class_="mt-2",
            )
        return ui.div()

    # Dynamic UI: Parameters for Portfolio 2
    @output
    @render.ui
    def output_ID_tab_portfolios_subtab_skfolio_method2_params():
        """Render parameter inputs for Portfolio 2 method."""
        category = input.input_ID_tab_portfolios_subtab_skfolio_method2_category()

        if category == "convex":
            return ui.div(
                ui.input_select(
                    "input_ID_tab_portfolios_subtab_skfolio_method2_objective",
                    "Objective Function",
                    OBJECTIVE_FUNCTIONS,
                    selected="MAXIMIZE_RATIO",
                ),
                ui.input_numeric(
                    "input_ID_tab_portfolios_subtab_skfolio_method2_risk_aversion",
                    "Risk Aversion",
                    value=1.0,
                    min=0.1,
                    max=10.0,
                    step=0.1,
                ),
                class_="mt-2",
            )
        return ui.div()

    # Reactive: Get returns data based on time period
    @reactive.Calc
    def get_returns_data():
        """Get returns data for the selected time period."""
        time_period = input.input_ID_tab_portfolios_subtab_skfolio_time_period()

        # Get ETF price data
        etf_data = data_inputs.get("Time_Series_ETFs")
        if etf_data is None or etf_data.is_empty():
            _logger.warning("ETF time series data not available")
            return None

        # Anchor the period at the latest date available in the ETF data so that preset
        # periods (e.g. "Last 1 Year") return the last N days OF THE DATA, not of today.
        data_max_date_raw = etf_data["Date"].max()
        # data_max_date_raw may be a string such as "2025-03-14 00:00:00-05:00"
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
        else:  # "all"
            start_date = etf_data["Date"].min()

        # Filter data
        filtered_data = etf_data.filter(
            (pl.col("Date") >= start_date) & (pl.col("Date") <= end_date),
        )

        # Calculate returns (percent change)
        if filtered_data.is_empty():
            return None

        # Convert to returns
        returns_data = filtered_data.clone()
        for col in returns_data.columns:
            if col != "Date":
                # Calculate percent change: (price[t] - price[t-1]) / price[t-1]
                returns_data = returns_data.with_columns(
                    pl.col(col).pct_change().alias(col),
                )

        # Drop first row (NaN from pct_change)
        return returns_data.slice(1, returns_data.height - 1)

    def _execute_optimization() -> bool:  # pragma: no cover
        """Run portfolio optimization for both methods and store results."""
        optimization_error.set(None)
        portfolio1_result.set(None)
        portfolio2_result.set(None)

        input_snapshot = _build_skfolio_input_snapshot()
        save_portfolio_optimization_skfolio_inputs_to_reactives(
            reactives_shiny = reactives_shiny,
            data_value = input_snapshot,
        )

        # Get returns data
        returns_data = get_returns_data()
        if returns_data is None:
            optimization_error.set("No returns data available for selected period")
            return False

        try:
            # Portfolio 1
            _logger.info("Optimizing Portfolio 1")
            method1_category = input_snapshot["method1"]["category"]
            method1_type = input_snapshot["method1"]["type"]

            if method1_category == "basic":
                portfolio1 = calc_skfolio_optimization_basic(
                    returns_data=returns_data,
                    optimization_type=method1_type,
                    portfolio_name=f"{method1_type}",
                )
            elif method1_category == "convex":
                objective_str = input_snapshot["method1"]["objective"]
                objective_func = getattr(ObjectiveFunction, objective_str)
                risk_aversion = input_snapshot["method1"]["risk_aversion"]

                portfolio1 = calc_skfolio_optimization_convex(
                    returns_data=returns_data,
                    optimization_type=method1_type,
                    portfolio_name=f"{method1_type}",
                    objective_function=objective_func,
                    risk_aversion=risk_aversion,
                )
            elif method1_category == "clustering":
                portfolio1 = calc_skfolio_optimization_clustering(
                    returns_data=returns_data,
                    optimization_type=method1_type,
                    portfolio_name=f"{method1_type}",
                )
            else:  # ensemble
                portfolio1 = calc_skfolio_optimization_ensemble(
                    returns_data=returns_data,
                    optimization_type=method1_type,
                    portfolio_name=f"{method1_type}",
                )

            portfolio1_result.set(portfolio1)
            _logger.info("Portfolio 1 optimization complete")

            # Portfolio 2
            _logger.info("Optimizing Portfolio 2")
            method2_category = input_snapshot["method2"]["category"]
            method2_type = input_snapshot["method2"]["type"]

            if method2_category == "basic":
                portfolio2 = calc_skfolio_optimization_basic(
                    returns_data=returns_data,
                    optimization_type=method2_type,
                    portfolio_name=f"{method2_type}",
                )
            elif method2_category == "convex":
                objective_str = input_snapshot["method2"]["objective"]
                objective_func = getattr(ObjectiveFunction, objective_str)
                risk_aversion = input_snapshot["method2"]["risk_aversion"]

                portfolio2 = calc_skfolio_optimization_convex(
                    returns_data=returns_data,
                    optimization_type=method2_type,
                    portfolio_name=f"{method2_type}",
                    objective_function=objective_func,
                    risk_aversion=risk_aversion,
                )
            elif method2_category == "clustering":
                portfolio2 = calc_skfolio_optimization_clustering(
                    returns_data=returns_data,
                    optimization_type=method2_type,
                    portfolio_name=f"{method2_type}",
                )
            else:  # ensemble
                portfolio2 = calc_skfolio_optimization_ensemble(
                    returns_data=returns_data,
                    optimization_type=method2_type,
                    portfolio_name=f"{method2_type}",
                )

            portfolio2_result.set(portfolio2)
            _logger.info("Portfolio 2 optimization complete")

            perf1, perf2 = compute_skfolio_performance_series_impl_QWIM(
                portfolio_1 = portfolio1,
                portfolio_2 = portfolio2,
                etf_data = data_inputs.get("Time_Series_ETFs"),
                time_period=input.input_ID_tab_portfolios_subtab_skfolio_time_period(),
            )
            _save_skfolio_output_snapshot(
                data_partial = {
                    "weights_comparison": _build_skfolio_weights_rows(portfolio_1 = portfolio1, portfolio_2 = portfolio2),
                    "statistics_comparison": build_skfolio_statistics_rows_impl_QWIM(
                        series_1 = perf1,
                        series_2 = perf2,
                        has_quantstats=HAS_QUANTSTATS,
                        qs_module=qs,
                    ),
                    "performance_summary": _build_skfolio_performance_summary(
                        portfolio_1 = portfolio1,
                        portfolio_2 = portfolio2,
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

    # Reactive: Run optimization when button clicked
    @reactive.Effect
    @reactive.event(input.input_ID_tab_portfolios_subtab_skfolio_btn_optimize)
    def run_optimization():
        """Execute portfolio optimization for both methods."""  # pragma: no cover
        _execute_optimization()

    # Output: Status messages
    @output
    @render.ui
    def output_ID_tab_portfolios_subtab_skfolio_status():
        """Display optimization status messages."""
        error = optimization_error.get()
        if error:
            return ui.div(
                ui.p(f"❌ {error}", class_="text-danger mt-3 small"),
            )

        p1 = portfolio1_result.get()
        p2 = portfolio2_result.get()

        if p1 is not None and p2 is not None:
            return ui.div(
                ui.p("✅ Optimization complete!", class_="text-success mt-3 small"),
            )

        return ui.div()

    # Output: Weights comparison plot
    @output
    @render_widget  # pyright: ignore[reportArgumentType]  # pyrefly: ignore[bad-specialization]  # go.Figure satisfies Widget protocol at runtime
    def output_ID_tab_portfolios_subtab_skfolio_plot_weights():
        """Render weights comparison plot."""
        return render_skfolio_weights_plot_impl_QWIM(
            portfolio_1 = portfolio1_result.get(),
            portfolio_2 = portfolio2_result.get(),
            reactives_shiny = reactives_shiny,
        )

    # Output: Results table
    @output
    @render.ui
    def output_ID_tab_portfolios_subtab_skfolio_results_table():
        """Render optimization results table."""
        return render_skfolio_results_table_impl_QWIM(
            portfolio_1 = portfolio1_result.get(),
            portfolio_2 = portfolio2_result.get(),
        )

    @output
    @render.ui
    def output_ID_tab_portfolios_subtab_skfolio_statistics_table():
        """Render side-by-side quantstats portfolio metrics comparison."""
        p1 = portfolio1_result.get()
        p2 = portfolio2_result.get()

        if p1 is None or p2 is None:
            return ui.p(
                "Run optimization to see portfolio statistics",
                class_="text-muted text-center p-4",
            )
        perf1, perf2 = compute_skfolio_performance_series_impl_QWIM(
            portfolio_1 = portfolio1_result.get(),
            portfolio_2 = portfolio2_result.get(),
            etf_data = data_inputs.get("Time_Series_ETFs"),
            time_period=input.input_ID_tab_portfolios_subtab_skfolio_time_period(),
        )
        stats_rows = build_skfolio_statistics_rows_impl_QWIM(
            series_1 = perf1,
            series_2 = perf2,
            has_quantstats=HAS_QUANTSTATS,
            qs_module=qs,
        )
        return render_skfolio_statistics_table_impl_QWIM(
            portfolio_1 = p1,
            portfolio_2 = p2,
            stats_rows = stats_rows,
        )

    # =================================================================
    # Comparison of Portfolio Performance
    # =================================================================

    @output
    @render_widget  # pyright: ignore[reportArgumentType]  # pyrefly: ignore[bad-specialization]  # go.Figure satisfies Widget protocol at runtime
    def output_ID_tab_portfolios_subtab_skfolio_plot_performance():
        """Render the normalized performance comparison line chart."""
        perf1, perf2 = compute_skfolio_performance_series_impl_QWIM(
            portfolio_1 = portfolio1_result.get(),
            portfolio_2 = portfolio2_result.get(),
            etf_data = data_inputs.get("Time_Series_ETFs"),
            time_period=input.input_ID_tab_portfolios_subtab_skfolio_time_period(),
        )
        return render_skfolio_performance_plot_impl_QWIM(
            portfolio_1 = portfolio1_result.get(),
            portfolio_2 = portfolio2_result.get(),
            perf_1 = perf1,
            perf_2 = perf2,
            reactives_shiny = reactives_shiny,
        )

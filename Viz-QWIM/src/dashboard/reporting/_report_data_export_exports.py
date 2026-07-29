"""Private export implementations for report_data_export."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import polars as pl


def _get_public_report_data_export_module_QWIM() -> Any:
    """Resolve the public report_data_export module at call time."""
    from src.dashboard.reporting import report_data_export

    return report_data_export

from src.dashboard.reporting._report_data_export_covariance import (
    export_inputs_covariance_impl_QWIM,
    export_outputs_covariance_impl_QWIM,
)
from src.dashboard.reporting._report_data_export_goal_parity import (  # noqa: E402
    export_inputs_goal_parity_impl_QWIM,
    export_outputs_goal_parity_impl_QWIM,
)


def export_report_metadata_impl_QWIM(
    *, reactives_shiny: dict | None = None) -> Path:
    """Export report metadata (date, version) to ``report_metadata.json``.

    Parameters
    ----------
    reactives_shiny : dict | None
        Unused — present for API consistency.

    Returns
    -------
    Path
        Absolute path to the written file.
    """
    import datetime

    public_module = _get_public_report_data_export_module_QWIM()
    today = datetime.date.today()
    data: dict[str, str] = {
        "report_date": today.strftime("%B %d, %Y"),
        "report_date_iso": today.isoformat(),
        "report_version": "1.0",
        "generated_by": "QWIM Analytics Platform",
    }
    out_path = public_module._REPORTING_DIR / "report_metadata.json"
    public_module._write_json(file_path = out_path, data = data)
    return out_path


def export_client_info_impl_QWIM(
    *, reactives_shiny: dict | None) -> Path:
    """Export investor data to ``client_info.json``.

    Reads client information stored in ``reactives_shiny["Data_Clients"]`` via
    :func:`~src.dashboard.shiny_utils.utils_reporting.build_client_info_json_from_reactives`
    and writes the resulting dictionary to ``client_info.json`` in the reporting
    directory.  When the ``Data_Clients`` structure is absent or unpopulated, an
    empty ``{}`` fallback is written so that downstream Typst compilation still
    succeeds.

    Parameters
    ----------
    reactives_shiny : dict | None
        Shared reactive state dictionary containing ``Data_Clients``.

    Returns
    -------
    Path
        Absolute path to the written JSON file.
    """
    from src.dashboard.shiny_utils.utils_reporting import build_client_info_json_from_reactives

    public_module = _get_public_report_data_export_module_QWIM()
    data: dict[str, Any] = {}
    try:
        data = build_client_info_json_from_reactives(reactives_shiny = reactives_shiny)
        public_module._logger.info("Built client_info JSON from Data_Clients reactives")
    except Exception as exc:
        public_module._logger.warning(
            "Could not build client_info from Data_Clients reactives, using empty fallback: %s",
            exc,
        )
        data = {}

    out_path = public_module._REPORTING_DIR / "client_info.json"
    public_module._write_json(file_path = out_path, data = data)
    return out_path


def export_inputs_portfolio_analysis_impl_QWIM(
    *, reactives_shiny: dict | None) -> Path:
    """Export Portfolio Analysis subtab inputs to JSON."""
    public_module = _get_public_report_data_export_module_QWIM()
    data: dict[str, Any] = public_module._get_data_results_value(
        reactives_shiny = reactives_shiny,
        subtab_key = "Portfolio_Analysis_Inputs",
    )
    if not data:
        user_inputs = public_module._get_user_inputs(reactives_shiny = reactives_shiny)
        data = {
            "time_period": public_module._safe_str(
                value = user_inputs.get("Portfolio_Analysis_Time_Period", "1Y"),
            ),
            "date_range_start": public_module._safe_str(
                value = user_inputs.get("Portfolio_Analysis_Date_Range_Start"),
            ),
            "date_range_end": public_module._safe_str(
                value = user_inputs.get("Portfolio_Analysis_Date_Range_End"),
            ),
            "analysis_type": public_module._safe_str(
                value = user_inputs.get("Portfolio_Analysis_Type", "returns"),
            ),
            "rolling_window": public_module._safe_str(
                value = user_inputs.get("Portfolio_Analysis_Rolling_Window", "30"),
            ),
            "include_benchmark": public_module._safe_bool(
                value = user_inputs.get("Portfolio_Analysis_Include_Benchmark", True),
                default = True,
            ),
        }

    out_path = public_module._INPUTS_JSON_DIR / "inputs_portfolio_analysis.json"
    public_module._write_json(file_path = out_path, data = data)
    return out_path


def export_outputs_portfolio_analysis_impl_QWIM(
    *, reactives_shiny: dict | None) -> Path:
    """Export Portfolio Analysis subtab outputs to JSON."""
    public_module = _get_public_report_data_export_module_QWIM()
    data: dict[str, Any] = public_module._get_data_results_value(
        reactives_shiny = reactives_shiny,
        subtab_key = "Portfolio_Analysis_Outputs",
    )
    if not data:
        inner = public_module._get_inner_variables(reactives_shiny = reactives_shiny)
        basic_stats = public_module._safe_reactive_get(reactive_value = inner.get("Portfolio_Analysis_Basic_Stats"))
        quantstats = public_module._safe_reactive_get(
            reactive_value = inner.get("Portfolio_Analysis_Quantstats_Metrics"),
        )
        basic_list: list[dict[str, Any]] = (
            public_module._polars_to_records(df = basic_stats)
            if isinstance(basic_stats, pl.DataFrame)
            else (basic_stats if isinstance(basic_stats, list) else [])
        )
        quant_list: list[dict[str, Any]] = (
            public_module._polars_to_records(df = quantstats)
            if isinstance(quantstats, pl.DataFrame)
            else (quantstats if isinstance(quantstats, list) else [])
        )

        if not basic_list and not quant_list:
            portfolio_values_df, benchmark_values_df = public_module._load_sample_portfolio_data()
            if portfolio_values_df is not None and portfolio_values_df.height >= 2:
                public_module._logger.info("Computing portfolio analysis stats from sample CSV data")
                portfolio_analysis_stats = public_module._compute_portfolio_analysis_stats_from_values(
                    pv = portfolio_values_df,
                    bv = benchmark_values_df,
                )
                basic_list = portfolio_analysis_stats["basic_statistics"]
                quant_list = portfolio_analysis_stats["performance_metrics"]

        data = {"basic_statistics": basic_list, "performance_metrics": quant_list}

    out_path = public_module._OUTPUTS_JSON_DIR / "outputs_portfolio_analysis.json"
    public_module._write_json(file_path = out_path, data = data)
    return out_path


def export_inputs_portfolio_comparison_impl_QWIM(
    *, reactives_shiny: dict | None) -> Path:
    """Export Portfolio Comparison subtab inputs to JSON."""
    public_module = _get_public_report_data_export_module_QWIM()
    data: dict[str, Any] = public_module._get_data_results_value(
        reactives_shiny = reactives_shiny,
        subtab_key = "Portfolio_Comparison_Inputs",
    )
    if not data:
        user_inputs = public_module._get_user_inputs(reactives_shiny = reactives_shiny)
        data = {
            "time_period": public_module._safe_str(
                value = user_inputs.get("Portfolio_Comparison_Time_Period", "1Y"),
            ),
            "date_range_start": public_module._safe_str(
                value = user_inputs.get("Portfolio_Comparison_Date_Range_Start"),
            ),
            "date_range_end": public_module._safe_str(
                value = user_inputs.get("Portfolio_Comparison_Date_Range_End"),
            ),
            "viz_type": public_module._safe_str(
                value = user_inputs.get("Portfolio_Comparison_Viz_Type", "normalized"),
            ),
            "show_diff": public_module._safe_bool(
                value = user_inputs.get("Portfolio_Comparison_Show_Diff", False),
                default = False,
            ),
        }

    out_path = public_module._INPUTS_JSON_DIR / "inputs_portfolio_comparison.json"
    public_module._write_json(file_path = out_path, data = data)
    return out_path


def export_outputs_portfolio_comparison_impl_QWIM(
    *, reactives_shiny: dict | None) -> Path:
    """Export Portfolio Comparison subtab outputs to JSON."""
    public_module = _get_public_report_data_export_module_QWIM()
    data: dict[str, Any] = public_module._get_data_results_value(
        reactives_shiny = reactives_shiny,
        subtab_key = "Portfolio_Comparison_Outputs",
    )
    if not data:
        inner = public_module._get_inner_variables(reactives_shiny = reactives_shiny)
        stats_raw = public_module._safe_reactive_get(reactive_value = inner.get("Portfolio_Comparison_Stats"))
        stats: dict[str, Any] = stats_raw if isinstance(stats_raw, dict) else {}

        if not stats:
            portfolio_values_df, benchmark_values_df = public_module._load_sample_portfolio_data()
            if portfolio_values_df is not None and portfolio_values_df.height >= 2:
                public_module._logger.info(
                    "Computing portfolio comparison metrics from sample CSV data",
                )
                stats = public_module._compute_portfolio_metrics_from_values(
                    pv = portfolio_values_df,
                    bv = benchmark_values_df,
                )

        data = {
            "time_period": public_module._safe_str(value = stats.get("time_period")),
            "start_date": public_module._safe_str(value = stats.get("start_date")),
            "end_date": public_module._safe_str(value = stats.get("end_date")),
            "viz_type": public_module._safe_str(value = stats.get("viz_type", "normalized")),
            "metrics": {
                "total_return": {
                    "portfolio": public_module._safe_float(value = stats.get("total_return_portfolio")),
                    "benchmark": public_module._safe_float(value = stats.get("total_return_benchmark")),
                    "difference": public_module._safe_float(value = stats.get("total_return_difference")),
                },
                "annualized_return": {
                    "portfolio": public_module._safe_float(
                        value = stats.get("annualized_return_portfolio"),
                    ),
                    "benchmark": public_module._safe_float(
                        value = stats.get("annualized_return_benchmark"),
                    ),
                    "difference": public_module._safe_float(
                        value = stats.get("annualized_return_difference"),
                    ),
                },
                "volatility": {
                    "portfolio": public_module._safe_float(value = stats.get("volatility_portfolio")),
                    "benchmark": public_module._safe_float(value = stats.get("volatility_benchmark")),
                    "difference": public_module._safe_float(value = stats.get("volatility_difference")),
                },
                "max_drawdown": {
                    "portfolio": public_module._safe_float(value = stats.get("max_drawdown_portfolio")),
                    "benchmark": public_module._safe_float(value = stats.get("max_drawdown_benchmark")),
                    "difference": public_module._safe_float(value = stats.get("max_drawdown_difference")),
                },
                "sharpe_ratio": {
                    "portfolio": public_module._safe_float(value = stats.get("sharpe_ratio_portfolio")),
                    "benchmark": public_module._safe_float(value = stats.get("sharpe_ratio_benchmark")),
                    "difference": public_module._safe_float(value = stats.get("sharpe_ratio_difference")),
                },
                "correlation": public_module._safe_float(value = stats.get("correlation")),
                "tracking_error": public_module._safe_float(value = stats.get("tracking_error")),
                "information_ratio": public_module._safe_float(value = stats.get("information_ratio")),
            },
        }

    out_path = public_module._OUTPUTS_JSON_DIR / "outputs_portfolio_comparison.json"
    public_module._write_json(file_path = out_path, data = data)
    return out_path


def export_inputs_weights_analysis_impl_QWIM(
    *, reactives_shiny: dict | None) -> Path:
    """Export Weights Distribution subtab inputs to JSON."""
    public_module = _get_public_report_data_export_module_QWIM()
    data: dict[str, Any] = public_module._get_data_results_value(
        reactives_shiny = reactives_shiny,
        subtab_key = "Weights_Analysis_Inputs",
    )
    if not data:
        user_inputs = public_module._get_user_inputs(reactives_shiny = reactives_shiny)
        selected = public_module._safe_reactive_get(reactive_value = user_inputs.get("Weights_Selected_Components"))
        if not isinstance(selected, list):
            selected = []
        data = {
            "time_period": public_module._safe_str(value = user_inputs.get("Weights_Time_Period", "5Y")),
            "date_range_start": public_module._safe_str(value = user_inputs.get("Weights_Date_Range_Start")),
            "date_range_end": public_module._safe_str(value = user_inputs.get("Weights_Date_Range_End")),
            "selected_components": [str(component_name) for component_name in selected],
            "viz_type": public_module._safe_str(value = user_inputs.get("Weights_Viz_Type", "area")),
            "show_pct": public_module._safe_bool(value = user_inputs.get("Weights_Show_Pct", True), default = True),
            "sort_components": public_module._safe_bool(
                value = user_inputs.get("Weights_Sort_Components", True),
                default = True,
            ),
        }

    out_path = public_module._INPUTS_JSON_DIR / "inputs_weights_analysis.json"
    public_module._write_json(file_path = out_path, data = data)
    return out_path


def export_outputs_weights_analysis_impl_QWIM(
    *, reactives_shiny: dict | None) -> Path:
    """Export Weights Distribution subtab outputs to JSON."""
    public_module = _get_public_report_data_export_module_QWIM()
    data: dict[str, Any] = public_module._get_data_results_value(
        reactives_shiny = reactives_shiny,
        subtab_key = "Weights_Analysis_Outputs",
    )
    if not data:
        inner = public_module._get_inner_variables(reactives_shiny = reactives_shiny)
        summary_raw = public_module._safe_reactive_get(reactive_value = inner.get("Weights_Summary_Stats"))
        summary: list[dict[str, Any]] = (
            public_module._polars_to_records(df = summary_raw)
            if isinstance(summary_raw, pl.DataFrame)
            else (summary_raw if isinstance(summary_raw, list) else [])
        )
        if not summary:
            sample_weights_df = public_module._load_sample_weights_data()
            if sample_weights_df is not None:
                public_module._logger.info(
                    "Computing weights analysis statistics from sample weights CSV data",
                )
                summary = public_module._compute_weight_statistics_from_weights(weights_df = sample_weights_df)

        data = {"weight_statistics": summary}

    out_path = public_module._OUTPUTS_JSON_DIR / "outputs_weights_analysis.json"
    public_module._write_json(file_path = out_path, data = data)
    return out_path


def export_inputs_skfolio_optimization_impl_QWIM(
    *, reactives_shiny: dict | None) -> Path:
    """Export skfolio Optimization subtab inputs to JSON."""
    public_module = _get_public_report_data_export_module_QWIM()
    data: dict[str, Any] = public_module._get_data_results_value(
        reactives_shiny = reactives_shiny,
        subtab_key = "Portfolio_Optimization_Skfolio_Inputs",
    )
    if not data:
        user_inputs = public_module._get_user_inputs(reactives_shiny = reactives_shiny)
        data = {
            "time_period": public_module._safe_str(value = user_inputs.get("Skfolio_Time_Period", "3Y")),
            "method1": {
                "category": public_module._safe_str(
                    value = user_inputs.get("Skfolio_Method1_Category", "basic"),
                ),
                "type": public_module._safe_str(
                    value = user_inputs.get("Skfolio_Method1_Type", "equal_weighted"),
                ),
                "objective": public_module._safe_str(value = user_inputs.get("Skfolio_Method1_Objective")),
                "risk_aversion": public_module._safe_float(
                    value = user_inputs.get("Skfolio_Method1_Risk_Aversion"),
                    default = 1.0,
                ),
            },
            "method2": {
                "category": public_module._safe_str(
                    value = user_inputs.get("Skfolio_Method2_Category", "convex"),
                ),
                "type": public_module._safe_str(
                    value = user_inputs.get("Skfolio_Method2_Type", "mean_risk"),
                ),
                "objective": public_module._safe_str(value = user_inputs.get("Skfolio_Method2_Objective")),
                "risk_aversion": public_module._safe_float(
                    value = user_inputs.get("Skfolio_Method2_Risk_Aversion"),
                    default = 1.0,
                ),
            },
        }

    out_path = public_module._INPUTS_JSON_DIR / "inputs_skfolio_optimization.json"
    public_module._write_json(file_path = out_path, data = data)
    return out_path


def export_outputs_skfolio_optimization_impl_QWIM(
    *, reactives_shiny: dict | None) -> Path:
    """Export skfolio Optimization subtab outputs to JSON."""
    public_module = _get_public_report_data_export_module_QWIM()
    data: dict[str, Any] = public_module._get_data_results_value(
        reactives_shiny = reactives_shiny,
        subtab_key = "Portfolio_Optimization_Skfolio_Outputs",
    )
    if not data:
        inner = public_module._get_inner_variables(reactives_shiny = reactives_shiny)
        weights_raw = public_module._safe_reactive_get(reactive_value = inner.get("Skfolio_Results_Table"))
        weights: list[dict[str, Any]] = (
            public_module._polars_to_records(df = weights_raw)
            if isinstance(weights_raw, pl.DataFrame)
            else (weights_raw if isinstance(weights_raw, list) else [])
        )
        perf_raw = public_module._safe_reactive_get(reactive_value = inner.get("Skfolio_Performance_Summary"))
        perf: dict[str, Any] = perf_raw if isinstance(perf_raw, dict) else {}
        method1_raw = perf.get("method1", {}) if perf else {}
        method2_raw = perf.get("method2", {}) if perf else {}
        performance_summary: dict[str, Any] = {
            "method1": {
                "label": public_module._safe_str(value = method1_raw.get("label", "Method 1")),
                "annualized_return": public_module._safe_float(value = method1_raw.get("annualized_return")),
                "volatility": public_module._safe_float(value = method1_raw.get("volatility")),
                "sharpe_ratio": public_module._safe_float(value = method1_raw.get("sharpe_ratio")),
            },
            "method2": {
                "label": public_module._safe_str(value = method2_raw.get("label", "Method 2")),
                "annualized_return": public_module._safe_float(value = method2_raw.get("annualized_return")),
                "volatility": public_module._safe_float(value = method2_raw.get("volatility")),
                "sharpe_ratio": public_module._safe_float(value = method2_raw.get("sharpe_ratio")),
            },
        }
        data = {
            "weights_comparison": weights,
            "statistics_comparison": [],
            "performance_summary": performance_summary,
        }

    out_path = public_module._OUTPUTS_JSON_DIR / "outputs_skfolio_optimization.json"
    public_module._write_json(file_path = out_path, data = data)
    return out_path


def export_inputs_optimalportfolios_optimization_impl_QWIM(
    *, reactives_shiny: dict | None) -> Path:
    """Export OptimalPortfolios Optimization subtab inputs to JSON."""
    public_module = _get_public_report_data_export_module_QWIM()
    data: dict[str, Any] = public_module._get_data_results_value(
        reactives_shiny = reactives_shiny,
        subtab_key = "Portfolio_Optimization_OptimalPortfolios_Inputs",
    )
    if not data:
        data = {
            "time_period": "3y",
            "benchmark_key": "Benchmark_Portfolio",
            "method1": {"type": "MIN_VARIANCE", "is_long_only": True},
            "method2": {"type": "MAX_SHARPE", "risk_free_rate": 0.0, "is_long_only": True},
        }

    out_path = public_module._INPUTS_JSON_DIR / "inputs_optimalportfolios_optimization.json"
    public_module._write_json(file_path = out_path, data = data)
    return out_path


def export_outputs_optimalportfolios_optimization_impl_QWIM(
    *, reactives_shiny: dict | None) -> Path:
    """Export OptimalPortfolios Optimization subtab outputs to JSON."""
    public_module = _get_public_report_data_export_module_QWIM()
    data: dict[str, Any] = public_module._get_data_results_value(
        reactives_shiny = reactives_shiny,
        subtab_key = "Portfolio_Optimization_OptimalPortfolios_Outputs",
    )
    if not data:
        data = {
            "weights_comparison": [],
            "statistics_comparison": [],
            "performance_summary": {
                "method1": {
                    "label": "Method 1",
                    "annualized_return": 0.0,
                    "volatility": 0.0,
                    "sharpe_ratio": 0.0,
                },
                "method2": {
                    "label": "Method 2",
                    "annualized_return": 0.0,
                    "volatility": 0.0,
                    "sharpe_ratio": 0.0,
                },
            },
        }

    out_path = public_module._OUTPUTS_JSON_DIR / "outputs_optimalportfolios_optimization.json"
    public_module._write_json(file_path = out_path, data = data)
    return out_path


def export_inputs_simulation_impl_QWIM(
    *, reactives_shiny: dict | None) -> Path:
    """Export Simulation subtab inputs to JSON."""
    public_module = _get_public_report_data_export_module_QWIM()
    data: dict[str, Any] = public_module._get_data_results_value(
        reactives_shiny = reactives_shiny,
        subtab_key = "Portfolio_Simulation_Inputs",
    )
    if not data:
        user_inputs = public_module._get_user_inputs(reactives_shiny = reactives_shiny)
        selected = public_module._safe_reactive_get(reactive_value = user_inputs.get("Simulation_Selected_Components"))
        if not isinstance(selected, list):
            selected = []
        data = {
            "selected_components": [str(component_name) for component_name in selected],
            "num_scenarios": int(
                public_module._safe_float(value = user_inputs.get("Simulation_Num_Scenarios"), default = 1000.0),
            ),
            "num_days": int(public_module._safe_float(value = user_inputs.get("Simulation_Num_Days"), default = 252.0)),
            "start_date": public_module._safe_str(value = user_inputs.get("Simulation_Start_Date")),
            "initial_value": public_module._safe_float(value = user_inputs.get("Simulation_Initial_Value"), default = 100.0),
            "distribution_type": public_module._safe_str(
                value = user_inputs.get("Simulation_Distribution_Type", "normal"),
            ),
            "degrees_of_freedom": public_module._safe_float(
                value = user_inputs.get("Simulation_Degrees_Of_Freedom"),
                default = 5.0,
            ),
            "rng_type": public_module._safe_str(value = user_inputs.get("Simulation_RNG_Type", "pcg64")),
            "seed": int(public_module._safe_float(value = user_inputs.get("Simulation_Seed"), default = 42.0)),
        }

    out_path = public_module._INPUTS_JSON_DIR / "inputs_simulation.json"
    public_module._write_json(file_path = out_path, data = data)
    return out_path


def export_outputs_simulation_impl_QWIM(
    *, reactives_shiny: dict | None) -> Path:
    """Export Simulation subtab outputs to JSON."""
    public_module = _get_public_report_data_export_module_QWIM()
    data: dict[str, Any] = public_module._get_data_results_value(
        reactives_shiny = reactives_shiny,
        subtab_key = "Portfolio_Simulation_Outputs",
    )
    if not data:
        inner = public_module._get_inner_variables(reactives_shiny = reactives_shiny)
        stats_raw = public_module._safe_reactive_get(reactive_value = inner.get("Simulation_Stats"))
        stats: dict[str, Any] = stats_raw if isinstance(stats_raw, dict) else {}
        user_inputs = public_module._get_user_inputs(reactives_shiny = reactives_shiny)
        fallback_num_scenarios = int(
            public_module._safe_float(
                value = public_module._safe_reactive_get(
                    reactive_value = user_inputs.get("Input_Tab_Results_Subtab_Simulation_Num_Scenarios"),
                ),
                default = 1000.0,
            ),
        )
        fallback_horizon_days = int(
            public_module._safe_float(
                value = public_module._safe_reactive_get(
                    reactive_value = user_inputs.get("Input_Tab_Results_Subtab_Simulation_Num_Days"),
                ),
                default = 252.0,
            ),
        )

        if not stats:
            portfolio_values_sim_df, _ = public_module._load_sample_portfolio_data()
            if portfolio_values_sim_df is not None and portfolio_values_sim_df.height >= 2:
                public_module._logger.info("Computing simulation stats from sample CSV data")
                stats = public_module._compute_simulation_stats_from_values(
                    pv = portfolio_values_sim_df,
                    num_scenarios=fallback_num_scenarios,
                    num_days=fallback_horizon_days,
                    initial_value=100.0,
                )

        data = {
            "summary_statistics": {
                "num_scenarios": int(public_module._safe_float(value = stats.get("num_scenarios")))
                or fallback_num_scenarios,
                "horizon_days": int(public_module._safe_float(value = stats.get("horizon_days")))
                or fallback_horizon_days,
                "initial_value": public_module._safe_float(value = stats.get("initial_value"), default = 100.0),
                "mean_terminal_value": public_module._safe_float(value = stats.get("mean_terminal_value")),
                "median_terminal_value": public_module._safe_float(value = stats.get("median_terminal_value")),
                "std_dev_terminal_value": public_module._safe_float(
                    value = stats.get("std_dev_terminal_value"),
                ),
                "percentile_5": public_module._safe_float(value = stats.get("percentile_5")),
                "percentile_25": public_module._safe_float(value = stats.get("percentile_25")),
                "percentile_75": public_module._safe_float(value = stats.get("percentile_75")),
                "percentile_95": public_module._safe_float(value = stats.get("percentile_95")),
                "min_terminal_value": public_module._safe_float(value = stats.get("min_terminal_value")),
                "max_terminal_value": public_module._safe_float(value = stats.get("max_terminal_value")),
                "probability_of_loss": public_module._safe_float(value = stats.get("probability_of_loss")),
            },
        }

    out_path = public_module._OUTPUTS_JSON_DIR / "outputs_simulation.json"
    public_module._write_json(file_path = out_path, data = data)
    return out_path


def export_all_report_data_impl_QWIM(
    *, reactives_shiny: dict | None) -> dict[str, Path]:
    """Export every JSON file required by the Typst report template."""
    public_module = _get_public_report_data_export_module_QWIM()
    public_module._logger.info("Exporting all report data to JSON files")

    paths: dict[str, Path] = {}
    paths["report_metadata"] = public_module.export_report_metadata(reactives_shiny = reactives_shiny)
    paths["client_info"] = public_module.export_client_info(reactives_shiny = reactives_shiny)
    paths["inputs_portfolio_analysis"] = public_module.export_inputs_portfolio_analysis(
        reactives_shiny = reactives_shiny,
    )
    paths["outputs_portfolio_analysis"] = public_module.export_outputs_portfolio_analysis(
        reactives_shiny = reactives_shiny,
    )
    paths["inputs_portfolio_comparison"] = public_module.export_inputs_portfolio_comparison(
        reactives_shiny = reactives_shiny,
    )
    paths["outputs_portfolio_comparison"] = public_module.export_outputs_portfolio_comparison(
        reactives_shiny = reactives_shiny,
    )
    paths["inputs_weights_analysis"] = public_module.export_inputs_weights_analysis(reactives_shiny = reactives_shiny)
    paths["outputs_weights_analysis"] = public_module.export_outputs_weights_analysis(reactives_shiny = reactives_shiny)
    paths["inputs_skfolio_optimization"] = public_module.export_inputs_skfolio_optimization(
        reactives_shiny = reactives_shiny,
    )
    paths["outputs_skfolio_optimization"] = public_module.export_outputs_skfolio_optimization(
        reactives_shiny = reactives_shiny,
    )
    paths["inputs_optimalportfolios_optimization"] = (
        public_module.export_inputs_optimalportfolios_optimization(reactives_shiny = reactives_shiny)
    )
    paths["outputs_optimalportfolios_optimization"] = (
        public_module.export_outputs_optimalportfolios_optimization(reactives_shiny = reactives_shiny)
    )
    paths["inputs_simulation"] = public_module.export_inputs_simulation(reactives_shiny = reactives_shiny)
    paths["outputs_simulation"] = public_module.export_outputs_simulation(reactives_shiny = reactives_shiny)
    paths["inputs_covariance"] = public_module.export_inputs_covariance(reactives_shiny=reactives_shiny)
    paths["outputs_covariance"] = public_module.export_outputs_covariance(reactives_shiny=reactives_shiny,)
    paths["data_clients"] = public_module.export_data_clients_json(reactives_shiny = reactives_shiny)
    paths["data_results"] = public_module.export_data_results_json(reactives_shiny = reactives_shiny)
    paths["report_config"] = public_module.export_report_config(
        reactives_shiny = reactives_shiny,
        section_flags = {
            "include_advisor_info": True,
            "include_portfolio_analysis": True,
            "include_portfolio_comparison": True,
            "include_weights_analysis": True,
            "include_skfolio_optimization": False,
            "include_optimalportfolios_optimization": False,
            "include_simulation": True,
            "include_goal_parity": True,
            "include_covariance": True,
        },
    )

    public_module._logger.info("Exported %d JSON files for report generation", len(paths))
    return paths


def export_data_clients_json_impl_QWIM(
    *, reactives_shiny: dict | None) -> Path:
    """Write ``data_clients.json`` combining client info and advisor info."""
    public_module = _get_public_report_data_export_module_QWIM()
    client_info_path = public_module.export_client_info(reactives_shiny = reactives_shiny)
    client_data = public_module._read_json_dict(file_path = client_info_path)

    advisor_data: dict[str, Any] = {}
    if reactives_shiny and isinstance(reactives_shiny, dict):
        raw_advisor = reactives_shiny.get("Advisor_Info", {})
        if isinstance(raw_advisor, dict):
            for key_name, reactive_value in raw_advisor.items():
                try:
                    advisor_data[key_name] = (
                        reactive_value.get() if hasattr(reactive_value, "get") else reactive_value
                    )
                except Exception:
                    advisor_data[key_name] = None

    consolidated: dict[str, Any] = {}
    consolidated.update(client_data)
    consolidated["advisor_info"] = advisor_data

    out_path = public_module._REPORTING_DIR / "data_clients.json"
    public_module._write_json(file_path = out_path, data = consolidated)
    public_module._logger.info("Wrote data_clients.json")
    return out_path


def export_data_results_json_impl_QWIM(
    *, reactives_shiny: dict | None) -> Path:
    """Write ``data_results.json`` combining all analysis inputs and outputs."""
    public_module = _get_public_report_data_export_module_QWIM()
    export_mapping = {
        "Portfolio_Analysis_Inputs": public_module.export_inputs_portfolio_analysis,
        "Portfolio_Analysis_Outputs": public_module.export_outputs_portfolio_analysis,
        "Portfolio_Comparison_Inputs": public_module.export_inputs_portfolio_comparison,
        "Portfolio_Comparison_Outputs": public_module.export_outputs_portfolio_comparison,
        "Weights_Analysis_Inputs": public_module.export_inputs_weights_analysis,
        "Weights_Analysis_Outputs": public_module.export_outputs_weights_analysis,
        "Portfolio_Optimization_Skfolio_Inputs": public_module.export_inputs_skfolio_optimization,
        "Portfolio_Optimization_Skfolio_Outputs": public_module.export_outputs_skfolio_optimization,
        "Portfolio_Optimization_OptimalPortfolios_Inputs": (
            public_module.export_inputs_optimalportfolios_optimization
        ),
        "Portfolio_Optimization_OptimalPortfolios_Outputs": (
            public_module.export_outputs_optimalportfolios_optimization
        ),
        "Portfolio_Simulation_Inputs": public_module.export_inputs_simulation,
        "Portfolio_Simulation_Outputs": public_module.export_outputs_simulation,
        "Goal_Parity_Inputs": public_module.export_inputs_goal_parity,
        "Goal_Parity_Outputs": public_module.export_outputs_goal_parity,
        "Covariance_Inputs": public_module.export_inputs_covariance,
        "Covariance_Outputs": public_module.export_outputs_covariance,
    }

    data: dict[str, Any] = {}
    for subtab_key_name, export_function in export_mapping.items():
        exported_path = export_function(reactives_shiny=reactives_shiny)
        data[subtab_key_name] = public_module._read_json_dict(file_path = exported_path)

    out_path = public_module._REPORTING_DIR / "data_results.json"
    public_module._write_json(file_path = out_path, data = data)
    public_module._logger.info("Wrote data_results.json")
    return out_path


def export_report_config_impl_QWIM(
    *, reactives_shiny: dict | None, section_flags: dict[str, bool], report_title: str = "") -> Path:
    """Write ``report_config.json`` with section enable flags."""
    import datetime

    public_module = _get_public_report_data_export_module_QWIM()
    today = datetime.date.today()
    include_partner = False
    if reactives_shiny and isinstance(reactives_shiny, dict):
        user_inputs = reactives_shiny.get("User_Inputs_Shiny", {})
        if isinstance(user_inputs, dict):
            reactive_value = user_inputs.get(
                "Input_Tab_Clients_Subtab_Setup_Checkbox_Include_Partner_in_Analysis",
            )
            if reactive_value is not None:
                try:
                    include_partner = public_module._safe_bool(
                        value = reactive_value.get() if hasattr(reactive_value, "get") else reactive_value,
                        default = False,
                    )
                except Exception:
                    include_partner = False

    config: dict[str, Any] = {
        "report_date": today.strftime("%B %d, %Y"),
        "report_date_iso": today.isoformat(),
        "report_title": report_title or "QWIM Wealth Management Report",
        "include_partner": include_partner,
    }
    config.update(section_flags)

    out_path = public_module._REPORTING_DIR / "report_config.json"
    public_module._write_json(file_path = out_path, data = config)
    public_module._logger.info("Wrote report_config.json with section flags: %s", section_flags)
    return out_path
"""Rendering and configuration helpers for the Simulation subtab.

This private module holds the pure and low-side-effect support logic used by
the public Simulation subtab facade. The public module retains the Shiny UI
and server entry points plus source-visible widget identifiers.
"""

from __future__ import annotations

import datetime as dt

from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import plotly.graph_objects as go
import polars as pl

from shiny import ui

from src.dashboard.reporting.report_plot_export import (
    build_plotnine_simulation_fan_chart,
    build_plotnine_simulation_terminal_value_distribution,
)
from src.dashboard.shiny_tab_results._subtab_simulation_shared import (
    ALL_ETF_SYMBOLS,
    _read_compute_and_compare_toggle_enabled,
    _resolve_compare_progress_running_display,
    _resolve_compare_progress_running_pill,
    format_compare_table_as_html,
)
from src.dashboard.shiny_utils.reactives_shiny import update_visual_object_in_reactives
from src.models.simulation.simulation_dispatch import (
    COMPUTATION_TYPES_SIMULATION_COMPARE,
    Simulation_Run_Config,
    build_compare_summary_table,
)
from src.num_methods.scenarios.scenarios_distrib import Distribution_Type
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name = __name__)


def _coerce_progress_int_or_default(
    *, raw_value: Any, default_value: int) -> int:
    """Convert progress counters to ``int`` while rejecting boolean inputs."""
    if raw_value is None or isinstance(raw_value, bool):
        return default_value

    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return default_value


def _coerce_progress_float_or_default(
    *, raw_value: Any, default_value: float = 0.0) -> float:
    """Convert progress timing values to ``float`` while rejecting booleans."""
    if raw_value is None or isinstance(raw_value, bool):
        return default_value

    try:
        return float(raw_value)
    except (TypeError, ValueError):
        return default_value


def load_etf_price_data_for_simulation(
    *, data_inputs: dict[str, Any], module_file_path: str) -> pl.DataFrame | None:
    """Load ETF price data from shared dashboard inputs or the CSV fallback."""
    if data_inputs and "ETF_Prices" in data_inputs:
        raw_data = data_inputs["ETF_Prices"]
        if isinstance(raw_data, pl.DataFrame) and not raw_data.is_empty():
            return raw_data

    csv_path = Path(module_file_path).resolve().parents[3] / "inputs" / "raw" / "data_ETFs.csv"
    if csv_path.exists():
        try:
            data_frame = pl.read_csv(csv_path)
            if "date" in data_frame.columns:
                data_frame = data_frame.rename({"date": "Date"})
            return data_frame
        except Exception as exc:
            _logger.error("Failed to load ETF CSV: %s", exc)
            return None
    return None


def resolve_available_etf_components_for_simulation(
    *, data_inputs: dict[str, Any], module_file_path: str) -> list[str]:
    """Resolve the ETF components available for the Simulation subtab."""
    etf_price_data = load_etf_price_data_for_simulation(data_inputs = data_inputs, module_file_path = module_file_path)
    if etf_price_data is None:
        return ALL_ETF_SYMBOLS
    return [column_name for column_name in etf_price_data.columns if column_name not in ("Date", "date")]


def resolve_selected_etf_components_for_simulation(
    *, input_obj: Any, available_components: list[str], num_default_selected: int) -> list[str]:
    """Resolve the selected ETF components from dynamic checkbox inputs."""
    if not available_components:
        return []

    try:
        select_all = input_obj.input_ID_tab_results_subtab_simulation_select_all_components()
    except Exception:
        return available_components[:num_default_selected]

    if select_all:
        return available_components

    selected_components: list[str] = []
    for component_name in available_components:
        component_input_id = f"input_ID_tab_results_subtab_simulation_component_{component_name}"
        try:
            if input_obj[component_input_id]():
                selected_components.append(component_name)
        except Exception:
            continue

    if not selected_components:
        return available_components[:num_default_selected]
    return selected_components


def build_simulation_run_config_for_subtab(
    *,
    data_inputs: dict[str, Any],
    degrees_of_freedom: float,
    distribution_type: Distribution_Type,
    initial_value: float,
    module_file_path: str,
    num_days: int,
    num_scenarios: int,
    rng_type: str,
    seed: int,
    selected_components: list[str],
    start_date: dt.date,
) -> Simulation_Run_Config:
    """Build a Simulation run configuration from normalized subtab inputs.

    Boolean ETF price columns are treated as invalid price data and excluded
    before numeric return estimation.
    """
    num_components = len(selected_components)
    etf_price_data = load_etf_price_data_for_simulation(data_inputs = data_inputs, module_file_path = module_file_path)
    if etf_price_data is not None:
        columns_present = [
            column_name
            for column_name in selected_components
            if column_name in etf_price_data.columns
            and etf_price_data.schema.get(column_name) != pl.Boolean
        ]
        if len(columns_present) < num_components:
            _logger.warning(
                "Some selected ETFs not in data: %s",
                set(selected_components) - set(columns_present),
            )
        if columns_present:
            prices = etf_price_data.select(columns_present).to_numpy()
            returns = np.diff(prices, axis=0) / prices[:-1]
            mean_returns = np.mean(returns, axis=0)
            covariance_matrix = np.cov(returns, rowvar=False)
            if distribution_type == Distribution_Type.LOGNORMAL:
                mean_returns = 1.0 + mean_returns
            selected_components = columns_present
        else:
            mean_returns = np.zeros(num_components, dtype=np.float64)
            covariance_matrix = np.eye(num_components, dtype=np.float64) * 0.0004
    else:
        mean_returns = np.zeros(num_components, dtype=np.float64)
        covariance_matrix = np.eye(num_components, dtype=np.float64) * 0.0004

    weights = np.ones(len(selected_components), dtype=np.float64) / len(selected_components)

    return Simulation_Run_Config(
        names_components=selected_components,
        weights=weights,
        distribution_type=distribution_type,
        mean_returns=mean_returns,
        covariance_matrix=covariance_matrix,
        initial_value=initial_value,
        num_scenarios=num_scenarios,
        num_days=num_days,
        start_date=start_date,
        random_seed=seed,
        degrees_of_freedom=degrees_of_freedom,
        rng_type=rng_type,
    )


def build_fan_chart_figure_for_simulation(
    *,
    create_empty_figure: Callable[..., go.Figure],
    reactives_shiny: dict[str, Any],
    results_df: pl.DataFrame | None,
    stats_df: pl.DataFrame | None,
) -> go.Figure:
    """Build the portfolio-value fan chart figure for the Simulation subtab.

    Boolean scenario columns are treated as invalid simulation results and keep
    the helper on the existing empty-figure path.
    """
    if stats_df is None or results_df is None:
        return create_empty_figure(
            title="Portfolio Value Fan Chart",
            message="Click 'Run Simulation' to generate results",
        )

    scenario_columns = [column_name for column_name in results_df.columns if column_name.startswith("Scenario_")]
    if not scenario_columns or any(results_df.schema.get(column_name) == pl.Boolean for column_name in scenario_columns):
        return create_empty_figure(
            title="Portfolio Value Fan Chart",
            message="Click 'Run Simulation' to generate results",
        )

    dates = stats_df["Date"].to_list()
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=dates + dates[::-1],
            y=stats_df["P95"].to_list() + stats_df["P5"].to_list()[::-1],
            fill="toself",
            fillcolor="rgba(31, 119, 180, 0.15)",
            line={"width": 0},
            name="5th-95th Percentile",
            hoverinfo="skip",
        ),
    )
    figure.add_trace(
        go.Scatter(
            x=dates + dates[::-1],
            y=stats_df["P75"].to_list() + stats_df["P25"].to_list()[::-1],
            fill="toself",
            fillcolor="rgba(31, 119, 180, 0.30)",
            line={"width": 0},
            name="25th-75th Percentile",
            hoverinfo="skip",
        ),
    )
    figure.add_trace(
        go.Scatter(
            x=dates,
            y=stats_df["Median"].to_list(),
            mode="lines",
            name="Median",
            line={"color": "rgb(31, 119, 180)", "width": 2.5},
            hovertemplate="<b>Median</b><br>Date: %{x}<br>Value: $%{y:,.2f}<extra></extra>",
        ),
    )
    figure.add_trace(
        go.Scatter(
            x=dates,
            y=stats_df["Mean"].to_list(),
            mode="lines",
            name="Mean",
            line={"color": "rgb(255, 127, 14)", "width": 2, "dash": "dash"},
            hovertemplate="<b>Mean</b><br>Date: %{x}<br>Value: $%{y:,.2f}<extra></extra>",
        ),
    )

    for path_column in scenario_columns[:10]:
        figure.add_trace(
            go.Scatter(
                x=dates,
                y=results_df[path_column].to_list(),
                mode="lines",
                line={"width": 0.5, "color": "rgba(150, 150, 150, 0.3)"},
                showlegend=False,
                hoverinfo="skip",
            ),
        )

    initial_value = results_df.select(scenario_columns[0]).to_series()[0]
    figure.add_hline(
        y=initial_value,
        line_dash="dot",
        line_color="gray",
        annotation_text=f"Initial: ${initial_value:,.2f}",
        annotation_position="bottom right",
    )
    figure.update_layout(
        title="Monte Carlo Simulation - Portfolio Value Paths",
        xaxis_title="Date",
        yaxis_title="Portfolio Value ($)",
        hovermode="x unified",
        template="plotly_white",
        height=600,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
        },
    )
    figure.update_xaxes(rangeslider_visible=True)

    plotnine_figure = build_plotnine_simulation_fan_chart(results_df = results_df)
    update_visual_object_in_reactives(
        reactives_shiny = reactives_shiny,
        chart_key = "Chart_Simulation_Portfolio_Value_Fan_Chart",
        figure = plotnine_figure,
    )
    return figure


def build_histogram_figure_for_simulation(
    *,
    create_empty_figure: Callable[..., go.Figure],
    reactives_shiny: dict[str, Any],
    results_df: pl.DataFrame | None,
) -> go.Figure:
    """Build the terminal-value histogram figure for the Simulation subtab.

    Boolean scenario columns are treated as invalid simulation results and keep
    the helper on the existing empty-figure path.
    """
    if results_df is None:
        return create_empty_figure(
            title="Terminal Value Distribution",
            message="Run a simulation first",
        )

    scenario_columns = [column_name for column_name in results_df.columns if column_name.startswith("Scenario_")]
    if not scenario_columns or any(results_df.schema.get(column_name) == pl.Boolean for column_name in scenario_columns):
        return create_empty_figure(
            title="Terminal Value Distribution",
            message="Run a simulation first",
        )

    terminal_values = results_df.tail(1).select(scenario_columns).to_numpy().flatten()

    figure = go.Figure()
    figure.add_trace(
        go.Histogram(
            x=terminal_values,
            nbinsx=50,
            marker_color="rgba(31, 119, 180, 0.7)",
            name="Terminal Values",
            hovertemplate="Value: $%{x:,.2f}<br>Count: %{y}<extra></extra>",
        ),
    )

    mean_value = float(np.mean(terminal_values))
    median_value = float(np.median(terminal_values))
    figure.add_vline(
        x=mean_value,
        line_dash="dash",
        line_color="orange",
        annotation_text=f"Mean: ${mean_value:,.2f}",
    )
    figure.add_vline(
        x=median_value,
        line_dash="solid",
        line_color="blue",
        annotation_text=f"Median: ${median_value:,.2f}",
    )
    figure.update_layout(
        title="Distribution of Terminal Portfolio Values",
        xaxis_title="Portfolio Value ($)",
        yaxis_title="Frequency",
        template="plotly_white",
        height=400,
        showlegend=False,
    )

    plotnine_figure = build_plotnine_simulation_terminal_value_distribution(terminal_values = terminal_values)
    update_visual_object_in_reactives(
        reactives_shiny = reactives_shiny,
        chart_key = "Chart_Simulation_Terminal_Value_Distribution",
        figure = plotnine_figure,
    )
    return figure


def build_compare_progress_ui_for_simulation(
    *,
    do_compare_enabled: bool,
    progress_state: dict[str, Any],
) -> ui.TagChild:
    """Build the Compare progress card UI for the Simulation subtab."""
    if not do_compare_enabled:
        return ui.div()

    status = str(progress_state.get("status", "idle"))
    total_types = _coerce_progress_int_or_default(
        raw_value = progress_state.get("total_types"),
        default_value = len(COMPUTATION_TYPES_SIMULATION_COMPARE),
    )
    current_index = _coerce_progress_int_or_default(
        raw_value = progress_state.get("current_index"),
        default_value = 0,
    )
    current_type = str(progress_state.get("current_type", ""))

    if status == "idle":
        return ui.div(
            ui.p(
                'Enable the toggle above and click "Run Compute & Compare" '
                "to benchmark all 5 backends.",
                class_="text-muted small",
            ),
        )

    if status == "failed":
        return ui.div(
            ui.div(
                ui.h6("Compute & Compare - Failed", class_="text-danger mb-2"),
                ui.p(
                    "The compare run failed before producing results. "
                    "Check application logs for details.",
                    class_="text-danger small mb-0",
                ),
                class_="sim-compare-card-failed",
            ),
        )

    if status == "done":
        completed_entries = progress_state.get("completed", [])
        num_failed = sum(
            1
            for entry in completed_entries
            if isinstance(entry, dict) and not bool(entry.get("ok"))
        )
        done_message = (
            f"All {total_types} backends completed successfully."
            if num_failed == 0
            else f"Completed - {total_types - num_failed}/{total_types} backends succeeded."
        )
        done_class = "text-success fw-semibold" if num_failed == 0 else "text-warning fw-semibold"

        pills: list[ui.Tag] = []
        for entry in completed_entries:
            if not isinstance(entry, dict):
                continue
            backend_type = str(entry.get("type", ""))
            backend_ok = bool(entry.get("ok", False))
            backend_elapsed = _coerce_progress_float_or_default(raw_value = entry.get("elapsed"), default_value = 0.0)
            pill_class = "sim-pill-success" if backend_ok else "sim-pill-error"
            pill_label = "OK" if backend_ok else "FAILED"
            elapsed_label = f"{backend_elapsed:.3f}s" if backend_ok else "-"
            pills.append(
                ui.div(
                    ui.span(backend_type, style="flex:1;"),
                    ui.span(pill_label, class_=f"sim-backend-pill {pill_class}"),
                    ui.span(
                        elapsed_label,
                        class_="ms-2 text-muted",
                        style="min-width:55px;text-align:right;font-size:0.82em;",
                    ),
                    class_="sim-backend-row",
                ),
            )

        return ui.div(
            ui.div(
                ui.h6(done_message, class_=f"{done_class} mb-2"),
                ui.div(
                    ui.div(
                        ui.div(
                            class_="sim-compare-progress-bar-fill sim-compare-progress-bar-fill-done",
                            style="width:100%;",
                        ),
                        ui.div("100%", class_="sim-compare-progress-bar-text"),
                        class_="sim-compare-progress-bar-wrap",
                    ),
                ),
                *pills,
                class_="sim-compare-card-done",
            ),
        )

    current_backend_number, percent_complete = _resolve_compare_progress_running_display(
        current_index = current_index,
        total_types = total_types,
    )
    running_pills: list[ui.Tag] = []
    for idx_backend, backend_type in enumerate(COMPUTATION_TYPES_SIMULATION_COMPARE):
        pill_class, pill_label = _resolve_compare_progress_running_pill(idx_backend = idx_backend, current_index = current_index)
        running_pills.append(
            ui.div(
                ui.span(backend_type, style="flex:1;"),
                ui.span(pill_label, class_=f"sim-backend-pill {pill_class}"),
                class_="sim-backend-row",
            ),
        )

    return ui.div(
        ui.div(
            ui.h6(
                f"Running backend {current_backend_number}/{total_types}: {current_type or '...'} ...",
                class_="mb-1 text-info",
            ),
            ui.div(
                ui.div(
                    class_="sim-compare-progress-bar-fill",
                    style=f"width:{percent_complete}%;",
                ),
                ui.div(f"{percent_complete}%", class_="sim-compare-progress-bar-text"),
                class_="sim-compare-progress-bar-wrap",
            ),
            *running_pills,
            class_="sim-compare-card",
        ),
    )


def build_compare_table_ui_for_simulation(
    *,
    compare_results_payload: dict[str, dict[str, Any]] | None,
    do_compare_enabled: bool,
    progress_state: dict[str, Any],
) -> ui.TagChild:
    """Build the Compare results table UI for the Simulation subtab."""
    if not do_compare_enabled:
        return ui.div()

    if compare_results_payload is None:
        status = str(progress_state.get("status", "idle"))
        if status == "running":
            total_types = _coerce_progress_int_or_default(
                raw_value = progress_state.get("total_types"),
                default_value = len(COMPUTATION_TYPES_SIMULATION_COMPARE),
            )
            current_index = _coerce_progress_int_or_default(
                raw_value = progress_state.get("current_index"),
                default_value = 0,
            )
            current_type = str(progress_state.get("current_type", ""))
            current_backend_number, _ = _resolve_compare_progress_running_display(
                current_index = current_index,
                total_types = total_types,
            )
            return ui.div(
                ui.p(
                    "Comparison results are not ready yet.",
                    f"Running backend {current_backend_number}/{total_types}: {current_type or '...'} ...",
                ),
            )

        return ui.div(
            ui.p(
                "No comparison results yet. Click Run with the toggle enabled.",
            ),
        )

    table_df = build_compare_summary_table(compare_results = compare_results_payload)
    return format_compare_table_as_html(table_df = table_df)


def build_stats_table_ui_for_simulation(
    *,
    results_df: pl.DataFrame | None,
    stats_df: pl.DataFrame | None,
) -> ui.TagChild:
    """Build the summary statistics table UI for the Simulation subtab.

    Boolean scenario columns are treated as invalid simulation results and keep
    the helper on the existing empty-message path.
    """
    if stats_df is None or results_df is None:
        return ui.div(
            ui.p(
                "Run a simulation to see statistics.",
                class_="text-muted text-center p-3",
            ),
        )

    scenario_columns = [column_name for column_name in results_df.columns if column_name.startswith("Scenario_")]
    if not scenario_columns or any(results_df.schema.get(column_name) == pl.Boolean for column_name in scenario_columns):
        return ui.div(
            ui.p(
                "Run a simulation to see statistics.",
                class_="text-muted text-center p-3",
            ),
        )

    terminal_values = results_df.tail(1).select(scenario_columns).to_numpy().flatten()
    initial_value = float(results_df.select(scenario_columns[0]).to_series()[0])
    rows: list[dict[str, str]] = [
        {"Metric": "Number of Scenarios", "Value": f"{len(scenario_columns):,}"},
        {"Metric": "Simulation Horizon", "Value": f"{results_df.height} days"},
        {"Metric": "Initial Value", "Value": f"${initial_value:,.2f}"},
        {"Metric": "Mean Terminal Value", "Value": f"${np.mean(terminal_values):,.2f}"},
        {"Metric": "Median Terminal Value", "Value": f"${np.median(terminal_values):,.2f}"},
        {"Metric": "Std Dev", "Value": f"${np.std(terminal_values, ddof=1):,.2f}"},
        {"Metric": "5th Percentile", "Value": f"${np.percentile(terminal_values, 5):,.2f}"},
        {"Metric": "25th Percentile", "Value": f"${np.percentile(terminal_values, 25):,.2f}"},
        {"Metric": "75th Percentile", "Value": f"${np.percentile(terminal_values, 75):,.2f}"},
        {"Metric": "95th Percentile", "Value": f"${np.percentile(terminal_values, 95):,.2f}"},
        {"Metric": "Minimum", "Value": f"${np.min(terminal_values):,.2f}"},
        {"Metric": "Maximum", "Value": f"${np.max(terminal_values):,.2f}"},
        {
            "Metric": "Prob(Loss)",
            "Value": f"{np.mean(terminal_values < initial_value) * 100:.1f}%",
        },
    ]
    header_html = "<thead><tr><th>Metric</th><th>Value</th></tr></thead>"
    body_rows = "".join(
        f"<tr><td>{row_dict['Metric']}</td><td class='text-end'>{row_dict['Value']}</td></tr>"
        for row_dict in rows
    )
    table_html = (
        '<table class="table table-striped table-hover table-sm">'
        f"{header_html}<tbody>{body_rows}</tbody></table>"
    )
    return ui.HTML(table_html)
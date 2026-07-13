"""Rendering helpers for the portfolio weights analysis subtab."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import polars as pl
from shiny import reactive, render, ui
from shinywidgets import render_widget

from src.dashboard.reporting.report_plot_export import (
    build_plotnine_weights_analysis_current_composition,
    build_plotnine_weights_analysis_distribution_over_time,
)
from src.dashboard.shiny_tab_portfolios._subtab_weights_analysis_data import (
    DEFAULT_SELECTED_COMPONENT_COUNT,
    build_report_weights_statistics_payload,
    build_weights_calculated_date_range_text,
    build_weights_statistics_rows,
    filter_weights_frame_by_date,
    filter_weights_frame_by_selected_ETF_components,
    resolve_available_ETF_components,
    resolve_max_points_from_data_utils,
    resolve_selected_ETF_components,
    resolve_weights_analysis_date_range,
)
from src.dashboard.shiny_utils.reactives_shiny import update_visual_object_in_reactives
from src.dashboard.shiny_utils.utils_reporting import save_weights_analysis_outputs_to_reactives
from src.dashboard.shiny_utils.utils_visuals import create_error_figure
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name = __name__)


def build_component_checkboxes_ui(
    *, available_components: list[str], default_selected_count: int = DEFAULT_SELECTED_COMPONENT_COUNT, select_all: bool = False) -> Any:
    """Build the dynamic ETF component checkbox container."""
    if not available_components:
        return ui.div(
            ui.p("No ETF components available", class_="text-muted"),
            class_="p-2",
        )

    effective_count = len(available_components) if select_all else default_selected_count
    checkbox_nodes = []
    for idx_component, component_name in enumerate(available_components):
        checkbox_id = (
            f"input_ID_tab_portfolios_subtab_weights_analysis_component_{component_name}"
        )
        checkbox_nodes.append(
            ui.div(
                ui.input_checkbox(
                    checkbox_id,
                    component_name,
                    value=idx_component < effective_count,
                ),
                class_="mb-1",
            ),
        )

    return ui.div(*checkbox_nodes)


def build_selected_components_count_text(
    *, available_components: list[str], selected_components: list[str]) -> str:
    """Build the selected-components counter text."""
    return (
        f"Selected: {len(selected_components)} of {len(available_components)} components"
    )


def build_weights_loading_status_ui(
    *, selected_row_count: int, selected_component_count: int) -> Any:
    """Build the status alert shown above the main visualization."""
    if selected_row_count == 0 or selected_component_count == 0:
        status_class = "alert-warning"
        status_icon = "⚠️"
        status_message = "No data available for the current time period and component selection"
    else:
        status_class = "alert-success"
        status_icon = "✅"
        status_message = (
            f"Ready for analysis with {selected_row_count} points across "
            f"{selected_component_count} components"
        )

    return ui.div(
        ui.div(
            ui.span(status_icon, class_="me-2"),
            status_message,
            class_=f"alert {status_class} mb-3 py-2",
        ),
    )


def build_weights_data_info_ui(
    *, weights_frame_original: pl.DataFrame, weights_frame_filtered: pl.DataFrame, weights_frame_selected: pl.DataFrame, available_components: list[str], selected_components: list[str]) -> Any:
    """Build the informational sidebar panel for weights analysis."""
    info_items = []

    if not weights_frame_original.is_empty():
        date_min = weights_frame_original.get_column("Date").min()
        date_max = weights_frame_original.get_column("Date").max()
        info_items.append(ui.p(f"📊 Total Data Points: {weights_frame_original.height}", class_="mb-1"))
        info_items.append(
            ui.p(
                f"📅 Full Date Range: {date_min} to {date_max}",
                class_="mb-1 small text-muted",
            ),
        )
    else:
        info_items.append(ui.p("❌ No weight data available", class_="mb-1 text-danger"))

    if not weights_frame_filtered.is_empty():
        info_items.append(ui.p(f"🔍 Filtered Points: {weights_frame_filtered.height}", class_="mb-1"))
    else:
        info_items.append(
            ui.p("⚠️ No data in selected date range", class_="mb-1 text-warning"),
        )

    info_items.append(
        ui.p(
            f"🎯 Selected Components: {len(selected_components)} of {len(available_components)}",
            class_="mb-1",
        ),
    )

    if not weights_frame_selected.is_empty():
        info_items.append(
            ui.p(
                f"✅ Ready for Analysis: {weights_frame_selected.height} data points",
                class_="mb-0 text-success fw-bold",
            ),
        )
    else:
        info_items.append(
            ui.p(
                "⚠️ No data available for current selection",
                class_="mb-0 text-warning fw-bold",
            ),
        )

    return ui.div(*info_items, class_="p-3 bg-light rounded")


def _build_display_weights_frame(
    *, weights_frame: pl.DataFrame, show_percentage: bool, sort_components: bool) -> tuple[pl.DataFrame, list[str]]:
    """Prepare the selected weights frame for chart rendering."""
    component_columns = resolve_available_ETF_components(weights_frame = weights_frame)
    if not component_columns:
        return weights_frame, []

    display_frame = weights_frame.clone()

    if show_percentage:
        row_total_expression = pl.sum_horizontal([pl.col(component_name) for component_name in component_columns])
        display_frame = display_frame.with_columns(
            [
                pl.when(row_total_expression > 0)
                .then(pl.col(component_name) / row_total_expression * 100.0)
                .otherwise(0.0)
                .alias(component_name)
                for component_name in component_columns
            ],
        )

    if sort_components:
        component_columns = sorted(
            component_columns,
            key=lambda component_name: float(display_frame.get_column(component_name).mean()),
            reverse=True,
        )

    return display_frame, component_columns


def _configure_plot_layout(
    *, figure_plot: go.Figure, title_text: str, yaxis_title: str) -> go.Figure:
    """Apply the shared Plotly layout for weights-analysis charts."""
    figure_plot.update_layout(
        title=title_text,
        xaxis_title="Date",
        yaxis_title=yaxis_title,
        hovermode="x unified",
        legend={
            "orientation": "v",
            "yanchor": "top",
            "y": 1,
            "xanchor": "left",
            "x": 1.02,
        },
        height=550,
        margin={"l": 50, "r": 50, "t": 60, "b": 50},
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    figure_plot.update_xaxes(rangeslider_visible=True)
    return figure_plot


def build_weights_main_figure(
    *, weights_frame_selected: pl.DataFrame, viz_type: str, show_percentage: bool, sort_components: bool, reactives_shiny: dict[str, Any]) -> go.Figure:
    """Build the main weights-analysis visualization."""
    if weights_frame_selected.is_empty():
        return create_error_figure(
            message_text = "No Data Available",
            title_text = "Please select a time period with available data and at least one ETF component.",
        )

    display_frame, component_columns = _build_display_weights_frame(
        weights_frame = weights_frame_selected,
        show_percentage=show_percentage,
        sort_components=sort_components,
    )
    if not component_columns:
        return create_error_figure(
            message_text = "No Components Selected",
            title_text = "Please select at least one ETF component.",
        )

    dates_list = display_frame.get_column("Date").to_list()
    figure_plot = go.Figure()

    if viz_type == "bar":
        for component_name in component_columns:
            figure_plot.add_trace(
                go.Bar(
                    x=dates_list,
                    y=display_frame.get_column(component_name).to_list(),
                    name=component_name,
                    hovertemplate=(
                        f"<b>{component_name}</b><br>Date: %{{x}}<br>"
                        f"Weight: %{{y:.2f}}{'%' if show_percentage else ''}<extra></extra>"
                    ),
                ),
            )
        figure_plot.update_layout(barmode="stack")
        title_text = "Portfolio Weight Distribution Over Time"
    elif viz_type == "heatmap":
        z_values = [
            display_frame.get_column(component_name).to_list()
            for component_name in component_columns
        ]
        figure_plot.add_trace(
            go.Heatmap(
                x=dates_list,
                y=component_columns,
                z=z_values,
                colorbar={"title": "Weight (%)" if show_percentage else "Weight"},
                hovertemplate="<b>%{y}</b><br>Date: %{x}<br>Weight: %{z:.2f}<extra></extra>",
            ),
        )
        title_text = "Portfolio Weight Heatmap"
    elif viz_type == "line":
        for component_name in component_columns:
            figure_plot.add_trace(
                go.Scatter(
                    x=dates_list,
                    y=display_frame.get_column(component_name).to_list(),
                    name=component_name,
                    mode="lines+markers",
                    hovertemplate=(
                        f"<b>{component_name}</b><br>Date: %{{x}}<br>"
                        f"Weight: %{{y:.2f}}{'%' if show_percentage else ''}<extra></extra>"
                    ),
                ),
            )
        title_text = "Individual Component Weight Trends"
    else:
        for component_name in component_columns:
            figure_plot.add_trace(
                go.Scatter(
                    x=dates_list,
                    y=display_frame.get_column(component_name).to_list(),
                    name=component_name,
                    mode="lines",
                    stackgroup="one",
                    hovertemplate=(
                        f"<b>{component_name}</b><br>Date: %{{x}}<br>"
                        f"Weight: %{{y:.2f}}{'%' if show_percentage else ''}<extra></extra>"
                    ),
                ),
            )
        title_text = "Portfolio Weight Distribution Over Time"

    plotnine_figure = build_plotnine_weights_analysis_distribution_over_time(
        weights_df = display_frame,
    )
    update_visual_object_in_reactives(
        reactives_shiny = reactives_shiny,
        chart_key = "Chart_Weights_Analysis_Portfolio_Weight_Distribution_Over_Time",
        figure = plotnine_figure,
    )

    return _configure_plot_layout(
        figure_plot = figure_plot,
        title_text=title_text,
        yaxis_title="Weight (%)" if show_percentage else "Weight",
    )


def build_weights_secondary_figure(
    *, weights_frame_selected: pl.DataFrame, reactives_shiny: dict[str, Any]) -> go.Figure:
    """Build the current-composition pie chart."""
    if weights_frame_selected.is_empty():
        return create_error_figure(
            message_text = "No Data Available",
            title_text = "Please select components to view current composition.",
        )

    component_columns = resolve_available_ETF_components(weights_frame = weights_frame_selected)
    if not component_columns:
        return create_error_figure(
            message_text = "No Components Selected",
            title_text = "Please select at least one ETF component.",
        )

    latest_row = weights_frame_selected.tail(1).to_dicts()[0]
    labels_list = component_columns
    values_list = [float(latest_row[component_name]) for component_name in component_columns]
    latest_date = latest_row["Date"]
    latest_date_text = (
        latest_date.strftime("%Y-%m-%d") if hasattr(latest_date, "strftime") else str(latest_date)
    )

    figure_plot = go.Figure(
        data=[
            go.Pie(
                labels=labels_list,
                values=values_list,
                hovertemplate="<b>%{label}</b><br>Weight: %{value:.2f}<br>Percentage: %{percent}<extra></extra>",
            ),
        ],
    )
    figure_plot.update_layout(
        title=f"Current Composition as of {latest_date_text}",
        showlegend=True,
    )

    plotnine_figure = build_plotnine_weights_analysis_current_composition(
        labels = labels_list,
        values = values_list,
    )
    update_visual_object_in_reactives(
        reactives_shiny = reactives_shiny,
        chart_key = "Chart_Weights_Analysis_Portfolio_Current_Composition",
        figure = plotnine_figure,
    )

    return figure_plot


def build_weights_summary_table_ui(
    *, weights_frame_selected: pl.DataFrame, reactives_shiny: dict[str, Any]) -> Any:
    """Build the HTML summary table for selected ETF weights."""
    statistics_rows = build_weights_statistics_rows(weights_frame = weights_frame_selected)
    if not statistics_rows:
        return ui.div(
            ui.p(
                "No data available for statistics calculation.",
                class_="text-muted text-center p-3",
            ),
        )

    report_payload = build_report_weights_statistics_payload(statistics_rows = statistics_rows)
    try:
        save_weights_analysis_outputs_to_reactives(
            reactives_shiny = reactives_shiny,
            data_value = {"weight_statistics": report_payload},
        )
    except Exception as exc_save:  # pragma: no cover
        _logger.debug("save_weights_analysis_outputs_to_reactives failed: %s", exc_save)

    stats_dataframe = pd.DataFrame(statistics_rows)  # pandas-boundary
    html_table = stats_dataframe.to_html(
        index=False,
        classes="table table-striped table-hover table-sm",
        float_format=lambda value_float: f"{value_float:.2f}",
    )
    return ui.HTML(html_table)


def register_weights_analysis_outputs(
    *,
    input: Any,
    output: Any,
    data_utils: dict[str, Any],
    weights_frame: pl.DataFrame,
    reactives_shiny: dict[str, Any],
) -> None:
    """Register the reactive outputs for the weights-analysis subtab."""
    max_points = resolve_max_points_from_data_utils(data_utils = data_utils)

    @reactive.calc
    def get_weights_frame() -> pl.DataFrame:
        return weights_frame

    @reactive.calc
    def get_effective_weights_date_range() -> tuple[datetime, datetime]:
        try:
            selected_period = input.input_ID_tab_portfolios_subtab_weights_analysis_time_period()
        except Exception:
            selected_period = "5y"

        try:
            custom_date_range = input.input_ID_tab_portfolios_subtab_weights_analysis_date_range()
        except Exception:
            custom_date_range = None

        return resolve_weights_analysis_date_range(
            time_period = selected_period,
            weights_frame = get_weights_frame(),
            custom_date_range=custom_date_range,
        )

    @reactive.calc
    def get_filtered_weights_frame() -> pl.DataFrame:
        start_datetime, end_datetime = get_effective_weights_date_range()
        return filter_weights_frame_by_date(
            weights_frame = get_weights_frame(),
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            max_points=max_points,
        )

    @reactive.calc
    def get_available_ETF_components() -> list[str]:
        return resolve_available_ETF_components(weights_frame = get_weights_frame())

    @reactive.calc
    def get_selected_ETF_components() -> list[str]:
        available_components = get_available_ETF_components()
        if not available_components:
            return []

        checkbox_values_by_component: dict[str, bool] = {}
        for component_name in available_components:
            checkbox_id = (
                f"input_ID_tab_portfolios_subtab_weights_analysis_component_{component_name}"
            )
            try:
                checkbox_values_by_component[component_name] = bool(input[checkbox_id]())
            except Exception:
                continue

        try:
            select_all_components = bool(
                input.input_ID_tab_portfolios_subtab_weights_analysis_select_all_components(),
            )
        except Exception:
            select_all_components = None

        return resolve_selected_ETF_components(
            available_components = available_components,
            select_all_components=select_all_components,
            checkbox_values_by_component=checkbox_values_by_component,
        )

    @reactive.calc
    def get_filtered_weights_frame_with_selected_components() -> pl.DataFrame:
        return filter_weights_frame_by_selected_ETF_components(
            weights_frame = get_filtered_weights_frame(),
            selected_components = get_selected_ETF_components(),
        )

    @output
    @render.ui
    def output_ID_tab_portfolios_subtab_weights_analysis_component_checkboxes():
        try:
            select_all = bool(
                input.input_ID_tab_portfolios_subtab_weights_analysis_select_all_components(),
            )
        except Exception:
            select_all = False
        return build_component_checkboxes_ui(
            available_components = get_available_ETF_components(),
            select_all=select_all,
        )

    @output
    @render.text
    def output_ID_tab_portfolios_subtab_weights_analysis_selected_components_count() -> str:
        return build_selected_components_count_text(
            available_components = get_available_ETF_components(),
            selected_components = get_selected_ETF_components(),
        )

    @output
    @render.text
    def output_ID_tab_portfolios_subtab_weights_analysis_calculated_date_range() -> str:
        start_datetime, end_datetime = get_effective_weights_date_range()
        return build_weights_calculated_date_range_text(start_datetime = start_datetime, end_datetime = end_datetime)

    @output
    @render.ui
    def output_ID_tab_portfolios_subtab_weights_analysis_loading_status():
        weights_selected = get_filtered_weights_frame_with_selected_components()
        selected_components = get_selected_ETF_components()
        return build_weights_loading_status_ui(
            selected_row_count = weights_selected.height,
            selected_component_count = len(selected_components),
        )

    @output
    @render.ui
    def output_ID_tab_portfolios_subtab_weights_analysis_data_info():
        return build_weights_data_info_ui(
            weights_frame_original = get_weights_frame(),
            weights_frame_filtered = get_filtered_weights_frame(),
            weights_frame_selected = get_filtered_weights_frame_with_selected_components(),
            available_components = get_available_ETF_components(),
            selected_components = get_selected_ETF_components(),
        )

    @output
    @render_widget  # pyright: ignore[reportArgumentType]  # pyrefly: ignore[bad-specialization]
    def output_ID_tab_portfolios_subtab_weights_analysis_plot_main():
        try:
            viz_type = input.input_ID_tab_portfolios_subtab_weights_analysis_viz_type()
        except Exception:
            viz_type = "area"

        try:
            show_percentage = bool(
                input.input_ID_tab_portfolios_subtab_weights_analysis_show_pct(),
            )
        except Exception:
            show_percentage = True

        try:
            sort_components = bool(
                input.input_ID_tab_portfolios_subtab_weights_analysis_sort_components(),
            )
        except Exception:
            sort_components = True

        return build_weights_main_figure(
            weights_frame_selected = get_filtered_weights_frame_with_selected_components(),
            viz_type=viz_type,
            show_percentage=show_percentage,
            sort_components=sort_components,
            reactives_shiny=reactives_shiny,
        )

    @output
    @render_widget  # pyright: ignore[reportArgumentType]  # pyrefly: ignore[bad-specialization]
    def output_ID_tab_portfolios_subtab_weights_analysis_plot_secondary():
        return build_weights_secondary_figure(
            weights_frame_selected = get_filtered_weights_frame_with_selected_components(),
            reactives_shiny=reactives_shiny,
        )

    @output
    @render.ui
    def output_ID_tab_portfolios_subtab_weights_analysis_table_summary():
        return build_weights_summary_table_ui(
            weights_frame_selected = get_filtered_weights_frame_with_selected_components(),
            reactives_shiny=reactives_shiny,
        )
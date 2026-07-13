"""Rendering helpers for the portfolio analysis subtab."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pandas as pd
import polars as pl
from shiny import reactive, render, ui
from shinywidgets import render_widget

from src.dashboard.reporting.report_plot_export import (
    build_plotnine_portfolio_analysis_returns_distribution,
)
from src.dashboard.shiny_tab_portfolios._subtab_portfolios_analysis_data import (
    build_calculated_date_range_text,
    build_filtered_analysis_data,
)
from src.dashboard.shiny_utils.reactives_shiny import update_visual_object_in_reactives
from src.dashboard.shiny_utils.utils_visuals import (
    calculate_table_metrics_performance,
    calculate_table_stats_basic,
    create_error_figure,
    create_plot_drawdowns_analysis,
    create_plot_portfolios_comparison,
    create_plot_returns_distribution,
    create_plot_rolling_statistics,
    format_value_for_display,
)
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Configuration,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name = __name__)

ANALYSIS_LABELS: dict[str, str] = {
    "returns": "Returns Distribution",
    "drawdowns": "Drawdowns Analysis",
    "rolling": "Rolling Statistics",
    "comparison": "Portfolio vs Benchmark",
}

PERIOD_LABELS: dict[str, str] = {
    "1y": "Last 1 Year",
    "3y": "Last 3 Years",
    "5y": "Last 5 Years",
    "10y": "Last 10 Years",
    "ytd": "Year to Date",
    "custom": "Custom Period",
}


def resolve_analysis_label(*, analysis_type: str | None) -> str:
    """Return the label used across the analysis subtab UI."""
    return ANALYSIS_LABELS.get(analysis_type or "", "Analysis")


def resolve_period_label(*, time_period: str | None) -> str:
    """Return the label used across the period selector UI."""
    return PERIOD_LABELS.get(time_period or "", "Selected Period")


def build_analysis_data_info_ui(
    *,
    time_period: str | None,
    analysis_type: str | None,
    portfolio_count: int,
    benchmark_count: int,
) -> Any:
    """Build the sidebar information block for the current analysis selection."""
    if portfolio_count > 0:
        if portfolio_count >= 30:
            status_icon = "✅"
            status_text = "Ready for analysis"
            status_class = "text-success"
        else:
            status_icon = "⚠️"
            status_text = "Limited data available"
            status_class = "text-warning"
    else:
        status_icon = "❌"
        status_text = "No portfolio data"
        status_class = "text-danger"

    return ui.div(
        ui.div(
            ui.strong("Period: "),
            resolve_period_label(time_period = time_period),
            class_="small text-muted mb-1",
        ),
        ui.div(
            ui.strong("Analysis: "),
            resolve_analysis_label(analysis_type = analysis_type),
            class_="small text-muted mb-1",
        ),
        ui.div(
            ui.strong("Portfolio Data: "),
            f"{portfolio_count} points" if portfolio_count > 0 else "No data",
            class_="small text-muted mb-1",
        ),
        ui.div(
            ui.strong("Benchmark Data: "),
            f"{benchmark_count} points" if benchmark_count > 0 else "No data",
            class_="small text-muted mb-1",
        ),
        ui.div(
            ui.span(status_icon, class_="me-1"),
            ui.span(status_text, class_=f"small {status_class}"),
            class_="mt-2 p-2 rounded bg-light",
        ),
    )


def build_loading_status_ui(*, portfolio_count: int, analysis_type: str | None) -> Any:
    """Build the alert shown above the main analysis plot."""
    if portfolio_count == 0:
        status_class = "alert-danger"
        status_icon = "❌"
        status_message = "No portfolio data available for the selected period"
    elif portfolio_count < 30:
        status_class = "alert-warning"
        status_icon = "⚠️"
        status_message = (
            f"Limited data available ({portfolio_count} points) - "
            "Analysis may be less accurate"
        )
    else:
        status_class = "alert-success"
        status_icon = "✅"
        status_message = (
            f"Ready for {resolve_analysis_label(analysis_type = analysis_type)} "
            f"({portfolio_count} data points)"
        )

    return ui.div(
        ui.div(
            ui.span(status_icon, class_="me-2"),
            status_message,
            class_=f"alert {status_class} mb-3 py-2",
        ),
    )


def _resolve_benchmark_data(
    *, data_benchmark_filtered: pl.DataFrame, include_benchmark: bool) -> pl.DataFrame | None:
    """Return benchmark data only when the selection and data both allow it."""
    if include_benchmark and not data_benchmark_filtered.is_empty():
        return data_benchmark_filtered
    return None


def _configure_analysis_figure(*, figure: Any) -> Any:
    """Apply the shared Plotly layout for analysis charts."""
    figure.update_layout(
        height=550,
        margin={"l": 50, "r": 50, "t": 60, "b": 50},
        paper_bgcolor="white",
        plot_bgcolor="white",
        showlegend=True,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
        },
    )
    return figure


def build_analysis_figure(
    *,
    analysis_type: str | None,
    data_portfolio_filtered: pl.DataFrame,
    data_benchmark_filtered: pl.DataFrame,
    include_benchmark: bool,
    rolling_window: int,
    reactives_shiny: dict[str, Any],
) -> Any:
    """Build the main analysis figure and update the shared report snapshot."""
    if data_portfolio_filtered.is_empty():
        return create_error_figure(message_text = "No portfolio data available for the selected time period")

    benchmark_data = _resolve_benchmark_data(
        data_benchmark_filtered = data_benchmark_filtered,
        include_benchmark=include_benchmark,
    )

    if analysis_type == "drawdowns":
        figure = create_plot_drawdowns_analysis(
            data_portfolio=data_portfolio_filtered,
            data_benchmark=benchmark_data,
            period_label="Drawdowns Analysis",
            data_was_validated=True,
            include_benchmark=include_benchmark,
        )
    elif analysis_type == "rolling":
        figure = create_plot_rolling_statistics(
            data_portfolio=data_portfolio_filtered,
            data_benchmark=benchmark_data,
            window_size=rolling_window,
            period_label=f"Rolling Statistics ({rolling_window}-day window)",
            data_was_validated=True,
            include_benchmark=include_benchmark,
        )
    elif analysis_type == "comparison":
        figure = create_plot_portfolios_comparison(
            data_portfolio=data_portfolio_filtered,
            data_benchmark=benchmark_data,
            period_label="Portfolio vs Benchmark Comparison",
            data_was_validated=True,
        )
    else:
        figure = create_plot_returns_distribution(
            data_portfolio=data_portfolio_filtered,
            data_benchmark=benchmark_data,
            period_label="Returns Distribution Analysis",
            data_was_validated=True,
            include_benchmark=include_benchmark,
        )

    if figure is None:
        return create_error_figure(message_text = "Failed to generate analysis plot")

    plotnine_figure = build_plotnine_portfolio_analysis_returns_distribution(
        portfolio_df = data_portfolio_filtered,
        benchmark_df = benchmark_data,
    )
    update_visual_object_in_reactives(
        reactives_shiny = reactives_shiny,
        chart_key = "Chart_Portfolio_Analysis_Returns_Distribution",
        figure = plotnine_figure,
    )

    return _configure_analysis_figure(figure = figure)


def build_fallback_table(
    *,
    label_column: str,
    label_value: str,
    portfolio_value: str = "-",
    include_benchmark: bool = True,
) -> pd.DataFrame:
    """Build a consistent fallback dataframe for table renderers."""
    table_data: dict[str, list[str]] = {
        label_column: [label_value],
        "Portfolio": [portfolio_value],
    }
    if include_benchmark:
        table_data["Benchmark"] = ["-"]
    return pd.DataFrame(table_data)


def _metric_format_type(*, metric_name: str) -> str:
    """Return the display format for a metrics table label."""
    if any(term in metric_name for term in ["return", "yield", "ratio", "volatility"]):
        return "percentage"
    if "drawdown" in metric_name:
        return "percentage"
    if "days" in metric_name or "count" in metric_name:
        return "integer"
    return "decimal"


def _statistic_format_type(*, metric_name: str) -> str:
    """Return the display format for a statistics table label."""
    if any(
        term in metric_name
        for term in ["mean", "median", "std", "variance", "volatility"]
    ):
        return "decimal"
    if any(term in metric_name for term in ["min", "max", "percentile", "quantile"]):
        return "decimal"
    if any(term in metric_name for term in ["count", "observations", "points"]):
        return "integer"
    if any(term in metric_name for term in ["skew", "kurtosis"]):
        return "decimal"
    return "decimal"


def _format_table_values(
    *, table: pd.DataFrame, label_column: str, value_columns: tuple[str, ...], format_selector: Callable[[str], str]) -> pd.DataFrame:
    """Format numeric dataframe values according to the associated row labels."""
    formatted_table = table.copy()

    for value_column in value_columns:
        if value_column not in formatted_table.columns:
            continue

        # Cast to object dtype before assigning formatted string values to
        # avoid pandas FutureWarning about incompatible dtype assignment.
        if formatted_table[value_column].dtype != object:
            formatted_table[value_column] = formatted_table[value_column].astype(object)

        for row_index in formatted_table.index:
            value = formatted_table.at[row_index, value_column]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or pd.isna(value):
                continue

            row_label = str(formatted_table.at[row_index, label_column]).lower()
            format_type = format_selector(metric_name=row_label)
            value_for_display = int(float(value)) if format_type == "integer" else value
            try:
                formatted_table.at[row_index, value_column] = format_value_for_display(
                    value_input = value_for_display,
                    format_type=format_type,
                )
            except (AttributeError, TypeError, ValueError) as exc:
                _logger.debug(
                    "%s formatting failed, keeping original: %s",
                    value_column,
                    exc,
                )

    return formatted_table


def format_metrics_table_for_display(*, metrics_table: pd.DataFrame) -> pd.DataFrame:
    """Format the metrics dataframe returned by the visualization utilities."""
    return _format_table_values(
        table = metrics_table,
        label_column="Metric",
        value_columns=("Portfolio", "Benchmark"),
        format_selector=_metric_format_type,
    )


def format_stats_table_for_display(*, stats_table: pd.DataFrame) -> pd.DataFrame:
    """Format the basic statistics dataframe returned by the visualization utilities."""
    return _format_table_values(
        table = stats_table,
        label_column="Statistic",
        value_columns=("Portfolio", "Benchmark"),
        format_selector=_statistic_format_type,
    )


def build_metrics_table(
    *,
    data_portfolio_filtered: pl.DataFrame,
    data_benchmark_filtered: pl.DataFrame,
    include_benchmark: bool,
) -> pd.DataFrame:
    """Build the quantstats-style metrics table for the active analysis slice."""
    if data_portfolio_filtered.is_empty():
        return build_fallback_table(
            label_column="Metric",
            label_value="No Data Available",
            include_benchmark=include_benchmark,
        )

    benchmark_data = _resolve_benchmark_data(
        data_benchmark_filtered = data_benchmark_filtered,
        include_benchmark=include_benchmark,
    )
    metrics_table = calculate_table_metrics_performance(
        data_portfolio=data_portfolio_filtered,
        data_benchmark=benchmark_data,
    )

    if metrics_table is None or metrics_table.empty:
        return build_fallback_table(
            label_column="Metric",
            label_value="Calculation Error",
            include_benchmark=include_benchmark,
        )

    return format_metrics_table_for_display(metrics_table = metrics_table)


def build_stats_table(
    *,
    data_portfolio_filtered: pl.DataFrame,
    data_benchmark_filtered: pl.DataFrame,
    include_benchmark: bool,
) -> pd.DataFrame:
    """Build the basic statistics table for the active analysis slice."""
    if data_portfolio_filtered.is_empty():
        return build_fallback_table(
            label_column="Statistic",
            label_value="No Data Available",
            include_benchmark=include_benchmark,
        )

    benchmark_data = _resolve_benchmark_data(
        data_benchmark_filtered = data_benchmark_filtered,
        include_benchmark=include_benchmark,
    )
    stats_table = calculate_table_stats_basic(
        data_portfolio=data_portfolio_filtered,
        data_benchmark=benchmark_data,
        include_benchmark=include_benchmark,
    )

    if stats_table is None or stats_table.empty:
        return build_fallback_table(
            label_column="Statistic",
            label_value="Calculation Error",
            include_benchmark=include_benchmark,
        )

    return format_stats_table_for_display(stats_table = stats_table)


def register_portfolios_analysis_outputs(
    *,
    input: Any,
    output: Any,
    data_portfolio: pl.DataFrame | None,
    data_benchmark: pl.DataFrame | None,
    reactives_shiny: dict[str, Any],
) -> None:  # pragma: no cover
    """Register the reactive outputs for the public portfolio analysis server."""

    def _safe_input_value(*, getter: Any, default: Any) -> Any:
        try:
            return getter()
        except Exception:
            return default

    @output
    @render.text
    def output_ID_tab_portfolios_subtab_portfolios_analysis_calculated_date_range() -> str:
        try:
            return build_calculated_date_range_text(
                time_period = _safe_input_value(
                    getter = input.input_ID_tab_portfolios_subtab_portfolios_analysis_time_period,
                    default = "1y",
                ),
            )
        except (AttributeError, TypeError, ValueError) as exc:
            raise Exception_Configuration(
                f"Error displaying calculated date range: {exc}",
            ) from exc

    @reactive.calc
    def get_filtered_analysis_data() -> tuple[pl.DataFrame, pl.DataFrame]:
        return build_filtered_analysis_data(
            data_portfolio=data_portfolio,
            data_benchmark=data_benchmark,
            time_period=_safe_input_value(
                getter = input.input_ID_tab_portfolios_subtab_portfolios_analysis_time_period,
                default = "1y",
            ),
            custom_date_range=_safe_input_value(
                getter = input.input_ID_tab_portfolios_subtab_portfolios_analysis_date_range,
                default = None,
            ),
        )

    @output
    @render.ui
    def output_ID_tab_portfolios_subtab_portfolios_analysis_data_info() -> Any:
        try:
            data_portfolio_filtered, data_benchmark_filtered = get_filtered_analysis_data()
            portfolio_count = (
                data_portfolio_filtered.height if not data_portfolio_filtered.is_empty() else 0
            )
            benchmark_count = (
                data_benchmark_filtered.height if not data_benchmark_filtered.is_empty() else 0
            )

            return build_analysis_data_info_ui(
                time_period=_safe_input_value(
                    getter = input.input_ID_tab_portfolios_subtab_portfolios_analysis_time_period,
                    default = "1y",
                ),
                analysis_type=_safe_input_value(
                    getter = input.input_ID_tab_portfolios_subtab_portfolios_analysis_type,
                    default = "returns",
                ),
                portfolio_count=portfolio_count,
                benchmark_count=benchmark_count,
            )
        except (AttributeError, TypeError, ValueError) as exc:
            raise Exception_Configuration(f"Error generating analysis data info: {exc}") from exc

    @output
    @render.ui
    def output_ID_tab_portfolios_subtab_portfolios_analysis_loading_status() -> Any:
        try:
            data_portfolio_filtered, _data_benchmark_filtered = get_filtered_analysis_data()
            portfolio_count = (
                data_portfolio_filtered.height if not data_portfolio_filtered.is_empty() else 0
            )
            return build_loading_status_ui(
                portfolio_count = portfolio_count,
                analysis_type = _safe_input_value(
                    getter = input.input_ID_tab_portfolios_subtab_portfolios_analysis_type,
                    default = "returns",
                ),
            )
        except Exception:
            return ui.div(
                ui.div("⏳ Loading analysis data...", class_="alert alert-info mb-3 py-2"),
            )

    @output
    @render_widget  # pyright: ignore[reportArgumentType]  # pyrefly: ignore[bad-specialization]
    def output_ID_tab_portfolios_subtab_portfolios_analysis_plot_main() -> Any:
        try:
            data_portfolio_filtered, data_benchmark_filtered = get_filtered_analysis_data()
            return build_analysis_figure(
                analysis_type=_safe_input_value(
                    getter = input.input_ID_tab_portfolios_subtab_portfolios_analysis_type,
                    default = "returns",
                ),
                data_portfolio_filtered=data_portfolio_filtered,
                data_benchmark_filtered=data_benchmark_filtered,
                include_benchmark=_safe_input_value(
                    getter = input.input_ID_tab_portfolios_subtab_portfolios_analysis_include_benchmark,
                    default = True,
                ),
                rolling_window=_safe_input_value(
                    getter = input.input_ID_tab_portfolios_subtab_portfolios_analysis_rolling_window,
                    default = 30,
                ),
                reactives_shiny=reactives_shiny,
            )
        except Exception as exc:
            error_message = f"Error generating analysis plot: {exc!s}"
            _logger.opt(exception=True).error(
                "Plot generation error: {}",
                error_message,
            )
            return create_error_figure(message_text = error_message)

    @output
    @render.table  # pyrefly: ignore[bad-argument-type]
    def output_ID_tab_portfolios_subtab_portfolios_analysis_table_quantstats_metrics() -> pd.DataFrame:
        try:
            data_portfolio_filtered, data_benchmark_filtered = get_filtered_analysis_data()
            include_benchmark = _safe_input_value(
                getter = input.input_ID_tab_portfolios_subtab_portfolios_analysis_include_benchmark,
                default = True,
            )
            return build_metrics_table(
                data_portfolio_filtered=data_portfolio_filtered,
                data_benchmark_filtered=data_benchmark_filtered,
                include_benchmark=include_benchmark,
            )
        except Exception as exc:
            error_message = f"Error generating performance metrics table: {exc!s}"
            _logger.opt(exception=True).error(
                "Metrics table generation error: {}",
                error_message,
            )
            return build_fallback_table(
                label_column="Metric",
                label_value="Error",
                portfolio_value=error_message,
                include_benchmark=True,
            )

    @output
    @render.table  # pyrefly: ignore[bad-argument-type]
    def output_ID_tab_portfolios_subtab_portfolios_analysis_table_stats() -> pd.DataFrame:
        try:
            data_portfolio_filtered, data_benchmark_filtered = get_filtered_analysis_data()
            include_benchmark = _safe_input_value(
                getter = input.input_ID_tab_portfolios_subtab_portfolios_analysis_include_benchmark,
                default = True,
            )
            return build_stats_table(
                data_portfolio_filtered=data_portfolio_filtered,
                data_benchmark_filtered=data_benchmark_filtered,
                include_benchmark=include_benchmark,
            )
        except Exception as exc:
            error_message = f"Error generating basic statistics table: {exc!s}"
            _logger.opt(exception=True).error(
                "Stats table generation error: {}",
                error_message,
            )
            return build_fallback_table(
                label_column="Statistic",
                label_value="Error",
                portfolio_value=error_message,
                include_benchmark=True,
            )
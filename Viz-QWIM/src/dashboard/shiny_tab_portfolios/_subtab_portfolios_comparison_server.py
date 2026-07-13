"""Private server helpers for the Portfolio Comparison subtab."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
import polars as pl

from shiny import reactive, render, ui
from shinywidgets import render_widget

from src.dashboard.reporting.report_plot_export import (
    build_plotnine_portfolio_comparison_portfolio_vs_benchmark,
)
from src.dashboard.shiny_utils.reactives_shiny import update_visual_object_in_reactives
from src.dashboard.shiny_utils.utils_data import validate_portfolio_data
from src.dashboard.shiny_utils.utils_visuals import (
    create_error_figure,
    create_plot_comparison_portfolios,
)
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Configuration,
    Exception_Validation_Input,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name = "src.dashboard.shiny_tab_portfolios.subtab_portfolios_comparison")


_EMPTY_COMPARISON_SCHEMA: dict[str, pl.DataType] = {
    "Date": pl.Datetime,
    "Value": pl.Float64,
}


_TIME_PERIOD_LABELS: dict[str, str] = {
    "1y": "Last 1 Year",
    "3y": "Last 3 Years",
    "5y": "Last 5 Years",
    "10y": "Last 10 Years",
    "ytd": "Year to Date",
    "custom": "Custom Period",
}


def _datetime_now_UTC_naive() -> datetime:
    """Return the current UTC timestamp without timezone information."""
    return datetime.now(UTC).replace(tzinfo=None)


def _create_empty_comparison_frame() -> pl.DataFrame:
    """Return an empty comparison frame with the expected schema."""
    return pl.DataFrame(
        {"Date": [], "Value": []},
        schema=_EMPTY_COMPARISON_SCHEMA,
    )


def _normalize_datetime_bound(
    *, value_datetime: Any, is_end: bool) -> datetime:
    """Normalize date-like values to naive datetime bounds."""
    if isinstance(value_datetime, str):
        value_datetime = pd.Timestamp(value_datetime).to_pydatetime()

    if isinstance(value_datetime, pd.Timestamp):
        value_datetime = value_datetime.to_pydatetime()

    if isinstance(value_datetime, datetime):
        normalized_datetime = (
            value_datetime.astimezone(UTC)
            if value_datetime.tzinfo is not None
            else value_datetime
        )
        normalized_datetime = normalized_datetime.replace(tzinfo=None)
    elif hasattr(value_datetime, "to_pydatetime"):
        return _normalize_datetime_bound(
            value_datetime = value_datetime.to_pydatetime(),
            is_end=is_end,
        )
    elif all(
        hasattr(value_datetime, attribute_name)
        for attribute_name in ("year", "month", "day")
    ):
        normalized_datetime = datetime(
            value_datetime.year,
            value_datetime.month,
            value_datetime.day,
        )
    else:
        normalized_datetime = _datetime_now_UTC_naive()

    if is_end:
        return normalized_datetime.replace(
            hour=23,
            minute=59,
            second=59,
            microsecond=999999,
        )

    return normalized_datetime.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )


def _coerce_date_frame_to_datetime(
    *, data_frame: pl.DataFrame, label_dataset: str) -> pl.DataFrame:
    """Convert the Date column to timezone-naive datetimes."""
    if data_frame.is_empty() or "Date" not in data_frame.columns or "Value" not in data_frame.columns:
        _logger.debug("%s: missing required columns or empty data", label_dataset)
        return _create_empty_comparison_frame()

    date_dtype = data_frame.select("Date").dtypes[0]
    _logger.debug("%s date column type: %s", label_dataset, date_dtype)

    if date_dtype in [pl.Utf8, pl.String]:
        # pandas-boundary: robust timezone normalization for mixed string inputs.
        data_frame_pandas = data_frame.to_pandas()
        data_frame_pandas["Date"] = pd.to_datetime(
            data_frame_pandas["Date"],
            utc=True,
            errors="coerce",
        )
        if isinstance(data_frame_pandas["Date"].dtype, pd.DatetimeTZDtype):
            data_frame_pandas["Date"] = data_frame_pandas["Date"].dt.tz_localize(None)
        return pl.from_pandas(data_frame_pandas)

    if date_dtype == pl.Date:
        return data_frame.clone().with_columns(
            pl.col("Date").cast(pl.Datetime).alias("Date"),
        )

    if date_dtype == pl.Datetime:
        data_frame_datetime = data_frame.clone()
        if getattr(data_frame_datetime["Date"].dtype, "time_zone", None) is not None:
            data_frame_datetime = data_frame_datetime.with_columns(
                pl.col("Date").dt.replace_time_zone(None).alias("Date"),
            )
        return data_frame_datetime

    # pandas-boundary: last-resort normalization for unexpected date types.
    data_frame_pandas = data_frame.to_pandas()
    data_frame_pandas["Date"] = pd.to_datetime(
        data_frame_pandas["Date"],
        utc=True,
        errors="coerce",
    )
    if isinstance(data_frame_pandas["Date"].dtype, pd.DatetimeTZDtype):
        data_frame_pandas["Date"] = data_frame_pandas["Date"].dt.tz_localize(None)
    return pl.from_pandas(data_frame_pandas)


def _resolve_available_date_bounds(
    *, data_frame_portfolio: pl.DataFrame | None) -> tuple[datetime, datetime]:
    """Resolve the available min/max dates from the portfolio input."""
    datetime_end_fallback = _datetime_now_UTC_naive()
    datetime_start_fallback = datetime_end_fallback - timedelta(days=365 * 10)

    if data_frame_portfolio is None:
        return datetime_start_fallback, datetime_end_fallback

    try:
        data_frame_portfolio_normalized = _coerce_date_frame_to_datetime(
            data_frame = data_frame_portfolio,
            label_dataset = "Portfolio",
        )
        if data_frame_portfolio_normalized.is_empty():
            return datetime_start_fallback, datetime_end_fallback

        datetime_min_data = _normalize_datetime_bound(
            value_datetime = data_frame_portfolio_normalized.select(pl.col("Date").min()).item(),
            is_end=False,
        )
        datetime_max_data = _normalize_datetime_bound(
            value_datetime = data_frame_portfolio_normalized.select(pl.col("Date").max()).item(),
            is_end=False,
        )
        return datetime_min_data, datetime_max_data
    except (TypeError, ValueError, AttributeError) as exc:
        _logger.warning("Date bound resolution failed: %s", exc)
        return datetime_start_fallback, datetime_end_fallback


def _calc_effective_date_range_for_comparison(
    *, input: Any, data_frame_portfolio: pl.DataFrame | None) -> tuple[datetime, datetime]:
    """Calculate the effective analysis window from user inputs."""
    try:
        value_time_period = input.input_ID_tab_portfolios_subtab_comparison_time_period()
        datetime_min_data, datetime_max_data = _resolve_available_date_bounds(data_frame_portfolio = data_frame_portfolio)
        _logger.debug(
            "Available comparison date range: %s to %s",
            datetime_min_data.strftime("%Y-%m-%d"),
            datetime_max_data.strftime("%Y-%m-%d"),
        )
        datetime_today = _normalize_datetime_bound(value_datetime = datetime_max_data, is_end=False)

        if value_time_period == "custom":
            try:
                value_date_range = input.input_ID_tab_portfolios_subtab_comparison_date_range()
                if value_date_range and len(value_date_range) == 2:
                    datetime_start = _normalize_datetime_bound(value_datetime = value_date_range[0], is_end=False)
                    datetime_end = _normalize_datetime_bound(value_datetime = value_date_range[1], is_end=True)
                    if datetime_end > datetime_today:
                        _logger.warning(
                            "Custom end date %s exceeds data availability, capping at %s",
                            datetime_end.strftime("%Y-%m-%d"),
                            datetime_today.strftime("%Y-%m-%d"),
                        )
                        datetime_end = datetime_today
                    return datetime_start, datetime_end
            except (TypeError, ValueError, AttributeError) as exc:
                _logger.warning("Custom range error: %s", exc)

            return (
                _normalize_datetime_bound(value_datetime = datetime_today - timedelta(days=365), is_end=False),
                _normalize_datetime_bound(value_datetime = datetime_today, is_end=True),
            )

        if value_time_period == "1y":
            datetime_start = datetime_today - timedelta(days=365)
        elif value_time_period == "3y":
            datetime_start = datetime_today - timedelta(days=365 * 3)
        elif value_time_period == "5y":
            datetime_start = datetime_today - timedelta(days=365 * 5)
        elif value_time_period == "10y":
            datetime_start = datetime_today - timedelta(days=365 * 10)
        elif value_time_period == "ytd":
            datetime_start = datetime(datetime_today.year, 1, 1)
        else:
            datetime_start = datetime_today - timedelta(days=365)

        return (
            _normalize_datetime_bound(value_datetime = datetime_start, is_end=False),
            _normalize_datetime_bound(value_datetime = datetime_today, is_end=True),
        )
    except (TypeError, ValueError, AttributeError) as exc:  # pragma: no cover
        _logger.opt(exception=True).error("Error calculating date range: {}", exc)
        datetime_end_fallback = _normalize_datetime_bound(value_datetime = _datetime_now_UTC_naive(), is_end=True)
        datetime_start_fallback = _normalize_datetime_bound(
            value_datetime = datetime_end_fallback - timedelta(days=365),
            is_end=False,
        )
        return datetime_start_fallback, datetime_end_fallback


def _filter_comparison_frame(
    *, data_frame_source: pl.DataFrame | None, datetime_start: datetime, datetime_end: datetime, label_dataset: str) -> pl.DataFrame:
    """Filter a comparison frame to the selected datetime window."""
    if data_frame_source is None:
        return _create_empty_comparison_frame()

    data_frame_normalized = _coerce_date_frame_to_datetime(data_frame = data_frame_source, label_dataset = label_dataset)
    if data_frame_normalized.is_empty():
        return data_frame_normalized

    literal_start = pl.lit(datetime_start).cast(pl.Datetime)
    literal_end = pl.lit(datetime_end).cast(pl.Datetime)

    data_frame_filtered = data_frame_normalized.filter(
        pl.col("Date").is_not_null()
        & (pl.col("Date") >= literal_start)
        & (pl.col("Date") <= literal_end),
    ).sort("Date")

    if data_frame_filtered.is_empty():
        _logger.warning("Filtering removed all %s data", label_dataset.lower())

    return data_frame_filtered


def _resolve_period_label_for_comparison(
    *,
    actual_start: pd.Timestamp,
    actual_end: pd.Timestamp,
    value_time_period: str,
) -> str:
    """Build the plot label for the active period selection."""
    if value_time_period == "custom":
        return f"{actual_start.strftime('%Y-%m-%d')} to {actual_end.strftime('%Y-%m-%d')}"

    label_period_base = _TIME_PERIOD_LABELS.get(value_time_period, "Selected Period")
    return (
        f"{label_period_base} ("
        f"{actual_start.strftime('%Y-%m-%d')} to {actual_end.strftime('%Y-%m-%d')})"
    )


def register_portfolios_comparison_server_outputs(
    *,
    input: Any,
    output: Any,
    data_inputs: dict[str, Any],
    reactives_shiny: dict[str, Any],
) -> None:
    """Register the Portfolio Comparison reactive server outputs."""
    data_frame_portfolio = data_inputs.get("My_Portfolio")
    data_frame_benchmark = data_inputs.get("Benchmark_Portfolio")

    validation_portfolio_result = validate_portfolio_data(data_portfolio=data_frame_portfolio)
    validation_benchmark_result = validate_portfolio_data(data_portfolio=data_frame_benchmark)

    if not validation_portfolio_result[0]:
        raise Exception_Validation_Input(
            f"Portfolio data validation failed: {validation_portfolio_result[1]}",
        )

    if not validation_benchmark_result[0]:
        raise Exception_Validation_Input(
            f"Benchmark data validation failed: {validation_benchmark_result[1]}",
        )

    @reactive.calc
    def get_effective_date_range() -> tuple[datetime, datetime]:
        return _calc_effective_date_range_for_comparison(
            input=input,
            data_frame_portfolio=data_frame_portfolio,
        )

    @reactive.calc
    def get_filtered_comparison_data() -> tuple[pl.DataFrame, pl.DataFrame]:
        try:
            datetime_start, datetime_end = get_effective_date_range()
            return (
                _filter_comparison_frame(
                    data_frame_source = data_frame_portfolio,
                    datetime_start=datetime_start,
                    datetime_end=datetime_end,
                    label_dataset="Portfolio",
                ),
                _filter_comparison_frame(
                    data_frame_source = data_frame_benchmark,
                    datetime_start=datetime_start,
                    datetime_end=datetime_end,
                    label_dataset="Benchmark",
                ),
            )
        except (TypeError, ValueError, AttributeError) as exc:  # pragma: no cover
            _logger.opt(exception=True).error("Error filtering comparison data: {}", exc)
            raise Exception_Configuration(f"Error filtering comparison data: {exc}")

    @output
    @render.text
    def output_ID_tab_portfolios_subtab_comparison_calculated_date_range() -> str:
        try:
            datetime_start, datetime_end = get_effective_date_range()
            value_time_period = input.input_ID_tab_portfolios_subtab_comparison_time_period()
            if value_time_period == "custom":
                return ""
            return f"📅 {datetime_start.strftime('%Y-%m-%d')} to {datetime_end.strftime('%Y-%m-%d')}"
        except (TypeError, ValueError, AttributeError, KeyError) as exc:  # pragma: no cover
            raise Exception_Configuration(f"Error displaying calculated date range: {exc}")

    @output
    @render.ui
    def output_ID_tab_portfolios_subtab_comparison_data_info() -> ui.Tag:
        try:
            data_frame_portfolio_filtered, data_frame_benchmark_filtered = get_filtered_comparison_data()
            value_time_period = input.input_ID_tab_portfolios_subtab_comparison_time_period()
            label_period = _TIME_PERIOD_LABELS.get(value_time_period, "Selected Period")

            count_portfolio = data_frame_portfolio_filtered.height if not data_frame_portfolio_filtered.is_empty() else 0
            count_benchmark = data_frame_benchmark_filtered.height if not data_frame_benchmark_filtered.is_empty() else 0

            if count_portfolio > 0 and count_benchmark > 0:
                status_icon = "✅"
                status_text = "Ready for comparison"
                status_class = "text-success"
            elif count_portfolio > 0 or count_benchmark > 0:
                status_icon = "⚠️"
                status_text = "Partial data available"
                status_class = "text-warning"
            else:
                status_icon = "❌"
                status_text = "No data available"
                status_class = "text-danger"

            return ui.div(
                ui.div(
                    ui.strong("Period: "),
                    label_period,
                    class_="small text-muted mb-1",
                ),
                ui.div(
                    ui.strong("Portfolio Data: "),
                    f"{count_portfolio} points" if count_portfolio > 0 else "No data",
                    class_="small text-muted mb-1",
                ),
                ui.div(
                    ui.strong("Benchmark Data: "),
                    f"{count_benchmark} points" if count_benchmark > 0 else "No data",
                    class_="small text-muted mb-1",
                ),
                ui.div(
                    ui.span(status_icon, class_="me-1"),
                    ui.span(status_text, class_=f"small {status_class}"),
                    class_="mt-2 p-2 rounded bg-light",
                ),
            )
        except (TypeError, ValueError, AttributeError, KeyError) as exc:  # pragma: no cover
            raise Exception_Configuration(f"Error generating data info: {exc}")

    @output
    @render.ui
    def output_ID_tab_portfolios_subtab_comparison_loading_status() -> ui.Tag:
        try:
            data_frame_portfolio_filtered, data_frame_benchmark_filtered = get_filtered_comparison_data()
            count_portfolio = data_frame_portfolio_filtered.height if not data_frame_portfolio_filtered.is_empty() else 0
            count_benchmark = data_frame_benchmark_filtered.height if not data_frame_benchmark_filtered.is_empty() else 0

            if count_portfolio > 0 and count_benchmark > 0:
                return ui.div(
                    ui.span("✅", class_="me-2"),
                    f"Data ready: {count_portfolio} portfolio points, {count_benchmark} benchmark points",
                    class_="alert alert-success p-2 mb-3",
                )
            if count_portfolio > 0 or count_benchmark > 0:
                return ui.div(
                    ui.span("⚠️", class_="me-2"),
                    f"Partial data: Portfolio ({count_portfolio} points), Benchmark ({count_benchmark} points)",
                    class_="alert alert-warning p-2 mb-3",
                )
            return ui.div(
                ui.span("❌", class_="me-2"),
                "No data available for selected period. Please adjust time range.",
                class_="alert alert-danger p-2 mb-3",
            )
        except (TypeError, ValueError, AttributeError) as exc:  # pragma: no cover
            _logger.error("Error creating loading status: %s", exc)
            return ui.div(
                ui.span("❌", class_="me-2"),
                f"Error: {exc!s}",
                class_="alert alert-danger p-2 mb-3",
            )

    @output
    @render_widget  # pyright: ignore[reportArgumentType]  # pyrefly: ignore[bad-specialization]
    def output_ID_tab_portfolios_subtab_comparison_plot_main():
        try:
            data_frame_portfolio_filtered, data_frame_benchmark_filtered = get_filtered_comparison_data()
            if data_frame_portfolio_filtered.is_empty() and data_frame_benchmark_filtered.is_empty():
                return create_error_figure(
                    message_text = "No Data Available",
                    title_text = "Please select a time period with available portfolio and benchmark data.",
                )

            value_viz_type = input.input_ID_tab_portfolios_subtab_comparison_viz_type()
            value_show_diff = input.input_ID_tab_portfolios_subtab_comparison_show_diff()

            if not data_frame_portfolio_filtered.is_empty():
                value_actual_start_raw = data_frame_portfolio_filtered.select(pl.col("Date").min()).item()
                value_actual_end_raw = data_frame_portfolio_filtered.select(pl.col("Date").max()).item()
            elif not data_frame_benchmark_filtered.is_empty():
                value_actual_start_raw = data_frame_benchmark_filtered.select(pl.col("Date").min()).item()
                value_actual_end_raw = data_frame_benchmark_filtered.select(pl.col("Date").max()).item()
            else:
                value_actual_start_raw, value_actual_end_raw = get_effective_date_range()

            value_actual_start = pd.Timestamp(value_actual_start_raw)
            value_actual_end = pd.Timestamp(value_actual_end_raw)
            value_time_period = input.input_ID_tab_portfolios_subtab_comparison_time_period()
            label_period = _resolve_period_label_for_comparison(
                actual_start=value_actual_start,
                actual_end=value_actual_end,
                value_time_period=value_time_period,
            )

            figure_main = create_plot_comparison_portfolios(
                data_portfolio=data_frame_portfolio_filtered,
                data_benchmark=data_frame_benchmark_filtered,
                viz_type=value_viz_type,
                show_diff=value_show_diff,
                period_label=label_period,
                start_date=value_actual_start,
                end_date=value_actual_end,
                data_was_validated=False,
            )

            figure_plotnine = build_plotnine_portfolio_comparison_portfolio_vs_benchmark(
                portfolio_df = data_frame_portfolio_filtered,
                benchmark_df = data_frame_benchmark_filtered,
            )
            update_visual_object_in_reactives(
                reactives_shiny = reactives_shiny,
                chart_key = "Chart_Portfolio_Comparison_Portfolio_vs_Benchmark",
                figure = figure_plotnine,
            )
            return figure_main
        except (TypeError, ValueError, AttributeError) as exc:  # pragma: no cover
            _logger.opt(exception=True).error("Error generating comparison plot: {}", exc)
            return create_error_figure(
                message_text = "Error Generating Chart",
                title_text = f"An error occurred while creating the comparison chart: {exc!s}",
            )

    @output
    @render.ui
    def output_ID_tab_portfolios_subtab_comparison_table_stats() -> ui.Tag:
        try:
            data_frame_portfolio_filtered, data_frame_benchmark_filtered = get_filtered_comparison_data()
            if data_frame_portfolio_filtered.is_empty() or data_frame_benchmark_filtered.is_empty():
                return ui.div(
                    ui.p(
                        "No data available for statistics calculation.",
                        class_="text-muted text-center p-3",
                    ),
                )

            # pandas-boundary: HTML table formatting and statistics remain pandas-based here.
            data_frame_pandas_portfolio = data_frame_portfolio_filtered.to_pandas().sort_values("Date")
            data_frame_pandas_benchmark = data_frame_benchmark_filtered.to_pandas().sort_values("Date")
            data_frame_pandas_portfolio["Date"] = pd.to_datetime(data_frame_pandas_portfolio["Date"])
            data_frame_pandas_benchmark["Date"] = pd.to_datetime(data_frame_pandas_benchmark["Date"])

            value_portfolio_start = data_frame_pandas_portfolio["Value"].iloc[0] if len(data_frame_pandas_portfolio) > 0 else 0
            value_portfolio_end = data_frame_pandas_portfolio["Value"].iloc[-1] if len(data_frame_pandas_portfolio) > 0 else 0
            value_portfolio_return = (
                ((value_portfolio_end / value_portfolio_start) - 1) * 100
                if value_portfolio_start > 0
                else 0
            )

            value_benchmark_start = data_frame_pandas_benchmark["Value"].iloc[0] if len(data_frame_pandas_benchmark) > 0 else 0
            value_benchmark_end = data_frame_pandas_benchmark["Value"].iloc[-1] if len(data_frame_pandas_benchmark) > 0 else 0
            value_benchmark_return = (
                ((value_benchmark_end / value_benchmark_start) - 1) * 100
                if value_benchmark_start > 0
                else 0
            )

            data_frame_pandas_portfolio["Daily_Return"] = data_frame_pandas_portfolio["Value"].pct_change()
            data_frame_pandas_benchmark["Daily_Return"] = data_frame_pandas_benchmark["Value"].pct_change()

            value_portfolio_volatility = data_frame_pandas_portfolio["Daily_Return"].std() * np.sqrt(252) * 100
            value_benchmark_volatility = data_frame_pandas_benchmark["Daily_Return"].std() * np.sqrt(252) * 100

            value_portfolio_mean_return = data_frame_pandas_portfolio["Daily_Return"].mean() * 252
            value_benchmark_mean_return = data_frame_pandas_benchmark["Daily_Return"].mean() * 252
            value_portfolio_std = data_frame_pandas_portfolio["Daily_Return"].std() * np.sqrt(252)
            value_benchmark_std = data_frame_pandas_benchmark["Daily_Return"].std() * np.sqrt(252)
            value_portfolio_sharpe = (value_portfolio_mean_return / value_portfolio_std) if value_portfolio_std > 0 else 0
            value_benchmark_sharpe = (value_benchmark_mean_return / value_benchmark_std) if value_benchmark_std > 0 else 0

            data_frame_pandas_portfolio["Cumulative_Max"] = data_frame_pandas_portfolio["Value"].cummax()
            data_frame_pandas_portfolio["Drawdown"] = (
                data_frame_pandas_portfolio["Value"]
                / data_frame_pandas_portfolio["Cumulative_Max"]
            ) - 1
            value_portfolio_drawdown_max = data_frame_pandas_portfolio["Drawdown"].min() * 100

            data_frame_pandas_benchmark["Cumulative_Max"] = data_frame_pandas_benchmark["Value"].cummax()
            data_frame_pandas_benchmark["Drawdown"] = (
                data_frame_pandas_benchmark["Value"]
                / data_frame_pandas_benchmark["Cumulative_Max"]
            ) - 1
            value_benchmark_drawdown_max = data_frame_pandas_benchmark["Drawdown"].min() * 100

            data_frame_stats = pd.DataFrame(
                [
                    {
                        "Metric": "Total Return (%)",
                        "Portfolio": f"{value_portfolio_return:.2f}",
                        "Benchmark": f"{value_benchmark_return:.2f}",
                        "Difference": f"{value_portfolio_return - value_benchmark_return:.2f}",
                    },
                    {
                        "Metric": "Annualized Volatility (%)",
                        "Portfolio": f"{value_portfolio_volatility:.2f}",
                        "Benchmark": f"{value_benchmark_volatility:.2f}",
                        "Difference": f"{value_portfolio_volatility - value_benchmark_volatility:.2f}",
                    },
                    {
                        "Metric": "Sharpe Ratio",
                        "Portfolio": f"{value_portfolio_sharpe:.2f}",
                        "Benchmark": f"{value_benchmark_sharpe:.2f}",
                        "Difference": f"{value_portfolio_sharpe - value_benchmark_sharpe:.2f}",
                    },
                    {
                        "Metric": "Max Drawdown (%)",
                        "Portfolio": f"{value_portfolio_drawdown_max:.2f}",
                        "Benchmark": f"{value_benchmark_drawdown_max:.2f}",
                        "Difference": f"{value_portfolio_drawdown_max - value_benchmark_drawdown_max:.2f}",
                    },
                ],
            )

            value_html_table = data_frame_stats.to_html(
                index=False,
                classes="table table-striped table-hover table-sm",
                escape=False,
                border=0,
            )
            value_html_table_styled = f"""
            <style>
                .stats-table-container table thead th {{
                    text-align: left !important;
                    vertical-align: bottom;
                    border-bottom: 2px solid #dee2e6;
                    padding: 0.75rem;
                    font-weight: 600;
                }}
                .stats-table-container table tbody td {{
                    text-align: left;
                    vertical-align: top;
                    padding: 0.75rem;
                }}
                .stats-table-container table tbody td:first-child {{
                    font-weight: 500;
                }}
            </style>
            <div class="stats-table-container">
                {value_html_table}
            </div>
            """
            return ui.HTML(value_html_table_styled)
        except (
            TypeError,
            ValueError,
            AttributeError,
            ZeroDivisionError,
        ) as exc:  # pragma: no cover
            _logger.opt(exception=True).error("Error generating comparison stats: {}", exc)
            return ui.div(
                ui.p(
                    f"Error generating statistics: {exc!s}",
                    class_="text-danger text-center p-3",
                ),
            )

"""Table-construction helpers for dashboard visual utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd
import polars as pl

from great_tables import GT, loc, md, style

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Configuration,
    Exception_Validation_Input,
)

from ._utils_visuals_summary_tables import (
    create_enhanced_summary_table_multi_column_impl_QWIM,
)

from ._utils_visuals_shared import format_value_for_display


if TYPE_CHECKING:
    from datetime import date
    from types import ModuleType


def _public_utils_visuals_module() -> ModuleType:
    from src.dashboard.shiny_utils import utils_visuals as public_utils_visuals

    return public_utils_visuals


def calculate_table_stats_basic(
    *, data_portfolio: pl.DataFrame | None, data_benchmark: pl.DataFrame | None, include_benchmark: bool = False) -> pd.DataFrame:
    """Calculate basic statistics table for portfolio and benchmark data."""
    if data_portfolio is None and data_benchmark is None:
        return pd.DataFrame(
            {"Metric": ["No Data"], "Value": ["No portfolio or benchmark data available"]},
        )

    has_portfolio_data = (
        data_portfolio is not None
        and isinstance(data_portfolio, pl.DataFrame)
        and not data_portfolio.is_empty()
    )

    has_benchmark_data = (
        data_benchmark is not None
        and isinstance(data_benchmark, pl.DataFrame)
        and not data_benchmark.is_empty()
    )

    if not has_portfolio_data and not has_benchmark_data:
        return pd.DataFrame(
            {"Metric": ["No Data"], "Value": ["Both portfolio and benchmark data are empty"]},
        )

    public_utils_visuals = _public_utils_visuals_module()

    try:
        stats_data = []

        if has_portfolio_data:
            portfolio_returns = public_utils_visuals.calculate_portfolio_returns(data_portfolio = data_portfolio)
            if len(portfolio_returns) > 0:
                portfolio_returns_series = portfolio_returns.to_pandas()

                stats_data.append(
                    {
                        "Metric": "Portfolio Daily Mean Return (%)",
                        "Value": f"{portfolio_returns_series.mean() * 100:.4f}",
                    },
                )
                stats_data.append(
                    {
                        "Metric": "Portfolio Daily Volatility (%)",
                        "Value": f"{portfolio_returns_series.std() * 100:.4f}",
                    },
                )
                stats_data.append(
                    {
                        "Metric": "Portfolio Annualized Return (%)",
                        "Value": f"{portfolio_returns_series.mean() * 252 * 100:.2f}",
                    },
                )
                stats_data.append(
                    {
                        "Metric": "Portfolio Annualized Volatility (%)",
                        "Value": f"{portfolio_returns_series.std() * np.sqrt(252) * 100:.2f}",
                    },
                )

                if portfolio_returns_series.std() > 0:
                    sharpe_ratio = (
                        portfolio_returns_series.mean()
                        / portfolio_returns_series.std()
                        * np.sqrt(252)
                    )
                    stats_data.append(
                        {
                            "Metric": "Portfolio Sharpe Ratio",
                            "Value": f"{sharpe_ratio:.4f}",
                        },
                    )

        if include_benchmark and has_benchmark_data:
            benchmark_returns = public_utils_visuals.calculate_portfolio_returns(data_portfolio = data_benchmark)
            if len(benchmark_returns) > 0:
                benchmark_returns_series = benchmark_returns.to_pandas()

                stats_data.append(
                    {
                        "Metric": "Benchmark Daily Mean Return (%)",
                        "Value": f"{benchmark_returns_series.mean() * 100:.4f}",
                    },
                )
                stats_data.append(
                    {
                        "Metric": "Benchmark Daily Volatility (%)",
                        "Value": f"{benchmark_returns_series.std() * 100:.4f}",
                    },
                )
                stats_data.append(
                    {
                        "Metric": "Benchmark Annualized Return (%)",
                        "Value": f"{benchmark_returns_series.mean() * 252 * 100:.2f}",
                    },
                )
                stats_data.append(
                    {
                        "Metric": "Benchmark Annualized Volatility (%)",
                        "Value": f"{benchmark_returns_series.std() * np.sqrt(252) * 100:.2f}",
                    },
                )

                if benchmark_returns_series.std() > 0:
                    sharpe_ratio = (
                        benchmark_returns_series.mean()
                        / benchmark_returns_series.std()
                        * np.sqrt(252)
                    )
                    stats_data.append(
                        {
                            "Metric": "Benchmark Sharpe Ratio",
                            "Value": f"{sharpe_ratio:.4f}",
                        },
                    )

        return (
            pd.DataFrame(stats_data)
            if stats_data
            else pd.DataFrame({"Metric": ["No Data"], "Value": ["N/A"]})
        )

    except Exception as exc:
        raise Exception_Configuration(f"Error generating basic statistics table: {exc}") from exc


def calculate_table_metrics_performance(
    *, data_portfolio: pl.DataFrame | None, data_benchmark: pl.DataFrame | None) -> pd.DataFrame:
    """Calculate performance metrics table for portfolio data."""
    _ = data_benchmark

    if data_portfolio is None:
        return pd.DataFrame({"Metric": ["No Data"], "Value": ["No portfolio data available"]})

    has_portfolio_data = isinstance(data_portfolio, pl.DataFrame) and not data_portfolio.is_empty()

    if not has_portfolio_data:
        return pd.DataFrame({"Metric": ["No Data"], "Value": ["Portfolio data is empty"]})

    public_utils_visuals = _public_utils_visuals_module()

    try:
        metrics_data = []

        portfolio_returns = public_utils_visuals.calculate_portfolio_returns(data_portfolio = data_portfolio)
        if len(portfolio_returns) > 0:
            portfolio_returns_series = portfolio_returns.to_pandas()
            cum_returns = (1 + portfolio_returns_series).cumprod()

            peak = cum_returns.cummax()
            drawdown = cum_returns / peak - 1
            max_dd = drawdown.min()

            metrics_data.append(
                {
                    "Metric": "Total Return (%)",
                    "Value": f"{(cum_returns.iloc[-1] - 1) * 100:.2f}",
                },
            )

            metrics_data.append(
                {
                    "Metric": "Max Drawdown (%)",
                    "Value": f"{max_dd * 100:.2f}",
                },
            )

            positive_returns = portfolio_returns_series > 0
            win_rate = positive_returns.sum() / len(portfolio_returns_series) * 100
            metrics_data.append(
                {
                    "Metric": "Win Rate (%)",
                    "Value": f"{win_rate:.2f}",
                },
            )

            metrics_data.append(
                {
                    "Metric": "Best Day (%)",
                    "Value": f"{portfolio_returns_series.max() * 100:.2f}",
                },
            )

            metrics_data.append(
                {
                    "Metric": "Worst Day (%)",
                    "Value": f"{portfolio_returns_series.min() * 100:.2f}",
                },
            )

            metrics_data.append(
                {
                    "Metric": "Skewness",
                    "Value": f"{portfolio_returns_series.skew():.4f}",
                },
            )

            metrics_data.append(
                {
                    "Metric": "Kurtosis",
                    "Value": f"{portfolio_returns_series.kurtosis():.4f}",
                },
            )

        return (
            pd.DataFrame(metrics_data)
            if metrics_data
            else pd.DataFrame({"Metric": ["No Data"], "Value": ["N/A"]})
        )

    except Exception as exc:
        raise Exception_Configuration(f"Error generating performance metrics table: {exc}") from exc


def create_table_comparison_stats(
    *, data_portfolio: pl.DataFrame | None, data_benchmark: pl.DataFrame | None, time_period: str, start_date: date, end_date: date, data_was_validated: bool = True) -> GT:
    """
    Create statistics comparison table using great-tables for portfolio and benchmark data.

    Parameters
    ----------
    data_portfolio : polars.DataFrame
        Portfolio data with "Date" and "Value" columns
    data_benchmark : polars.DataFrame
        Benchmark data with "Date" and "Value" columns
    time_period : str
        Time period identifier
    start_date : datetime.date
        Start date for the period
    end_date : datetime.date
        End date for the period
    data_was_validated : bool, optional
        Whether data has already been validated, by default True

    Returns
    -------
    great_tables.GT
        Formatted comparison statistics table

    Raises
    ------
    ValueError
        If data validation fails
    RuntimeError
        If table creation fails
    """
    _ = data_was_validated

    if data_portfolio is None and data_benchmark is None:
        empty_data = pd.DataFrame(
            {
                "Metric": ["No Data Available"],
                "Portfolio": ["-"],
                "Benchmark": ["-"],
                "Difference": ["-"],
            },
        )
        return GT(empty_data).tab_header(
            title="Portfolio vs Benchmark Statistics",
            subtitle="No data available for comparison",
        )

    if not isinstance(time_period, str):
        time_period = str(time_period) if time_period is not None else "Unknown Period"

    has_portfolio = (
        data_portfolio is not None
        and isinstance(data_portfolio, pl.DataFrame)
        and not data_portfolio.is_empty()
        and "Date" in data_portfolio.columns
        and "Value" in data_portfolio.columns
    )

    has_benchmark = (
        data_benchmark is not None
        and isinstance(data_benchmark, pl.DataFrame)
        and not data_benchmark.is_empty()
        and "Date" in data_benchmark.columns
        and "Value" in data_benchmark.columns
    )

    if not has_portfolio and not has_benchmark:
        empty_data = pd.DataFrame(
            {
                "Metric": ["No Valid Data"],
                "Portfolio": ["-"],
                "Benchmark": ["-"],
                "Difference": ["-"],
            },
        )
        return GT(empty_data).tab_header(
            title="Portfolio vs Benchmark Statistics",
            subtitle="Both portfolio and benchmark data are empty or invalid",
        )

    try:
        period_info = {
            "Period": time_period.replace("_", " ").title()
            if time_period != "custom"
            else "Custom Range",
            "Date Range": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            "Portfolio Points": 0,
            "Benchmark Points": 0,
        }

        def _normalize_stats_input_frame(
            *, data_frame: pl.DataFrame) -> pl.DataFrame:
            date_dtype = data_frame.select("Date").dtypes[0]
            value_dtype = data_frame.select("Value").dtypes[0]

            if date_dtype in [pl.Utf8, pl.String]:
                date_expression = pl.col("Date").str.to_datetime(strict=False)
            elif date_dtype == pl.Date:
                date_expression = pl.col("Date").cast(pl.Datetime)
            else:
                date_expression = pl.col("Date").cast(pl.Datetime, strict=False)

            value_expression = (
                pl.lit(None, dtype=pl.Float64)
                if value_dtype == pl.Boolean
                else pl.col("Value").cast(pl.Float64, strict=False)
            )

            return data_frame.with_columns(
                [
                    date_expression.alias("Date"),
                    value_expression.alias("Value"),
                ],
            )

        portfolio_stats = {}
        if has_portfolio:
            try:
                assert data_portfolio is not None
                portfolio_sorted = data_portfolio.sort("Date")
                portfolio_processed = _normalize_stats_input_frame(data_frame = portfolio_sorted)

                portfolio_clean = portfolio_processed.filter(
                    pl.col("Date").is_not_null() & pl.col("Value").is_not_null(),
                )

                if portfolio_clean.height > 0:
                    portfolio_values = portfolio_clean.select("Value").to_series().to_list()

                    period_info["Portfolio Points"] = len(portfolio_values)

                    start_value: float = 0.0
                    end_value: float = 0.0
                    if len(portfolio_values) > 1:
                        start_value = portfolio_values[0]
                        end_value = portfolio_values[-1]

                        if start_value != 0:
                            total_return = ((end_value / start_value) - 1) * 100
                            portfolio_stats["Total Return (%)"] = total_return

                        portfolio_returns = (
                            portfolio_clean.select(
                                pl.col("Value").pct_change().alias("returns"),
                            )
                            .drop_nulls()
                            .to_series()
                            .to_list()
                        )

                        if len(portfolio_returns) > 0:  # pragma: no branch
                            portfolio_stats["Daily Mean Return (%)"] = (
                                np.mean(portfolio_returns) * 100
                            )
                            portfolio_stats["Daily Volatility (%)"] = (
                                np.std(portfolio_returns) * 100
                            )
                            portfolio_stats["Annualized Return (%)"] = (
                                np.mean(portfolio_returns) * 252 * 100
                            )
                            portfolio_stats["Annualized Volatility (%)"] = (
                                np.std(portfolio_returns) * np.sqrt(252) * 100
                            )

                            if np.std(portfolio_returns) > 0:
                                portfolio_stats["Sharpe Ratio"] = (
                                    np.mean(portfolio_returns)
                                    / np.std(portfolio_returns)
                                    * np.sqrt(252)
                                )

                        cum_returns = np.cumprod(1 + np.array(portfolio_returns))
                        peak_values = np.maximum.accumulate(cum_returns)
                        drawdown_values = cum_returns / peak_values - 1
                        max_dd = drawdown_values.min()

                        portfolio_stats["Max Drawdown (%)"] = max_dd * 100

                    portfolio_stats["Start Value"] = start_value
                    portfolio_stats["End Value"] = end_value
                    portfolio_stats["Min Value"] = min(portfolio_values)
                    portfolio_stats["Max Value"] = max(portfolio_values)

            except Exception:  # pragma: no cover
                portfolio_stats = {"Error": "Failed to calculate portfolio statistics"}

        benchmark_stats = {}
        if has_benchmark:
            try:
                assert data_benchmark is not None
                benchmark_sorted = data_benchmark.sort("Date")
                benchmark_processed = _normalize_stats_input_frame(data_frame = benchmark_sorted)

                benchmark_clean = benchmark_processed.filter(
                    pl.col("Date").is_not_null() & pl.col("Value").is_not_null(),
                )

                if benchmark_clean.height > 0:
                    benchmark_values = benchmark_clean.select("Value").to_series().to_list()

                    period_info["Benchmark Points"] = len(benchmark_values)

                    start_value = 0.0
                    end_value = 0.0
                    if len(benchmark_values) > 1:
                        start_value = benchmark_values[0]
                        end_value = benchmark_values[-1]

                        if start_value != 0:
                            total_return = ((end_value / start_value) - 1) * 100
                            benchmark_stats["Total Return (%)"] = total_return

                        benchmark_returns = (
                            benchmark_clean.select(
                                pl.col("Value").pct_change().alias("returns"),
                            )
                            .drop_nulls()
                            .to_series()
                            .to_list()
                        )

                        if len(benchmark_returns) > 0:  # pragma: no branch
                            benchmark_stats["Daily Mean Return (%)"] = (
                                np.mean(benchmark_returns) * 100
                            )
                            benchmark_stats["Daily Volatility (%)"] = (
                                np.std(benchmark_returns) * 100
                            )
                            benchmark_stats["Annualized Return (%)"] = (
                                np.mean(benchmark_returns) * 252 * 100
                            )
                            benchmark_stats["Annualized Volatility (%)"] = (
                                np.std(benchmark_returns) * np.sqrt(252) * 100
                            )

                            if np.std(benchmark_returns) > 0:
                                benchmark_stats["Sharpe Ratio"] = (
                                    np.mean(benchmark_returns)
                                    / np.std(benchmark_returns)
                                    * np.sqrt(252)
                                )

                        cum_returns = np.cumprod(1 + np.array(benchmark_returns))
                        peak_values = np.maximum.accumulate(cum_returns)
                        drawdown_values = cum_returns / peak_values - 1
                        benchmark_stats["Max Drawdown (%)"] = np.min(drawdown_values) * 100

                    benchmark_stats["Start Value"] = start_value
                    benchmark_stats["End Value"] = end_value
                    benchmark_stats["Min Value"] = min(benchmark_values)
                    benchmark_stats["Max Value"] = max(benchmark_values)

            except Exception:  # pragma: no cover
                benchmark_stats = {"Error": "Failed to calculate benchmark statistics"}

        all_metrics = set()
        if portfolio_stats:
            all_metrics.update(portfolio_stats.keys())
        if benchmark_stats:
            all_metrics.update(benchmark_stats.keys())

        all_metrics = sorted([metric for metric in all_metrics if metric != "Error"])

        table_data = []

        table_data.append(
            {
                "Metric": "Selected Period",
                "Portfolio": period_info["Period"],
                "Benchmark": period_info["Period"],
                "Difference": "-",
            },
        )

        table_data.append(
            {
                "Metric": "Date Range",
                "Portfolio": period_info["Date Range"],
                "Benchmark": period_info["Date Range"],
                "Difference": "-",
            },
        )

        table_data.append(
            {
                "Metric": "Data Points",
                "Portfolio": str(period_info["Portfolio Points"]),
                "Benchmark": str(period_info["Benchmark Points"]),
                "Difference": str(
                    period_info["Portfolio Points"] - period_info["Benchmark Points"],
                ),
            },
        )

        for metric in all_metrics:
            portfolio_value = portfolio_stats.get(metric, "N/A")
            benchmark_value = benchmark_stats.get(metric, "N/A")

            difference = "N/A"
            if (
                not isinstance(portfolio_value, bool)
                and not isinstance(benchmark_value, bool)
                and isinstance(portfolio_value, (int, float))
                and isinstance(benchmark_value, (int, float))
                and not pd.isna(portfolio_value)
                and not pd.isna(benchmark_value)
            ):
                difference = portfolio_value - benchmark_value
                difference = f"{difference:.4f}"

            portfolio_display = (
                format_value_for_display(value_input = portfolio_value) if portfolio_value != "N/A" else "N/A"
            )
            benchmark_display = (
                format_value_for_display(value_input = benchmark_value) if benchmark_value != "N/A" else "N/A"
            )

            table_data.append(
                {
                    "Metric": metric,
                    "Portfolio": portfolio_display,
                    "Benchmark": benchmark_display,
                    "Difference": difference,
                },
            )

        comparison_df = pd.DataFrame(table_data)

        return (
            GT(comparison_df)
            .tab_header(
                title="Portfolio vs Benchmark Statistics",
                subtitle=f"Performance comparison for {period_info['Period']}",
            )
            .cols_label(
                Metric="Metric",
                Portfolio="Portfolio",
                Benchmark="Benchmark",
                Difference="Difference (P-B)",
            )
            .tab_style(
                style=style.fill(color="#f8f9fa"),
                locations=loc.body(rows=[0, 1, 2]),
            )
            .tab_style(
                style=style.text(weight="bold"),
                locations=loc.body(columns=["Metric"]),
            )
        )

    except Exception as exc:  # pragma: no cover
        error_data = pd.DataFrame(
            {
                "Metric": ["Error"],
                "Portfolio": [f"Error: {exc!s}"],
                "Benchmark": ["-"],
                "Difference": ["-"],
            },
        )

        (
            GT(error_data)
            .tab_header(
                title="Portfolio vs Benchmark Statistics",
                subtitle="Error occurred during calculation",
            )
            .tab_style(
                style=style.fill(color="#f8d7da"),
                locations=loc.body(),
            )
        )

        raise Exception_Configuration(f"Error creating comparison statistics table: {exc}") from exc


def create_table_summary_weights_analysis(
    *, data_stats: dict[str, Any], show_pct: bool = True, data_was_validated: bool = True) -> GT:
    """
    Create summary statistics table for Weights Analysis using great-tables.

    Parameters
    ----------
    data_stats : dict
        Dictionary containing weight statistics for each component
    show_pct : bool, optional
        Whether to show values as percentages, by default True
    data_was_validated : bool, optional
        Whether data has already been validated, by default True

    Returns
    -------
    great_tables.GT
        Formatted Weights Analysis statistics table

    Raises
    ------
    ValueError
        If data validation fails
    RuntimeError
        If table creation fails
    """
    _ = data_was_validated

    if not data_stats or not isinstance(data_stats, dict):
        empty_data = pd.DataFrame(
            {
                "Component": ["No Data Available"],
                "Latest": ["-"],
                "Average": ["-"],
                "Min": ["-"],
                "Max": ["-"],
                "StdDev": ["-"],
            },
        )
        return GT(empty_data).tab_header(
            title="Portfolio Weight Distribution Statistics",
            subtitle="No data available",
        )

    period_info = data_stats.get("_period_info", {})
    period_label = period_info.get("period_label", "Unknown Period")
    data_points = period_info.get("data_points", 0)

    try:
        component_stats = {k: v for k, v in data_stats.items() if not k.startswith("_")}

        if not component_stats:
            empty_data = pd.DataFrame(
                {
                    "Component": ["No Components Available"],
                    "Latest": ["-"],
                    "Average": ["-"],
                    "Min": ["-"],
                    "Max": ["-"],
                    "StdDev": ["-"],
                },
            )
            return GT(empty_data).tab_header(
                title="Portfolio Weight Distribution Statistics",
                subtitle="No component data available",
            )

        table_data = []

        for component_name, stats in component_stats.items():
            latest_weight = stats.get("Latest", 0)
            average_weight = stats.get("Average", 0)
            min_weight = stats.get("Min", 0)
            max_weight = stats.get("Max", 0)
            std_weight = stats.get("StdDev", 0)

            def safe_format_value(*, value: Any, as_percentage: Any = True) -> str | None:
                """Safely format a value for display with defensive programming."""
                if value is None:
                    return "-"

                if pd.isna(value):
                    return "-"

                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    return "-"

                try:
                    if as_percentage:
                        return f"{float(value):.2f}%"
                    return f"{float(value):.4f}"
                except (ValueError, TypeError, OverflowError):
                    return "-"

            latest_display = safe_format_value(value = latest_weight, as_percentage = show_pct)
            average_display = safe_format_value(value = average_weight, as_percentage = show_pct)
            min_display = safe_format_value(value = min_weight, as_percentage = show_pct)
            max_display = safe_format_value(value = max_weight, as_percentage = show_pct)
            std_display = safe_format_value(value = std_weight, as_percentage = show_pct)

            table_data.append(
                {
                    "Component": str(component_name),
                    "Latest": latest_display,
                    "Average": average_display,
                    "Min": min_display,
                    "Max": max_display,
                    "StdDev": std_display,
                },
            )

        def extract_numeric_for_sorting(*, display_value: Any) -> Any:
            """Extract numeric value from display string for sorting."""
            if display_value == "-":
                return 0

            try:
                numeric_str = display_value.rstrip("%")
                return float(numeric_str)
            except (ValueError, TypeError, AttributeError):  # pragma: no cover
                return 0

        table_data.sort(key=lambda x: extract_numeric_for_sorting(display_value = x["Latest"]), reverse=True)

        weights_df = pd.DataFrame(table_data)

        return (
            GT(weights_df)
            .tab_header(
                title="Portfolio Weight Distribution Statistics",
                subtitle=f"Weight analysis for {period_label} ({data_points} data points)",
            )
            .cols_label(
                Component="Component",
                Latest="Latest Weight",
                Average="Average Weight",
                Min="Minimum Weight",
                Max="Maximum Weight",
                StdDev="Standard Deviation",
            )
            .tab_style(
                style=style.text(weight="bold"),
                locations=loc.body(columns=["Component"]),
            )
        )

    except Exception as exc:  # pragma: no cover
        error_data = pd.DataFrame(
            {
                "Component": ["Error"],
                "Latest": [f"Error: {exc!s}"],
                "Average": ["-"],
                "Min": ["-"],
                "Max": ["-"],
                "StdDev": ["-"],
            },
        )

        (
            GT(error_data)
            .tab_header(
                title="Portfolio Weight Distribution Statistics",
                subtitle="Error occurred during calculation",
            )
            .tab_style(
                style=style.fill(color="#f8d7da"),
                locations=loc.body(),
            )
        )

        raise Exception_Configuration(
            f"Error creating Weights Analysis statistics table: {exc}",
        ) from exc


def create_enhanced_summary_table(
    *, dataframe_input: pl.DataFrame, table_title: str = "Summary Table", table_subtitle: str = "", column_headers: list[str] | None = None, currency_columns: list[str] | None = None, percentage_columns: list[str] | None = None, table_theme: str = "professional", show_row_numbers: bool = False, table_width: str = "100%") -> GT:
    """Create a formatted great-tables summary table for one- or two-column data.

    The function validates the input dataframe, applies optional currency and
    percentage formatting, and styles the result with one of the supported
    summary-table themes.
    """
    if dataframe_input is None:
        raise Exception_Validation_Input("Dataframe input cannot be None")

    if not isinstance(dataframe_input, pl.DataFrame):
        raise TypeError("Input must be a polars DataFrame")

    if dataframe_input.is_empty():
        raise Exception_Validation_Input("Dataframe cannot be empty")

    Column_Count = len(dataframe_input.columns)
    if Column_Count not in [1, 2]:
        raise Exception_Validation_Input("Dataframe must have exactly 1 or 2 columns")

    if column_headers is not None:
        if not isinstance(column_headers, list):
            raise TypeError("Column headers must be a list")
        if len(column_headers) != Column_Count:
            raise Exception_Validation_Input("Column headers count must match dataframe columns")

    try:
        Table_GT = GT(dataframe_input)

        if column_headers is not None:
            Table_GT = Table_GT.cols_label(
                cases={
                    dataframe_input.columns[idx]: column_headers[idx]
                    for idx in range(len(column_headers))
                },
            )

        if table_title:
            Table_GT = Table_GT.tab_header(
                title=md(f"**{table_title}**"),
                subtitle=md(table_subtitle) if table_subtitle else None,
            )

        if currency_columns:
            for Currency_Column in currency_columns:
                if Currency_Column in dataframe_input.columns:
                    Table_GT = Table_GT.fmt_currency(
                        columns=[Currency_Column],
                        currency="USD",
                        decimals=2,
                    )

        if percentage_columns:
            for Percentage_Column in percentage_columns:
                if Percentage_Column in dataframe_input.columns:
                    Table_GT = Table_GT.fmt_percent(
                        columns=[Percentage_Column],
                        decimals=1,
                    )

        if table_theme == "professional":
            Table_GT = Table_GT.tab_options(
                table_width=table_width,
                table_font_size="14px",
                heading_background_color="#f8f9fa",
                heading_title_font_size="18px",
                heading_subtitle_font_size="14px",
                column_labels_background_color="#e9ecef",
                row_striping_background_color="#f8f9fa",
            )
        elif table_theme == "minimal":
            Table_GT = Table_GT.tab_options(
                table_width=table_width,
                table_font_size="13px",
                table_border_top_style="hidden",
                table_border_bottom_style="hidden",
            )
        elif table_theme == "enhanced":
            Table_GT = Table_GT.tab_options(
                table_width=table_width,
                table_font_size="14px",
                heading_background_color="#007bff",
                heading_title_font_size="20px",
                column_labels_background_color="#6c757d",
                row_striping_background_color="#f1f3f4",
            )

        if show_row_numbers:
            Table_GT = Table_GT.opt_row_striping()

        return Table_GT

    except Exception as exc_error:  # pragma: no cover
        raise Exception_Configuration(
            f"Error creating enhanced summary table: {exc_error!s}",
        ) from exc_error


def create_enhanced_summary_table_multi_column(
    *, dataframe_input: pl.DataFrame, table_title: str = "Summary Table", table_subtitle: str = "", currency_columns: list[str] | None = None, percentage_columns: list[str] | None = None, table_theme: str = "professional", table_width: str = "100%") -> GT:
    """Create a formatted great-tables summary table for multi-column data."""
    return create_enhanced_summary_table_multi_column_impl_QWIM(
        dataframe_input=dataframe_input,
        table_title=table_title,
        table_subtitle=table_subtitle,
        currency_columns=currency_columns,
        percentage_columns=percentage_columns,
        table_theme=table_theme,
        table_width=table_width,
    )


__all__ = [
    "calculate_table_metrics_performance",
    "calculate_table_stats_basic",
    "create_enhanced_summary_table",
    "create_enhanced_summary_table_multi_column",
    "create_table_comparison_stats",
    "create_table_summary_weights_analysis",
]

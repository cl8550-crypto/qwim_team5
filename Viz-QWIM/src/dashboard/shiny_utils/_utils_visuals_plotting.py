"""Plot-construction helpers for dashboard visual utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import plotly.graph_objects as go
import polars as pl

from plotly.subplots import make_subplots

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Configuration,
)

from ._utils_visuals_shared import create_error_figure


if TYPE_CHECKING:
    from datetime import date
    from types import ModuleType


def _public_utils_visuals_module() -> ModuleType:
    from src.dashboard.shiny_utils import utils_visuals as public_utils_visuals

    return public_utils_visuals


def create_plot_portfolios_comparison(
    *, data_portfolio: pl.DataFrame | None, data_benchmark: pl.DataFrame | None, period_label: str, data_was_validated: bool = True) -> go.Figure:
    """
    Create portfolio vs benchmark comparison plot using Polars DataFrames.

    Parameters
    ----------
    data_portfolio : polars.DataFrame
        Portfolio data with "Date" and "Value" columns
    data_benchmark : polars.DataFrame
        Benchmark data with "Date" and "Value" columns
    period_label : str
        Label for the time period
    data_was_validated : bool, optional
        Whether data has already been validated, by default True

    Returns
    -------
    plotly.graph_objects.Figure
        Portfolio vs benchmark comparison plot

    Raises
    ------
    ValueError
        If data validation fails
    RuntimeError
        If plot creation fails
    """
    if data_portfolio is None and data_benchmark is None:
        return create_error_figure(message_text = "No portfolio or benchmark data available")

    if not isinstance(period_label, str):
        period_label = str(period_label) if period_label is not None else "Unknown Period"

    has_portfolio_data = True
    has_benchmark_data = True
    public_utils_visuals = _public_utils_visuals_module()

    if not data_was_validated:
        has_portfolio_data, has_benchmark_data = (
            public_utils_visuals.validate_portfolio_and_benchmark_data_if_not_already_validated(
                data_portfolio=data_portfolio,
                data_benchmark=data_benchmark,
            )
        )

    if not has_portfolio_data and not has_benchmark_data:
        return create_error_figure(message_text = "Both portfolio and benchmark data are empty")

    try:
        figure_obj = go.Figure()

        if has_portfolio_data and data_portfolio is not None:
            assert data_portfolio is not None
            portfolio_sorted = data_portfolio.sort("Date")

            portfolio_dates = portfolio_sorted.select("Date").to_series().to_list()
            portfolio_values = portfolio_sorted.select("Value").to_series()

            portfolio_numeric = portfolio_values.cast(pl.Float64, strict=False)
            portfolio_clean = portfolio_numeric.drop_nulls()

            if len(portfolio_clean) > 0:
                valid_indices = portfolio_numeric.is_not_null()
                portfolio_dates_clean = [
                    date_val
                    for idx, date_val in enumerate(portfolio_dates)
                    if idx < len(valid_indices) and valid_indices[idx]
                ]

                portfolio_values_list = portfolio_clean.to_list()
                first_value = portfolio_values_list[0]

                if first_value != 0:
                    normalized_portfolio = [
                        (value / first_value) * 100 for value in portfolio_values_list
                    ]

                    figure_obj.add_trace(
                        go.Scatter(
                            x=portfolio_dates_clean,
                            y=normalized_portfolio,
                            mode="lines",
                            name="Portfolio",
                            line={"width": 3, "color": "#1f77b4"},
                            hovertemplate="<b>Portfolio</b><br>Date: %{x}<br>Value: %{y:.2f}<extra></extra>",
                        ),
                    )

        if has_benchmark_data and data_benchmark is not None:
            assert data_benchmark is not None
            benchmark_sorted = data_benchmark.sort("Date")

            benchmark_dates = benchmark_sorted.select("Date").to_series().to_list()
            benchmark_values = benchmark_sorted.select("Value").to_series()

            benchmark_numeric = benchmark_values.cast(pl.Float64, strict=False)
            benchmark_clean = benchmark_numeric.drop_nulls()

            if len(benchmark_clean) > 0:
                valid_indices = benchmark_numeric.is_not_null()
                benchmark_dates_clean = [
                    date_val
                    for idx, date_val in enumerate(benchmark_dates)
                    if idx < len(valid_indices) and valid_indices[idx]
                ]

                benchmark_values_list = benchmark_clean.to_list()
                first_value = benchmark_values_list[0]

                if first_value != 0:
                    normalized_benchmark = [
                        (value / first_value) * 100 for value in benchmark_values_list
                    ]

                    figure_obj.add_trace(
                        go.Scatter(
                            x=benchmark_dates_clean,
                            y=normalized_benchmark,
                            mode="lines",
                            name="Benchmark",
                            line={"width": 3, "color": "#ff7f0e", "dash": "dash"},
                            hovertemplate="<b>Benchmark</b><br>Date: %{x}<br>Value: %{y:.2f}<extra></extra>",
                        ),
                    )

        if len(figure_obj.data) == 0:  # pyright: ignore[reportArgumentType]
            return create_error_figure(
                message_text = "No valid data series to display",
                details_text="Both portfolio and benchmark data contain no valid numeric values",
            )

        layout_config = {
            "title": {
                "text": f"Portfolio vs Benchmark Performance ({period_label})",
                "font": {"size": 18},
                "x": 0.5,
                "xanchor": "center",
            },
            "xaxis_title": "Date",
            "yaxis_title": "Normalized Value (Base=100)",
            "template": "plotly_white",
            "height": 600,
            "margin": {"l": 60, "r": 40, "t": 120, "b": 60},
            "legend": {
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "center",
                "x": 0.5,
            },
            "hovermode": "x unified",
        }

        figure_obj.update_layout(**layout_config)

        return figure_obj

    except Exception as plotly_error:
        raise Exception_Configuration(
            f"Error creating comparison plot: {plotly_error}",
        ) from plotly_error


def create_plot_rolling_statistics(
    *, data_portfolio: pl.DataFrame | None, data_benchmark: pl.DataFrame | None, window_size: int, period_label: str, data_was_validated: bool = True, include_benchmark: bool = False) -> go.Figure:
    """Create rolling statistics subplot."""
    if data_portfolio is None and data_benchmark is None:
        return create_error_figure(message_text = "No portfolio or benchmark data available")

    if not isinstance(period_label, str):
        period_label = str(period_label) if period_label is not None else "Unknown Period"

    if isinstance(window_size, bool) or not isinstance(window_size, int) or window_size < 1:
        window_size = 30

    has_portfolio_data = True
    has_benchmark_data = True
    public_utils_visuals = _public_utils_visuals_module()

    if not data_was_validated:
        has_portfolio_data, has_benchmark_data = (
            public_utils_visuals.validate_portfolio_and_benchmark_data_if_not_already_validated(
                data_portfolio=data_portfolio,
                data_benchmark=data_benchmark,
            )
        )

    if not has_portfolio_data and not has_benchmark_data:
        return create_error_figure(message_text = "Both portfolio and benchmark data are empty")

    try:
        figure_obj = make_subplots(
            rows=2,
            cols=1,
            subplot_titles=[
                f"Rolling {window_size}-Day Average Returns (%)",
                f"Rolling {window_size}-Day Volatility (% Annualized)",
            ],
            vertical_spacing=0.15,
            shared_xaxes=True,
        )

        if has_portfolio_data and data_portfolio is not None and not data_portfolio.is_empty():
            portfolio_returns = public_utils_visuals.calculate_portfolio_returns(data_portfolio = data_portfolio)
            if len(portfolio_returns) >= window_size:
                portfolio_returns_pandas = portfolio_returns.to_pandas()
                rolling_returns = portfolio_returns_pandas.rolling(window=window_size).mean() * 100
                rolling_vol = (
                    portfolio_returns_pandas.rolling(window=window_size).std() * 100 * np.sqrt(252)
                )

                assert data_portfolio is not None
                portfolio_sorted = data_portfolio.sort("Date")
                dates_list = portfolio_sorted.select("Date").to_series().to_list()

                if len(dates_list) >= window_size:  # pragma: no branch
                    dates_aligned = dates_list[
                        window_size - 1 : window_size - 1 + len(rolling_returns.dropna())
                    ]

                    figure_obj.add_trace(
                        go.Scatter(
                            x=dates_aligned,
                            y=rolling_returns.dropna(),
                            mode="lines",
                            name="Portfolio Returns",
                            line={"color": "#1f77b4", "width": 2},
                            hovertemplate="Date: %{x}<br>Portfolio Avg Return: %{y:.3f}%<extra></extra>",
                        ),
                        row=1,
                        col=1,
                    )

                    figure_obj.add_trace(
                        go.Scatter(
                            x=dates_aligned,
                            y=rolling_vol.dropna(),
                            mode="lines",
                            name="Portfolio Volatility",
                            line={"color": "#1f77b4", "width": 2},
                            hovertemplate="Date: %{x}<br>Portfolio Volatility: %{y:.2f}%<extra></extra>",
                        ),
                        row=2,
                        col=1,
                    )

        if (
            include_benchmark
            and has_benchmark_data
            and data_benchmark is not None
            and not data_benchmark.is_empty()
        ):
            benchmark_returns = public_utils_visuals.calculate_portfolio_returns(data_portfolio = data_benchmark)
            if len(benchmark_returns) >= window_size:
                benchmark_returns_pandas = benchmark_returns.to_pandas()
                rolling_returns = benchmark_returns_pandas.rolling(window=window_size).mean() * 100
                rolling_vol = (
                    benchmark_returns_pandas.rolling(window=window_size).std() * 100 * np.sqrt(252)
                )

                assert data_benchmark is not None
                benchmark_sorted = data_benchmark.sort("Date")
                dates_list = benchmark_sorted.select("Date").to_series().to_list()

                if len(dates_list) >= window_size:  # pragma: no branch
                    dates_aligned = dates_list[
                        window_size - 1 : window_size - 1 + len(rolling_returns.dropna())
                    ]

                    figure_obj.add_trace(
                        go.Scatter(
                            x=dates_aligned,
                            y=rolling_returns.dropna(),
                            mode="lines",
                            name="Benchmark Returns",
                            line={"color": "#ff7f0e", "width": 2, "dash": "dash"},
                            hovertemplate="Date: %{x}<br>Benchmark Avg Return: %{y:.3f}%<extra></extra>",
                        ),
                        row=1,
                        col=1,
                    )

                    figure_obj.add_trace(
                        go.Scatter(
                            x=dates_aligned,
                            y=rolling_vol.dropna(),
                            mode="lines",
                            name="Benchmark Volatility",
                            line={"color": "#ff7f0e", "width": 2, "dash": "dash"},
                            hovertemplate="Date: %{x}<br>Benchmark Volatility: %{y:.2f}%<extra></extra>",
                        ),
                        row=2,
                        col=1,
                    )

        figure_obj.add_hline(y=0, line_dash="dot", line_color="gray", row=1, col=1)  # pyright: ignore[reportArgumentType]

        figure_obj.update_layout(
            title={
                "text": f"Rolling {window_size}-Day Statistics ({period_label})",
                "font": {"size": 18},
                "x": 0.5,
                "xanchor": "center",
            },
            template="plotly_white",
            height=700,
            showlegend=True,
            margin={"l": 60, "r": 60, "t": 140, "b": 60},
            hovermode="x unified",
            legend={
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "center",
                "x": 0.5,
            },
        )

        figure_obj.update_xaxes(title_text="Date", row=2, col=1)
        figure_obj.update_yaxes(title_text="Return (%)", row=1, col=1)
        figure_obj.update_yaxes(title_text="Volatility (%)", row=2, col=1)

        return figure_obj

    except Exception as plotly_error:
        raise Exception_Configuration(
            f"Error creating rolling statistics plot: {plotly_error}",
        ) from plotly_error


def create_plot_returns_distribution(
    *, data_portfolio: pl.DataFrame | None, data_benchmark: pl.DataFrame | None, period_label: str, data_was_validated: bool = True, include_benchmark: bool = False) -> go.Figure:
    """Create returns distribution histogram comparing portfolio and benchmark."""
    if data_portfolio is None and data_benchmark is None:
        return create_error_figure(message_text = "No portfolio or benchmark data available")

    if not isinstance(period_label, str):
        period_label = str(period_label) if period_label is not None else "Unknown Period"

    has_portfolio_data = True
    has_benchmark_data = True
    public_utils_visuals = _public_utils_visuals_module()

    if not data_was_validated:
        has_portfolio_data, has_benchmark_data = (
            public_utils_visuals.validate_portfolio_and_benchmark_data_if_not_already_validated(
                data_portfolio=data_portfolio,
                data_benchmark=data_benchmark,
            )
        )

    if not has_portfolio_data and not has_benchmark_data:
        return create_error_figure(message_text = "Both portfolio and benchmark data are empty")

    try:
        figure_obj = go.Figure()

        if has_portfolio_data and data_portfolio is not None and not data_portfolio.is_empty():
            portfolio_returns = public_utils_visuals.calculate_portfolio_returns(data_portfolio = data_portfolio)
            if len(portfolio_returns) > 0:
                portfolio_returns_pct = portfolio_returns.to_pandas() * 100
                figure_obj.add_trace(
                    go.Histogram(
                        x=portfolio_returns_pct,
                        name="Portfolio",
                        opacity=0.7,
                        marker_color="#1f77b4",
                        nbinsx=min(50, max(10, len(portfolio_returns_pct) // 5)),
                        hovertemplate="Portfolio Return: %{x:.2f}%<br>Frequency: %{y}<extra></extra>",
                    ),
                )

        if (
            include_benchmark
            and has_benchmark_data
            and data_benchmark is not None
            and not data_benchmark.is_empty()
        ):
            benchmark_returns = public_utils_visuals.calculate_portfolio_returns(data_portfolio = data_benchmark)
            if len(benchmark_returns) > 0:
                benchmark_returns_pct = benchmark_returns.to_pandas() * 100
                figure_obj.add_trace(
                    go.Histogram(
                        x=benchmark_returns_pct,
                        name="Benchmark",
                        opacity=0.7,
                        marker_color="#ff7f0e",
                        nbinsx=min(50, max(10, len(benchmark_returns_pct) // 5)),
                        hovertemplate="Benchmark Return: %{x:.2f}%<br>Frequency: %{y}<extra></extra>",
                    ),
                )

        if has_portfolio_data and data_portfolio is not None and not data_portfolio.is_empty():
            portfolio_returns = public_utils_visuals.calculate_portfolio_returns(data_portfolio = data_portfolio)
            if len(portfolio_returns) > 0:
                portfolio_returns_pandas = portfolio_returns.to_pandas()
                mean_ret = portfolio_returns_pandas.mean() * 100
                std_ret = portfolio_returns_pandas.std() * 100
                subtitle_text = f"Portfolio Mean: {mean_ret:.3f}%, Std Dev: {std_ret:.3f}%"
            else:
                subtitle_text = "No data available"
        else:
            subtitle_text = "No data available"

        figure_obj.update_layout(
            title={
                "text": f"Returns Distribution ({period_label})<br><sub>{subtitle_text}</sub>",
                "font": {"size": 18},
                "x": 0.5,
                "xanchor": "center",
            },
            xaxis_title="Daily Return (%)",
            yaxis_title="Frequency",
            template="plotly_white",
            height=600,
            margin={"l": 60, "r": 60, "t": 120, "b": 60},
            hovermode="closest",
            barmode="overlay",
            legend={
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "center",
                "x": 0.5,
            },
        )

        return figure_obj

    except Exception as plotly_error:
        raise Exception_Configuration(
            f"Error creating returns distribution plot: {plotly_error}",
        ) from plotly_error


def create_plot_drawdowns_analysis(
    *, data_portfolio: pl.DataFrame | None, data_benchmark: pl.DataFrame | None, period_label: str, data_was_validated: bool = True, include_benchmark: bool = False) -> go.Figure:
    """Create drawdowns analysis plot."""
    if data_portfolio is None and data_benchmark is None:
        return create_error_figure(message_text = "No portfolio or benchmark data available")

    if not isinstance(period_label, str):
        period_label = str(period_label) if period_label is not None else "Unknown Period"

    has_portfolio_data = True
    has_benchmark_data = True
    public_utils_visuals = _public_utils_visuals_module()

    if not data_was_validated:
        has_portfolio_data, has_benchmark_data = (
            public_utils_visuals.validate_portfolio_and_benchmark_data_if_not_already_validated(
                data_portfolio=data_portfolio,
                data_benchmark=data_benchmark,
            )
        )

    if not has_portfolio_data and not has_benchmark_data:
        return create_error_figure(message_text = "Both portfolio and benchmark data are empty")

    try:
        figure_obj = go.Figure()

        if has_portfolio_data and data_portfolio is not None and not data_portfolio.is_empty():
            portfolio_returns = public_utils_visuals.calculate_portfolio_returns(data_portfolio = data_portfolio)
            if len(portfolio_returns) > 0:
                portfolio_returns_pandas = portfolio_returns.to_pandas()
                cum_rets = (1 + portfolio_returns_pandas).cumprod()
                peak_values = cum_rets.cummax()
                drawdown_values = (cum_rets / peak_values - 1) * 100

                assert data_portfolio is not None
                portfolio_sorted = data_portfolio.sort("Date")
                dates_list = portfolio_sorted.select("Date").to_series().to_list()

                if len(dates_list) > 1:  # pragma: no branch
                    dates_for_drawdowns = dates_list[1 : len(drawdown_values) + 1]

                    figure_obj.add_trace(
                        go.Scatter(
                            x=dates_for_drawdowns,
                            y=drawdown_values,
                            fill="tozeroy",
                            fillcolor="rgba(31, 119, 180, 0.3)",
                            line={"color": "#1f77b4", "width": 2},
                            name="Portfolio Drawdowns",
                            hovertemplate="Date: %{x}<br>Portfolio Drawdown: %{y:.2f}%<extra></extra>",
                        ),
                    )

        if (
            include_benchmark
            and has_benchmark_data
            and data_benchmark is not None
            and not data_benchmark.is_empty()
        ):
            benchmark_returns = public_utils_visuals.calculate_portfolio_returns(data_portfolio = data_benchmark)
            if len(benchmark_returns) > 0:
                benchmark_returns_pandas = benchmark_returns.to_pandas()
                cum_rets = (1 + benchmark_returns_pandas).cumprod()
                peak_values = cum_rets.cummax()
                drawdown_values = (cum_rets / peak_values - 1) * 100

                assert data_benchmark is not None
                benchmark_sorted = data_benchmark.sort("Date")
                dates_list = benchmark_sorted.select("Date").to_series().to_list()

                if len(dates_list) > 1:  # pragma: no branch
                    dates_for_drawdowns = dates_list[1 : len(drawdown_values) + 1]

                    figure_obj.add_trace(
                        go.Scatter(
                            x=dates_for_drawdowns,
                            y=drawdown_values,
                            fill="tozeroy",
                            fillcolor="rgba(255, 127, 14, 0.3)",
                            line={"color": "#ff7f0e", "width": 2, "dash": "dash"},
                            name="Benchmark Drawdowns",
                            hovertemplate="Date: %{x}<br>Benchmark Drawdown: %{y:.2f}%<extra></extra>",
                        ),
                    )

        figure_obj.update_layout(
            title={
                "text": f"Drawdowns Analysis ({period_label})",
                "font": {"size": 18},
                "x": 0.5,
                "xanchor": "center",
            },
            xaxis_title="Date",
            yaxis_title="Drawdown (%)",
            template="plotly_white",
            height=600,
            margin={"l": 60, "r": 60, "t": 120, "b": 60},
            hovermode="x unified",
            legend={
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "center",
                "x": 0.5,
            },
        )

        return figure_obj

    except Exception as plotly_error:
        raise Exception_Configuration(
            f"Error creating drawdowns plot: {plotly_error}",
        ) from plotly_error


def create_plot_comparison_portfolios(
    *, data_portfolio: pl.DataFrame | None, data_benchmark: pl.DataFrame | None, viz_type: str, show_diff: bool, period_label: str, start_date: date, end_date: date, data_was_validated: bool = True) -> go.Figure:
    """Generate the comparison plot figure using Polars DataFrames.

    Parameters
    ----------
    data_portfolio : polars.DataFrame
        Portfolio data with "Date" and "Value" columns
    data_benchmark : polars.DataFrame
        Benchmark data with "Date" and "Value" columns
    viz_type : str
        Visualization type ("normalized", "pct_change", "cum_return", "absolute")
    show_diff : bool
        Whether to show difference between portfolio and benchmark
    period_label : str
        Label for the time period
    start_date : datetime.date
        Start date for the period
    end_date : datetime.date
        End date for the period
    data_was_validated : bool, optional
        Whether data has already been validated, by default True

    Returns
    -------
    plotly.graph_objects.Figure
        Portfolio vs benchmark comparison plot

    Raises
    ------
    ValueError
        If data validation fails
    RuntimeError
        If plot creation fails
    """
    if data_portfolio is None and data_benchmark is None:
        return create_error_figure(message_text = "No portfolio or benchmark data available")

    _ = show_diff

    if not isinstance(period_label, str):
        period_label = str(period_label) if period_label is not None else "Unknown Period"

    if not isinstance(viz_type, str):
        viz_type = "normalized"

    has_portfolio_data = True
    has_benchmark_data = True
    public_utils_visuals = _public_utils_visuals_module()

    if not data_was_validated:
        has_portfolio_data, has_benchmark_data = (
            public_utils_visuals.validate_portfolio_and_benchmark_data_if_not_already_validated(
                data_portfolio=data_portfolio,
                data_benchmark=data_benchmark,
            )
        )

    if not has_portfolio_data and not has_benchmark_data:
        return create_error_figure(message_text = "Both portfolio and benchmark data are empty")

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

    try:
        if has_portfolio:
            data_portfolio = public_utils_visuals.downsample_dataframe(
                polars_DF = data_portfolio,
                max_points=200,
                date_column="Date",
            )

        if has_benchmark:
            data_benchmark = public_utils_visuals.downsample_dataframe(
                polars_DF = data_benchmark,
                max_points=200,
                date_column="Date",
            )

        figure_obj = go.Figure()

        if viz_type == "normalized":
            plot_title = f"Portfolio vs Benchmark - Normalized ({period_label})"
            y_title = "Normalized Value (Base=100)"
        elif viz_type == "pct_change":
            plot_title = f"Portfolio vs Benchmark - Daily Changes ({period_label})"
            y_title = "Daily Change (%)"
        elif viz_type == "cum_return":
            plot_title = f"Portfolio vs Benchmark - Cumulative Returns ({period_label})"
            y_title = "Cumulative Return (%)"
        else:
            plot_title = f"Portfolio vs Benchmark - Absolute Values ({period_label})"
            y_title = "Value"

        if has_portfolio:
            try:
                assert data_portfolio is not None
                portfolio_sorted = data_portfolio.sort("Date")

                date_dtype = portfolio_sorted.select("Date").dtypes[0]

                if date_dtype in [pl.Utf8, pl.String]:
                    portfolio_processed = portfolio_sorted.with_columns(
                        [
                            pl.col("Date").str.to_datetime(strict=False).alias("Date"),
                            pl.col("Value").cast(pl.Float64, strict=False).alias("Value"),
                        ],
                    )
                elif date_dtype == pl.Date:
                    portfolio_processed = portfolio_sorted.with_columns(
                        [
                            pl.col("Date").cast(pl.Datetime).alias("Date"),
                            pl.col("Value").cast(pl.Float64, strict=False).alias("Value"),
                        ],
                    )
                else:
                    portfolio_processed = portfolio_sorted.with_columns(
                        [
                            pl.col("Date").cast(pl.Datetime, strict=False).alias("Date"),
                            pl.col("Value").cast(pl.Float64, strict=False).alias("Value"),
                        ],
                    )

                portfolio_clean = portfolio_processed.filter(
                    pl.col("Date").is_not_null() & pl.col("Value").is_not_null(),
                )

                if portfolio_clean.height > 0:
                    portfolio_dates = portfolio_clean.select("Date").to_series().to_list()
                    portfolio_values = portfolio_clean.select("Value").to_series().to_list()

                    if viz_type == "normalized" and len(portfolio_values) > 0:
                        start_value = portfolio_values[0]
                        if start_value != 0:
                            y_values = [(value / start_value) * 100 for value in portfolio_values]
                        else:
                            y_values = portfolio_values
                    elif viz_type == "pct_change" and len(portfolio_values) > 1:
                        pct_change_series = (
                            portfolio_clean.select(
                                pl.col("Value").pct_change().alias("pct_change"),
                            ).to_series()
                            * 100
                        )
                        y_values = pct_change_series.drop_nulls().to_list()
                        portfolio_dates = (
                            portfolio_dates[1 : len(y_values) + 1]
                            if len(portfolio_dates) > 1
                            else portfolio_dates
                        )
                    elif viz_type == "cum_return" and len(portfolio_values) > 0:
                        start_value = portfolio_values[0]
                        if start_value != 0:
                            y_values = [
                                ((value / start_value) - 1) * 100 for value in portfolio_values
                            ]
                        else:
                            y_values = portfolio_values
                    else:
                        y_values = portfolio_values

                    if len(y_values) > 0 and len(portfolio_dates) >= len(y_values):  # pragma: no branch
                        figure_obj.add_trace(
                            go.Scatter(
                                x=portfolio_dates[: len(y_values)],
                                y=y_values,
                                mode="lines",
                                name="Portfolio",
                                line={"width": 2, "color": "#1f77b4"},
                                hovertemplate="<b>Portfolio</b><br>Date: %{x}<br>Value: %{y:.2f}<extra></extra>",
                            ),
                        )
            except Exception:  # pragma: no cover
                pass

        if has_benchmark:
            try:
                assert data_benchmark is not None
                benchmark_sorted = data_benchmark.sort("Date")

                date_dtype = benchmark_sorted.select("Date").dtypes[0]

                if date_dtype in [pl.Utf8, pl.String]:
                    benchmark_processed = benchmark_sorted.with_columns(
                        [
                            pl.col("Date").str.to_datetime(strict=False).alias("Date"),
                            pl.col("Value").cast(pl.Float64, strict=False).alias("Value"),
                        ],
                    )
                elif date_dtype == pl.Date:
                    benchmark_processed = benchmark_sorted.with_columns(
                        [
                            pl.col("Date").cast(pl.Datetime).alias("Date"),
                            pl.col("Value").cast(pl.Float64, strict=False).alias("Value"),
                        ],
                    )
                else:
                    benchmark_processed = benchmark_sorted.with_columns(
                        [
                            pl.col("Date").cast(pl.Datetime, strict=False).alias("Date"),
                            pl.col("Value").cast(pl.Float64, strict=False).alias("Value"),
                        ],
                    )

                benchmark_clean = benchmark_processed.filter(
                    pl.col("Date").is_not_null() & pl.col("Value").is_not_null(),
                )

                if benchmark_clean.height > 0:
                    benchmark_dates = benchmark_clean.select("Date").to_series().to_list()
                    benchmark_values = benchmark_clean.select("Value").to_series().to_list()

                    if viz_type == "normalized" and len(benchmark_values) > 0:
                        start_value = benchmark_values[0]
                        if start_value != 0:
                            y_values = [(value / start_value) * 100 for value in benchmark_values]
                        else:
                            y_values = benchmark_values
                    elif viz_type == "pct_change" and len(benchmark_values) > 1:
                        pct_change_series = (
                            benchmark_clean.select(
                                pl.col("Value").pct_change().alias("pct_change"),
                            ).to_series()
                            * 100
                        )
                        y_values = pct_change_series.drop_nulls().to_list()
                        benchmark_dates = (
                            benchmark_dates[1 : len(y_values) + 1]
                            if len(benchmark_dates) > 1
                            else benchmark_dates
                        )
                    elif viz_type == "cum_return" and len(benchmark_values) > 0:
                        start_value = benchmark_values[0]
                        if start_value != 0:
                            y_values = [
                                ((value / start_value) - 1) * 100 for value in benchmark_values
                            ]
                        else:
                            y_values = benchmark_values
                    else:
                        y_values = benchmark_values

                    if len(y_values) > 0 and len(benchmark_dates) >= len(y_values):  # pragma: no branch
                        figure_obj.add_trace(
                            go.Scatter(
                                x=benchmark_dates[: len(y_values)],
                                y=y_values,
                                mode="lines",
                                name="Benchmark",
                                line={"width": 2, "color": "#ff7f0e", "dash": "dash"},
                                hovertemplate="<b>Benchmark</b><br>Date: %{x}<br>Value: %{y:.2f}<extra></extra>",
                            ),
                        )
            except Exception:  # pragma: no cover
                pass

        if len(figure_obj.data) == 0:  # pyright: ignore[reportArgumentType]
            figure_obj.add_annotation(
                text=f"No data available for {period_label}<br>{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font={"size": 16},
                align="center",
            )

        figure_obj.update_layout(
            title={
                "text": plot_title,
                "font": {"size": 16},
                "x": 0.5,
                "xanchor": "center",
            },
            xaxis_title="Date",
            yaxis_title=y_title,
            template="plotly_white",
            height=600,
            margin={"l": 60, "r": 40, "t": 80, "b": 60},
            legend={
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "center",
                "x": 0.5,
            },
            hovermode="x unified",
        )

        return figure_obj

    except Exception as exc:  # pragma: no cover
        raise Exception_Configuration(f"Error generating comparison plot: {exc}") from exc


__all__ = [
    "create_plot_comparison_portfolios",
    "create_plot_drawdowns_analysis",
    "create_plot_portfolios_comparison",
    "create_plot_returns_distribution",
    "create_plot_rolling_statistics",
]

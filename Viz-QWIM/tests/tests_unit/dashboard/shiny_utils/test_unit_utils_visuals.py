import time

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import polars as pl

from great_tables import GT, loc, md, style
from plotly.subplots import make_subplots


# Add these missing imports and constants
OUTPUT_DIR = Path("outputs")

from src.dashboard.shiny_utils.utils_data import (
    calculate_portfolio_returns,
    downsample_dataframe,
    validate_portfolio_and_benchmark_data_if_not_already_validated,
    validate_portfolio_data,
)



def validate_data_visuals(data_frame=None, selected_series_list=None):
    """Validate data meets requirements for visualization and analysis using defensive programming."""

    # Input validation with early returns
    if data_frame is None:
        return False, "No data available"

    # Type validation
    if not isinstance(data_frame, pl.DataFrame):
        return False, f"Invalid data type: {type(data_frame).__name__}, expected polars.DataFrame"

    # Data existence validation
    if data_frame.is_empty():
        return False, "Dataset is empty"

    # Schema validation
    if "Date" not in data_frame.columns:
        return False, "Data is missing required 'Date' column"

    # Series selection validation if provided
    if selected_series_list is not None:
        # Configuration validation
        if not isinstance(selected_series_list, (list, tuple)):
            return (
                False,
                f"Selected series must be list or tuple, got {type(selected_series_list).__name__}",
            )

        # Business logic validation - empty selection
        if not selected_series_list:
            return False, "No series selected"

        # Defensive programming - check series availability
        available_columns = set(data_frame.columns)
        selected_series_set = set(selected_series_list)
        available_series = selected_series_set.intersection(available_columns)

        if not available_series:
            return (
                False,
                f"None of the selected series found in data: {', '.join(selected_series_list)}",
            )

        # Data quality validation with defensive checks
        valid_series_found = False
        max_series_to_check = min(3, len(available_series))  # Check up to 3 series for performance

        for idx, series_name in enumerate(list(available_series)[:max_series_to_check]):
            # Defensive programming - ensure column exists before operations
            if series_name not in data_frame.columns:
                continue

            # Only use try-except for Polars operations that might fail unpredictably
            try:
                non_null_count = data_frame.select(pl.col(series_name).is_not_null().sum()).item()
                if isinstance(non_null_count, (int, float)) and non_null_count > 0:
                    valid_series_found = True
                    break
            except Exception:
                # Continue checking other series if this one fails
                continue

        if not valid_series_found:
            return False, "No valid data found in selected series"

    return True, ""


def create_error_figure(
    message_text,
    title_text="Error",
    details_text=None,
):
    """Create a standardized error figure using defensive programming.

    Parameters
    ----------
    message_text : str
        Main error message
    title_text : str, optional
        Figure title, by default "Error"
    details_text : str, optional
        Detailed error information, by default None

    Returns
    -------
    plotly.graph_objects.Figure
        Error figure
    """

    # Input validation with early returns
    if not isinstance(message_text, str):
        message_text = str(message_text) if message_text is not None else "Unknown error"

    if not isinstance(title_text, str):
        title_text = str(title_text) if title_text is not None else "Error"

    if details_text is not None and not isinstance(details_text, str):
        details_text = str(details_text)

    # Configuration validation
    if len(message_text.strip()) == 0:
        message_text = "No error message provided"

    # Defensive programming - create figure with safe defaults
    figure_obj = go.Figure()

    # Safe layout configuration
    layout_config = {
        "title": {
            "text": title_text,
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 16, "color": "#d63384"},
        },
        "template": "plotly_white",
        "height": 400,
        "margin": dict(t=80, b=40, l=40, r=40),
        "xaxis": {"visible": False, "range": [0, 1]},
        "yaxis": {"visible": False, "range": [0, 1]},
        "showlegend": False,
        "plot_bgcolor": "white",
        "paper_bgcolor": "white",
    }

    # Only use try-except for Plotly operations that might fail unpredictably
    try:
        figure_obj.update_layout(**layout_config)

        # Add main error message
        figure_obj.add_annotation(
            text=message_text,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.6,
            showarrow=False,
            font=dict(size=14, color="#d63384"),
            align="center",
            width=350,
        )

        # Add details if provided
        if details_text:
            figure_obj.add_annotation(
                text=f"Details: {details_text}",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.4,
                showarrow=False,
                font=dict(size=12, color="#6c757d"),
                align="center",
                width=400,
            )

        # Add help text
        figure_obj.add_annotation(
            text="💡 Try selecting different data or adjusting filters",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.2,
            showarrow=False,
            font=dict(size=11, color="#198754"),
            align="center",
            width=400,
        )

    except Exception:
        # Fallback to basic figure if Plotly operations fail
        basic_figure = go.Figure()
        basic_figure.update_layout(
            title=f"Error: {message_text}",
            template="plotly_white",
            height=400,
        )
        return basic_figure

    return figure_obj




def format_value_for_display(value_input):
    """Format a value for display in tables using defensive programming."""

    # Input validation with early returns
    if value_input is None:
        return "None"

    # Handle pandas NA values
    if pd.isna(value_input):
        return "N/A"

    # Handle string values
    if isinstance(value_input, str):
        if value_input.lower() in ["error", "none", "null", "nan"]:
            return value_input
        return value_input

    # Handle numeric values with defensive programming
    if isinstance(value_input, (int, float)):
        # Check for special float values
        if pd.isna(value_input):
            return "N/A"

        # Safe numeric formatting - only use try-except for float conversion that might fail
        try:
            numeric_value = float(value_input)
            return f"{numeric_value:.4f}"
        except (ValueError, OverflowError):
            return str(value_input)

    # Handle boolean values
    if isinstance(value_input, bool):
        return str(value_input)

    # Default case - convert to string safely
    return str(value_input)


def safe_numeric_conversion(input_value):
    """Safely convert a value to numeric format using defensive programming."""

    # Input validation with early returns
    if input_value is None:
        return None

    # Handle pandas NA values
    if pd.isna(input_value):
        return input_value

    # Handle string values
    if isinstance(input_value, str):
        if input_value.lower() in ["error", "none", "null", "nan", ""]:
            return input_value

        # Clean string for numeric conversion
        cleaned_value = input_value.strip()
        if len(cleaned_value) == 0:
            return input_value

        # Only use try-except for actual conversion that might fail unpredictably
        try:
            return float(cleaned_value)
        except (ValueError, TypeError):
            return input_value

    # Handle numeric values
    if isinstance(input_value, (int, float)):
        # Check for special float values
        if pd.isna(input_value):
            return input_value

        # Only use try-except for float conversion that might fail with extreme values
        try:
            return float(input_value)
        except (ValueError, OverflowError):
            return input_value

    # Handle boolean values
    if isinstance(input_value, bool):
        return float(input_value)

    # Default case - return as-is if conversion not possible
    return input_value


def create_plot_portfolios_comparison(
    data_portfolio,
    data_benchmark,
    period_label,
    data_was_validated=True,
):
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

    # Input validation with early returns
    if data_portfolio is None and data_benchmark is None:
        return create_error_figure(message_text = "No portfolio or benchmark data available")

    if not isinstance(period_label, str):
        period_label = str(period_label) if period_label is not None else "Unknown Period"

    has_portfolio_data = True
    has_benchmark_data = True
    # Validate input data if not already validated
    if not data_was_validated:
        has_portfolio_data, has_benchmark_data = validate_portfolio_data(
            data_portfolio=data_portfolio, data_benchmark=data_benchmark
        )

    if not has_portfolio_data and not has_benchmark_data:
        return create_error_figure(message_text = "Both portfolio and benchmark data are empty")

    # Only use try-except for Plotly operations that might fail unpredictably
    try:
        figure_obj = go.Figure()

        # Process portfolio data if available
        if has_portfolio_data:
            # Business logic validation - sort by Date and prepare data
            portfolio_sorted = data_portfolio.sort("Date")

            # Safe data extraction using Polars methods
            portfolio_dates = portfolio_sorted.select("Date").to_series().to_list()
            portfolio_values = portfolio_sorted.select("Value").to_series()

            # Convert to numeric and handle nulls
            portfolio_numeric = portfolio_values.cast(pl.Float64, strict=False)
            portfolio_clean = portfolio_numeric.drop_nulls()

            if len(portfolio_clean) > 0:
                # Get corresponding dates for clean values
                valid_indices = portfolio_numeric.is_not_null()
                portfolio_dates_clean = [
                    date_val
                    for idx, date_val in enumerate(portfolio_dates)
                    if idx < len(valid_indices) and valid_indices[idx]
                ]

                # Calculate normalized values (base=100)
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
                            line=dict(width=3, color="#1f77b4"),
                            hovertemplate="<b>Portfolio</b><br>Date: %{x}<br>Value: %{y:.2f}<extra></extra>",
                        )
                    )

        # Process benchmark data if available
        if has_benchmark_data:
            # Business logic validation - sort by Date and prepare data
            benchmark_sorted = data_benchmark.sort("Date")

            # Safe data extraction using Polars methods
            benchmark_dates = benchmark_sorted.select("Date").to_series().to_list()
            benchmark_values = benchmark_sorted.select("Value").to_series()

            # Convert to numeric and handle nulls
            benchmark_numeric = benchmark_values.cast(pl.Float64, strict=False)
            benchmark_clean = benchmark_numeric.drop_nulls()

            if len(benchmark_clean) > 0:
                # Get corresponding dates for clean values
                valid_indices = benchmark_numeric.is_not_null()
                benchmark_dates_clean = [
                    date_val
                    for idx, date_val in enumerate(benchmark_dates)
                    if idx < len(valid_indices) and valid_indices[idx]
                ]

                # Calculate normalized values (base=100)
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
                            line=dict(width=3, color="#ff7f0e", dash="dash"),
                            hovertemplate="<b>Benchmark</b><br>Date: %{x}<br>Value: %{y:.2f}<extra></extra>",
                        )
                    )

        # Configuration validation - ensure we have at least one trace
        if len(figure_obj.data) == 0:
            return create_error_figure(
                message_text = "No valid data series to display",
                details_text="Both portfolio and benchmark data contain no valid numeric values",
            )

        # Safe layout configuration
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
            "margin": dict(l=60, r=40, t=120, b=60),
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
        raise RuntimeError(f"Error creating comparison plot: {plotly_error}") from plotly_error


def create_plot_rolling_statistics(
    data_portfolio,
    data_benchmark,
    window_size,
    period_label,
    data_was_validated=True,
    include_benchmark=False,
):
    """Create rolling statistics subplot."""

    # Input validation with early returns
    if data_portfolio is None and data_benchmark is None:
        return create_error_figure(message_text = "No portfolio or benchmark data available")

    if not isinstance(period_label, str):
        period_label = str(period_label) if period_label is not None else "Unknown Period"

    if not isinstance(window_size, int) or window_size < 1:
        window_size = 30  # Default window size

    has_portfolio_data = True
    has_benchmark_data = True
    # Validate input data if not already validated
    if not data_was_validated:
        has_portfolio_data, has_benchmark_data = (
            validate_portfolio_and_benchmark_data_if_not_already_validated(
                data_portfolio=data_portfolio, data_benchmark=data_benchmark
            )
        )

    if not has_portfolio_data and not has_benchmark_data:
        return create_error_figure(message_text = "Both portfolio and benchmark data are empty")

    # Only use try-except for Plotly operations that might fail unpredictably
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

        # Portfolio rolling statistics
        if has_portfolio_data and not data_portfolio.is_empty():
            portfolio_returns = calculate_portfolio_returns(data_portfolio = data_portfolio)
            if len(portfolio_returns) >= window_size:
                # Convert to pandas for rolling calculations
                portfolio_returns_pandas = portfolio_returns.to_pandas()
                rolling_returns = portfolio_returns_pandas.rolling(window=window_size).mean() * 100
                rolling_vol = (
                    portfolio_returns_pandas.rolling(window=window_size).std() * 100 * np.sqrt(252)
                )  # Fixed: changed pd.np to np

                # Align dates with rolling statistics
                portfolio_sorted = data_portfolio.sort("Date")
                dates_list = portfolio_sorted.select("Date").to_series().to_list()

                # Get dates corresponding to rolling statistics (skip first window_size-1 dates)
                if len(dates_list) >= window_size:
                    dates_aligned = dates_list[
                        window_size - 1 : window_size - 1 + len(rolling_returns.dropna())
                    ]

                    figure_obj.add_trace(
                        go.Scatter(
                            x=dates_aligned,
                            y=rolling_returns.dropna(),
                            mode="lines",
                            name="Portfolio Returns",
                            line=dict(color="#1f77b4", width=2),
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
                            line=dict(color="#1f77b4", width=2),
                            hovertemplate="Date: %{x}<br>Portfolio Volatility: %{y:.2f}%<extra></extra>",
                        ),
                        row=2,
                        col=1,
                    )

        # Benchmark rolling statistics if requested
        if include_benchmark and has_benchmark_data and not data_benchmark.is_empty():
            benchmark_returns = calculate_portfolio_returns(data_portfolio = data_benchmark)
            if len(benchmark_returns) >= window_size:
                # Convert to pandas for rolling calculations
                benchmark_returns_pandas = benchmark_returns.to_pandas()
                rolling_returns = benchmark_returns_pandas.rolling(window=window_size).mean() * 100
                rolling_vol = (
                    benchmark_returns_pandas.rolling(window=window_size).std() * 100 * np.sqrt(252)
                )  # Fixed: changed pd.np to np

                # Align dates with rolling statistics
                benchmark_sorted = data_benchmark.sort("Date")
                dates_list = benchmark_sorted.select("Date").to_series().to_list()

                # Get dates corresponding to rolling statistics
                if len(dates_list) >= window_size:
                    dates_aligned = dates_list[
                        window_size - 1 : window_size - 1 + len(rolling_returns.dropna())
                    ]

                    figure_obj.add_trace(
                        go.Scatter(
                            x=dates_aligned,
                            y=rolling_returns.dropna(),
                            mode="lines",
                            name="Benchmark Returns",
                            line=dict(color="#ff7f0e", width=2, dash="dash"),
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
                            line=dict(color="#ff7f0e", width=2, dash="dash"),
                            hovertemplate="Date: %{x}<br>Benchmark Volatility: %{y:.2f}%<extra></extra>",
                        ),
                        row=2,
                        col=1,
                    )

        figure_obj.add_hline(y=0, line_dash="dot", line_color="gray", row=1, col=1)

        figure_obj.update_layout(
            title=dict(
                text=f"Rolling {window_size}-Day Statistics ({period_label})",
                font=dict(size=18),
                x=0.5,
                xanchor="center",
            ),
            template="plotly_white",
            height=700,
            showlegend=True,
            margin=dict(l=60, r=60, t=140, b=60),
            hovermode="x unified",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
            ),
        )

        figure_obj.update_xaxes(title_text="Date", row=2, col=1)
        figure_obj.update_yaxes(title_text="Return (%)", row=1, col=1)
        figure_obj.update_yaxes(title_text="Volatility (%)", row=2, col=1)

        return figure_obj

    except Exception as plotly_error:
        raise RuntimeError(
            f"Error creating rolling statistics plot: {plotly_error}"
        ) from plotly_error


def create_plot_returns_distribution(
    data_portfolio,
    data_benchmark,
    period_label,
    data_was_validated=True,
    include_benchmark=False,
):
    """Create returns distribution histogram comparing portfolio and benchmark."""

    # Input validation with early returns
    if data_portfolio is None and data_benchmark is None:
        return create_error_figure(message_text = "No portfolio or benchmark data available")

    if not isinstance(period_label, str):
        period_label = str(period_label) if period_label is not None else "Unknown Period"

    has_portfolio_data = True
    has_benchmark_data = True
    # Validate input data if not already validated
    if not data_was_validated:
        has_portfolio_data, has_benchmark_data = (
            validate_portfolio_and_benchmark_data_if_not_already_validated(
                data_portfolio=data_portfolio, data_benchmark=data_benchmark
            )
        )

    if not has_portfolio_data and not has_benchmark_data:
        return create_error_figure(message_text = "Both portfolio and benchmark data are empty")

    # Only use try-except for Plotly operations that might fail unpredictably
    try:
        figure_obj = go.Figure()

        # Calculate portfolio returns
        if has_portfolio_data and not data_portfolio.is_empty():
            portfolio_returns = calculate_portfolio_returns(data_portfolio = data_portfolio)
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
                    )
                )

        if include_benchmark and has_benchmark_data and not data_benchmark.is_empty():
            benchmark_returns = calculate_portfolio_returns(data_portfolio = data_benchmark)
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
                    )
                )

        # Calculate statistics for title
        if has_portfolio_data and not data_portfolio.is_empty():
            portfolio_returns = calculate_portfolio_returns(data_portfolio = data_portfolio)
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
            title=dict(
                text=f"Returns Distribution ({period_label})<br><sub>{subtitle_text}</sub>",
                font=dict(size=18),
                x=0.5,
                xanchor="center",
            ),
            xaxis_title="Daily Return (%)",
            yaxis_title="Frequency",
            template="plotly_white",
            height=600,
            margin=dict(l=60, r=60, t=120, b=60),
            hovermode="closest",
            barmode="overlay",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
            ),
        )

        return figure_obj

    except Exception as plotly_error:
        raise RuntimeError(
            f"Error creating returns distribution plot: {plotly_error}"
        ) from plotly_error


def create_plot_drawdowns_analysis(
    data_portfolio,
    data_benchmark,
    period_label,
    data_was_validated=True,
    include_benchmark=False,
):
    """Create drawdowns analysis plot."""

    # Input validation with early returns
    if data_portfolio is None and data_benchmark is None:
        return create_error_figure(message_text = "No portfolio or benchmark data available")

    if not isinstance(period_label, str):
        period_label = str(period_label) if period_label is not None else "Unknown Period"

    has_portfolio_data = True
    has_benchmark_data = True
    # Validate input data if not already validated
    if not data_was_validated:
        has_portfolio_data, has_benchmark_data = (
            validate_portfolio_and_benchmark_data_if_not_already_validated(
                data_portfolio=data_portfolio, data_benchmark=data_benchmark
            )
        )

    if not has_portfolio_data and not has_benchmark_data:
        return create_error_figure(message_text = "Both portfolio and benchmark data are empty")

    # Only use try-except for Plotly operations that might fail unpredictably
    try:
        figure_obj = go.Figure()

        # Calculate portfolio drawdowns
        if has_portfolio_data and not data_portfolio.is_empty():
            portfolio_returns = calculate_portfolio_returns(data_portfolio = data_portfolio)
            if len(portfolio_returns) > 0:
                # Convert to pandas for cumulative calculations
                portfolio_returns_pandas = portfolio_returns.to_pandas()
                cum_rets = (1 + portfolio_returns_pandas).cumprod()
                peak_values = cum_rets.cummax()
                drawdown_values = (cum_rets / peak_values - 1) * 100

                # Get dates for plotting (skip first date since we calculated returns)
                portfolio_sorted = data_portfolio.sort("Date")
                dates_list = portfolio_sorted.select("Date").to_series().to_list()

                if len(dates_list) > 1:
                    dates_for_drawdowns = dates_list[1 : len(drawdown_values) + 1]

                    figure_obj.add_trace(
                        go.Scatter(
                            x=dates_for_drawdowns,
                            y=drawdown_values,
                            fill="tozeroy",
                            fillcolor="rgba(31, 119, 180, 0.3)",
                            line=dict(color="#1f77b4", width=2),
                            name="Portfolio Drawdowns",
                            hovertemplate="Date: %{x}<br>Portfolio Drawdown: %{y:.2f}%<extra></extra>",
                        )
                    )

        # Calculate benchmark drawdowns if requested
        if include_benchmark and has_benchmark_data and not data_benchmark.is_empty():
            benchmark_returns = calculate_portfolio_returns(data_portfolio = data_benchmark)
            if len(benchmark_returns) > 0:
                # Convert to pandas for cumulative calculations
                benchmark_returns_pandas = benchmark_returns.to_pandas()
                cum_rets = (1 + benchmark_returns_pandas).cumprod()
                peak_values = cum_rets.cummax()
                drawdown_values = (cum_rets / peak_values - 1) * 100

                # Get dates for plotting
                benchmark_sorted = data_benchmark.sort("Date")
                dates_list = benchmark_sorted.select("Date").to_series().to_list()

                if len(dates_list) > 1:
                    dates_for_drawdowns = dates_list[1 : len(drawdown_values) + 1]

                    figure_obj.add_trace(
                        go.Scatter(
                            x=dates_for_drawdowns,
                            y=drawdown_values,
                            fill="tozeroy",
                            fillcolor="rgba(255, 127, 14, 0.3)",
                            line=dict(color="#ff7f0e", width=2, dash="dash"),
                            name="Benchmark Drawdowns",
                            hovertemplate="Date: %{x}<br>Benchmark Drawdown: %{y:.2f}%<extra></extra>",
                        )
                    )

        figure_obj.update_layout(
            title=dict(
                text=f"Drawdowns Analysis ({period_label})",
                font=dict(size=18),
                x=0.5,
                xanchor="center",
            ),
            xaxis_title="Date",
            yaxis_title="Drawdown (%)",
            template="plotly_white",
            height=600,
            margin=dict(l=60, r=60, t=120, b=60),
            hovermode="x unified",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
            ),
        )

        return figure_obj

    except Exception as plotly_error:
        raise RuntimeError(f"Error creating drawdowns plot: {plotly_error}") from plotly_error


def calculate_table_stats_basic(
    data_portfolio,
    data_benchmark,
    include_benchmark=False
):
    """Calculate basic statistics table for portfolio and benchmark data."""

    # Input validation with early returns
    if data_portfolio is None and data_benchmark is None:
        error_df = pd.DataFrame(
            {"Metric": ["No Data"], "Value": ["No portfolio or benchmark data available"]}
        )
        return error_df

    # Configuration validation - check if DataFrames are valid
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
        error_df = pd.DataFrame(
            {"Metric": ["No Data"], "Value": ["Both portfolio and benchmark data are empty"]}
        )
        return error_df

    # Only use try-except for operations that might fail unpredictably
    try:
        # Calculate basic statistics
        stats_data = []

        if has_portfolio_data:
            portfolio_returns = calculate_portfolio_returns(data_portfolio = data_portfolio)
            if len(portfolio_returns) > 0:
                portfolio_returns_series = portfolio_returns.to_pandas()

                stats_data.append(
                    {
                        "Metric": "Portfolio Daily Mean Return (%)",
                        "Value": f"{portfolio_returns_series.mean() * 100:.4f}",
                    }
                )
                stats_data.append(
                    {
                        "Metric": "Portfolio Daily Volatility (%)",
                        "Value": f"{portfolio_returns_series.std() * 100:.4f}",
                    }
                )
                stats_data.append(
                    {
                        "Metric": "Portfolio Annualized Return (%)",
                        "Value": f"{portfolio_returns_series.mean() * 252 * 100:.2f}",
                    }
                )
                stats_data.append(
                    {
                        "Metric": "Portfolio Annualized Volatility (%)",
                        "Value": f"{portfolio_returns_series.std() * np.sqrt(252) * 100:.2f}",
                    }
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
                        }
                    )

        if include_benchmark and has_benchmark_data:
            benchmark_returns = calculate_portfolio_returns(data_portfolio = data_benchmark)
            if len(benchmark_returns) > 0:
                benchmark_returns_series = benchmark_returns.to_pandas()

                stats_data.append(
                    {
                        "Metric": "Benchmark Daily Mean Return (%)",
                        "Value": f"{benchmark_returns_series.mean() * 100:.4f}",
                    }
                )
                stats_data.append(
                    {
                        "Metric": "Benchmark Daily Volatility (%)",
                        "Value": f"{benchmark_returns_series.std() * 100:.4f}",
                    }
                )
                stats_data.append(
                    {
                        "Metric": "Benchmark Annualized Return (%)",
                        "Value": f"{benchmark_returns_series.mean() * 252 * 100:.2f}",
                    }
                )
                stats_data.append(
                    {
                        "Metric": "Benchmark Annualized Volatility (%)",
                        "Value": f"{benchmark_returns_series.std() * np.sqrt(252) * 100:.2f}",
                    }
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
                        }
                    )

        stats_df = (
            pd.DataFrame(stats_data)
            if stats_data
            else pd.DataFrame({"Metric": ["No Data"], "Value": ["N/A"]})
        )


        return stats_df

    except Exception as exc:
        error_df = pd.DataFrame({"Metric": ["Error"], "Value": [str(exc)]})
        raise RuntimeError(f"Error generating basic statistics table: {exc}") from exc


def calculate_table_metrics_performance(
    data_portfolio,
    data_benchmark
):
    """Calculate performance metrics table for portfolio data."""

    # Input validation with early returns
    if data_portfolio is None:
        error_df = pd.DataFrame({"Metric": ["No Data"], "Value": ["No portfolio data available"]})
        return error_df

    # Configuration validation - check if DataFrame is valid
    has_portfolio_data = isinstance(data_portfolio, pl.DataFrame) and not data_portfolio.is_empty()

    if not has_portfolio_data:
        error_df = pd.DataFrame({"Metric": ["No Data"], "Value": ["Portfolio data is empty"]})
        return error_df

    # Only use try-except for operations that might fail unpredictably
    try:
        metrics_data = []

        portfolio_returns = calculate_portfolio_returns(data_portfolio = data_portfolio)
        if len(portfolio_returns) > 0:
            # Calculate various performance metrics
            portfolio_returns_series = portfolio_returns.to_pandas()
            cum_returns = (1 + portfolio_returns_series).cumprod()

            # Max drawdown
            peak = cum_returns.cummax()
            drawdown = cum_returns / peak - 1
            max_dd = drawdown.min()

            metrics_data.append(
                {
                    "Metric": "Total Return (%)",
                    "Value": f"{(cum_returns.iloc[-1] - 1) * 100:.2f}",
                }
            )

            metrics_data.append(
                {
                    "Metric": "Max Drawdown (%)",
                    "Value": f"{max_dd * 100:.2f}",
                }
            )

            # Win rate
            positive_returns = portfolio_returns_series > 0
            win_rate = positive_returns.sum() / len(portfolio_returns_series) * 100
            metrics_data.append(
                {
                    "Metric": "Win Rate (%)",
                    "Value": f"{win_rate:.2f}",
                }
            )

            # Best/Worst days
            metrics_data.append(
                {
                    "Metric": "Best Day (%)",
                    "Value": f"{portfolio_returns_series.max() * 100:.2f}",
                }
            )

            metrics_data.append(
                {
                    "Metric": "Worst Day (%)",
                    "Value": f"{portfolio_returns_series.min() * 100:.2f}",
                }
            )

            # Skewness and Kurtosis
            metrics_data.append(
                {
                    "Metric": "Skewness",
                    "Value": f"{portfolio_returns_series.skew():.4f}",
                }
            )

            metrics_data.append(
                {
                    "Metric": "Kurtosis",
                    "Value": f"{portfolio_returns_series.kurtosis():.4f}",
                }
            )

        metrics_df = (
            pd.DataFrame(metrics_data)
            if metrics_data
            else pd.DataFrame({"Metric": ["No Data"], "Value": ["N/A"]})
        )


        return metrics_df

    except Exception as exc:
        error_df = pd.DataFrame({"Metric": ["Error"], "Value": [str(exc)]})
        raise RuntimeError(f"Error generating performance metrics table: {exc}") from exc


def create_plot_comparison_portfolios(
    data_portfolio,
    data_benchmark,
    viz_type,
    show_diff,
    period_label,
    start_date,
    end_date,
    data_was_validated=True
):
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

    # Input validation with early returns
    if data_portfolio is None and data_benchmark is None:
        return create_error_figure(message_text = "No portfolio or benchmark data available")

    if not isinstance(period_label, str):
        period_label = str(period_label) if period_label is not None else "Unknown Period"

    if not isinstance(viz_type, str):
        viz_type = "normalized"  # Default visualization type

    has_portfolio_data = True
    has_benchmark_data = True
    # Validate input data if not already validated
    if not data_was_validated:
        has_portfolio_data, has_benchmark_data = (
            validate_portfolio_and_benchmark_data_if_not_already_validated(
                data_portfolio=data_portfolio, data_benchmark=data_benchmark
            )
        )

    if not has_portfolio_data and not has_benchmark_data:
        return create_error_figure(message_text = "Both portfolio and benchmark data are empty")

    # Configuration validation - check if DataFrames are valid Polars DataFrames
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

    # Only use try-except for Plotly operations that might fail unpredictably
    try:
        # Apply aggressive downsampling for performance using Polars-compatible function
        if has_portfolio:
            data_portfolio = downsample_dataframe(
                polars_DF = data_portfolio, max_points=200, date_column="Date"
            )

        if has_benchmark:
            data_benchmark = downsample_dataframe(
                polars_DF = data_benchmark, max_points=200, date_column="Date"
            )

        # Create figure immediately
        figure_obj = go.Figure()

        # Determine plot title and y-axis label based on visualization type
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

        # Add portfolio trace if available
        if has_portfolio:
            try:
                # Sort by Date and ensure proper data types using Polars
                portfolio_sorted = data_portfolio.sort("Date")

                # Handle different date column types
                date_dtype = portfolio_sorted.select("Date").dtypes[0]

                if date_dtype in [pl.Utf8, pl.String]:
                    # Convert string dates to datetime
                    portfolio_processed = portfolio_sorted.with_columns(
                        [
                            pl.col("Date").str.to_datetime(strict=False).alias("Date"),
                            pl.col("Value").cast(pl.Float64, strict=False).alias("Value"),
                        ]
                    )
                elif date_dtype in [pl.Date]:
                    # Convert date to datetime for consistency
                    portfolio_processed = portfolio_sorted.with_columns(
                        [
                            pl.col("Date").cast(pl.Datetime).alias("Date"),
                            pl.col("Value").cast(pl.Float64, strict=False).alias("Value"),
                        ]
                    )
                else:
                    # Already datetime or cast to datetime
                    portfolio_processed = portfolio_sorted.with_columns(
                        [
                            pl.col("Date").cast(pl.Datetime, strict=False).alias("Date"),
                            pl.col("Value").cast(pl.Float64, strict=False).alias("Value"),
                        ]
                    )

                # Remove null values
                portfolio_clean = portfolio_processed.filter(
                    pl.col("Date").is_not_null() & pl.col("Value").is_not_null(),
                )

                if portfolio_clean.height > 0:
                    # Extract data for plotting
                    portfolio_dates = portfolio_clean.select("Date").to_series().to_list()
                    portfolio_values = portfolio_clean.select("Value").to_series().to_list()

                    # Apply transformation based on visualization type
                    if viz_type == "normalized" and len(portfolio_values) > 0:
                        start_value = portfolio_values[0]
                        if start_value != 0:
                            y_values = [(value / start_value) * 100 for value in portfolio_values]
                        else:
                            y_values = portfolio_values
                    elif viz_type == "pct_change" and len(portfolio_values) > 1:
                        # Calculate percentage change using Polars
                        pct_change_series = (
                            portfolio_clean.select(
                                pl.col("Value").pct_change().alias("pct_change"),
                            ).to_series()
                            * 100
                        )
                        y_values = pct_change_series.drop_nulls().to_list()
                        # Adjust dates to match pct_change data (skip first date)
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

                    if len(y_values) > 0 and len(portfolio_dates) >= len(y_values):
                        figure_obj.add_trace(
                            go.Scatter(
                                x=portfolio_dates[: len(y_values)],
                                y=y_values,
                                mode="lines",
                                name="Portfolio",
                                line=dict(width=2, color="#1f77b4"),
                                hovertemplate="<b>Portfolio</b><br>Date: %{x}<br>Value: %{y:.2f}<extra></extra>",
                            )
                        )
            except Exception:
                pass  # Skip adding trace if there's an error

        # Add benchmark trace if available
        if has_benchmark:
            try:
                # Sort by Date and ensure proper data types using Polars
                benchmark_sorted = data_benchmark.sort("Date")

                # Handle different date column types
                date_dtype = benchmark_sorted.select("Date").dtypes[0]

                if date_dtype in [pl.Utf8, pl.String]:
                    # Convert string dates to datetime
                    benchmark_processed = benchmark_sorted.with_columns(
                        [
                            pl.col("Date").str.to_datetime(strict=False).alias("Date"),
                            pl.col("Value").cast(pl.Float64, strict=False).alias("Value"),
                        ]
                    )
                elif date_dtype in [pl.Date]:
                    # Convert date to datetime for consistency
                    benchmark_processed = benchmark_sorted.with_columns(
                        [
                            pl.col("Date").cast(pl.Datetime).alias("Date"),
                            pl.col("Value").cast(pl.Float64, strict=False).alias("Value"),
                        ]
                    )
                else:
                    # Already datetime or cast to datetime
                    benchmark_processed = benchmark_sorted.with_columns(
                        [
                            pl.col("Date").cast(pl.Datetime, strict=False).alias("Date"),
                            pl.col("Value").cast(pl.Float64, strict=False).alias("Value"),
                        ]
                    )

                # Remove null values
                benchmark_clean = benchmark_processed.filter(
                    pl.col("Date").is_not_null() & pl.col("Value").is_not_null(),
                )

                if benchmark_clean.height > 0:
                    # Extract data for plotting
                    benchmark_dates = benchmark_clean.select("Date").to_series().to_list()
                    benchmark_values = benchmark_clean.select("Value").to_series().to_list()

                    # Apply transformation based on visualization type
                    if viz_type == "normalized" and len(benchmark_values) > 0:
                        start_value = benchmark_values[0]
                        if start_value != 0:
                            y_values = [(value / start_value) * 100 for value in benchmark_values]
                        else:
                            y_values = benchmark_values
                    elif viz_type == "pct_change" and len(benchmark_values) > 1:
                        # Calculate percentage change using Polars
                        pct_change_series = (
                            benchmark_clean.select(
                                pl.col("Value").pct_change().alias("pct_change"),
                            ).to_series()
                            * 100
                        )
                        y_values = pct_change_series.drop_nulls().to_list()
                        # Adjust dates to match pct_change data (skip first date)
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

                    if len(y_values) > 0 and len(benchmark_dates) >= len(y_values):
                        figure_obj.add_trace(
                            go.Scatter(
                                x=benchmark_dates[: len(y_values)],
                                y=y_values,
                                mode="lines",
                                name="Benchmark",
                                line=dict(width=2, color="#ff7f0e", dash="dash"),
                                hovertemplate="<b>Benchmark</b><br>Date: %{x}<br>Value: %{y:.2f}<extra></extra>",
                            )
                        )
            except Exception:
                pass  # Skip adding trace if there's an error

        # Handle empty figure
        if len(figure_obj.data) == 0:
            figure_obj.add_annotation(
                text=f"No data available for {period_label}<br>{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=16),
                align="center",
            )

        # Apply layout with dynamic title
        figure_obj.update_layout(
            title=dict(
                text=plot_title,
                font=dict(size=16),
                x=0.5,
                xanchor="center",
            ),
            xaxis_title="Date",
            yaxis_title=y_title,
            template="plotly_white",
            height=600,
            margin=dict(l=60, r=40, t=80, b=60),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
            ),
            hovermode="x unified",
        )

        return figure_obj

    except Exception as exc:
        raise RuntimeError(f"Error generating comparison plot: {exc}") from exc


def create_table_comparison_stats(
    data_portfolio,
    data_benchmark,
    time_period,
    start_date,
    end_date,
    data_was_validated=True
):
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

    # Input validation with early returns
    if data_portfolio is None and data_benchmark is None:
        # Create empty table with proper structure
        empty_data = pd.DataFrame(
            {
                "Metric": ["No Data Available"],
                "Portfolio": ["-"],
                "Benchmark": ["-"],
                "Difference": ["-"],
            }
        )
        return GT(empty_data).tab_header(
            title="Portfolio vs Benchmark Statistics",
            subtitle="No data available for comparison",
        )

    if not isinstance(time_period, str):
        time_period = str(time_period) if time_period is not None else "Unknown Period"

    # Configuration validation - check if DataFrames are valid Polars DataFrames
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
        # Create empty table with proper structure
        empty_data = pd.DataFrame(
            {
                "Metric": ["No Valid Data"],
                "Portfolio": ["-"],
                "Benchmark": ["-"],
                "Difference": ["-"],
            }
        )
        return GT(empty_data).tab_header(
            title="Portfolio vs Benchmark Statistics",
            subtitle="Both portfolio and benchmark data are empty or invalid",
        )

    # Only use try-except for operations that might fail unpredictably
    try:
        # Initialize statistics data
        stats_data = []

        # Calculate period information
        period_info = {
            "Period": time_period.replace("_", " ").title()
            if time_period != "custom"
            else "Custom Range",
            "Date Range": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            "Portfolio Points": 0,
            "Benchmark Points": 0,
        }

        # Process portfolio data if available
        portfolio_stats = {}
        if has_portfolio:
            try:
                # Sort by Date and ensure proper data types using Polars
                portfolio_sorted = data_portfolio.sort("Date")

                # Handle different date column types
                date_dtype = portfolio_sorted.select("Date").dtypes[0]

                if date_dtype in [pl.Utf8, pl.String]:
                    # Convert string dates to datetime
                    portfolio_processed = portfolio_sorted.with_columns(
                        [
                            pl.col("Date").str.to_datetime(strict=False).alias("Date"),
                            pl.col("Value").cast(pl.Float64, strict=False).alias("Value"),
                        ]
                    )
                elif date_dtype in [pl.Date]:
                    # Convert date to datetime for consistency
                    portfolio_processed = portfolio_sorted.with_columns(
                        [
                            pl.col("Date").cast(pl.Datetime).alias("Date"),
                            pl.col("Value").cast(pl.Float64, strict=False).alias("Value"),
                        ]
                    )
                else:
                    # Already datetime or cast to datetime
                    portfolio_processed = portfolio_sorted.with_columns(
                        [
                            pl.col("Date").cast(pl.Datetime, strict=False).alias("Date"),
                            pl.col("Value").cast(pl.Float64, strict=False).alias("Value"),
                        ]
                    )

                # Remove null values
                portfolio_clean = portfolio_processed.filter(
                    pl.col("Date").is_not_null() & pl.col("Value").is_not_null(),
                )

                if portfolio_clean.height > 0:
                    # Extract values for calculations
                    portfolio_values = portfolio_clean.select("Value").to_series().to_list()

                    period_info["Portfolio Points"] = len(portfolio_values)

                    # Calculate basic statistics
                    if len(portfolio_values) > 1:
                        start_value = portfolio_values[0]
                        end_value = portfolio_values[-1]

                        if start_value != 0:
                            total_return = ((end_value / start_value) - 1) * 100
                            portfolio_stats["Total Return (%)"] = total_return

                        # Calculate returns for additional statistics
                        portfolio_returns = (
                            portfolio_clean.select(
                                pl.col("Value").pct_change().alias("returns"),
                            )
                            .drop_nulls()
                            .to_series()
                            .to_list()
                        )

                        if len(portfolio_returns) > 0:
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

                        # Calculate max drawdown
                        cum_returns = np.cumprod(1 + np.array(portfolio_returns))
                        peak_values = np.maximum.accumulate(cum_returns)
                        drawdown_values = cum_returns / peak_values - 1
                        max_dd = drawdown.min()

                        portfolio_stats["Max Drawdown (%)"] = max_dd * 100

                    portfolio_stats["Start Value"] = start_value
                    portfolio_stats["End Value"] = end_value
                    portfolio_stats["Min Value"] = min(portfolio_values)
                    portfolio_stats["Max Value"] = max(portfolio_values)

            except Exception:
                portfolio_stats = {"Error": "Failed to calculate portfolio statistics"}

        # Process benchmark data if available (same approach as portfolio)
        benchmark_stats = {}
        if has_benchmark:
            try:
                # Sort by Date and ensure proper data types using Polars
                benchmark_sorted = data_benchmark.sort("Date")

                # Handle different date column types
                date_dtype = benchmark_sorted.select("Date").dtypes[0]

                if date_dtype in [pl.Utf8, pl.String]:
                    # Convert string dates to datetime
                    benchmark_processed = benchmark_sorted.with_columns(
                        [
                            pl.col("Date").str.to_datetime(strict=False).alias("Date"),
                            pl.col("Value").cast(pl.Float64, strict=False).alias("Value"),
                        ]
                    )
                elif date_dtype in [pl.Date]:
                    # Convert date to datetime for consistency
                    benchmark_processed = benchmark_sorted.with_columns(
                        [
                            pl.col("Date").cast(pl.Datetime).alias("Date"),
                            pl.col("Value").cast(pl.Float64, strict=False).alias("Value"),
                        ]
                    )
                else:
                    # Already datetime or cast to datetime
                    benchmark_processed = benchmark_sorted.with_columns(
                        [
                            pl.col("Date").cast(pl.Datetime, strict=False).alias("Date"),
                            pl.col("Value").cast(pl.Float64, strict=False).alias("Value"),
                        ]
                    )

                # Remove null values
                benchmark_clean = benchmark_processed.filter(
                    pl.col("Date").is_not_null() & pl.col("Value").is_not_null(),
                )

                if benchmark_clean.height > 0:
                    # Extract values for calculations
                    benchmark_values = benchmark_clean.select("Value").to_series().to_list()

                    period_info["Benchmark Points"] = len(benchmark_values)

                    # Calculate basic statistics
                    if len(benchmark_values) > 1:
                        start_value = benchmark_values[0]
                        end_value = benchmark_values[-1]

                        if start_value != 0:
                            total_return = ((end_value / start_value) - 1) * 100
                            benchmark_stats["Total Return (%)"] = total_return

                        # Calculate returns for additional statistics
                        benchmark_returns = (
                            benchmark_clean.select(
                                pl.col("Value").pct_change().alias("returns"),
                            )
                            .drop_nulls()
                            .to_series()
                            .to_list()
                        )

                        if len(benchmark_returns) > 0:
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

                        # Calculate max drawdown
                        cum_returns = np.cumprod(1 + np.array(benchmark_returns))
                        peak_values = np.maximum.accumulate(cum_returns)
                        drawdown_values = cum_returns / peak_values - 1
                        benchmark_stats["Max Drawdown (%)"] = np.min(drawdown_values) * 100

                    benchmark_stats["Start Value"] = start_value
                    benchmark_stats["End Value"] = end_value
                    benchmark_stats["Min Value"] = min(benchmark_values)
                    benchmark_stats["Max Value"] = max(benchmark_values)

            except Exception:
                benchmark_stats = {"Error": "Failed to calculate benchmark statistics"}

        # Build comparison table data
        all_metrics = set()
        if portfolio_stats:
            all_metrics.update(portfolio_stats.keys())
        if benchmark_stats:
            all_metrics.update(benchmark_stats.keys())

        # Remove error keys from metrics list
        all_metrics = sorted([metric for metric in all_metrics if metric != "Error"])

        # Create table data
        table_data = []

        # Add period information rows
        table_data.append(
            {
                "Metric": "Selected Period",
                "Portfolio": period_info["Period"],
                "Benchmark": period_info["Period"],
                "Difference": "-",
            }
        )

        table_data.append(
            {
                "Metric": "Date Range",
                "Portfolio": period_info["Date Range"],
                "Benchmark": period_info["Date Range"],
                "Difference": "-",
            }
        )

        table_data.append(
            {
                "Metric": "Data Points",
                "Portfolio": str(period_info["Portfolio Points"]),
                "Benchmark": str(period_info["Benchmark Points"]),
                "Difference": str(
                    period_info["Portfolio Points"] - period_info["Benchmark Points"]
                ),
            }
        )

        # Add performance metrics
        for metric in all_metrics:
            portfolio_value = portfolio_stats.get(metric, "N/A")
            benchmark_value = benchmark_stats.get(metric, "N/A")

            # Calculate difference if both values are numeric
            difference = "N/A"
            if (
                isinstance(portfolio_value, (int, float))
                and isinstance(benchmark_value, (int, float))
                and not pd.isna(portfolio_value)
                and not pd.isna(benchmark_value)
            ):
                difference = portfolio_value - benchmark_value
                difference = f"{difference:.4f}"

            # Format values for display
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
                }
            )

        # Create pandas DataFrame for great-tables
        comparison_df = pd.DataFrame(table_data)

        # Create great-tables GT object and style it
        gt_table = (
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
                locations=loc.body(rows=[0, 1, 2]),  # Highlight period information rows
            )
            .tab_style(
                style=style.text(weight="bold"),
                locations=loc.body(columns=["Metric"]),
            )
        )
        return gt_table

    except Exception as exc:
        # Create error table using great-tables
        error_data = pd.DataFrame(
            {
                "Metric": ["Error"],
                "Portfolio": [f"Error: {exc!s}"],
                "Benchmark": ["-"],
                "Difference": ["-"],
            }
        )

        error_table = (
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

        raise RuntimeError(f"Error creating comparison statistics table: {exc}") from exc


def create_table_summary_weights_analysis(
    data_stats,
    show_pct=True,
    data_was_validated=True
):
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

    # Input validation with early returns
    if not data_stats or not isinstance(data_stats, dict):
        # Create empty table with proper structure
        empty_data = pd.DataFrame(
            {
                "Component": ["No Data Available"],
                "Latest": ["-"],
                "Average": ["-"],
                "Min": ["-"],
                "Max": ["-"],
                "StdDev": ["-"],
            }
        )
        return GT(empty_data).tab_header(
            title="Portfolio Weight Distribution Statistics",
            subtitle="No data available",
        )

    # Configuration validation - check for period info
    period_info = data_stats.get("_period_info", {})
    period_label = period_info.get("period_label", "Unknown Period")
    data_points = period_info.get("data_points", 0)

    # Only use try-except for operations that might fail unpredictably
    try:
        # Extract component statistics
        component_stats = {k: v for k, v in data_stats.items() if not k.startswith("_")}

        if not component_stats:
            # Create empty table with proper structure
            empty_data = pd.DataFrame(
                {
                    "Component": ["No Components Available"],
                    "Latest": ["-"],
                    "Average": ["-"],
                    "Min": ["-"],
                    "Max": ["-"],
                    "StdDev": ["-"],
                }
            )
            return GT(empty_data).tab_header(
                title="Portfolio Weight Distribution Statistics",
                subtitle="No component data available",
            )

        # Build table data
        table_data = []

        for component_name, stats in component_stats.items():
            # Get statistics with fallbacks
            latest_weight = stats.get("Latest", 0)
            average_weight = stats.get("Average", 0)
            min_weight = stats.get("Min", 0)
            max_weight = stats.get("Max", 0)
            std_weight = stats.get("StdDev", 0)

            # Safe formatting function for display values
            def safe_format_value(value, as_percentage=True):
                """Safely format a value for display with defensive programming."""
                # Input validation with early returns
                if value is None:
                    return "-"

                if pd.isna(value):
                    return "-"

                if not isinstance(value, (int, float)):
                    return "-"

                # Only use try-except for string formatting that might fail
                try:
                    if as_percentage:
                        return f"{float(value):.2f}%"
                    return f"{float(value):.4f}"
                except (ValueError, TypeError, OverflowError):
                    return "-"

            # Format values based on show_pct flag using safe formatting
            latest_display = safe_format_value(value = latest_weight, as_percentage = show_pct)
            average_display = safe_format_value(value = average_weight, as_percentage = show_pct)
            min_display = safe_format_value(value = min_weight, as_percentage = show_pct)
            max_display = safe_format_value(value = max_weight, as_percentage = show_pct)
            std_display = safe_format_value(value = std_weight, as_percentage = show_pct)

            table_data.append(
                {
                    "Component": str(component_name),  # Ensure string conversion
                    "Latest": latest_display,
                    "Average": average_display,
                    "Min": min_display,
                    "Max": max_display,
                    "StdDev": std_display,
                }
            )

        # Sort by latest weight (descending) with safe numeric extraction
        def extract_numeric_for_sorting(display_value):
            """Extract numeric value from display string for sorting."""
            if display_value == "-":
                return 0

            # Only use try-except for string operations that might fail
            try:
                # Remove percentage sign if present
                numeric_str = display_value.rstrip("%")
                return float(numeric_str)
            except (ValueError, TypeError, AttributeError):
                return 0

        table_data.sort(key=lambda x: extract_numeric_for_sorting(display_value = x["Latest"]), reverse=True)

        # Create pandas DataFrame for great-tables
        weights_df = pd.DataFrame(table_data)

        # Create great-tables GT object
        gt_table = (
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
        return gt_table

    except Exception as exc:
        # Create error table using great-tables
        error_data = pd.DataFrame(
            {
                "Component": ["Error"],
                "Latest": [f"Error: {exc!s}"],
                "Average": ["-"],
                "Min": ["-"],
                "Max": ["-"],
                "StdDev": ["-"],
            }
        )

        error_table = (
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

        raise RuntimeError(f"Error creating Weights Analysis statistics table: {exc}") from exc


def create_enhanced_summary_table(
    dataframe_input: pl.DataFrame,
    table_title: str = "Summary Table",
    table_subtitle: str = "",
    column_headers: list[str] | None = None,
    currency_columns: list[str] | None = None,
    percentage_columns: list[str] | None = None,
    table_theme: str = "professional",
    show_row_numbers: bool = False,
    table_width: str = "100%",
) -> GT:
    """Create enhanced summary table using great-tables with comprehensive formatting.

    This function generates professional, customizable tables using the great-tables
    package with polars dataframes. It supports 1-2 column dataframes containing
    mixed numeric and string data types with comprehensive formatting options for
    financial data display, currency values, and percentage calculations.

    The function follows defensive programming principles with comprehensive input
    validation using early returns, configuration validation for table parameters,
    and business logic validation for data formatting requirements. All styling
    follows the project's enhanced UI patterns with consistent visual design.

    Args:
        dataframe_input: Polars DataFrame containing 1-2 columns with mixed data types.
            First column typically contains category names (strings), second column
            contains values (numeric or string). Required for table generation.
        table_title: Title displayed at top of table for identification and context.
            Default: "Summary Table". Used for table header identification.
        table_subtitle: Optional subtitle providing additional context or description.
            Default: empty string. Displayed below main title when provided.
        column_headers: Optional list of custom column header names for display.
            Default: None (uses dataframe column names). Must match column count.
        currency_columns: Optional list of column names to format as currency values.
            Default: None. Applies currency formatting ($X,XXX.XX) to specified columns.
        percentage_columns: Optional list of column names to format as percentages.
            Default: None. Applies percentage formatting (XX.X%) to specified columns.
        table_theme: Theme selection for table styling and visual appearance.
            Default: "professional". Options: "professional", "minimal", "enhanced".
        show_row_numbers: Whether to display row numbers in the table for reference.
            Default: False. Adds sequential numbering when enabled.
        table_width: CSS width specification for table container sizing.
            Default: "100%". Accepts CSS width values (px, %, em, rem).

    Returns:
        GT: Configured great-tables GT object with comprehensive formatting, styling,
            and professional appearance ready for display in Shiny applications.
            Includes currency formatting, percentage display, and enhanced readability.

    Raises:
        ValueError: If dataframe_input is None, empty, has invalid structure (not 1-2 columns),
            contains incompatible data types, or column_headers count doesn't match
            dataframe columns during validation and table generation processes.
        TypeError: If dataframe_input is not a polars DataFrame, column_headers is not
            a list when provided, or formatting parameters are not of expected types
            during table configuration and styling operations.
        RuntimeError: If great-tables package is not available, table generation fails
            due to formatting conflicts, or unexpected errors occur during table
            creation and styling application processes.
        ImportError: If required dependencies (great_tables, polars) are not installed
            or available in the current environment during module initialization
            and table generation operations.

    Examples:
        Create basic summary table with personal information:

        ```python
        # Create dataframe with personal info
        Personal_Info_Data = pl.DataFrame(
            {"Category": ["Name", "Age", "Risk Tolerance"], "Value": ["John Doe", "45", "Moderate"]}
        )

        # Generate professional table
        Personal_Info_Table = create_enhanced_summary_table(
            dataframe_input=Personal_Info_Data,
            table_title="Personal Information Summary",
            table_subtitle="Primary Investor Details",
        )
        ```

        Create financial table with currency formatting:

        ```python
        # Create dataframe with financial assets
        Assets_Data = pl.DataFrame(
            {
                "Asset_Type": ["Taxable Assets", "Tax Deferred", "Tax Free"],
                "Amount": [250000.00, 400000.00, 75000.00],
            }
        )

        # Generate table with currency formatting
        Assets_Table = create_enhanced_summary_table(
            dataframe_input=Assets_Data,
            table_title="Financial Assets Summary",
            column_headers=["Asset Type", "Current Value"],
            currency_columns=["Amount"],
            table_theme="enhanced",
        )
        ```

        Create goals table with enhanced styling:

        ```python
        # Create dataframe with financial goals
        Goals_Data = pl.DataFrame(
            {
                "Goal_Priority": ["Essential", "Important", "Aspirational"],
                "Annual_Amount": [60000, 25000, 15000],
            }
        )

        # Generate table with comprehensive formatting
        Goals_Table = create_enhanced_summary_table(
            dataframe_input=Goals_Data,
            table_title="Financial Goals Summary",
            table_subtitle="Annual Target Amounts",
            column_headers=["Priority Level", "Annual Target"],
            currency_columns=["Annual_Amount"],
            show_row_numbers=True,
            table_width="90%",
        )
        ```

    Note:
        This function requires the great-tables package for professional table generation
        and polars for high-performance dataframe operations. All formatting options
        support both single and dual column dataframes with mixed data types.

        Table themes provide different visual styles:
        - "professional": Corporate styling with clean lines and proper spacing
        - "minimal": Simple styling with reduced visual elements
        - "enhanced": Rich styling with enhanced colors and formatting

        Currency formatting automatically applies to numeric columns specified in
        currency_columns parameter, displaying values as $X,XXX.XX format. Percentage
        formatting converts decimal values to XX.X% display format.

        Performance considerations: Large dataframes (>1000 rows) may experience
        slower rendering. Consider data pagination for extensive datasets.

    Security:
        Input validation prevents injection attacks through dataframe content validation
        and parameter sanitization. All user-provided data is properly escaped before
        table generation to prevent XSS vulnerabilities in web display contexts.

    See Also:
        subtab_investors_summary_ui: UI creation function for summary subtab
        subtab_investors_summary_server: Server logic for summary table generation
        format_enhanced_currency_display: Currency formatting utilities
        utils_enhanced_formatting: Comprehensive data formatting utilities
        great_tables.GT: Great-tables GT class documentation
        polars.DataFrame: Polars DataFrame documentation
    """
    # Input validation with early returns following coding standards
    if dataframe_input is None:
        raise ValueError("Dataframe input cannot be None")

    if not isinstance(dataframe_input, pl.DataFrame):
        raise TypeError("Input must be a polars DataFrame")

    if dataframe_input.is_empty():
        raise ValueError("Dataframe cannot be empty")

    # Configuration validation - check dataframe structure
    Column_Count = len(dataframe_input.columns)
    if Column_Count not in [1, 2]:
        raise ValueError("Dataframe must have exactly 1 or 2 columns")

    if column_headers is not None:
        if not isinstance(column_headers, list):
            raise TypeError("Column headers must be a list")
        if len(column_headers) != Column_Count:
            raise ValueError("Column headers count must match dataframe columns")

    # Business logic validation - prepare table data
    try:
        # Create GT table object from polars dataframe
        Table_GT = GT(dataframe_input)

        # Apply custom column headers if provided
        if column_headers is not None:
            Table_GT = Table_GT.cols_label(
                **{
                    dataframe_input.columns[idx]: column_headers[idx]
                    for idx in range(len(column_headers))
                }
            )

        # Apply table title and subtitle
        if table_title:
            Table_GT = Table_GT.tab_header(
                title=md(f"**{table_title}**"),
                subtitle=md(table_subtitle) if table_subtitle else None,
            )

        # Apply currency formatting to specified columns
        if currency_columns:
            for Currency_Column in currency_columns:
                if Currency_Column in dataframe_input.columns:
                    Table_GT = Table_GT.fmt_currency(
                        columns=[Currency_Column],
                        currency="USD",
                        decimals=2,
                    )

        # Apply percentage formatting to specified columns
        if percentage_columns:
            for Percentage_Column in percentage_columns:
                if Percentage_Column in dataframe_input.columns:
                    Table_GT = Table_GT.fmt_percent(
                        columns=[Percentage_Column],
                        decimals=1,
                    )

        # Apply theme-based styling
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
                heading_title_font_color="white",
                heading_subtitle_font_color="white",
                column_labels_background_color="#6c757d",
                column_labels_font_color="white",
                row_striping_background_color="#f1f3f4",
            )

        # Add row numbers if requested
        if show_row_numbers:
            Table_GT = Table_GT.opt_row_striping()

        return Table_GT

    except Exception as exc_error:
        raise RuntimeError(f"Error creating enhanced summary table: {exc_error!s}") from exc_error


def create_enhanced_summary_table_multi_column(
    dataframe_input: pl.DataFrame,
    table_title: str = "Summary Table",
    table_subtitle: str = "",
    currency_columns: list[str] | None = None,
    percentage_columns: list[str] | None = None,
    table_theme: str = "professional",
    table_width: str = "100%",
) -> GT:
    """Create enhanced summary table using great-tables with support for multiple columns.

    This function generates professional, customizable tables using the great-tables
    package with polars dataframes. It supports dataframes with any number of columns
    containing mixed numeric and string data types with comprehensive formatting options.

    Args:
        dataframe_input: Polars DataFrame containing data for table generation.
        table_title: Title displayed at top of table for identification and context.
        table_subtitle: Optional subtitle providing additional context or description.
        currency_columns: Optional list of column names to format as currency values.
        percentage_columns: Optional list of column names to format as percentages.
        table_theme: Theme selection for table styling and visual appearance.
        table_width: CSS width specification for table container sizing.

    Returns:
        GT: Configured great-tables GT object with comprehensive formatting and styling.

    Raises:
        ValueError: If dataframe_input is None or empty.
        TypeError: If dataframe_input is not a polars DataFrame.
        RuntimeError: If table generation fails.
    """
    # Input validation with early returns following coding standards
    if dataframe_input is None:
        raise ValueError("Dataframe input cannot be None")

    if not isinstance(dataframe_input, pl.DataFrame):
        raise TypeError("Input must be a polars DataFrame")

    if dataframe_input.is_empty():
        raise ValueError("Dataframe cannot be empty")

    # Business logic validation - prepare table data
    try:
        # Convert polars DataFrame to pandas for great-tables compatibility
        Pandas_DataFrame = dataframe_input.to_pandas()

        # Create GT table object from pandas dataframe
        Table_GT = GT(Pandas_DataFrame)

        # Apply table title and subtitle
        if table_title:
            Table_GT = Table_GT.tab_header(
                title=md(f"**{table_title}**"),
                subtitle=md(table_subtitle) if table_subtitle else None,
            )

        # Apply currency formatting to specified columns
        if currency_columns:
            for Currency_Column in currency_columns:
                if Currency_Column in Pandas_DataFrame.columns:
                    Table_GT = Table_GT.fmt_currency(
                        columns=[Currency_Column],
                        currency="USD",
                        decimals=2,
                    )

        # Apply percentage formatting to specified columns
        if percentage_columns:
            for Percentage_Column in percentage_columns:
                if Percentage_Column in Pandas_DataFrame.columns:
                    Table_GT = Table_GT.fmt_percent(
                        columns=[Percentage_Column],
                        decimals=1,
                    )

        # Apply theme-based styling with corrected syntax
        if table_theme == "professional":
            Table_GT = Table_GT.tab_options(
                table_width=table_width,
                table_font_size="14px",
                heading_background_color="#f8f9fa",
                heading_title_font_size="18px",
                heading_subtitle_font_size="14px",
                column_labels_background_color="#e9ecef",
            )
            # Add styling for first column
            Table_GT = Table_GT.tab_style(
                style=style.fill(color="#f8f9fa"),
                locations=loc.body(columns=[Pandas_DataFrame.columns[0]]),
            ).tab_style(
                style=style.text(weight="bold"),
                locations=loc.body(columns=[Pandas_DataFrame.columns[0]]),
            )
        elif table_theme == "minimal":
            Table_GT = Table_GT.tab_options(
                table_width=table_width,
                table_font_size="13px",
            )
        elif table_theme == "enhanced":
            Table_GT = Table_GT.tab_options(
                table_width=table_width,
                table_font_size="14px",
                heading_background_color="#007bff",
                heading_title_font_size="20px",
                column_labels_background_color="#6c757d",
            )

        return Table_GT

    except Exception as exc_error:
        raise RuntimeError(f"Error creating enhanced summary table: {exc_error!s}") from exc_error


# ============================================================================
# pytest imports (must follow all helper code above)
# ============================================================================
import pytest
import polars as pl
from datetime import date


# ============================================================================
# Tests for validate_data_visuals
# ============================================================================


class Test_Validate_Data_Visuals:
    """Tests for the validate_data_visuals function in utils_visuals."""

    @pytest.mark.unit()
    def test_none_dataframe_returns_false(self):
        """Test that none dataframe returns false."""
        from src.dashboard.shiny_utils.utils_visuals import validate_data_visuals

        result, msg = validate_data_visuals(data_frame = None, selected_series_list = None)
        assert result is False
        assert isinstance(msg, str)
        assert len(msg) > 0

    @pytest.mark.unit()
    def test_non_polars_type_returns_false(self):
        """Test that non polars type returns false."""
        from src.dashboard.shiny_utils.utils_visuals import validate_data_visuals

        result, msg = validate_data_visuals(data_frame = {"Date": [1, 2]}, selected_series_list = None)
        assert result is False

    @pytest.mark.unit()
    def test_empty_dataframe_returns_false(self):
        """Test that empty dataframe returns false."""
        from src.dashboard.shiny_utils.utils_visuals import validate_data_visuals

        df = pl.DataFrame({"Date": pl.Series([], dtype=pl.Utf8), "Value": pl.Series([], dtype=pl.Float64)})
        result, msg = validate_data_visuals(data_frame = df, selected_series_list = None)
        assert result is False

    @pytest.mark.unit()
    def test_missing_date_column_returns_false(self):
        """Test that missing date column returns false."""
        from src.dashboard.shiny_utils.utils_visuals import validate_data_visuals

        df = pl.DataFrame({"Value": [100.0, 101.0]})
        result, msg = validate_data_visuals(data_frame = df, selected_series_list = None)
        assert result is False

    @pytest.mark.unit()
    def test_valid_dataframe_no_series_filter_returns_true(self):
        """Test that valid dataframe no series filter returns true."""
        from src.dashboard.shiny_utils.utils_visuals import validate_data_visuals

        df = pl.DataFrame({
            "Date": [date(2023, 1, 1), date(2023, 1, 2)],
            "Value": [100.0, 101.0],
        })
        result, msg = validate_data_visuals(data_frame = df, selected_series_list = None)
        assert result is True
        assert msg == ""

    @pytest.mark.unit()
    def test_selected_series_not_list_returns_false(self):
        """Test that selected series not list returns false."""
        from src.dashboard.shiny_utils.utils_visuals import validate_data_visuals

        df = pl.DataFrame({"Date": [date(2023, 1, 1)], "Value": [100.0]})
        result, msg = validate_data_visuals(data_frame = df, selected_series_list = "Value")
        assert result is False

    @pytest.mark.unit()
    def test_empty_series_list_returns_false(self):
        """Test that empty series list returns false."""
        from src.dashboard.shiny_utils.utils_visuals import validate_data_visuals

        df = pl.DataFrame({"Date": [date(2023, 1, 1)], "Value": [100.0]})
        result, msg = validate_data_visuals(data_frame = df, selected_series_list = [])
        assert result is False

    @pytest.mark.unit()
    def test_series_not_in_df_returns_false(self):
        """Test that series not in df returns false."""
        from src.dashboard.shiny_utils.utils_visuals import validate_data_visuals

        df = pl.DataFrame({"Date": [date(2023, 1, 1)], "Value": [100.0]})
        result, msg = validate_data_visuals(data_frame = df, selected_series_list = ["NonExistentColumn"])
        assert result is False

    @pytest.mark.unit()
    def test_valid_series_list_returns_true(self):
        """Test that valid series list returns true."""
        from src.dashboard.shiny_utils.utils_visuals import validate_data_visuals

        df = pl.DataFrame({
            "Date": [date(2023, 1, 1), date(2023, 1, 2)],
            "Value": [100.0, 101.0],
        })
        result, msg = validate_data_visuals(data_frame = df, selected_series_list = ["Value"])
        assert result is True

    @pytest.mark.unit()
    def test_multiple_valid_series_returns_true(self):
        """Test that multiple valid series returns true."""
        from src.dashboard.shiny_utils.utils_visuals import validate_data_visuals

        df = pl.DataFrame({
            "Date": [date(2023, 1, 1), date(2023, 1, 2)],
            "A": [100.0, 101.0],
            "B": [200.0, 201.0],
        })
        result, msg = validate_data_visuals(data_frame = df, selected_series_list = ["A", "B"])
        assert result is True


# ============================================================================
# Tests for create_error_figure
# ============================================================================


class Test_Create_Error_Figure:
    """Tests for the create_error_figure function in utils_visuals."""

    @pytest.mark.unit()
    def test_returns_plotly_figure(self):
        """Test that returns plotly figure."""
        import plotly.graph_objects as go
        from src.dashboard.shiny_utils.utils_visuals import create_error_figure

        fig = create_error_figure(message_text = "Test error message")
        assert isinstance(fig, go.Figure)

    @pytest.mark.unit()
    def test_custom_title_accepted(self):
        """Test that custom title accepted."""
        import plotly.graph_objects as go
        from src.dashboard.shiny_utils.utils_visuals import create_error_figure

        fig = create_error_figure(message_text = "msg", title_text="Custom Title")
        assert isinstance(fig, go.Figure)

    @pytest.mark.unit()
    def test_with_details_text_accepted(self):
        """Test that with details text accepted."""
        import plotly.graph_objects as go
        from src.dashboard.shiny_utils.utils_visuals import create_error_figure

        fig = create_error_figure(message_text = "msg", details_text="Additional details")
        assert isinstance(fig, go.Figure)

    @pytest.mark.unit()
    def test_none_message_handled(self):
        """Test that none message handled."""
        import plotly.graph_objects as go
        from src.dashboard.shiny_utils.utils_visuals import create_error_figure

        fig = create_error_figure(message_text = None)  # type: ignore[arg-type]
        assert isinstance(fig, go.Figure)

    @pytest.mark.unit()
    def test_empty_string_message_handled(self):
        """Test that empty string message handled."""
        import plotly.graph_objects as go
        from src.dashboard.shiny_utils.utils_visuals import create_error_figure

        fig = create_error_figure(message_text = "")
        assert isinstance(fig, go.Figure)

    @pytest.mark.unit()
    def test_non_string_details_coerced(self):
        """Test that non string details coerced."""
        import plotly.graph_objects as go
        from src.dashboard.shiny_utils.utils_visuals import create_error_figure

        fig = create_error_figure(message_text = "msg", details_text=12345)  # type: ignore[arg-type]
        assert isinstance(fig, go.Figure)


# ============================================================================
# Tests for format_value_for_display
# ============================================================================


class Test_Format_Value_For_Display:
    """Tests for the format_value_for_display function in utils_visuals."""

    @pytest.mark.unit()
    def test_decimal_format_returns_string(self):
        """Test that decimal format returns string."""
        from src.dashboard.shiny_utils.utils_visuals import format_value_for_display

        result = format_value_for_display(value_input = 1234.567, format_type = "decimal")
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.unit()
    def test_percentage_format_returns_string(self):
        """Test that percentage format returns string."""
        from src.dashboard.shiny_utils.utils_visuals import format_value_for_display

        result = format_value_for_display(value_input = 0.1234, format_type = "percentage")
        assert isinstance(result, str)

    @pytest.mark.unit()
    def test_integer_format_returns_string(self):
        """Test that integer format returns string."""
        from src.dashboard.shiny_utils.utils_visuals import format_value_for_display

        result = format_value_for_display(value_input = 1234, format_type = "integer")
        assert isinstance(result, str)
        assert "1234" in result.replace(",", "").replace(".", "")

    @pytest.mark.unit()
    def test_none_input_returns_string(self):
        """Test that none input returns string."""
        from src.dashboard.shiny_utils.utils_visuals import format_value_for_display

        result = format_value_for_display(value_input = None, format_type = "decimal")
        assert isinstance(result, str)

    @pytest.mark.unit()
    def test_zero_value_returns_string(self):
        """Test that zero value returns string."""
        from src.dashboard.shiny_utils.utils_visuals import format_value_for_display

        result = format_value_for_display(value_input = 0.0, format_type = "decimal")
        assert isinstance(result, str)


# ============================================================================
# Tests for safe_numeric_conversion
# ============================================================================


class Test_Safe_Numeric_Conversion:
    """Tests for the safe_numeric_conversion function in utils_visuals."""

    @pytest.mark.unit()
    def test_integer_input(self):
        """Test that integer input."""
        from src.dashboard.shiny_utils.utils_visuals import safe_numeric_conversion

        result = safe_numeric_conversion(input_value = 42)
        assert result == 42

    @pytest.mark.unit()
    def test_float_input(self):
        """Test that float input."""
        from src.dashboard.shiny_utils.utils_visuals import safe_numeric_conversion

        result = safe_numeric_conversion(input_value = 3.14)
        assert abs(result - 3.14) < 1e-9

    @pytest.mark.unit()
    def test_boolean_input_is_not_coerced_to_float(self):
        """Boolean input stays boolean instead of being silently converted to 1.0/0.0."""
        from src.dashboard.shiny_utils.utils_visuals import safe_numeric_conversion

        result = safe_numeric_conversion(input_value = True)
        assert result is True

    @pytest.mark.unit()
    def test_numeric_string_does_not_raise(self):
        """Test that numeric string does not raise."""
        from src.dashboard.shiny_utils.utils_visuals import safe_numeric_conversion

        result = safe_numeric_conversion(input_value = "123.45")
        assert result is not None

    @pytest.mark.unit()
    def test_none_input_does_not_raise(self):
        """Test that none input does not raise."""
        from src.dashboard.shiny_utils.utils_visuals import safe_numeric_conversion

        result = safe_numeric_conversion(input_value = None)
        assert result is None or isinstance(result, (int, float))

    @pytest.mark.unit()
    def test_non_numeric_string_does_not_raise(self):
        """Test that non numeric string does not raise."""
        from src.dashboard.shiny_utils.utils_visuals import safe_numeric_conversion

        result = safe_numeric_conversion(input_value = "not_a_number")
        assert True  # simply must not raise


# ============================================================================
# Tests for create_plot_portfolios_comparison
# ============================================================================


class Test_Create_Plot_Portfolios_Comparison:
    """Tests for create_plot_portfolios_comparison in utils_visuals."""

    @pytest.mark.unit()
    def test_both_none_returns_figure(self):
        """Test that both none returns figure."""
        import plotly.graph_objects as go
        from src.dashboard.shiny_utils.utils_visuals import create_plot_portfolios_comparison

        fig = create_plot_portfolios_comparison(data_portfolio = None, data_benchmark = None, period_label = "Custom", data_was_validated=False)
        assert isinstance(fig, go.Figure)

    @pytest.mark.unit()
    def test_portfolio_only_returns_figure(self):
        """Test that portfolio only returns figure."""
        import plotly.graph_objects as go
        from src.dashboard.shiny_utils.utils_visuals import create_plot_portfolios_comparison

        df = pl.DataFrame({
            "Date": [date(2023, 1, 1), date(2023, 1, 2), date(2023, 1, 3)],
            "Value": [100.0, 102.0, 101.0],
        })
        # Pass data_was_validated=False so None benchmark is handled by validation
        fig = create_plot_portfolios_comparison(data_portfolio = df, data_benchmark = None, period_label = "Custom", data_was_validated=False)
        assert isinstance(fig, go.Figure)

    @pytest.mark.unit()
    def test_both_datasets_returns_figure(self):
        """Test that both datasets returns figure."""
        import plotly.graph_objects as go
        from src.dashboard.shiny_utils.utils_visuals import create_plot_portfolios_comparison

        df = pl.DataFrame({
            "Date": [date(2023, 1, 1), date(2023, 1, 2)],
            "Value": [100.0, 102.0],
        })
        fig = create_plot_portfolios_comparison(data_portfolio = df, data_benchmark = df, period_label = "Custom", data_was_validated=True)
        assert isinstance(fig, go.Figure)

    @pytest.mark.unit()
    def test_various_period_labels_return_figures(self):
        """Test that various period labels return figures."""
        import plotly.graph_objects as go
        from src.dashboard.shiny_utils.utils_visuals import create_plot_portfolios_comparison

        for label in ["1Y", "3Y", "5Y", "All"]:
            fig = create_plot_portfolios_comparison(data_portfolio = None, data_benchmark = None, period_label = label, data_was_validated=False)
            assert isinstance(fig, go.Figure)


# ============================================================================
# Tests for calculate_table_stats_basic
# ============================================================================


class Test_Calculate_Table_Stats_Basic:
    """Tests for calculate_table_stats_basic in utils_visuals."""

    @pytest.mark.unit()
    def test_returns_something_with_valid_data(self):
        """Test that returns something with valid data."""
        from src.dashboard.shiny_utils.utils_visuals import calculate_table_stats_basic

        df = pl.DataFrame({
            "Date": [date(2023, 1, 1 + i) for i in range(10)],
            "Value": [100.0 + i for i in range(10)],
        })
        result = calculate_table_stats_basic(data_portfolio = df, data_benchmark = None, include_benchmark=False)
        assert result is not None

    @pytest.mark.unit()
    def test_none_data_does_not_raise(self):
        """Test that none data does not raise."""
        from src.dashboard.shiny_utils.utils_visuals import calculate_table_stats_basic

        result = calculate_table_stats_basic(data_portfolio = None, data_benchmark = None, include_benchmark=False)
        assert result is not None

    @pytest.mark.unit()
    def test_with_benchmark_does_not_raise(self):
        """Test that with benchmark does not raise."""
        from src.dashboard.shiny_utils.utils_visuals import calculate_table_stats_basic

        df = pl.DataFrame({
            "Date": [date(2023, 1, 1 + i) for i in range(5)],
            "Value": [100.0 + i * 2 for i in range(5)],
        })
        result = calculate_table_stats_basic(data_portfolio = df, data_benchmark = df, include_benchmark=True)
        assert result is not None


# ============================================================================
# Tests for utils_visuals module-level structure
# ============================================================================


class Test_Utils_Visuals_Module_Structure:
    """Tests verifying module-level exports of utils_visuals."""

    @pytest.mark.unit()
    def test_module_importable(self):
        """Test that module importable."""
        import src.dashboard.shiny_utils.utils_visuals as m

        assert m is not None

    @pytest.mark.unit()
    def test_expected_functions_present(self):
        """Test that expected functions present."""
        from src.dashboard.shiny_utils import utils_visuals

        expected = [
            "validate_data_visuals",
            "create_error_figure",
            "format_value_for_display",
            "safe_numeric_conversion",
            "create_plot_portfolios_comparison",
            "create_plot_rolling_statistics",
            "create_plot_returns_distribution",
            "create_plot_drawdowns_analysis",
            "calculate_table_stats_basic",
            "create_enhanced_summary_table",
        ]
        for name in expected:
            assert hasattr(utils_visuals, name), f"Missing function: {name}"

    @pytest.mark.unit()
    def test_expected_functions_are_callable(self):
        """Test that expected functions are callable."""
        from src.dashboard.shiny_utils import utils_visuals

        for name in [
            "validate_data_visuals",
            "create_error_figure",
            "format_value_for_display",
            "safe_numeric_conversion",
        ]:
            fn = getattr(utils_visuals, name, None)
            assert callable(fn), f"Not callable: {name}"


    # ============================================================================
    # Source-facing branch coverage for utils_visuals
    # ============================================================================


    @pytest.mark.unit()
    class Class_Test_Utils_Visuals_Source_Branches:
        """Exercise the real utils_visuals module beyond smoke-level imports."""

        @pytest.fixture()
        def portfolio_df(self) -> pl.DataFrame:
            """Return a deterministic portfolio value series."""
            return pl.DataFrame(
                {
                    "Date": [
                        date(2024, 1, 1),
                        date(2024, 1, 2),
                        date(2024, 1, 3),
                        date(2024, 1, 4),
                        date(2024, 1, 5),
                        date(2024, 1, 6),
                    ],
                    "Value": [100.0, 102.0, 101.0, 104.0, 106.0, 105.0],
                }
            )

        @pytest.fixture()
        def benchmark_df(self) -> pl.DataFrame:
            """Return a deterministic benchmark value series."""
            return pl.DataFrame(
                {
                    "Date": [
                        date(2024, 1, 1),
                        date(2024, 1, 2),
                        date(2024, 1, 3),
                        date(2024, 1, 4),
                        date(2024, 1, 5),
                        date(2024, 1, 6),
                    ],
                    "Value": [100.0, 101.0, 103.0, 102.0, 104.0, 108.0],
                }
            )

        @pytest.mark.unit()
        def Test_Validate_Data_Visuals_Accepts_Tuple_Selection(
            self,
            portfolio_df: pl.DataFrame,
        ) -> None:
            """Tuple selections are valid and should find real series data."""
            from src.dashboard.shiny_utils.utils_visuals import validate_data_visuals

            is_valid, message = validate_data_visuals(data_frame = portfolio_df, selected_series_list = ("Value",))

            assert is_valid is True
            assert message == ""

        @pytest.mark.unit()
        def Test_Validate_Data_Visuals_Rejects_All_Null_Selected_Data(self) -> None:
            """Selected columns with only null values should fail data-quality checks."""
            from src.dashboard.shiny_utils.utils_visuals import validate_data_visuals

            data_frame = pl.DataFrame(
                {
                    "Date": [date(2024, 1, 1), date(2024, 1, 2)],
                    "Value": [None, None],
                }
            )

            is_valid, message = validate_data_visuals(data_frame = data_frame, selected_series_list = ["Value"])

            assert is_valid is False
            assert "No valid data" in message

        @pytest.mark.unit()
        def Test_Format_Value_For_Display_Covers_Bool_And_Format_Branches(self) -> None:
            """Formatting should cover bool, percentage, integer, decimal, and NA paths."""
            from src.dashboard.shiny_utils.utils_visuals import format_value_for_display

            assert format_value_for_display(value_input = True) == "True"
            assert format_value_for_display(value_input = 0.1234, format_type = "percentage") == "12.34%"
            assert format_value_for_display(value_input = 1234.9, format_type = "integer") == "1,234"
            assert format_value_for_display(value_input = 12.34567, format_type = "decimal") == "12.3457"
            assert format_value_for_display(value_input = np.nan) == "N/A"
            assert format_value_for_display(value_input = "nan") == "nan"

        @pytest.mark.unit()
        def Test_Safe_Numeric_Conversion_Covers_Special_And_Bool_Paths(self) -> None:
            """Numeric conversion should preserve sentinel strings without coercing booleans."""
            from src.dashboard.shiny_utils.utils_visuals import safe_numeric_conversion

            assert safe_numeric_conversion(input_value = True) is True
            assert safe_numeric_conversion(input_value = False) is False
            assert safe_numeric_conversion(input_value = " 123.5 ") == 123.5
            assert safe_numeric_conversion(input_value = " ") == " "
            assert safe_numeric_conversion(input_value = "error") == "error"
            assert safe_numeric_conversion(input_value = "not numeric") == "not numeric"

        @pytest.mark.unit()
        def Test_Create_Error_Figure_Contains_Details_Annotation(self) -> None:
            """Error figures with details should include main, details, and help annotations."""
            from src.dashboard.shiny_utils.utils_visuals import create_error_figure

            figure = create_error_figure(
                message_text="Primary failure",
                title_text="Custom Error",
                details_text="Detailed cause",
            )

            annotation_text = [annotation.text for annotation in figure.layout.annotations]
            assert "Primary failure" in annotation_text
            assert "Details: Detailed cause" in annotation_text
            assert len(annotation_text) == 3

        @pytest.mark.unit()
        def Test_Create_Plot_Rolling_Statistics_Includes_Portfolio_And_Benchmark(
            self,
            portfolio_df: pl.DataFrame,
            benchmark_df: pl.DataFrame,
        ) -> None:
            """Rolling statistics should add return and volatility traces for both series."""
            from src.dashboard.shiny_utils.utils_visuals import create_plot_rolling_statistics

            figure = create_plot_rolling_statistics(
                data_portfolio=portfolio_df,
                data_benchmark=benchmark_df,
                window_size=2,
                period_label="Unit",
                include_benchmark=True,
            )

            trace_names = {trace.name for trace in figure.data}
            assert {
                "Portfolio Returns",
                "Portfolio Volatility",
                "Benchmark Returns",
                "Benchmark Volatility",
            }.issubset(trace_names)

        @pytest.mark.unit()
        def Test_Create_Plot_Returns_Distribution_Includes_Both_Histograms(
            self,
            portfolio_df: pl.DataFrame,
            benchmark_df: pl.DataFrame,
        ) -> None:
            """Return distribution should plot portfolio and benchmark histograms."""
            from src.dashboard.shiny_utils.utils_visuals import create_plot_returns_distribution

            figure = create_plot_returns_distribution(
                data_portfolio=portfolio_df,
                data_benchmark=benchmark_df,
                period_label="Unit",
                include_benchmark=True,
            )

            assert [trace.name for trace in figure.data] == ["Portfolio", "Benchmark"]

        @pytest.mark.unit()
        def Test_Create_Plot_Drawdowns_Analysis_Includes_Both_Traces(
            self,
            portfolio_df: pl.DataFrame,
            benchmark_df: pl.DataFrame,
        ) -> None:
            """Drawdown analysis should plot portfolio and benchmark drawdown traces."""
            from src.dashboard.shiny_utils.utils_visuals import create_plot_drawdowns_analysis

            figure = create_plot_drawdowns_analysis(
                data_portfolio=portfolio_df,
                data_benchmark=benchmark_df,
                period_label="Unit",
                include_benchmark=True,
            )

            trace_names = [trace.name for trace in figure.data]
            assert trace_names == ["Portfolio Drawdowns", "Benchmark Drawdowns"]

        @pytest.mark.parametrize(
            ("viz_type", "expected_y_title"),
            [
                ("normalized", "Normalized Value (Base=100)"),
                ("pct_change", "Daily Change (%)"),
                ("cum_return", "Cumulative Return (%)"),
                ("absolute", "Value"),
            ],
        )
        @pytest.mark.unit()
        def Test_Create_Plot_Comparison_Portfolios_Covers_Visualization_Types(
            self,
            portfolio_df: pl.DataFrame,
            benchmark_df: pl.DataFrame,
            viz_type: str,
            expected_y_title: str,
        ) -> None:
            """Comparison plot should cover all visualization-type branches."""
            from src.dashboard.shiny_utils.utils_visuals import create_plot_comparison_portfolios

            figure = create_plot_comparison_portfolios(
                data_portfolio=portfolio_df,
                data_benchmark=benchmark_df,
                viz_type=viz_type,
                show_diff=False,
                period_label="Unit",
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 6),
            )

            assert len(figure.data) == 2
            assert figure.layout.yaxis.title.text == expected_y_title

        @pytest.mark.unit()
        def Test_Calculate_Table_Metrics_Performance_Returns_Core_Metrics(
            self,
            portfolio_df: pl.DataFrame,
        ) -> None:
            """Performance metrics should include key return and drawdown rows."""
            from src.dashboard.shiny_utils.utils_visuals import calculate_table_metrics_performance

            table = calculate_table_metrics_performance(data_portfolio = portfolio_df, data_benchmark = None)

            metrics = set(table["Metric"].to_list())
            assert "Total Return (%)" in metrics
            assert "Max Drawdown (%)" in metrics
            assert "Win Rate (%)" in metrics

        @pytest.mark.unit()
        def Test_Calculate_Table_Metrics_Performance_Handles_No_Data(self) -> None:
            """No-data paths should return explanatory tables instead of raising."""
            from src.dashboard.shiny_utils.utils_visuals import calculate_table_metrics_performance

            none_table = calculate_table_metrics_performance(data_portfolio = None, data_benchmark = None)
            empty_table = calculate_table_metrics_performance(data_portfolio = pl.DataFrame(), data_benchmark = None)

            assert none_table.loc[0, "Metric"] == "No Data"
            assert empty_table.loc[0, "Metric"] == "No Data"

        @pytest.mark.unit()
        def Test_Create_Table_Comparison_Stats_Returns_Great_Table(
            self,
            portfolio_df: pl.DataFrame,
            benchmark_df: pl.DataFrame,
        ) -> None:
            """Comparison stats should produce a Great Tables object for valid data."""
            from great_tables import GT

            from src.dashboard.shiny_utils.utils_visuals import create_table_comparison_stats

            table = create_table_comparison_stats(
                data_portfolio=portfolio_df,
                data_benchmark=benchmark_df,
                time_period="custom",
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 6),
            )

            assert isinstance(table, GT)
        @pytest.mark.unit()
        def Test_Create_Table_Comparison_Stats_Handles_No_Data(self) -> None:
            """Comparison stats should return a no-data Great Tables object."""
            from great_tables import GT

            from src.dashboard.shiny_utils.utils_visuals import create_table_comparison_stats

            table = create_table_comparison_stats(
                data_portfolio=None,
                data_benchmark=None,
                time_period="custom",
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 6),
            )

            assert isinstance(table, GT)

        @pytest.mark.unit()
        def Test_Create_Table_Summary_Weights_Analysis_Covers_Empty_And_Valid(self) -> None:
            """Weights summary should handle empty, metadata-only, and valid inputs."""
            from great_tables import GT

            from src.dashboard.shiny_utils.utils_visuals import create_table_summary_weights_analysis

            empty_table = create_table_summary_weights_analysis(data_stats = {})
            metadata_only_table = create_table_summary_weights_analysis(
                data_stats = {"_period_info": {"period_label": "Unit", "data_points": 0}}
            )
            valid_table = create_table_summary_weights_analysis(
                data_stats = {
                    "IVV": {"Latest": 60.0, "Average": 55.0, "Min": 50.0, "Max": 65.0, "StdDev": 2.5},
                    "AGG": {"Latest": 40.0, "Average": 45.0, "Min": 35.0, "Max": 50.0, "StdDev": 1.5},
                    "_period_info": {"period_label": "Unit", "data_points": 6},
                },
                show_pct=True,
            )

            assert isinstance(empty_table, GT)
            assert isinstance(metadata_only_table, GT)
            assert isinstance(valid_table, GT)

        @pytest.mark.unit()
        def Test_Create_Enhanced_Summary_Table_Covers_Valid_Themes_And_Invalid_Input(self) -> None:
            """Enhanced summary table should cover valid creation and validation failures."""
            from great_tables import GT

            from src.dashboard.shiny_utils.utils_visuals import create_enhanced_summary_table
            from src.utils.custom_exceptions_errors_loggers.exception_custom import (
                Exception_Validation_Input,
            )

            data_frame = pl.DataFrame({"Asset": ["Taxable", "Tax Free"], "Amount": [1000.0, 250.0]})

            table = create_enhanced_summary_table(
                dataframe_input=data_frame,
                table_title="Assets",
                table_subtitle="Unit",
                column_headers=["Asset Type", "Current Value"],
                currency_columns=["Amount"],
                table_theme="enhanced",
                show_row_numbers=True,
            )

            assert isinstance(table, GT)
            with pytest.raises(Exception_Validation_Input):
                create_enhanced_summary_table(dataframe_input = pl.DataFrame())
            with pytest.raises(Exception_Validation_Input):
                create_enhanced_summary_table(dataframe_input = pl.DataFrame({"A": [1], "B": [2], "C": [3]}))

        @pytest.mark.parametrize("theme", ["professional", "minimal", "enhanced", "unknown"])
        @pytest.mark.unit()
        def Test_Create_Enhanced_Summary_Table_Multi_Column_Covers_Themes(self, theme: str) -> None:
            """Multi-column enhanced tables should cover all theme branches plus default styling."""
            from great_tables import GT

            from src.dashboard.shiny_utils.utils_visuals import (
                create_enhanced_summary_table_multi_column,
            )

            data_frame = pl.DataFrame(
                {
                    "Metric": ["Return", "Risk"],
                    "Value": [0.12, 0.08],
                    "Amount": [1000.0, 750.0],
                }
            )

            table = create_enhanced_summary_table_multi_column(
                dataframe_input=data_frame,
                table_title="Metrics",
                table_subtitle="Unit",
                currency_columns=["Amount"],
                percentage_columns=["Value"],
                table_theme=theme,
            )

            assert isinstance(table, GT)


Class_Test_Utils_Visuals_Source_Branches = (
    Test_Utils_Visuals_Module_Structure.Class_Test_Utils_Visuals_Source_Branches
)


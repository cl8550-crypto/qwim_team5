"""Shared validation and formatting helpers for dashboard visual utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import polars as pl


OUTPUT_DIR = Path("outputs")


def _series_has_non_null_data(*, data_frame: pl.DataFrame, series_name: str) -> bool:
    try:
        non_null_count = data_frame.select(pl.col(series_name).is_not_null().sum()).item()
    except Exception:
        return False

    return (
        not isinstance(non_null_count, bool)
        and isinstance(non_null_count, (int, float))
        and non_null_count > 0
    )


def validate_data_visuals(
    *, data_frame: pl.DataFrame | None = None, selected_series_list: list[str] | None = None) -> tuple[bool, str]:
    """Validate data meets requirements for visualization and analysis using defensive programming."""
    if data_frame is None:
        return False, "No data available"

    if not isinstance(data_frame, pl.DataFrame):
        return False, f"Invalid data type: {type(data_frame).__name__}, expected polars.DataFrame"

    if data_frame.is_empty():
        return False, "Dataset is empty"

    if "Date" not in data_frame.columns:
        return False, "Data is missing required 'Date' column"

    if selected_series_list is not None:
        if not isinstance(selected_series_list, (list, tuple)):
            return (
                False,
                f"Selected series must be list or tuple, got {type(selected_series_list).__name__}",
            )

        if not selected_series_list:
            return False, "No series selected"

        available_columns = set(data_frame.columns)
        selected_series_set = set(selected_series_list)
        available_series = selected_series_set.intersection(available_columns)

        if not available_series:
            return (
                False,
                f"None of the selected series found in data: {', '.join(selected_series_list)}",
            )

        valid_series_found = False
        max_series_to_check = min(3, len(available_series))

        for _idx, series_name in enumerate(list(available_series)[:max_series_to_check]):
            if _series_has_non_null_data(data_frame = data_frame, series_name = series_name):
                valid_series_found = True
                break

        if not valid_series_found:
            return False, "No valid data found in selected series"

    return True, ""


def create_error_figure(
    *, message_text: str, title_text: str = "Error", details_text: str | None = None) -> go.Figure:
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
    if not isinstance(message_text, str):
        message_text = str(message_text) if message_text is not None else "Unknown error"

    if not isinstance(title_text, str):
        title_text = str(title_text) if title_text is not None else "Error"

    if details_text is not None and not isinstance(details_text, str):
        details_text = str(details_text)

    if len(message_text.strip()) == 0:
        message_text = "No error message provided"

    figure_obj = go.Figure()

    layout_config = {
        "title": {
            "text": title_text,
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 16, "color": "#d63384"},
        },
        "template": "plotly_white",
        "height": 400,
        "margin": {"t": 80, "b": 40, "l": 40, "r": 40},
        "xaxis": {"visible": False, "range": [0, 1]},
        "yaxis": {"visible": False, "range": [0, 1]},
        "showlegend": False,
        "plot_bgcolor": "white",
        "paper_bgcolor": "white",
    }

    try:
        figure_obj.update_layout(**layout_config)

        figure_obj.add_annotation(
            text=message_text,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.6,
            showarrow=False,
            font={"size": 14, "color": "#d63384"},
            align="center",
            width=350,
        )

        if details_text:
            figure_obj.add_annotation(
                text=f"Details: {details_text}",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.4,
                showarrow=False,
                font={"size": 12, "color": "#6c757d"},
                align="center",
                width=400,
            )

        figure_obj.add_annotation(
            text="💡 Try selecting different data or adjusting filters",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.2,
            showarrow=False,
            font={"size": 11, "color": "#198754"},
            align="center",
            width=400,
        )

    except Exception:
        basic_figure = go.Figure()
        basic_figure.update_layout(
            title=f"Error: {message_text}",
            template="plotly_white",
            height=400,
        )
        return basic_figure

    return figure_obj


def format_value_for_display(*, value_input: Any, format_type: str = "decimal") -> str:
    """Format a value for display in tables using defensive programming.

    Parameters
    ----------
    value_input : Any
        The value to format for display.
    format_type : str, optional
        How to format numeric values. Supported values:
        - ``"percentage"`` — multiply by 100 and append ``%``.
        - ``"integer"`` — format as a comma-separated integer.
        - ``"decimal"`` — four decimal places (default).

    Returns
    -------
    str
        A formatted string representation of *value_input*.
    """
    if value_input is None:
        return "None"

    if pd.isna(value_input):
        return "N/A"

    if isinstance(value_input, str):
        if value_input.lower() in ["error", "none", "null", "nan"]:
            return value_input
        return value_input

    if isinstance(value_input, bool):
        return str(value_input)

    if isinstance(value_input, (int, float)):
        try:
            numeric_value = float(value_input)
            if format_type == "percentage":
                return f"{numeric_value * 100:.2f}%"
            if format_type == "integer":
                return f"{int(numeric_value):,}"
            return f"{numeric_value:.4f}"
        except (ValueError, OverflowError):
            return str(value_input)

    return str(value_input)


def safe_numeric_conversion(*, input_value: Any) -> Any:
    """Safely convert a value to numeric format using defensive programming."""
    if input_value is None:
        return None

    if pd.isna(input_value):
        return input_value

    if isinstance(input_value, str):
        if input_value.lower() in ["error", "none", "null", "nan", ""]:
            return input_value

        cleaned_value = input_value.strip()
        if len(cleaned_value) == 0:
            return input_value

        try:
            return float(cleaned_value)
        except (ValueError, TypeError):
            return input_value

    if isinstance(input_value, bool):
        return input_value

    if isinstance(input_value, (int, float)):
        try:
            return float(input_value)
        except (ValueError, OverflowError):
            return input_value

    return input_value


__all__ = [
    "OUTPUT_DIR",
    "create_error_figure",
    "format_value_for_display",
    "safe_numeric_conversion",
    "validate_data_visuals",
]

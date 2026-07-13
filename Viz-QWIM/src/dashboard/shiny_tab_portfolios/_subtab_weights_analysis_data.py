"""Data helpers for the portfolio weights analysis subtab."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from typing import Any

import pandas as pd
import polars as pl

from src.dashboard.shiny_utils.utils_data import downsample_dataframe
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Configuration,
    Exception_Validation_Input,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name = __name__)

DEFAULT_SELECTED_COMPONENT_COUNT = 3
DEFAULT_MAX_POINTS = 200

EMPTY_WEIGHTS_SCHEMA: dict[str, pl.DataType] = {"Date": pl.Datetime}


def create_empty_weights_frame(
    *, component_columns: list[str] | None = None) -> pl.DataFrame:
    """Return an empty weights dataframe with the expected schema."""
    frame_data: dict[str, list[Any]] = {"Date": []}
    frame_schema: dict[str, pl.DataType] = {"Date": pl.Datetime}

    for component_name in component_columns or []:
        frame_data[component_name] = []
        frame_schema[component_name] = pl.Float64

    return pl.DataFrame(frame_data, schema=frame_schema)


def _coerce_naive_datetime(
    *, value_datetime: datetime) -> datetime:
    """Return a timezone-naive datetime suitable for dataframe filtering."""
    if value_datetime.tzinfo is None:
        return value_datetime.replace(tzinfo=None)

    return value_datetime.astimezone(UTC).replace(tzinfo=None)


def _coerce_datetime_value(
    *, date_value: Any, use_end_of_day: bool) -> datetime:
    """Convert a date-like value into a naive datetime boundary."""
    if isinstance(date_value, datetime):
        normalized_datetime = _coerce_naive_datetime(value_datetime = date_value)
    elif hasattr(date_value, "year") and hasattr(date_value, "month") and hasattr(date_value, "day"):
        normalized_datetime = datetime(
            date_value.year,
            date_value.month,
            date_value.day,
        )
    else:
        date_text = str(date_value).strip()
        parse_candidates = [
            date_text.replace("Z", "+00:00"),
            date_text[:19].replace("Z", "+00:00"),
            date_text[:10],
        ]

        normalized_datetime = None
        for candidate_text in parse_candidates:
            if not candidate_text:
                continue
            try:
                normalized_datetime = _coerce_naive_datetime(
                    value_datetime = datetime.fromisoformat(candidate_text),
                )
                break
            except ValueError:
                continue

        if normalized_datetime is None:
            raise Exception_Validation_Input(
                f"Unsupported date value for weights analysis: {date_value!s}",
            )

    if use_end_of_day:
        return normalized_datetime.replace(hour=23, minute=59, second=59, microsecond=0)

    return normalized_datetime.replace(hour=0, minute=0, second=0, microsecond=0)


def _is_string_dtype(
    *, date_dtype: pl.DataType) -> bool:
    """Return True when a Polars dtype represents strings."""
    return date_dtype in {pl.Utf8, pl.String}


def _is_date_dtype(
    *, date_dtype: pl.DataType) -> bool:
    """Return True when a Polars dtype represents dates."""
    return date_dtype == pl.Date or str(date_dtype) == "Date"


def _is_datetime_dtype(
    *, date_dtype: pl.DataType) -> bool:
    """Return True when a Polars dtype represents datetimes."""
    return date_dtype == pl.Datetime or str(date_dtype).startswith("Datetime")


def _normalize_weights_date_column(
    *, weights_frame: pl.DataFrame) -> pl.DataFrame:
    """Normalize the Date column into a timezone-naive Polars Datetime."""
    date_dtype = weights_frame.select("Date").dtypes[0]

    if _is_date_dtype(date_dtype = date_dtype):
        return weights_frame.with_columns(
            pl.col("Date").cast(pl.Datetime).alias("Date"),
        )

    if _is_datetime_dtype(date_dtype = date_dtype):
        normalization_attempts = [
            pl.col("Date").dt.replace_time_zone(None).alias("Date"),
            pl.col("Date").cast(pl.Datetime).alias("Date"),
        ]
        for expression_date in normalization_attempts:
            try:
                return weights_frame.with_columns(expression_date)
            except (AttributeError, TypeError, ValueError, pl.exceptions.PolarsError):
                continue

    if _is_string_dtype(date_dtype = date_dtype):
        normalization_attempts = [
            pl.col("Date").str.to_datetime(strict=False).dt.replace_time_zone(None).alias("Date"),
            pl.col("Date").str.to_date(strict=False).cast(pl.Datetime).alias("Date"),
            pl.col("Date").str.slice(0, 10).str.to_date(strict=False).cast(pl.Datetime).alias("Date"),
        ]
        for expression_date in normalization_attempts:
            try:
                return weights_frame.with_columns(expression_date)
            except (AttributeError, TypeError, ValueError, pl.exceptions.PolarsError):
                continue

    normalization_attempts = [
        pl.col("Date").cast(pl.Utf8).str.to_datetime(strict=False).dt.replace_time_zone(None).alias("Date"),
        pl.col("Date").cast(pl.Utf8).str.to_date(strict=False).cast(pl.Datetime).alias("Date"),
        pl.col("Date").cast(pl.Utf8).str.slice(0, 10).str.to_date(strict=False).cast(pl.Datetime).alias("Date"),
    ]
    for expression_date in normalization_attempts:
        try:
            return weights_frame.with_columns(expression_date)
        except (AttributeError, TypeError, ValueError, pl.exceptions.PolarsError):
            continue

    raise Exception_Validation_Input("Unable to normalize weights Date column")


def normalize_weights_source_frame(
    *, weights_source: Any) -> pl.DataFrame:
    """Validate and normalize the source weights dataframe into Polars."""
    if weights_source is None:
        raise Exception_Validation_Input(
            "Portfolio weights data (Weights_My_Portfolio) is None",
        )

    if isinstance(weights_source, pd.DataFrame):  # pandas-boundary
        try:
            weights_frame = pl.from_pandas(weights_source)
        except (TypeError, ValueError) as exc_conversion:
            raise Exception_Validation_Input(
                f"Failed to convert Pandas weights data to Polars: {exc_conversion!s}",
            ) from exc_conversion
    else:
        weights_frame = weights_source

    if not isinstance(weights_frame, pl.DataFrame):
        raise Exception_Validation_Input(
            f"Portfolio weights data must be a Polars DataFrame, got {type(weights_frame)}",
        )

    if weights_frame.is_empty():
        raise Exception_Validation_Input("Portfolio weights data is empty (0 rows)")

    if "Date" not in weights_frame.columns:
        raise Exception_Validation_Input(
            f"Portfolio weights data must contain a 'Date' column. Available: {', '.join(weights_frame.columns)}",
        )

    component_columns = [column_name for column_name in weights_frame.columns if column_name != "Date"]
    if not component_columns:
        raise Exception_Validation_Input(
            "Portfolio weights data must contain at least one ETF component column besides 'Date'",
        )

    weights_frame_normalized = _normalize_weights_date_column(weights_frame = weights_frame.clone())
    weights_frame_normalized = (
        weights_frame_normalized
        .filter(pl.col("Date").is_not_null())
        .with_columns(
            [
                pl.col(component_name).cast(pl.Float64, strict=False).fill_null(0.0).alias(component_name)
                for component_name in component_columns
            ],
        )
        .select(["Date", *component_columns])
        .sort("Date")
    )

    if weights_frame_normalized.is_empty():
        raise Exception_Validation_Input(
            "Portfolio weights data contains no valid dates after normalization",
        )

    _logger.debug(
        "Normalized weights dataframe: rows=%d, components=%d",
        weights_frame_normalized.height,
        len(component_columns),
    )

    return weights_frame_normalized


def resolve_max_points_from_data_utils(
    *, data_utils: Mapping[str, Any] | None) -> int:
    """Resolve the downsampling threshold from dashboard utilities.

    Boolean threshold values are treated as invalid configuration so they fall
    back to the same default used for missing or non-numeric values.
    """
    if data_utils is None:
        return DEFAULT_MAX_POINTS

    max_points_raw = data_utils.get("downsampling_threshold", DEFAULT_MAX_POINTS)
    if isinstance(max_points_raw, bool):
        return DEFAULT_MAX_POINTS

    try:
        max_points_value = int(max_points_raw)
    except (TypeError, ValueError):
        return DEFAULT_MAX_POINTS

    return max_points_value if max_points_value > 0 else DEFAULT_MAX_POINTS


def resolve_weights_anchor_datetime(
    *, weights_frame: pl.DataFrame | None, today_datetime: datetime | None = None) -> datetime:
    """Resolve the effective anchor datetime for preset period calculations."""
    if today_datetime is None:
        anchor_datetime = _coerce_naive_datetime(value_datetime = datetime.now(UTC))
    else:
        anchor_datetime = _coerce_naive_datetime(value_datetime = today_datetime)

    anchor_datetime = anchor_datetime.replace(hour=23, minute=59, second=59, microsecond=0)

    if (
        weights_frame is None
        or not isinstance(weights_frame, pl.DataFrame)
        or weights_frame.is_empty()
        or "Date" not in weights_frame.columns
    ):
        return anchor_datetime

    try:
        max_date_value = weights_frame.select(pl.col("Date").max()).item()
    except (AttributeError, TypeError, ValueError, pl.exceptions.PolarsError):
        return anchor_datetime

    if max_date_value is None:
        return anchor_datetime

    if isinstance(max_date_value, datetime):
        return _coerce_naive_datetime(value_datetime = max_date_value).replace(
            hour=23,
            minute=59,
            second=59,
            microsecond=0,
        )

    return _coerce_datetime_value(date_value = max_date_value, use_end_of_day=True)


def resolve_weights_analysis_date_range(
    *, time_period: str | None, weights_frame: pl.DataFrame | None, custom_date_range: Any = None, today_datetime: datetime | None = None) -> tuple[datetime, datetime]:
    """Resolve the effective weights-analysis date range."""
    normalized_time_period = time_period or "5y"
    anchor_datetime = resolve_weights_anchor_datetime(
        weights_frame = weights_frame,
        today_datetime=today_datetime,
    )

    if normalized_time_period == "custom":
        try:
            if custom_date_range and len(custom_date_range) == 2:
                start_datetime = _coerce_datetime_value(
                    date_value = custom_date_range[0],
                    use_end_of_day=False,
                )
                end_datetime = _coerce_datetime_value(
                    date_value = custom_date_range[1],
                    use_end_of_day=True,
                )
                if start_datetime > end_datetime:
                    return end_datetime, start_datetime
                return start_datetime, end_datetime
        except Exception_Validation_Input:
            pass
        return anchor_datetime - timedelta(days=365 * 5), anchor_datetime

    if normalized_time_period == "1y":
        return anchor_datetime - timedelta(days=365), anchor_datetime
    if normalized_time_period == "3y":
        return anchor_datetime - timedelta(days=365 * 3), anchor_datetime
    if normalized_time_period == "5y":
        return anchor_datetime - timedelta(days=365 * 5), anchor_datetime
    if normalized_time_period == "10y":
        return anchor_datetime - timedelta(days=365 * 10), anchor_datetime
    if normalized_time_period == "ytd":
        return datetime(anchor_datetime.year, 1, 1, 0, 0, 0), anchor_datetime

    return anchor_datetime - timedelta(days=365 * 5), anchor_datetime


def build_weights_calculated_date_range_text(
    *, start_datetime: datetime, end_datetime: datetime) -> str:
    """Build the public date-range text shown beside the time selector."""
    return (
        f"Analysis Period: {start_datetime.strftime('%Y-%m-%d')} "
        f"to {end_datetime.strftime('%Y-%m-%d')}"
    )


def filter_weights_frame_by_date(
    *, weights_frame: pl.DataFrame, start_datetime: datetime, end_datetime: datetime, max_points: int) -> pl.DataFrame:
    """Filter a normalized weights dataframe into the active date range."""
    if weights_frame.is_empty():
        return create_empty_weights_frame()

    filtered_frame = (
        weights_frame
        .filter(pl.col("Date") >= pl.lit(start_datetime))
        .filter(pl.col("Date") <= pl.lit(end_datetime))
        .sort("Date")
    )

    if filtered_frame.is_empty():
        return create_empty_weights_frame(
            component_columns = [column_name for column_name in weights_frame.columns if column_name != "Date"],
        )

    if filtered_frame.height <= max_points:
        return filtered_frame

    try:
        filtered_frame = downsample_dataframe(
            polars_DF = filtered_frame,
            max_points=max_points,
            date_column="Date",
        )
    except Exception_Configuration:
        pass

    return filtered_frame.sort("Date")


def resolve_available_ETF_components(
    *, weights_frame: pl.DataFrame) -> list[str]:
    """Return the ETF component columns available in the weights dataframe.

    Boolean columns are excluded because downstream charting and report helpers
    expect numeric ETF weight series and should not treat ``True`` or ``False``
    as weights.
    """
    if weights_frame.is_empty():
        return []

    return [
        column_name
        for column_name in weights_frame.columns
        if column_name != "Date" and weights_frame.schema.get(column_name) != pl.Boolean
    ]


def resolve_selected_ETF_components(
    *, available_components: list[str], select_all_components: bool | None, checkbox_values_by_component: Mapping[str, bool] | None, default_selected_count: int = DEFAULT_SELECTED_COMPONENT_COUNT) -> list[str]:
    """Resolve the ordered ETF component selection for the active UI state."""
    if not available_components:
        return []

    if select_all_components:
        return available_components

    if checkbox_values_by_component is None:
        return available_components[:default_selected_count]

    selected_components = [
        component_name
        for component_name in available_components
        if checkbox_values_by_component.get(component_name, False)
    ]

    if selected_components:
        return selected_components

    return available_components[:default_selected_count]


def filter_weights_frame_by_selected_ETF_components(
    *, weights_frame: pl.DataFrame, selected_components: list[str]) -> pl.DataFrame:
    """Keep only Date and selected ETF component columns."""
    if weights_frame.is_empty() or not selected_components:
        return create_empty_weights_frame()

    valid_components = [
        component_name
        for component_name in selected_components
        if component_name in weights_frame.columns
    ]
    if not valid_components:
        return create_empty_weights_frame()

    return weights_frame.select(["Date", *valid_components])


def build_weights_statistics_rows(
    *, weights_frame: pl.DataFrame) -> list[dict[str, float | str]]:
    """Build summary statistic rows for the selected ETF components."""
    if weights_frame.is_empty():
        return []

    component_columns = resolve_available_ETF_components(weights_frame = weights_frame)
    if not component_columns:
        return []

    statistics_rows: list[dict[str, float | str]] = []
    for component_name in component_columns:
        component_series = weights_frame.get_column(component_name)
        component_values = component_series.to_list()
        if any(isinstance(component_value, bool) for component_value in component_values):
            continue

        std_value = component_series.std()
        std_value_normalized = float(std_value) if std_value is not None else 0.0
        if std_value_normalized != std_value_normalized:
            std_value_normalized = 0.0

        statistics_rows.append(
            {
                "Component": component_name,
                "Current": float(component_series[-1]),
                "Average": float(component_series.mean()),
                "Min": float(component_series.min()),
                "Max": float(component_series.max()),
                "Std Dev": std_value_normalized,
            },
        )

    return statistics_rows


def build_report_weights_statistics_payload(
    *, statistics_rows: list[dict[str, float | str]]) -> list[dict[str, float | str]]:
    """Build the report-compatible weights statistics payload."""
    payload_rows: list[dict[str, float | str]] = []
    for row_stats in statistics_rows:
        numeric_values = [
            row_stats["Current"],
            row_stats["Average"],
            row_stats["Min"],
            row_stats["Max"],
            row_stats["Std Dev"],
        ]
        if any(isinstance(numeric_value, bool) for numeric_value in numeric_values):
            continue

        payload_rows.append(
            {
                "component": str(row_stats["Component"]),
                "current_weight": float(row_stats["Current"]),
                "mean_weight": float(row_stats["Average"]),
                "min_weight": float(row_stats["Min"]),
                "max_weight": float(row_stats["Max"]),
                "std_weight": float(row_stats["Std Dev"]),
            },
        )

    return payload_rows
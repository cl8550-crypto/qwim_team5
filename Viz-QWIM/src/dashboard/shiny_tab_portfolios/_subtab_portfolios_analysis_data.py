"""Data helpers for the portfolio analysis subtab."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import polars as pl

from src.dashboard.shiny_utils.utils_data import downsample_dataframe
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Configuration,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name = __name__)

_EMPTY_ANALYSIS_SCHEMA: dict[str, pl.DataType] = {
    "Date": pl.Datetime,
    "Value": pl.Float64,
}


def create_empty_analysis_frame() -> pl.DataFrame:
    """Return an empty analysis dataframe with the expected schema."""
    return pl.DataFrame({"Date": [], "Value": []}, schema=_EMPTY_ANALYSIS_SCHEMA)


def _resolve_today(*, today_datetime: datetime | None = None) -> datetime:
    """Return the supplied datetime or the current UTC timestamp."""
    return today_datetime if today_datetime is not None else datetime.now(UTC)


def _coerce_date_value(*, date_value: Any) -> str:
    """Convert a date-like value into the YYYY-MM-DD string used by filters."""
    if hasattr(date_value, "strftime"):
        return date_value.strftime("%Y-%m-%d")
    return str(date_value)[:10]


def resolve_analysis_date_range(
    *, time_period: str | None, custom_date_range: Any = None, today_datetime: datetime | None = None) -> tuple[str, str]:
    """Resolve the analysis date bounds for a time-period selection."""
    normalized_time_period = time_period or "1y"
    current_datetime = _resolve_today(today_datetime = today_datetime)
    today_str = current_datetime.strftime("%Y-%m-%d")

    if normalized_time_period == "custom":
        try:
            if custom_date_range and len(custom_date_range) == 2:
                return (
                    _coerce_date_value(date_value = custom_date_range[0]),
                    _coerce_date_value(date_value = custom_date_range[1]),
                )
        except (TypeError, ValueError, AttributeError):
            pass

        fallback_start_datetime = current_datetime - timedelta(days=365)
        return fallback_start_datetime.strftime("%Y-%m-%d"), today_str

    if normalized_time_period == "1y":
        start_datetime = current_datetime - timedelta(days=365)
    elif normalized_time_period == "3y":
        start_datetime = current_datetime - timedelta(days=365 * 3)
    elif normalized_time_period == "5y":
        start_datetime = current_datetime - timedelta(days=365 * 5)
    elif normalized_time_period == "10y":
        start_datetime = current_datetime - timedelta(days=365 * 10)
    elif normalized_time_period == "ytd":
        start_datetime = datetime(current_datetime.year, 1, 1, tzinfo=UTC)
    else:
        start_datetime = current_datetime - timedelta(days=365)

    return start_datetime.strftime("%Y-%m-%d"), today_str


def build_calculated_date_range_text(
    *, time_period: str | None, today_datetime: datetime | None = None) -> str:
    """Build the preset period label shown beside the date picker."""
    normalized_time_period = time_period or "1y"
    if normalized_time_period == "custom":
        return ""

    start_date_str, end_date_str = resolve_analysis_date_range(
        time_period = normalized_time_period,
        today_datetime=today_datetime,
    )
    return f"📅 {start_date_str} to {end_date_str}"


def _is_string_dtype(*, date_dtype: pl.DataType) -> bool:
    """Return True when a Polars dtype represents strings."""
    return date_dtype in {pl.Utf8, pl.String}


def _is_date_dtype(*, date_dtype: pl.DataType) -> bool:
    """Return True when a Polars dtype represents dates."""
    return date_dtype == pl.Date or str(date_dtype) == "Date"


def _is_datetime_dtype(*, date_dtype: pl.DataType) -> bool:
    """Return True when a Polars dtype represents datetimes."""
    return date_dtype == pl.Datetime or str(date_dtype).startswith("Datetime")


def _normalize_date_strings(*, data_frame: pl.DataFrame, label: str) -> pl.DataFrame:
    """Normalize mixed Date column dtypes into YYYY-MM-DD strings."""
    date_dtype = data_frame.select("Date").dtypes[0]
    _logger.debug("%s date column type: %s", label, date_dtype)

    if _is_string_dtype(date_dtype = date_dtype):
        normalization_attempts = (
            (
                pl.col("Date").str.to_datetime(strict=False).dt.strftime("%Y-%m-%d").alias("Date_String"),
                "Converted string to datetime then to YYYY-MM-DD format",
            ),
            (
                pl.col("Date").str.to_date(strict=False).dt.strftime("%Y-%m-%d").alias("Date_String"),
                "Converted string to date then to YYYY-MM-DD format",
            ),
            (
                pl.col("Date").str.slice(0, 10).alias("Date_String"),
                "Using string as-is (first 10 characters)",
            ),
        )

        for expression, message in normalization_attempts:
            try:
                normalized_frame = data_frame.with_columns([expression])
                _logger.debug("%s: %s", label, message)
                return normalized_frame
            except (
                AttributeError,
                TypeError,
                ValueError,
                pl.exceptions.PolarsError,
            ):
                continue

    if _is_date_dtype(date_dtype = date_dtype) or _is_datetime_dtype(date_dtype = date_dtype):
        normalized_frame = data_frame.with_columns(
            [pl.col("Date").dt.strftime("%Y-%m-%d").alias("Date_String")],
        )
        _logger.debug("%s: Converted temporal dtype to YYYY-MM-DD string format", label)
        return normalized_frame

    normalization_attempts = (
        (
            pl.col("Date")
            .cast(pl.Utf8)
            .str.to_datetime(strict=False)
            .dt.strftime("%Y-%m-%d")
            .alias("Date_String"),
            "Cast unknown type to string, parsed as datetime, converted to YYYY-MM-DD",
        ),
        (
            pl.col("Date").cast(pl.Utf8).str.slice(0, 10).alias("Date_String"),
            "Cast to string and took first 10 characters",
        ),
    )

    for expression, message in normalization_attempts:
        try:
            normalized_frame = data_frame.with_columns([expression])
            _logger.debug("%s: %s", label, message)
            return normalized_frame
        except (AttributeError, TypeError, ValueError, pl.exceptions.PolarsError):
            continue

    return data_frame.with_columns(
        [pl.col("Date").cast(pl.Utf8).str.slice(0, 10).alias("Date_String")],
    )


def filter_analysis_dataframe(
    *, data_frame: pl.DataFrame | None, start_date_str: str, end_date_str: str, label: str) -> pl.DataFrame:
    """Filter a portfolio-like dataframe into the active analysis window."""
    if (
        data_frame is None
        or not isinstance(data_frame, pl.DataFrame)
        or data_frame.is_empty()
    ):
        _logger.debug("%s data is None, not a DataFrame, or empty", label)
        return create_empty_analysis_frame()

    if "Date" not in data_frame.columns or "Value" not in data_frame.columns:
        _logger.warning("%s data missing required columns", label)
        return create_empty_analysis_frame()

    normalized_frame = _normalize_date_strings(data_frame = data_frame, label=label)
    filtered_frame = normalized_frame.filter(pl.col("Date_String").is_not_null()).filter(
        (pl.col("Date_String") >= start_date_str)
        & (pl.col("Date_String") <= end_date_str),
    )

    _logger.debug("%s rows after date filtering: %d", label, filtered_frame.height)

    if filtered_frame.is_empty():
        _logger.warning(
            "%s filtering removed all data — filter range: %s to %s",
            label,
            start_date_str,
            end_date_str,
        )
        return create_empty_analysis_frame()

    try:
        return (
            filtered_frame.with_columns(
                [pl.col("Date_String").str.to_datetime(format="%Y-%m-%d").alias("Date")],
            )
            .select(["Date", "Value"])
            .sort("Date")
        )
    except (AttributeError, TypeError, ValueError, pl.exceptions.PolarsError) as exc:
        _logger.warning("%s: Error converting Date_String to Datetime: %s", label, exc)
        return create_empty_analysis_frame()


def build_filtered_analysis_data(
    *,
    data_portfolio: pl.DataFrame | None,
    data_benchmark: pl.DataFrame | None,
    time_period: str | None,
    custom_date_range: Any = None,
    today_datetime: datetime | None = None,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Build the filtered portfolio and benchmark frames for analysis outputs."""
    if data_portfolio is None and data_benchmark is None:
        return create_empty_analysis_frame(), create_empty_analysis_frame()

    try:
        start_date_str, end_date_str = resolve_analysis_date_range(
            time_period = time_period,
            custom_date_range=custom_date_range,
            today_datetime=today_datetime,
        )

        filtered_portfolio = filter_analysis_dataframe(
            data_frame = data_portfolio,
            start_date_str=start_date_str,
            end_date_str=end_date_str,
            label="Portfolio",
        )
        filtered_benchmark = filter_analysis_dataframe(
            data_frame = data_benchmark,
            start_date_str=start_date_str,
            end_date_str=end_date_str,
            label="Benchmark",
        )

        if not filtered_portfolio.is_empty():
            filtered_portfolio = downsample_dataframe(
                polars_DF = filtered_portfolio,
                max_points=200,
                date_column="Date",
            )

        if not filtered_benchmark.is_empty():
            filtered_benchmark = downsample_dataframe(
                polars_DF = filtered_benchmark,
                max_points=200,
                date_column="Date",
            )

        return filtered_portfolio, filtered_benchmark

    except (AttributeError, TypeError, ValueError, pl.exceptions.PolarsError) as exc:
        raise Exception_Configuration(f"Error in get_filtered_analysis_data: {exc}") from exc
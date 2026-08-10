"""Data-loading utilities for covariance-estimation analysis."""

from __future__ import annotations

from pathlib import Path

import polars as pl

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)


def load_etf_prices(
    *,
    file_path: str | Path = "inputs/raw/data_ETFs.csv",
) -> pl.DataFrame:
    """Load ETF price data from CSV.

    Parameters
    ----------
    file_path
        Path to the ETF price CSV file.

    Returns
    -------
    pl.DataFrame
        DataFrame containing a parsed ``Date`` column and ETF price columns.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise Exception_Validation_Input(
            f"ETF data file not found: {file_path}"
        )

    prices = pl.read_csv(
        file_path,
        try_parse_dates=True,
    )

    if "Date" not in prices.columns:
        raise Exception_Validation_Input(
            "ETF data must contain a 'Date' column."
        )

    asset_columns = [
        column for column in prices.columns if column != "Date"
    ]

    if len(asset_columns) < 2:
        raise Exception_Validation_Input(
            "ETF data must contain at least two asset columns."
        )

    return prices.sort("Date")


def prices_to_returns(
    *,
    prices: pl.DataFrame,
) -> pl.DataFrame:
    """Convert ETF price levels into simple daily returns."""
    if "Date" not in prices.columns:
        raise Exception_Validation_Input(
            "Price data must contain a 'Date' column."
        )

    asset_columns = [
        column for column in prices.columns if column != "Date"
    ]

    returns = prices.select(
        [
            pl.col("Date"),
            *[
                pl.col(column)
                .pct_change()
                .alias(column)
                for column in asset_columns
            ],
        ]
    ).drop_nulls()

    return returns


def load_etf_returns(
    *,
    file_path: str | Path = "inputs/raw/data_ETFs.csv",
) -> pl.DataFrame:
    """Load ETF prices and convert them into daily returns."""
    prices = load_etf_prices(file_path=file_path)

    return prices_to_returns(prices=prices)
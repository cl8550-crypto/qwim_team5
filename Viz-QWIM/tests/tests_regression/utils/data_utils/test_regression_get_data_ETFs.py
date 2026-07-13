"""Regression baselines for get_data_ETFs full output and default ticker ordering."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pandas as pd
import polars as pl
import pytest
from polars.testing import assert_frame_equal

import src.utils.data_utils.get_data_ETFs as module


BASELINE_PARQUET_PATH = (
    Path(__file__).resolve().parents[3]
    / "regression_data"
    / "utils"
    / "get_data_ETFs__sample_output.parquet"
)
DEFAULT_ETF_TICKERS = [
    "IVV",
    "IJH",
    "IWM",
    "EFA",
    "EEM",
    "AGG",
    "SPTL",
    "HYG",
    "SPBO",
    "IYR",
    "DBC",
    "GLD",
]


@pytest.fixture(autouse=True)
def _clear_etf_cache():
    """Clear the module-level ETF cache around each test."""
    module._ETF_CACHE.clear()
    yield
    module._ETF_CACHE.clear()


@pytest.fixture(scope="module")
def baseline_df() -> pl.DataFrame:
    """Load the committed Parquet baseline for get_etf_data().

    Returns
    -------
    pl.DataFrame
        The canonical sample output DataFrame stored in
        ``tests/regression_data/utils/get_data_ETFs__sample_output.parquet``.
    """
    return pl.read_parquet(BASELINE_PARQUET_PATH)


def _make_bulk_download_frame(*, tickers: list[str]) -> pd.DataFrame:
    """Build a MultiIndex pandas DataFrame matching the yfinance bulk shape.

    Parameters
    ----------
    tickers : list[str]
        ETF ticker symbols to include as columns.

    Returns
    -------
    pd.DataFrame
        MultiIndex DataFrame with ``(Ticker, 'Close')`` columns and
        deterministic price values over three business days.
    """
    index = pd.date_range("2024-01-02", periods=3, freq="B")
    data: dict[tuple[str, str], list[float]] = {}
    for idx_ticker, ticker in enumerate(tickers):
        data[(ticker, "Close")] = [
            100.0 + idx_ticker * 10 + idx_row for idx_row in range(3)
        ]
    frame = pd.DataFrame(data, index=index)
    frame.columns = pd.MultiIndex.from_tuples(frame.columns)
    return frame


class Class_Test_Regression_Get_Data_ETFs:
    """Regression tests for stable get_etf_data public output."""

    @pytest.mark.regression()
    def Test_Full_Output_Matches_Parquet_Baseline(
        self,
        baseline_df: pl.DataFrame,
    ) -> None:
        """Full DataFrame output matches the committed Parquet baseline.

        Notes
        -----
        Compares both schema and values using
        ``polars.testing.assert_frame_equal``.
        """
        # Arrange
        mock_frame = _make_bulk_download_frame(tickers=DEFAULT_ETF_TICKERS)

        # Act
        with patch("yfinance.download", return_value=mock_frame):
            result = module.get_etf_data(
                tickers=DEFAULT_ETF_TICKERS,
                start_date="2024-01-02",
                end_date="2024-01-05",
            )

        # Assert
        assert_frame_equal(result, baseline_df)

    @pytest.mark.regression()
    def Test_Default_Ticker_Order_Remains_Stable(
        self,
        baseline_df: pl.DataFrame,
    ) -> None:
        """Default ticker column order remains unchanged for downstream CSV consumers.

        Notes
        -----
        Verifies that ``Date`` is first, followed by the 12 default ETF
        tickers in the canonical order.
        """
        # Arrange
        mock_frame = _make_bulk_download_frame(tickers=DEFAULT_ETF_TICKERS)

        # Act
        with patch("yfinance.download", return_value=mock_frame):
            result = module.get_etf_data(
                tickers=DEFAULT_ETF_TICKERS,
                start_date="2024-01-02",
                end_date="2024-01-05",
            )

        # Assert
        assert result.columns == baseline_df.columns
        assert result.columns == ["Date", *DEFAULT_ETF_TICKERS]
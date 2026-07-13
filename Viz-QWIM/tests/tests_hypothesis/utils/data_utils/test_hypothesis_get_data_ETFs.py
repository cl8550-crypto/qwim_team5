"""Property-based tests for get_data_ETFs utility helpers."""

from __future__ import annotations

from unittest.mock import patch

import pandas as pd
import polars as pl
import pytest

from hypothesis import given, settings
from hypothesis import strategies as st

import src.utils.data_utils.get_data_ETFs as module


TICKER_POOL = ["SPY", "QQQ", "IVV", "AGG", "EFA", "GLD"]
TICKER_LIST_STRATEGY = st.lists(
    st.sampled_from(TICKER_POOL),
    min_size=1,
    max_size=4,
    unique=True,
)
ORDERED_TICKER_LIST_STRATEGY = st.lists(
    st.sampled_from(TICKER_POOL),
    min_size=2,
    max_size=4,
    unique=True,
)
ROW_COUNT_STRATEGY = st.integers(min_value=1, max_value=5)


@pytest.fixture(autouse=True)
def _clear_etf_cache():
    """Clear the module-level ETF cache around each test."""
    module._ETF_CACHE.clear()
    yield
    module._ETF_CACHE.clear()


def _make_bulk_download_frame(tickers: list[str], row_count: int) -> pd.DataFrame:
    """Build a MultiIndex pandas DataFrame matching the yfinance bulk shape."""
    index = pd.date_range("2024-01-02", periods=row_count, freq="B")
    data: dict[tuple[str, str], list[float]] = {}
    for ticker_index, ticker in enumerate(tickers):
        data[(ticker, "Close")] = [
            100.0 + ticker_index * 10 + row_index for row_index in range(row_count)
        ]
    frame = pd.DataFrame(data, index=index)
    frame.columns = pd.MultiIndex.from_tuples(frame.columns)
    return frame


class Class_Test_Hypothesis_Get_Data_ETFs:
    """Property-based tests for public schema and cache invariants."""

    @pytest.mark.unit()
    @given(tickers=TICKER_LIST_STRATEGY, row_count=ROW_COUNT_STRATEGY)
    @settings(max_examples=40)
    def Test_Get_Etf_Data_Preserves_Input_Order_And_Dtypes(
        self,
        tickers: list[str],
        row_count: int,
    ) -> None:
        """Bulk downloads preserve caller ticker order and public dtypes."""
        module._ETF_CACHE.clear()
        with patch(
            "yfinance.download",
            return_value=_make_bulk_download_frame(tickers, row_count),
        ):
            result = module.get_etf_data(
                tickers=tickers,
                start_date="2024-01-02",
                end_date="2024-01-31",
            )

        assert result.columns == ["Date", *tickers]
        assert result.schema["Date"] == pl.Date
        assert result.shape[0] == row_count
        for ticker in tickers:
            assert result.schema[ticker] == pl.Float64

    @pytest.mark.unit()
    @given(tickers=ORDERED_TICKER_LIST_STRATEGY)
    @settings(max_examples=30)
    def Test_Cache_Key_Distinguishes_Ticker_Order(self, tickers: list[str]) -> None:
        """A reversed ticker request must not reuse a cached frame with stale column order."""
        reversed_tickers = list(reversed(tickers))

        module._ETF_CACHE.clear()
        with patch(
            "yfinance.download",
            side_effect=[
                _make_bulk_download_frame(tickers, 3),
                _make_bulk_download_frame(reversed_tickers, 3),
            ],
        ) as mock_download:
            first_result = module.get_etf_data(
                tickers=tickers,
                start_date="2024-01-02",
                end_date="2024-01-05",
            )
            second_result = module.get_etf_data(
                tickers=reversed_tickers,
                start_date="2024-01-02",
                end_date="2024-01-05",
            )

        assert first_result.columns == ["Date", *tickers]
        assert second_result.columns == ["Date", *reversed_tickers]
        assert mock_download.call_count == 2
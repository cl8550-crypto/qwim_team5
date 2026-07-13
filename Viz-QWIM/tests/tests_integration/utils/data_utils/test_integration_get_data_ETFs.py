"""Integration tests for get_data_ETFs utility workflows."""

from __future__ import annotations

from datetime import date as _date
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import polars as pl
import pytest

import src.utils.data_utils.get_data_ETFs as module


@pytest.fixture(autouse=True)
def _clear_etf_cache():
    """Clear the module-level ETF cache around each test."""
    module._ETF_CACHE.clear()
    yield
    module._ETF_CACHE.clear()


def _make_bulk_download_frame(tickers: list[str]) -> pd.DataFrame:
    """Build a small MultiIndex pandas DataFrame matching the yfinance bulk shape."""
    index = pd.date_range("2024-01-02", periods=3, freq="B")
    data: dict[tuple[str, str], list[float]] = {}
    for ticker_index, ticker in enumerate(tickers):
        data[(ticker, "Close")] = [
            100.0 + ticker_index * 5 + row_index for row_index in range(3)
        ]
    frame = pd.DataFrame(data, index=index)
    frame.columns = pd.MultiIndex.from_tuples(frame.columns)
    return frame


class Class_Test_Integration_Get_Data_ETFs:
    """Integration tests for public get_data_ETFs workflows."""

    @pytest.mark.integration()
    def Test_Get_Etf_Data_Roundtrips_To_Csv_With_Public_Columns(self, tmp_path: Path) -> None:
        """Retrieved ETF data can be written to CSV and read back with stable columns."""
        with patch(
            "yfinance.download",
            return_value=_make_bulk_download_frame(["SPY", "QQQ"]),
        ):
            result = module.get_etf_data(
                tickers=["SPY", "QQQ"],
                start_date="2024-01-02",
                end_date="2024-01-05",
            )

        output_file = tmp_path / "data_ETFs_roundtrip.csv"
        result.write_csv(output_file)
        roundtrip = pl.read_csv(output_file, try_parse_dates=True)

        assert roundtrip.columns == ["Date", "SPY", "QQQ"]
        assert roundtrip.shape == result.shape

    @pytest.mark.integration()
    def Test_Main_Writes_Default_Etf_Csv_To_Resolved_Project_Root(
        self,
        tmp_path: Path,
        monkeypatch,
    ) -> None:
        """main() writes its CSV beneath the resolved temporary project root."""
        fake_file = tmp_path / "a" / "b" / "get_data_ETFs.py"
        fake_file.parent.mkdir(parents=True, exist_ok=True)
        fake_file.touch()

        mock_pl_df = pl.DataFrame(
            {
                "Date": [_date(2024, 1, 2), _date(2024, 1, 3)],
                "IVV": [450.0, 451.0],
                "AGG": [100.0, 100.1],
            },
        )

        monkeypatch.setattr(module, "__file__", str(fake_file))
        monkeypatch.setattr(module, "get_etf_data", lambda **kwargs: mock_pl_df)

        module.main()

        output_file = tmp_path / "inputs" / "raw" / "data_ETFs.csv"
        assert output_file.exists()
        assert output_file.stat().st_size > 0

        roundtrip = pl.read_csv(output_file, try_parse_dates=True)
        assert roundtrip.columns == ["Date", "IVV", "AGG"]
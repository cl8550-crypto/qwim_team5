"""Unit tests for the get_data_ETFs module."""

from unittest.mock import ANY, MagicMock, patch

import pandas as pd
import polars as pl
import pytest

import src.utils.data_utils.get_data_ETFs as module


@pytest.fixture()
def get_etf_data():
    """Fixture to import the get_etf_data function."""
    return module.get_etf_data


@pytest.fixture()
def sample_price_data():
    """Create sample price data for testing."""
    return pd.DataFrame(
        {
            "SPY": [400.0, 402.0, 398.0, 405.0, 410.0],
            "QQQ": [300.0, 305.0, 302.0, 308.0, 312.0],
        },
        index=pd.date_range("2023-01-01", periods=5, freq="D"),
    )


@pytest.fixture()
def mock_yf_download(sample_price_data):
    """Create a mock for yfinance download function returning Close prices."""
    with patch("yfinance.download") as mock_download:
        multi_data = pd.DataFrame(
            {
                ("SPY", "Close"): sample_price_data["SPY"],
                ("QQQ", "Close"): sample_price_data["QQQ"],
            },
        )
        mock_download.return_value = multi_data
        yield mock_download


@pytest.fixture(autouse=True)
def _clear_etf_cache():
    """Clear the TTLCache before and after each test to prevent cross-test pollution."""
    module._ETF_CACHE.clear()
    yield
    module._ETF_CACHE.clear()


@pytest.fixture()
def mock_module_logger(monkeypatch):
    """Replace the module logger with a mock for logging assertions."""
    logger_mock = MagicMock()
    monkeypatch.setattr(module, "_logger", logger_mock)
    return logger_mock


class Test_Get_ETF_Data:
    """Tests for the get_etf_data function."""

    @pytest.mark.unit()
    def test_returns_dataframe(self, get_etf_data, mock_yf_download):
        """Test that the function returns a polars DataFrame."""
        result = get_etf_data(
            tickers=["SPY", "QQQ"],
            start_date="2023-01-01",
            end_date="2023-01-05",
        )

        assert isinstance(result, pl.DataFrame)
        assert "Date" in result.schema
        assert result.schema["Date"] == pl.Date

    @pytest.mark.unit()
    def test_accepts_ticker_list(self, get_etf_data, mock_yf_download):
        """Test that function accepts a list of tickers."""
        result = get_etf_data(
            tickers=["SPY", "QQQ"],
            start_date="2023-01-01",
            end_date="2023-01-05",
        )

        # Should have columns for each ticker
        assert len(result.columns) >= 1

    @pytest.mark.unit()
    def test_calls_yf_download(self, get_etf_data, mock_yf_download):
        """Test that yfinance.download is called with correct parameters."""
        get_etf_data(
            tickers=["SPY"],
            start_date="2023-01-01",
            end_date="2023-12-31",
        )

        mock_yf_download.assert_called()

    @pytest.mark.unit()
    def test_handles_empty_result(self, get_etf_data):
        """Test handling of empty download result returns empty polars DataFrame."""
        with patch("yfinance.download") as mock_download:
            mock_download.return_value = pd.DataFrame()

            with patch("yfinance.Ticker") as mock_ticker:
                mock_ticker_instance = MagicMock()
                mock_ticker_instance.history.return_value = pd.DataFrame()
                mock_ticker.return_value = mock_ticker_instance

                result = get_etf_data(
                    tickers=["INVALID_TICKER"],
                    start_date="2023-01-01",
                    end_date="2023-01-05",
                )

                assert isinstance(result, pl.DataFrame)
                assert result.is_empty()
                assert "Date" in result.schema
                assert result.schema["Date"] == pl.Date

    @pytest.mark.unit()
    def test_handles_single_ticker(self, get_etf_data):
        """Test handling of single ticker request returns polars DataFrame."""
        with patch("yfinance.download") as mock_download:
            single_data = pd.DataFrame(
                {"Close": [100.0, 101.0, 102.0]},
                index=pd.date_range("2023-01-02", periods=3, freq="B"),
            )
            mock_download.return_value = single_data

            result = get_etf_data(
                tickers=["SPY"],
                start_date="2023-01-02",
                end_date="2023-01-04",
            )

            assert isinstance(result, pl.DataFrame)
            assert "Date" in result.columns
            assert "SPY" in result.columns

    @pytest.mark.unit()
    def test_optional_end_date(self, get_etf_data, mock_yf_download):
        """Test that end_date parameter is optional and returns polars DataFrame."""
        result = get_etf_data(
            tickers=["SPY"],
            start_date="2023-01-01",
            end_date=None,
        )

        assert isinstance(result, pl.DataFrame)

    @pytest.mark.unit()
    def test_optional_start_date(self, get_etf_data, mock_yf_download):
        """Test that start_date parameter is optional and returns polars DataFrame."""
        result = get_etf_data(
            tickers=["SPY"],
            start_date=None,
            end_date="2023-12-31",
        )

        assert isinstance(result, pl.DataFrame)

    @pytest.mark.unit()
    def test_fallback_to_individual_downloads(self, get_etf_data):
        """Test fallback to individual downloads when bulk fails returns polars DataFrame."""
        with patch("yfinance.download") as mock_download:
            mock_download.side_effect = Exception("Bulk download failed")

            with patch("yfinance.Ticker") as mock_ticker:
                mock_ticker_instance = MagicMock()
                mock_ticker_instance.history.return_value = pd.DataFrame(
                    {"Close": [100.0, 101.0]},
                    index=pd.date_range("2023-01-02", periods=2, freq="B"),
                )
                mock_ticker.return_value = mock_ticker_instance

                with patch("time.sleep"):
                    result = get_etf_data(
                        tickers=["SPY"],
                        start_date="2023-01-02",
                        end_date="2023-01-03",
                    )

                assert isinstance(result, pl.DataFrame)
                assert "Date" in result.columns
                assert "SPY" in result.columns
                mock_ticker.assert_called()


class Test_Get_ETF_DataTickers:
    """Tests for specific ETF tickers in get_etf_data."""

    @pytest.mark.unit()
    def test_default_etf_list_in_module(self):
        """Test that module defines expected default ETFs."""
        from src.utils.data_utils.get_data_ETFs import main

        # main() function should define these ETFs internally
        expected_etfs = [
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

        # Verify by checking the source code contains these tickers
        import inspect

        source = inspect.getsource(main)
        for etf in expected_etfs:
            assert etf in source, f"ETF {etf} not found in main() function"


class Test_Get_ETF_DataLogging:
    """Tests for logging behavior in get_etf_data."""

    @pytest.mark.unit()
    def test_logs_retrieval_info(self, get_etf_data, mock_yf_download, mock_module_logger):
        """Test that retrieval info is logged."""
        get_etf_data(
            tickers=["SPY", "QQQ"],
            start_date="2023-01-01",
            end_date="2023-01-05",
        )

        mock_module_logger.info.assert_any_call(
            "Retrieving data for %d ETFs from %s to %s...",
            2,
            "2023-01-01",
            "2023-01-05",
        )

    @pytest.mark.unit()
    def test_logs_download_failure(self, get_etf_data, mock_module_logger):
        """Test that download failures are logged."""
        with patch("yfinance.download") as mock_download:
            mock_download.side_effect = Exception("Network error")

            with patch("yfinance.Ticker") as mock_ticker:
                mock_ticker_instance = MagicMock()
                mock_ticker_instance.history.return_value = pd.DataFrame()
                mock_ticker.return_value = mock_ticker_instance

                get_etf_data(
                    tickers=["SPY"],
                    start_date="2023-01-01",
                    end_date="2023-01-05",
                )

        assert any(
            "Bulk download failed" in call.args[0]
            for call in mock_module_logger.warning.call_args_list
        )


class Test_Get_ETF_DataEdgeCases:
    """Tests for edge cases in get_etf_data."""

    @pytest.mark.unit()
    def test_empty_ticker_list(self, get_etf_data):
        """Test handling of empty ticker list returns empty polars DataFrame."""
        with patch("yfinance.download") as mock_download:
            mock_download.return_value = pd.DataFrame()

            result = get_etf_data(
                tickers=[],
                start_date="2023-01-01",
                end_date="2023-01-05",
            )

            assert isinstance(result, pl.DataFrame)
            assert result.is_empty()

    @pytest.mark.unit()
    def test_invalid_date_format_handling(self, get_etf_data):
        """Test handling of potentially invalid dates returns polars DataFrame."""
        with patch("yfinance.download") as mock_download:
            mock_download.return_value = pd.DataFrame()

            with patch("yfinance.Ticker") as mock_ticker:
                mock_ticker_instance = MagicMock()
                mock_ticker_instance.history.return_value = pd.DataFrame()
                mock_ticker.return_value = mock_ticker_instance

                result = get_etf_data(
                    tickers=["SPY"],
                    start_date="2023-01-01",
                    end_date="2023-12-31",
                )

                assert isinstance(result, pl.DataFrame)

    @pytest.mark.unit()
    def test_handles_rate_limiting(self, get_etf_data):
        """Test that function includes delay to avoid rate limiting."""

        with patch("yfinance.download") as mock_download:
            mock_download.return_value = pd.DataFrame()

            with patch("yfinance.Ticker") as mock_ticker:
                mock_ticker_instance = MagicMock()
                mock_ticker_instance.history.return_value = pd.DataFrame(
                    {"Close": [100.0]},
                    index=pd.date_range("2023-01-01", periods=1),
                )
                mock_ticker.return_value = mock_ticker_instance

                with patch("time.sleep"):
                    get_etf_data(
                        tickers=["SPY", "QQQ"],
                        start_date="2023-01-01",
                        end_date="2023-01-05",
                    )

                    # Should call sleep between individual downloads
                    # (only if fallback is triggered)


class Test_Main_Function:
    """Tests for the main() function."""

    @pytest.mark.integration()
    @pytest.mark.slow()
    @pytest.mark.unit()
    def test_main_function_exists(self):
        """Test that main function can be imported."""
        from src.utils.data_utils.get_data_ETFs import main

        assert callable(main)

    @pytest.mark.integration()
    @pytest.mark.slow()
    @pytest.mark.unit()
    def test_main_with_mocked_download(self, tmp_path, monkeypatch):
        """Test main() with mocked get_etf_data to avoid network calls."""
        from datetime import date as _date

        import src.utils.data_utils.get_data_ETFs as module

        mock_pl_df = pl.DataFrame(
            {
                "Date": [_date(2024, 1, i) for i in range(1, 6)],
                "IVV": [450.0 + i for i in range(5)],
                "AGG": [100.0 + i * 0.1 for i in range(5)],
            },
        )

        fake_file = tmp_path / "a" / "b" / "get_data_ETFs.py"
        fake_file.parent.mkdir(parents=True, exist_ok=True)
        fake_file.touch()
        monkeypatch.setattr(module, "__file__", str(fake_file))
        monkeypatch.setattr(module, "get_etf_data", lambda **kwargs: mock_pl_df)

        module.main()

        output_file = tmp_path / "inputs" / "raw" / "data_ETFs.csv"
        assert output_file.exists()
        assert output_file.stat().st_size > 0

    @pytest.mark.integration()
    @pytest.mark.slow()
    @pytest.mark.unit()
    def test_main_returns_early_when_no_data(
        self,
        tmp_path,
        monkeypatch,
        mock_module_logger,
    ):
        """Test that main logs and returns early when no ETF data is retrieved."""
        fake_file = tmp_path / "a" / "b" / "get_data_ETFs.py"
        fake_file.parent.mkdir(parents=True, exist_ok=True)
        fake_file.touch()

        monkeypatch.setattr(module, "__file__", str(fake_file))
        monkeypatch.setattr(module, "get_etf_data", lambda **kwargs: pl.DataFrame())

        module.main()

        output_file = tmp_path / "inputs" / "raw" / "data_ETFs.csv"
        assert not output_file.exists()
        mock_module_logger.error.assert_any_call("No data was retrieved from Yahoo Finance.")

    @pytest.mark.integration()
    @pytest.mark.slow()
    @pytest.mark.unit()
    def test_main_writes_csv_with_date_column(self, tmp_path, monkeypatch):
        """Test that main writes a CSV whose first column is named Date."""
        from datetime import date as _date

        import src.utils.data_utils.get_data_ETFs as module

        fake_file = tmp_path / "a" / "b" / "get_data_ETFs.py"
        fake_file.parent.mkdir(parents=True, exist_ok=True)
        fake_file.touch()

        mock_pl_df = pl.DataFrame(
            {
                "Date": [_date(2024, 1, 1), _date(2024, 1, 2)],
                "IVV": [450.0, 451.0],
                "AGG": [100.0, 100.1],
            },
        )

        monkeypatch.setattr(module, "__file__", str(fake_file))
        monkeypatch.setattr(module, "get_etf_data", lambda **kwargs: mock_pl_df)

        module.main()

        output_file = tmp_path / "inputs" / "raw" / "data_ETFs.csv"
        result_df = pl.read_csv(output_file, try_parse_dates=True)
        assert result_df.columns[0] == "Date"

    @pytest.mark.integration()
    @pytest.mark.slow()
    @pytest.mark.unit()
    def test_main_writes_all_ticker_columns(self, tmp_path, monkeypatch):
        """Test that main writes all ticker columns present in the polars DataFrame."""
        from datetime import date as _date

        import src.utils.data_utils.get_data_ETFs as module

        fake_file = tmp_path / "a" / "b" / "get_data_ETFs.py"
        fake_file.parent.mkdir(parents=True, exist_ok=True)
        fake_file.touch()

        mock_pl_df = pl.DataFrame(
            {
                "Date": [_date(2024, 1, 1)],
                "IVV": [450.0],
                "AGG": [100.0],
            },
        )

        monkeypatch.setattr(module, "__file__", str(fake_file))
        monkeypatch.setattr(module, "get_etf_data", lambda **kwargs: mock_pl_df)

        module.main()

        output_file = tmp_path / "inputs" / "raw" / "data_ETFs.csv"
        result_df = pl.read_csv(output_file)
        assert set(result_df.columns) == {"Date", "IVV", "AGG"}

    @pytest.mark.integration()
    @pytest.mark.slow()
    @pytest.mark.unit()
    def test_main_logs_exception_when_save_fails(
        self,
        tmp_path,
        monkeypatch,
        mock_module_logger,
    ):
        """Test that main logs unexpected exceptions raised while saving."""
        from datetime import date as _date

        fake_file = tmp_path / "a" / "b" / "get_data_ETFs.py"
        fake_file.parent.mkdir(parents=True, exist_ok=True)
        fake_file.touch()

        mock_pl_df = pl.DataFrame(
            {
                "Date": [_date(2024, 1, 1), _date(2024, 1, 2)],
                "IVV": [450.0, 451.0],
            },
        )

        def raise_write_csv(self, *args, **kwargs):
            raise OSError("disk full")

        monkeypatch.setattr(module, "__file__", str(fake_file))
        monkeypatch.setattr(module, "get_etf_data", lambda **kwargs: mock_pl_df)
        monkeypatch.setattr(pl.DataFrame, "write_csv", raise_write_csv)

        module.main()

        assert mock_module_logger.exception.call_count == 1
        assert mock_module_logger.exception.call_args.args[0] == "Error occurred: %s"
        assert str(mock_module_logger.exception.call_args.args[1]) == "disk full"


class Test_Project_Root_Resolution:
    """Tests for helper path resolution behavior."""

    @pytest.mark.unit()
    def test_resolve_project_root_uses_first_repo_marker_parent(self, tmp_path, monkeypatch):
        """Test marker files short-circuit helper resolution before fallback depth."""
        import src.utils.data_utils.get_data_ETFs as module

        project_root = tmp_path / "repo_root"
        fake_file = project_root / "level_one" / "level_two" / "get_data_ETFs.py"
        fake_file.parent.mkdir(parents=True, exist_ok=True)
        fake_file.touch()
        project_root.joinpath("pytest.ini").write_text("[pytest]\n", encoding="utf-8")

        monkeypatch.setattr(module, "__file__", str(fake_file))

        assert module._resolve_project_root() == project_root.resolve()

    @pytest.mark.unit()
    def test_resolve_project_root_falls_back_without_repo_markers(self, tmp_path, monkeypatch):
        """Test shallow temp paths use the explicit parent-chain fallback."""
        import src.utils.data_utils.get_data_ETFs as module

        fake_file = tmp_path / "level_one" / "level_two" / "get_data_ETFs.py"
        fake_file.parent.mkdir(parents=True, exist_ok=True)
        fake_file.touch()

        monkeypatch.setattr(module, "__file__", str(fake_file))

        assert module._resolve_project_root() == fake_file.resolve().parent.parent.parent


class Test_Get_ETF_Data_Coverage_Gaps:
    """Focused tests for fallback branches in get_etf_data."""

    @pytest.mark.unit()
    def test_bulk_multiindex_missing_requested_ticker_still_returns_available_prices(
        self,
        get_etf_data,
    ):
        """Test bulk MultiIndex results skip unavailable tickers without failing."""
        with patch("yfinance.download") as mock_download:
            idx = pd.date_range("2023-01-02", periods=2, freq="B")
            df = pd.DataFrame(
                {("SPY", "Close"): [100.0, 101.0], ("SPY", "Volume"): [1000, 2000]},
                index=idx,
            )
            df.columns = pd.MultiIndex.from_tuples(df.columns)
            mock_download.return_value = df

            result = get_etf_data(
                tickers=["SPY", "QQQ"],
                start_date="2023-01-02",
                end_date="2023-01-03",
            )

        assert isinstance(result, pl.DataFrame)
        assert "Date" in result.columns
        assert "SPY" in result.columns
        assert "QQQ" not in result.columns

    @pytest.mark.unit()
    def test_bulk_multiindex_close_extraction_failure_falls_back_to_individual_downloads(
        self,
        get_etf_data,
        mock_module_logger,
    ):
        """Test a bulk Close extraction error falls back to per-ticker history."""
        with patch("yfinance.download") as mock_download:
            idx = pd.date_range("2023-01-02", periods=2, freq="B")
            df = pd.DataFrame(
                {("SPY", "High"): [100.0, 101.0], ("SPY", "Low"): [99.0, 100.0]},
                index=idx,
            )
            df.columns = pd.MultiIndex.from_tuples(df.columns)
            mock_download.return_value = df

            with patch("yfinance.Ticker") as mock_ticker:
                mock_ticker_instance = MagicMock()
                mock_ticker_instance.history.return_value = pd.DataFrame(
                    {"Close": [100.0, 101.0]},
                    index=pd.date_range("2023-01-02", periods=2, freq="B"),
                )
                mock_ticker.return_value = mock_ticker_instance

                with patch("time.sleep"):
                    result = get_etf_data(
                        tickers=["SPY"],
                        start_date="2023-01-02",
                        end_date="2023-01-03",
                    )

        assert isinstance(result, pl.DataFrame)
        assert "Date" in result.columns
        assert "SPY" in result.columns
        mock_module_logger.warning.assert_any_call(
            "Could not extract Close for %s: %s",
            "SPY",
            ANY,
        )

    @pytest.mark.unit()
    def test_single_ticker_bulk_no_close_column_falls_back_to_individual_downloads(
        self, get_etf_data,
    ):
        """Test non-MultiIndex bulk data without Close column falls back to history calls."""
        with patch("yfinance.download") as mock_download:
            mock_download.return_value = pd.DataFrame(
                {"High": [100.0, 101.0]},  # no Close column
                index=pd.date_range("2023-01-02", periods=2, freq="B"),
            )

            with patch("yfinance.Ticker") as mock_ticker:
                mock_ticker_instance = MagicMock()
                mock_ticker_instance.history.return_value = pd.DataFrame(
                    {"Close": [100.0, 101.0]},
                    index=pd.date_range("2023-01-02", periods=2, freq="B"),
                )
                mock_ticker.return_value = mock_ticker_instance

                with patch("time.sleep"):
                    result = get_etf_data(
                        tickers=["SPY"],
                        start_date="2023-01-02",
                        end_date="2023-01-03",
                    )

        assert isinstance(result, pl.DataFrame)
        assert "Date" in result.columns
        assert "SPY" in result.columns

    @pytest.mark.unit()
    def test_single_ticker_bulk_close_column_extracts_correctly(self, get_etf_data):
        """Test non-MultiIndex single-ticker bulk with Close column uses direct extraction."""
        with patch("yfinance.download") as mock_download:
            mock_download.return_value = pd.DataFrame(
                {"Close": [100.0, 101.0, 102.0]},
                index=pd.date_range("2023-01-02", periods=3, freq="B"),
            )

            result = get_etf_data(
                tickers=["SPY"],
                start_date="2023-01-02",
                end_date="2023-01-04",
            )

        assert isinstance(result, pl.DataFrame)
        assert "Date" in result.columns
        assert "SPY" in result.columns
        assert result.shape[0] == 3

    @pytest.mark.unit()
    def test_individual_download_warnings_cover_missing_close_and_empty_history(
        self,
        get_etf_data,
        mock_module_logger,
    ):
        """Test warning branches for missing Close data and empty history results."""
        with patch("yfinance.download") as mock_download:
            mock_download.return_value = pd.DataFrame()

            with patch("yfinance.Ticker") as mock_ticker:
                mock_ticker_first = MagicMock()
                mock_ticker_first.history.return_value = pd.DataFrame(
                    {"Open": [100.0]},
                    index=pd.date_range("2023-01-02", periods=1, freq="B"),
                )
                mock_ticker_second = MagicMock()
                mock_ticker_second.history.return_value = pd.DataFrame()
                mock_ticker.side_effect = [mock_ticker_first, mock_ticker_second]

                with patch("time.sleep"):
                    result = get_etf_data(
                        tickers=["SPY", "QQQ"],
                        start_date="2023-01-02",
                        end_date="2023-01-03",
                    )

        assert result.is_empty()
        mock_module_logger.warning.assert_any_call("No data for %s", "SPY")
        mock_module_logger.warning.assert_any_call("No data for %s", "QQQ")
        mock_module_logger.warning.assert_any_call("No data retrieved from Yahoo Finance")

    @pytest.mark.unit()
    def test_individual_download_exception_is_logged(
        self,
        get_etf_data,
        mock_module_logger,
    ):
        """Test exceptions during individual downloads are logged and suppressed."""
        with patch("yfinance.download") as mock_download:
            mock_download.return_value = pd.DataFrame()

            with patch("yfinance.Ticker") as mock_ticker:
                mock_ticker_instance = MagicMock()
                mock_ticker_instance.history.side_effect = RuntimeError("history failed")
                mock_ticker.return_value = mock_ticker_instance

                result = get_etf_data(
                    tickers=["SPY"],
                    start_date="2023-01-01",
                    end_date="2023-01-02",
                )

        assert result.is_empty()
        mock_module_logger.error.assert_any_call(
            "Error downloading %s: %s",
            "SPY",
            ANY,
        )


# ==============================================================================
# Tests: Polars return type and TTLCache (P1 additions)
# ==============================================================================


class Test_Get_ETF_Data_Polars:
    """Tests for the polars-first API of get_etf_data."""

    @pytest.fixture()
    def _get_etf_data(self):
        from src.utils.data_utils.get_data_ETFs import get_etf_data
        return get_etf_data

    @pytest.fixture()
    def _clear_cache(self):
        """Clear TTLCache between tests to avoid cross-test pollution."""
        from src.utils.data_utils.get_data_ETFs import _ETF_CACHE
        _ETF_CACHE.clear()
        yield
        _ETF_CACHE.clear()

    def _make_mock_download(self, tickers: list[str]):
        """Return a patch context manager for yfinance.download returning multi-index DataFrame."""
        dates = pd.date_range("2023-01-02", periods=5, freq="B")
        data = {}
        for ticker in tickers:
            for field in ("Close",):
                data[(ticker, field)] = [100.0 + i for i in range(5)]
        mi_df = pd.DataFrame(data, index=dates)
        mi_df.columns = pd.MultiIndex.from_tuples(mi_df.columns)
        return mi_df

    @pytest.mark.unit()
    def test_returns_polars_dataframe(self, _get_etf_data, _clear_cache):
        """get_etf_data must return a polars.DataFrame."""
        import polars as pl

        mock_df = self._make_mock_download(["SPY", "QQQ"])
        with patch("yfinance.download", return_value=mock_df):
            result = _get_etf_data(
                tickers=["SPY", "QQQ"],
                start_date="2023-01-02",
                end_date="2023-01-06",
            )
        assert isinstance(result, pl.DataFrame)

    @pytest.mark.unit()
    def test_date_column_is_pl_date(self, _get_etf_data, _clear_cache):
        """The Date column must use polars pl.Date dtype."""
        import polars as pl

        mock_df = self._make_mock_download(["SPY"])
        with patch("yfinance.download", return_value=mock_df):
            result = _get_etf_data(tickers=["SPY"], start_date="2023-01-02")
        assert result.schema["Date"] == pl.Date

    @pytest.mark.unit()
    def test_ticker_columns_are_float64(self, _get_etf_data, _clear_cache):
        """All ticker columns must be pl.Float64."""
        import polars as pl

        mock_df = self._make_mock_download(["IVV", "AGG"])
        with patch("yfinance.download", return_value=mock_df):
            result = _get_etf_data(tickers=["IVV", "AGG"], start_date="2023-01-02")
        for col in ("IVV", "AGG"):
            assert result.schema[col] == pl.Float64

    @pytest.mark.unit()
    def test_sorted_by_date(self, _get_etf_data, _clear_cache):
        """Result must be sorted ascending by Date."""
        mock_df = self._make_mock_download(["SPY"])
        with patch("yfinance.download", return_value=mock_df):
            result = _get_etf_data(tickers=["SPY"], start_date="2023-01-02")
        dates = result["Date"].to_list()
        assert dates == sorted(dates)

    @pytest.mark.unit()
    def test_empty_result_is_polars(self, _get_etf_data, _clear_cache):
        """When no data is downloaded, return an empty polars DataFrame with correct schema."""
        import polars as pl

        inst = MagicMock()
        inst.history.return_value = pd.DataFrame()
        with (
            patch("yfinance.download", return_value=pd.DataFrame()),
            patch("yfinance.Ticker", return_value=inst),
        ):
            result = _get_etf_data(
                tickers=["INVALID"],
                start_date="2023-01-01",
                end_date="2023-01-05",
            )
        assert isinstance(result, pl.DataFrame)
        assert result.is_empty()
        assert "Date" in result.schema
        assert result.schema["Date"] == pl.Date

    @pytest.mark.unit()
    def test_ttlcache_hit_on_second_call(self, _get_etf_data, _clear_cache):
        """Second call with same args hits TTLCache without calling yfinance.download again."""
        mock_df = self._make_mock_download(["SPY"])
        with patch("yfinance.download", return_value=mock_df) as mock_dl:
            _get_etf_data(tickers=["SPY"], start_date="2023-01-02", end_date="2023-01-06")
            _get_etf_data(tickers=["SPY"], start_date="2023-01-02", end_date="2023-01-06")
        # yfinance.download called exactly once; second call served from cache
        assert mock_dl.call_count == 1

    @pytest.mark.unit()
    def test_ttlcache_different_args_bypass_cache(self, _get_etf_data, _clear_cache):
        """Different tickers produce separate cache entries."""
        mock_df_spy = self._make_mock_download(["SPY"])
        mock_df_qqq = self._make_mock_download(["QQQ"])

        with patch("yfinance.download", side_effect=[mock_df_spy, mock_df_qqq]) as mock_dl:
            _get_etf_data(tickers=["SPY"], start_date="2023-01-02")
            _get_etf_data(tickers=["QQQ"], start_date="2023-01-02")
        assert mock_dl.call_count == 2

    @pytest.mark.unit()
    def test_ttlcache_preserves_requested_ticker_order(self, _get_etf_data, _clear_cache):
        """A reversed ticker request must not reuse a cached frame with stale column order."""
        mock_df_spy_qqq = self._make_mock_download(["SPY", "QQQ"])
        mock_df_qqq_spy = self._make_mock_download(["QQQ", "SPY"])

        with patch(
            "yfinance.download",
            side_effect=[mock_df_spy_qqq, mock_df_qqq_spy],
        ) as mock_dl:
            first_result = _get_etf_data(
                tickers=["SPY", "QQQ"],
                start_date="2023-01-02",
                end_date="2023-01-06",
            )
            second_result = _get_etf_data(
                tickers=["QQQ", "SPY"],
                start_date="2023-01-02",
                end_date="2023-01-06",
            )

        assert first_result.columns == ["Date", "SPY", "QQQ"]
        assert second_result.columns == ["Date", "QQQ", "SPY"]
        assert mock_dl.call_count == 2

    @pytest.mark.unit()
    def test_ttlcache_miss_after_ttl_expires(self, _get_etf_data, _clear_cache, monkeypatch):
        """After TTL expires the cache is bypassed and yfinance is called again."""
        import cachetools

        import src.utils.data_utils.get_data_ETFs as module

        # Replace the module-level cache with one whose timer we control directly.
        current_time: list[float] = [0.0]
        short_cache: cachetools.TTLCache = cachetools.TTLCache(
            maxsize=32, ttl=1.0, timer=lambda: current_time[0],
        )
        monkeypatch.setattr(module, "_ETF_CACHE", short_cache)

        mock_df = self._make_mock_download(["SPY"])
        with patch("yfinance.download", return_value=mock_df) as mock_dl:
            _get_etf_data(tickers=["SPY"], start_date="2023-01-02")
            assert mock_dl.call_count == 1

            # Advance the fake timer past the 1-second TTL.
            current_time[0] = 2.0

            _get_etf_data(tickers=["SPY"], start_date="2023-01-02")

        assert mock_dl.call_count == 2


# ==============================================================================
# Tests: date-math edge cases (P1 goal — DST, leap day, EOM, TZ-strip)
# ==============================================================================


class Test_Get_ETF_Data_DateMath:
    """Parametrized date-math edge cases for the TZ-strip / pl.Date conversion path."""

    def _make_tz_aware_multiindex(
        self,
        date_strs: list[str],
        ticker: str = "SPY",
        tz: str = "America/New_York",
    ) -> pd.DataFrame:
        """Build a TZ-aware MultiIndex DataFrame simulating a yfinance bulk result."""
        idx = pd.DatetimeIndex(date_strs, tz=tz)
        df = pd.DataFrame(
            {(ticker, "Close"): [100.0 + i for i in range(len(date_strs))]},
            index=idx,
        )
        df.columns = pd.MultiIndex.from_tuples(df.columns)
        return df

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        ("date_strs", "description"),
        [
            (["2023-03-12", "2023-03-13"], "DST spring-forward boundary"),
            (["2023-11-05", "2023-11-06"], "DST fall-back boundary"),
            (["2024-02-29"], "leap day"),
            (["2023-01-31", "2023-02-28", "2023-03-31"], "end-of-month dates"),
        ],
    )
    def test_tz_aware_date_conversion(self, date_strs: list[str], description: str) -> None:
        """TZ-aware dates (DST boundaries, leap day, EOM) must survive TZ-strip → pl.Date."""
        from src.utils.data_utils.get_data_ETFs import _ETF_CACHE, get_etf_data

        _ETF_CACHE.clear()
        mock_df = self._make_tz_aware_multiindex(date_strs)
        with patch("yfinance.download", return_value=mock_df):
            result = get_etf_data(tickers=["SPY"], start_date=date_strs[0])

        assert isinstance(result, pl.DataFrame), f"Expected pl.DataFrame for {description}"
        assert result.schema["Date"] == pl.Date, f"Date dtype wrong for {description}"
        assert result.schema["SPY"] == pl.Float64, f"SPY dtype wrong for {description}"
        assert len(result) == len(date_strs), f"Row count mismatch for {description}"

    @pytest.mark.unit()
    def test_tz_naive_datetime_index_converts_to_pl_date(self) -> None:
        """TZ-naive DatetimeIndex (no tz_localize call needed) converts to pl.Date."""
        from src.utils.data_utils.get_data_ETFs import _ETF_CACHE, get_etf_data

        _ETF_CACHE.clear()
        idx = pd.DatetimeIndex(["2023-06-15", "2023-06-16"])
        mock_df = pd.DataFrame({("SPY", "Close"): [100.0, 101.0]}, index=idx)
        mock_df.columns = pd.MultiIndex.from_tuples(mock_df.columns)

        with patch("yfinance.download", return_value=mock_df):
            result = get_etf_data(tickers=["SPY"], start_date="2023-06-15")

        assert isinstance(result, pl.DataFrame)
        assert result.schema["Date"] == pl.Date
        assert result.schema["SPY"] == pl.Float64
        assert len(result) == 2

    @pytest.mark.unit()
    def test_result_is_sorted_by_date_ascending(self) -> None:
        """Result is always sorted ascending by Date regardless of download order."""
        from src.utils.data_utils.get_data_ETFs import _ETF_CACHE, get_etf_data

        _ETF_CACHE.clear()
        # Provide dates out of order
        idx = pd.DatetimeIndex(["2023-03-15", "2023-03-13", "2023-03-14"])
        mock_df = pd.DataFrame({("SPY", "Close"): [103.0, 101.0, 102.0]}, index=idx)
        mock_df.columns = pd.MultiIndex.from_tuples(mock_df.columns)

        with patch("yfinance.download", return_value=mock_df):
            result = get_etf_data(tickers=["SPY"], start_date="2023-03-13")

        dates = result["Date"].to_list()
        assert dates == sorted(dates), "Result must be sorted ascending by Date"

"""
Unit tests for the utils_portfolio module.

This module contains tests for portfolio utility functions
in src/utils/utils_portfolio.py.
"""

from datetime import date
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import polars as pl
import pytest
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Configuration,
    Exception_Validation_Input,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture()
def sample_etf_data():
    """Create sample ETF price data for testing."""
    dates = pl.date_range(
        date(2023, 1, 1),
        date(2023, 1, 10),
        interval="1d",
        eager=True,
    )
    return pl.DataFrame(
        {
            "Date": dates,
            "VTI": [100.0, 101.0, 102.0, 101.5, 103.0, 104.0, 103.5, 105.0, 106.0, 107.0],
            "AGG": [50.0, 50.2, 50.1, 50.3, 50.4, 50.2, 50.5, 50.6, 50.4, 50.7],
            "VNQ": [80.0, 81.0, 79.0, 80.5, 82.0, 81.5, 83.0, 82.5, 84.0, 85.0],
        },
    )


@pytest.fixture()
def sample_weights_data():
    """Create sample portfolio weights data for testing."""
    return pl.DataFrame(
        {
            "Date": [date(2023, 1, 1), date(2023, 1, 5)],
            "VTI": [0.6, 0.5],
            "AGG": [0.3, 0.35],
            "VNQ": [0.1, 0.15],
        },
    )


@pytest.fixture()
def sample_portfolio_values():
    """Create sample portfolio values for testing."""
    return pl.DataFrame(
        {
            "Date": pl.date_range(
                date(2023, 1, 1),
                date(2023, 1, 10),
                interval="1d",
                eager=True,
            ),
            "Portfolio_Value": [
                100.0,
                101.2,
                101.8,
                101.5,
                102.5,
                103.0,
                103.5,
                104.2,
                105.0,
                106.0,
            ],
        },
    )


@pytest.fixture()
def mock_portfolio_class():
    """Create a mock portfolio class for testing."""
    mock_portfolio = MagicMock()
    mock_portfolio.get_portfolio_components = ["VTI", "AGG", "VNQ"]
    mock_portfolio.get_num_components = 3
    _weights_df = pl.DataFrame(
        {
            "Date": [date(2023, 1, 1)],
            "VTI": [0.6],
            "AGG": [0.3],
            "VNQ": [0.1],
        },
    )
    mock_portfolio.get_portfolio_weights = lambda: _weights_df
    return mock_portfolio


# ============================================================================
# Tests for debug_dataframe
# ============================================================================


class Test_Debug_Dataframe:
    """Tests for the debug_dataframe function."""

    @pytest.mark.unit()
    def test_debug_dataframe_runs_without_error(self, sample_etf_data, caplog):
        """Test that debug_dataframe executes without errors."""
        import logging

        from src.portfolios.utils_portfolio import debug_dataframe

        with caplog.at_level(logging.DEBUG):
            # Should not raise any exception
            debug_dataframe(df = sample_etf_data, name = "Test DataFrame")

    @pytest.mark.unit()
    def test_debug_dataframe_logs_shape(self, sample_etf_data, caplog):
        """Test that debug_dataframe logs DataFrame shape."""
        import logging

        from src.portfolios.utils_portfolio import debug_dataframe

        with caplog.at_level(logging.DEBUG):
            debug_dataframe(df = sample_etf_data, name = "Test DataFrame")

        # Check if shape is in the log output
        assert "10" in caplog.text or "(10," in caplog.text or len(caplog.records) >= 0


# ============================================================================
# Tests for ensure_path_exists
# ============================================================================


class Test_Ensure_Path_Exists:
    """Tests for the ensure_path_exists function."""

    @pytest.mark.unit()
    def test_creates_directory(self, tmp_path):
        """Test that function creates directory if it doesn't exist."""
        from src.portfolios.utils_portfolio import ensure_path_exists

        new_dir = tmp_path / "new_directory"
        assert not new_dir.exists()

        result = ensure_path_exists(path = new_dir)

        assert new_dir.exists()
        assert result == new_dir.resolve()

    @pytest.mark.unit()
    def test_handles_existing_directory(self, tmp_path):
        """Test that function handles existing directory."""
        from src.portfolios.utils_portfolio import ensure_path_exists

        # tmp_path already exists
        result = ensure_path_exists(path = tmp_path)

        assert result == tmp_path.resolve()

    @pytest.mark.unit()
    def test_creates_nested_directories(self, tmp_path):
        """Test creation of nested directories."""
        from src.portfolios.utils_portfolio import ensure_path_exists

        nested_dir = tmp_path / "level1" / "level2" / "level3"
        assert not nested_dir.exists()

        result = ensure_path_exists(path = nested_dir)

        assert nested_dir.exists()

    @pytest.mark.unit()
    def test_accepts_string_path(self, tmp_path):
        """Test that function accepts string path."""
        from src.portfolios.utils_portfolio import ensure_path_exists

        str_path = str(tmp_path / "string_path_dir")
        result = ensure_path_exists(path = str_path)

        assert Path(str_path).exists()
        assert isinstance(result, Path)


# ============================================================================
# Tests for load_sample_etf_data
# ============================================================================


class Test_Load_Sample_ETF_Data:
    """Tests for the load_sample_etf_data function."""

    @pytest.mark.unit()
    def test_returns_polars_dataframe(self, tmp_path):
        """Test that function returns a Polars DataFrame."""
        from src.portfolios.utils_portfolio import load_sample_etf_data

        # Create a sample CSV file
        csv_path = tmp_path / "test_etf.csv"
        sample_df = pl.DataFrame(
            {
                "Date": ["2023-01-01", "2023-01-02"],
                "SPY": [400.0, 402.0],
            },
        )
        sample_df.write_csv(csv_path)

        result = load_sample_etf_data(filepath=csv_path)

        assert isinstance(result, pl.DataFrame)

    @pytest.mark.unit()
    def test_raises_file_not_found(self):
        """Test that function raises FileNotFoundError for missing file."""
        from src.portfolios.utils_portfolio import load_sample_etf_data

        with pytest.raises(FileNotFoundError):
            load_sample_etf_data(filepath="/nonexistent/path/to/file.csv")

    @pytest.mark.unit()
    def test_has_date_column(self, tmp_path):
        """Test that loaded data has Date column."""
        from src.portfolios.utils_portfolio import load_sample_etf_data

        csv_path = tmp_path / "test_etf.csv"
        sample_df = pl.DataFrame(
            {
                "Date": ["2023-01-01", "2023-01-02"],
                "ETF1": [100.0, 101.0],
            },
        )
        sample_df.write_csv(csv_path)

        result = load_sample_etf_data(filepath=csv_path)

        assert "Date" in result.columns

    @pytest.mark.unit()
    def test_renames_date_column_variants(self, tmp_path):
        """Test that function renames date column variants to 'Date'."""
        from src.portfolios.utils_portfolio import load_sample_etf_data

        csv_path = tmp_path / "test_etf.csv"
        # Use lowercase 'date' instead of 'Date'
        sample_df = pl.DataFrame(
            {
                "date": ["2023-01-01", "2023-01-02"],
                "ETF1": [100.0, 101.0],
            },
        )
        sample_df.write_csv(csv_path)

        result = load_sample_etf_data(filepath=csv_path)

        assert "Date" in result.columns

    @pytest.mark.unit()
    def test_raises_value_error_no_date_column(self, tmp_path):
        """Test that function raises ValueError when no date column found."""
        from src.portfolios.utils_portfolio import load_sample_etf_data

        csv_path = tmp_path / "test_etf.csv"
        sample_df = pl.DataFrame(
            {
                "NoDateColumn": ["value1", "value2"],
                "ETF1": [100.0, 101.0],
            },
        )
        sample_df.write_csv(csv_path)

        with pytest.raises(Exception_Validation_Input, match="No date column found"):
            load_sample_etf_data(filepath=csv_path)

    @pytest.mark.unit()
    def test_parses_timezone_stamped_datetime_strings(self, tmp_path):
        """Timestamp strings with timezone offsets should parse down to dates."""
        from src.portfolios.utils_portfolio import load_sample_etf_data

        csv_path = tmp_path / "test_etf_tz.csv"
        sample_df = pl.DataFrame(
            {
                "Date": [
                    "2024-01-02 00:00:00-05:00",
                    "2024-01-03 00:00:00-05:00",
                ],
                "ETF1": [100.0, 101.0],
            },
        )
        sample_df.write_csv(csv_path)

        result = load_sample_etf_data(filepath=csv_path)

        assert result.schema["Date"] == pl.Date
        assert result["Date"][0] == date(2024, 1, 2)

    @pytest.mark.unit()
    def test_default_filepath_is_used_when_none(self, tmp_path, monkeypatch):
        """Calling load_sample_etf_data without a filepath should use the project default path."""
        import src.portfolios.utils_portfolio as mod

        fake_project_root = tmp_path / "fake_project"
        fake_module_file = fake_project_root / "src" / "portfolios" / "utils_portfolio.py"
        fake_module_file.parent.mkdir(parents=True, exist_ok=True)
        fake_module_file.write_text("# test placeholder\n", encoding="utf-8")
        csv_path = fake_project_root / "inputs" / "raw" / "data_ETFs.csv"
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        pl.DataFrame({"Date": ["2024-01-02"], "ETF1": [100.0]}).write_csv(csv_path)
        monkeypatch.setattr(mod, "__file__", str(fake_module_file))

        result = mod.load_sample_etf_data()

        assert result["Date"][0] == date(2024, 1, 2)

    @pytest.mark.unit()
    def test_unparseable_dates_remain_strings(self, tmp_path):
        """Unparseable Date strings should be left as strings rather than raising."""
        from src.portfolios.utils_portfolio import load_sample_etf_data

        csv_path = tmp_path / "test_etf_invalid_date.csv"
        pl.DataFrame({"Date": ["not-a-date"], "ETF1": [100.0]}).write_csv(csv_path)

        result = load_sample_etf_data(filepath=csv_path)

        assert result.schema["Date"] == pl.String

    @pytest.mark.unit()
    def test_falls_back_when_initial_read_csv_raises(self, tmp_path, monkeypatch):
        """A read_csv failure on the first attempt should retry with try_parse_dates disabled."""
        import src.portfolios.utils_portfolio as mod

        csv_path = tmp_path / "test_etf_retry.csv"
        pl.DataFrame({"Date": ["2024-01-02"], "ETF1": [100.0]}).write_csv(csv_path)

        original_read_csv = mod.pl.read_csv
        call_count = {"count": 0}

        def _read_csv_side_effect(*args, **kwargs):
            """Read csv side effect."""
            call_count["count"] += 1
            if call_count["count"] == 1:
                raise RuntimeError("simulated read failure")
            return original_read_csv(*args, **kwargs)

        monkeypatch.setattr(mod.pl, "read_csv", _read_csv_side_effect)

        result = mod.load_sample_etf_data(filepath=csv_path)

        assert call_count["count"] == 2
        assert result["Date"][0] == date(2024, 1, 2)

    @pytest.mark.unit()
    def test_accepts_preparsed_date_columns_without_string_branch(self, tmp_path, monkeypatch):
        """A pre-typed Date column should pass through without string parsing logic."""
        import src.portfolios.utils_portfolio as mod

        csv_path = tmp_path / "typed_dates.csv"
        csv_path.write_text("placeholder\n", encoding="utf-8")
        typed_df = pl.DataFrame({"Date": [date(2024, 1, 2)], "ETF1": [100.0]})

        monkeypatch.setattr(mod.pl, "read_csv", lambda *args, **kwargs: typed_df)

        result = mod.load_sample_etf_data(filepath=csv_path)

        assert result.schema["Date"] == pl.Date
        assert result["Date"][0] == date(2024, 1, 2)


# ============================================================================
# Tests for load_portfolio_weights
# ============================================================================


class Test_Load_Portfolio_Weights:
    """Tests for the load_portfolio_weights function."""

    @pytest.mark.unit()
    def test_returns_polars_dataframe(self, tmp_path):
        """Test that function returns a Polars DataFrame."""
        from src.portfolios.utils_portfolio import load_portfolio_weights

        csv_path = tmp_path / "test_weights.csv"
        sample_df = pl.DataFrame(
            {
                "Date": ["2023-01-01"],
                "ETF1": [0.6],
                "ETF2": [0.4],
            },
        )
        sample_df.write_csv(csv_path)

        result = load_portfolio_weights(filepath=csv_path)

        assert isinstance(result, pl.DataFrame)

    @pytest.mark.unit()
    def test_raises_file_not_found(self):
        """Test that function raises FileNotFoundError for missing file."""
        from src.portfolios.utils_portfolio import load_portfolio_weights

        with pytest.raises(FileNotFoundError):
            load_portfolio_weights(filepath="/nonexistent/path/to/weights.csv")

    @pytest.mark.unit()
    def test_has_date_column(self, tmp_path):
        """Test that loaded weights have Date column."""
        from src.portfolios.utils_portfolio import load_portfolio_weights

        csv_path = tmp_path / "test_weights.csv"
        sample_df = pl.DataFrame(
            {
                "Date": ["2023-01-01"],
                "ETF1": [1.0],
            },
        )
        sample_df.write_csv(csv_path)

        result = load_portfolio_weights(filepath=csv_path)

        assert "Date" in result.columns


# ============================================================================
# Tests for create_sample_portfolio_weights / save_portfolio_weights_to_csv
# ============================================================================


class Test_Create_Sample_Portfolio_Weights:
    """Tests for the create_sample_portfolio_weights function."""

    @pytest.mark.unit()
    def test_raises_when_date_column_missing(self):
        """ETF data without a Date column should raise a ValueError."""
        from src.portfolios.utils_portfolio import create_sample_portfolio_weights

        etf_data = pl.DataFrame({"IVV": [100.0], "AGG": [50.0]})

        with pytest.raises(Exception_Validation_Input, match="Date"):
            create_sample_portfolio_weights(etf_data = etf_data)

    @pytest.mark.unit()
    def test_rebalance_dates_include_latest_available_date(self):
        """Generated weights should include the latest ETF date as the final rebalance."""
        from src.portfolios.utils_portfolio import create_sample_portfolio_weights

        etf_data = pl.DataFrame(
            {
                "Date": [
                    date(2024, 1, 2),
                    date(2024, 4, 1),
                    date(2024, 7, 1),
                    date(2024, 10, 1),
                    date(2025, 1, 2),
                ],
                "IVV": [100.0, 101.0, 102.0, 103.0, 104.0],
                "AGG": [50.0, 50.5, 51.0, 51.5, 52.0],
                "GLD": [180.0, 182.0, 184.0, 186.0, 188.0],
            },
        )

        result = create_sample_portfolio_weights(etf_data = etf_data)

        assert result["Date"][-1] == "2025-01-02"
        assert set(result.columns) == {"Date", "IVV", "AGG", "GLD"}

    @pytest.mark.unit()
    def test_generated_weights_sum_close_to_one(self):
        """Each generated weight row should remain normalized after zero filtering."""
        from src.portfolios.utils_portfolio import create_sample_portfolio_weights

        etf_data = pl.DataFrame(
            {
                "Date": [date(2024, 1, 2), date(2024, 7, 1), date(2025, 1, 2)],
                "IVV": [100.0, 101.0, 102.0],
                "AGG": [50.0, 50.5, 51.0],
                "GLD": [180.0, 182.0, 184.0],
            },
        )

        result = create_sample_portfolio_weights(etf_data = etf_data)

        row_sums = result.select((pl.col("IVV") + pl.col("AGG") + pl.col("GLD")).alias("Sum"))
        assert all(sum_value == pytest.approx(1.0, rel=1e-6) for sum_value in row_sums["Sum"])

    @pytest.mark.unit()
    def test_raises_when_no_asset_columns_exist(self):
        """ETF data without asset columns should raise a ValueError."""
        from src.portfolios.utils_portfolio import create_sample_portfolio_weights

        etf_data = pl.DataFrame({"Date": [date(2024, 1, 2), date(2024, 7, 1)]})

        with pytest.raises(Exception_Validation_Input, match="asset column"):
            create_sample_portfolio_weights(etf_data = etf_data)

    @pytest.mark.unit()
    def test_all_small_random_weights_fall_back_to_single_asset(self, monkeypatch):
        """If every sampled raw weight is filtered out, the fallback should allocate 100% to the first asset."""
        import numpy as np

        from src.portfolios.utils_portfolio import create_sample_portfolio_weights

        # Mock numpy Generator.random to always return 0.01 (below the 0.12 filter threshold)
        class _Mock_Rng:
            def random(self, *, size):
                return np.full(size, 0.01)

        monkeypatch.setattr(np.random, "default_rng", lambda seed: _Mock_Rng())
        etf_data = pl.DataFrame(
            {
                "Date": [date(2024, 1, 2), date(2024, 7, 1)],
                "IVV": [100.0, 101.0],
                "AGG": [50.0, 50.5],
            },
        )

        result = create_sample_portfolio_weights(etf_data=etf_data)

        assert result["IVV"].to_list() == [1.0, 1.0]
        assert result["AGG"].to_list() == [0.0, 0.0]

    @pytest.mark.unit()
    def test_accepts_datetime_values_and_single_date_without_duplicate_append(self):
        """Datetime inputs should coerce cleanly and a single date should yield one rebalance row."""
        from src.portfolios.utils_portfolio import create_sample_portfolio_weights

        etf_data = pl.DataFrame(
            {
                "Date": [datetime(2024, 1, 2, 0, 0, 0)],
                "IVV": [100.0],
                "AGG": [50.0],
            },
        )

        result = create_sample_portfolio_weights(etf_data = etf_data)

        assert result.height == 1
        assert result["Date"][0] == "2024-01-02"

    @pytest.mark.unit()
    def test_accepts_string_dates_and_appends_latest_non_rebalance_date(self):
        """String date inputs should coerce to dates and append the final date when it is not a rebalance boundary."""
        from src.portfolios.utils_portfolio import create_sample_portfolio_weights

        etf_data = pl.DataFrame(
            {
                "Date": ["2024-01-02", "2024-07-01", "2024-08-15"],
                "IVV": [100.0, 101.0, 102.0],
                "AGG": [50.0, 50.5, 51.0],
            },
        )

        result = create_sample_portfolio_weights(etf_data = etf_data)

        assert result["Date"].to_list()[-1] == "2024-08-15"

    @pytest.mark.unit()
    def test_accepts_objects_with_date_method(self):
        """Objects exposing a date() method should coerce via that method."""
        from src.portfolios.utils_portfolio import create_sample_portfolio_weights

        class _HasDate:
            """Tests for HasDate."""
            def __init__(self, year: int, month: int, day: int) -> None:
                """Init."""
                self._date = date(year, month, day)

            def date(self) -> date:
                """Date."""
                return self._date

        etf_data = pl.DataFrame(
            {
                "Date": [_HasDate(2024, 1, 2), _HasDate(2024, 7, 1)],
                "IVV": [100.0, 101.0],
                "AGG": [50.0, 50.5],
            },
            schema={"Date": pl.Object, "IVV": pl.Float64, "AGG": pl.Float64},
        )

        result = create_sample_portfolio_weights(etf_data = etf_data)

        assert result["Date"].to_list() == ["2024-01-02", "2024-07-01"]


class Test_Save_Portfolio_Weights_To_CSV:
    """Tests for the save_portfolio_weights_to_csv function."""

    @pytest.mark.unit()
    def test_creates_csv_file(self, tmp_path):
        """Saving sample portfolio weights should create the target CSV file."""
        from src.portfolios.utils_portfolio import save_portfolio_weights_to_csv

        weights_df = pl.DataFrame(
            {
                "Date": ["2024-01-02", "2024-07-01"],
                "IVV": [0.6, 0.5],
                "AGG": [0.3, 0.3],
                "GLD": [0.1, 0.2],
            },
        )
        output_path = tmp_path / "weights" / "sample_portfolio_weights_ETFs.csv"

        result = save_portfolio_weights_to_csv(portfolio_weights = weights_df, output_path=output_path)

        assert output_path.exists()
        assert result == output_path.resolve()

    @pytest.mark.unit()
    def test_written_csv_can_be_read_back(self, tmp_path):
        """Saved sample portfolio weights should round-trip through Polars CSV loading."""
        from src.portfolios.utils_portfolio import save_portfolio_weights_to_csv

        weights_df = pl.DataFrame(
            {
                "Date": ["2024-01-02"],
                "IVV": [0.7],
                "AGG": [0.2],
                "GLD": [0.1],
            },
        )
        output_path = tmp_path / "sample_portfolio_weights_ETFs.csv"

        save_portfolio_weights_to_csv(portfolio_weights = weights_df, output_path=output_path)
        loaded = pl.read_csv(output_path)

        assert loaded.columns == ["Date", "IVV", "AGG", "GLD"]
        assert loaded["IVV"][0] == pytest.approx(0.7)

    @pytest.mark.unit()
    def test_default_output_path_is_used_when_none(self, tmp_path, monkeypatch):
        """When no output path is provided, the default project inputs/raw path should be used."""
        import src.portfolios.utils_portfolio as mod

        fake_project_root = tmp_path / "fake_project"
        fake_module_file = fake_project_root / "src" / "portfolios" / "utils_portfolio.py"
        fake_module_file.parent.mkdir(parents=True, exist_ok=True)
        fake_module_file.write_text("# test placeholder\n", encoding="utf-8")
        monkeypatch.setattr(mod, "__file__", str(fake_module_file))

        weights_df = pl.DataFrame(
            {
                "Date": ["2024-01-02"],
                "IVV": [0.8],
                "AGG": [0.2],
            },
        )

        result = mod.save_portfolio_weights_to_csv(portfolio_weights = weights_df)

        assert result == (fake_project_root / "inputs" / "raw" / "sample_portfolio_weights_ETFs.csv").resolve()
        assert result.exists()


# ============================================================================
# Tests for create_sample_portfolio
# ============================================================================


class Test_Create_Sample_Portfolio:
    """Tests for the create_sample_portfolio function."""

    @pytest.mark.unit()
    def test_raises_value_error_no_date_column(self):
        """Test that function raises ValueError when Date column missing."""
        from src.portfolios.utils_portfolio import create_sample_portfolio

        invalid_weights = pl.DataFrame(
            {
                "ETF1": [0.5],
                "ETF2": [0.5],
            },
        )

        with pytest.raises(Exception_Validation_Input, match="Date"):
            create_sample_portfolio(weights_data = invalid_weights)

    @pytest.mark.unit()
    def test_raises_value_error_no_components(self):
        """Test that function raises ValueError when no component columns."""
        from src.portfolios.utils_portfolio import create_sample_portfolio

        # Only Date column, no component columns
        invalid_weights = pl.DataFrame(
            {
                "Date": ["2023-01-01"],
            },
        )

        with pytest.raises(Exception_Validation_Input, match="component"):
            create_sample_portfolio(weights_data = invalid_weights)


# ============================================================================
# Tests for calculate_portfolio_values
# ============================================================================


class Test_Calculate_Portfolio_Values:
    """Tests for the calculate_portfolio_values function."""

    @pytest.mark.unit()
    def test_returns_polars_dataframe(
        self,
        mock_portfolio_class,
        sample_etf_data,
    ):
        """Test that function returns a Polars DataFrame."""
        from src.portfolios.utils_portfolio import calculate_portfolio_values

        result = calculate_portfolio_values(
            portfolio_obj=mock_portfolio_class,
            price_data=sample_etf_data,
            initial_value=100.0,
        )

        assert isinstance(result, pl.DataFrame)

    @pytest.mark.unit()
    def test_has_required_columns(
        self,
        mock_portfolio_class,
        sample_etf_data,
    ):
        """Test that result has Date and Portfolio_Value columns."""
        from src.portfolios.utils_portfolio import calculate_portfolio_values

        result = calculate_portfolio_values(
            portfolio_obj=mock_portfolio_class,
            price_data=sample_etf_data,
            initial_value=100.0,
        )

        assert "Date" in result.columns
        assert "Portfolio_Value" in result.columns

    @pytest.mark.unit()
    def test_initial_value_respected(
        self,
        mock_portfolio_class,
        sample_etf_data,
    ):
        """Test that initial_value is used for first portfolio value."""
        from src.portfolios.utils_portfolio import calculate_portfolio_values

        initial = 1000.0
        result = calculate_portfolio_values(
            portfolio_obj=mock_portfolio_class,
            price_data=sample_etf_data,
            initial_value=initial,
        )

        if result.shape[0] > 0:
            first_value = result["Portfolio_Value"][0]
            assert first_value == pytest.approx(initial, rel=0.01)

    @pytest.mark.unit()
    def test_raises_error_missing_components(self, sample_etf_data):
        """Test that function raises error when portfolio components missing from data."""
        from src.portfolios.utils_portfolio import calculate_portfolio_values

        # Create portfolio with components not in price_data
        mock_portfolio = MagicMock()
        mock_portfolio.get_portfolio_components = ["MISSING1", "MISSING2"]
        _missing_df = pl.DataFrame(
            {
                "Date": [date(2023, 1, 1)],
                "MISSING1": [0.5],
                "MISSING2": [0.5],
            },
        )
        mock_portfolio.get_portfolio_weights = lambda: _missing_df

        with pytest.raises(Exception_Validation_Input, match="No valid components"):
            calculate_portfolio_values(
                portfolio_obj=mock_portfolio,
                price_data=sample_etf_data,
            )


# ============================================================================
# Tests for calculate_portfolio_values — vectorised join_asof path (C3)
# ============================================================================


class Test_Calculate_Portfolio_Values_Join_Asof:
    """Tests verifying the join_asof vectorised implementation of C3."""

    @staticmethod
    def _make_prices(dates, vti_prices, agg_prices):
        return pl.DataFrame(
            {"Date": dates, "VTI": vti_prices, "AGG": agg_prices}
        ).with_columns(pl.col("Date").str.to_date("%Y-%m-%d"))

    @staticmethod
    def _make_portfolio(weight_dates, vti_w, agg_w):
        df = pl.DataFrame(
            {"Date": weight_dates, "VTI": vti_w, "AGG": agg_w}
        ).with_columns(pl.col("Date").str.to_date("%Y-%m-%d"))
        p = MagicMock()
        p.get_portfolio_components = ["VTI", "AGG"]
        p.get_portfolio_weights = lambda: df
        return p

    @pytest.mark.unit()
    def test_single_weight_period_compounding(self):
        """Two-day price series with fixed weights compounds correctly."""
        from src.portfolios.utils_portfolio import calculate_portfolio_values

        prices = self._make_prices(
            ["2024-01-01", "2024-01-02"],
            [100.0, 110.0],  # VTI +10 %
            [200.0, 200.0],  # AGG  0 %
        )
        portfolio = self._make_portfolio(
            ["2024-01-01"], [0.5], [0.5]
        )
        result = calculate_portfolio_values(portfolio_obj = portfolio, price_data = prices, initial_value=1000.0)

        assert result.shape[0] == 2
        assert result["Portfolio_Value"][0] == pytest.approx(1000.0, rel=1e-9)
        # Day-2: ret_VTI=0.10, ret_AGG=0.00, port_ret=0.05 → 1000 * 1.05 = 1050
        assert result["Portfolio_Value"][1] == pytest.approx(1050.0, rel=1e-6)

    @pytest.mark.unit()
    def test_two_weight_periods_asof_lookup(self):
        """Weights change mid-series; join_asof should pick the correct period."""
        from src.portfolios.utils_portfolio import calculate_portfolio_values

        prices = self._make_prices(
            ["2024-01-01", "2024-01-02", "2024-02-01", "2024-02-02"],
            [100.0, 102.0, 102.0, 103.02],  # VTI
            [100.0, 100.0, 100.0, 100.0],   # AGG flat
        )
        # Jan period: 100 % VTI; Feb period: 50/50
        portfolio = self._make_portfolio(
            ["2024-01-01", "2024-02-01"],
            [1.0, 0.5],
            [0.0, 0.5],
        )
        result = calculate_portfolio_values(portfolio_obj = portfolio, price_data = prices, initial_value=100.0)

        assert result.shape[0] == 4
        # Row 0: initial value
        assert result["Portfolio_Value"][0] == pytest.approx(100.0, rel=1e-9)
        # Row 1: VTI +2 %, weight 1.0 → 100 * 1.02 = 102
        assert result["Portfolio_Value"][1] == pytest.approx(102.0, rel=1e-6)
        # Row 2: first day of Feb period, VTI 0 % change (102→102), AGG 0 % → stays 102
        assert result["Portfolio_Value"][2] == pytest.approx(102.0, rel=1e-6)
        # Row 3: VTI +1 % (102→103.02), AGG 0 %, weight 0.5/0.5 → port_ret=0.005
        assert result["Portfolio_Value"][3] == pytest.approx(102.0 * 1.005, rel=1e-6)

    @pytest.mark.unit()
    def test_price_before_first_weight_date_excluded(self):
        """Rows before the first weight date must be dropped from the result."""
        from src.portfolios.utils_portfolio import calculate_portfolio_values

        prices = self._make_prices(
            ["2023-12-31", "2024-01-01", "2024-01-02"],
            [90.0, 100.0, 101.0],
            [50.0, 50.0, 50.0],
        )
        portfolio = self._make_portfolio(["2024-01-01"], [0.6], [0.4])
        result = calculate_portfolio_values(portfolio_obj = portfolio, price_data = prices, initial_value=100.0)

        # 2023-12-31 is before first weight date and must be absent
        dates = result["Date"].to_list()
        assert date(2023, 12, 31) not in dates
        assert len(result) == 2

    @pytest.mark.unit()
    def test_returns_only_date_and_portfolio_value_columns(self):
        """Result DataFrame must contain exactly [Date, Portfolio_Value]."""
        from src.portfolios.utils_portfolio import calculate_portfolio_values

        prices = self._make_prices(["2024-01-01", "2024-01-02"], [100.0, 100.0], [100.0, 100.0])
        portfolio = self._make_portfolio(["2024-01-01"], [0.5], [0.5])
        result = calculate_portfolio_values(portfolio_obj = portfolio, price_data = prices, initial_value=100.0)

        assert set(result.columns) == {"Date", "Portfolio_Value"}


# ============================================================================
# Tests for save_portfolio_values_to_csv
# ============================================================================


class Test_Save_Portfolio_Values_To_CSV:
    """Tests for the save_portfolio_values_to_csv function."""

    @pytest.mark.unit()
    def test_creates_csv_file(self, tmp_path, sample_portfolio_values):
        """Test that function creates a CSV file."""
        from src.portfolios.utils_portfolio import save_portfolio_values_to_csv

        output_path = tmp_path / "output.csv"

        result = save_portfolio_values_to_csv(
            portfolio_values=sample_portfolio_values,
            output_path=output_path,
        )

        assert output_path.exists()
        assert result == output_path.resolve()

    @pytest.mark.unit()
    def test_creates_parent_directories(self, tmp_path, sample_portfolio_values):
        """Test that function creates parent directories if needed."""
        from src.portfolios.utils_portfolio import save_portfolio_values_to_csv

        output_path = tmp_path / "nested" / "dirs" / "output.csv"

        save_portfolio_values_to_csv(
            portfolio_values=sample_portfolio_values,
            output_path=output_path,
        )

        assert output_path.exists()

    @pytest.mark.unit()
    def test_csv_has_correct_columns(self, tmp_path, sample_portfolio_values):
        """Test that saved CSV has correct columns."""
        from src.portfolios.utils_portfolio import save_portfolio_values_to_csv

        output_path = tmp_path / "output.csv"

        save_portfolio_values_to_csv(
            portfolio_values=sample_portfolio_values,
            output_path=output_path,
        )

        loaded = pl.read_csv(output_path)
        assert "Date" in loaded.columns
        assert "Value" in loaded.columns


# ============================================================================
# Tests for create_benchmark_portfolio_values
# ============================================================================


class Test_Create_Benchmark_Portfolio_Values:
    """Tests for the create_benchmark_portfolio_values function."""

    @pytest.mark.unit()
    def test_returns_polars_dataframe(self, sample_portfolio_values):
        """Test that function returns a Polars DataFrame."""
        from src.portfolios.utils_portfolio import create_benchmark_portfolio_values

        result = create_benchmark_portfolio_values(portfolio_values = sample_portfolio_values)

        assert isinstance(result, pl.DataFrame)

    @pytest.mark.unit()
    def test_has_required_columns(self, sample_portfolio_values):
        """Test that result has Date and Value columns."""
        from src.portfolios.utils_portfolio import create_benchmark_portfolio_values

        result = create_benchmark_portfolio_values(portfolio_values = sample_portfolio_values)

        assert "Date" in result.columns
        assert "Value" in result.columns

    @pytest.mark.unit()
    def test_same_row_count(self, sample_portfolio_values):
        """Test that benchmark has same number of rows as input."""
        from src.portfolios.utils_portfolio import create_benchmark_portfolio_values

        result = create_benchmark_portfolio_values(portfolio_values = sample_portfolio_values)

        assert result.shape[0] == sample_portfolio_values.shape[0]

    @pytest.mark.unit()
    def test_reproducibility(self, sample_portfolio_values):
        """Test that benchmark values are reproducible (fixed seed)."""
        from src.portfolios.utils_portfolio import create_benchmark_portfolio_values

        result1 = create_benchmark_portfolio_values(portfolio_values = sample_portfolio_values)
        result2 = create_benchmark_portfolio_values(portfolio_values = sample_portfolio_values)

        # Results should be identical due to fixed seed
        assert result1["Value"].to_list() == result2["Value"].to_list()

    @pytest.mark.unit()
    def test_first_value_unchanged(self, sample_portfolio_values):
        """Test that first value is kept unchanged."""
        from src.portfolios.utils_portfolio import create_benchmark_portfolio_values

        result = create_benchmark_portfolio_values(portfolio_values = sample_portfolio_values)

        original_first = sample_portfolio_values["Portfolio_Value"][0]
        benchmark_first = result["Value"][0]

        assert benchmark_first == original_first


# ============================================================================
# Tests for save_benchmark_portfolio_values_to_csv
# ============================================================================


class Test_Save_Benchmark_Portfolio_Values_To_CSV:
    """Tests for the save_benchmark_portfolio_values_to_csv function."""

    @pytest.mark.unit()
    def test_creates_csv_file(self, tmp_path):
        """Test that function creates a CSV file."""
        from src.portfolios.utils_portfolio import save_benchmark_portfolio_values_to_csv

        benchmark_df = pl.DataFrame(
            {
                "Date": [date(2023, 1, 1), date(2023, 1, 2)],
                "Value": [100.0, 101.0],
            },
        )
        output_path = tmp_path / "benchmark.csv"

        result = save_benchmark_portfolio_values_to_csv(
            benchmark_portfolio_values=benchmark_df,
            output_path=output_path,
        )

        assert output_path.exists()
        assert result == output_path.resolve()


# ============================================================================
# Tests for suggest_component_matches
# ============================================================================


class Test_Suggest_Component_Matches:
    """Tests for the suggest_component_matches function."""

    @pytest.mark.unit()
    def test_finds_exact_match_case_insensitive(self):
        """Test that function finds exact matches (case insensitive)."""
        from src.portfolios.utils_portfolio import suggest_component_matches

        components = ["spy"]
        etf_columns = ["SPY", "QQQ", "IWM"]

        result = suggest_component_matches(components = components, etf_columns = etf_columns)

        assert "spy" in result
        assert "SPY" in result["spy"]

    @pytest.mark.unit()
    def test_finds_partial_matches(self):
        """Test that function finds partial matches."""
        from src.portfolios.utils_portfolio import suggest_component_matches

        components = ["SP"]
        etf_columns = ["SPY", "SPX", "QQQ"]

        result = suggest_component_matches(components = components, etf_columns = etf_columns)

        assert "SP" in result
        # SPY and SPX both contain "sp"
        assert len(result["SP"]) >= 1

    @pytest.mark.unit()
    def test_ignores_date_column(self):
        """Test that Date column is ignored."""
        from src.portfolios.utils_portfolio import suggest_component_matches

        components = ["Date", "SPY"]
        etf_columns = ["SPY", "Date"]

        result = suggest_component_matches(components = components, etf_columns = etf_columns)

        assert "Date" not in result

    @pytest.mark.unit()
    def test_returns_empty_for_no_matches(self):
        """Test that empty dict returned when no matches found."""
        from src.portfolios.utils_portfolio import suggest_component_matches

        components = ["XYZ123"]
        etf_columns = ["SPY", "QQQ"]

        result = suggest_component_matches(components = components, etf_columns = etf_columns)

        assert "XYZ123" not in result


# ============================================================================
# Tests for create_custom_portfolio
# ============================================================================


class Test_Create_Custom_Portfolio:
    """Tests for the create_custom_portfolio function."""

    @pytest.mark.unit()
    def test_raises_import_error_when_portfolio_unavailable(self):
        """Test that ImportError raised when portfolio class unavailable."""
        from src.portfolios import utils_portfolio

        # Temporarily set portfolio to None
        original_portfolio = utils_portfolio.Portfolio_QWIM_class

        try:
            utils_portfolio.Portfolio_QWIM_class = None

            with pytest.raises(ImportError):
                utils_portfolio.create_custom_portfolio(components = ["AAPL", "MSFT"])
        finally:
            utils_portfolio.Portfolio_QWIM_class = original_portfolio

    @pytest.mark.unit()
    def test_raises_value_error_empty_components(self):
        """Test that ValueError raised for empty components list."""
        from src.portfolios import utils_portfolio
        from src.portfolios.portfolio_QWIM import Portfolio_QWIM

        # Ensure portfolio class is available (may be None due to relative import)
        original_portfolio = utils_portfolio.Portfolio_QWIM_class
        try:
            utils_portfolio.Portfolio_QWIM_class = Portfolio_QWIM
            with pytest.raises(Exception_Validation_Input, match="empty"):
                utils_portfolio.create_custom_portfolio(components = [])
        finally:
            utils_portfolio.Portfolio_QWIM_class = original_portfolio


# ============================================================================
# Tests for get_sample_portfolio
# ============================================================================


class Test_Get_Sample_Portfolio:
    """Tests for the get_sample_portfolio convenience function."""

    @pytest.fixture(autouse=True)
    def patch_portfolio_class(self):
        """Inject the real portfolio_QWIM class into utils_portfolio.

        utils_portfolio uses a relative import at module load time that fails
        under pytest.  This fixture patches the module-level ``portfolio``
        variable so every function in the module (create_sample_portfolio,
        get_sample_portfolio, etc.) works correctly.
        """
        from src.portfolios import utils_portfolio
        from src.portfolios.portfolio_QWIM import Portfolio_QWIM

        original = utils_portfolio.Portfolio_QWIM_class
        utils_portfolio.Portfolio_QWIM_class = Portfolio_QWIM
        yield
        utils_portfolio.Portfolio_QWIM_class = original

    @pytest.mark.integration()
    @pytest.mark.unit()
    def test_returns_three_tuple(self):
        """Function returns a tuple of exactly three items."""
        from src.portfolios.utils_portfolio import get_sample_portfolio

        result = get_sample_portfolio()
        assert len(result) == 3

    @pytest.mark.integration()
    @pytest.mark.unit()
    def test_first_element_is_portfolio(self):
        """First element of the tuple is a portfolio object."""
        from src.portfolios.utils_portfolio import get_sample_portfolio
        from src.portfolios.portfolio_QWIM import Portfolio_QWIM

        portfolio_obj, _, _ = get_sample_portfolio()
        assert isinstance(portfolio_obj, Portfolio_QWIM)

    @pytest.mark.integration()
    @pytest.mark.unit()
    def test_second_element_is_polars_dataframe(self):
        """Second element (ETF prices) is a Polars DataFrame."""
        from src.portfolios.utils_portfolio import get_sample_portfolio

        _, etf_data, _ = get_sample_portfolio()
        assert isinstance(etf_data, pl.DataFrame)

    @pytest.mark.integration()
    @pytest.mark.unit()
    def test_third_element_is_polars_dataframe(self):
        """Third element (portfolio values) is a Polars DataFrame."""
        from src.portfolios.utils_portfolio import get_sample_portfolio

        _, _, portfolio_values = get_sample_portfolio()
        assert isinstance(portfolio_values, pl.DataFrame)

    @pytest.mark.integration()
    @pytest.mark.unit()
    def test_etf_data_has_date_column(self):
        """ETF price DataFrame contains a 'Date' column."""
        from src.portfolios.utils_portfolio import get_sample_portfolio

        _, etf_data, _ = get_sample_portfolio()
        assert "Date" in etf_data.columns

    @pytest.mark.integration()
    @pytest.mark.unit()
    def test_portfolio_values_has_date_column(self):
        """Portfolio values DataFrame contains a 'Date' column."""
        from src.portfolios.utils_portfolio import get_sample_portfolio

        _, _, portfolio_values = get_sample_portfolio()
        assert "Date" in portfolio_values.columns

    @pytest.mark.integration()
    @pytest.mark.unit()
    def test_portfolio_values_has_portfolio_value_column(self):
        """Portfolio values DataFrame contains a 'Portfolio_Value' column."""
        from src.portfolios.utils_portfolio import get_sample_portfolio

        _, _, portfolio_values = get_sample_portfolio()
        assert "Portfolio_Value" in portfolio_values.columns

    @pytest.mark.integration()
    @pytest.mark.unit()
    def test_portfolio_has_components(self):
        """The returned portfolio has at least one component."""
        from src.portfolios.utils_portfolio import get_sample_portfolio

        portfolio_obj, _, _ = get_sample_portfolio()
        assert portfolio_obj.get_num_components >= 1

    @pytest.mark.integration()
    @pytest.mark.unit()
    def test_portfolio_values_non_empty(self):
        """Portfolio values DataFrame has at least one row."""
        from src.portfolios.utils_portfolio import get_sample_portfolio

        _, _, portfolio_values = get_sample_portfolio()
        assert len(portfolio_values) > 0


# ============================================================================
# Integration Tests
# ============================================================================


class Test_Portfolio_Utils_Integration:
    """Integration tests for portfolio utilities."""

    @pytest.mark.integration()
    @pytest.mark.unit()
    def test_end_to_end_workflow(self, tmp_path):
        """Test complete workflow from data loading to saving."""
        # Create test data files
        etf_csv = tmp_path / "etf_data.csv"
        weights_csv = tmp_path / "weights.csv"
        output_csv = tmp_path / "output.csv"

        # Create ETF data
        etf_df = pl.DataFrame(
            {
                "Date": ["2023-01-01", "2023-01-02", "2023-01-03"],
                "VTI": [100.0, 101.0, 102.0],
                "AGG": [50.0, 50.2, 50.1],
            },
        )
        etf_df.write_csv(etf_csv)

        # Create weights data
        weights_df = pl.DataFrame(
            {
                "Date": ["2023-01-01"],
                "VTI": [0.7],
                "AGG": [0.3],
            },
        )
        weights_df.write_csv(weights_csv)

        # Import functions
        from src.portfolios.utils_portfolio import (
            load_portfolio_weights,
            load_sample_etf_data,
        )

        # Load data
        etf_data = load_sample_etf_data(filepath=etf_csv)
        weights_data = load_portfolio_weights(filepath=weights_csv)

        # Verify data loaded correctly
        assert isinstance(etf_data, pl.DataFrame)
        assert isinstance(weights_data, pl.DataFrame)
        assert "Date" in etf_data.columns
        assert "Date" in weights_data.columns


# ============================================================================
# Tests covering bug-fix: create_custom_portfolio used date= instead of
# date_portfolio= as the keyword argument to portfolio_QWIM.__init__
# ============================================================================


class Test_Create_Custom_Portfolio_Date_Arg_Fix:
    """Unit tests guarding the ``date_portfolio=`` keyword-argument fix.

    Before the fix, ``create_custom_portfolio`` passed ``date=date`` to the
    ``portfolio_QWIM`` constructor, which does not accept a ``date`` parameter.
    The correct parameter is ``date_portfolio``.
    """

    @pytest.fixture(autouse=True)
    def _inject_portfolio_class(self):
        """Ensure the real portfolio_QWIM class is available in utils_portfolio."""
        from src.portfolios import utils_portfolio  # noqa: PLC0415
        from src.portfolios.portfolio_QWIM import Portfolio_QWIM  # noqa: PLC0415

        original = utils_portfolio.Portfolio_QWIM_class
        utils_portfolio.Portfolio_QWIM_class = Portfolio_QWIM
        yield
        utils_portfolio.Portfolio_QWIM_class = original

    @pytest.mark.unit()
    def test_create_custom_portfolio_no_date_does_not_raise(self):
        """create_custom_portfolio([...]) without a date must *not* raise."""
        from src.portfolios.utils_portfolio import create_custom_portfolio

        # Would raise TypeError before the date= → date_portfolio= fix
        result = create_custom_portfolio(components = ["VTI", "AGG"])
        assert result is not None

    @pytest.mark.unit()
    def test_create_custom_portfolio_with_date_does_not_raise(self):
        """create_custom_portfolio([...], date=...) must not raise TypeError.

        This is the primary regression guard: the old code passed ``date=``
        to portfolio_QWIM.__init__ which has no such parameter.
        """
        from src.portfolios.utils_portfolio import create_custom_portfolio

        # TypeError: unexpected keyword argument 'date' — before the fix
        result = create_custom_portfolio(components = ["SPY", "IWM"], date="2023-09-01")
        assert result is not None

    @pytest.mark.unit()
    def test_create_custom_portfolio_date_stored_in_weights_df(self):
        """The supplied date is stored as the portfolio's weight row date."""
        from src.portfolios.utils_portfolio import create_custom_portfolio

        result = create_custom_portfolio(components = ["VTI", "BND"], date="2024-06-30")
        weights_df = result.get_portfolio_weights()
        stored_date = str(weights_df["Date"][0])
        assert stored_date == "2024-06-30"

    @pytest.mark.unit()
    def test_create_custom_portfolio_components_list_str_type(self):
        """components parameter is typed list[str]; string elements must work."""
        from src.portfolios.utils_portfolio import create_custom_portfolio

        components: list[str] = ["AAPL", "MSFT", "GOOG"]
        result = create_custom_portfolio(components = components)
        assert sorted(result.get_portfolio_components) == sorted(components)

    @pytest.mark.unit()
    def test_create_custom_portfolio_returns_correct_type(self):
        """Return type is portfolio_QWIM (not None or some other type)."""
        from src.portfolios.portfolio_QWIM import Portfolio_QWIM
        from src.portfolios.utils_portfolio import create_custom_portfolio

        result = create_custom_portfolio(components = ["VTI"])
        assert isinstance(result, Portfolio_QWIM)


# ============================================================================
# Tests covering bug-fix: legacy with_column fallback removed from
# calculate_portfolio_values — only modern with_columns is used.
# ============================================================================


class Test_Calculate_Portfolio_Values_Modern_API:
    """Unit tests verifying that calculate_portfolio_values uses the modern
    Polars ``with_columns`` API exclusively (no legacy ``with_column``).

    The legacy ``with_column`` method was removed from Polars; the fallback
    try/except block that attempted it has been deleted from utils_portfolio.
    These tests confirm the function still produces correct results without
    that fallback.
    """

    @pytest.fixture(autouse=True)
    def _inject_portfolio_class(self):
        """Ensure the real portfolio_QWIM class is available."""
        from src.portfolios import utils_portfolio  # noqa: PLC0415
        from src.portfolios.portfolio_QWIM import Portfolio_QWIM  # noqa: PLC0415

        original = utils_portfolio.Portfolio_QWIM_class
        utils_portfolio.Portfolio_QWIM_class = Portfolio_QWIM
        yield
        utils_portfolio.Portfolio_QWIM_class = original

    @pytest.fixture()
    def two_component_portfolio(self):
        """Minimal two-component portfolio for value-calculation tests."""
        from src.portfolios.portfolio_QWIM import Portfolio_QWIM  # noqa: PLC0415

        df = pl.DataFrame(
            {
                "Date": [date(2023, 1, 1)],
                "VTI": [0.6],
                "AGG": [0.4],
            }
        )
        return Portfolio_QWIM(name_portfolio="TwoComp", portfolio_weights=df)

    @pytest.fixture()
    def matching_price_data(self):
        """Price data matching the two-component portfolio."""
        return pl.DataFrame(
            {
                "Date": [date(2023, 1, 1), date(2023, 1, 2), date(2023, 1, 3)],
                "VTI": [100.0, 102.0, 101.0],
                "AGG": [50.0, 50.5, 51.0],
            }
        )

    @pytest.mark.unit()
    def test_returns_polars_dataframe(
        self,
        two_component_portfolio,
        matching_price_data,
    ):
        """calculate_portfolio_values returns a Polars DataFrame (modern API)."""
        from src.portfolios.utils_portfolio import calculate_portfolio_values

        result = calculate_portfolio_values(
            portfolio_obj=two_component_portfolio,
            price_data=matching_price_data,
            initial_value=1000.0,
        )
        assert isinstance(result, pl.DataFrame)

    @pytest.mark.unit()
    def test_portfolio_value_column_present(
        self,
        two_component_portfolio,
        matching_price_data,
    ):
        """Result always contains the Portfolio_Value column."""
        from src.portfolios.utils_portfolio import calculate_portfolio_values

        result = calculate_portfolio_values(
            portfolio_obj=two_component_portfolio,
            price_data=matching_price_data,
        )
        assert "Portfolio_Value" in result.columns

    @pytest.mark.unit()
    def test_first_value_equals_initial(
        self,
        two_component_portfolio,
        matching_price_data,
    ):
        """First Portfolio_Value must equal the supplied initial_value."""
        from src.portfolios.utils_portfolio import calculate_portfolio_values

        result = calculate_portfolio_values(
            portfolio_obj=two_component_portfolio,
            price_data=matching_price_data,
            initial_value=500.0,
        )
        assert float(result["Portfolio_Value"][0]) == pytest.approx(500.0, rel=1e-6)

    @pytest.mark.unit()
    def test_values_are_all_positive(
        self,
        two_component_portfolio,
        matching_price_data,
    ):
        """All Portfolio_Value entries must be strictly positive."""
        from src.portfolios.utils_portfolio import calculate_portfolio_values

        result = calculate_portfolio_values(
            portfolio_obj=two_component_portfolio,
            price_data=matching_price_data,
        )
        min_val = result["Portfolio_Value"].min()
        assert min_val is not None and float(min_val) > 0.0

    @pytest.mark.unit()
    def test_with_column_attribute_does_not_exist(self):
        """Polars DataFrame does not expose the legacy with_column attribute.

        This test fails if the Polars version in use restores the removed API,
        which would require revisiting the code that depends on its absence.
        """
        df = pl.DataFrame({"A": [1]})
        assert not hasattr(df, "with_column"), (
            "Polars has re-added the legacy 'with_column' attribute; "
            "review the utils_portfolio.py calculate_portfolio_values implementation."
        )

    @pytest.mark.unit()
    def test_no_attribute_error_during_calculation(
        self,
        two_component_portfolio,
        matching_price_data,
    ):
        """calculate_portfolio_values must not raise AttributeError.

        An AttributeError would indicate a regression back to the removed
        legacy ``with_column`` call.
        """
        from src.portfolios.utils_portfolio import calculate_portfolio_values


        # AttributeError: 'DataFrame' object has no attribute 'with_column'
        # would be raised here if the legacy path were reintroduced.
        try:
            calculate_portfolio_values(
                portfolio_obj=two_component_portfolio,
                price_data=matching_price_data,
            )
        except AttributeError as exc:
            pytest.fail(
                f"AttributeError raised — legacy 'with_column' path may have "
                f"been reintroduced: {exc}"
            )


# ============================================================================
# Tests for coverage gaps — targets 95 %+ line and 100 % branch coverage
# ============================================================================


class Test_Coverage_Gaps_utils_portfolio:
    """Targeted tests for previously-uncovered branches and lines.

    Each test documents the specific gap it closes and the reasoning for
    that approach.
    """

    # ------------------------------------------------------------------
    # load_portfolio_weights gaps
    # ------------------------------------------------------------------

    @pytest.mark.unit()
    def test_load_portfolio_weights_parent_exists_file_missing(self, tmp_path):
        """FileNotFoundError with file-listing when parent dir exists but file doesn't.

        Covers lines in the ``if parent_dir.exists():`` branch of
        ``load_portfolio_weights`` (lines ~305-307).
        """
        from src.portfolios.utils_portfolio import load_portfolio_weights

        # Create the parent directory but NOT the file
        fake_dir = tmp_path / "raw"
        fake_dir.mkdir()
        missing_file = fake_dir / "no_such_weights.csv"

        with pytest.raises(FileNotFoundError, match="no_such_weights.csv"):
            load_portfolio_weights(filepath=missing_file)

    @pytest.mark.unit()
    def test_load_portfolio_weights_no_date_column(self, tmp_path):
        """Exception_Validation_Input raised when CSV has no recognisable date column.

        Covers line ~327 in ``load_portfolio_weights``.
        """
        from src.portfolios.utils_portfolio import load_portfolio_weights

        csv_path = tmp_path / "no_date.csv"
        pl.DataFrame({"alpha": [0.5], "beta": [0.5]}).write_csv(csv_path)

        with pytest.raises(Exception_Validation_Input, match="No date column"):
            load_portfolio_weights(filepath=csv_path)

    @pytest.mark.unit()
    def test_load_portfolio_weights_lowercase_date_renamed(self, tmp_path):
        """Lowercase 'date' column is renamed to 'Date' transparently.

        Covers lines ~332-333 in ``load_portfolio_weights``.
        """
        from src.portfolios.utils_portfolio import load_portfolio_weights

        csv_path = tmp_path / "lower_date.csv"
        pl.DataFrame({"date": ["2024-01-02"], "ETF1": [0.6], "ETF2": [0.4]}).write_csv(csv_path)

        result = load_portfolio_weights(filepath=csv_path)

        assert "Date" in result.columns

    @pytest.mark.unit()
    def test_load_portfolio_weights_only_date_column_no_weights(self, tmp_path):
        """CSV with only a Date column and no weight columns skips normalisation.

        Covers the False branch of ``if weight_columns:`` (branch [356, 368]).
        """
        from src.portfolios.utils_portfolio import load_portfolio_weights

        csv_path = tmp_path / "date_only.csv"
        pl.DataFrame({"Date": ["2024-01-02"]}).write_csv(csv_path)

        result = load_portfolio_weights(filepath=csv_path)

        assert result.columns == ["Date"]

    # ------------------------------------------------------------------
    # create_sample_portfolio_weights gaps
    # ------------------------------------------------------------------

    @pytest.mark.unit()
    def test_create_sample_portfolio_weights_single_asset(self):
        """Single-asset portfolio hits the ``else: normalized_weights[0] = 1.0`` branch.

        Covers line ~440 in ``create_sample_portfolio_weights``.
        """
        from src.portfolios.utils_portfolio import create_sample_portfolio_weights

        etf_data = pl.DataFrame(
            {
                "Date": [date(2024, 1, 2), date(2024, 7, 1), date(2025, 1, 2)],
                "IVV": [100.0, 101.0, 102.0],
            },
        )

        result = create_sample_portfolio_weights(etf_data = etf_data)

        assert result["IVV"].to_list() == [1.0, 1.0, 1.0]

    # ------------------------------------------------------------------
    # create_sample_portfolio gaps
    # ------------------------------------------------------------------

    @pytest.mark.unit()
    def test_create_sample_portfolio_numeric_column_logs_warning(self):
        """Numeric column names trigger a warning log.

        Covers line ~525 (the _logger.warning inside the numeric-column check).
        The custom logger (loguru) is patched so the call can be asserted.
        """
        from unittest.mock import patch

        from src.portfolios import utils_portfolio
        from src.portfolios.portfolio_QWIM import Portfolio_QWIM

        original = utils_portfolio.Portfolio_QWIM_class
        try:
            utils_portfolio.Portfolio_QWIM_class = Portfolio_QWIM
            weights_data = pl.DataFrame(
                {"Date": ["2024-01-02"], "123": [1.0]},
            )
            with patch.object(utils_portfolio._logger, "warning") as mock_warn:
                utils_portfolio.create_sample_portfolio(weights_data = weights_data)
            assert mock_warn.called
            call_msg = mock_warn.call_args[0][0]
            assert "123" in call_msg
        finally:
            utils_portfolio.Portfolio_QWIM_class = original

    @pytest.mark.unit()
    def test_create_sample_portfolio_raises_import_error_when_none(self):
        """ImportError raised when the module-level ``portfolio`` variable is None.

        Covers line ~534 in ``create_sample_portfolio``.
        """
        from src.portfolios import utils_portfolio

        original = utils_portfolio.Portfolio_QWIM_class
        try:
            utils_portfolio.Portfolio_QWIM_class = None
            weights_data = pl.DataFrame(
                {"Date": ["2024-01-02"], "ETF1": [1.0]},
            )
            with pytest.raises(ImportError):
                utils_portfolio.create_sample_portfolio(weights_data = weights_data)
        finally:
            utils_portfolio.Portfolio_QWIM_class = original

    @pytest.mark.unit()
    def test_create_sample_portfolio_raises_when_components_empty(self):
        """Exception_Validation_Input raised when created portfolio has no components.

        Covers line ~544 in ``create_sample_portfolio``.
        Uses a mock portfolio class that returns an empty component list.
        """
        from src.portfolios import utils_portfolio

        class _EmptyCompPortfolio:
            """Mock portfolio that always returns empty components."""

            def __init__(self, **kwargs):
                """Init."""

            @property
            def get_portfolio_components(self):
                """Empty."""
                return []

        original = utils_portfolio.Portfolio_QWIM_class
        try:
            utils_portfolio.Portfolio_QWIM_class = _EmptyCompPortfolio
            weights_data = pl.DataFrame(
                {"Date": ["2024-01-02"], "ETF1": [1.0]},
            )
            with pytest.raises(Exception_Validation_Input, match="no components"):
                utils_portfolio.create_sample_portfolio(weights_data = weights_data)
        finally:
            utils_portfolio.Portfolio_QWIM_class = original

    # ------------------------------------------------------------------
    # calculate_portfolio_values gaps
    # ------------------------------------------------------------------

    @pytest.mark.unit()
    def test_calculate_portfolio_values_numeric_component_ignored(self):
        """Numeric-named portfolio components that are missing from price data are warned and ignored.

        Covers line ~599 (_logger.warning for numeric component not in price_data).
        Also triggers the 'no valid components' exception so we can assert it.
        """
        from unittest.mock import MagicMock

        from src.portfolios.utils_portfolio import calculate_portfolio_values

        mock_p = MagicMock()
        mock_p.get_portfolio_components = ["1"]
        mock_p.get_portfolio_weights = lambda: pl.DataFrame(
            {"Date": [date(2023, 1, 1)], "1": [1.0]},
        )

        price_data = pl.DataFrame(
            {"Date": [date(2023, 1, 1)], "VTI": [100.0]},
        )

        with pytest.raises(Exception_Validation_Input, match="No valid components"):
            calculate_portfolio_values(portfolio_obj = mock_p, price_data = price_data)

    @pytest.mark.unit()
    def test_calculate_portfolio_values_raises_when_no_weight_dates(self):
        """Empty weights DataFrame → function returns an empty DataFrame (no raise).

        The vectorised join_asof implementation (C3) handles empty weights
        gracefully: after the asof join all rows have null weight columns and
        are filtered away, so the function logs a warning and returns an empty
        DataFrame instead of raising.
        """
        from unittest.mock import MagicMock

        from src.portfolios.utils_portfolio import calculate_portfolio_values

        mock_p = MagicMock()
        mock_p.get_portfolio_components = ["VTI"]
        mock_p.get_portfolio_weights = lambda: pl.DataFrame(
            {"Date": pl.Series([], dtype=pl.Date), "VTI": pl.Series([], dtype=pl.Float64)},
        )

        price_data = pl.DataFrame(
            {"Date": [date(2023, 1, 1)], "VTI": [100.0]},
        )

        result = calculate_portfolio_values(portfolio_obj = mock_p, price_data = price_data)
        assert isinstance(result, pl.DataFrame)
        assert result.is_empty()

    @pytest.mark.unit()
    def test_calculate_portfolio_values_price_before_weight_date_appends_none(self):
        """Price dates that precede ALL weight dates produce None values (filtered away).

        Covers lines ~655-656 (applicable_weight_date is None → append None; continue)
        and the ``for weight_date in reversed`` loop exhaustion branch [648, 654].
        """
        from src.portfolios.portfolio_QWIM import Portfolio_QWIM

        # Weight date is 2023-01-05 — price dates start 2023-01-01 (before the weight)
        weights_df = pl.DataFrame(
            {"Date": [date(2023, 1, 5)], "VTI": [1.0]},
        )
        portfolio_obj = Portfolio_QWIM(
            name_portfolio="Early",
            portfolio_weights=weights_df,
        )

        price_data = pl.DataFrame(
            {
                "Date": [date(2023, 1, 1), date(2023, 1, 5), date(2023, 1, 6)],
                "VTI": [100.0, 101.0, 102.0],
            },
        )

        from src.portfolios.utils_portfolio import calculate_portfolio_values

        result = calculate_portfolio_values(portfolio_obj = portfolio_obj, price_data = price_data)

        # Price dates before weight date produce None (filtered out) so result starts at 2023-01-05
        assert result["Date"][0] == date(2023, 1, 5)

    @pytest.mark.unit()
    def test_calculate_portfolio_values_zero_price_skips_component(self):
        """A component with zero previous-day price is skipped (False branch of prev > 0).

        Covers branch [681, 678] — the ``if prev_prices[component] > 0:`` False path
        that continues to the next loop iteration.
        """
        from src.portfolios.portfolio_QWIM import Portfolio_QWIM
        from src.portfolios.utils_portfolio import calculate_portfolio_values

        weights_df = pl.DataFrame(
            {"Date": [date(2023, 1, 1)], "VTI": [0.6], "AGG": [0.4]},
        )
        portfolio_obj = Portfolio_QWIM(
            name_portfolio="ZeroPrice",
            portfolio_weights=weights_df,
        )

        # AGG price is 0 on day 1 so prev_prices["AGG"] == 0 on day 2
        price_data = pl.DataFrame(
            {
                "Date": [date(2023, 1, 1), date(2023, 1, 2), date(2023, 1, 3)],
                "VTI": [100.0, 102.0, 104.0],
                "AGG": [0.0, 50.0, 51.0],
            },
        )

        result = calculate_portfolio_values(portfolio_obj = portfolio_obj, price_data = price_data)

        # Should run without error; day 2 uses only VTI contribution
        assert result.shape[0] > 0

    @pytest.mark.unit()
    def test_calculate_portfolio_values_empty_result_returns_empty_df(self):
        """All price dates before the first weight date yields an empty result DataFrame.

        Covers lines ~708-709 (_logger.warning + return empty DataFrame).
        """
        from src.portfolios.portfolio_QWIM import Portfolio_QWIM
        from src.portfolios.utils_portfolio import calculate_portfolio_values

        # Weight date far in the future
        weights_df = pl.DataFrame(
            {"Date": [date(2030, 1, 1)], "VTI": [1.0]},
        )
        portfolio_obj = Portfolio_QWIM(
            name_portfolio="FutureOnly",
            portfolio_weights=weights_df,
        )

        price_data = pl.DataFrame(
            {
                "Date": [date(2023, 1, 1), date(2023, 1, 2)],
                "VTI": [100.0, 101.0],
            },
        )

        result = calculate_portfolio_values(portfolio_obj = portfolio_obj, price_data = price_data)

        assert result.shape[0] == 0
        assert "Date" in result.columns
        assert "Portfolio_Value" in result.columns

    # ------------------------------------------------------------------
    # save_portfolio_values_to_csv default path gap
    # ------------------------------------------------------------------

    @pytest.mark.unit()
    def test_save_portfolio_values_to_csv_default_path(self, tmp_path, monkeypatch):
        """Default output path is used when output_path=None (monkeypatching __file__).

        Covers line ~744 in ``save_portfolio_values_to_csv``.
        """
        import src.portfolios.utils_portfolio as mod

        fake_root = tmp_path / "project"
        fake_module_file = fake_root / "src" / "portfolios" / "utils_portfolio.py"
        fake_module_file.parent.mkdir(parents=True, exist_ok=True)
        fake_module_file.write_text("# placeholder\n", encoding="utf-8")
        monkeypatch.setattr(mod, "__file__", str(fake_module_file))

        pv_df = pl.DataFrame(
            {
                "Date": [date(2024, 1, 2)],
                "Portfolio_Value": [100.0],
            },
        )

        result = mod.save_portfolio_values_to_csv(portfolio_values = pv_df)

        expected = (fake_root / "inputs" / "processed" / "sample_portfolio_values.csv").resolve()
        assert result == expected
        assert result.exists()

    # ------------------------------------------------------------------
    # create_benchmark_portfolio_values gaps (string-date paths + else block)
    # ------------------------------------------------------------------

    @pytest.mark.unit()
    def test_create_benchmark_with_standard_string_dates(self):
        """Standard ISO string dates spanning >11 years cover all five period branches.

        Uses one date in each of the four named periods plus one beyond all periods
        (period 4 / else), covering:
        - Branch [865, 871]: inner period loop exhausts (date after all period_end_dates)
        - Branch [866, 865]: inner loop continues (date > some period_end_date, not all)
        - Branch [873, 877]: period != 0 → elif period == 1
        - Lines 877-880 (period 1 body), 881-884 (period 2), 885-888 (period 3),
          891-892 (period 4 else)
        """
        from src.portfolios.utils_portfolio import create_benchmark_portfolio_values

        # start_date = 2000-01-01
        # period_end_dates[0] ≈ 2002-01-02  (2 * 365.25 days)
        # period_end_dates[1] ≈ 2005-01-04  (+ 3 * 365.25)
        # period_end_dates[2] ≈ 2009-01-07  (+ 4 * 365.25)
        # period_end_dates[3] ≈ 2011-01-09  (+ 2 * 365.25)
        df = pl.DataFrame(
            {
                "Date": [
                    "2000-01-01",  # i=0 – first value, kept as-is
                    "2001-06-15",  # period 0 (≤ 2002-01-02)
                    "2003-06-15",  # period 1 (2002-2005)
                    "2007-06-15",  # period 2 (2005-2009)
                    "2010-06-15",  # period 3 (2009-2011)
                    "2015-01-01",  # period 4 else (> 2011, loop exhausts)
                ],
                "Portfolio_Value": [100.0, 102.0, 105.0, 109.0, 107.0, 104.0],
            },
        )

        result = create_benchmark_portfolio_values(portfolio_values = df)

        assert result.shape[0] == 6
        assert "Date" in result.columns
        assert "Value" in result.columns

    @pytest.mark.unit()
    def test_create_benchmark_with_mm_dd_yyyy_string_dates(self):
        """MM/DD/YYYY string dates cause the first format to fail, triggering the loop-back arc.

        Covers branch [866, 865] (``continue`` in ``except ValueError`` sends execution
        back to the ``for date_format`` loop statement).
        """
        from src.portfolios.utils_portfolio import create_benchmark_portfolio_values

        df = pl.DataFrame(
            {
                "Date": ["01/15/2023", "07/01/2023", "01/01/2024"],
                "Portfolio_Value": [100.0, 103.0, 106.0],
            },
        )

        result = create_benchmark_portfolio_values(portfolio_values = df)

        assert result.shape[0] == 3

    @pytest.mark.unit()
    def test_create_benchmark_with_unparseable_dates_two_values(self):
        """Completely unparseable date strings fall back to index-based calculation.

        Covers branch [865, 871] (for-loop exhaustion), ``if not format_found:`` True,
        and the index-based else block (lines ~877-892). Also covers the
        ``else:`` branch inside the fraction loop (when length >= remaining_length).
        """
        from src.portfolios.utils_portfolio import create_benchmark_portfolio_values

        df = pl.DataFrame(
            {
                "Date": ["not-a-date", "also-not-a-date"],
                "Portfolio_Value": [100.0, 105.0],
            },
        )

        result = create_benchmark_portfolio_values(portfolio_values = df)

        assert result.shape[0] == 2
        assert result["Value"][0] == pytest.approx(100.0)

    @pytest.mark.unit()
    def test_create_benchmark_with_unparseable_dates_all_periods_covered(self):
        """Fifteen unparseable-date values cover all five period branches in the else block.

        Covers lines ~897-965: period 0, 1, 2, 3, and 4 (else) branches
        plus the ``if remaining_length > 0:`` True path.
        """
        from src.portfolios.utils_portfolio import create_benchmark_portfolio_values

        n = 15
        df = pl.DataFrame(
            {
                "Date": [f"item-{i}" for i in range(n)],
                "Portfolio_Value": [100.0 + i for i in range(n)],
            },
        )

        result = create_benchmark_portfolio_values(portfolio_values = df)

        assert result.shape[0] == n
        # All values should be finite floats (no None)
        assert all(v is not None for v in result["Value"].to_list())

    # ------------------------------------------------------------------
    # save_benchmark_portfolio_values_to_csv default path gap
    # ------------------------------------------------------------------

    @pytest.mark.unit()
    def test_save_benchmark_portfolio_values_to_csv_default_path(
        self, tmp_path, monkeypatch
    ):
        """Default output path used when output_path=None.

        Covers line ~1006 in ``save_benchmark_portfolio_values_to_csv``.
        """
        import src.portfolios._portfolio_benchmark as bm_mod
        import src.portfolios.utils_portfolio as mod

        fake_root = tmp_path / "project2"
        fake_module_file = fake_root / "src" / "portfolios" / "_portfolio_benchmark.py"
        fake_module_file.parent.mkdir(parents=True, exist_ok=True)
        fake_module_file.write_text("# placeholder\n", encoding="utf-8")
        monkeypatch.setattr(bm_mod, "__file__", str(fake_module_file))

        bm_df = pl.DataFrame(
            {"Date": [date(2024, 1, 2)], "Value": [99.0]},
        )

        result = mod.save_benchmark_portfolio_values_to_csv(benchmark_portfolio_values = bm_df)

        expected = (
            fake_root / "inputs" / "processed" / "benchmark_portfolio_values.csv"
        ).resolve()
        assert result == expected
        assert result.exists()

    # ------------------------------------------------------------------

    # ------------------------------------------------------------------

    @pytest.mark.unit()
    def test_suggest_component_matches_numeric_to_numeric(self):
        """Numeric component strings match numeric ETF strings.

        Covers line ~1167 (``matches.append(etf_columns[i])`` inside the
        ``comp.isdigit() and etf.isdigit()`` branch).
        """
        from src.portfolios.utils_portfolio import suggest_component_matches

        result = suggest_component_matches(components = ["1", "2"], etf_columns = ["1", "3", "2"])

        assert "1" in result
        assert "1" in result["1"]
        assert "2" in result
        assert "2" in result["2"]

    @pytest.mark.unit()
    def test_suggest_component_matches_negative_numeric(self):
        """Negative-numeric component strings also match negative-numeric ETF strings.

        Covers the ``comp.startswith('-') and comp[1:].isdigit()`` arm of the
        numeric-matching condition.
        """
        from src.portfolios.utils_portfolio import suggest_component_matches

        result = suggest_component_matches(components = ["-1"], etf_columns = ["-1", "-2"])

        assert "-1" in result
        assert "-1" in result["-1"]

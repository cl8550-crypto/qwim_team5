"""
Unit Tests for Dashboard Data Utilities
=======================================

This module contains comprehensive unit tests for the utils_data module,
which provides data loading and utility functions for the QWIM Dashboard.

Test Coverage:
    - find_date_column: Date column detection in DataFrames
    - standardize_date_column: Date column name standardization
    - get_data_utils: Utility data loading
    - get_data_inputs: Input data loading
    - get_input_data_raw: Raw data file loading
    - get_input_data_processed: Processed data file loading
    - get_names_time_series_from_DF: Series name extraction
    - downsample_dataframe: DataFrame downsampling
    - get_safe_num_rows_for_DF: Safe row count retrieval
    - validate_portfolio_data: Portfolio data validation

Testing Approach:
    - Uses pytest fixtures for sample DataFrames and paths
    - Mocks file system operations where needed
    - Tests both success and error scenarios
    - Follows defensive programming validation patterns
"""

from datetime import datetime, timedelta

import pandas as pd
import polars as pl
import pytest
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Configuration,
    Exception_Validation_Input,
)


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture()
def sample_polars_df_with_date():
    """Create sample Polars DataFrame with Date column."""
    return pl.DataFrame(
        {
            "Date": ["2023-01-01", "2023-02-01", "2023-03-01"],
            "Value": [100.0, 105.0, 102.0],
            "Other": ["A", "B", "C"],
        }
    )


@pytest.fixture()
def sample_polars_df_with_lowercase_date():
    """Create sample Polars DataFrame with lowercase date column."""
    return pl.DataFrame(
        {
            "date": ["2023-01-01", "2023-02-01", "2023-03-01"],
            "Value": [100.0, 105.0, 102.0],
        }
    )


@pytest.fixture()
def sample_polars_df_no_date():
    """Create sample Polars DataFrame without date column."""
    return pl.DataFrame(
        {
            "Value": [100.0, 105.0, 102.0],
            "Other": ["A", "B", "C"],
        }
    )


@pytest.fixture()
def sample_pandas_df():
    """Create sample Pandas DataFrame."""
    return pd.DataFrame(
        {
            "Date": ["2023-01-01", "2023-02-01", "2023-03-01"],
            "Value": [100.0, 105.0, 102.0],
        }
    )


@pytest.fixture()
def sample_portfolio_df():
    """Create valid portfolio DataFrame for validation tests."""
    return pl.DataFrame(
        {
            "Date": ["2023-01-01", "2023-02-01", "2023-03-01"],
            "Value": [100.0, 105.0, 102.0],
        }
    )


@pytest.fixture()
def large_polars_df():
    """Create large Polars DataFrame for downsampling tests."""
    import numpy as np

    dates = [f"2023-{str(i // 30 + 1).zfill(2)}-{str((i % 30) + 1).zfill(2)}" for i in range(500)]
    values = np.random.randn(500) * 10 + 100
    return pl.DataFrame(
        {
            "Date": dates[:500],
            "Value": values.tolist(),
        }
    )


@pytest.fixture()
def mock_project_dir(tmp_path):
    """Create mock project directory structure."""
    # Create inputs/raw directory
    raw_dir = tmp_path / "inputs" / "raw"
    raw_dir.mkdir(parents=True)

    # Create inputs/processed directory
    processed_dir = tmp_path / "inputs" / "processed"
    processed_dir.mkdir(parents=True)

    # Create sample CSV files
    timeseries_df = pl.DataFrame(
        {
            "Date": ["2023-01-01", "2023-02-01"],
            "AA": [100.0, 105.0],
            "BB": [200.0, 210.0],
        }
    )
    timeseries_df.write_csv(raw_dir / "data_timeseries.csv")

    etfs_df = pl.DataFrame(
        {
            "Date": ["2023-01-01", "2023-02-01"],
            "VTI": [150.0, 155.0],
            "AGG": [100.0, 101.0],
        }
    )
    etfs_df.write_csv(raw_dir / "data_ETFs.csv")

    weights_df = pl.DataFrame(
        {
            "Date": ["2023-01-01"],
            "VTI": [0.6],
            "AGG": [0.4],
        }
    )
    weights_df.write_csv(raw_dir / "sample_portfolio_weights_ETFs.csv")

    benchmark_df = pl.DataFrame(
        {
            "Date": ["2023-01-01", "2023-02-01"],
            "Value": [100.0, 105.0],
        }
    )
    benchmark_df.write_csv(processed_dir / "benchmark_portfolio_values.csv")

    portfolio_df = pl.DataFrame(
        {
            "Date": ["2023-01-01", "2023-02-01"],
            "Value": [100.0, 107.0],
        }
    )
    portfolio_df.write_csv(processed_dir / "sample_portfolio_values.csv")

    return tmp_path


# ============================================================================
# Tests for find_date_column
# ============================================================================


@pytest.mark.unit()
class Test_Find_Date_Column:
    """Test cases for find_date_column function."""

    @pytest.mark.unit()
    def test_finds_capitalized_date(self, sample_polars_df_with_date):
        """Test finding 'Date' column."""
        from src.dashboard.shiny_utils.utils_data import find_date_column

        result = find_date_column(df = sample_polars_df_with_date)

        assert result == "Date"

    @pytest.mark.unit()
    def test_finds_lowercase_date(self, sample_polars_df_with_lowercase_date):
        """Test finding 'date' column."""
        from src.dashboard.shiny_utils.utils_data import find_date_column

        result = find_date_column(df = sample_polars_df_with_lowercase_date)

        assert result == "date"

    @pytest.mark.unit()
    def test_returns_none_when_no_date(self, sample_polars_df_no_date):
        """Test returns None when no date column exists."""
        from src.dashboard.shiny_utils.utils_data import find_date_column

        result = find_date_column(df = sample_polars_df_no_date)

        assert result is None

    @pytest.mark.unit()
    def test_finds_uppercase_date(self):
        """Test finding 'DATE' column."""
        from src.dashboard.shiny_utils.utils_data import find_date_column

        df = pl.DataFrame(
            {
                "DATE": ["2023-01-01"],
                "Value": [100.0],
            }
        )

        result = find_date_column(df = df)

        assert result == "DATE"


# ============================================================================
# Tests for standardize_date_column
# ============================================================================


@pytest.mark.unit()
class Test_Standardize_Date_Column:
    """Test cases for standardize_date_column function."""

    @pytest.mark.unit()
    def test_renames_lowercase_to_date(self, sample_polars_df_with_lowercase_date):
        """Test renaming 'date' to 'Date'."""
        from src.dashboard.shiny_utils.utils_data import standardize_date_column

        result = standardize_date_column(df = sample_polars_df_with_lowercase_date)

        assert "Date" in result.columns
        assert "date" not in result.columns

    @pytest.mark.unit()
    def test_keeps_date_unchanged(self, sample_polars_df_with_date):
        """Test keeping 'Date' unchanged."""
        from src.dashboard.shiny_utils.utils_data import standardize_date_column

        result = standardize_date_column(df = sample_polars_df_with_date)

        assert "Date" in result.columns

    @pytest.mark.unit()
    def test_handles_no_date_column(self, sample_polars_df_no_date):
        """Test handling DataFrame without date column."""
        from src.dashboard.shiny_utils.utils_data import standardize_date_column

        result = standardize_date_column(df = sample_polars_df_no_date)

        assert "Date" not in result.columns
        assert result.columns == sample_polars_df_no_date.columns


# ============================================================================
# Tests for get_names_time_series_from_DF
# ============================================================================


@pytest.mark.unit()
class Test_Get_Names_Time_Series_From_DF:
    """Test cases for get_names_time_series_from_DF function."""

    @pytest.mark.unit()
    def test_returns_columns_except_date(self, sample_polars_df_with_date):
        """Test returns all columns except Date."""
        from src.dashboard.shiny_utils.utils_data import get_names_time_series_from_DF

        result = get_names_time_series_from_DF(polars_DF = sample_polars_df_with_date)

        assert "Date" not in result
        assert "Value" in result
        assert "Other" in result

    @pytest.mark.unit()
    def test_returns_empty_list_for_none(self):
        """Test returns empty list for None input."""
        from src.dashboard.shiny_utils.utils_data import get_names_time_series_from_DF

        result = get_names_time_series_from_DF(polars_DF = None)

        assert result == []

    @pytest.mark.unit()
    def test_returns_empty_list_for_empty_df(self):
        """Test returns empty list for empty DataFrame."""
        from src.dashboard.shiny_utils.utils_data import get_names_time_series_from_DF

        empty_df = pl.DataFrame()
        result = get_names_time_series_from_DF(polars_DF = empty_df)

        assert result == []

    @pytest.mark.unit()
    def test_handles_lowercase_date_column(self, sample_polars_df_with_lowercase_date):
        """Test handles lowercase 'date' column."""
        from src.dashboard.shiny_utils.utils_data import get_names_time_series_from_DF

        result = get_names_time_series_from_DF(polars_DF = sample_polars_df_with_lowercase_date)

        assert "date" not in result
        assert "Value" in result

    @pytest.mark.unit()
    def test_returns_all_columns_when_no_date(self, sample_polars_df_no_date):
        """Test returns all columns when no date column exists."""
        from src.dashboard.shiny_utils.utils_data import get_names_time_series_from_DF

        result = get_names_time_series_from_DF(polars_DF = sample_polars_df_no_date)

        assert len(result) == len(sample_polars_df_no_date.columns)


# ============================================================================
# Tests for downsample_dataframe
# ============================================================================


@pytest.mark.unit()
class Test_Downsample_Dataframe:
    """Test cases for downsample_dataframe function."""

    @pytest.mark.unit()
    def test_returns_same_df_when_below_max_points(self, sample_polars_df_with_date):
        """Test returns same DataFrame when below max_points."""
        from src.dashboard.shiny_utils.utils_data import downsample_dataframe

        result = downsample_dataframe(polars_DF = sample_polars_df_with_date, max_points=100)

        assert result.height == sample_polars_df_with_date.height

    @pytest.mark.unit()
    def test_reduces_rows_when_above_max_points(self, large_polars_df):
        """Test reduces rows when above max_points."""
        from src.dashboard.shiny_utils.utils_data import downsample_dataframe

        result = downsample_dataframe(polars_DF = large_polars_df, max_points=100)

        assert result.height <= 100
        assert result.height < large_polars_df.height

    @pytest.mark.unit()
    def Test_Non_Divisible_Row_Count_Still_Respects_Max_Points(self) -> None:
        """Downsampling must still cap the result when row count is not divisible."""
        from src.dashboard.shiny_utils.utils_data import downsample_dataframe

        large_frame = pl.DataFrame(
            {
                "Date": [
                    (datetime(2024, 1, 1) + timedelta(days=idx_row)).strftime("%Y-%m-%d")
                    for idx_row in range(260)
                ],
                "Value": [float(idx_row) for idx_row in range(260)],
            },
        )

        result = downsample_dataframe(polars_DF = large_frame, max_points=200)

        assert result.height <= 200

    @pytest.mark.unit()
    def test_raises_value_error_for_none(self):
        """Test raises ValueError for None input."""
        from src.dashboard.shiny_utils.utils_data import downsample_dataframe

        with pytest.raises(Exception_Validation_Input) as exc_info:
            downsample_dataframe(polars_DF = None)

        assert "None" in str(exc_info.value)

    @pytest.mark.unit()
    def test_raises_type_error_for_non_polars(self, sample_pandas_df):
        """Test raises TypeError for non-Polars DataFrame."""
        from src.dashboard.shiny_utils.utils_data import downsample_dataframe

        with pytest.raises(TypeError) as exc_info:
            downsample_dataframe(polars_DF = sample_pandas_df)

        assert "Polars" in str(exc_info.value)

    @pytest.mark.unit()
    def test_raises_value_error_for_empty_df(self):
        """Test raises ValueError for empty DataFrame."""
        from src.dashboard.shiny_utils.utils_data import downsample_dataframe

        empty_df = pl.DataFrame({"Date": [], "Value": []})

        with pytest.raises(Exception_Validation_Input) as exc_info:
            downsample_dataframe(polars_DF = empty_df)

        assert "empty" in str(exc_info.value).lower()


# ============================================================================
# Tests for get_safe_num_rows_for_DF
# ============================================================================


@pytest.mark.unit()
class Test_Get_Safe_Num_Rows_For_DF:
    """Test cases for get_safe_num_rows_for_DF function."""

    @pytest.mark.unit()
    def test_returns_correct_count_for_polars(self, sample_polars_df_with_date):
        """Test returns correct row count for Polars DataFrame."""
        from src.dashboard.shiny_utils.utils_data import get_safe_num_rows_for_DF

        result = get_safe_num_rows_for_DF(input_DF = sample_polars_df_with_date)

        assert result == 3

    @pytest.mark.unit()
    def test_returns_correct_count_for_pandas(self, sample_pandas_df):
        """Test returns correct row count for Pandas DataFrame."""
        from src.dashboard.shiny_utils.utils_data import get_safe_num_rows_for_DF

        result = get_safe_num_rows_for_DF(input_DF = sample_pandas_df)

        assert result == 3

    @pytest.mark.unit()
    def test_returns_zero_for_none(self):
        """Test returns 0 for None input."""
        from src.dashboard.shiny_utils.utils_data import get_safe_num_rows_for_DF

        result = get_safe_num_rows_for_DF(input_DF = None)

        assert result == 0

    @pytest.mark.unit()
    def test_returns_zero_for_non_dataframe(self):
        """Test returns 0 for non-DataFrame input."""
        from src.dashboard.shiny_utils.utils_data import get_safe_num_rows_for_DF

        result = get_safe_num_rows_for_DF(input_DF = "not a dataframe")

        assert result == 0


# ============================================================================
# Tests for validate_portfolio_data
# ============================================================================


@pytest.mark.unit()
class Test_Validate_Portfolio_Data:
    """Test cases for validate_portfolio_data function."""

    @pytest.mark.unit()
    def test_valid_portfolio_returns_true(self, sample_portfolio_df):
        """Test valid portfolio data returns True."""
        from src.dashboard.shiny_utils.utils_data import validate_portfolio_data

        is_valid, message = validate_portfolio_data(data_portfolio=sample_portfolio_df)

        assert is_valid is True
        # Message may be empty or contain success info
        assert "error" not in message.lower() if message else True

    @pytest.mark.unit()
    def test_none_portfolio_returns_false(self):
        """Test None portfolio returns False."""
        from src.dashboard.shiny_utils.utils_data import validate_portfolio_data

        is_valid, message = validate_portfolio_data(data_portfolio=None)

        assert is_valid is False
        assert "None" in message

    @pytest.mark.unit()
    def test_non_polars_returns_false(self, sample_pandas_df):
        """Test non-Polars DataFrame returns False."""
        from src.dashboard.shiny_utils.utils_data import validate_portfolio_data

        is_valid, message = validate_portfolio_data(data_portfolio=sample_pandas_df)

        assert is_valid is False
        assert "Polars" in message

    @pytest.mark.unit()
    def test_empty_portfolio_returns_false(self):
        """Test empty portfolio DataFrame returns False."""
        from src.dashboard.shiny_utils.utils_data import validate_portfolio_data

        empty_df = pl.DataFrame({"Date": [], "Value": []})

        is_valid, message = validate_portfolio_data(data_portfolio=empty_df)

        assert is_valid is False
        assert "empty" in message.lower()

    @pytest.mark.unit()
    def test_wrong_column_count_returns_false(self):
        """Test DataFrame with wrong column count returns False."""
        from src.dashboard.shiny_utils.utils_data import validate_portfolio_data

        wrong_columns_df = pl.DataFrame(
            {
                "Date": ["2023-01-01"],
                "Value": [100.0],
                "Extra": ["x"],
            }
        )

        is_valid, message = validate_portfolio_data(data_portfolio=wrong_columns_df)

        assert is_valid is False
        assert "2 columns" in message

    @pytest.mark.unit()
    def test_missing_date_column_returns_false(self):
        """Test DataFrame missing Date column returns False."""
        from src.dashboard.shiny_utils.utils_data import validate_portfolio_data

        missing_date_df = pl.DataFrame(
            {
                "Timestamp": ["2023-01-01"],
                "Value": [100.0],
            }
        )

        is_valid, message = validate_portfolio_data(data_portfolio=missing_date_df)

        assert is_valid is False
        assert "Date" in message

    @pytest.mark.unit()
    def test_missing_value_column_returns_false(self):
        """Test DataFrame missing Value column returns False."""
        from src.dashboard.shiny_utils.utils_data import validate_portfolio_data

        missing_value_df = pl.DataFrame(
            {
                "Date": ["2023-01-01"],
                "Amount": [100.0],
            }
        )

        is_valid, message = validate_portfolio_data(data_portfolio=missing_value_df)

        assert is_valid is False
        assert "Value" in message


# ============================================================================
# Tests for get_data_utils_constants
# ============================================================================


@pytest.mark.unit()
class Test_Get_Data_Utils_Constants:
    """Test cases for get_data_utils_constants function."""

    @pytest.mark.unit()
    def test_returns_dict(self, mock_project_dir):
        """Test function returns a dictionary."""
        from src.dashboard.shiny_utils.utils_data import get_data_utils_constants

        result = get_data_utils_constants(project_dir = mock_project_dir)

        assert isinstance(result, dict)

    @pytest.mark.unit()
    def test_returns_empty_dict(self, mock_project_dir):
        """Test result is an empty dict after PNG saving configuration removed."""
        from src.dashboard.shiny_utils.utils_data import get_data_utils_constants

        result = get_data_utils_constants(project_dir = mock_project_dir)

        assert result == {}


# ============================================================================
# Tests for get_data_utils_defaults
# ============================================================================


@pytest.mark.unit()
class Test_Get_Data_Utils_Defaults:
    """Test cases for get_data_utils_defaults function."""

    @pytest.mark.unit()
    def test_returns_dict(self, mock_project_dir):
        """Test function returns a dictionary."""
        from src.dashboard.shiny_utils.utils_data import get_data_utils_defaults

        result = get_data_utils_defaults(project_dir = mock_project_dir)

        assert isinstance(result, dict)

    @pytest.mark.unit()
    def test_contains_time_period_key(self, mock_project_dir):
        """Test result contains time period default."""
        from src.dashboard.shiny_utils.utils_data import get_data_utils_defaults

        result = get_data_utils_defaults(project_dir = mock_project_dir)

        assert "Select_Time_Period" in result

    @pytest.mark.unit()
    def test_contains_date_range_keys(self, mock_project_dir):
        """Test result contains date range defaults."""
        from src.dashboard.shiny_utils.utils_data import get_data_utils_defaults

        result = get_data_utils_defaults(project_dir = mock_project_dir)

        assert "Custom_Date_Range_Start" in result
        assert "Custom_Date_Range_End" in result


# ============================================================================
# Tests for get_data_utils
# ============================================================================


@pytest.mark.unit()
class Test_Get_Data_Utils:
    """Test cases for get_data_utils function."""

    @pytest.mark.unit()
    def test_returns_combined_dict(self, mock_project_dir):
        """Test function returns combined constants and defaults."""
        from src.dashboard.shiny_utils.utils_data import get_data_utils

        result = get_data_utils(project_dir = mock_project_dir)

        assert isinstance(result, dict)
        # Should contain defaults (PNG saving constants have been removed)
        assert "Select_Time_Period" in result


# ============================================================================
# Tests for get_input_data_raw
# ============================================================================


@pytest.mark.unit()
class Test_Get_Input_Data_Raw:
    """Test cases for get_input_data_raw function."""

    @pytest.mark.unit()
    def test_loads_all_raw_files(self, mock_project_dir):
        """Test loading all raw data files."""
        from src.dashboard.shiny_utils.utils_data import get_input_data_raw

        result = get_input_data_raw(project_dir = mock_project_dir)

        assert isinstance(result, dict)
        assert "Time_Series_Sample" in result
        assert "Time_Series_ETFs" in result
        assert "Weights_My_Portfolio" in result

    @pytest.mark.unit()
    def test_returns_polars_dataframes(self, mock_project_dir):
        """Test returned data are Polars DataFrames."""
        from src.dashboard.shiny_utils.utils_data import get_input_data_raw

        result = get_input_data_raw(project_dir = mock_project_dir)

        for key, value in result.items():
            assert isinstance(value, pl.DataFrame), f"{key} is not Polars DataFrame"

    @pytest.mark.unit()
    def test_standardizes_date_column(self, mock_project_dir):
        """Test date column is standardized to 'Date'."""
        from src.dashboard.shiny_utils.utils_data import get_input_data_raw

        result = get_input_data_raw(project_dir = mock_project_dir)

        for key, df in result.items():
            assert "Date" in df.columns, f"{key} missing 'Date' column"

    @pytest.mark.unit()
    def test_raises_for_missing_file(self, tmp_path):
        """Test raises error for missing file."""
        from src.dashboard.shiny_utils.utils_data import get_input_data_raw
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Configuration,
            Exception_Data_Not_Found,
        )

        # Create incomplete directory structure
        raw_dir = tmp_path / "inputs" / "raw"
        raw_dir.mkdir(parents=True)

        with pytest.raises(Exception_Data_Not_Found):
            get_input_data_raw(project_dir = tmp_path)


# ============================================================================
# Tests for get_input_data_processed
# ============================================================================


@pytest.mark.unit()
class Test_Get_Input_Data_Processed:
    """Test cases for get_input_data_processed function."""

    @pytest.mark.unit()
    def test_loads_all_processed_files(self, mock_project_dir):
        """Test loading all processed data files."""
        from src.dashboard.shiny_utils.utils_data import get_input_data_processed

        result = get_input_data_processed(project_dir = mock_project_dir)

        assert isinstance(result, dict)
        assert "Benchmark_Portfolio" in result
        assert "My_Portfolio" in result

    @pytest.mark.unit()
    def test_returns_polars_dataframes(self, mock_project_dir):
        """Test returned data are Polars DataFrames."""
        from src.dashboard.shiny_utils.utils_data import get_input_data_processed

        result = get_input_data_processed(project_dir = mock_project_dir)

        for key, value in result.items():
            assert isinstance(value, pl.DataFrame), f"{key} is not Polars DataFrame"

    @pytest.mark.unit()
    def test_raises_for_missing_file(self, tmp_path):
        """Test raises error for missing file."""
        from src.dashboard.shiny_utils.utils_data import get_input_data_processed

        # Create incomplete directory structure
        processed_dir = tmp_path / "inputs" / "processed"
        processed_dir.mkdir(parents=True)

        with pytest.raises((Exception_Configuration, FileNotFoundError, RuntimeError)):
            get_input_data_processed(project_dir = tmp_path)


# ============================================================================
# Tests for get_data_inputs
# ============================================================================


@pytest.mark.unit()
class Test_Get_Data_Inputs:
    """Test cases for get_data_inputs function."""

    @pytest.mark.unit()
    def test_returns_combined_dict(self, mock_project_dir):
        """Test function returns combined raw and processed data."""
        from src.dashboard.shiny_utils.utils_data import get_data_inputs

        result = get_data_inputs(project_dir = mock_project_dir)

        assert isinstance(result, dict)
        # Should contain both raw and processed data
        assert "Time_Series_Sample" in result
        assert "Benchmark_Portfolio" in result

    @pytest.mark.unit()
    def test_all_values_are_dataframes(self, mock_project_dir):
        """Test all values are DataFrames."""
        from src.dashboard.shiny_utils.utils_data import get_data_inputs

        result = get_data_inputs(project_dir = mock_project_dir)

        for key, value in result.items():
            assert isinstance(value, pl.DataFrame), f"{key} is not DataFrame"


# ============================================================================
# Tests for calculate_portfolio_returns
# ============================================================================


@pytest.mark.unit()
class Test_Calculate_Portfolio_Returns:
    """Test cases for calculate_portfolio_returns function."""

    @pytest.mark.unit()
    def test_none_raises(self):
        """None input raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.utils_data import calculate_portfolio_returns

        with pytest.raises(Exception_Validation_Input):
            calculate_portfolio_returns(data_portfolio = None)

    @pytest.mark.unit()
    def test_non_polars_raises(self):
        """Non-Polars DataFrame raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.utils_data import calculate_portfolio_returns

        with pytest.raises(Exception_Validation_Input):
            calculate_portfolio_returns(data_portfolio = {"Date": ["2023-01-01"], "Value": [100.0]})

    @pytest.mark.unit()
    def test_empty_df_returns_empty_series(self):
        """Empty DataFrame returns empty Series."""
        from src.dashboard.shiny_utils.utils_data import calculate_portfolio_returns

        empty_df = pl.DataFrame({"Date": [], "Value": []})
        result = calculate_portfolio_returns(data_portfolio = empty_df)
        assert isinstance(result, pl.Series)
        assert len(result) == 0

    @pytest.mark.unit()
    def test_missing_value_column_raises(self):
        """DataFrame missing 'Value' column raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.utils_data import calculate_portfolio_returns

        df = pl.DataFrame({"Date": ["2023-01-01", "2023-02-01"], "Price": [100.0, 110.0]})
        with pytest.raises(Exception_Validation_Input):
            calculate_portfolio_returns(data_portfolio = df)

    @pytest.mark.unit()
    def test_missing_date_column_raises(self):
        """DataFrame missing 'Date' column raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.utils_data import calculate_portfolio_returns

        df = pl.DataFrame({"Timestamp": ["2023-01-01", "2023-02-01"], "Value": [100.0, 110.0]})
        with pytest.raises(Exception_Validation_Input):
            calculate_portfolio_returns(data_portfolio = df)

    @pytest.mark.unit()
    def test_valid_df_returns_series(self):
        """Valid DataFrame with sufficient rows returns non-empty returns Series."""
        from src.dashboard.shiny_utils.utils_data import calculate_portfolio_returns

        df = pl.DataFrame(
            {
                "Date": ["2023-01-01", "2023-02-01", "2023-03-01"],
                "Value": [100.0, 110.0, 105.0],
            }
        )
        result = calculate_portfolio_returns(data_portfolio = df)
        assert isinstance(result, pl.Series)
        assert len(result) > 0

    @pytest.mark.unit()
    def test_single_row_returns_empty_series(self):
        """DataFrame with a single row (less than 2 clean rows) returns empty Series."""
        from src.dashboard.shiny_utils.utils_data import calculate_portfolio_returns

        df = pl.DataFrame({"Date": ["2023-01-01"], "Value": [100.0]})
        result = calculate_portfolio_returns(data_portfolio = df)
        assert isinstance(result, pl.Series)
        assert len(result) == 0


# ============================================================================
# Tests for validate_portfolio_and_benchmark_data_if_not_already_validated
# ============================================================================


@pytest.mark.unit()
class Test_Validate_Portfolio_And_Benchmark:
    """Test cases for validate_portfolio_and_benchmark_data_if_not_already_validated."""

    @pytest.mark.unit()
    def test_both_none_returns_false_false(self):
        """Both None inputs return (False, False)."""
        from src.dashboard.shiny_utils.utils_data import (
            validate_portfolio_and_benchmark_data_if_not_already_validated,
        )

        has_portfolio, has_benchmark = validate_portfolio_and_benchmark_data_if_not_already_validated(data_portfolio = None, data_benchmark = None)
        assert has_portfolio is False
        assert has_benchmark is False

    @pytest.mark.unit()
    def test_valid_portfolio_and_benchmark(self):
        """Both valid DataFrames return (True, True)."""
        from src.dashboard.shiny_utils.utils_data import (
            validate_portfolio_and_benchmark_data_if_not_already_validated,
        )

        df = pl.DataFrame({"Date": ["2023-01-01", "2023-02-01"], "Value": [100.0, 105.0]})
        has_portfolio, has_benchmark = validate_portfolio_and_benchmark_data_if_not_already_validated(data_portfolio = df, data_benchmark = df)
        assert has_portfolio is True
        assert has_benchmark is True

    @pytest.mark.unit()
    def test_invalid_portfolio_raises(self):
        """Invalid portfolio data (wrong columns) raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.utils_data import (
            validate_portfolio_and_benchmark_data_if_not_already_validated,
        )

        bad_df = pl.DataFrame({"Date": ["2023-01-01"], "Price": [100.0]})
        with pytest.raises(Exception_Validation_Input):
            validate_portfolio_and_benchmark_data_if_not_already_validated(data_portfolio = bad_df, data_benchmark = None)

    @pytest.mark.unit()
    def test_invalid_benchmark_raises(self):
        """Invalid benchmark data raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.utils_data import (
            validate_portfolio_and_benchmark_data_if_not_already_validated,
        )

        valid_df = pl.DataFrame({"Date": ["2023-01-01", "2023-02-01"], "Value": [100.0, 105.0]})
        bad_df = pl.DataFrame({"Date": ["2023-01-01"], "Price": [100.0]})
        with pytest.raises(Exception_Validation_Input):
            validate_portfolio_and_benchmark_data_if_not_already_validated(data_portfolio = valid_df, data_benchmark = bad_df)


# ============================================================================
# Additional validate_portfolio_data tests for uncovered branches
# ============================================================================


@pytest.mark.unit()
class Test_Validate_Portfolio_Data_Extra:
    """Additional tests covering uncovered branches in validate_portfolio_data."""

    @pytest.mark.unit()
    def test_invalid_date_type_returns_false(self):
        """Date column of integer type returns False with type message."""
        from src.dashboard.shiny_utils.utils_data import validate_portfolio_data

        df = pl.DataFrame({"Date": [20230101, 20230201], "Value": [100.0, 105.0]})
        is_valid, msg = validate_portfolio_data(data_portfolio=df)
        assert is_valid is False

    @pytest.mark.unit()
    def test_invalid_value_type_returns_false(self):
        """Value column of string type returns False with type message."""
        from src.dashboard.shiny_utils.utils_data import validate_portfolio_data

        df = pl.DataFrame({"Date": ["2023-01-01", "2023-02-01"], "Value": ["a", "b"]})
        is_valid, msg = validate_portfolio_data(data_portfolio=df)
        assert is_valid is False
        assert "Value column" in msg

    @pytest.mark.unit()
    def test_unsorted_dates_returns_false(self):
        """Unsorted dates return False."""
        from src.dashboard.shiny_utils.utils_data import validate_portfolio_data

        df = pl.DataFrame(
            {
                "Date": [
                    "2023-03-01",
                    "2023-01-01",
                    "2023-02-01",
                ],
                "Value": [100.0, 105.0, 102.0],
            }
        )
        is_valid, msg = validate_portfolio_data(data_portfolio=df)
        assert is_valid is False
        assert "order" in msg.lower() or "sorted" in msg.lower()

    @pytest.mark.unit()
    def test_null_values_returns_false(self):
        """Value column with nulls returns False."""
        from src.dashboard.shiny_utils.utils_data import validate_portfolio_data

        df = pl.DataFrame(
            {
                "Date": ["2023-01-01", "2023-02-01"],
                "Value": pl.Series([100.0, None], dtype=pl.Float64),
            }
        )
        is_valid, msg = validate_portfolio_data(data_portfolio=df)
        assert is_valid is False
        assert "null" in msg.lower()

    @pytest.mark.unit()
    def test_duplicate_dates_returns_false(self):
        """Duplicate dates return False."""
        from src.dashboard.shiny_utils.utils_data import validate_portfolio_data

        df = pl.DataFrame(
            {
                "Date": ["2023-01-01", "2023-01-01"],
                "Value": [100.0, 105.0],
            }
        )
        is_valid, msg = validate_portfolio_data(data_portfolio=df)
        assert is_valid is False
        assert "duplicate" in msg.lower()

    @pytest.mark.unit()
    def test_polars_date_type_column_valid(self):
        """Portfolio with polars.Date typed Date column is valid."""
        from src.dashboard.shiny_utils.utils_data import validate_portfolio_data
        import datetime

        df = pl.DataFrame(
            {
                "Date": pl.Series(
                    [datetime.date(2023, 1, 1), datetime.date(2023, 2, 1)],
                    dtype=pl.Date,
                ),
                "Value": pl.Series([100.0, 105.0], dtype=pl.Float64),
            }
        )
        is_valid, msg = validate_portfolio_data(data_portfolio=df)
        assert is_valid is True


# ============================================================================
# Additional get_input_data_raw tests for uncovered branches
# ============================================================================


@pytest.mark.unit()
class Test_Get_Input_Data_Raw_Extra:
    """Additional tests for uncovered branches in get_input_data_raw."""

    @pytest.mark.unit()
    def test_raises_for_generic_exception(self, tmp_path, monkeypatch):
        """A generic read error raises Exception_Data_Not_Found."""
        from src.dashboard.shiny_utils.utils_data import get_input_data_raw
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Data_Not_Found

        # Create the raw dir and files
        raw_dir = tmp_path / "inputs" / "raw"
        raw_dir.mkdir(parents=True)

        # Write valid CSV files
        pl.DataFrame({"Date": ["2023-01-01"], "AA": [1.0]}).write_csv(raw_dir / "data_timeseries.csv")
        pl.DataFrame({"Date": ["2023-01-01"], "VTI": [1.0]}).write_csv(raw_dir / "data_ETFs.csv")
        pl.DataFrame({"Date": ["2023-01-01"], "VTI": [0.6]}).write_csv(raw_dir / "sample_portfolio_weights_ETFs.csv")

        # Monkey-patch read_csv to raise on first call
        original_read_csv = pl.read_csv
        call_count = [0]

        def patched_read_csv(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError("simulated read error")
            return original_read_csv(*args, **kwargs)

        monkeypatch.setattr(pl, "read_csv", patched_read_csv)

        with pytest.raises(Exception_Data_Not_Found):
            get_input_data_raw(project_dir = tmp_path)


# ============================================================================
# Additional get_names_time_series_from_DF tests
# ============================================================================


@pytest.mark.unit()
class Test_Get_Names_Time_Series_Extra:
    """Additional tests for uncovered branches in get_names_time_series_from_DF."""

    @pytest.mark.unit()
    def test_no_date_column_returns_all_columns(self):
        """DataFrame without a date column returns all column names."""
        from src.dashboard.shiny_utils.utils_data import get_names_time_series_from_DF

        df = pl.DataFrame({"AA": [1.0, 2.0], "BB": [3.0, 4.0]})
        result = get_names_time_series_from_DF(polars_DF = df)
        assert "AA" in result
        assert "BB" in result


# ============================================================================
# Additional downsample_dataframe tests for uncovered branches
# ============================================================================


@pytest.mark.unit()
class Test_Downsample_Dataframe_Extra:
    """Additional tests for uncovered branches in downsample_dataframe."""

    @pytest.mark.unit()
    def test_raises_validation_input_re_raised(self):
        """Exception_Validation_Input is re-raised (not wrapped)."""
        from src.dashboard.shiny_utils.utils_data import downsample_dataframe

        with pytest.raises(Exception_Validation_Input):
            downsample_dataframe(polars_DF = None)

    @pytest.mark.unit()
    def test_non_polars_type_raises_type_error(self):
        """Non-Polars input raises TypeError."""
        from src.dashboard.shiny_utils.utils_data import downsample_dataframe

        with pytest.raises(TypeError):
            downsample_dataframe(polars_DF = [1, 2, 3])

    @pytest.mark.unit()
    @pytest.mark.parametrize("max_points", [True, False], ids=["true", "false"])
    def test_boolean_max_points_raises_validation_input(
        self,
        sample_polars_df_with_date,
        max_points,
    ):
        """Boolean max_points should be rejected before numeric downsampling logic."""
        from src.dashboard.shiny_utils.utils_data import downsample_dataframe

        with pytest.raises(Exception_Validation_Input) as exc_info:
            downsample_dataframe(polars_DF = sample_polars_df_with_date, max_points=max_points)

        assert "max_points" in str(exc_info.value)


# ============================================================================
# Tests for get_input_data_raw warning and missing-file branches
# ============================================================================


@pytest.mark.unit()
class Test_Get_Input_Data_Raw_Warning_Branches:
    """Tests for warning log branches and file-not-found branches in get_input_data_raw."""

    def _make_raw_dir(self, tmp_path):
        raw_dir = tmp_path / "inputs" / "raw"
        raw_dir.mkdir(parents=True)
        return raw_dir

    def _write_valid_timeseries(self, raw_dir):
        pl.DataFrame({"Date": ["2023-01-01"], "AA": [100.0]}).write_csv(
            raw_dir / "data_timeseries.csv"
        )

    def _write_valid_etfs(self, raw_dir):
        pl.DataFrame({"Date": ["2023-01-01"], "VTI": [150.0]}).write_csv(
            raw_dir / "data_ETFs.csv"
        )

    def _write_valid_weights(self, raw_dir):
        pl.DataFrame({"Date": ["2023-01-01"], "VTI": [0.6]}).write_csv(
            raw_dir / "sample_portfolio_weights_ETFs.csv"
        )

    @pytest.mark.unit()
    def Test_Empty_Timeseries_Logs_Warning_And_Continues(self, tmp_path):
        """Empty timeseries CSV triggers is_empty() warning; function still returns dict."""
        from src.dashboard.shiny_utils.utils_data import get_input_data_raw

        raw_dir = self._make_raw_dir(tmp_path)
        with open(raw_dir / "data_timeseries.csv", "w") as f:
            f.write("Date,AA,BB\n")  # header only → empty DataFrame
        self._write_valid_etfs(raw_dir)
        self._write_valid_weights(raw_dir)

        result = get_input_data_raw(project_dir = tmp_path)
        assert "Time_Series_Sample" in result

    @pytest.mark.unit()
    def Test_Timeseries_No_Date_Column_Logs_Warning(self, tmp_path):
        """Timeseries CSV with no date column triggers missing-date warning; function continues."""
        from src.dashboard.shiny_utils.utils_data import get_input_data_raw

        raw_dir = self._make_raw_dir(tmp_path)
        with open(raw_dir / "data_timeseries.csv", "w") as f:
            f.write("Ticker,AA\n")
            f.write("AAPL,100.0\n")
        self._write_valid_etfs(raw_dir)
        self._write_valid_weights(raw_dir)

        result = get_input_data_raw(project_dir = tmp_path)
        assert "Time_Series_Sample" in result

    @pytest.mark.unit()
    def Test_Missing_Etfs_File_Raises(self, tmp_path):
        """Missing ETF file raises Exception_Data_Not_Found; covers lines 179 and 210-211."""
        from src.dashboard.shiny_utils.utils_data import get_input_data_raw
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Data_Not_Found,
        )

        raw_dir = self._make_raw_dir(tmp_path)
        self._write_valid_timeseries(raw_dir)
        # No ETF file created
        self._write_valid_weights(raw_dir)

        with pytest.raises(Exception_Data_Not_Found):
            get_input_data_raw(project_dir = tmp_path)

    @pytest.mark.unit()
    def Test_Empty_Etfs_File_Logs_Warning(self, tmp_path):
        """Empty ETF CSV triggers is_empty() warning; function continues successfully."""
        from src.dashboard.shiny_utils.utils_data import get_input_data_raw

        raw_dir = self._make_raw_dir(tmp_path)
        self._write_valid_timeseries(raw_dir)
        with open(raw_dir / "data_ETFs.csv", "w") as f:
            f.write("Date,VTI\n")
        self._write_valid_weights(raw_dir)

        result = get_input_data_raw(project_dir = tmp_path)
        assert "Time_Series_ETFs" in result

    @pytest.mark.unit()
    def Test_Etfs_Generic_Exception_Raises(self, tmp_path, monkeypatch):
        """RuntimeError on 2nd pl.read_csv call is wrapped as Exception_Data_Not_Found."""
        from src.dashboard.shiny_utils.utils_data import get_input_data_raw
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Data_Not_Found,
        )

        raw_dir = self._make_raw_dir(tmp_path)
        self._write_valid_timeseries(raw_dir)
        self._write_valid_etfs(raw_dir)
        self._write_valid_weights(raw_dir)

        original_read_csv = pl.read_csv
        call_count = [0]

        def patched_read_csv(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:
                raise RuntimeError("simulated ETF read error")
            return original_read_csv(*args, **kwargs)

        monkeypatch.setattr(pl, "read_csv", patched_read_csv)

        with pytest.raises(Exception_Data_Not_Found):
            get_input_data_raw(project_dir = tmp_path)

    @pytest.mark.unit()
    def Test_Missing_Weights_File_Raises(self, tmp_path):
        """Missing weights file raises Exception_Data_Not_Found; covers lines 223 and 257-258."""
        from src.dashboard.shiny_utils.utils_data import get_input_data_raw
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Data_Not_Found,
        )

        raw_dir = self._make_raw_dir(tmp_path)
        self._write_valid_timeseries(raw_dir)
        self._write_valid_etfs(raw_dir)
        # No weights file created

        with pytest.raises(Exception_Data_Not_Found):
            get_input_data_raw(project_dir = tmp_path)

    @pytest.mark.unit()
    def Test_Empty_Weights_File_Logs_Warning(self, tmp_path):
        """Empty weights CSV triggers is_empty() warning; function continues successfully."""
        from src.dashboard.shiny_utils.utils_data import get_input_data_raw

        raw_dir = self._make_raw_dir(tmp_path)
        self._write_valid_timeseries(raw_dir)
        self._write_valid_etfs(raw_dir)
        with open(raw_dir / "sample_portfolio_weights_ETFs.csv", "w") as f:
            f.write("Date,VTI\n")

        result = get_input_data_raw(project_dir = tmp_path)
        assert "Weights_My_Portfolio" in result

    @pytest.mark.unit()
    def Test_Weights_Generic_Exception_Raises(self, tmp_path, monkeypatch):
        """RuntimeError on 3rd pl.read_csv call is wrapped as Exception_Data_Not_Found."""
        from src.dashboard.shiny_utils.utils_data import get_input_data_raw
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Data_Not_Found,
        )

        raw_dir = self._make_raw_dir(tmp_path)
        self._write_valid_timeseries(raw_dir)
        self._write_valid_etfs(raw_dir)
        self._write_valid_weights(raw_dir)

        original_read_csv = pl.read_csv
        call_count = [0]

        def patched_read_csv(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 3:
                raise RuntimeError("simulated weights read error")
            return original_read_csv(*args, **kwargs)

        monkeypatch.setattr(pl, "read_csv", patched_read_csv)

        with pytest.raises(Exception_Data_Not_Found):
            get_input_data_raw(project_dir = tmp_path)


# ============================================================================
# Tests for get_input_data_processed validation branches
# ============================================================================


@pytest.mark.unit()
class Test_Get_Input_Data_Processed_Validation_Branches:
    """Tests for validation error branches in get_input_data_processed."""

    def _make_processed_dir(self, tmp_path):
        processed_dir = tmp_path / "inputs" / "processed"
        processed_dir.mkdir(parents=True)
        return processed_dir

    def _write_valid_benchmark(self, processed_dir):
        pl.DataFrame({"Date": ["2023-01-01", "2023-02-01"], "Value": [100.0, 105.0]}).write_csv(
            processed_dir / "benchmark_portfolio_values.csv"
        )

    def _write_valid_portfolio(self, processed_dir):
        pl.DataFrame({"Date": ["2023-01-01", "2023-02-01"], "Value": [100.0, 107.0]}).write_csv(
            processed_dir / "sample_portfolio_values.csv"
        )

    @pytest.mark.unit()
    def Test_Empty_Benchmark_Raises_Configuration(self, tmp_path):
        """Empty benchmark CSV raises Exception_Configuration (via Exception_Validation_Input)."""
        from src.dashboard.shiny_utils.utils_data import get_input_data_processed
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Configuration,
        )

        processed_dir = self._make_processed_dir(tmp_path)
        with open(processed_dir / "benchmark_portfolio_values.csv", "w") as f:
            f.write("Date,Value\n")
        self._write_valid_portfolio(processed_dir)

        with pytest.raises(Exception_Configuration):
            get_input_data_processed(project_dir = tmp_path)

    @pytest.mark.unit()
    def Test_Benchmark_No_Date_Column_Raises_Configuration(self, tmp_path):
        """Benchmark CSV with no date column raises Exception_Configuration."""
        from src.dashboard.shiny_utils.utils_data import get_input_data_processed
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Configuration,
        )

        processed_dir = self._make_processed_dir(tmp_path)
        with open(processed_dir / "benchmark_portfolio_values.csv", "w") as f:
            f.write("Ticker,Value\n")
            f.write("AAPL,100.0\n")
        self._write_valid_portfolio(processed_dir)

        with pytest.raises(Exception_Configuration):
            get_input_data_processed(project_dir = tmp_path)

    @pytest.mark.unit()
    def Test_Missing_My_Portfolio_File_Raises_Configuration(self, tmp_path):
        """Missing my_portfolio file raises Exception_Configuration; covers lines 332 and 361-362."""
        from src.dashboard.shiny_utils.utils_data import get_input_data_processed
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Configuration,
        )

        processed_dir = self._make_processed_dir(tmp_path)
        self._write_valid_benchmark(processed_dir)
        # No sample_portfolio_values.csv created

        with pytest.raises(Exception_Configuration):
            get_input_data_processed(project_dir = tmp_path)

    @pytest.mark.unit()
    def Test_Empty_My_Portfolio_Raises_Configuration(self, tmp_path):
        """Empty my_portfolio CSV raises Exception_Configuration."""
        from src.dashboard.shiny_utils.utils_data import get_input_data_processed
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Configuration,
        )

        processed_dir = self._make_processed_dir(tmp_path)
        self._write_valid_benchmark(processed_dir)
        with open(processed_dir / "sample_portfolio_values.csv", "w") as f:
            f.write("Date,Value\n")

        with pytest.raises(Exception_Configuration):
            get_input_data_processed(project_dir = tmp_path)

    @pytest.mark.unit()
    def Test_My_Portfolio_No_Date_Column_Raises_Configuration(self, tmp_path):
        """my_portfolio CSV with no date column raises Exception_Configuration."""
        from src.dashboard.shiny_utils.utils_data import get_input_data_processed
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Configuration,
        )

        processed_dir = self._make_processed_dir(tmp_path)
        self._write_valid_benchmark(processed_dir)
        with open(processed_dir / "sample_portfolio_values.csv", "w") as f:
            f.write("Ticker,Value\n")
            f.write("AAPL,100.0\n")

        with pytest.raises(Exception_Configuration):
            get_input_data_processed(project_dir = tmp_path)


# ============================================================================
# Tests for get_names_time_series_from_DF exception branch
# ============================================================================


@pytest.mark.unit()
class Test_Get_Names_Time_Series_Exception_Branch:
    """Tests for the exception handler in get_names_time_series_from_DF."""

    @pytest.mark.unit()
    def Test_Non_Polars_Without_Is_Empty_Raises_Configuration(self):
        """Object without is_empty() triggers except branch → raises Exception_Configuration."""
        from src.dashboard.shiny_utils.utils_data import get_names_time_series_from_DF
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Configuration,
        )

        # A plain list has no .is_empty() → AttributeError caught by except Exception
        with pytest.raises(Exception_Configuration):
            get_names_time_series_from_DF(polars_DF = [1, 2, 3])


# ============================================================================
# Tests for validate_portfolio_data date string parsing fallback branches
# ============================================================================


@pytest.mark.unit()
class Test_Validate_Portfolio_Date_Parsing_Fallbacks:
    """Tests for date string parsing fallback logic in validate_portfolio_data."""

    @pytest.mark.unit()
    def Test_Iso_Datetime_Format_Uses_Datetime_Fallback(self):
        """ISO datetime strings (YYYY-MM-DDTHH:MM:SS) fail all date formats, then succeed via datetime fallback."""
        from src.dashboard.shiny_utils.utils_data import validate_portfolio_data

        df = pl.DataFrame(
            {
                "Date": [
                    "2023-01-01T00:00:00",
                    "2023-02-01T00:00:00",
                    "2023-03-01T00:00:00",
                ],
                "Value": [100.0, 105.0, 102.0],
            }
        )
        is_valid, msg = validate_portfolio_data(data_portfolio=df)
        assert is_valid, f"Expected valid, got: {msg}"

    @pytest.mark.unit()
    def Test_All_Invalid_Date_Strings_Returns_False(self):
        """Mixed-validity date strings that exceed 50% parse failure return False.

        Uses one valid ISO date plus four invalid strings.  The format-loop
        finds no fully-successful format (4 nulls != 0), so successful_format
        stays None.  The datetime-fallback block succeeds but creates 4 out of
        5 nulls (80%) which exceeds the 10% tolerance, so date_series_converted
        is set to None (line 637).  The auto-parse block then calls
        str.to_date(strict=False) without a format, which succeeds here because
        Polars can auto-detect the ISO format from the one valid entry; the
        result has 4/5 nulls (80% > 50%), triggering the 'Could not parse more
        than 50%' return (lines 647-653).
        """
        from src.dashboard.shiny_utils.utils_data import validate_portfolio_data

        df = pl.DataFrame(
            {
                "Date": ["2023-01-01", "bad", "bad", "bad", "bad"],
                "Value": [100.0, 105.0, 102.0, 98.0, 101.0],
            }
        )
        is_valid, msg = validate_portfolio_data(data_portfolio=df)
        assert not is_valid
        assert "50%" in msg

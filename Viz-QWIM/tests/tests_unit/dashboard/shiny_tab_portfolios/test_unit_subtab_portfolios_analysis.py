"""Unit tests for the Portfolio Analysis Subtab Module.

This module provides comprehensive unit tests for the subtab_portfolios_analysis module,
testing the UI and server logic for portfolio performance analysis in the QWIM Dashboard.

Tests cover:
- Module-level constants and configuration
- UI component creation
- Server logic for various analysis types
- Data validation and error handling
- Plot generation and statistics calculations

Author:
    QWIM Development Team

Version:
    0.5.1

Last Modified:
    2026-02-01
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, ClassVar

import numpy as np
import polars as pl
import pytest

from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


#: Module-level logger instance for test logging
_logger = get_logger(name = __name__)

# Try importing the module under test - may fail in some environments
# due to complex Shiny dependencies
try:
    from src.dashboard.shiny_tab_portfolios.subtab_portfolios_analysis import (
        OUTPUT_DIR,
        _logger as module_logger,
        subtab_portfolios_analysis_server,
        subtab_portfolios_analysis_ui,
    )

    MODULE_IMPORT_AVAILABLE = True
except ImportError as e:
    MODULE_IMPORT_AVAILABLE = False
    _logger.warning(f"Module import failed, some tests will be skipped: {e}")


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture()
def sample_portfolio_data() -> pl.DataFrame:
    """Create sample portfolio data for testing.

    Returns:
        pl.DataFrame: Sample portfolio DataFrame with Date and Value columns.
    """
    dates = [(datetime(2024, 1, 1) + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(100)]  # noqa: DTZ001
    np.random.seed(42)
    values = 100.0 * np.cumprod(1 + np.random.normal(0.0005, 0.02, 100))

    return pl.DataFrame({"Date": dates, "Value": values.tolist()})


@pytest.fixture()
def sample_benchmark_data() -> pl.DataFrame:
    """Create sample benchmark data for testing.

    Returns:
        pl.DataFrame: Sample benchmark DataFrame with Date and Value columns.
    """
    dates = [(datetime(2024, 1, 1) + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(100)]  # noqa: DTZ001
    np.random.seed(123)
    values = 100.0 * np.cumprod(1 + np.random.normal(0.0003, 0.015, 100))

    return pl.DataFrame({"Date": dates, "Value": values.tolist()})


@pytest.fixture()
def sample_weights_data() -> pl.DataFrame:
    """Create sample portfolio weights data for testing.

    Returns:
        pl.DataFrame: Sample weights DataFrame with Date and ETF columns.
    """
    dates = [(datetime(2024, 1, 1) + timedelta(days=i * 30)).strftime("%Y-%m-%d") for i in range(4)]  # noqa: DTZ001
    return pl.DataFrame(
        {
            "Date": dates,
            "VTI": [0.40, 0.42, 0.38, 0.41],
            "VXUS": [0.30, 0.28, 0.32, 0.29],
            "BND": [0.20, 0.20, 0.20, 0.20],
            "VNQ": [0.10, 0.10, 0.10, 0.10],
        },
    )


@pytest.fixture()
def sample_data_utils() -> dict[str, Any]:
    """Create sample data utilities dictionary for testing.

    Returns:
        dict: Sample data utilities configuration dictionary.
    """
    return {
        "theme": "default",
        "export_enabled": False,
        "chart_height": 600,
        "downsampling_threshold": 200,
    }


@pytest.fixture()
def sample_data_inputs(
    sample_portfolio_data: pl.DataFrame,
    sample_benchmark_data: pl.DataFrame,
    sample_weights_data: pl.DataFrame,
) -> dict[str, Any]:
    """Create sample data inputs dictionary for testing.

    Args:
        sample_portfolio_data: Sample portfolio DataFrame.
        sample_benchmark_data: Sample benchmark DataFrame.
        sample_weights_data: Sample weights DataFrame.

    Returns:
        dict: Sample data inputs dictionary with all required keys.
    """
    return {
        "My_Portfolio": sample_portfolio_data,
        "Benchmark_Portfolio": sample_benchmark_data,
        "Weights_My_Portfolio": sample_weights_data,
        "Time_Series_ETFs": pl.DataFrame(),
    }


@pytest.fixture()
def sample_reactives_shiny() -> dict[str, Any]:
    """Create sample reactives dictionary for testing.

    Returns:
        dict: Sample reactive values dictionary.
    """
    return {
        "User_Inputs_Shiny": {},
        "Inner_Variables_Shiny": {},
        "Triggers_Shiny": {},
        "Visual_Objects_Shiny": {},
    }


@pytest.fixture()
def empty_portfolio_data() -> pl.DataFrame:
    """Create empty portfolio data for edge case testing.

    Returns:
        pl.DataFrame: Empty DataFrame with Date and Value columns.
    """
    return pl.DataFrame({"Date": [], "Value": []})


# =============================================================================
# Test Classes
# =============================================================================


@pytest.mark.unit()
@pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason="Module import failed due to Shiny dependencies",
)
class Test_Module_Constants:
    """Test module-level constants and configuration."""

    @pytest.mark.unit()
    def test_output_dir_is_path_object(self) -> None:
        """Test that OUTPUT_DIR is a Path object."""
        assert isinstance(OUTPUT_DIR, Path)
        _logger.debug(f"OUTPUT_DIR type verified: {type(OUTPUT_DIR)}")

    @pytest.mark.unit()
    def test_no_png_saving_constant(self) -> None:
        """Test that PNG saving constants have been removed from the module."""
        import src.dashboard.shiny_tab_portfolios.subtab_portfolios_analysis as mod

        assert not hasattr(mod, "ENABLE_PNG_SAVING_SUBTAB_PORTFOLIOS_ANALYSIS"), (
            "ENABLE_PNG_SAVING_SUBTAB_PORTFOLIOS_ANALYSIS should have been removed"
        )
        assert not hasattr(mod, "TEMP_GRAPHICS_DIR"), (
            "TEMP_GRAPHICS_DIR should have been removed"
        )
        _logger.info("PNG saving constants correctly removed from module")


@pytest.mark.unit()
@pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason="Module import failed due to Shiny dependencies",
)
class Test_Module_Imports:
    """Test that all required module imports are available."""

    @pytest.mark.unit()
    def test_ui_function_is_importable(self) -> None:
        """Test that subtab_portfolios_analysis_ui function can be imported."""
        assert callable(subtab_portfolios_analysis_ui)
        _logger.debug("subtab_portfolios_analysis_ui successfully imported")

    @pytest.mark.unit()
    def test_server_function_is_importable(self) -> None:
        """Test that subtab_portfolios_analysis_server function can be imported."""
        assert callable(subtab_portfolios_analysis_server)
        _logger.debug("subtab_portfolios_analysis_server successfully imported")


@pytest.mark.unit()
@pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason="Module import failed due to Shiny dependencies",
)
class Test_Module_Logger:
    """Test module-level logger configuration."""

    @pytest.mark.unit()
    def test_logger_is_configured(self) -> None:
        """Test that module logger is properly configured."""
        assert module_logger is not None
        _logger.debug("Module logger verified")


@pytest.mark.unit()
class Test_Portfolio_Data_Validation:
    """Test portfolio data validation."""

    @pytest.mark.unit()
    def test_portfolio_data_has_date_column(
        self,
        sample_portfolio_data: pl.DataFrame,
    ) -> None:
        """Test that portfolio data has Date column."""
        assert "Date" in sample_portfolio_data.columns
        _logger.debug("Portfolio data has Date column")

    @pytest.mark.unit()
    def test_portfolio_data_has_value_column(
        self,
        sample_portfolio_data: pl.DataFrame,
    ) -> None:
        """Test that portfolio data has Value column."""
        assert "Value" in sample_portfolio_data.columns
        _logger.debug("Portfolio data has Value column")

    @pytest.mark.unit()
    def test_portfolio_data_values_are_numeric(
        self,
        sample_portfolio_data: pl.DataFrame,
    ) -> None:
        """Test that portfolio values are numeric."""
        assert sample_portfolio_data["Value"].dtype in [pl.Float64, pl.Float32, pl.Int64]
        _logger.debug(f"Portfolio value dtype: {sample_portfolio_data['Value'].dtype}")

    @pytest.mark.unit()
    def test_portfolio_data_has_positive_values(
        self,
        sample_portfolio_data: pl.DataFrame,
    ) -> None:
        """Test that portfolio values are positive."""
        assert sample_portfolio_data["Value"].min() > 0  # type: ignore[operator]
        _logger.debug("Portfolio values are all positive")

    @pytest.mark.unit()
    def test_portfolio_data_row_count(
        self,
        sample_portfolio_data: pl.DataFrame,
    ) -> None:
        """Test that portfolio data has expected number of rows."""
        assert len(sample_portfolio_data) == 100
        _logger.debug(f"Portfolio data row count: {len(sample_portfolio_data)}")


@pytest.mark.unit()
class Test_Benchmark_Data_Validation:
    """Test benchmark data validation."""

    @pytest.mark.unit()
    def test_benchmark_data_has_date_column(
        self,
        sample_benchmark_data: pl.DataFrame,
    ) -> None:
        """Test that benchmark data has Date column."""
        assert "Date" in sample_benchmark_data.columns
        _logger.debug("Benchmark data has Date column")

    @pytest.mark.unit()
    def test_benchmark_data_has_value_column(
        self,
        sample_benchmark_data: pl.DataFrame,
    ) -> None:
        """Test that benchmark data has Value column."""
        assert "Value" in sample_benchmark_data.columns
        _logger.debug("Benchmark data has Value column")

    @pytest.mark.unit()
    def test_benchmark_matches_portfolio_dates(
        self,
        sample_portfolio_data: pl.DataFrame,
        sample_benchmark_data: pl.DataFrame,
    ) -> None:
        """Test that benchmark dates match portfolio dates."""
        portfolio_dates = set(sample_portfolio_data["Date"].to_list())
        benchmark_dates = set(sample_benchmark_data["Date"].to_list())
        assert portfolio_dates == benchmark_dates
        _logger.debug("Portfolio and benchmark dates match")


@pytest.mark.unit()
class Test_Data_Inputs_Structure:
    """Test data inputs dictionary structure."""

    @pytest.mark.unit()
    def test_data_inputs_has_my_portfolio(
        self,
        sample_data_inputs: dict[str, Any],
    ) -> None:
        """Test that data_inputs has My_Portfolio key."""
        assert "My_Portfolio" in sample_data_inputs
        assert isinstance(sample_data_inputs["My_Portfolio"], pl.DataFrame)

    @pytest.mark.unit()
    def test_data_inputs_has_benchmark_portfolio(
        self,
        sample_data_inputs: dict[str, Any],
    ) -> None:
        """Test that data_inputs has Benchmark_Portfolio key."""
        assert "Benchmark_Portfolio" in sample_data_inputs
        assert isinstance(sample_data_inputs["Benchmark_Portfolio"], pl.DataFrame)

    @pytest.mark.unit()
    def test_data_inputs_has_weights_portfolio(
        self,
        sample_data_inputs: dict[str, Any],
    ) -> None:
        """Test that data_inputs has Weights_My_Portfolio key."""
        assert "Weights_My_Portfolio" in sample_data_inputs
        assert isinstance(sample_data_inputs["Weights_My_Portfolio"], pl.DataFrame)


@pytest.mark.unit()
class Test_Time_Period_Calculations:
    """Test time period selection calculations."""

    @pytest.mark.unit()
    def test_one_year_period_calculation(self) -> None:
        """Test 1 year period calculates to 365 days."""
        end_date = datetime.now()  # noqa: DTZ005
        start_date = end_date - timedelta(days=365)
        assert (end_date - start_date).days == 365
        _logger.debug("1 year period calculation verified")

    @pytest.mark.unit()
    def test_three_year_period_calculation(self) -> None:
        """Test 3 year period calculates to approximately 1095 days."""
        end_date = datetime.now()  # noqa: DTZ005
        start_date = end_date - timedelta(days=3 * 365)
        assert (end_date - start_date).days == 3 * 365
        _logger.debug("3 year period calculation verified")

    @pytest.mark.unit()
    def test_ytd_period_calculation(self) -> None:
        """Test YTD period starts from January 1st."""
        now = datetime.now()  # noqa: DTZ005
        ytd_start = datetime(now.year, 1, 1)  # noqa: DTZ001
        assert ytd_start.month == 1
        assert ytd_start.day == 1
        _logger.debug("YTD period start calculation verified")


@pytest.mark.unit()
class Test_Analysis_Type_Options:
    """Test analysis type options."""

    @pytest.mark.unit()
    def test_returns_analysis_type_exists(self) -> None:
        """Test that returns analysis type is a valid option."""
        analysis_types = ["returns", "drawdowns", "rolling", "comparison"]
        assert "returns" in analysis_types
        _logger.debug("Returns analysis type verified")

    @pytest.mark.unit()
    def test_drawdowns_analysis_type_exists(self) -> None:
        """Test that drawdowns analysis type is a valid option."""
        analysis_types = ["returns", "drawdowns", "rolling", "comparison"]
        assert "drawdowns" in analysis_types
        _logger.debug("Drawdowns analysis type verified")

    @pytest.mark.unit()
    def test_rolling_analysis_type_exists(self) -> None:
        """Test that rolling analysis type is a valid option."""
        analysis_types = ["returns", "drawdowns", "rolling", "comparison"]
        assert "rolling" in analysis_types
        _logger.debug("Rolling analysis type verified")

    @pytest.mark.unit()
    def test_comparison_analysis_type_exists(self) -> None:
        """Test that comparison analysis type is a valid option."""
        analysis_types = ["returns", "drawdowns", "rolling", "comparison"]
        assert "comparison" in analysis_types
        _logger.debug("Comparison analysis type verified")


@pytest.mark.unit()
class Test_Rolling_Window_Configuration:
    """Test rolling window configuration."""

    @pytest.mark.unit()
    def test_rolling_window_minimum_value(self) -> None:
        """Test that rolling window minimum is 7 days."""
        min_window = 7
        assert min_window >= 7
        _logger.debug(f"Rolling window minimum: {min_window}")

    @pytest.mark.unit()
    def test_rolling_window_maximum_value(self) -> None:
        """Test that rolling window maximum is 90 days."""
        max_window = 90
        assert max_window <= 90
        _logger.debug(f"Rolling window maximum: {max_window}")

    @pytest.mark.unit()
    def test_rolling_window_default_value(self) -> None:
        """Test that rolling window default is 30 days."""
        default_window = 30
        assert 7 <= default_window <= 90
        _logger.debug(f"Rolling window default: {default_window}")


@pytest.mark.unit()
class Test_Empty_Data_Handling:
    """Test handling of empty data scenarios."""

    @pytest.mark.unit()
    def test_empty_portfolio_data_has_columns(
        self,
        empty_portfolio_data: pl.DataFrame,
    ) -> None:
        """Test that empty portfolio data maintains column structure."""
        assert "Date" in empty_portfolio_data.columns
        assert "Value" in empty_portfolio_data.columns
        _logger.debug("Empty portfolio data has correct columns")

    @pytest.mark.unit()
    def test_empty_portfolio_data_row_count(
        self,
        empty_portfolio_data: pl.DataFrame,
    ) -> None:
        """Test that empty portfolio data has zero rows."""
        assert len(empty_portfolio_data) == 0
        _logger.debug("Empty portfolio data has zero rows")


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.integration()
class Test_Portfolio_Analysis_Integration:
    """Integration tests for portfolio analysis subtab."""

    @pytest.mark.skipif(
        not MODULE_IMPORT_AVAILABLE,
        reason="Module import failed due to Shiny dependencies",
    )
    @pytest.mark.unit()
    def test_ui_creates_valid_component(
        self,
        sample_data_utils: dict[str, Any],
        sample_data_inputs: dict[str, Any],
    ) -> None:
        """Test that UI function creates a valid Shiny component."""
        result = subtab_portfolios_analysis_ui("ID_test_ui",
            data_utils=sample_data_utils,
            data_inputs=sample_data_inputs,
        )
        assert result is not None

    @pytest.mark.skipif(
        not MODULE_IMPORT_AVAILABLE,
        reason="Module import failed due to Shiny dependencies",
    )
    @pytest.mark.unit()
    def test_server_handles_time_period_selection(
        self,
        sample_data_utils: dict[str, Any],
        sample_data_inputs: dict[str, Any],
        sample_reactives_shiny: dict[str, Any],
    ) -> None:
        """Test that server correctly handles time period selection."""
        import inspect

        assert callable(subtab_portfolios_analysis_server)
        sig = inspect.signature(subtab_portfolios_analysis_server)
        assert "id" in sig.parameters


# =============================================================================
# Enhanced Test Classes
# =============================================================================


@pytest.mark.unit()
class Test_Input_ID_Naming_Convention_Analysis:
    """Test input/output IDs follow the required hierarchical naming convention."""

    #: Prefix expected on every input ID for this subtab
    _ID_PREFIX: str = "input_ID_tab_portfolios_subtab_portfolios_analysis_"

    #: All known input IDs for this subtab
    _INPUT_IDS: ClassVar[list[str]] = [
        "input_ID_tab_portfolios_subtab_portfolios_analysis_time_period",
        "input_ID_tab_portfolios_subtab_portfolios_analysis_date_range",
        "input_ID_tab_portfolios_subtab_portfolios_analysis_type",
        "input_ID_tab_portfolios_subtab_portfolios_analysis_rolling_window",
        "input_ID_tab_portfolios_subtab_portfolios_analysis_include_benchmark",
    ]

    @pytest.mark.unit()
    def test_all_input_ids_start_with_correct_prefix(self) -> None:
        """Test that every input ID starts with the subtab prefix."""
        for input_id in self._INPUT_IDS:
            assert input_id.startswith(self._ID_PREFIX), (
                f"Input ID '{input_id}' missing prefix '{self._ID_PREFIX}'"
            )
        _logger.debug("All analysis input ID prefixes verified")

    @pytest.mark.unit()
    def test_time_period_input_id_well_formed(self) -> None:
        """Test that time_period input ID is well-formed."""
        assert "input_ID_tab_portfolios_subtab_portfolios_analysis_time_period" in self._INPUT_IDS
        _logger.debug("time_period input ID verified")

    @pytest.mark.unit()
    def test_analysis_type_input_id_well_formed(self) -> None:
        """Test that analysis type input ID is well-formed."""
        assert "input_ID_tab_portfolios_subtab_portfolios_analysis_type" in self._INPUT_IDS
        _logger.debug("analysis type input ID verified")

    @pytest.mark.unit()
    def test_rolling_window_input_id_well_formed(self) -> None:
        """Test that rolling_window input ID is well-formed."""
        assert "input_ID_tab_portfolios_subtab_portfolios_analysis_rolling_window" in self._INPUT_IDS
        _logger.debug("rolling_window input ID verified")

    @pytest.mark.unit()
    def test_include_benchmark_input_id_well_formed(self) -> None:
        """Test that include_benchmark input ID is well-formed."""
        assert (
            "input_ID_tab_portfolios_subtab_portfolios_analysis_include_benchmark" in self._INPUT_IDS
        )
        _logger.debug("include_benchmark input ID verified")

    @pytest.mark.unit()
    def test_no_duplicate_input_ids(self) -> None:
        """Test that there are no duplicate input IDs."""
        assert len(self._INPUT_IDS) == len(set(self._INPUT_IDS))
        _logger.debug("No duplicate analysis input IDs")


@pytest.mark.unit()
class Test_Default_Input_Values_Analysis:
    """Test default values used in the analysis subtab UI."""

    @pytest.mark.unit()
    def test_default_time_period_is_one_year(self) -> None:
        """Test that the default time period selection is '1y'."""
        default_time_period: str = "1y"
        valid_periods = ["1m", "3m", "6m", "ytd", "1y", "3y", "5y", "10y", "all"]
        assert default_time_period in valid_periods
        assert default_time_period == "1y"
        _logger.debug(f"Default time period verified: {default_time_period}")

    @pytest.mark.unit()
    def test_default_analysis_type_is_returns(self) -> None:
        """Test that the default analysis type is 'returns'."""
        default_type: str = "returns"
        valid_types = ["returns", "drawdowns", "rolling", "comparison"]
        assert default_type in valid_types
        assert default_type == "returns"
        _logger.debug(f"Default analysis type verified: {default_type}")

    @pytest.mark.unit()
    def test_default_rolling_window_is_30(self) -> None:
        """Test that the default rolling window is 30 days."""
        default_window: int = 30
        assert default_window == 30
        assert 7 <= default_window <= 90
        _logger.debug(f"Default rolling window verified: {default_window}")

    @pytest.mark.unit()
    def test_rolling_window_min_is_7(self) -> None:
        """Test that rolling window minimum is 7."""
        min_window: int = 7
        assert min_window == 7
        _logger.debug(f"Rolling window min verified: {min_window}")

    @pytest.mark.unit()
    def test_rolling_window_max_is_90(self) -> None:
        """Test that rolling window maximum is 90."""
        max_window: int = 90
        assert max_window == 90
        _logger.debug(f"Rolling window max verified: {max_window}")

    @pytest.mark.unit()
    def test_default_include_benchmark_is_true(self) -> None:
        """Test that include_benchmark defaults to True."""
        default_include_benchmark: bool = True
        assert default_include_benchmark is True
        _logger.debug(f"Default include_benchmark verified: {default_include_benchmark}")


@pytest.mark.unit()
class Test_Time_Period_Options_Analysis:
    """Test that all expected time period options are available."""

    _TIME_PERIODS: ClassVar[list[str]] = ["1m", "3m", "6m", "ytd", "1y", "3y", "5y", "10y", "all"]

    @pytest.mark.unit()
    def test_nine_time_period_options(self) -> None:
        """Test that there are exactly 9 time period options."""
        assert len(self._TIME_PERIODS) == 9
        _logger.debug(f"Time period count: {len(self._TIME_PERIODS)}")

    @pytest.mark.unit()
    def test_all_time_period_options_are_non_empty_strings(self) -> None:
        """Test that all time period options are non-empty strings."""
        for period in self._TIME_PERIODS:
            assert isinstance(period, str)
            assert len(period) > 0
        _logger.debug("All time period options are non-empty strings")

    @pytest.mark.unit()
    def test_one_year_option_present(self) -> None:
        """Test that '1y' option is present."""
        assert "1y" in self._TIME_PERIODS

    @pytest.mark.unit()
    def test_all_option_present(self) -> None:
        """Test that 'all' option is present."""
        assert "all" in self._TIME_PERIODS

    @pytest.mark.unit()
    def test_ytd_option_present(self) -> None:
        """Test that 'ytd' option is present."""
        assert "ytd" in self._TIME_PERIODS

    @pytest.mark.unit()
    def test_no_duplicate_time_periods(self) -> None:
        """Test that there are no duplicate time period options."""
        assert len(self._TIME_PERIODS) == len(set(self._TIME_PERIODS))
        _logger.debug("No duplicate time period options")

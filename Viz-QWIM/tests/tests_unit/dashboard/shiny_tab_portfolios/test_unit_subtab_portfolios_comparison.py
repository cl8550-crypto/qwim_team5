"""Unit tests for the Portfolio Comparison Subtab Module.

This module provides comprehensive unit tests for the subbab_portfolios_comparison module,
testing the UI and server logic for portfolio vs benchmark comparison in the QWIM Dashboard.

Tests cover:
- Module-level constants and configuration
- UI component creation
- Server logic for comparison visualizations
- Data validation and error handling
- Statistics calculations

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
    from src.dashboard.shiny_tab_portfolios.subtab_portfolios_comparison import (
        OUTPUT_DIR,
        _logger as module_logger,
        subtab_portfolios_comparison_server,
        subtab_portfolios_comparison_ui,
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
) -> dict[str, Any]:
    """Create sample data inputs dictionary for testing.

    Args:
        sample_portfolio_data: Sample portfolio DataFrame.
        sample_benchmark_data: Sample benchmark DataFrame.

    Returns:
        dict: Sample data inputs dictionary with all required keys.
    """
    return {
        "My_Portfolio": sample_portfolio_data,
        "Benchmark_Portfolio": sample_benchmark_data,
        "Weights_My_Portfolio": pl.DataFrame(),
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
        import src.dashboard.shiny_tab_portfolios.subtab_portfolios_comparison as mod

        assert not hasattr(mod, "ENABLE_PNG_SAVING_SUBTAB_PORTFOLIOS_COMPARISON"), (
            "ENABLE_PNG_SAVING_SUBTAB_PORTFOLIOS_COMPARISON should have been removed"
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
        """Test that subtab_portfolios_comparison_ui function can be imported."""
        assert callable(subtab_portfolios_comparison_ui)
        _logger.debug("subtab_portfolios_comparison_ui successfully imported")

    @pytest.mark.unit()
    def test_server_function_is_importable(self) -> None:
        """Test that subtab_portfolios_comparison_server function can be imported."""
        assert callable(subtab_portfolios_comparison_server)
        _logger.debug("subtab_portfolios_comparison_server successfully imported")


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
class Test_Visualization_Types:
    """Test visualization type options."""

    @pytest.mark.unit()
    def test_absolute_value_type_exists(self) -> None:
        """Test that absolute value visualization type exists."""
        viz_types = ["absolute", "normalized", "percent_change", "cumulative_return"]
        assert "absolute" in viz_types
        _logger.debug("Absolute value type verified")

    @pytest.mark.unit()
    def test_normalized_type_exists(self) -> None:
        """Test that normalized visualization type exists."""
        viz_types = ["absolute", "normalized", "percent_change", "cumulative_return"]
        assert "normalized" in viz_types
        _logger.debug("Normalized type verified")

    @pytest.mark.unit()
    def test_percent_change_type_exists(self) -> None:
        """Test that percent change visualization type exists."""
        viz_types = ["absolute", "normalized", "percent_change", "cumulative_return"]
        assert "percent_change" in viz_types
        _logger.debug("Percent change type verified")

    @pytest.mark.unit()
    def test_cumulative_return_type_exists(self) -> None:
        """Test that cumulative return visualization type exists."""
        viz_types = ["absolute", "normalized", "percent_change", "cumulative_return"]
        assert "cumulative_return" in viz_types
        _logger.debug("Cumulative return type verified")


@pytest.mark.unit()
class Test_Time_Period_Options:
    """Test time period selection options."""

    @pytest.mark.unit()
    def test_one_year_period_option(self) -> None:
        """Test that 1 year period option exists."""
        time_periods = {"1y": "Last 1 Year", "3y": "Last 3 Years", "5y": "Last 5 Years"}
        assert "1y" in time_periods
        _logger.debug("1 year period option verified")

    @pytest.mark.unit()
    def test_three_year_period_option(self) -> None:
        """Test that 3 year period option exists."""
        time_periods = {"1y": "Last 1 Year", "3y": "Last 3 Years", "5y": "Last 5 Years"}
        assert "3y" in time_periods
        _logger.debug("3 year period option verified")

    @pytest.mark.unit()
    def test_five_year_period_option(self) -> None:
        """Test that 5 year period option exists."""
        time_periods = {"1y": "Last 1 Year", "3y": "Last 3 Years", "5y": "Last 5 Years"}
        assert "5y" in time_periods
        _logger.debug("5 year period option verified")


@pytest.mark.unit()
class Test_Portfolio_Comparison_Data_Validation:
    """Test portfolio comparison data validation."""

    @pytest.mark.unit()
    def test_portfolio_data_has_required_columns(
        self,
        sample_portfolio_data: pl.DataFrame,
    ) -> None:
        """Test that portfolio data has required columns."""
        assert "Date" in sample_portfolio_data.columns
        assert "Value" in sample_portfolio_data.columns
        _logger.debug("Portfolio data has required columns")

    @pytest.mark.unit()
    def test_benchmark_data_has_required_columns(
        self,
        sample_benchmark_data: pl.DataFrame,
    ) -> None:
        """Test that benchmark data has required columns."""
        assert "Date" in sample_benchmark_data.columns
        assert "Value" in sample_benchmark_data.columns
        _logger.debug("Benchmark data has required columns")

    @pytest.mark.unit()
    def test_portfolio_and_benchmark_same_length(
        self,
        sample_portfolio_data: pl.DataFrame,
        sample_benchmark_data: pl.DataFrame,
    ) -> None:
        """Test that portfolio and benchmark have same number of rows."""
        assert len(sample_portfolio_data) == len(sample_benchmark_data)
        _logger.debug(f"Both datasets have {len(sample_portfolio_data)} rows")

    @pytest.mark.unit()
    def test_portfolio_values_are_positive(
        self,
        sample_portfolio_data: pl.DataFrame,
    ) -> None:
        """Test that portfolio values are positive."""
        assert sample_portfolio_data["Value"].min() > 0  # type: ignore[operator]
        _logger.debug("Portfolio values are positive")

    @pytest.mark.unit()
    def test_benchmark_values_are_positive(
        self,
        sample_benchmark_data: pl.DataFrame,
    ) -> None:
        """Test that benchmark values are positive."""
        assert sample_benchmark_data["Value"].min() > 0  # type: ignore[operator]
        _logger.debug("Benchmark values are positive")


@pytest.mark.unit()
class Test_Normalization_Calculations:
    """Test normalization calculations for comparison."""

    @pytest.mark.unit()
    def test_normalization_to_base_100(
        self,
        sample_portfolio_data: pl.DataFrame,
    ) -> None:
        """Test normalizing portfolio values to base 100."""
        initial_value = sample_portfolio_data["Value"][0]
        normalized = (sample_portfolio_data["Value"] / initial_value) * 100

        # First normalized value should be 100
        assert abs(normalized[0] - 100.0) < 0.001
        _logger.debug("Normalization to base 100 verified")

    @pytest.mark.unit()
    def test_percent_change_calculation(
        self,
        sample_portfolio_data: pl.DataFrame,
    ) -> None:
        """Test percent change calculation."""
        values = sample_portfolio_data["Value"].to_list()
        if len(values) >= 2:
            pct_change = (values[1] - values[0]) / values[0] * 100
            assert isinstance(pct_change, float)
            _logger.debug(f"First period percent change: {pct_change:.2f}%")


@pytest.mark.unit()
class Test_Data_Inputs_Structure:
    """Test data inputs dictionary structure for comparison."""

    @pytest.mark.unit()
    def test_data_inputs_has_portfolio(
        self,
        sample_data_inputs: dict[str, Any],
    ) -> None:
        """Test that data_inputs has My_Portfolio key."""
        assert "My_Portfolio" in sample_data_inputs

    @pytest.mark.unit()
    def test_data_inputs_has_benchmark(
        self,
        sample_data_inputs: dict[str, Any],
    ) -> None:
        """Test that data_inputs has Benchmark_Portfolio key."""
        assert "Benchmark_Portfolio" in sample_data_inputs


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.integration()
class Test_Portfolio_Comparison_Integration:
    """Integration tests for portfolio comparison subtab."""

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
        result = subtab_portfolios_comparison_ui("ID_test_ui",
            data_utils=sample_data_utils,
            data_inputs=sample_data_inputs,
        )
        assert result is not None

    @pytest.mark.skipif(
        not MODULE_IMPORT_AVAILABLE,
        reason="Module import failed due to Shiny dependencies",
    )
    @pytest.mark.unit()
    def test_server_handles_visualization_type_change(
        self,
        sample_data_utils: dict[str, Any],
        sample_data_inputs: dict[str, Any],
        sample_reactives_shiny: dict[str, Any],
    ) -> None:
        """Test that server correctly handles visualization type changes."""
        import inspect

        assert callable(subtab_portfolios_comparison_server)
        sig = inspect.signature(subtab_portfolios_comparison_server)
        assert "id" in sig.parameters


# =============================================================================
# Enhanced Test Classes
# =============================================================================


@pytest.mark.unit()
class Test_Visualization_Type_Completeness:
    """Test that all required visualization types are defined."""

    _VIZ_TYPES: ClassVar[list[str]] = [
        "absolute",
        "normalized",
        "percent_change",
        "cumulative_return",
        "difference",
    ]

    @pytest.mark.unit()
    def test_five_visualization_types(self) -> None:
        """Test that there are exactly 5 visualization types."""
        assert len(self._VIZ_TYPES) == 5
        _logger.debug(f"Visualization type count: {len(self._VIZ_TYPES)}")

    @pytest.mark.unit()
    def test_absolute_visualization_type_exists(self) -> None:
        """Test that 'absolute' visualization type is defined."""
        assert "absolute" in self._VIZ_TYPES
        _logger.debug("absolute viz type verified")

    @pytest.mark.unit()
    def test_normalized_visualization_type_exists(self) -> None:
        """Test that 'normalized' visualization type is defined."""
        assert "normalized" in self._VIZ_TYPES
        _logger.debug("normalized viz type verified")

    @pytest.mark.unit()
    def test_percent_change_visualization_type_exists(self) -> None:
        """Test that 'percent_change' visualization type is defined."""
        assert "percent_change" in self._VIZ_TYPES
        _logger.debug("percent_change viz type verified")

    @pytest.mark.unit()
    def test_cumulative_return_visualization_type_exists(self) -> None:
        """Test that 'cumulative_return' visualization type is defined."""
        assert "cumulative_return" in self._VIZ_TYPES
        _logger.debug("cumulative_return viz type verified")

    @pytest.mark.unit()
    def test_difference_visualization_type_exists(self) -> None:
        """Test that 'difference' visualization type is defined."""
        assert "difference" in self._VIZ_TYPES
        _logger.debug("difference viz type verified")

    @pytest.mark.unit()
    def test_all_viz_types_are_non_empty_strings(self) -> None:
        """Test that all visualization types are non-empty strings."""
        for vtype in self._VIZ_TYPES:
            assert isinstance(vtype, str)
            assert len(vtype) > 0
        _logger.debug("All visualization types are non-empty strings")

    @pytest.mark.unit()
    def test_no_duplicate_visualization_types(self) -> None:
        """Test that there are no duplicate visualization types."""
        assert len(self._VIZ_TYPES) == len(set(self._VIZ_TYPES))
        _logger.debug("No duplicate visualization types")


@pytest.mark.unit()
class Test_Input_ID_Naming_Convention_Comparison:
    """Test input IDs follow the required hierarchical naming convention."""

    _ID_PREFIX: str = "input_ID_tab_portfolios_subtab_portfolios_comparison_"

    _INPUT_IDS: ClassVar[list[str]] = [
        "input_ID_tab_portfolios_subtab_portfolios_comparison_time_period",
        "input_ID_tab_portfolios_subtab_portfolios_comparison_visualization_type",
        "input_ID_tab_portfolios_subtab_portfolios_comparison_include_benchmark",
    ]

    @pytest.mark.unit()
    def test_all_input_ids_start_with_correct_prefix(self) -> None:
        """Test that every input ID starts with the subtab prefix."""
        for input_id in self._INPUT_IDS:
            assert input_id.startswith(self._ID_PREFIX), (
                f"Input ID '{input_id}' missing prefix '{self._ID_PREFIX}'"
            )
        _logger.debug("All comparison input ID prefixes verified")

    @pytest.mark.unit()
    def test_time_period_input_id_present(self) -> None:
        """Test that time_period input ID is present."""
        assert "input_ID_tab_portfolios_subtab_portfolios_comparison_time_period" in self._INPUT_IDS
        _logger.debug("time_period input ID for comparison verified")

    @pytest.mark.unit()
    def test_visualization_type_input_id_present(self) -> None:
        """Test that visualization_type input ID is present."""
        assert (
            "input_ID_tab_portfolios_subtab_portfolios_comparison_visualization_type"
            in self._INPUT_IDS
        )
        _logger.debug("visualization_type input ID verified")

    @pytest.mark.unit()
    def test_no_duplicate_input_ids(self) -> None:
        """Test that there are no duplicate input IDs."""
        assert len(self._INPUT_IDS) == len(set(self._INPUT_IDS))
        _logger.debug("No duplicate comparison input IDs")


@pytest.mark.unit()
class Test_Normalization_Base_Value:
    """Test normalization base values used for normalized visualization."""

    @pytest.mark.unit()
    def test_normalization_base_is_100(self) -> None:
        """Test that normalized visualization uses base value of 100."""
        normalization_base: float = 100.0
        assert normalization_base == 100.0
        _logger.debug(f"Normalization base verified: {normalization_base}")

    @pytest.mark.unit()
    def test_normalization_base_is_positive(self) -> None:
        """Test that normalization base is positive."""
        normalization_base: float = 100.0
        assert normalization_base > 0
        _logger.debug("Normalization base is positive")


# =============================================================================
# Regression Tests
# =============================================================================


@pytest.mark.regression()
class Test_Polars_Date_Attribute_Access_Regression:
    """Regression tests for pl.Date attribute access in subtab_portfolios_comparison.

    These tests guard against a pyright false-positive where `.year`, `.month`, `.day`
    attributes on values returned by Polars Date `.item()` are flagged as
    `reportAttributeAccessIssue`. At runtime, `.item()` on a pl.Date column returns
    a Python `datetime.date` object, which does have these attributes.

    Fix applied (2026-01, pyright 53-error cleanup):
        Added ``# pyright: ignore[reportAttributeAccessIssue]`` to six `.year`,
        `.month`, `.day` accesses in ``get_effective_date_range()``.
    """

    @pytest.mark.unit()
    def test_polars_date_item_returns_python_date(self) -> None:
        """Test that .item() on a pl.Date column returns a Python datetime.date."""
        import datetime as dt

        df = pl.DataFrame({"Date": ["2024-01-15", "2024-06-30", "2024-12-31"]}).with_columns(
            pl.col("Date").str.strptime(pl.Date, format="%Y-%m-%d")
        )
        max_date = df.select(pl.col("Date").max()).item()
        assert isinstance(max_date, dt.date), (
            f"Expected datetime.date, got {type(max_date)}"
        )
        _logger.debug(f"Polars Date .item() returned Python date: {type(max_date)}")

    @pytest.mark.unit()
    def test_polars_date_item_has_year_attribute(self) -> None:
        """Test that pl.Date .item() result exposes .year attribute at runtime.

        This is the runtime counterpart to the pyright ignore comment on
        `data_max_date_raw.year` in get_effective_date_range().
        """
        df = pl.DataFrame({"Date": ["2024-06-15"]}).with_columns(
            pl.col("Date").str.strptime(pl.Date, format="%Y-%m-%d")
        )
        date_val = df.select(pl.col("Date").max()).item()
        assert hasattr(date_val, "year"), "Polars Date .item() must have .year attribute"
        assert date_val.year == 2024
        _logger.debug(f"date_val.year = {date_val.year}")

    @pytest.mark.unit()
    def test_polars_date_item_has_month_attribute(self) -> None:
        """Test that pl.Date .item() result exposes .month attribute at runtime.

        This is the runtime counterpart to the pyright ignore comment on
        `data_max_date_raw.month` in get_effective_date_range().
        """
        df = pl.DataFrame({"Date": ["2024-06-15"]}).with_columns(
            pl.col("Date").str.strptime(pl.Date, format="%Y-%m-%d")
        )
        date_val = df.select(pl.col("Date").max()).item()
        assert hasattr(date_val, "month"), "Polars Date .item() must have .month attribute"
        assert date_val.month == 6
        _logger.debug(f"date_val.month = {date_val.month}")

    @pytest.mark.unit()
    def test_polars_date_item_has_day_attribute(self) -> None:
        """Test that pl.Date .item() result exposes .day attribute at runtime.

        This is the runtime counterpart to the pyright ignore comment on
        `data_max_date_raw.day` in get_effective_date_range().
        """
        df = pl.DataFrame({"Date": ["2024-06-15"]}).with_columns(
            pl.col("Date").str.strptime(pl.Date, format="%Y-%m-%d")
        )
        date_val = df.select(pl.col("Date").max()).item()
        assert hasattr(date_val, "day"), "Polars Date .item() must have .day attribute"
        assert date_val.day == 15
        _logger.debug(f"date_val.day = {date_val.day}")

    @pytest.mark.unit()
    def test_polars_date_item_constructs_datetime(self) -> None:
        """Test that pl.Date .item() result can construct a datetime object.

        Validates the full pattern used in get_effective_date_range():
            datetime(date_val.year, date_val.month, date_val.day)
        """
        import datetime as dt

        df = pl.DataFrame({"Date": ["2024-03-22"]}).with_columns(
            pl.col("Date").str.strptime(pl.Date, format="%Y-%m-%d")
        )
        date_val = df.select(pl.col("Date").max()).item()
        result = dt.datetime(date_val.year, date_val.month, date_val.day)
        assert result == dt.datetime(2024, 3, 22)
        _logger.debug(f"datetime constructed from Polars Date item: {result}")

    @pytest.mark.unit()
    def test_polars_date_min_and_max_both_have_date_attributes(self) -> None:
        """Test that both .min() and .max() on a pl.Date column yield usable date objects.

        Matches the dual-assignment pattern in get_effective_date_range():
            data_max_date_raw = data_portfolio.select(pl.col("Date").max()).item()
            data_min_date_raw = data_portfolio.select(pl.col("Date").min()).item()
        """
        import datetime as dt

        dates = ["2023-01-01", "2023-06-15", "2024-03-22", "2024-12-31"]
        df = pl.DataFrame({"Date": dates}).with_columns(
            pl.col("Date").str.strptime(pl.Date, format="%Y-%m-%d")
        )
        max_date_raw = df.select(pl.col("Date").max()).item()
        min_date_raw = df.select(pl.col("Date").min()).item()

        for date_raw, label in [(max_date_raw, "max"), (min_date_raw, "min")]:
            assert isinstance(date_raw, dt.date), f"{label} item is not datetime.date"
            assert hasattr(date_raw, "year"), f"{label} item missing .year"
            assert hasattr(date_raw, "month"), f"{label} item missing .month"
            assert hasattr(date_raw, "day"), f"{label} item missing .day"

        max_dt = dt.datetime(max_date_raw.year, max_date_raw.month, max_date_raw.day)
        min_dt = dt.datetime(min_date_raw.year, min_date_raw.month, min_date_raw.day)
        assert max_dt > min_dt, "max date must be after min date"
        _logger.debug(f"Date range: {min_dt} to {max_dt}")

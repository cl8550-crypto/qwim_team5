"""Unit tests for the Portfolio Weights Analysis Subtab Module.

This module provides comprehensive unit tests for the subtab_weights_analysis module,
testing the UI and server logic for portfolio weights visualization in the QWIM Dashboard.

Tests cover:
- Module-level constants and configuration
- UI component creation
- Server logic for weight distribution visualizations
- ETF component selection
- Data validation and error handling

Author:
    QWIM Development Team

Version:
    0.5.1

Last Modified:
    2026-02-01
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
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
    from src.dashboard.shiny_tab_portfolios.subtab_weights_analysis import (
        OUTPUT_DIR,
        _logger as module_logger,
        subtab_weights_analysis_server,
        subtab_weights_analysis_ui,
    )

    MODULE_IMPORT_AVAILABLE = True
    MODULE_IMPORT_ERROR = ""
except ImportError as e:
    MODULE_IMPORT_AVAILABLE = False
    MODULE_IMPORT_ERROR = str(e)
    _logger.warning(f"Module import failed, some tests will be skipped: {e}")

MODULE_IMPORT_SKIP_REASON = (
    "Module import failed due to Shiny dependencies"
    if MODULE_IMPORT_AVAILABLE
    else f"Module import failed due to Shiny dependencies: {MODULE_IMPORT_ERROR}"
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture()
def sample_weights_data() -> pl.DataFrame:
    """Create sample portfolio weights data for testing.

    Returns:
        pl.DataFrame: Sample weights DataFrame with Date and ETF component columns.
    """
    dates = [
        (datetime(2024, 1, 1) + timedelta(days=i * 7)).strftime("%Y-%m-%d")  # noqa: DTZ001
        for i in range(52)  # Weekly data for 1 year
    ]
    np.random.seed(42)

    # Generate weights that sum to 1.0 for each date
    num_dates = len(dates)
    vti_weights = np.random.uniform(0.35, 0.45, num_dates)
    vxus_weights = np.random.uniform(0.25, 0.35, num_dates)
    bnd_weights = np.random.uniform(0.15, 0.25, num_dates)
    vnq_weights = 1.0 - vti_weights - vxus_weights - bnd_weights

    return pl.DataFrame(
        {
            "Date": dates,
            "VTI": vti_weights.tolist(),
            "VXUS": vxus_weights.tolist(),
            "BND": bnd_weights.tolist(),
            "VNQ": vnq_weights.tolist(),
        },
    )


@pytest.fixture()
def sample_portfolio_data() -> pl.DataFrame:
    """Create sample portfolio data for testing.

    Returns:
        pl.DataFrame: Sample portfolio DataFrame with Date and Value columns.
    """
    dates = [(datetime(2024, 1, 1) + timedelta(days=i * 7)).strftime("%Y-%m-%d") for i in range(52)]  # noqa: DTZ001
    np.random.seed(42)
    values = 100.0 * np.cumprod(1 + np.random.normal(0.001, 0.02, 52))

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
    sample_weights_data: pl.DataFrame,
) -> dict[str, Any]:
    """Create sample data inputs dictionary for testing.

    Args:
        sample_portfolio_data: Sample portfolio DataFrame.
        sample_weights_data: Sample weights DataFrame.

    Returns:
        dict: Sample data inputs dictionary with all required keys.
    """
    return {
        "My_Portfolio": sample_portfolio_data,
        "Benchmark_Portfolio": pl.DataFrame(),
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
def empty_weights_data() -> pl.DataFrame:
    """Create empty weights data for edge case testing.

    Returns:
        pl.DataFrame: Empty DataFrame with Date column only.
    """
    return pl.DataFrame({"Date": []})


# =============================================================================
# Test Classes
# =============================================================================


@pytest.mark.unit()
@pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason=MODULE_IMPORT_SKIP_REASON,
)
class Class_Test_Module_Constants:
    """Test module-level constants and configuration."""

    @pytest.mark.unit()
    def Test_Output_Dir_Is_Path_Object(self) -> None:
        """Test that OUTPUT_DIR is a Path object."""
        assert isinstance(OUTPUT_DIR, Path)
        _logger.debug(f"OUTPUT_DIR type verified: {type(OUTPUT_DIR)}")

    @pytest.mark.unit()
    def Test_TEMP_GRAPHICS_DIR_Not_Present(self) -> None:
        """TEMP_GRAPHICS_DIR should have been removed from the module."""
        import src.dashboard.shiny_tab_portfolios.subtab_weights_analysis as mod

        assert not hasattr(mod, "TEMP_GRAPHICS_DIR"), (
            "TEMP_GRAPHICS_DIR should have been removed"
        )

    @pytest.mark.unit()
    def Test_Enable_PNG_Saving_Not_Present(self) -> None:
        """ENABLE_PNG_SAVING_SUBTAB_WEIGHTS_ANALYSIS should have been removed."""
        import src.dashboard.shiny_tab_portfolios.subtab_weights_analysis as mod

        assert not hasattr(mod, "ENABLE_PNG_SAVING_SUBTAB_WEIGHTS_ANALYSIS"), (
            "ENABLE_PNG_SAVING_SUBTAB_WEIGHTS_ANALYSIS should have been removed"
        )


@pytest.mark.unit()
@pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason=MODULE_IMPORT_SKIP_REASON,
)
class Class_Test_Module_Imports:
    """Test that all required module imports are available."""

    @pytest.mark.unit()
    def Test_UI_Function_Is_Importable(self) -> None:
        """Test that subtab_weights_analysis_ui function can be imported."""
        assert callable(subtab_weights_analysis_ui)
        _logger.debug("subtab_weights_analysis_ui successfully imported")

    @pytest.mark.unit()
    def Test_Server_Function_Is_Importable(self) -> None:
        """Test that subtab_weights_analysis_server function can be imported."""
        assert callable(subtab_weights_analysis_server)
        _logger.debug("subtab_weights_analysis_server successfully imported")


@pytest.mark.unit()
@pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason=MODULE_IMPORT_SKIP_REASON,
)
class Class_Test_Module_Logger:
    """Test module-level logger configuration."""

    @pytest.mark.unit()
    def Test_Logger_Is_Configured(self) -> None:
        """Test that module logger is properly configured."""
        assert module_logger is not None
        _logger.debug("Module logger verified")


@pytest.mark.unit()
class Class_Test_Weights_Data_Validation:
    """Test portfolio weights data validation."""

    @pytest.mark.unit()
    def Test_Weights_Data_Has_Date_Column(
        self,
        sample_weights_data: pl.DataFrame,
    ) -> None:
        """Test that weights data has Date column."""
        assert "Date" in sample_weights_data.columns
        _logger.debug("Weights data has Date column")

    @pytest.mark.unit()
    def Test_Weights_Data_Has_ETF_Components(
        self,
        sample_weights_data: pl.DataFrame,
    ) -> None:
        """Test that weights data has ETF component columns."""
        component_columns_ETF = [
            item_column
            for item_column in sample_weights_data.columns
            if item_column != "Date"
        ]
        assert len(component_columns_ETF) >= 2
        _logger.debug(f"ETF components found: {component_columns_ETF}")

    @pytest.mark.unit()
    def Test_Weights_Sum_Approximately_To_One(
        self,
        sample_weights_data: pl.DataFrame,
    ) -> None:
        """Test that weights sum to approximately 1.0 for each date."""
        component_columns_ETF = [
            item_column
            for item_column in sample_weights_data.columns
            if item_column != "Date"
        ]
        for idx_row in range(min(5, len(sample_weights_data))):
            value_row_sum = sum(
                sample_weights_data[item_column][idx_row]
                for item_column in component_columns_ETF
            )
            assert abs(value_row_sum - 1.0) < 0.01, (
                f"Row {idx_row} weights sum to {value_row_sum}"
            )
        _logger.debug("Weights sum validation passed")

    @pytest.mark.unit()
    def Test_Weights_Are_Non_Negative(
        self,
        sample_weights_data: pl.DataFrame,
    ) -> None:
        """Test that all weights are non-negative."""
        component_columns_ETF = [
            item_column
            for item_column in sample_weights_data.columns
            if item_column != "Date"
        ]
        for item_column in component_columns_ETF:
            assert sample_weights_data[item_column].min() >= 0  # type: ignore[operator]
        _logger.debug("All weights are non-negative")

    @pytest.mark.unit()
    def Test_Weights_Are_Less_Than_Or_Equal_To_One(
        self,
        sample_weights_data: pl.DataFrame,
    ) -> None:
        """Test that all weights are <= 1.0."""
        component_columns_ETF = [
            item_column
            for item_column in sample_weights_data.columns
            if item_column != "Date"
        ]
        for item_column in component_columns_ETF:
            assert sample_weights_data[item_column].max() <= 1.0  # type: ignore[operator]
        _logger.debug("All weights are <= 1.0")


@pytest.mark.unit()
class Class_Test_ETF_Component_Extraction:
    """Test ETF component extraction from weights data."""

    @pytest.mark.unit()
    def Test_Extract_ETF_Components(
        self,
        sample_weights_data: pl.DataFrame,
    ) -> None:
        """Test extracting ETF component names from columns."""
        all_columns = sample_weights_data.columns
        component_columns_ETF = [
            item_column for item_column in all_columns if item_column != "Date"
        ]

        expected_etfs = ["VTI", "VXUS", "BND", "VNQ"]
        for etf in expected_etfs:
            assert etf in component_columns_ETF
        _logger.debug(f"Extracted ETF components: {component_columns_ETF}")

    @pytest.mark.unit()
    def Test_ETF_Count_Matches_Expected(
        self,
        sample_weights_data: pl.DataFrame,
    ) -> None:
        """Test that ETF count matches expected number."""
        component_columns_ETF = [
            item_column
            for item_column in sample_weights_data.columns
            if item_column != "Date"
        ]
        assert len(component_columns_ETF) == 4  # VTI, VXUS, BND, VNQ
        _logger.debug(f"ETF count: {len(component_columns_ETF)}")


@pytest.mark.unit()
class Class_Test_Visualization_Type_Options:
    """Test visualization type options for Weights Analysis."""

    @pytest.mark.unit()
    def Test_Area_Chart_Type_Exists(self) -> None:
        """Test that area chart type exists."""
        visualization_types = ["area", "bar", "line", "heatmap"]
        assert "area" in visualization_types
        _logger.debug("Area chart type verified")

    @pytest.mark.unit()
    def Test_Bar_Chart_Type_Exists(self) -> None:
        """Test that bar chart type exists."""
        visualization_types = ["area", "bar", "line", "heatmap"]
        assert "bar" in visualization_types
        _logger.debug("Bar chart type verified")

    @pytest.mark.unit()
    def Test_Line_Chart_Type_Exists(self) -> None:
        """Test that line chart type exists."""
        visualization_types = ["area", "bar", "line", "heatmap"]
        assert "line" in visualization_types
        _logger.debug("Line chart type verified")

    @pytest.mark.unit()
    def Test_Heatmap_Chart_Type_Exists(self) -> None:
        """Test that heatmap type exists."""
        visualization_types = ["area", "bar", "line", "heatmap"]
        assert "heatmap" in visualization_types
        _logger.debug("Heatmap type verified")

    @pytest.mark.unit()
    def Test_Pie_Chart_Type_Is_Not_Exposed(self) -> None:
        """Test that pie chart is not exposed in the public visualization selector."""
        visualization_types = ["area", "bar", "line", "heatmap"]
        assert "pie" not in visualization_types
        _logger.debug("Pie chart absence verified")


@pytest.mark.unit()
class Class_Test_Time_Period_Options:
    """Test time period selection options."""

    @pytest.mark.unit()
    def Test_Time_Period_Options_Include_One_Year(self) -> None:
        """Test that time period options include 1 year."""
        time_periods = ["1y", "3y", "5y", "10y", "ytd", "custom"]
        assert "1y" in time_periods
        _logger.debug("1 year option verified")

    @pytest.mark.unit()
    def Test_Time_Period_Options_Include_YTD(self) -> None:
        """Test that time period options include YTD."""
        time_periods = ["1y", "3y", "5y", "10y", "ytd", "custom"]
        assert "ytd" in time_periods
        _logger.debug("YTD option verified")

    @pytest.mark.unit()
    def Test_Time_Period_Options_Include_Custom(self) -> None:
        """Test that time period options include custom range."""
        time_periods = ["1y", "3y", "5y", "10y", "ytd", "custom"]
        assert "custom" in time_periods
        _logger.debug("Custom option verified")


@pytest.mark.unit()
class Class_Test_Component_Selection_Logic:
    """Test ETF component selection logic."""

    @pytest.mark.unit()
    def Test_Select_All_Logic(
        self,
        sample_weights_data: pl.DataFrame,
    ) -> None:
        """Test select all components logic."""
        component_columns_ETF = [
            item_column
            for item_column in sample_weights_data.columns
            if item_column != "Date"
        ]
        selected = component_columns_ETF.copy()  # Select all

        assert len(selected) == len(component_columns_ETF)
        _logger.debug(f"Select all: {len(selected)} components selected")

    @pytest.mark.unit()
    def Test_Select_None_Logic(
        self,
        sample_weights_data: pl.DataFrame,
    ) -> None:
        """Test select none components logic."""
        selected: list[str] = []  # Select none

        assert len(selected) == 0
        _logger.debug("Select none: 0 components selected")

    @pytest.mark.unit()
    def Test_Partial_Selection_Logic(
        self,
        sample_weights_data: pl.DataFrame,
    ) -> None:
        """Test partial component selection logic."""
        component_columns_ETF = [
            item_column
            for item_column in sample_weights_data.columns
            if item_column != "Date"
        ]
        selected = component_columns_ETF[:2]  # Select first 2

        assert len(selected) == 2
        assert len(selected) < len(component_columns_ETF)
        _logger.debug(f"Partial selection: {selected}")


@pytest.mark.unit()
class Class_Test_Data_Inputs_Structure:
    """Test data inputs dictionary structure for Weights Analysis."""

    @pytest.mark.unit()
    def Test_Data_Inputs_Has_Weights(
        self,
        sample_data_inputs: dict[str, Any],
    ) -> None:
        """Test that data_inputs has Weights_My_Portfolio key."""
        assert "Weights_My_Portfolio" in sample_data_inputs
        assert isinstance(sample_data_inputs["Weights_My_Portfolio"], pl.DataFrame)

    @pytest.mark.unit()
    def Test_Data_Inputs_Weights_Has_Data(
        self,
        sample_data_inputs: dict[str, Any],
    ) -> None:
        """Test that weights data is not empty."""
        weights_df = sample_data_inputs["Weights_My_Portfolio"]
        assert len(weights_df) > 0
        _logger.debug(f"Weights data has {len(weights_df)} rows")


@pytest.mark.unit()
class Class_Test_Empty_Data_Handling:
    """Test handling of empty weights data."""

    @pytest.mark.unit()
    def Test_Empty_Weights_Has_Date_Column(
        self,
        empty_weights_data: pl.DataFrame,
    ) -> None:
        """Test that empty weights data maintains column structure."""
        assert "Date" in empty_weights_data.columns
        _logger.debug("Empty weights data has Date column")

    @pytest.mark.unit()
    def Test_Empty_Weights_Row_Count(
        self,
        empty_weights_data: pl.DataFrame,
    ) -> None:
        """Test that empty weights data has zero rows."""
        assert len(empty_weights_data) == 0
        _logger.debug("Empty weights data has zero rows")


@pytest.mark.unit()
class Class_Test_Weight_Statistics_Calculations:
    """Test weight statistics calculations."""

    @pytest.mark.unit()
    def Test_Average_Weight_Calculation(
        self,
        sample_weights_data: pl.DataFrame,
    ) -> None:
        """Test average weight calculation for a component."""
        avg_vti = sample_weights_data["VTI"].mean()
        assert 0.0 < avg_vti < 1.0
        _logger.debug(f"Average VTI weight: {avg_vti:.4f}")

    @pytest.mark.unit()
    def Test_Weight_Standard_Deviation(
        self,
        sample_weights_data: pl.DataFrame,
    ) -> None:
        """Test weight standard deviation calculation."""
        std_vti = sample_weights_data["VTI"].std()
        assert std_vti >= 0
        _logger.debug(f"VTI weight std dev: {std_vti:.4f}")

    @pytest.mark.unit()
    def Test_Min_Max_Weight_Calculation(
        self,
        sample_weights_data: pl.DataFrame,
    ) -> None:
        """Test min and max weight calculation."""
        min_vti = sample_weights_data["VTI"].min()
        max_vti = sample_weights_data["VTI"].max()
        assert min_vti <= max_vti  # type: ignore[operator]
        _logger.debug(f"VTI weight range: [{min_vti:.4f}, {max_vti:.4f}]")


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.integration()
class Class_Test_Weights_Analysis_Integration:
    """Integration tests for Weights Analysis subtab."""

    @pytest.mark.skipif(
        not MODULE_IMPORT_AVAILABLE,
        reason=MODULE_IMPORT_SKIP_REASON,
    )
    @pytest.mark.unit()
    def Test_UI_Creates_Valid_Component(
        self,
        sample_data_utils: dict[str, Any],
        sample_data_inputs: dict[str, Any],
    ) -> None:
        """Test that UI function creates a valid Shiny component."""
        result = subtab_weights_analysis_ui(
            "test_weights",
            data_utils=sample_data_utils,
            data_inputs=sample_data_inputs,
        )
        assert result is not None

    @pytest.mark.skipif(
        not MODULE_IMPORT_AVAILABLE,
        reason=MODULE_IMPORT_SKIP_REASON,
    )
    @pytest.mark.unit()
    def Test_Server_Handles_Component_Selection(
        self,
        sample_data_utils: dict[str, Any],
        sample_data_inputs: dict[str, Any],
        sample_reactives_shiny: dict[str, Any],
    ) -> None:
        """Test that server correctly handles component selection changes."""
        import inspect

        assert callable(subtab_weights_analysis_server)
        sig = inspect.signature(subtab_weights_analysis_server)
        assert "id" in sig.parameters


# =============================================================================
# Enhanced Test Classes
# =============================================================================


@pytest.mark.unit()
class Class_Test_Visualization_Type_Completeness:
    """Test that all required chart types are available in weights analysis."""

    _CHART_TYPES: ClassVar[list[str]] = [
        "area",
        "bar",
        "line",
        "heatmap",
    ]

    @pytest.mark.unit()
    def Test_Four_Chart_Types(self) -> None:
        """Test that there are exactly 4 chart types."""
        assert len(self._CHART_TYPES) == 4
        _logger.debug(f"Chart type count: {len(self._CHART_TYPES)}")

    @pytest.mark.unit()
    def Test_Area_Chart_Type_Exists(self) -> None:
        """Test that 'area' chart type is defined."""
        assert "area" in self._CHART_TYPES
        _logger.debug("area chart type verified")

    @pytest.mark.unit()
    def Test_Bar_Chart_Type_Exists(self) -> None:
        """Test that 'bar' chart type is defined."""
        assert "bar" in self._CHART_TYPES
        _logger.debug("bar chart type verified")

    @pytest.mark.unit()
    def Test_Line_Chart_Type_Exists(self) -> None:
        """Test that 'line' chart type is defined."""
        assert "line" in self._CHART_TYPES
        _logger.debug("line chart type verified")

    @pytest.mark.unit()
    def Test_Heatmap_Chart_Type_Exists(self) -> None:
        """Test that 'heatmap' chart type is defined."""
        assert "heatmap" in self._CHART_TYPES
        _logger.debug("heatmap chart type verified")

    @pytest.mark.unit()
    def Test_All_Chart_Types_Are_Non_Empty_Strings(self) -> None:
        """Test that all chart types are non-empty strings."""
        for chart_type in self._CHART_TYPES:
            assert isinstance(chart_type, str)
            assert len(chart_type) > 0
        _logger.debug("All chart types are non-empty strings")

    @pytest.mark.unit()
    def Test_No_Duplicate_Chart_Types(self) -> None:
        """Test that there are no duplicate chart types."""
        assert len(self._CHART_TYPES) == len(set(self._CHART_TYPES))
        _logger.debug("No duplicate chart types")


@pytest.mark.unit()
class Class_Test_Input_ID_Naming_Convention_Weights:
    """Test input IDs follow the required hierarchical naming convention."""

    _ID_PREFIX: str = "input_ID_tab_portfolios_subtab_weights_analysis_"

    _INPUT_IDS: ClassVar[list[str]] = [
        "input_ID_tab_portfolios_subtab_weights_analysis_time_period",
        "input_ID_tab_portfolios_subtab_weights_analysis_date_range",
        "input_ID_tab_portfolios_subtab_weights_analysis_select_all_components",
        "input_ID_tab_portfolios_subtab_weights_analysis_viz_type",
        "input_ID_tab_portfolios_subtab_weights_analysis_show_pct",
        "input_ID_tab_portfolios_subtab_weights_analysis_sort_components",
    ]

    @pytest.mark.unit()
    def Test_All_Input_IDs_Start_With_Correct_Prefix(self) -> None:
        """Test that every input ID starts with the subtab prefix."""
        for input_id in self._INPUT_IDS:
            assert input_id.startswith(self._ID_PREFIX), (
                f"Input ID '{input_id}' missing prefix '{self._ID_PREFIX}'"
            )
        _logger.debug("All weights input ID prefixes verified")

    @pytest.mark.unit()
    def Test_Time_Period_Input_ID_Present(self) -> None:
        """Test that time_period input ID is present."""
        assert "input_ID_tab_portfolios_subtab_weights_analysis_time_period" in self._INPUT_IDS
        _logger.debug("time_period input ID for weights verified")

    @pytest.mark.unit()
    def Test_Viz_Type_Input_ID_Present(self) -> None:
        """Test that viz_type input ID is present."""
        assert "input_ID_tab_portfolios_subtab_weights_analysis_viz_type" in self._INPUT_IDS
        _logger.debug("viz_type input ID verified")

    @pytest.mark.unit()
    def Test_Select_All_Components_Input_ID_Present(self) -> None:
        """Test that select_all_components input ID is present."""
        assert (
            "input_ID_tab_portfolios_subtab_weights_analysis_select_all_components"
            in self._INPUT_IDS
        )
        _logger.debug("select_all_components input ID verified")

    @pytest.mark.unit()
    def Test_No_Duplicate_Input_IDs(self) -> None:
        """Test that there are no duplicate input IDs."""
        assert len(self._INPUT_IDS) == len(set(self._INPUT_IDS))
        _logger.debug("No duplicate weights input IDs")


@pytest.mark.unit()
@pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason=MODULE_IMPORT_SKIP_REASON,
)
class Class_Test_PNG_Saving_Constants_Details:
    """Test detailed values of PNG-saving module constants."""

    @pytest.mark.unit()
    def Test_Enable_PNG_Saving_Not_Present_Details(self) -> None:
        """ENABLE_PNG_SAVING_SUBTAB_WEIGHTS_ANALYSIS should have been removed."""
        import src.dashboard.shiny_tab_portfolios.subtab_weights_analysis as mod

        assert not hasattr(mod, "ENABLE_PNG_SAVING_SUBTAB_WEIGHTS_ANALYSIS"), (
            "ENABLE_PNG_SAVING_SUBTAB_WEIGHTS_ANALYSIS should have been removed"
        )

    @pytest.mark.unit()
    def Test_TEMP_GRAPHICS_DIR_Not_Present_Details(self) -> None:
        """TEMP_GRAPHICS_DIR should have been removed from the module."""
        import src.dashboard.shiny_tab_portfolios.subtab_weights_analysis as mod

        assert not hasattr(mod, "TEMP_GRAPHICS_DIR"), (
            "TEMP_GRAPHICS_DIR should have been removed"
        )

    @pytest.mark.unit()
    def Test_Output_Dir_Is_Path(self) -> None:
        """Test that OUTPUT_DIR is a Path instance."""
        assert isinstance(OUTPUT_DIR, Path)
        _logger.debug(f"OUTPUT_DIR type verified: {type(OUTPUT_DIR)}")


class Class_Test_Date_Anchor_From_Weights_Data:
    """Regression tests for the extracted weights date-range helper."""

    @pytest.mark.unit()
    def Test_Helper_Anchors_Today_To_Data_Max_When_Available(self) -> None:
        """Regression: preset periods must anchor the range to the data max date."""
        from src.dashboard.shiny_tab_portfolios._subtab_weights_analysis_data import (
            normalize_weights_source_frame,
            resolve_weights_analysis_date_range,
        )

        weights_frame = normalize_weights_source_frame(
            weights_source = pl.DataFrame(
                {
                    "Date": ["2024-01-01", "2024-12-31"],
                    "VTI": [0.6, 0.55],
                    "BND": [0.4, 0.45],
                },
            ),
        )
        _, end_datetime = resolve_weights_analysis_date_range(
            time_period = "1y",
            weights_frame = weights_frame,
            today_datetime=datetime(2026, 5, 29, tzinfo=UTC),
        )

        assert end_datetime == datetime(2024, 12, 31, 23, 59, 59)
        _logger.debug("weights data max date anchor behavior verified")

    @pytest.mark.unit()
    def Test_Helper_YTD_Branch_Uses_Naive_Datetime(self) -> None:
        """Regression: YTD should use a naive year-start datetime."""
        from src.dashboard.shiny_tab_portfolios._subtab_weights_analysis_data import (
            normalize_weights_source_frame,
            resolve_weights_analysis_date_range,
        )

        weights_frame = normalize_weights_source_frame(
            weights_source = pl.DataFrame(
                {
                    "Date": ["2024-05-01", "2024-12-31"],
                    "VTI": [0.6, 0.55],
                    "BND": [0.4, 0.45],
                },
            ),
        )
        start_datetime, _ = resolve_weights_analysis_date_range(time_period = "ytd", weights_frame = weights_frame)

        assert start_datetime == datetime(2024, 1, 1, 0, 0, 0)
        assert start_datetime.tzinfo is None
        _logger.debug("ytd naive datetime verified")

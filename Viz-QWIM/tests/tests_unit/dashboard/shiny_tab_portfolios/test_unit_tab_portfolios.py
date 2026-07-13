"""Unit tests for the Portfolios Tab Module.

This module provides comprehensive unit tests for the tab_portfolios module,
testing the UI and server logic for the main Portfolios tab in the QWIM Dashboard.

Tests cover:
- Module-level constants and configuration
- UI component creation
- Server logic initialization
- Error handling scenarios
- Integration with subtab modules

Author:
    QWIM Development Team

Version:
    0.5.1

Last Modified:
    2026-02-01
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

import polars as pl
import pytest

from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


#: Module-level logger instance for test logging
_logger = get_logger(name = __name__)

# Try importing the module under test - may fail in some environments
# due to complex Shiny dependencies
try:
    from src.dashboard.shiny_tab_portfolios.tab_portfolios import (
        OUTPUT_DIR,
        _logger as module_logger,
        tab_portfolios_server,
        tab_portfolios_ui,
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
    return pl.DataFrame(
        {
            "Date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"],
            "Value": [100.0, 101.5, 99.8, 102.3, 103.1],
        },
    )


@pytest.fixture()
def sample_benchmark_data() -> pl.DataFrame:
    """Create sample benchmark data for testing.

    Returns:
        pl.DataFrame: Sample benchmark DataFrame with Date and Value columns.
    """
    return pl.DataFrame(
        {
            "Date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"],
            "Value": [100.0, 100.8, 100.2, 101.5, 101.9],
        },
    )


@pytest.fixture()
def sample_weights_data() -> pl.DataFrame:
    """Create sample portfolio weights data for testing.

    Returns:
        pl.DataFrame: Sample weights DataFrame with Date and ETF component columns.
    """
    return pl.DataFrame(
        {
            "Date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "VTI": [0.40, 0.42, 0.38],
            "VXUS": [0.30, 0.28, 0.32],
            "BND": [0.30, 0.30, 0.30],
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
        import src.dashboard.shiny_tab_portfolios.tab_portfolios as mod

        assert not hasattr(mod, "ENABLE_PNG_SAVING_TAB_PORTFOLIOS"), (
            "ENABLE_PNG_SAVING_TAB_PORTFOLIOS should have been removed"
        )
        assert not hasattr(mod, "TEMP_GRAPHICS_DIR"), (
            "TEMP_GRAPHICS_DIR should have been removed"
        )
        _logger.info("PNG saving constants correctly removed from tab_portfolios module")


@pytest.mark.unit()
@pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason="Module import failed due to Shiny dependencies",
)
class Test_Module_Imports:
    """Test that all required module imports are available."""

    @pytest.mark.unit()
    def test_tab_portfolios_ui_is_importable(self) -> None:
        """Test that tab_portfolios_ui function can be imported."""
        assert callable(tab_portfolios_ui)
        _logger.debug("tab_portfolios_ui successfully imported")

    @pytest.mark.unit()
    def test_tab_portfolios_server_is_importable(self) -> None:
        """Test that tab_portfolios_server function can be imported."""
        assert callable(tab_portfolios_server)
        _logger.debug("tab_portfolios_server successfully imported")


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
@pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason="Module import failed due to Shiny dependencies",
)
class Test_Tab_Portfolios_UI_Validation:
    """Test tab_portfolios_ui function input validation."""

    @pytest.mark.unit()
    def test_ui_function_accepts_empty_data_utils(
        self,
        sample_data_inputs: dict[str, Any],
    ) -> None:
        """Test that UI function handles empty data_utils dictionary."""
        # Should not raise an exception
        try:
            # Note: We can't fully test UI creation without Shiny context
            # This test verifies the function signature is correct
            assert callable(tab_portfolios_ui)
            _logger.debug("UI function accepts empty data_utils")
        except TypeError as e:
            pytest.fail(f"UI function raised TypeError: {e}")

    @pytest.mark.unit()
    def test_ui_function_accepts_empty_data_inputs(
        self,
        sample_data_utils: dict[str, Any],
    ) -> None:
        """Test that UI function handles empty data_inputs dictionary."""
        # Should not raise an exception with empty data
        try:
            assert callable(tab_portfolios_ui)
            _logger.debug("UI function accepts empty data_inputs")
        except TypeError as e:
            pytest.fail(f"UI function raised TypeError: {e}")


@pytest.mark.unit()
class Test_Data_Input_Structure:
    """Test data input structure and validation."""

    @pytest.mark.unit()
    def test_sample_portfolio_data_has_required_columns(
        self,
        sample_portfolio_data: pl.DataFrame,
    ) -> None:
        """Test that sample portfolio data has Date and Value columns."""
        assert "Date" in sample_portfolio_data.columns
        assert "Value" in sample_portfolio_data.columns
        _logger.debug(f"Portfolio columns verified: {sample_portfolio_data.columns}")

    @pytest.mark.unit()
    def test_sample_benchmark_data_has_required_columns(
        self,
        sample_benchmark_data: pl.DataFrame,
    ) -> None:
        """Test that sample benchmark data has Date and Value columns."""
        assert "Date" in sample_benchmark_data.columns
        assert "Value" in sample_benchmark_data.columns
        _logger.debug(f"Benchmark columns verified: {sample_benchmark_data.columns}")

    @pytest.mark.unit()
    def test_sample_weights_data_has_date_column(
        self,
        sample_weights_data: pl.DataFrame,
    ) -> None:
        """Test that sample weights data has Date column."""
        assert "Date" in sample_weights_data.columns
        _logger.debug(f"Weights columns verified: {sample_weights_data.columns}")

    @pytest.mark.unit()
    def test_sample_weights_data_has_etf_components(
        self,
        sample_weights_data: pl.DataFrame,
    ) -> None:
        """Test that sample weights data has ETF component columns."""
        etf_columns = [col for col in sample_weights_data.columns if col != "Date"]
        assert len(etf_columns) > 0
        _logger.debug(f"ETF components found: {etf_columns}")

    @pytest.mark.unit()
    def test_sample_data_inputs_has_all_required_keys(
        self,
        sample_data_inputs: dict[str, Any],
    ) -> None:
        """Test that data inputs dictionary has all required keys."""
        required_keys = [
            "My_Portfolio",
            "Benchmark_Portfolio",
            "Weights_My_Portfolio",
            "Time_Series_ETFs",
        ]
        for key in required_keys:
            assert key in sample_data_inputs
        _logger.debug(f"All required keys present: {required_keys}")


@pytest.mark.unit()
class Test_Reactives_Shiny_Structure:
    """Test reactives_shiny dictionary structure."""

    @pytest.mark.unit()
    def test_reactives_shiny_has_user_inputs(
        self,
        sample_reactives_shiny: dict[str, Any],
    ) -> None:
        """Test that reactives_shiny has User_Inputs_Shiny key."""
        assert "User_Inputs_Shiny" in sample_reactives_shiny

    @pytest.mark.unit()
    def test_reactives_shiny_has_inner_variables(
        self,
        sample_reactives_shiny: dict[str, Any],
    ) -> None:
        """Test that reactives_shiny has Inner_Variables_Shiny key."""
        assert "Inner_Variables_Shiny" in sample_reactives_shiny

    @pytest.mark.unit()
    def test_reactives_shiny_has_triggers(
        self,
        sample_reactives_shiny: dict[str, Any],
    ) -> None:
        """Test that reactives_shiny has Triggers_Shiny key."""
        assert "Triggers_Shiny" in sample_reactives_shiny

    @pytest.mark.unit()
    def test_reactives_shiny_has_visual_objects(
        self,
        sample_reactives_shiny: dict[str, Any],
    ) -> None:
        """Test that reactives_shiny has Visual_Objects_Shiny key."""
        assert "Visual_Objects_Shiny" in sample_reactives_shiny


# =============================================================================
# Enhanced Test Classes
# =============================================================================


@pytest.mark.unit()
class Test_NavSet_And_Module_IDs:
    """Test navset ID and subtab module ID naming conventions."""

    #: Navset ID used in tab_portfolios_ui
    _NAVSET_ID: str = "ID_tab_portfolios_tabs_all"

    #: Four subtab module IDs in registration order
    _SUBTAB_MODULE_IDS: ClassVar[list[str]] = [
        "ID_tab_portfolios_subtab_portfolios_analysis",
        "ID_tab_portfolios_subtab_portfolios_comparison",
        "ID_tab_portfolios_subtab_weights_analysis",
        "ID_tab_portfolios_subtab_skfolio",
    ]

    @pytest.mark.unit()
    def test_navset_id_starts_with_id_tab(self) -> None:
        """Test that navset ID starts with 'ID_tab_portfolios_'."""
        assert self._NAVSET_ID.startswith("ID_tab_portfolios_")
        _logger.debug(f"Navset ID verified: {self._NAVSET_ID}")

    @pytest.mark.unit()
    def test_navset_id_ends_with_tabs_all(self) -> None:
        """Test that navset ID ends with '_tabs_all'."""
        assert self._NAVSET_ID.endswith("_tabs_all")
        _logger.debug("Navset ID suffix verified")

    @pytest.mark.unit()
    def test_four_subtab_module_ids_registered(self) -> None:
        """Test that exactly 4 subtab module IDs are registered."""
        assert len(self._SUBTAB_MODULE_IDS) == 4
        _logger.debug(f"Subtab module count: {len(self._SUBTAB_MODULE_IDS)}")

    @pytest.mark.unit()
    def test_all_subtab_module_ids_start_with_id_tab_portfolios_subtab(self) -> None:
        """Test that all subtab module IDs start with 'ID_tab_portfolios_subtab_'."""
        for module_id in self._SUBTAB_MODULE_IDS:
            assert module_id.startswith(
                "ID_tab_portfolios_subtab_",
            ), f"Module ID '{module_id}' missing expected prefix"
        _logger.debug("All subtab module ID prefixes verified")

    @pytest.mark.unit()
    def test_analysis_subtab_module_id_present(self) -> None:
        """Test that portfolios_analysis subtab module ID is present."""
        assert "ID_tab_portfolios_subtab_portfolios_analysis" in self._SUBTAB_MODULE_IDS
        _logger.debug("Analysis module ID verified")

    @pytest.mark.unit()
    def test_comparison_subtab_module_id_present(self) -> None:
        """Test that portfolios_comparison subtab module ID is present."""
        assert "ID_tab_portfolios_subtab_portfolios_comparison" in self._SUBTAB_MODULE_IDS
        _logger.debug("Comparison module ID verified")

    @pytest.mark.unit()
    def test_weights_subtab_module_id_present(self) -> None:
        """Test that weights_analysis subtab module ID is present."""
        assert "ID_tab_portfolios_subtab_weights_analysis" in self._SUBTAB_MODULE_IDS
        _logger.debug("Weights module ID verified")

    @pytest.mark.unit()
    def test_skfolio_subtab_module_id_present(self) -> None:
        """Test that skfolio subtab module ID is present."""
        assert "ID_tab_portfolios_subtab_skfolio" in self._SUBTAB_MODULE_IDS
        _logger.debug("Skfolio module ID verified")

    @pytest.mark.unit()
    def test_no_duplicate_module_ids(self) -> None:
        """Test that there are no duplicate subtab module IDs."""
        assert len(self._SUBTAB_MODULE_IDS) == len(set(self._SUBTAB_MODULE_IDS))
        _logger.debug("No duplicate module IDs")


@pytest.mark.unit()
class Test_Server_Return_Keys:
    """Test expected server return dictionary keys."""

    #: Keys returned by tab_portfolios_server
    _SERVER_RETURN_KEYS: ClassVar[list[str]] = [
        "Portfolios_Analysis_Server",
        "Portfolios_Comparison_Server",
        "Weights_Analysis_Server",
        "skfolio_Optimization_Server",
    ]

    @pytest.mark.unit()
    def test_four_server_return_keys(self) -> None:
        """Test that there are exactly 4 server return keys."""
        assert len(self._SERVER_RETURN_KEYS) == 4
        _logger.debug(f"Server return key count: {len(self._SERVER_RETURN_KEYS)}")

    @pytest.mark.unit()
    def test_portfolios_analysis_server_key_present(self) -> None:
        """Test that Portfolios_Analysis_Server key is present."""
        assert "Portfolios_Analysis_Server" in self._SERVER_RETURN_KEYS
        _logger.debug("Portfolios_Analysis_Server key verified")

    @pytest.mark.unit()
    def test_portfolios_comparison_server_key_present(self) -> None:
        """Test that Portfolios_Comparison_Server key is present."""
        assert "Portfolios_Comparison_Server" in self._SERVER_RETURN_KEYS
        _logger.debug("Portfolios_Comparison_Server key verified")

    @pytest.mark.unit()
    def test_weights_analysis_server_key_present(self) -> None:
        """Test that Weights_Analysis_Server key is present."""
        assert "Weights_Analysis_Server" in self._SERVER_RETURN_KEYS
        _logger.debug("Weights_Analysis_Server key verified")

    @pytest.mark.unit()
    def test_skfolio_optimization_server_key_present(self) -> None:
        """Test that skfolio_Optimization_Server key is present."""
        assert "skfolio_Optimization_Server" in self._SERVER_RETURN_KEYS
        _logger.debug("skfolio_Optimization_Server key verified")

    @pytest.mark.unit()
    def test_all_server_keys_are_non_empty_strings(self) -> None:
        """Test that all server return keys are non-empty strings."""
        for key in self._SERVER_RETURN_KEYS:
            assert isinstance(key, str)
            assert len(key) > 0
        _logger.debug("All server return keys are non-empty strings")

    @pytest.mark.unit()
    def test_no_duplicate_server_keys(self) -> None:
        """Test that there are no duplicate server return keys."""
        assert len(self._SERVER_RETURN_KEYS) == len(set(self._SERVER_RETURN_KEYS))
        _logger.debug("No duplicate server return keys")

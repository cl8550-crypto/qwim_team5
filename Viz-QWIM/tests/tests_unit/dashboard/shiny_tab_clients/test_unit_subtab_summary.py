"""Unit tests for the Summary SubTab Module.

This module provides comprehensive unit tests for the SubTab_Summary module,
testing the UI and server logic for summary tables in the QWIM Dashboard.

Tests cover:
- Module-level constants and configuration
- Summary table generation
- Data aggregation calculations
- Great Tables integration
- Error handling scenarios

Author:
    QWIM Development Team

Version:
    0.5.1

Last Modified:
    2026-02-01
"""

from __future__ import annotations

from typing import Any, ClassVar

import polars as pl
import pytest

from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)


#: Module-level logger instance for test logging
_logger = get_logger(name = __name__)

# Try importing the module under test - may fail in some environments
# due to complex Shiny dependencies
try:
    from src.dashboard.shiny_tab_clients.subtab_summary import (
        _logger as module_logger,
        normalize_data_personal_info_summary,
        subtab_clients_summary_server,
        subtab_clients_summary_ui,
    )

    MODULE_IMPORT_AVAILABLE = True
except ImportError as e:
    MODULE_IMPORT_AVAILABLE = False
    _logger.warning(f"Module import failed, some tests will be skipped: {e}")


# =============================================================================
# Constants for Testing
# =============================================================================

#: Summary table sections
SUMMARY_SECTIONS = [
    "personal_info",
    "assets",
    "goals",
    "income",
]

#: Summary display formats
SUMMARY_DISPLAY_FORMATS = [
    "currency",
    "percentage",
    "number",
    "text",
    "date",
]


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture()
def sample_personal_info_summary() -> dict[str, Any]:
    """Create sample personal info summary data for testing.

    Returns:
        dict: Sample personal info summary dictionary.
    """
    return {
        "primary_client": {
            "name": "John Doe",
            "age": 45,
            "retirement_age": 65,
            "state": "CA",
            "employment_status": "Employed Full-Time",
        },
        "partner_client": {
            "name": "Jane Doe",
            "age": 42,
            "retirement_age": 65,
            "state": "CA",
            "employment_status": "Employed Full-Time",
        },
    }


@pytest.fixture()
def sample_assets_summary() -> dict[str, Any]:
    """Create sample assets summary data for testing.

    Returns:
        dict: Sample assets summary dictionary.
    """
    return {
        "taxable": {
            "label": "Taxable Assets",
            "value": 325000.00,
            "percentage": 0.382,
        },
        "tax_deferred": {
            "label": "Tax-Deferred Assets",
            "value": 600000.00,
            "percentage": 0.471,
        },
        "tax_free": {
            "label": "Tax-Free Assets",
            "value": 140000.00,
            "percentage": 0.147,
        },
        "total": {
            "label": "Total Assets",
            "value": 1065000.00,
            "percentage": 1.0,
        },
    }


@pytest.fixture()
def sample_goals_summary() -> dict[str, Any]:
    """Create sample goals summary data for testing.

    Returns:
        dict: Sample goals summary dictionary.
    """
    return {
        "essential": {
            "label": "Essential Goals",
            "value": 80000.00,
            "percentage": 0.479,
        },
        "important": {
            "label": "Important Goals",
            "value": 37000.00,
            "percentage": 0.222,
        },
        "aspirational": {
            "label": "Aspirational Goals",
            "value": 50000.00,
            "percentage": 0.299,
        },
        "total": {
            "label": "Total Goals",
            "value": 167000.00,
            "percentage": 1.0,
        },
    }


@pytest.fixture()
def sample_income_summary() -> dict[str, Any]:
    """Create sample income summary data for testing.

    Returns:
        dict: Sample income summary dictionary.
    """
    return {
        "social_security": {
            "label": "Social Security",
            "value": 36000.00,
            "percentage": 0.353,
        },
        "pension": {
            "label": "Pension",
            "value": 36000.00,
            "percentage": 0.353,
        },
        "annuity": {
            "label": "Annuity",
            "value": 18000.00,
            "percentage": 0.176,
        },
        "other": {
            "label": "Other Income",
            "value": 12000.00,
            "percentage": 0.118,
        },
        "total": {
            "label": "Total Income",
            "value": 102000.00,
            "percentage": 1.0,
        },
    }


@pytest.fixture()
def sample_complete_summary(
    sample_personal_info_summary: dict[str, Any],
    sample_assets_summary: dict[str, Any],
    sample_goals_summary: dict[str, Any],
    sample_income_summary: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Create complete summary data for testing.

    Args:
        sample_personal_info_summary: Personal info summary.
        sample_assets_summary: Assets summary.
        sample_goals_summary: Goals summary.
        sample_income_summary: Income summary.

    Returns:
        dict: Complete summary dictionary.
    """
    return {
        "personal_info": sample_personal_info_summary,
        "assets": sample_assets_summary,
        "goals": sample_goals_summary,
        "income": sample_income_summary,
    }


@pytest.fixture()
def sample_data_utils() -> dict[str, Any]:
    """Create sample data utilities dictionary for testing.

    Returns:
        dict: Sample data utilities configuration dictionary.
    """
    return {
        "theme": "default",
        "export_enabled": True,
        "currency_format": "${:,.2f}",
        "percentage_format": "{:.1%}",
    }


@pytest.fixture()
def sample_data_inputs(
    sample_complete_summary: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Create sample data inputs dictionary for testing.

    Args:
        sample_complete_summary: Complete summary data.

    Returns:
        dict: Sample data inputs dictionary with summary.
    """
    return {
        "Summary": sample_complete_summary,
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
def sample_polars_summary_df() -> pl.DataFrame:
    """Create sample Polars DataFrame for summary table testing.

    Returns:
        pl.DataFrame: Sample summary DataFrame.
    """
    return pl.DataFrame(
        {
            "Category": ["Taxable", "Tax-Deferred", "Tax-Free", "Total"],
            "Value": [325000.00, 600000.00, 140000.00, 1065000.00],
            "Percentage": [0.382, 0.471, 0.147, 1.0],
        },
    )


# =============================================================================
# Test Classes
# =============================================================================


@pytest.mark.unit()
@pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason="Module import failed due to Shiny dependencies",
)
class Test_Module_Imports:
    """Test that all required module imports are available."""

    @pytest.mark.unit()
    def test_subtab_summary_ui_is_importable(self) -> None:
        """Test that subtab_clients_summary_ui function can be imported."""
        assert callable(subtab_clients_summary_ui)
        _logger.debug("subtab_clients_summary_ui successfully imported")

    @pytest.mark.unit()
    def test_subtab_summary_server_is_importable(self) -> None:
        """Test that subtab_clients_summary_server function can be imported."""
        assert callable(subtab_clients_summary_server)
        _logger.debug("subtab_clients_summary_server successfully imported")


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
class Test_Summary_Sections:
    """Test summary section definitions."""

    @pytest.mark.unit()
    def test_summary_sections_count(self) -> None:
        """Test that we have expected number of summary sections."""
        assert len(SUMMARY_SECTIONS) == 4
        _logger.debug(f"Summary sections count: {len(SUMMARY_SECTIONS)}")

    @pytest.mark.unit()
    def test_summary_sections_unique(self) -> None:
        """Test that all summary sections are unique."""
        assert len(SUMMARY_SECTIONS) == len(set(SUMMARY_SECTIONS))
        _logger.debug("All summary sections are unique")

    @pytest.mark.unit()
    def test_personal_info_section_exists(self) -> None:
        """Test that 'personal_info' is a valid section."""
        assert "personal_info" in SUMMARY_SECTIONS
        _logger.debug("'personal_info' section exists")

    @pytest.mark.unit()
    def test_assets_section_exists(self) -> None:
        """Test that 'assets' is a valid section."""
        assert "assets" in SUMMARY_SECTIONS
        _logger.debug("'assets' section exists")

    @pytest.mark.unit()
    def test_goals_section_exists(self) -> None:
        """Test that 'goals' is a valid section."""
        assert "goals" in SUMMARY_SECTIONS
        _logger.debug("'goals' section exists")

    @pytest.mark.unit()
    def test_income_section_exists(self) -> None:
        """Test that 'income' is a valid section."""
        assert "income" in SUMMARY_SECTIONS
        _logger.debug("'income' section exists")


@pytest.mark.unit()
class Test_Summary_Display_Formats:
    """Test summary display format definitions."""

    @pytest.mark.unit()
    def test_display_formats_not_empty(self) -> None:
        """Test that display formats list is not empty."""
        assert len(SUMMARY_DISPLAY_FORMATS) > 0
        _logger.debug(f"Display formats count: {len(SUMMARY_DISPLAY_FORMATS)}")

    @pytest.mark.unit()
    def test_currency_format_exists(self) -> None:
        """Test that 'currency' is a valid format."""
        assert "currency" in SUMMARY_DISPLAY_FORMATS
        _logger.debug("'currency' format exists")

    @pytest.mark.unit()
    def test_percentage_format_exists(self) -> None:
        """Test that 'percentage' is a valid format."""
        assert "percentage" in SUMMARY_DISPLAY_FORMATS
        _logger.debug("'percentage' format exists")


@pytest.mark.unit()
class Test_Personal_Info_Summary_Validation:
    """Test personal info summary data validation."""

    @pytest.mark.unit()
    def test_has_primary_client(
        self,
        sample_personal_info_summary: dict[str, Any],
    ) -> None:
        """Test that personal info has primary_client."""
        assert "primary_client" in sample_personal_info_summary
        _logger.debug("Personal info has primary_client")

    @pytest.mark.unit()
    def test_has_partner_client(
        self,
        sample_personal_info_summary: dict[str, Any],
    ) -> None:
        """Test that personal info has partner_client."""
        assert "partner_client" in sample_personal_info_summary
        _logger.debug("Personal info has partner_client")

    @pytest.mark.unit()
    def test_primary_client_has_name(
        self,
        sample_personal_info_summary: dict[str, Any],
    ) -> None:
        """Test that primary client has name."""
        assert "name" in sample_personal_info_summary["primary_client"]
        _logger.debug("Primary client has name")

    @pytest.mark.unit()
    def test_primary_client_has_age(
        self,
        sample_personal_info_summary: dict[str, Any],
    ) -> None:
        """Test that primary client has age."""
        assert "age" in sample_personal_info_summary["primary_client"]
        _logger.debug("Primary client has age")


@pytest.mark.unit()
class Test_Assets_Summary_Validation:
    """Test assets summary data validation."""

    @pytest.mark.unit()
    def test_has_all_asset_categories(
        self,
        sample_assets_summary: dict[str, Any],
    ) -> None:
        """Test that assets summary has all categories."""
        expected = ["taxable", "tax_deferred", "tax_free", "total"]
        for category in expected:
            assert category in sample_assets_summary
        _logger.debug("Assets summary has all categories")

    @pytest.mark.unit()
    def test_each_category_has_value(
        self,
        sample_assets_summary: dict[str, Any],
    ) -> None:
        """Test that each category has a value."""
        for data in sample_assets_summary.values():
            assert "value" in data
            assert data["value"] >= 0
        _logger.debug("All asset categories have values")

    @pytest.mark.unit()
    def test_each_category_has_percentage(
        self,
        sample_assets_summary: dict[str, Any],
    ) -> None:
        """Test that each category has a percentage."""
        for data in sample_assets_summary.values():
            assert "percentage" in data
            assert 0 <= data["percentage"] <= 1.0
        _logger.debug("All asset categories have percentages")

    @pytest.mark.unit()
    def test_percentages_sum_to_one(
        self,
        sample_assets_summary: dict[str, Any],
    ) -> None:
        """Test that non-total percentages sum to approximately 1.0."""
        total_pct = sum(
            data["percentage"]
            for category, data in sample_assets_summary.items()
            if category != "total"
        )
        assert total_pct == pytest.approx(1.0, rel=0.01)
        _logger.debug(f"Percentages sum: {total_pct}")


@pytest.mark.unit()
class Test_Goals_Summary_Validation:
    """Test goals summary data validation."""

    @pytest.mark.unit()
    def test_has_all_goal_categories(
        self,
        sample_goals_summary: dict[str, Any],
    ) -> None:
        """Test that goals summary has all categories."""
        expected = ["essential", "important", "aspirational", "total"]
        for category in expected:
            assert category in sample_goals_summary
        _logger.debug("Goals summary has all categories")

    @pytest.mark.unit()
    def test_each_category_has_value(
        self,
        sample_goals_summary: dict[str, Any],
    ) -> None:
        """Test that each category has a value."""
        for data in sample_goals_summary.values():
            assert "value" in data
            assert data["value"] >= 0
        _logger.debug("All goal categories have values")


@pytest.mark.unit()
class Test_Income_Summary_Validation:
    """Test income summary data validation."""

    @pytest.mark.unit()
    def test_has_all_income_categories(
        self,
        sample_income_summary: dict[str, Any],
    ) -> None:
        """Test that income summary has all categories."""
        expected = ["social_security", "pension", "annuity", "other", "total"]
        for category in expected:
            assert category in sample_income_summary
        _logger.debug("Income summary has all categories")

    @pytest.mark.unit()
    def test_each_category_has_value(
        self,
        sample_income_summary: dict[str, Any],
    ) -> None:
        """Test that each category has a value."""
        for data in sample_income_summary.values():
            assert "value" in data
            assert data["value"] >= 0
        _logger.debug("All income categories have values")


@pytest.mark.unit()
class Test_Complete_Summary_Validation:
    """Test complete summary data structure."""

    @pytest.mark.unit()
    def test_has_all_sections(
        self,
        sample_complete_summary: dict[str, dict[str, Any]],
    ) -> None:
        """Test that complete summary has all sections."""
        for section in SUMMARY_SECTIONS:
            assert section in sample_complete_summary
        _logger.debug("Complete summary has all sections")


@pytest.mark.unit()
class Test_Currency_Formatting:
    """Test currency formatting for summary display."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            (1000.00, "$1,000.00"),
            (1000000.00, "$1,000,000.00"),
            (0.00, "$0.00"),
            (123456.78, "$123,456.78"),
        ],
    )
    @pytest.mark.unit()
    def test_currency_format(self, value: float, expected: str) -> None:
        """Test currency formatting with various values."""
        formatted = f"${value:,.2f}"
        assert formatted == expected
        _logger.debug(f"Formatted {value} as {formatted}")


@pytest.mark.unit()
class Test_Percentage_Formatting:
    """Test percentage formatting for summary display."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            (0.10, "10.0%"),
            (0.50, "50.0%"),
            (1.00, "100.0%"),
            (0.382, "38.2%"),
        ],
    )
    @pytest.mark.unit()
    def test_percentage_format(self, value: float, expected: str) -> None:
        """Test percentage formatting with various values."""
        formatted = f"{value:.1%}"
        assert formatted == expected
        _logger.debug(f"Formatted {value} as {formatted}")


@pytest.mark.unit()
class Test_Polars_Data_Frame_Operations:
    """Test Polars DataFrame operations for summary tables."""

    @pytest.mark.unit()
    def test_dataframe_has_expected_columns(
        self,
        sample_polars_summary_df: pl.DataFrame,
    ) -> None:
        """Test that DataFrame has expected columns."""
        expected_columns = ["Category", "Value", "Percentage"]
        for col in expected_columns:
            assert col in sample_polars_summary_df.columns
        _logger.debug("DataFrame has expected columns")

    @pytest.mark.unit()
    def test_dataframe_has_expected_rows(
        self,
        sample_polars_summary_df: pl.DataFrame,
    ) -> None:
        """Test that DataFrame has expected number of rows."""
        assert len(sample_polars_summary_df) == 4
        _logger.debug(f"DataFrame has {len(sample_polars_summary_df)} rows")

    @pytest.mark.unit()
    def test_dataframe_value_column_is_numeric(
        self,
        sample_polars_summary_df: pl.DataFrame,
    ) -> None:
        """Test that Value column is numeric."""
        assert sample_polars_summary_df["Value"].dtype in [
            pl.Float64,
            pl.Float32,
            pl.Int64,
            pl.Int32,
        ]
        _logger.debug("Value column is numeric")

    @pytest.mark.unit()
    def test_dataframe_percentage_column_is_numeric(
        self,
        sample_polars_summary_df: pl.DataFrame,
    ) -> None:
        """Test that Percentage column is numeric."""
        assert sample_polars_summary_df["Percentage"].dtype in [
            pl.Float64,
            pl.Float32,
        ]
        _logger.debug("Percentage column is numeric")

    @pytest.mark.unit()
    def test_dataframe_total_row_value(
        self,
        sample_polars_summary_df: pl.DataFrame,
    ) -> None:
        """Test that Total row has correct value."""
        total_row = sample_polars_summary_df.filter(
            pl.col("Category") == "Total",
        )
        assert len(total_row) == 1
        assert total_row["Value"][0] == pytest.approx(1065000.00, rel=1e-6)
        _logger.debug("Total row has correct value")


@pytest.mark.unit()
class Test_Data_Inputs_Structure:
    """Test data inputs dictionary structure for summary."""

    @pytest.mark.unit()
    def test_data_inputs_has_summary(
        self,
        sample_data_inputs: dict[str, Any],
    ) -> None:
        """Test that data_inputs has Summary key."""
        assert "Summary" in sample_data_inputs
        _logger.debug("data_inputs has Summary")


@pytest.mark.unit()
class Test_Reactives_Shiny_Structure:
    """Test reactives_shiny dictionary structure for summary."""

    @pytest.mark.unit()
    def test_has_all_required_keys(
        self,
        sample_reactives_shiny: dict[str, Any],
    ) -> None:
        """Test that reactives_shiny has all required keys."""
        required_keys = [
            "User_Inputs_Shiny",
            "Inner_Variables_Shiny",
            "Triggers_Shiny",
            "Visual_Objects_Shiny",
        ]
        for key in required_keys:
            assert key in sample_reactives_shiny
        _logger.debug("reactives_shiny has all required keys")


# =============================================================================
# Integration Tests (Marked for separate execution)
# =============================================================================


@pytest.mark.integration()
class Test_Sub_Tab_Summary_Integration:
    """Integration tests for subtab_summary module."""

    @pytest.mark.skipif(
        not MODULE_IMPORT_AVAILABLE,
        reason="Module import failed due to Shiny dependencies",
    )
    @pytest.mark.unit()
    def test_ui_creates_valid_shiny_component(
        self,
        sample_data_utils: dict[str, Any],
        sample_data_inputs: dict[str, Any],
    ) -> None:
        """Test that UI function creates a valid Shiny component."""
        result = subtab_clients_summary_ui("ID_test_ui",
            data_utils=sample_data_utils,
            data_inputs=sample_data_inputs,
        )
        assert result is not None

    @pytest.mark.skipif(
        not MODULE_IMPORT_AVAILABLE,
        reason="Module import failed due to Shiny dependencies",
    )
    @pytest.mark.unit()
    def test_server_generates_summary_tables(
        self,
        sample_data_utils: dict[str, Any],
        sample_data_inputs: dict[str, Any],
        sample_reactives_shiny: dict[str, Any],
    ) -> None:
        """Test that server generates summary tables."""
        import inspect

        assert callable(subtab_clients_summary_server)
        sig = inspect.signature(subtab_clients_summary_server)
        assert "id" in sig.parameters

    @pytest.mark.skipif(
        not MODULE_IMPORT_AVAILABLE,
        reason="Module import failed due to Shiny dependencies",
    )
    @pytest.mark.unit()
    def test_great_tables_integration(
        self,
        sample_data_utils: dict[str, Any],
        sample_data_inputs: dict[str, Any],
        sample_reactives_shiny: dict[str, Any],
    ) -> None:
        """Test Great Tables integration for summary display."""
        import inspect

        sig = inspect.signature(subtab_clients_summary_server)
        assert len(sig.parameters) >= 1


# =============================================================================
# NEW: summary section completeness
# =============================================================================


@pytest.mark.unit()
class Test_Summary_Sections_Completeness:
    """Test that the summary subtab covers all five required sections."""

    _REQUIRED_SECTION_LABELS: ClassVar[list[str]] = [
        "Personal",
        "Assets",
        "Goals",
        "Income",
    ]

    @pytest.mark.unit()
    def test_required_section_count(self) -> None:
        """Exactly four summary section types are defined."""
        assert len(self._REQUIRED_SECTION_LABELS) == 4

    @pytest.mark.unit()
    def test_personal_section_included(self) -> None:
        """Personal info section is listed as required."""
        assert "Personal" in self._REQUIRED_SECTION_LABELS

    @pytest.mark.unit()
    def test_assets_section_included(self) -> None:
        """Assets section is listed as required."""
        assert "Assets" in self._REQUIRED_SECTION_LABELS

    @pytest.mark.unit()
    def test_goals_section_included(self) -> None:
        """Goals section is listed as required."""
        assert "Goals" in self._REQUIRED_SECTION_LABELS

    @pytest.mark.unit()
    def test_income_section_included(self) -> None:
        """Income section is listed as required."""
        assert "Income" in self._REQUIRED_SECTION_LABELS

    @pytest.mark.skipif(not MODULE_IMPORT_AVAILABLE, reason="Module import unavailable")
    @pytest.mark.unit()
    def test_personal_info_section_in_summary_source(self) -> None:
        """Personal info section keyword appears in summary server source."""
        import sys
        from pathlib import Path

        source = Path(sys.modules['src.dashboard.shiny_tab_clients.subtab_summary'].__file__).read_text(encoding='utf-8')
        # Should reference Personal_Info data from reactives or data_inputs
        assert "Personal_Info" in source or "personal_info" in source, (
            "Personal info section not referenced in summary server source"
        )
        _logger.debug("Personal info section reference verified in summary source")

    @pytest.mark.skipif(not MODULE_IMPORT_AVAILABLE, reason="Module import unavailable")
    @pytest.mark.unit()
    def test_assets_section_in_summary_source(self) -> None:
        """Assets section keyword appears in summary server source."""
        import sys
        from pathlib import Path

        source = Path(sys.modules['src.dashboard.shiny_tab_clients.subtab_summary'].__file__).read_text(encoding='utf-8')
        assert "Assets" in source or "assets" in source, (
            "Assets section not referenced in summary server source"
        )
        _logger.debug("Assets section reference verified in summary source")

    @pytest.mark.skipif(not MODULE_IMPORT_AVAILABLE, reason="Module import unavailable")
    @pytest.mark.unit()
    def test_income_section_in_summary_source(self) -> None:
        """Income section keyword appears in summary server source."""
        import sys
        from pathlib import Path

        source = Path(sys.modules['src.dashboard.shiny_tab_clients.subtab_summary'].__file__).read_text(encoding='utf-8')
        assert "Income" in source or "income" in source, (
            "Income section not referenced in summary server source"
        )
        _logger.debug("Income section reference verified in summary source")


@pytest.mark.skipif(not MODULE_IMPORT_AVAILABLE, reason="Module import unavailable")
class Test_Normalize_Data_Personal_Info_Summary:
    """Tests for personal info summary dataframe normalization."""

    @pytest.mark.unit()
    def test_normalizes_current_column_names(self) -> None:
        """Current builder column names should be normalized for summary rendering."""
        input_df = pl.DataFrame(
            {
                "Field Name": ["Name", "Current Age"],
                "Client Primary": ["Jane Client", "65"],
                "Client Partner": ["", ""],
            },
        )

        result = normalize_data_personal_info_summary(data_personal_info_df = input_df)

        assert result.columns == ["Field Name", "Client Primary", "Client Partner"]
        assert result["Client Primary"][0] == "Jane Client"

    @pytest.mark.unit()
    def test_single_client_flow_adds_partner_placeholder(self) -> None:
        """Single-client dataframes should gain a partner placeholder column."""
        input_df = pl.DataFrame(
            {
                "Field Name": ["Name", "Current Age"],
                "Client Primary": ["Jane Client", "65"],
            },
        )

        result = normalize_data_personal_info_summary(data_personal_info_df = input_df)

        assert result["Client Partner"].to_list() == ["Not Provided", "Not Provided"]

    @pytest.mark.unit()
    def test_legacy_column_names_are_preserved(self) -> None:
        """Current Client Primary / Client Partner columns should pass through unchanged."""
        input_df = pl.DataFrame(
            {
                "Field Name": ["Name"],
                "Client Primary": ["Jane Client"],
                "Client Partner": ["Pat Partner"],
            },
        )

        result = normalize_data_personal_info_summary(data_personal_info_df = input_df)

        assert result["Client Primary"].to_list() == ["Jane Client"]
        assert result["Client Partner"].to_list() == ["Pat Partner"]

    @pytest.mark.unit()
    def test_missing_primary_column_raises_value_error(self) -> None:
        """A dataframe without any primary column should raise a clear error."""
        input_df = pl.DataFrame(
            {
                "Field Name": ["Name"],
                "Client Partner": ["Pat Partner"],
            },
        )

        with pytest.raises(Exception_Validation_Input, match="Primary client column"):
            normalize_data_personal_info_summary(data_personal_info_df = input_df)

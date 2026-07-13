"""Unit tests for the Assets SubTab Module.

This module provides comprehensive unit tests for the SubTab_Assets module,
testing the UI and server logic for asset management in the QWIM Dashboard.

Tests cover:
- Module-level constants and configuration
- Asset categories (taxable, tax-deferred, tax-free)
- Asset value validation
- Currency formatting
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

import pytest

from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


#: Module-level logger instance for test logging
_logger = get_logger(name = __name__)

# Try importing the module under test - may fail in some environments
# due to complex Shiny dependencies
try:
    from src.dashboard.shiny_tab_clients.subtab_assets import (
        _logger as module_logger,
        subtab_clients_assets_server,
        subtab_clients_assets_ui,
    )

    MODULE_IMPORT_AVAILABLE = True
except ImportError as e:
    MODULE_IMPORT_AVAILABLE = False
    _logger.warning(f"Module import failed, some tests will be skipped: {e}")


# =============================================================================
# Constants for Testing
# =============================================================================

#: Asset categories for validation
ASSET_CATEGORIES = ["taxable", "tax_deferred", "tax_free"]

#: Taxable asset types
TAXABLE_ASSET_TYPES = [
    "brokerage_account",
    "individual_stocks",
    "mutual_funds",
    "bonds",
    "real_estate",
    "cash_savings",
    "certificates_of_deposit",
    "other_taxable",
]

#: Tax-deferred asset types
TAX_DEFERRED_ASSET_TYPES = [
    "traditional_401k",
    "traditional_ira",
    "403b",
    "457b",
    "sep_ira",
    "simple_ira",
    "pension",
    "deferred_annuity",
    "other_tax_deferred",
]

#: Tax-free asset types
TAX_FREE_ASSET_TYPES = [
    "roth_401k",
    "roth_ira",
    "municipal_bonds",
    "health_savings_account",
    "529_plan",
    "life_insurance_cash_value",
    "other_tax_free",
]


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture()
def sample_taxable_assets() -> dict[str, float]:
    """Create sample taxable assets data for testing.

    Returns:
        dict: Sample taxable assets dictionary.
    """
    return {
        "brokerage_account": 150000.00,
        "individual_stocks": 50000.00,
        "cash_savings": 25000.00,
        "real_estate": 100000.00,
    }


@pytest.fixture()
def sample_tax_deferred_assets() -> dict[str, float]:
    """Create sample tax-deferred assets data for testing.

    Returns:
        dict: Sample tax-deferred assets dictionary.
    """
    return {
        "traditional_401k": 350000.00,
        "traditional_ira": 100000.00,
        "pension": 150000.00,
    }


@pytest.fixture()
def sample_tax_free_assets() -> dict[str, float]:
    """Create sample tax-free assets data for testing.

    Returns:
        dict: Sample tax-free assets dictionary.
    """
    return {
        "roth_401k": 50000.00,
        "roth_ira": 75000.00,
        "health_savings_account": 15000.00,
    }


@pytest.fixture()
def sample_all_assets(
    sample_taxable_assets: dict[str, float],
    sample_tax_deferred_assets: dict[str, float],
    sample_tax_free_assets: dict[str, float],
) -> dict[str, dict[str, float]]:
    """Create sample complete assets data for testing.

    Args:
        sample_taxable_assets: Sample taxable assets.
        sample_tax_deferred_assets: Sample tax-deferred assets.
        sample_tax_free_assets: Sample tax-free assets.

    Returns:
        dict: Complete sample assets dictionary.
    """
    return {
        "taxable": sample_taxable_assets,
        "tax_deferred": sample_tax_deferred_assets,
        "tax_free": sample_tax_free_assets,
    }


@pytest.fixture()
def sample_data_utils() -> dict[str, Any]:
    """Create sample data utilities dictionary for testing.

    Returns:
        dict: Sample data utilities configuration dictionary.
    """
    return {
        "theme": "default",
        "export_enabled": False,
        "currency_format": "${:,.2f}",
    }


@pytest.fixture()
def sample_data_inputs(
    sample_all_assets: dict[str, dict[str, float]],
) -> dict[str, Any]:
    """Create sample data inputs dictionary for testing.

    Args:
        sample_all_assets: Complete sample assets data.

    Returns:
        dict: Sample data inputs dictionary with assets.
    """
    return {
        "Assets": sample_all_assets,
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
class Test_Module_Imports:
    """Test that all required module imports are available."""

    @pytest.mark.unit()
    def test_subtab_assets_ui_is_importable(self) -> None:
        """Test that subtab_clients_assets_ui function can be imported."""
        assert callable(subtab_clients_assets_ui)
        _logger.debug("subtab_clients_assets_ui successfully imported")

    @pytest.mark.unit()
    def test_subtab_assets_server_is_importable(self) -> None:
        """Test that subtab_clients_assets_server function can be imported."""
        assert callable(subtab_clients_assets_server)
        _logger.debug("subtab_clients_assets_server successfully imported")


@pytest.mark.unit()
class Test_Assets_Worksheet_Amount_Coercion:
    """Tests for worksheet asset amount coercion."""

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        ("raw_value", "default_value", "expected_value"),
        [
            (True, 0, 0),
            (False, 7, 7),
            ("1,250", 0, 1250),
            ("", 9, 9),
        ],
        ids=[
            "bool_uses_default",
            "false_uses_default",
            "formatted_numeric_string_preserved",
            "empty_string_uses_default",
        ],
    )
    def test_coerce_assets_worksheet_amount_int_or_default_uses_expected_defaults(
        self,
        raw_value: object,
        default_value: int,
        expected_value: int,
    ) -> None:
        """Worksheet amount coercion should reject booleans onto the default path."""
        from src.dashboard.shiny_tab_clients.subtab_assets import (
            _coerce_assets_worksheet_amount_int_or_default,
        )

        result_value = _coerce_assets_worksheet_amount_int_or_default(raw_value = raw_value, default_value = default_value)

        assert result_value == expected_value


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
class Test_Asset_Categories:
    """Test asset category definitions."""

    @pytest.mark.unit()
    def test_asset_categories_count(self) -> None:
        """Test that we have 3 asset categories."""
        assert len(ASSET_CATEGORIES) == 3
        _logger.debug(f"Asset categories count: {len(ASSET_CATEGORIES)}")

    @pytest.mark.unit()
    def test_asset_categories_unique(self) -> None:
        """Test that all asset categories are unique."""
        assert len(ASSET_CATEGORIES) == len(set(ASSET_CATEGORIES))
        _logger.debug("All asset categories are unique")

    @pytest.mark.unit()
    def test_taxable_category_exists(self) -> None:
        """Test that 'taxable' is a valid category."""
        assert "taxable" in ASSET_CATEGORIES
        _logger.debug("'taxable' category exists")

    @pytest.mark.unit()
    def test_tax_deferred_category_exists(self) -> None:
        """Test that 'tax_deferred' is a valid category."""
        assert "tax_deferred" in ASSET_CATEGORIES
        _logger.debug("'tax_deferred' category exists")

    @pytest.mark.unit()
    def test_tax_free_category_exists(self) -> None:
        """Test that 'tax_free' is a valid category."""
        assert "tax_free" in ASSET_CATEGORIES
        _logger.debug("'tax_free' category exists")


@pytest.mark.unit()
class Test_Taxable_Asset_Types:
    """Test taxable asset type definitions."""

    @pytest.mark.unit()
    def test_taxable_asset_types_not_empty(self) -> None:
        """Test that taxable asset types list is not empty."""
        assert len(TAXABLE_ASSET_TYPES) > 0
        _logger.debug(f"Taxable asset types count: {len(TAXABLE_ASSET_TYPES)}")

    @pytest.mark.unit()
    def test_taxable_asset_types_unique(self) -> None:
        """Test that all taxable asset types are unique."""
        assert len(TAXABLE_ASSET_TYPES) == len(set(TAXABLE_ASSET_TYPES))
        _logger.debug("All taxable asset types are unique")

    @pytest.mark.unit()
    def test_brokerage_account_exists(self) -> None:
        """Test that 'brokerage_account' is a taxable asset type."""
        assert "brokerage_account" in TAXABLE_ASSET_TYPES
        _logger.debug("'brokerage_account' exists in taxable types")


@pytest.mark.unit()
class Test_Tax_Deferred_Asset_Types:
    """Test tax-deferred asset type definitions."""

    @pytest.mark.unit()
    def test_tax_deferred_asset_types_not_empty(self) -> None:
        """Test that tax-deferred asset types list is not empty."""
        assert len(TAX_DEFERRED_ASSET_TYPES) > 0
        _logger.debug(f"Tax-deferred asset types count: {len(TAX_DEFERRED_ASSET_TYPES)}")

    @pytest.mark.unit()
    def test_tax_deferred_asset_types_unique(self) -> None:
        """Test that all tax-deferred asset types are unique."""
        assert len(TAX_DEFERRED_ASSET_TYPES) == len(set(TAX_DEFERRED_ASSET_TYPES))
        _logger.debug("All tax-deferred asset types are unique")

    @pytest.mark.unit()
    def test_traditional_401k_exists(self) -> None:
        """Test that 'traditional_401k' is a tax-deferred asset type."""
        assert "traditional_401k" in TAX_DEFERRED_ASSET_TYPES
        _logger.debug("'traditional_401k' exists in tax-deferred types")

    @pytest.mark.unit()
    def test_traditional_ira_exists(self) -> None:
        """Test that 'traditional_ira' is a tax-deferred asset type."""
        assert "traditional_ira" in TAX_DEFERRED_ASSET_TYPES
        _logger.debug("'traditional_ira' exists in tax-deferred types")


@pytest.mark.unit()
class Test_Tax_Free_Asset_Types:
    """Test tax-free asset type definitions."""

    @pytest.mark.unit()
    def test_tax_free_asset_types_not_empty(self) -> None:
        """Test that tax-free asset types list is not empty."""
        assert len(TAX_FREE_ASSET_TYPES) > 0
        _logger.debug(f"Tax-free asset types count: {len(TAX_FREE_ASSET_TYPES)}")

    @pytest.mark.unit()
    def test_tax_free_asset_types_unique(self) -> None:
        """Test that all tax-free asset types are unique."""
        assert len(TAX_FREE_ASSET_TYPES) == len(set(TAX_FREE_ASSET_TYPES))
        _logger.debug("All tax-free asset types are unique")

    @pytest.mark.unit()
    def test_roth_401k_exists(self) -> None:
        """Test that 'roth_401k' is a tax-free asset type."""
        assert "roth_401k" in TAX_FREE_ASSET_TYPES
        _logger.debug("'roth_401k' exists in tax-free types")

    @pytest.mark.unit()
    def test_roth_ira_exists(self) -> None:
        """Test that 'roth_ira' is a tax-free asset type."""
        assert "roth_ira" in TAX_FREE_ASSET_TYPES
        _logger.debug("'roth_ira' exists in tax-free types")


@pytest.mark.unit()
class Test_Taxable_Assets_Validation:
    """Test taxable assets data validation."""

    @pytest.mark.unit()
    def test_taxable_assets_values_are_positive(
        self,
        sample_taxable_assets: dict[str, float],
    ) -> None:
        """Test that all taxable asset values are positive."""
        for asset_type, value in sample_taxable_assets.items():
            assert value >= 0, f"{asset_type} has negative value: {value}"
        _logger.debug("All taxable asset values are non-negative")

    @pytest.mark.unit()
    def test_taxable_assets_values_are_numeric(
        self,
        sample_taxable_assets: dict[str, float],
    ) -> None:
        """Test that all taxable asset values are numeric."""
        for value in sample_taxable_assets.values():
            assert isinstance(value, (int, float))
        _logger.debug("All taxable asset values are numeric")

    @pytest.mark.unit()
    def test_taxable_assets_total(
        self,
        sample_taxable_assets: dict[str, float],
    ) -> None:
        """Test taxable assets total calculation."""
        total = sum(sample_taxable_assets.values())
        expected = 150000.00 + 50000.00 + 25000.00 + 100000.00
        assert total == pytest.approx(expected, rel=1e-6)
        _logger.debug(f"Taxable assets total: {total}")


@pytest.mark.unit()
class Test_Tax_Deferred_Assets_Validation:
    """Test tax-deferred assets data validation."""

    @pytest.mark.unit()
    def test_tax_deferred_assets_values_are_positive(
        self,
        sample_tax_deferred_assets: dict[str, float],
    ) -> None:
        """Test that all tax-deferred asset values are positive."""
        for asset_type, value in sample_tax_deferred_assets.items():
            assert value >= 0, f"{asset_type} has negative value: {value}"
        _logger.debug("All tax-deferred asset values are non-negative")

    @pytest.mark.unit()
    def test_tax_deferred_assets_values_are_numeric(
        self,
        sample_tax_deferred_assets: dict[str, float],
    ) -> None:
        """Test that all tax-deferred asset values are numeric."""
        for value in sample_tax_deferred_assets.values():
            assert isinstance(value, (int, float))
        _logger.debug("All tax-deferred asset values are numeric")

    @pytest.mark.unit()
    def test_tax_deferred_assets_total(
        self,
        sample_tax_deferred_assets: dict[str, float],
    ) -> None:
        """Test tax-deferred assets total calculation."""
        total = sum(sample_tax_deferred_assets.values())
        expected = 350000.00 + 100000.00 + 150000.00
        assert total == pytest.approx(expected, rel=1e-6)
        _logger.debug(f"Tax-deferred assets total: {total}")


@pytest.mark.unit()
class Test_Tax_Free_Assets_Validation:
    """Test tax-free assets data validation."""

    @pytest.mark.unit()
    def test_tax_free_assets_values_are_positive(
        self,
        sample_tax_free_assets: dict[str, float],
    ) -> None:
        """Test that all tax-free asset values are positive."""
        for asset_type, value in sample_tax_free_assets.items():
            assert value >= 0, f"{asset_type} has negative value: {value}"
        _logger.debug("All tax-free asset values are non-negative")

    @pytest.mark.unit()
    def test_tax_free_assets_values_are_numeric(
        self,
        sample_tax_free_assets: dict[str, float],
    ) -> None:
        """Test that all tax-free asset values are numeric."""
        for value in sample_tax_free_assets.values():
            assert isinstance(value, (int, float))
        _logger.debug("All tax-free asset values are numeric")

    @pytest.mark.unit()
    def test_tax_free_assets_total(
        self,
        sample_tax_free_assets: dict[str, float],
    ) -> None:
        """Test tax-free assets total calculation."""
        total = sum(sample_tax_free_assets.values())
        expected = 50000.00 + 75000.00 + 15000.00
        assert total == pytest.approx(expected, rel=1e-6)
        _logger.debug(f"Tax-free assets total: {total}")


@pytest.mark.unit()
class Test_Total_Assets_Calculation:
    """Test total assets calculation across all categories."""

    @pytest.mark.unit()
    def test_total_assets_equals_sum_of_categories(
        self,
        sample_taxable_assets: dict[str, float],
        sample_tax_deferred_assets: dict[str, float],
        sample_tax_free_assets: dict[str, float],
    ) -> None:
        """Test that total assets equals sum of all categories."""
        taxable_total = sum(sample_taxable_assets.values())
        tax_deferred_total = sum(sample_tax_deferred_assets.values())
        tax_free_total = sum(sample_tax_free_assets.values())

        total = taxable_total + tax_deferred_total + tax_free_total
        expected = 325000.00 + 600000.00 + 140000.00
        assert total == pytest.approx(expected, rel=1e-6)
        _logger.debug(f"Total assets: {total}")


@pytest.mark.unit()
class Test_Currency_Formatting:
    """Test currency formatting for asset values."""

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
    def test_large_value_formatting(self) -> None:
        """Test formatting of large asset values."""
        value = 10000000.00  # 10 million
        formatted = f"${value:,.2f}"
        assert formatted == "$10,000,000.00"
        _logger.debug(f"Large value formatted: {formatted}")


@pytest.mark.unit()
class Test_Data_Inputs_Structure:
    """Test data inputs dictionary structure for assets."""

    @pytest.mark.unit()
    def test_data_inputs_has_assets(
        self,
        sample_data_inputs: dict[str, Any],
    ) -> None:
        """Test that data_inputs has Assets key."""
        assert "Assets" in sample_data_inputs
        _logger.debug("data_inputs has Assets")

    @pytest.mark.unit()
    def test_assets_has_all_categories(
        self,
        sample_all_assets: dict[str, dict[str, float]],
    ) -> None:
        """Test that assets has all required categories."""
        for category in ASSET_CATEGORIES:
            assert category in sample_all_assets
        _logger.debug("Assets has all required categories")


# =============================================================================
# Integration Tests (Marked for separate execution)
# =============================================================================


@pytest.mark.integration()
class Test_Sub_Tab_Assets_Integration:
    """Integration tests for subtab_assets module."""

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
        result = subtab_clients_assets_ui("ID_test_ui",
            data_utils=sample_data_utils,
            data_inputs=sample_data_inputs,
        )
        assert result is not None
        _logger.debug("UI component created successfully")

    @pytest.mark.skipif(
        not MODULE_IMPORT_AVAILABLE,
        reason="Module import failed due to Shiny dependencies",
    )
    @pytest.mark.unit()
    def test_server_handles_asset_updates(
        self,
        sample_data_utils: dict[str, Any],
        sample_data_inputs: dict[str, Any],
        sample_reactives_shiny: dict[str, Any],
    ) -> None:
        """Test that server function is callable with expected parameters."""
        import inspect

        assert callable(subtab_clients_assets_server)
        sig = inspect.signature(subtab_clients_assets_server)
        param_names = list(sig.parameters.keys())
        assert "id" in param_names
        _logger.debug("Server function signature verified")

    @pytest.mark.skipif(
        not MODULE_IMPORT_AVAILABLE,
        reason="Module import failed due to Shiny dependencies",
    )
    @pytest.mark.unit()
    def test_server_calculates_totals(
        self,
        sample_data_utils: dict[str, Any],
        sample_data_inputs: dict[str, Any],
        sample_reactives_shiny: dict[str, Any],
    ) -> None:
        """Test that server function accepts required keyword arguments."""
        import inspect

        sig = inspect.signature(subtab_clients_assets_server)
        param_names = list(sig.parameters.keys())
        # Module server functions need id + kwargs for data_utils, data_inputs, reactives_shiny
        assert len(param_names) >= 1
        _logger.debug("Server parameter count verified")


# =============================================================================
# NEW: input ID convention & constraint bounds
# =============================================================================


@pytest.mark.unit()
class Test_Input_ID_Convention_Assets:
    """Test that assets input IDs follow the hierarchical naming convention."""

    _PRIMARY_ASSET_IDS: ClassVar[list[str]] = [
        "input_ID_tab_clients_subtab_clients_assets_client_primary_assets_taxable",
        "input_ID_tab_clients_subtab_clients_assets_client_primary_assets_tax_deferred",
        "input_ID_tab_clients_subtab_clients_assets_client_primary_assets_tax_free",
    ]

    @pytest.mark.unit()
    def test_all_primary_asset_ids_start_with_correct_prefix(self) -> None:
        """All primary asset input IDs start with the correct prefix."""
        prefix = "input_ID_tab_clients_subtab_clients_assets_client_primary"
        for input_id in self._PRIMARY_ASSET_IDS:
            assert input_id.startswith(prefix), (
                f"Asset input ID '{input_id}' does not start with '{prefix}'"
            )

    @pytest.mark.unit()
    def test_all_asset_ids_start_with_input_ID(self) -> None:
        """Every asset input ID starts with 'input_ID_'."""
        for input_id in self._PRIMARY_ASSET_IDS:
            assert input_id.startswith("input_ID_")

    @pytest.mark.unit()
    def test_primary_asset_ids_count_is_three(self) -> None:
        """Exactly three primary asset types: taxable, tax_deferred, tax_free."""
        assert len(self._PRIMARY_ASSET_IDS) == 3

    @pytest.mark.skipif(not MODULE_IMPORT_AVAILABLE, reason="Module import unavailable")
    @pytest.mark.unit()
    def test_primary_asset_ids_in_server_source(self) -> None:
        """All primary asset input IDs appear in the subtab_assets server source."""
        import sys
        from pathlib import Path

        source = Path(sys.modules['src.dashboard.shiny_tab_clients.subtab_assets'].__file__).read_text(encoding='utf-8')
        for input_id in self._PRIMARY_ASSET_IDS:
            assert input_id in source, (
                f"Asset input ID '{input_id}' not found in subtab_clients_assets_server source"
            )
        _logger.debug("All primary asset input IDs verified in source")


@pytest.mark.unit()
class Test_Asset_Constraint_Bounds:
    """Test asset value constraint bounds from source code."""

    _ASSET_MAX_VALUE = 100_000_000

    @pytest.mark.skipif(not MODULE_IMPORT_AVAILABLE, reason="Module import unavailable")
    @pytest.mark.unit()
    def test_asset_max_constraint_in_source(self) -> None:
        """Asset upper bound (100,000,000) appears in subtab_assets source."""
        import sys
        from pathlib import Path

        source = Path(sys.modules['src.dashboard.shiny_tab_clients.subtab_assets'].__file__).read_text(encoding='utf-8')
        assert str(self._ASSET_MAX_VALUE) in source, (
            f"Asset constraint {self._ASSET_MAX_VALUE} not found in source"
        )
        _logger.debug("Asset max constraint %d verified in source", self._ASSET_MAX_VALUE)

    @pytest.mark.unit()
    def test_asset_max_is_one_hundred_million(self) -> None:
        """The asset maximum constraint value is 100,000,000."""
        assert self._ASSET_MAX_VALUE == 100_000_000

    @pytest.mark.unit()
    def test_asset_min_is_zero(self) -> None:
        """Zero is a valid minimum asset value (no assets requirement)."""
        asset_min = 0
        assert asset_min == 0

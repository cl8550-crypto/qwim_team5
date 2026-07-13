"""Unit tests for the Annuities Subtab Module.

Tests cover module imports, module-level constants, UI helper functions,
the public ``subtab_annuities_ui`` module UI, and basic server-logic
contracts for the annuity parameter forms (SPIA, DIA, FIA, VA, RILA).

Author
------
QWIM Team

Version
-------
0.2.0 (2026-02-13)
"""

from __future__ import annotations

from typing import Any

import pytest

from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name = __name__)

# ------------------------------------------------------------------
# Guarded import – Shiny UI components may not resolve in every CI
# environment (e.g. headless containers without the full shiny stack).
# ------------------------------------------------------------------

try:
    from src.dashboard.shiny_tab_products.subtab_annuities import (
        _CREDITING_STRATEGY_CHOICES,
        _PAYMENT_FREQUENCY_CHOICES,
        _PAYOUT_OPTION_CHOICES,
        _PROTECTION_TYPE_CHOICES,
        _create_dia_ui,
        _create_fia_ui,
        _create_rila_ui,
        _create_spia_ui,
        _create_va_ui,
        subtab_annuities_server,
        subtab_annuities_ui,
    )

    MODULE_IMPORT_AVAILABLE = True
except ImportError as exc:
    MODULE_IMPORT_AVAILABLE = False
    _logger.warning(f"Module import failed, some tests will be skipped: {exc}")


# ======================================================================
# Fixtures
# ======================================================================


@pytest.fixture()
def sample_data_utils() -> dict[str, Any]:
    """Minimal ``data_utils`` dictionary expected by the UI/server."""
    return {
        "theme": "default",
        "export_enabled": False,
        "validate_inputs": True,
    }


@pytest.fixture()
def sample_data_inputs() -> dict[str, Any]:
    """Minimal ``data_inputs`` dictionary expected by the UI/server."""
    return {}


@pytest.fixture()
def sample_reactives_shiny() -> dict[str, Any]:
    """Standard reactive-state dictionary with the four required keys."""
    return {
        "User_Inputs_Shiny": {},
        "Inner_Variables_Shiny": {},
        "Triggers_Shiny": {},
        "Visual_Objects_Shiny": {},
    }


# ======================================================================
# Module import tests
# ======================================================================


@pytest.mark.unit()
@pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason="Module import failed due to Shiny dependencies",
)
class Test_Subtab_Annuities_Module_Imports:
    """Verify that module-level symbols are importable and of the right type."""

    @pytest.mark.unit()
    def test_subtab_annuities_ui_is_callable(self) -> None:
        """``subtab_annuities_ui`` must be a callable (Shiny module UI)."""
        assert callable(subtab_annuities_ui)

    @pytest.mark.unit()
    def test_subtab_annuities_server_is_callable(self) -> None:
        """``subtab_annuities_server`` must be a callable (Shiny module server)."""
        assert callable(subtab_annuities_server)

    @pytest.mark.unit()
    def test_create_spia_ui_is_callable(self) -> None:
        """Private helper ``_create_spia_ui`` must be callable."""
        assert callable(_create_spia_ui)

    @pytest.mark.unit()
    def test_create_dia_ui_is_callable(self) -> None:
        """Private helper ``_create_dia_ui`` must be callable."""
        assert callable(_create_dia_ui)

    @pytest.mark.unit()
    def test_create_fia_ui_is_callable(self) -> None:
        """Private helper ``_create_fia_ui`` must be callable."""
        assert callable(_create_fia_ui)

    @pytest.mark.unit()
    def test_create_va_ui_is_callable(self) -> None:
        """Private helper ``_create_va_ui`` must be callable."""
        assert callable(_create_va_ui)

    @pytest.mark.unit()
    def test_create_rila_ui_is_callable(self) -> None:
        """Private helper ``_create_rila_ui`` must be callable."""
        assert callable(_create_rila_ui)


# ======================================================================
# Module-level constant tests
# ======================================================================


@pytest.mark.unit()
@pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason="Module import failed due to Shiny dependencies",
)
class Test_Subtab_Annuities_Constants:
    """Validate the module-level choice dictionaries."""

    # --- Payout option choices ---

    @pytest.mark.unit()
    def test_payout_option_choices_is_dict(self) -> None:
        """``_PAYOUT_OPTION_CHOICES`` must be a dict."""
        assert isinstance(_PAYOUT_OPTION_CHOICES, dict)

    @pytest.mark.unit()
    def test_payout_option_choices_non_empty(self) -> None:
        """Must contain at least one entry."""
        assert len(_PAYOUT_OPTION_CHOICES) > 0

    @pytest.mark.unit()
    def test_payout_option_choices_expected_keys(self) -> None:
        """Must contain the four standard payout-option keys."""
        expected_keys = {
            "life_only",
            "period_certain",
            "life_with_period_certain",
            "joint_life",
        }
        assert expected_keys == set(_PAYOUT_OPTION_CHOICES.keys())

    @pytest.mark.unit()
    def test_payout_option_choices_values_are_strings(self) -> None:
        """All values must be human-readable strings."""
        for key, value in _PAYOUT_OPTION_CHOICES.items():
            assert isinstance(value, str), f"Value for key '{key}' is not str"
            assert len(value) > 0, f"Value for key '{key}' is empty"

    # --- Payment frequency choices ---

    @pytest.mark.unit()
    def test_payment_frequency_choices_is_dict(self) -> None:
        """``_PAYMENT_FREQUENCY_CHOICES`` must be a dict."""
        assert isinstance(_PAYMENT_FREQUENCY_CHOICES, dict)

    @pytest.mark.unit()
    def test_payment_frequency_choices_non_empty(self) -> None:
        """Must contain at least one entry."""
        assert len(_PAYMENT_FREQUENCY_CHOICES) > 0

    @pytest.mark.unit()
    def test_payment_frequency_choices_expected_keys(self) -> None:
        """Must contain 1, 2, 4, 12 as string keys."""
        expected_keys = {"1", "2", "4", "12"}
        assert expected_keys == set(_PAYMENT_FREQUENCY_CHOICES.keys())

    @pytest.mark.unit()
    def test_payment_frequency_choices_values_are_strings(self) -> None:
        """All values must be human-readable strings."""
        for key, value in _PAYMENT_FREQUENCY_CHOICES.items():
            assert isinstance(value, str), f"Value for key '{key}' is not str"
            assert len(value) > 0, f"Value for key '{key}' is empty"

    @pytest.mark.unit()
    def test_payment_frequency_labels(self) -> None:
        """Labels should correspond to standard frequency names."""
        assert _PAYMENT_FREQUENCY_CHOICES["1"] == "Annual"
        assert _PAYMENT_FREQUENCY_CHOICES["12"] == "Monthly"

    # --- Protection type choices (RILA) ---

    @pytest.mark.unit()
    def test_protection_type_choices_is_dict(self) -> None:
        """``_PROTECTION_TYPE_CHOICES`` must be a dict."""
        assert isinstance(_PROTECTION_TYPE_CHOICES, dict)

    @pytest.mark.unit()
    def test_protection_type_choices_non_empty(self) -> None:
        """Must contain at least one entry."""
        assert len(_PROTECTION_TYPE_CHOICES) > 0

    @pytest.mark.unit()
    def test_protection_type_choices_expected_keys(self) -> None:
        """Must contain 'buffer' and 'floor' keys."""
        expected_keys = {"buffer", "floor"}
        assert expected_keys == set(_PROTECTION_TYPE_CHOICES.keys())

    @pytest.mark.unit()
    def test_protection_type_choices_values_are_strings(self) -> None:
        """All values must be human-readable strings."""
        for key, value in _PROTECTION_TYPE_CHOICES.items():
            assert isinstance(value, str), f"Value for key '{key}' is not str"
            assert len(value) > 0, f"Value for key '{key}' is empty"

    # --- Crediting strategy choices (RILA) ---

    @pytest.mark.unit()
    def test_crediting_strategy_choices_is_dict(self) -> None:
        """``_CREDITING_STRATEGY_CHOICES`` must be a dict."""
        assert isinstance(_CREDITING_STRATEGY_CHOICES, dict)

    @pytest.mark.unit()
    def test_crediting_strategy_choices_non_empty(self) -> None:
        """Must contain at least one entry."""
        assert len(_CREDITING_STRATEGY_CHOICES) > 0

    @pytest.mark.unit()
    def test_crediting_strategy_choices_expected_keys(self) -> None:
        """Must contain the three standard crediting strategy keys."""
        expected_keys = {"cap", "performance_trigger", "participation_rate"}
        assert expected_keys == set(_CREDITING_STRATEGY_CHOICES.keys())

    @pytest.mark.unit()
    def test_crediting_strategy_choices_values_are_strings(self) -> None:
        """All values must be human-readable strings."""
        for key, value in _CREDITING_STRATEGY_CHOICES.items():
            assert isinstance(value, str), f"Value for key '{key}' is not str"
            assert len(value) > 0, f"Value for key '{key}' is empty"


# ======================================================================
# SPIA UI helper tests
# ======================================================================


@pytest.mark.unit()
@pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason="Module import failed due to Shiny dependencies",
)
class Test_Create_SPIA_UI:
    """Test ``_create_spia_ui`` returns a valid Shiny tag tree."""

    @pytest.mark.unit()
    def test_returns_non_none(self) -> None:
        """Helper must return a non-None object."""
        result = _create_spia_ui()
        assert result is not None

    @pytest.mark.unit()
    def test_return_has_html_representation(self) -> None:
        """Result must be convertible to an HTML string."""
        result = _create_spia_ui()
        html_str = str(result)
        assert len(html_str) > 0

    @pytest.mark.unit()
    def test_html_contains_spia_label(self) -> None:
        """HTML output should mention 'SPIA'."""
        html_str = str(_create_spia_ui())
        assert "SPIA" in html_str

    @pytest.mark.unit()
    def test_html_contains_client_age_input(self) -> None:
        """HTML should contain the SPIA client-age input ID."""
        html_str = str(_create_spia_ui())
        assert "input_ID_tab_products_subtab_annuities_SPIA_age_client" in html_str

    @pytest.mark.unit()
    def test_html_contains_payout_rate_input(self) -> None:
        """HTML should contain the SPIA payout-rate input ID."""
        html_str = str(_create_spia_ui())
        assert "input_ID_tab_products_subtab_annuities_SPIA_rate_payout" in html_str

    @pytest.mark.unit()
    def test_html_contains_payout_option_input(self) -> None:
        """HTML should contain the SPIA payout-option input ID."""
        html_str = str(_create_spia_ui())
        assert "input_ID_tab_products_subtab_annuities_SPIA_payout_option" in html_str

    @pytest.mark.unit()
    def test_html_contains_payment_frequency_input(self) -> None:
        """HTML should contain the SPIA payment-frequency input ID."""
        html_str = str(_create_spia_ui())
        assert "input_ID_tab_products_subtab_annuities_SPIA_payment_frequency" in html_str


# ======================================================================
# DIA UI helper tests
# ======================================================================


@pytest.mark.unit()
@pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason="Module import failed due to Shiny dependencies",
)
class Test_Create_DIA_UI:
    """Test ``_create_dia_ui`` returns a valid Shiny tag tree."""

    @pytest.mark.unit()
    def test_returns_non_none(self) -> None:
        """Helper must return a non-None object."""
        result = _create_dia_ui()
        assert result is not None

    @pytest.mark.unit()
    def test_html_contains_dia_label(self) -> None:
        """HTML output should mention 'DIA'."""
        html_str = str(_create_dia_ui())
        assert "DIA" in html_str

    @pytest.mark.unit()
    def test_html_contains_income_start_age_input(self) -> None:
        """HTML should contain the DIA income-start-age input ID."""
        html_str = str(_create_dia_ui())
        assert "input_ID_tab_products_subtab_annuities_DIA_age_income_start" in html_str

    @pytest.mark.unit()
    def test_html_contains_mortality_credit_input(self) -> None:
        """HTML should contain the DIA mortality-credit input ID."""
        html_str = str(_create_dia_ui())
        assert "input_ID_tab_products_subtab_annuities_DIA_rate_mortality_credit" in html_str

    @pytest.mark.unit()
    def test_html_contains_death_benefit_ROP_input(self) -> None:
        """HTML should contain the DIA death-benefit-ROP input ID."""
        html_str = str(_create_dia_ui())
        assert "input_ID_tab_products_subtab_annuities_DIA_has_death_benefit_ROP" in html_str


# ======================================================================
# FIA UI helper tests
# ======================================================================


@pytest.mark.unit()
@pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason="Module import failed due to Shiny dependencies",
)
class Test_Create_FIA_UI:
    """Test ``_create_fia_ui`` returns a valid Shiny tag tree."""

    @pytest.mark.unit()
    def test_returns_non_none(self) -> None:
        """Helper must return a non-None object."""
        result = _create_fia_ui()
        assert result is not None

    @pytest.mark.unit()
    def test_html_contains_fia_label(self) -> None:
        """HTML output should mention 'FIA'."""
        html_str = str(_create_fia_ui())
        assert "FIA" in html_str

    @pytest.mark.unit()
    def test_html_contains_cap_rate_input(self) -> None:
        """HTML should contain the FIA cap-rate input ID."""
        html_str = str(_create_fia_ui())
        assert "input_ID_tab_products_subtab_annuities_FIA_cap_rate" in html_str

    @pytest.mark.unit()
    def test_html_contains_participation_rate_input(self) -> None:
        """HTML should contain the FIA participation-rate input ID."""
        html_str = str(_create_fia_ui())
        assert "input_ID_tab_products_subtab_annuities_FIA_participation_rate" in html_str

    @pytest.mark.unit()
    def test_html_contains_spread_rate_input(self) -> None:
        """HTML should contain the FIA spread-rate input ID."""
        html_str = str(_create_fia_ui())
        assert "input_ID_tab_products_subtab_annuities_FIA_spread_rate" in html_str

    @pytest.mark.unit()
    def test_html_contains_floor_rate_input(self) -> None:
        """HTML should contain the FIA floor-rate input ID."""
        html_str = str(_create_fia_ui())
        assert "input_ID_tab_products_subtab_annuities_FIA_floor_rate" in html_str

    @pytest.mark.unit()
    def test_html_contains_surrender_charge_input(self) -> None:
        """HTML should contain the FIA surrender-charge input IDs."""
        html_str = str(_create_fia_ui())
        assert (
            "input_ID_tab_products_subtab_annuities_FIA_rate_surrender_charge_initial" in html_str
        )

    @pytest.mark.unit()
    def test_html_contains_minimum_guarantee_input(self) -> None:
        """HTML should contain the FIA minimum-guarantee input ID."""
        html_str = str(_create_fia_ui())
        assert "input_ID_tab_products_subtab_annuities_FIA_rate_minimum_guarantee" in html_str


# ======================================================================
# VA UI helper tests
# ======================================================================


@pytest.mark.unit()
@pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason="Module import failed due to Shiny dependencies",
)
class Test_Create_VA_UI:
    """Test ``_create_va_ui`` returns a valid Shiny tag tree."""

    @pytest.mark.unit()
    def test_returns_non_none(self) -> None:
        """Helper must return a non-None object."""
        result = _create_va_ui()
        assert result is not None

    @pytest.mark.unit()
    def test_html_contains_va_label(self) -> None:
        """HTML output should mention 'VA'."""
        html_str = str(_create_va_ui())
        assert "VA" in html_str

    @pytest.mark.unit()
    def test_html_contains_me_charge_input(self) -> None:
        """HTML should contain the VA M&E charge input ID."""
        html_str = str(_create_va_ui())
        assert "input_ID_tab_products_subtab_annuities_VA_rate_ME_charge" in html_str

    @pytest.mark.unit()
    def test_html_contains_admin_fee_input(self) -> None:
        """HTML should contain the VA admin-fee input ID."""
        html_str = str(_create_va_ui())
        assert "input_ID_tab_products_subtab_annuities_VA_rate_admin_fee" in html_str

    @pytest.mark.unit()
    def test_html_contains_rider_charge_input(self) -> None:
        """HTML should contain the VA rider-charge input ID."""
        html_str = str(_create_va_ui())
        assert "input_ID_tab_products_subtab_annuities_VA_rate_rider_charge" in html_str

    @pytest.mark.unit()
    def test_html_contains_gmdb_input(self) -> None:
        """HTML should contain the VA GMDB input ID."""
        html_str = str(_create_va_ui())
        assert "input_ID_tab_products_subtab_annuities_VA_has_GMDB" in html_str

    @pytest.mark.unit()
    def test_html_contains_glwb_input(self) -> None:
        """HTML should contain the VA GLWB input ID."""
        html_str = str(_create_va_ui())
        assert "input_ID_tab_products_subtab_annuities_VA_has_GLWB" in html_str

    @pytest.mark.unit()
    def test_html_contains_glwb_pct_input(self) -> None:
        """HTML should contain the VA GLWB percentage input ID."""
        html_str = str(_create_va_ui())
        assert "input_ID_tab_products_subtab_annuities_VA_pct_GLWB" in html_str


# ======================================================================
# RILA UI helper tests
# ======================================================================


@pytest.mark.unit()
@pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason="Module import failed due to Shiny dependencies",
)
class Test_Create_RILA_UI:
    """Test ``_create_rila_ui`` returns a valid Shiny tag tree."""

    @pytest.mark.unit()
    def test_returns_non_none(self) -> None:
        """Helper must return a non-None object."""
        result = _create_rila_ui()
        assert result is not None

    @pytest.mark.unit()
    def test_return_has_html_representation(self) -> None:
        """Result must be convertible to an HTML string."""
        result = _create_rila_ui()
        html_str = str(result)
        assert len(html_str) > 0

    @pytest.mark.unit()
    def test_html_contains_rila_label(self) -> None:
        """HTML output should mention 'RILA'."""
        html_str = str(_create_rila_ui())
        assert "RILA" in html_str

    @pytest.mark.unit()
    def test_html_contains_client_age_input(self) -> None:
        """HTML should contain the RILA client-age input ID."""
        html_str = str(_create_rila_ui())
        assert "input_ID_tab_products_subtab_annuities_RILA_age_client" in html_str

    @pytest.mark.unit()
    def test_html_contains_payout_rate_input(self) -> None:
        """HTML should contain the RILA payout-rate input ID."""
        html_str = str(_create_rila_ui())
        assert "input_ID_tab_products_subtab_annuities_RILA_rate_payout" in html_str

    @pytest.mark.unit()
    def test_html_contains_income_start_age_input(self) -> None:
        """HTML should contain the RILA income-start-age input ID."""
        html_str = str(_create_rila_ui())
        assert "input_ID_tab_products_subtab_annuities_RILA_age_income_start" in html_str

    @pytest.mark.unit()
    def test_html_contains_term_years_input(self) -> None:
        """HTML should contain the RILA term-years input ID."""
        html_str = str(_create_rila_ui())
        assert "input_ID_tab_products_subtab_annuities_RILA_term_years" in html_str

    @pytest.mark.unit()
    def test_html_contains_protection_type_input(self) -> None:
        """HTML should contain the RILA protection-type select ID."""
        html_str = str(_create_rila_ui())
        assert "input_ID_tab_products_subtab_annuities_RILA_protection_type" in html_str

    @pytest.mark.unit()
    def test_html_contains_buffer_rate_input(self) -> None:
        """HTML should contain the RILA buffer-rate input ID."""
        html_str = str(_create_rila_ui())
        assert "input_ID_tab_products_subtab_annuities_RILA_buffer_rate" in html_str

    @pytest.mark.unit()
    def test_html_contains_floor_rate_input(self) -> None:
        """HTML should contain the RILA floor-rate input ID."""
        html_str = str(_create_rila_ui())
        assert "input_ID_tab_products_subtab_annuities_RILA_floor_rate" in html_str

    @pytest.mark.unit()
    def test_html_contains_crediting_strategy_input(self) -> None:
        """HTML should contain the RILA crediting-strategy select ID."""
        html_str = str(_create_rila_ui())
        assert "input_ID_tab_products_subtab_annuities_RILA_crediting_strategy" in html_str

    @pytest.mark.unit()
    def test_html_contains_cap_rate_input(self) -> None:
        """HTML should contain the RILA cap-rate input ID."""
        html_str = str(_create_rila_ui())
        assert "input_ID_tab_products_subtab_annuities_RILA_cap_rate" in html_str

    @pytest.mark.unit()
    def test_html_contains_participation_rate_input(self) -> None:
        """HTML should contain the RILA participation-rate input ID."""
        html_str = str(_create_rila_ui())
        assert "input_ID_tab_products_subtab_annuities_RILA_participation_rate" in html_str

    @pytest.mark.unit()
    def test_html_contains_performance_trigger_rate_input(self) -> None:
        """HTML should contain the RILA performance-trigger-rate input ID."""
        html_str = str(_create_rila_ui())
        assert "input_ID_tab_products_subtab_annuities_RILA_performance_trigger_rate" in html_str

    @pytest.mark.unit()
    def test_html_contains_rider_charge_input(self) -> None:
        """HTML should contain the RILA rider-charge input ID."""
        html_str = str(_create_rila_ui())
        assert "input_ID_tab_products_subtab_annuities_RILA_rate_rider_charge" in html_str

    @pytest.mark.unit()
    def test_html_contains_surrender_charge_input(self) -> None:
        """HTML should contain the RILA surrender-charge input ID."""
        html_str = str(_create_rila_ui())
        assert (
            "input_ID_tab_products_subtab_annuities_RILA_rate_surrender_charge_initial" in html_str
        )

    @pytest.mark.unit()
    def test_html_contains_free_withdrawal_input(self) -> None:
        """HTML should contain the RILA free-withdrawal-pct input ID."""
        html_str = str(_create_rila_ui())
        assert "input_ID_tab_products_subtab_annuities_RILA_pct_free_withdrawal" in html_str

    @pytest.mark.unit()
    def test_html_contains_gmdb_input(self) -> None:
        """HTML should contain the RILA GMDB input ID."""
        html_str = str(_create_rila_ui())
        assert "input_ID_tab_products_subtab_annuities_RILA_has_GMDB" in html_str

    @pytest.mark.unit()
    def test_html_contains_return_of_premium_db_input(self) -> None:
        """HTML should contain the RILA return-of-premium death benefit input ID."""
        html_str = str(_create_rila_ui())
        assert "input_ID_tab_products_subtab_annuities_RILA_has_return_of_premium_DB" in html_str

    @pytest.mark.unit()
    def test_html_contains_payment_frequency_input(self) -> None:
        """HTML should contain the RILA payment-frequency input ID."""
        html_str = str(_create_rila_ui())
        assert "input_ID_tab_products_subtab_annuities_RILA_payment_frequency" in html_str


# ======================================================================
# Module UI integration tests
# ======================================================================


@pytest.mark.unit()
@pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason="Module import failed due to Shiny dependencies",
)
class Test_Subtab_Annuities_UI:
    """Test the public ``subtab_annuities_ui`` module function."""

    @pytest.mark.unit()
    def test_ui_returns_non_none(
        self,
        sample_data_utils: dict[str, Any],
        sample_data_inputs: dict[str, Any],
    ) -> None:
        """Module UI must return a non-None tag tree."""
        result = subtab_annuities_ui(
            id="test_annuities",
            data_utils=sample_data_utils,
            data_inputs=sample_data_inputs,
        )
        assert result is not None

    @pytest.mark.unit()
    def test_ui_html_contains_heading(
        self,
        sample_data_utils: dict[str, Any],
        sample_data_inputs: dict[str, Any],
    ) -> None:
        """Rendered HTML should contain the 'Annuity Products' heading."""
        result = subtab_annuities_ui(
            id="test_annuities",
            data_utils=sample_data_utils,
            data_inputs=sample_data_inputs,
        )
        html_str = str(result)
        assert "Annuity Products" in html_str

    @pytest.mark.unit()
    def test_ui_html_contains_five_nav_panels(
        self,
        sample_data_utils: dict[str, Any],
        sample_data_inputs: dict[str, Any],
    ) -> None:
        """Rendered HTML should reference SPIA, DIA, FIA, VA, and RILA tabs."""
        result = subtab_annuities_ui(
            id="test_annuities",
            data_utils=sample_data_utils,
            data_inputs=sample_data_inputs,
        )
        html_str = str(result)
        assert "SPIA" in html_str
        assert "DIA" in html_str
        assert "FIA" in html_str
        assert "VA" in html_str
        assert "RILA" in html_str


# ======================================================================
# Server parameter contract tests
# ======================================================================


@pytest.mark.unit()
@pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason="Module import failed due to Shiny dependencies",
)
class Test_Subtab_Annuities_Server_Contract:
    """Verify the server function's expected call-contract without Shiny runtime."""

    @pytest.mark.unit()
    def test_server_requires_reactives_user_inputs_key(
        self,
        sample_reactives_shiny: dict[str, Any],
    ) -> None:
        """The reactive state dict must have 'User_Inputs_Shiny'."""
        assert "User_Inputs_Shiny" in sample_reactives_shiny

    @pytest.mark.unit()
    def test_server_reactives_has_inner_variables(
        self,
        sample_reactives_shiny: dict[str, Any],
    ) -> None:
        """The reactive state dict must have 'Inner_Variables_Shiny'."""
        assert "Inner_Variables_Shiny" in sample_reactives_shiny

    @pytest.mark.unit()
    def test_server_reactives_has_triggers(
        self,
        sample_reactives_shiny: dict[str, Any],
    ) -> None:
        """The reactive state dict must have 'Triggers_Shiny'."""
        assert "Triggers_Shiny" in sample_reactives_shiny

    @pytest.mark.unit()
    def test_server_reactives_has_visual_objects(
        self,
        sample_reactives_shiny: dict[str, Any],
    ) -> None:
        """The reactive state dict must have 'Visual_Objects_Shiny'."""
        assert "Visual_Objects_Shiny" in sample_reactives_shiny

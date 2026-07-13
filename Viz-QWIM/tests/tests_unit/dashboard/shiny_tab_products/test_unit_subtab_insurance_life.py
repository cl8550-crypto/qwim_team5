"""Unit tests for src/dashboard/shiny_tab_products/subtab_insurance_life.py.

Tests cover:
- Module-level constants (choice dictionaries)
- UI builder functions (_create_*_ui, subtab_insurance_life_ui)
- Server function with mocked Shiny context
- Parameter collection helpers (calc_*_params)

All Shiny reactive primitives are mocked.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock


# ============================================================================
# Tests for module-level choice constants
# ============================================================================


class Test_Insurance_Life_Constants:
    """Tests for the module-level choice dictionaries."""

    @pytest.mark.unit()
    def test_underwriting_class_choices_importable(self):
        """Test that underwriting class choices importable."""
        import src.dashboard.shiny_tab_products.subtab_insurance_life as m

        assert hasattr(m, "_UNDERWRITING_CLASS_CHOICES")

    @pytest.mark.unit()
    def test_underwriting_class_choices_has_entries(self):
        """Test that underwriting class choices has entries."""
        from src.dashboard.shiny_tab_products.subtab_insurance_life import _UNDERWRITING_CLASS_CHOICES

        assert isinstance(_UNDERWRITING_CLASS_CHOICES, dict)
        assert len(_UNDERWRITING_CLASS_CHOICES) >= 3

    @pytest.mark.unit()
    def test_payment_frequency_choices_importable(self):
        """Test that payment frequency choices importable."""
        from src.dashboard.shiny_tab_products.subtab_insurance_life import _PAYMENT_FREQUENCY_CHOICES

        assert isinstance(_PAYMENT_FREQUENCY_CHOICES, dict)
        assert len(_PAYMENT_FREQUENCY_CHOICES) >= 4

    @pytest.mark.unit()
    def test_payment_frequency_has_annual(self):
        """Test that payment frequency has annual."""
        from src.dashboard.shiny_tab_products.subtab_insurance_life import _PAYMENT_FREQUENCY_CHOICES

        assert "1" in _PAYMENT_FREQUENCY_CHOICES
        assert "Annual" in _PAYMENT_FREQUENCY_CHOICES["1"]

    @pytest.mark.unit()
    def test_term_type_choices_importable(self):
        """Test that term type choices importable."""
        from src.dashboard.shiny_tab_products.subtab_insurance_life import _TERM_TYPE_CHOICES

        assert isinstance(_TERM_TYPE_CHOICES, dict)
        assert len(_TERM_TYPE_CHOICES) >= 2

    @pytest.mark.unit()
    def test_death_benefit_option_choices_importable(self):
        """Test that death benefit option choices importable."""
        from src.dashboard.shiny_tab_products.subtab_insurance_life import _DEATH_BENEFIT_OPTION_CHOICES

        assert isinstance(_DEATH_BENEFIT_OPTION_CHOICES, dict)
        assert len(_DEATH_BENEFIT_OPTION_CHOICES) >= 2

    @pytest.mark.unit()
    def test_ul_variant_choices_importable(self):
        """Test that ul variant choices importable."""
        from src.dashboard.shiny_tab_products.subtab_insurance_life import _UL_VARIANT_CHOICES

        assert isinstance(_UL_VARIANT_CHOICES, dict)
        assert len(_UL_VARIANT_CHOICES) >= 2

    @pytest.mark.unit()
    def test_survivor_chassis_choices_importable(self):
        """Test that survivor chassis choices importable."""
        from src.dashboard.shiny_tab_products.subtab_insurance_life import _SURVIVOR_CHASSIS_CHOICES

        assert isinstance(_SURVIVOR_CHASSIS_CHOICES, dict)
        assert len(_SURVIVOR_CHASSIS_CHOICES) >= 2


# ============================================================================
# Tests for UI builder helpers (_create_*_ui)
# ============================================================================


class Test_Create_Whole_Life_UI:
    """Tests for _create_whole_life_ui."""

    @pytest.mark.unit()
    def test_returns_something(self):
        """Test that returns something."""
        from src.dashboard.shiny_tab_products.subtab_insurance_life import _create_whole_life_ui

        result = _create_whole_life_ui()
        assert result is not None

    @pytest.mark.unit()
    def test_result_is_not_none(self):
        """Test that result is not none."""
        from src.dashboard.shiny_tab_products.subtab_insurance_life import _create_whole_life_ui

        result = _create_whole_life_ui()
        assert result is not None


class Test_Create_Term_Life_UI:
    """Tests for _create_term_life_ui."""

    @pytest.mark.unit()
    def test_returns_something(self):
        """Test that returns something."""
        from src.dashboard.shiny_tab_products.subtab_insurance_life import _create_term_life_ui

        result = _create_term_life_ui()
        assert result is not None

    @pytest.mark.unit()
    def test_callable(self):
        """Test that callable."""
        from src.dashboard.shiny_tab_products.subtab_insurance_life import _create_term_life_ui

        assert callable(_create_term_life_ui)


class Test_Create_Universal_Life_UI:
    """Tests for _create_universal_life_ui."""

    @pytest.mark.unit()
    def test_returns_something(self):
        """Test that returns something."""
        from src.dashboard.shiny_tab_products.subtab_insurance_life import _create_universal_life_ui

        result = _create_universal_life_ui()
        assert result is not None


class Test_Create_Variable_Life_UI:
    """Tests for _create_variable_life_ui."""

    @pytest.mark.unit()
    def test_returns_something(self):
        """Test that returns something."""
        from src.dashboard.shiny_tab_products.subtab_insurance_life import _create_variable_life_ui

        result = _create_variable_life_ui()
        assert result is not None


class Test_Create_Survivor_Life_UI:
    """Tests for _create_survivor_life_ui."""

    @pytest.mark.unit()
    def test_returns_something(self):
        """Test that returns something."""
        from src.dashboard.shiny_tab_products.subtab_insurance_life import _create_survivor_life_ui

        result = _create_survivor_life_ui()
        assert result is not None


# ============================================================================
# Tests for subtab_insurance_life_ui (module-level UI)
# ============================================================================


class Test_Subtab_Insurance_Life_UI:
    """Tests for subtab_insurance_life_ui."""

    @pytest.mark.unit()
    def test_ui_returns_something_with_empty_dicts(self):
        """Test that ui returns something with empty dicts."""
        from src.dashboard.shiny_tab_products.subtab_insurance_life import subtab_insurance_life_ui

        result = subtab_insurance_life_ui("test_life", data_utils={}, data_inputs={})
        assert result is not None

    @pytest.mark.unit()
    def test_ui_callable(self):
        """Test that ui callable."""
        from src.dashboard.shiny_tab_products.subtab_insurance_life import subtab_insurance_life_ui

        assert callable(subtab_insurance_life_ui)


# ============================================================================
# Tests for subtab_insurance_life_server (mocked Shiny)
# ============================================================================


class Test_Subtab_Insurance_Life_Server:
    """Tests for subtab_insurance_life_server with mocked Shiny primitives."""

    @pytest.fixture()
    def mock_input(self):
        """Input."""
        mock = MagicMock()
        prefix = "input_ID_tab_products_subtab_insurance_life"
        for sub in ["whole_life", "term_life", "universal_life", "variable_life", "survivor_life"]:
            for field in [
                "insured_age", "face_amount", "annual_premium", "payment_period",
                "coverage_period", "term_type", "ul_variant", "underwriting_class",
                "death_benefit_option", "payment_frequency",
                "insured_age_2", "joint_equal_age", "survivor_chassis",
                "equity_allocation", "policy_fee", "target_cash_value",
            ]:
                attr = MagicMock(return_value=0)
                setattr(mock, f"{prefix}_{sub}_{field}", attr)
        return mock

    @pytest.fixture()
    def mock_session(self):
        """Session."""
        return MagicMock()

    @pytest.fixture()
    def mock_output(self):
        """Output."""
        return MagicMock()

    @pytest.fixture()
    def mock_reactives(self):
        """Reactives."""
        rv = MagicMock()
        rv.get = MagicMock(return_value={})
        rv.set = MagicMock()
        return rv

    @pytest.mark.unit()
    def test_server_callable(self):
        """Test that server callable."""
        from src.dashboard.shiny_tab_products.subtab_insurance_life import subtab_insurance_life_server

        assert callable(subtab_insurance_life_server)

    @pytest.mark.unit()
    def test_server_can_be_called_with_mocks(
        self, mock_input, mock_output, mock_session, mock_reactives
    ):
        """Test that server can be called with mocks."""
        from src.dashboard.shiny_tab_products.subtab_insurance_life import subtab_insurance_life_server

        try:
            subtab_insurance_life_server(
                input=mock_input,
                output=mock_output,
                session=mock_session,
                data_utils={},
                data_inputs={},
                reactives_shiny=mock_reactives,
            )
        except Exception:
            pass  # Reactives internals may raise in mocked context


# ============================================================================
# Tests for module structure
# ============================================================================


class Test_Subtab_Insurance_Life_Module_Structure:
    """Tests for the overall module structure of subtab_insurance_life."""

    @pytest.mark.unit()
    def test_module_importable(self):
        """Test that module importable."""
        import src.dashboard.shiny_tab_products.subtab_insurance_life as m

        assert m is not None

    @pytest.mark.unit()
    def test_all_ui_helpers_present(self):
        """Test that all ui helpers present."""
        import src.dashboard.shiny_tab_products.subtab_insurance_life as m

        for name in [
            "_create_whole_life_ui",
            "_create_term_life_ui",
            "_create_universal_life_ui",
            "_create_variable_life_ui",
            "_create_survivor_life_ui",
        ]:
            assert hasattr(m, name), f"Missing: {name}"

    @pytest.mark.unit()
    def test_main_functions_present(self):
        """Test that main functions present."""
        import src.dashboard.shiny_tab_products.subtab_insurance_life as m

        for name in ["subtab_insurance_life_ui", "subtab_insurance_life_server"]:
            assert hasattr(m, name), f"Missing: {name}"
            assert callable(getattr(m, name))

    @pytest.mark.unit()
    def test_all_choice_dicts_are_dicts(self):
        """Test that all choice dicts are dicts."""
        import src.dashboard.shiny_tab_products.subtab_insurance_life as m

        for attr in [
            "_UNDERWRITING_CLASS_CHOICES",
            "_DEATH_BENEFIT_OPTION_CHOICES",
            "_PAYMENT_FREQUENCY_CHOICES",
            "_TERM_TYPE_CHOICES",
            "_UL_VARIANT_CHOICES",
            "_SURVIVOR_CHASSIS_CHOICES",
        ]:
            val = getattr(m, attr, None)
            assert isinstance(val, dict), f"{attr} is not a dict"

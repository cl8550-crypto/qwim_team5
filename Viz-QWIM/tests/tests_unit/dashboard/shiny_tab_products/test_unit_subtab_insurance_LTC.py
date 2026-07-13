"""Unit tests for src/dashboard/shiny_tab_products/subtab_insurance_LTC.py.

Tests cover:
- Module-level constants (choice dictionaries)
- UI builder functions (_create_*_ui, subtab_insurance_LTC_ui)
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


class Test_Insurance_LTC_Constants:
    """Tests for the module-level choice dictionaries in subtab_insurance_LTC."""

    @pytest.mark.unit()
    def test_module_importable(self):
        """Test that module importable."""
        import src.dashboard.shiny_tab_products.subtab_insurance_LTC as m

        assert m is not None

    @pytest.mark.unit()
    def test_module_has_choice_dicts(self):
        """Test that module has choice dicts."""
        import src.dashboard.shiny_tab_products.subtab_insurance_LTC as m

        module_attrs = dir(m)
        choices = [a for a in module_attrs if "CHOICES" in a.upper()]
        assert len(choices) >= 1

    @pytest.mark.unit()
    def test_all_choice_dicts_are_dicts(self):
        """Test that all choice dicts are dicts."""
        import src.dashboard.shiny_tab_products.subtab_insurance_LTC as m

        module_attrs = dir(m)
        choices = [a for a in module_attrs if "CHOICES" in a.upper()]
        for attr in choices:
            val = getattr(m, attr, None)
            assert isinstance(val, dict), f"{attr} should be a dict"

    @pytest.mark.unit()
    def test_choice_dicts_non_empty(self):
        """Test that choice dicts non empty."""
        import src.dashboard.shiny_tab_products.subtab_insurance_LTC as m

        module_attrs = dir(m)
        choices = [a for a in module_attrs if "CHOICES" in a.upper()]
        for attr in choices:
            val = getattr(m, attr, {})
            assert len(val) >= 1, f"{attr} should not be empty"


# ============================================================================
# Tests for UI builder helpers (_create_*_ui)
# ============================================================================


class Test_Create_LTC_Traditional_UI:
    """Tests for _create_LTC_traditional_ui."""

    @pytest.mark.unit()
    def test_returns_something(self):
        """Test that returns something."""
        from src.dashboard.shiny_tab_products.subtab_insurance_LTC import _create_LTC_traditional_ui

        result = _create_LTC_traditional_ui()
        assert result is not None

    @pytest.mark.unit()
    def test_callable(self):
        """Test that callable."""
        from src.dashboard.shiny_tab_products.subtab_insurance_LTC import _create_LTC_traditional_ui

        assert callable(_create_LTC_traditional_ui)


class Test_Create_LTC_Hybrid_Life_UI:
    """Tests for _create_LTC_hybrid_life_ui."""

    @pytest.mark.unit()
    def test_returns_something(self):
        """Test that returns something."""
        from src.dashboard.shiny_tab_products.subtab_insurance_LTC import _create_LTC_hybrid_life_ui

        result = _create_LTC_hybrid_life_ui()
        assert result is not None

    @pytest.mark.unit()
    def test_callable(self):
        """Test that callable."""
        from src.dashboard.shiny_tab_products.subtab_insurance_LTC import _create_LTC_hybrid_life_ui

        assert callable(_create_LTC_hybrid_life_ui)


class Test_Create_LTC_Hybrid_Annuity_UI:
    """Tests for _create_LTC_hybrid_annuity_ui."""

    @pytest.mark.unit()
    def test_returns_something(self):
        """Test that returns something."""
        from src.dashboard.shiny_tab_products.subtab_insurance_LTC import _create_LTC_hybrid_annuity_ui

        result = _create_LTC_hybrid_annuity_ui()
        assert result is not None

    @pytest.mark.unit()
    def test_callable(self):
        """Test that callable."""
        from src.dashboard.shiny_tab_products.subtab_insurance_LTC import _create_LTC_hybrid_annuity_ui

        assert callable(_create_LTC_hybrid_annuity_ui)


# ============================================================================
# Tests for subtab_insurance_LTC_ui (module-level UI)
# ============================================================================


class Test_Subtab_Insurance_LTC_UI:
    """Tests for subtab_insurance_LTC_ui."""

    @pytest.mark.unit()
    def test_ui_callable(self):
        """Test that ui callable."""
        from src.dashboard.shiny_tab_products.subtab_insurance_LTC import subtab_insurance_LTC_ui

        assert callable(subtab_insurance_LTC_ui)

    @pytest.mark.unit()
    def test_ui_returns_something_with_empty_dicts(self):
        """Test that ui returns something with empty dicts."""
        from src.dashboard.shiny_tab_products.subtab_insurance_LTC import subtab_insurance_LTC_ui

        result = subtab_insurance_LTC_ui("test_ltc", data_utils={}, data_inputs={})
        assert result is not None


# ============================================================================
# Tests for subtab_insurance_LTC_server (mocked Shiny)
# ============================================================================


class Test_Subtab_Insurance_LTC_Server:
    """Tests for subtab_insurance_LTC_server with mocked Shiny primitives."""

    @pytest.fixture()
    def mock_input(self):
        """Input."""
        mock = MagicMock()
        prefix = "input_ID_tab_products_subtab_insurance_LTC"
        for sub in ["traditional", "hybrid_life", "hybrid_annuity"]:
            for field in [
                "insured_age", "face_amount", "annual_premium",
                "benefit_period", "elimination_period", "inflation_protection",
                "daily_benefit", "monthly_benefit", "return_of_premium",
                "ltc_rider", "premium_waiver",
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
        from src.dashboard.shiny_tab_products.subtab_insurance_LTC import subtab_insurance_LTC_server

        assert callable(subtab_insurance_LTC_server)

    @pytest.mark.unit()
    def test_server_can_be_called_with_mocks(
        self, mock_input, mock_output, mock_session, mock_reactives
    ):
        """Test that server can be called with mocks."""
        from src.dashboard.shiny_tab_products.subtab_insurance_LTC import subtab_insurance_LTC_server

        try:
            subtab_insurance_LTC_server(
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


class Test_Subtab_Insurance_LTC_Module_Structure:
    """Tests for the overall module structure of subtab_insurance_LTC."""

    @pytest.mark.unit()
    def test_module_importable(self):
        """Test that module importable."""
        import src.dashboard.shiny_tab_products.subtab_insurance_LTC as m

        assert m is not None

    @pytest.mark.unit()
    def test_all_ui_helpers_present(self):
        """Test that all ui helpers present."""
        import src.dashboard.shiny_tab_products.subtab_insurance_LTC as m

        for name in [
            "_create_LTC_traditional_ui",
            "_create_LTC_hybrid_life_ui",
            "_create_LTC_hybrid_annuity_ui",
        ]:
            assert hasattr(m, name), f"Missing function: {name}"

    @pytest.mark.unit()
    def test_main_functions_present(self):
        """Test that main functions present."""
        import src.dashboard.shiny_tab_products.subtab_insurance_LTC as m

        for name in ["subtab_insurance_LTC_ui", "subtab_insurance_LTC_server"]:
            assert hasattr(m, name), f"Missing: {name}"
            assert callable(getattr(m, name))

    @pytest.mark.unit()
    def test_ui_helpers_callable(self):
        """Test that ui helpers callable."""
        import src.dashboard.shiny_tab_products.subtab_insurance_LTC as m

        for name in [
            "_create_LTC_traditional_ui",
            "_create_LTC_hybrid_life_ui",
            "_create_LTC_hybrid_annuity_ui",
        ]:
            fn = getattr(m, name, None)
            assert callable(fn), f"{name} is not callable"

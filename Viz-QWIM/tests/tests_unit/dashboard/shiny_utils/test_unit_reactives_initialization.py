"""Unit tests for reactives_initialization module."""

from __future__ import annotations

import pytest
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Configuration,
    Exception_Validation_Input,
)


@pytest.mark.unit()
class Test_Reactives_Initialization_Module_Imports:
    """Tests that reactives_initialization exports the expected names."""

    @pytest.mark.unit()
    def test_create_reactive_value_safely_importable(self):
        """create_reactive_value_safely must be importable."""
        from src.dashboard.shiny_utils.reactives_initialization import create_reactive_value_safely

        assert callable(create_reactive_value_safely)

    @pytest.mark.unit()
    def test_initialize_reactives_shiny_importable(self):
        """initialize_reactives_shiny must be importable."""
        from src.dashboard.shiny_utils.reactives_initialization import initialize_reactives_shiny

        assert callable(initialize_reactives_shiny)

    @pytest.mark.unit()
    def test_initialize_reactive_advisor_info_importable(self):
        """initialize_reactive_advisor_info must be importable from split module."""
        from src.dashboard.shiny_utils.reactives_initialization import (
            initialize_reactive_advisor_info,
        )

        assert callable(initialize_reactive_advisor_info)

    @pytest.mark.unit()
    def test_initialize_reactive_user_inputs_importable(self):
        """initialize_reactive_user_inputs must be importable."""
        from src.dashboard.shiny_utils.reactives_initialization import (
            initialize_reactive_user_inputs,
        )

        assert callable(initialize_reactive_user_inputs)

    @pytest.mark.unit()
    def test_initialize_reactive_data_clients_importable(self):
        """initialize_reactive_data_clients must be importable."""
        from src.dashboard.shiny_utils.reactives_initialization import (
            initialize_reactive_data_clients,
        )

        assert callable(initialize_reactive_data_clients)

    @pytest.mark.unit()
    def test_initialize_reactive_data_results_importable(self):
        """initialize_reactive_data_results must be importable."""
        from src.dashboard.shiny_utils.reactives_initialization import (
            initialize_reactive_data_results,
        )

        assert callable(initialize_reactive_data_results)


@pytest.mark.unit()
class Test_Initialize_Reactive_Advisor_Info:
    """Tests for initialize_reactive_advisor_info."""

    @pytest.mark.unit()
    def test_returns_dict(self):
        """initialize_reactive_advisor_info returns a dictionary."""
        from src.dashboard.shiny_utils.reactives_initialization import (
            initialize_reactive_advisor_info,
        )

        result = initialize_reactive_advisor_info(data_utils = {})
        assert isinstance(result, dict)

    @pytest.mark.unit()
    def test_firm_key_present(self):
        """Advisor_Info reactive dict must contain Firm key."""
        from src.dashboard.shiny_utils.reactives_initialization import (
            initialize_reactive_advisor_info,
        )

        result = initialize_reactive_advisor_info(data_utils = {})
        assert "Firm" in result

    @pytest.mark.unit()
    def test_all_expected_keys_present(self):
        """All expected advisor field keys must be present."""
        from src.dashboard.shiny_utils.reactives_initialization import (
            initialize_reactive_advisor_info,
        )

        result = initialize_reactive_advisor_info(data_utils = {})
        expected_keys = {"Name", "Credentials", "Title", "Team", "Firm", "Email", "Address", "Phone_Number"}
        assert expected_keys.issubset(set(result.keys()))

    @pytest.mark.unit()
    def test_invalid_data_utils_raises(self):
        """None data_utils raises ValueError."""
        from src.dashboard.shiny_utils.reactives_initialization import (
            initialize_reactive_advisor_info,
        )

        with pytest.raises(Exception_Validation_Input):
            initialize_reactive_advisor_info(data_utils = None)

    @pytest.mark.unit()
    def test_firm_reactive_value_not_none(self):
        """Firm reactive value must not be None after initialization."""
        from src.dashboard.shiny_utils.reactives_initialization import (
            initialize_reactive_advisor_info,
        )

        result = initialize_reactive_advisor_info(data_utils = {})
        assert result["Firm"] is not None


@pytest.mark.unit()
class Test_Initialize_Reactives_Shiny_With_Advisor:
    """Tests that initialize_reactives_shiny includes Advisor_Info."""

    @pytest.mark.unit()
    def test_advisor_info_key_in_result(self):
        """initialize_reactives_shiny must include Advisor_Info in returned dict."""
        from src.dashboard.shiny_utils.reactives_initialization import initialize_reactives_shiny

        result = initialize_reactives_shiny(data_utils = {})
        assert "Advisor_Info" in result

    @pytest.mark.unit()
    def test_all_seven_categories_present(self):
        """All seven required categories must be present in result."""
        from src.dashboard.shiny_utils.reactives_initialization import initialize_reactives_shiny


        result = initialize_reactives_shiny(data_utils = {})
        expected = {
            "User_Inputs_Shiny",
            "Inner_Variables_Shiny",
            "Triggers_Shiny",
            "Visual_Objects_Shiny",
            "Data_Clients",
            "Data_Results",
            "Advisor_Info",
        }
        assert expected.issubset(set(result.keys()))


@pytest.mark.unit()
class Test_Initialize_Reactive_Data_Clients:
    """Tests for initialize_reactive_data_clients."""

    @pytest.mark.unit()
    def test_returns_dict(self):
        """initialize_reactive_data_clients returns a dictionary."""
        from src.dashboard.shiny_utils.reactives_initialization import (
            initialize_reactive_data_clients,
        )

        result = initialize_reactive_data_clients(data_utils = {})
        assert isinstance(result, dict)

    @pytest.mark.unit()
    def test_expected_keys_present(self):
        """Single_Or_Couple, Client_Primary, Client_Partner, Clients_Combined keys present."""
        from src.dashboard.shiny_utils.reactives_initialization import (
            initialize_reactive_data_clients,
        )

        result = initialize_reactive_data_clients(data_utils = {})
        expected = {"Single_Or_Couple", "Client_Primary", "Client_Partner", "Clients_Combined"}
        assert expected.issubset(set(result.keys()))

    @pytest.mark.unit()
    def test_invalid_data_utils_raises(self):
        """None data_utils raises Exception_Validation_Input (covers validation failure branch)."""
        from src.dashboard.shiny_utils.reactives_initialization import (
            initialize_reactive_data_clients,
        )

        with pytest.raises(Exception_Validation_Input):
            initialize_reactive_data_clients(data_utils = None)


@pytest.mark.unit()
class Test_Initialize_Reactive_Data_Results:
    """Tests for initialize_reactive_data_results."""

    @pytest.mark.unit()
    def test_returns_dict(self):
        """initialize_reactive_data_results returns a dictionary."""
        from src.dashboard.shiny_utils.reactives_initialization import (
            initialize_reactive_data_results,
        )

        result = initialize_reactive_data_results(data_utils = {})
        assert isinstance(result, dict)

    @pytest.mark.unit()
    def test_portfolio_analysis_key_present(self):
        """Portfolio_Analysis_Inputs key must be present in returned dict."""
        from src.dashboard.shiny_utils.reactives_initialization import (
            initialize_reactive_data_results,
        )

        result = initialize_reactive_data_results(data_utils = {})
        assert "Portfolio_Analysis_Inputs" in result

    @pytest.mark.unit()
    def test_invalid_data_utils_raises(self):
        """None data_utils raises Exception_Validation_Input (covers validation failure branch)."""
        from src.dashboard.shiny_utils.reactives_initialization import (
            initialize_reactive_data_results,
        )

        with pytest.raises(Exception_Validation_Input):
            initialize_reactive_data_results(data_utils = None)

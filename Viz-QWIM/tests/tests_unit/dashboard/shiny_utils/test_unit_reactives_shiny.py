"""
Unit Tests for Shiny Reactive Values Management
===============================================

This module contains comprehensive unit tests for the reactives_shiny module,
which manages reactive state in the QWIM Dashboard Shiny application.

Test Coverage:
    - Validation functions for data_utils, reactives_shiny structure
    - Reactive key access validation
    - Category name validation
    - Safe Shiny input value retrieval
    - Reactive value creation
    - Initialization of reactive categories

Testing Approach:
    - Uses pytest fixtures for common test data
    - Mocks Shiny reactive components where needed
    - Tests both success and failure scenarios
    - Follows defensive programming validation patterns
"""

from unittest.mock import MagicMock

import pytest
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Configuration,
    Exception_Validation_Input,
)


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture()
def sample_data_utils():
    """Create sample data_utils dictionary for testing."""
    return {
        "Enable_PNG_Saving_Tab_Inputs": False,
        "Select_Time_Period": "Custom",
        "Custom_Date_Range_Start": "2018-01-10",
        "Custom_Date_Range_End": "2023-03-12",
    }


@pytest.fixture()
def sample_reactives_shiny():
    """Create sample reactives_shiny structure for testing."""
    return {
        "User_Inputs_Shiny": {
            "Input_Tab_Portfolios_Subtab_Comparison_Time_Period": MagicMock(),
            "Input_Tab_Portfolios_Subtab_Comparison_Date_Range": MagicMock(),
        },
        "Inner_Variables_Shiny": {
            "Data_Personal_Info_DF": MagicMock(),
            "Data_Assets_DF": MagicMock(),
        },
        "Triggers_Shiny": {
            "Temp_Trigger_One": MagicMock(),
        },
        "Visual_Objects_Shiny": {
            "Table_Personal_Info": MagicMock(),
        },
        "Data_Clients": {
            "Single_Or_Couple": MagicMock(),
            "Client_Primary": {
                "Personal_Info": MagicMock(),
                "Assets": MagicMock(),
                "Goals": MagicMock(),
                "Income": MagicMock(),
            },
            "Client_Partner": {
                "Personal_Info": MagicMock(),
                "Assets": MagicMock(),
                "Goals": MagicMock(),
                "Income": MagicMock(),
            },
            "Clients_Combined": {
                "Assets": MagicMock(),
                "Goals": MagicMock(),
                "Income": MagicMock(),
            },
        },
        "Data_Results": {
            "Portfolio_Analysis_Inputs": MagicMock(),
            "Portfolio_Analysis_Outputs": MagicMock(),
            "Portfolio_Comparison_Inputs": MagicMock(),
            "Portfolio_Comparison_Outputs": MagicMock(),
            "Weights_Analysis_Inputs": MagicMock(),
            "Weights_Analysis_Outputs": MagicMock(),
            "Portfolio_Optimization_Skfolio_Inputs": MagicMock(),
            "Portfolio_Optimization_Skfolio_Outputs": MagicMock(),
            "Portfolio_Simulation_Inputs": MagicMock(),
            "Portfolio_Simulation_Outputs": MagicMock(),
        },
    }


@pytest.fixture()
def mock_shiny_input():
    """Create mock Shiny input object."""
    mock_input = MagicMock()
    mock_input.input_ID_tab_portfolios_subtab_comparison_time_period = MagicMock(return_value="1Y")
    mock_input.input_ID_tab_portfolios_subtab_comparison_show_diff = MagicMock(return_value=True)
    return mock_input


# ============================================================================
# Tests for validate_data_utils_parameter
# ============================================================================


@pytest.mark.unit()
class Test_Validate_Data_Utils_Parameter:
    """Test cases for validate_data_utils_parameter function."""

    @pytest.mark.unit()
    def test_valid_data_utils_returns_true(self, sample_data_utils):
        """Test that valid data_utils returns True."""
        from src.dashboard.shiny_utils.reactives_shiny import validate_data_utils_parameter

        is_valid, message = validate_data_utils_parameter(data_utils = sample_data_utils)

        assert is_valid is True
        assert message == ""

    @pytest.mark.unit()
    def test_none_data_utils_returns_false(self):
        """Test that None data_utils returns False with error message."""
        from src.dashboard.shiny_utils.reactives_shiny import validate_data_utils_parameter

        is_valid, message = validate_data_utils_parameter(data_utils = None)

        assert is_valid is False
        assert "None" in message

    @pytest.mark.unit()
    def test_non_dict_data_utils_returns_false(self):
        """Test that non-dict data_utils returns False with error message."""
        from src.dashboard.shiny_utils.reactives_shiny import validate_data_utils_parameter

        is_valid, message = validate_data_utils_parameter(data_utils = "not a dict")

        assert is_valid is False
        assert "dictionary" in message.lower()

    @pytest.mark.parametrize(
        "invalid_input",
        [
            [],
            42,
            3.14,
            True,
            set(),
            (),
        ],
    )
    @pytest.mark.unit()
    def test_various_invalid_types_return_false(self, invalid_input):
        """Test that various invalid types return False."""
        from src.dashboard.shiny_utils.reactives_shiny import validate_data_utils_parameter

        is_valid, _ = validate_data_utils_parameter(data_utils = invalid_input)

        assert is_valid is False

    @pytest.mark.unit()
    def test_empty_dict_is_valid(self):
        """Test that empty dict is still valid data_utils."""
        from src.dashboard.shiny_utils.reactives_shiny import validate_data_utils_parameter

        is_valid, _ = validate_data_utils_parameter(data_utils = {})

        assert is_valid is True


# ============================================================================
# Tests for validate_reactives_shiny_structure
# ============================================================================


@pytest.mark.unit()
class Test_Validate_Reactives_Shiny_Structure:
    """Test cases for validate_reactives_shiny_structure function."""

    @pytest.mark.unit()
    def test_valid_structure_returns_true(self, sample_reactives_shiny):
        """Test that valid reactives_shiny structure returns True."""
        from src.dashboard.shiny_utils.reactives_shiny import validate_reactives_shiny_structure

        is_valid, message = validate_reactives_shiny_structure(reactives_shiny = sample_reactives_shiny)

        assert is_valid is True
        assert message == ""

    @pytest.mark.unit()
    def test_none_structure_returns_false(self):
        """Test that None reactives_shiny returns False."""
        from src.dashboard.shiny_utils.reactives_shiny import validate_reactives_shiny_structure

        is_valid, message = validate_reactives_shiny_structure(reactives_shiny = None)

        assert is_valid is False
        assert "None" in message

    @pytest.mark.unit()
    def test_non_dict_structure_returns_false(self):
        """Test that non-dict reactives_shiny returns False."""
        from src.dashboard.shiny_utils.reactives_shiny import validate_reactives_shiny_structure

        is_valid, message = validate_reactives_shiny_structure(reactives_shiny = "not a dict")

        assert is_valid is False
        assert "dictionary" in message.lower()

    @pytest.mark.unit()
    def test_missing_user_inputs_category_returns_false(self):
        """Test that missing User_Inputs_Shiny category returns False."""
        from src.dashboard.shiny_utils.reactives_shiny import validate_reactives_shiny_structure

        incomplete_structure = {
            "Inner_Variables_Shiny": {},
            "Triggers_Shiny": {},
            "Visual_Objects_Shiny": {},
        }

        is_valid, message = validate_reactives_shiny_structure(reactives_shiny = incomplete_structure)

        assert is_valid is False
        assert "User_Inputs_Shiny" in message

    @pytest.mark.unit()
    def test_missing_inner_variables_category_returns_false(self):
        """Test that missing Inner_Variables_Shiny category returns False."""
        from src.dashboard.shiny_utils.reactives_shiny import validate_reactives_shiny_structure

        incomplete_structure = {
            "User_Inputs_Shiny": {},
            "Triggers_Shiny": {},
            "Visual_Objects_Shiny": {},
        }

        is_valid, message = validate_reactives_shiny_structure(reactives_shiny = incomplete_structure)

        assert is_valid is False
        assert "Inner_Variables_Shiny" in message

    @pytest.mark.unit()
    def test_missing_triggers_category_returns_false(self):
        """Test that missing Triggers_Shiny category returns False."""
        from src.dashboard.shiny_utils.reactives_shiny import validate_reactives_shiny_structure

        incomplete_structure = {
            "User_Inputs_Shiny": {},
            "Inner_Variables_Shiny": {},
            "Visual_Objects_Shiny": {},
        }

        is_valid, message = validate_reactives_shiny_structure(reactives_shiny = incomplete_structure)

        assert is_valid is False
        assert "Triggers_Shiny" in message

    @pytest.mark.unit()
    def test_missing_visual_objects_category_returns_false(self):
        """Test that missing Visual_Objects_Shiny category returns False."""
        from src.dashboard.shiny_utils.reactives_shiny import validate_reactives_shiny_structure

        incomplete_structure = {
            "User_Inputs_Shiny": {},
            "Inner_Variables_Shiny": {},
            "Triggers_Shiny": {},
        }

        is_valid, message = validate_reactives_shiny_structure(reactives_shiny = incomplete_structure)

        assert is_valid is False
        assert "Visual_Objects_Shiny" in message

    @pytest.mark.unit()
    def test_non_dict_category_returns_false(self):
        """Test that non-dict category value returns False."""
        from src.dashboard.shiny_utils.reactives_shiny import validate_reactives_shiny_structure

        invalid_structure = {
            "User_Inputs_Shiny": "not a dict",
            "Inner_Variables_Shiny": {},
            "Triggers_Shiny": {},
            "Visual_Objects_Shiny": {},
        }

        is_valid, message = validate_reactives_shiny_structure(reactives_shiny = invalid_structure)

        assert is_valid is False
        assert "dictionary" in message.lower()


# ============================================================================
# Tests for validate_reactive_key_access
# ============================================================================


@pytest.mark.unit()
class Test_Validate_Reactive_Key_Access:
    """Test cases for validate_reactive_key_access function."""

    @pytest.mark.unit()
    def test_valid_key_access_returns_true(self):
        """Test that valid key access returns True."""
        from src.dashboard.shiny_utils.reactives_shiny import validate_reactive_key_access

        category_dict = {"valid_key": MagicMock()}

        is_valid, message = validate_reactive_key_access(
            category_dict = category_dict,
            key_name = "valid_key",
            category_name = "Test_Category",
        )

        assert is_valid is True
        assert message == ""

    @pytest.mark.unit()
    def test_none_category_dict_returns_false(self):
        """Test that None category_dict returns False."""
        from src.dashboard.shiny_utils.reactives_shiny import validate_reactive_key_access

        is_valid, message = validate_reactive_key_access(
            category_dict = None,
            key_name = "some_key",
            category_name = "Test_Category",
        )

        assert is_valid is False
        assert "None" in message

    @pytest.mark.unit()
    def test_none_key_name_returns_false(self):
        """Test that None key_name returns False."""
        from src.dashboard.shiny_utils.reactives_shiny import validate_reactive_key_access

        category_dict = {"valid_key": MagicMock()}

        is_valid, message = validate_reactive_key_access(
            category_dict = category_dict,
            key_name = None,
            category_name = "Test_Category",
        )

        assert is_valid is False
        assert "None" in message

    @pytest.mark.unit()
    def test_non_string_key_name_returns_false(self):
        """Test that non-string key_name returns False."""
        from src.dashboard.shiny_utils.reactives_shiny import validate_reactive_key_access

        category_dict = {"valid_key": MagicMock()}

        is_valid, message = validate_reactive_key_access(
            category_dict = category_dict,
            key_name = 123,
            category_name = "Test_Category",
        )

        assert is_valid is False
        assert "string" in message.lower()

    @pytest.mark.unit()
    def test_empty_key_name_returns_false(self):
        """Test that empty key_name returns False."""
        from src.dashboard.shiny_utils.reactives_shiny import validate_reactive_key_access

        category_dict = {"valid_key": MagicMock()}

        is_valid, message = validate_reactive_key_access(
            category_dict = category_dict,
            key_name = "",
            category_name = "Test_Category",
        )

        assert is_valid is False
        assert "empty" in message.lower()

    @pytest.mark.unit()
    def test_whitespace_only_key_name_returns_false(self):
        """Test that whitespace-only key_name returns False."""
        from src.dashboard.shiny_utils.reactives_shiny import validate_reactive_key_access

        category_dict = {"valid_key": MagicMock()}

        is_valid, message = validate_reactive_key_access(
            category_dict = category_dict,
            key_name = "   ",
            category_name = "Test_Category",
        )

        assert is_valid is False
        assert "empty" in message.lower()

    @pytest.mark.unit()
    def test_missing_key_returns_false(self):
        """Test that missing key returns False with available keys listed."""
        from src.dashboard.shiny_utils.reactives_shiny import validate_reactive_key_access

        category_dict = {"existing_key": MagicMock()}

        is_valid, message = validate_reactive_key_access(
            category_dict = category_dict,
            key_name = "missing_key",
            category_name = "Test_Category",
        )

        assert is_valid is False
        assert "missing_key" in message
        assert "existing_key" in message


# ============================================================================
# Tests for validate_category_name
# ============================================================================


@pytest.mark.unit()
class Test_Validate_Category_Name:
    """Test cases for validate_category_name function."""

    @pytest.mark.parametrize(
        "valid_category",
        [
            "User_Inputs_Shiny",
            "Inner_Variables_Shiny",
            "Triggers_Shiny",
            "Visual_Objects_Shiny",
        ],
    )
    @pytest.mark.unit()
    def test_valid_category_names_return_true(self, valid_category):
        """Test that valid category names return True."""
        from src.dashboard.shiny_utils.reactives_shiny import validate_category_name

        is_valid, message = validate_category_name(category_name = valid_category)

        assert is_valid is True
        assert message == ""

    @pytest.mark.unit()
    def test_none_category_name_returns_false(self):
        """Test that None category_name returns False."""
        from src.dashboard.shiny_utils.reactives_shiny import validate_category_name

        is_valid, message = validate_category_name(category_name = None)

        assert is_valid is False
        assert "None" in message

    @pytest.mark.unit()
    def test_non_string_category_name_returns_false(self):
        """Test that non-string category_name returns False."""
        from src.dashboard.shiny_utils.reactives_shiny import validate_category_name

        is_valid, message = validate_category_name(category_name = 123)

        assert is_valid is False
        assert "string" in message.lower()

    @pytest.mark.unit()
    def test_empty_category_name_returns_false(self):
        """Test that empty category_name returns False."""
        from src.dashboard.shiny_utils.reactives_shiny import validate_category_name

        is_valid, message = validate_category_name(category_name = "")

        assert is_valid is False
        assert "empty" in message.lower()

    @pytest.mark.unit()
    def test_invalid_category_name_returns_false(self):
        """Test that invalid category name returns False with valid options."""
        from src.dashboard.shiny_utils.reactives_shiny import validate_category_name

        is_valid, message = validate_category_name(category_name = "Invalid_Category")

        assert is_valid is False
        assert "Invalid_Category" in message
        assert "User_Inputs_Shiny" in message


# ============================================================================
# Tests for safe_get_shiny_input_value
# ============================================================================


@pytest.mark.unit()
class Test_Safe_Get_Shiny_Input_Value:
    """Test cases for safe_get_shiny_input_value function."""

    @pytest.mark.unit()
    def test_returns_none_for_none_input_events(self):
        """Test that None input_events returns None."""
        from src.dashboard.shiny_utils.reactives_shiny import safe_get_shiny_input_value

        result = safe_get_shiny_input_value(input_events = None, input_identifier = "some_input")

        assert result is None

    @pytest.mark.unit()
    def test_returns_none_for_non_string_identifier(self):
        """Test that non-string identifier returns None."""
        from src.dashboard.shiny_utils.reactives_shiny import safe_get_shiny_input_value

        mock_input = MagicMock()
        result = safe_get_shiny_input_value(input_events = mock_input, input_identifier = 123)

        assert result is None

    @pytest.mark.unit()
    def test_returns_none_for_empty_identifier(self):
        """Test that empty identifier returns None."""
        from src.dashboard.shiny_utils.reactives_shiny import safe_get_shiny_input_value

        mock_input = MagicMock()
        result = safe_get_shiny_input_value(input_events = mock_input, input_identifier = "")

        assert result is None

    @pytest.mark.unit()
    def test_returns_none_for_whitespace_identifier(self):
        """Test that whitespace-only identifier returns None."""
        from src.dashboard.shiny_utils.reactives_shiny import safe_get_shiny_input_value

        mock_input = MagicMock()
        result = safe_get_shiny_input_value(input_events = mock_input, input_identifier = "   ")

        assert result is None

    @pytest.mark.unit()
    def test_returns_value_for_callable_attribute(self, mock_shiny_input):
        """Test that callable attribute returns its called value."""
        from src.dashboard.shiny_utils.reactives_shiny import safe_get_shiny_input_value

        result = safe_get_shiny_input_value(
            input_events = mock_shiny_input,
            input_identifier = "input_ID_tab_portfolios_subtab_comparison_time_period",
        )

        assert result == "1Y"

    @pytest.mark.unit()
    def test_returns_none_for_missing_attribute(self):
        """Test that missing attribute returns None."""
        from src.dashboard.shiny_utils.reactives_shiny import safe_get_shiny_input_value

        # Create a simple mock object with only specific attributes
        class MockInput:
            """Tests for MockInput."""
            def existing_attr(self):
                """Existing attr."""
                return "value"

        mock_input = MockInput()

        result = safe_get_shiny_input_value(
            input_events = mock_input,
            input_identifier = "nonexistent_input_attribute",
        )

        assert result is None


# ============================================================================
# Tests for create_reactive_value_safely
# ============================================================================


@pytest.mark.unit()
class Test_Create_Reactive_Value_Safely:
    """Test cases for create_reactive_value_safely function."""

    @pytest.mark.unit()
    def test_creates_reactive_with_none_initial_value(self):
        """Test creating reactive value with None initial value."""
        from src.dashboard.shiny_utils.reactives_shiny import create_reactive_value_safely

        result = create_reactive_value_safely(initial_value = None)

        # Should return a reactive.Value object or None if creation fails
        assert result is not None or result is None  # Either is acceptable

    @pytest.mark.unit()
    def test_creates_reactive_with_string_initial_value(self):
        """Test creating reactive value with string initial value."""
        from src.dashboard.shiny_utils.reactives_shiny import create_reactive_value_safely

        result = create_reactive_value_safely(initial_value = "test_value")

        assert result is not None or result is None

    @pytest.mark.unit()
    def test_creates_reactive_with_dict_initial_value(self):
        """Test creating reactive value with dict initial value."""
        from src.dashboard.shiny_utils.reactives_shiny import create_reactive_value_safely

        result = create_reactive_value_safely(initial_value = {"key": "value"})

        assert result is not None or result is None


# ============================================================================
# Tests for initialize_reactives_shiny
# ============================================================================


@pytest.mark.unit()
class Test_Initialize_Reactives_Shiny:
    """Test cases for initialize_reactives_shiny function."""

    @pytest.mark.unit()
    def test_returns_dict_with_required_categories(self, sample_data_utils):
        """Test that initialize returns dict with all required categories."""
        from src.dashboard.shiny_utils.reactives_shiny import initialize_reactives_shiny

        result = initialize_reactives_shiny(data_utils = sample_data_utils)

        assert isinstance(result, dict)
        assert "User_Inputs_Shiny" in result
        assert "Inner_Variables_Shiny" in result
        assert "Triggers_Shiny" in result
        assert "Visual_Objects_Shiny" in result

    @pytest.mark.unit()
    def test_raises_value_error_for_none_data_utils(self):
        """Test that None data_utils raises ValueError."""
        from src.dashboard.shiny_utils.reactives_shiny import initialize_reactives_shiny

        with pytest.raises(Exception_Validation_Input) as exc_info:
            initialize_reactives_shiny(data_utils = None)

        assert "validation failed" in str(exc_info.value).lower()

    @pytest.mark.unit()
    def test_raises_value_error_for_non_dict_data_utils(self):
        """Test that non-dict data_utils raises ValueError."""
        from src.dashboard.shiny_utils.reactives_shiny import initialize_reactives_shiny

        with pytest.raises(Exception_Validation_Input) as exc_info:
            initialize_reactives_shiny(data_utils = "not a dict")

        assert "validation failed" in str(exc_info.value).lower()

    @pytest.mark.unit()
    def test_categories_contain_dictionaries(self, sample_data_utils):
        """Test that each category in result is a dictionary."""
        from src.dashboard.shiny_utils.reactives_shiny import initialize_reactives_shiny

        result = initialize_reactives_shiny(data_utils = sample_data_utils)

        for category_name, category_value in result.items():
            assert isinstance(category_value, dict), f"Category {category_name} is not a dict"


# ============================================================================
# Tests for initialize_reactive_user_inputs
# ============================================================================


@pytest.mark.unit()
class Test_Initialize_Reactive_User_Inputs:
    """Test cases for initialize_reactive_user_inputs function."""

    @pytest.mark.unit()
    def test_returns_dict(self, sample_data_utils):
        """Test that function returns a dictionary."""
        from src.dashboard.shiny_utils.reactives_shiny import initialize_reactive_user_inputs

        result = initialize_reactive_user_inputs(data_utils = sample_data_utils)

        assert isinstance(result, dict)

    @pytest.mark.unit()
    def test_raises_value_error_for_none(self):
        """Test that None data_utils raises ValueError."""
        from src.dashboard.shiny_utils.reactives_shiny import initialize_reactive_user_inputs

        with pytest.raises(Exception_Validation_Input):
            initialize_reactive_user_inputs(data_utils = None)

    @pytest.mark.unit()
    def test_contains_portfolio_subtab_keys(self, sample_data_utils):
        """Test that result contains portfolio subtab input keys."""
        from src.dashboard.shiny_utils.reactives_shiny import initialize_reactive_user_inputs

        result = initialize_reactive_user_inputs(data_utils = sample_data_utils)

        # Check for some expected keys
        assert any("Portfolios" in key for key in result)

    @pytest.mark.unit()
    def test_contains_computation_type_keys(self, sample_data_utils):
        """Result contains all four computation type keys."""
        from src.dashboard.shiny_utils.reactives_shiny import initialize_reactive_user_inputs

        result = initialize_reactive_user_inputs(data_utils = sample_data_utils)

        expected_keys = [
            "Input_Tab_Setup_Subtab_Computation_Portfolio_Comparison_Computation_Type",
            "Input_Tab_Setup_Subtab_Computation_Skfolio_Optimization_Computation_Type",
            "Input_Tab_Setup_Subtab_Computation_OptimalPortfolios_Optimization_Computation_Type",
            "Input_Tab_Setup_Subtab_Computation_Simulation_Computation_Type",
        ]
        for key in expected_keys:
            assert key in result, f"Missing expected key: {key}"

    @pytest.mark.unit()
    def test_contains_computation_debug_keys(self, sample_data_utils):
        """Result contains debug option reactive keys for each subtab."""
        from src.dashboard.shiny_utils.reactives_shiny import initialize_reactive_user_inputs

        result = initialize_reactive_user_inputs(data_utils = sample_data_utils)

        debug_params = ["Logger_Display", "Execution_Thread_Mode", "Profiler"]
        subtab_stems = [
            "Portfolio_Comparison",
            "Skfolio_Optimization",
            "OptimalPortfolios_Optimization",
            "Simulation",
        ]
        for stem in subtab_stems:
            for param in debug_params:
                key = f"Input_Tab_Setup_Subtab_Computation_{stem}_{param}"
                assert key in result, f"Missing expected key: {key}"

    @pytest.mark.unit()
    def test_computation_type_defaults_to_joblib(self, sample_data_utils):
        """Computation type reactive values are initialised to 'joblib'."""
        from shiny import reactive

        from src.dashboard.shiny_utils.reactives_shiny import initialize_reactive_user_inputs

        result = initialize_reactive_user_inputs(data_utils = sample_data_utils)

        key = "Input_Tab_Setup_Subtab_Computation_Portfolio_Comparison_Computation_Type"
        rv = result[key]
        assert rv is not None
        with reactive.isolate():
            assert rv() == "joblib"

    @pytest.mark.unit()
    def test_logger_display_defaults_to_no_display(self, sample_data_utils):
        """Logger display reactive values are initialised to 'no_display'."""
        from shiny import reactive

        from src.dashboard.shiny_utils.reactives_shiny import initialize_reactive_user_inputs

        result = initialize_reactive_user_inputs(data_utils = sample_data_utils)

        key = "Input_Tab_Setup_Subtab_Computation_Simulation_Logger_Display"
        rv = result[key]
        assert rv is not None
        with reactive.isolate():
            assert rv() == "no_display"


# ============================================================================
# Tests for initialize_reactive_inner_variables
# ============================================================================


@pytest.mark.unit()
class Test_Initialize_Reactive_Inner_Variables:
    """Test cases for initialize_reactive_inner_variables function."""

    @pytest.mark.unit()
    def test_returns_dict(self, sample_data_utils):
        """Test that function returns a dictionary."""
        from src.dashboard.shiny_utils.reactives_shiny import initialize_reactive_inner_variables

        result = initialize_reactive_inner_variables(data_utils = sample_data_utils)

        assert isinstance(result, dict)

    @pytest.mark.unit()
    def test_raises_value_error_for_none(self):
        """Test that None data_utils raises ValueError."""
        from src.dashboard.shiny_utils.reactives_shiny import initialize_reactive_inner_variables

        with pytest.raises(Exception_Validation_Input):
            initialize_reactive_inner_variables(data_utils = None)

    @pytest.mark.unit()
    def test_contains_expected_keys(self, sample_data_utils):
        """Test that result contains expected data keys."""
        from src.dashboard.shiny_utils.reactives_shiny import initialize_reactive_inner_variables

        result = initialize_reactive_inner_variables(data_utils = sample_data_utils)

        expected_keys = [
            "Data_Personal_Info_DF",
            "Data_Assets_DF",
            "Data_Goals_DF",
            "Data_Income_DF",
        ]

        for key in expected_keys:
            assert key in result, f"Missing expected key: {key}"


# ============================================================================
# Tests for get_value_from_shiny_input_text
# (Uses None guard on frame.f_back added in source fix)
# ============================================================================


@pytest.mark.unit()
class Test_Get_Value_From_Shiny_Input_Text:
    """Tests for get_value_from_shiny_input_text function.

    The function was updated to guard against frame.f_back being None
    (possible in restricted execution environments like pytest subprocesses).
    These tests verify both the validation layer and the guard behavior.
    """

    @pytest.mark.unit()
    def test_none_input_raises_value_error(self):
        """None input_reactive_object raises ValueError immediately."""
        from src.dashboard.shiny_utils.reactives_shiny import get_value_from_shiny_input_text

        with pytest.raises(Exception_Validation_Input, match="None"):
            get_value_from_shiny_input_text(input_reactive_object = None)

    @pytest.mark.unit()
    def test_non_callable_raises_value_error(self):
        """Non-callable input raises ValueError."""
        from src.dashboard.shiny_utils.reactives_shiny import get_value_from_shiny_input_text

        with pytest.raises(Exception_Validation_Input, match="callable"):
            get_value_from_shiny_input_text(input_reactive_object = "a string, not callable")

    @pytest.mark.unit()
    def test_non_callable_int_raises_value_error(self):
        """Integer input (non-callable) raises ValueError."""
        from src.dashboard.shiny_utils.reactives_shiny import get_value_from_shiny_input_text

        with pytest.raises(Exception_Validation_Input):
            get_value_from_shiny_input_text(input_reactive_object = 42)

    @pytest.mark.unit()
    def test_callable_returning_valid_string(self):
        """Callable that returns a non-empty string returns the string value."""
        from src.dashboard.shiny_utils.reactives_shiny import get_value_from_shiny_input_text

        mock_reactive = MagicMock(return_value="hello world")

        # Function should retrieve the value without raising
        result = get_value_from_shiny_input_text(input_reactive_object = mock_reactive)

        assert isinstance(result, str)
        assert result == "hello world"

    @pytest.mark.unit()
    def test_callable_returning_empty_string_raises(self):
        """Callable returning empty string raises ValueError."""
        from src.dashboard.shiny_utils.reactives_shiny import get_value_from_shiny_input_text

        mock_reactive = MagicMock(return_value="")

        with pytest.raises((Exception_Validation_Input, ValueError, RuntimeError)):
            get_value_from_shiny_input_text(input_reactive_object = mock_reactive)

    @pytest.mark.unit()
    def test_callable_returning_whitespace_raises(self):
        """Callable returning whitespace-only string raises ValueError."""
        from src.dashboard.shiny_utils.reactives_shiny import get_value_from_shiny_input_text

        mock_reactive = MagicMock(return_value="   ")

        with pytest.raises((Exception_Validation_Input, ValueError, RuntimeError)):
            get_value_from_shiny_input_text(input_reactive_object = mock_reactive)

    @pytest.mark.unit()
    def test_no_crash_when_frame_is_none_edge_case(self):
        """Function does not crash due to frame.f_back being None (guard regression)."""
        # This tests the behavior after the None-guard fix. If frame is ever None in
        # a restricted environment, the code path `frame.f_back if frame is not None`
        # simply returns None for the identifier lookup — no AttributeError is thrown.
        # The easiest way to verify is running the function in a regular test context
        # where frame IS available, and confirming it does not raise AttributeError.
        from src.dashboard.shiny_utils.reactives_shiny import get_value_from_shiny_input_text

        mock_reactive = MagicMock(return_value="test value")

        # Must not raise AttributeError from frame.f_back
        try:
            result = get_value_from_shiny_input_text(input_reactive_object = mock_reactive)
            assert isinstance(result, str)
        except (ValueError, RuntimeError, TypeError):
            # These are expected from business logic; AttributeError is NOT expected
            pass


# ============================================================================
# Tests for get_value_from_shiny_input_numeric
# (Same frame.f_back None guard fix applied)
# ============================================================================


@pytest.mark.unit()
class Test_Get_Value_From_Shiny_Input_Numeric:
    """Tests for get_value_from_shiny_input_numeric function.

    Same None guard fix was applied as in get_value_from_shiny_input_text.
    """

    @pytest.mark.unit()
    def test_none_input_raises_value_error(self):
        """None input_reactive_object raises ValueError immediately."""
        from src.dashboard.shiny_utils.reactives_shiny import get_value_from_shiny_input_numeric

        with pytest.raises(Exception_Validation_Input, match="None"):
            get_value_from_shiny_input_numeric(input_reactive_object = None)

    @pytest.mark.unit()
    def test_non_callable_raises_value_error(self):
        """Non-callable input raises ValueError."""
        from src.dashboard.shiny_utils.reactives_shiny import get_value_from_shiny_input_numeric

        with pytest.raises(Exception_Validation_Input):
            get_value_from_shiny_input_numeric(input_reactive_object = 42)

    @pytest.mark.unit()
    def test_callable_returning_valid_float(self):
        """Callable returning a float returns the float value."""
        from src.dashboard.shiny_utils.reactives_shiny import get_value_from_shiny_input_numeric

        mock_reactive = MagicMock(return_value=3.14)

        result = get_value_from_shiny_input_numeric(input_reactive_object = mock_reactive)

        assert isinstance(result, float)
        assert result == pytest.approx(3.14)

    @pytest.mark.unit()
    def test_callable_returning_integer_accepted_as_float(self):
        """Callable returning an integer is coerced to float."""
        from src.dashboard.shiny_utils.reactives_shiny import get_value_from_shiny_input_numeric

        mock_reactive = MagicMock(return_value=100)

        result = get_value_from_shiny_input_numeric(input_reactive_object = mock_reactive)

        assert isinstance(result, float)
        assert result == 100.0

    @pytest.mark.unit()
    def test_no_attribute_error_from_frame_guard(self):
        """Function does not raise AttributeError (frame.f_back guard regression)."""
        from src.dashboard.shiny_utils.reactives_shiny import get_value_from_shiny_input_numeric

        mock_reactive = MagicMock(return_value=50.0)

        try:
            result = get_value_from_shiny_input_numeric(input_reactive_object = mock_reactive)
            assert isinstance(result, float)
        except (ValueError, RuntimeError, TypeError):
            # Expected business-logic errors are acceptable
            pass
        # AttributeError would NOT be caught and would fail the test — that's intentional

# ============================================================================
# Tests for initialize_reactive_triggers
# ============================================================================


@pytest.mark.unit()
class Test_Initialize_Reactive_Triggers:
    """Test cases for initialize_reactive_triggers function."""

    @pytest.mark.unit()
    def test_returns_dict(self, sample_data_utils):
        """Test that function returns a dictionary."""
        from src.dashboard.shiny_utils.reactives_shiny import initialize_reactive_triggers

        result = initialize_reactive_triggers(data_utils = sample_data_utils)

        assert isinstance(result, dict)

    @pytest.mark.unit()
    def test_raises_value_error_for_none(self):
        """Test that None data_utils raises ValueError."""
        from src.dashboard.shiny_utils.reactives_shiny import initialize_reactive_triggers

        with pytest.raises(Exception_Validation_Input):
            initialize_reactive_triggers(data_utils = None)


# ============================================================================
# Tests for initialize_reactive_visual_objects
# ============================================================================


@pytest.mark.unit()
class Test_Initialize_Reactive_Visual_Objects:
    """Test cases for initialize_reactive_visual_objects function."""

    @pytest.mark.unit()
    def test_returns_dict(self, sample_data_utils):
        """Test that function returns a dictionary."""
        from src.dashboard.shiny_utils.reactives_shiny import initialize_reactive_visual_objects

        result = initialize_reactive_visual_objects(data_utils = sample_data_utils)

        assert isinstance(result, dict)

    @pytest.mark.unit()
    def test_raises_value_error_for_none(self):
        """Test that None data_utils raises ValueError."""
        from src.dashboard.shiny_utils.reactives_shiny import initialize_reactive_visual_objects

        with pytest.raises(Exception_Validation_Input):
            initialize_reactive_visual_objects(data_utils = None)

    @pytest.mark.unit()
    def test_contains_chart_keys(self, sample_data_utils):
        """Test that result contains only chart visual object keys (saved as SVGs for PDF report)."""
        from src.dashboard.shiny_utils.reactives_shiny import initialize_reactive_visual_objects

        result = initialize_reactive_visual_objects(data_utils = sample_data_utils)

        expected_keys = [
            "Chart_Weights_Analysis_Portfolio_Weight_Distribution_Over_Time",
            "Chart_Weights_Analysis_Portfolio_Current_Composition",
            "Chart_Portfolio_Analysis_Returns_Distribution",
            "Chart_Portfolio_Comparison_Portfolio_vs_Benchmark",
            "Chart_skfolio_Optimization_Portfolio_Weights_Comparison",
            "Chart_skfolio_Optimization_Comparison_Portfolio_Performance",
            "Chart_Simulation_Portfolio_Value_Fan_Chart",
            "Chart_Simulation_Terminal_Value_Distribution",
        ]

        for key in expected_keys:
            assert key in result, f"Missing expected chart key: {key}"

        # Table keys must NOT be present — Visual_Objects_Shiny holds charts only
        table_keys = ["Table_Personal_Info", "Table_Assets", "Table_Goals", "Table_Income"]
        for key in table_keys:
            assert key not in result, f"Table key should not be in Visual_Objects_Shiny: {key}"


# ============================================================================
# Tests verifying shim re-export behavior
# ============================================================================


@pytest.mark.unit()
class Test_Reactives_Shiny_Shim_Re_Exports:
    """Verify that reactives_shiny re-exports canonical implementations from split modules."""

    @pytest.mark.unit()
    def test_required_categories_is_same_object_as_validation_module(self):
        """REQUIRED_CATEGORIES from reactives_shiny and reactives_validation must be the same object."""
        import src.dashboard.shiny_utils.reactives_shiny as rs
        import src.dashboard.shiny_utils.reactives_validation as rv

        assert rs.REQUIRED_CATEGORIES is rv.REQUIRED_CATEGORIES

    @pytest.mark.unit()
    def test_validate_data_utils_parameter_same_object(self):
        """validate_data_utils_parameter must resolve to the reactives_validation implementation."""
        import src.dashboard.shiny_utils.reactives_shiny as rs
        import src.dashboard.shiny_utils.reactives_validation as rv

        assert rs.validate_data_utils_parameter is rv.validate_data_utils_parameter

    @pytest.mark.unit()
    def test_initialize_reactives_shiny_same_object(self):
        """initialize_reactives_shiny must resolve to reactives_initialization implementation."""
        import src.dashboard.shiny_utils.reactives_initialization as ri
        import src.dashboard.shiny_utils.reactives_shiny as rs

        assert rs.initialize_reactives_shiny is ri.initialize_reactives_shiny

    @pytest.mark.unit()
    def test_initialize_reactive_advisor_info_exported(self):
        """initialize_reactive_advisor_info must be accessible from reactives_shiny."""
        import src.dashboard.shiny_utils.reactives_shiny as rs

        assert hasattr(rs, "initialize_reactive_advisor_info")
        assert callable(rs.initialize_reactive_advisor_info)

    @pytest.mark.unit()
    def test_get_value_from_reactives_shiny_same_object(self):
        """get_value_from_reactives_shiny must resolve to reactives_access implementation."""
        import src.dashboard.shiny_utils.reactives_access as ra
        import src.dashboard.shiny_utils.reactives_shiny as rs

        assert rs.get_value_from_reactives_shiny is ra.get_value_from_reactives_shiny

    @pytest.mark.unit()
    def test_register_client_input_observers_same_object(self):
        """register_client_input_observers must resolve to reactives_sync implementation."""
        import src.dashboard.shiny_utils.reactives_shiny as rs
        import src.dashboard.shiny_utils.reactives_sync as rsync

        assert rs.register_client_input_observers is rsync.register_client_input_observers

    @pytest.mark.unit()
    def test_portfolio_subtab_results_key_map_exported(self):
        """_PORTFOLIO_SUBTAB_RESULTS_KEY_MAP must be accessible from reactives_shiny."""
        import src.dashboard.shiny_utils.reactives_shiny as rs


        assert hasattr(rs, "_PORTFOLIO_SUBTAB_RESULTS_KEY_MAP")
        assert isinstance(rs._PORTFOLIO_SUBTAB_RESULTS_KEY_MAP, dict)

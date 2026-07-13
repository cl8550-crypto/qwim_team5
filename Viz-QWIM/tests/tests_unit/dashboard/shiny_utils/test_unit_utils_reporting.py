"""Unit tests for utils_reporting module.

Tests all public functions in
``src/dashboard/shiny_utils/utils_reporting.py``, including:

- Constant validation (frozensets)
- Validation helpers for Data_Clients and Data_Results structures
- get / save core functions for client data and results data
- Ten convenience wrappers for Data_Clients
- Twelve convenience wrappers for Data_Results
- JSON-builder helpers (_coerce_results_value_to_json, build_results_data_json_from_reactives)
- build_client_info_json_from_reactives

Testing Approach:
    - Uses a lightweight ``MockReactiveValue`` helper – no Shiny dependency.
    - All fixtures provide fully-initialised reactives_shiny structures.
    - Each test class focuses on a single public function.
    - Parameterised tests cover boundary / invalid inputs systematically.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import polars as pl
import pytest
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Configuration,
    Exception_Validation_Input,
)


# ============================================================================
# Helper: mock reactive value (no Shiny dependency)
# ============================================================================


class MockReactiveValue:
    """Minimal stand-in for ``shiny.reactive.Value`` used in unit tests."""

    def __init__(self, value=None) -> None:
        """Init."""
        self._value = value

    def get(self):  # noqa: ANN201
        """Return the stored reactive value."""
        return self._value

    def set(self, value) -> None:  # noqa: ANN001
        """Update the stored reactive value."""
        self._value = value


class MockReactiveValueGetRaises:
    """Reactive whose ``get()`` always raises RuntimeError."""

    def get(self):  # noqa: ANN201
        """Raise RuntimeError to simulate a failing get()."""
        raise RuntimeError("simulated get() failure")

    def set(self, value) -> None:  # noqa: ANN001
        """Accept a value (no-op in this stub)."""
        pass


class MockReactiveValueSetRaises:
    """Reactive whose ``set()`` always raises RuntimeError."""

    def __init__(self, value=None) -> None:
        """Init."""
        self._value = value

    def get(self):  # noqa: ANN201
        """Return the stored value."""
        return self._value

    def set(self, value) -> None:  # noqa: ANN001
        """Raise RuntimeError to simulate a failing set()."""
        raise RuntimeError("simulated set() failure")


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture()
def data_clients_structure():
    """Return a minimal but fully-valid ``Data_Clients`` sub-dict."""
    return {
        "Single_Or_Couple": MockReactiveValue("Single"),
        "Client_Primary": {
            "Personal_Info": MockReactiveValue(None),
            "Assets": MockReactiveValue(None),
            "Goals": MockReactiveValue(None),
            "Income": MockReactiveValue(None),
        },
        "Client_Partner": {
            "Personal_Info": MockReactiveValue(None),
            "Assets": MockReactiveValue(None),
            "Goals": MockReactiveValue(None),
            "Income": MockReactiveValue(None),
        },
        "Clients_Combined": {
            "Assets": MockReactiveValue(None),
            "Goals": MockReactiveValue(None),
            "Income": MockReactiveValue(None),
        },
    }


@pytest.fixture()
def data_results_structure():
    """Return a minimal but fully-valid ``Data_Results`` sub-dict."""
    return {
        "Portfolio_Analysis_Inputs": MockReactiveValue(None),
        "Portfolio_Analysis_Outputs": MockReactiveValue(None),
        "Portfolio_Comparison_Inputs": MockReactiveValue(None),
        "Portfolio_Comparison_Outputs": MockReactiveValue(None),
        "Weights_Analysis_Inputs": MockReactiveValue(None),
        "Weights_Analysis_Outputs": MockReactiveValue(None),
        "Portfolio_Optimization_Skfolio_Inputs": MockReactiveValue(None),
        "Portfolio_Optimization_Skfolio_Outputs": MockReactiveValue(None),
        "Portfolio_Optimization_OptimalPortfolios_Inputs": MockReactiveValue(None),
        "Portfolio_Optimization_OptimalPortfolios_Outputs": MockReactiveValue(None),
        "Portfolio_Simulation_Inputs": MockReactiveValue(None),
        "Portfolio_Simulation_Outputs": MockReactiveValue(None),
    }


@pytest.fixture()
def reactives_with_clients(data_clients_structure):
    """Full ``reactives_shiny`` dict with Data_Clients populated."""
    return {"Data_Clients": data_clients_structure}


@pytest.fixture()
def reactives_with_results(data_results_structure):
    """Full ``reactives_shiny`` dict with Data_Results populated."""
    return {"Data_Results": data_results_structure}


@pytest.fixture()
def reactives_full(data_clients_structure, data_results_structure):
    """Full ``reactives_shiny`` dict with both categories populated."""
    return {
        "Data_Clients": data_clients_structure,
        "Data_Results": data_results_structure,
    }


@pytest.fixture()
def sample_df():
    """Small Polars DataFrame used as test data value."""
    return pl.DataFrame({"col_a": [1, 2, 3], "col_b": ["x", "y", "z"]})


# ============================================================================
# 1. Constants
# ============================================================================


@pytest.mark.unit()
class Test_Valid_Client_Constants:
    """Verify constant frozensets have the expected contents."""

    @pytest.mark.unit()
    def test_valid_client_levels_contains_expected_values(self):
        """Test that valid client levels contains expected values."""
        from src.dashboard.shiny_utils.utils_reporting import VALID_CLIENT_LEVELS

        assert "Client_Primary" in VALID_CLIENT_LEVELS
        assert "Client_Partner" in VALID_CLIENT_LEVELS
        assert "Clients_Combined" in VALID_CLIENT_LEVELS
        assert len(VALID_CLIENT_LEVELS) == 3

    @pytest.mark.unit()
    def test_valid_client_data_categories_per_client(self):
        """Test that valid client data categories per client."""
        from src.dashboard.shiny_utils.utils_reporting import (
            VALID_CLIENT_DATA_CATEGORIES_PER_CLIENT,
        )

        assert "Personal_Info" in VALID_CLIENT_DATA_CATEGORIES_PER_CLIENT
        assert "Assets" in VALID_CLIENT_DATA_CATEGORIES_PER_CLIENT
        assert "Goals" in VALID_CLIENT_DATA_CATEGORIES_PER_CLIENT
        assert "Income" in VALID_CLIENT_DATA_CATEGORIES_PER_CLIENT
        assert len(VALID_CLIENT_DATA_CATEGORIES_PER_CLIENT) == 4

    @pytest.mark.unit()
    def test_valid_client_data_categories_combined_excludes_personal_info(self):
        """Test that valid client data categories combined excludes personal info."""
        from src.dashboard.shiny_utils.utils_reporting import (
            VALID_CLIENT_DATA_CATEGORIES_COMBINED,
        )

        assert "Personal_Info" not in VALID_CLIENT_DATA_CATEGORIES_COMBINED
        assert "Assets" in VALID_CLIENT_DATA_CATEGORIES_COMBINED
        assert "Goals" in VALID_CLIENT_DATA_CATEGORIES_COMBINED
        assert "Income" in VALID_CLIENT_DATA_CATEGORIES_COMBINED
        assert len(VALID_CLIENT_DATA_CATEGORIES_COMBINED) == 3

    @pytest.mark.unit()
    def test_valid_single_or_couple_values(self):
        """Test that valid single or couple values."""
        from src.dashboard.shiny_utils.utils_reporting import VALID_SINGLE_OR_COUPLE_VALUES

        assert "Single" in VALID_SINGLE_OR_COUPLE_VALUES
        assert "Couple" in VALID_SINGLE_OR_COUPLE_VALUES
        assert len(VALID_SINGLE_OR_COUPLE_VALUES) == 2


@pytest.mark.unit()
class Test_Valid_Results_Constants:
    """Verify VALID_RESULTS_SUBTAB_KEYS frozenset has the expected 12 entries."""

    @pytest.mark.unit()
    def test_results_subtab_keys_count(self):
        """Test that results subtab keys count."""
        from src.dashboard.shiny_utils.utils_reporting import VALID_RESULTS_SUBTAB_KEYS

        assert len(VALID_RESULTS_SUBTAB_KEYS) == 12

    @pytest.mark.parametrize(
        "key",
        [
            "Portfolio_Analysis_Inputs",
            "Portfolio_Analysis_Outputs",
            "Portfolio_Comparison_Inputs",
            "Portfolio_Comparison_Outputs",
            "Weights_Analysis_Inputs",
            "Weights_Analysis_Outputs",
            "Portfolio_Optimization_Skfolio_Inputs",
            "Portfolio_Optimization_Skfolio_Outputs",
            "Portfolio_Optimization_OptimalPortfolios_Inputs",
            "Portfolio_Optimization_OptimalPortfolios_Outputs",
            "Portfolio_Simulation_Inputs",
            "Portfolio_Simulation_Outputs",
        ],
    )
    @pytest.mark.unit()
    def test_all_expected_keys_present(self, key):
        """Test that all expected keys present."""
        from src.dashboard.shiny_utils.utils_reporting import VALID_RESULTS_SUBTAB_KEYS

        assert key in VALID_RESULTS_SUBTAB_KEYS


# ============================================================================
# 2. validate_data_clients_in_reactives
# ============================================================================


@pytest.mark.unit()
class Test_Validate_Data_Clients_In_Reactives:
    """Tests for ``validate_data_clients_in_reactives``."""

    @pytest.mark.unit()
    def test_valid_structure_returns_true(self, reactives_with_clients):
        """Test that valid structure returns true."""
        from src.dashboard.shiny_utils.utils_reporting import validate_data_clients_in_reactives

        is_valid, msg = validate_data_clients_in_reactives(reactives_shiny = reactives_with_clients)

        assert is_valid is True
        assert msg == ""

    @pytest.mark.unit()
    def test_none_returns_false(self):
        """Test that none returns false."""
        from src.dashboard.shiny_utils.utils_reporting import validate_data_clients_in_reactives

        is_valid, msg = validate_data_clients_in_reactives(reactives_shiny = None)

        assert is_valid is False
        assert "None" in msg

    @pytest.mark.unit()
    def test_non_dict_returns_false(self):
        """Test that non dict returns false."""
        from src.dashboard.shiny_utils.utils_reporting import validate_data_clients_in_reactives

        is_valid, msg = validate_data_clients_in_reactives(reactives_shiny = "not a dict")

        assert is_valid is False
        assert "dictionary" in msg.lower()

    @pytest.mark.unit()
    def test_missing_data_clients_key_returns_false(self):
        """Test that missing data clients key returns false."""
        from src.dashboard.shiny_utils.utils_reporting import validate_data_clients_in_reactives

        is_valid, msg = validate_data_clients_in_reactives(reactives_shiny = {"Other_Category": {}})

        assert is_valid is False
        assert "Data_Clients" in msg

    @pytest.mark.unit()
    def test_data_clients_not_dict_returns_false(self):
        """Test that data clients not dict returns false."""
        from src.dashboard.shiny_utils.utils_reporting import validate_data_clients_in_reactives

        is_valid, msg = validate_data_clients_in_reactives(reactives_shiny = {"Data_Clients": "not a dict"})

        assert is_valid is False
        assert "dictionary" in msg.lower()

    @pytest.mark.unit()
    def test_missing_single_or_couple_returns_false(self):
        """Test that missing single or couple returns false."""
        from src.dashboard.shiny_utils.utils_reporting import validate_data_clients_in_reactives

        is_valid, msg = validate_data_clients_in_reactives(
            reactives_shiny = {
                "Data_Clients": {
                    "Client_Primary": {},
                    "Client_Partner": {},
                    "Clients_Combined": {},
                    # No "Single_Or_Couple"
                }
            }
        )

        assert is_valid is False
        assert "Single_Or_Couple" in msg

    @pytest.mark.unit()
    def test_missing_sub_level_returns_false(self):
        """Test that missing sub level returns false."""
        from src.dashboard.shiny_utils.utils_reporting import validate_data_clients_in_reactives

        is_valid, msg = validate_data_clients_in_reactives(
            reactives_shiny = {
                "Data_Clients": {
                    "Single_Or_Couple": MockReactiveValue("Single"),
                    "Client_Primary": {},
                    # Missing Client_Partner and Clients_Combined
                }
            }
        )

        assert is_valid is False
        assert "Client_Partner" in msg or "Clients_Combined" in msg

    @pytest.mark.unit()
    def test_sub_level_not_dict_returns_false(self):
        """Test that sub level not dict returns false."""
        from src.dashboard.shiny_utils.utils_reporting import validate_data_clients_in_reactives

        is_valid, msg = validate_data_clients_in_reactives(
            reactives_shiny = {
                "Data_Clients": {
                    "Single_Or_Couple": MockReactiveValue("Single"),
                    "Client_Primary": "should be a dict",
                    "Client_Partner": {},
                    "Clients_Combined": {},
                }
            }
        )

        assert is_valid is False
        assert "dictionary" in msg.lower()


# ============================================================================
# 3. validate_client_level_name
# ============================================================================


@pytest.mark.unit()
class Test_Validate_Client_Level_Name:
    """Tests for ``validate_client_level_name``."""

    @pytest.mark.parametrize(
        "level",
        ["Client_Primary", "Client_Partner", "Clients_Combined"],
    )
    @pytest.mark.unit()
    def test_valid_levels_return_true(self, level):
        """Test that valid levels return true."""
        from src.dashboard.shiny_utils.utils_reporting import validate_client_level_name

        is_valid, msg = validate_client_level_name(client_level = level)

        assert is_valid is True
        assert msg == ""

    @pytest.mark.unit()
    def test_none_returns_false(self):
        """Test that none returns false."""
        from src.dashboard.shiny_utils.utils_reporting import validate_client_level_name

        is_valid, msg = validate_client_level_name(client_level = None)

        assert is_valid is False
        assert "None" in msg

    @pytest.mark.unit()
    def test_empty_string_returns_false(self):
        """Test that empty string returns false."""
        from src.dashboard.shiny_utils.utils_reporting import validate_client_level_name

        is_valid, msg = validate_client_level_name(client_level = "")

        assert is_valid is False
        assert "empty" in msg.lower()

    @pytest.mark.unit()
    def test_non_string_returns_false(self):
        """Test that non string returns false."""
        from src.dashboard.shiny_utils.utils_reporting import validate_client_level_name

        is_valid, msg = validate_client_level_name(client_level = 42)

        assert is_valid is False
        assert "string" in msg.lower()

    @pytest.mark.unit()
    def test_unknown_level_returns_false(self):
        """Test that unknown level returns false."""
        from src.dashboard.shiny_utils.utils_reporting import validate_client_level_name

        is_valid, msg = validate_client_level_name(client_level = "Client_Unknown")

        assert is_valid is False
        assert "Client_Unknown" in msg


# ============================================================================
# 4. validate_client_data_category_name
# ============================================================================


@pytest.mark.unit()
class Test_Validate_Client_Data_Category_Name:
    """Tests for ``validate_client_data_category_name``."""

    @pytest.mark.parametrize(
        "category",
        ["Personal_Info", "Assets", "Goals", "Income"],
    )
    @pytest.mark.unit()
    def test_valid_categories_without_level(self, category):
        """Test that valid categories without level."""
        from src.dashboard.shiny_utils.utils_reporting import (
            validate_client_data_category_name,
        )

        is_valid, msg = validate_client_data_category_name(data_category = category)

        assert is_valid is True
        assert msg == ""

    @pytest.mark.parametrize(
        "category",
        ["Assets", "Goals", "Income"],
    )
    @pytest.mark.unit()
    def test_valid_categories_for_clients_combined(self, category):
        """Test that valid categories for clients combined."""
        from src.dashboard.shiny_utils.utils_reporting import (
            validate_client_data_category_name,
        )

        is_valid, msg = validate_client_data_category_name(data_category = category, client_level = "Clients_Combined")

        assert is_valid is True

    @pytest.mark.unit()
    def test_personal_info_invalid_for_clients_combined(self):
        """Test that personal info invalid for clients combined."""
        from src.dashboard.shiny_utils.utils_reporting import (
            validate_client_data_category_name,
        )

        is_valid, msg = validate_client_data_category_name(data_category = "Personal_Info", client_level = "Clients_Combined")

        assert is_valid is False
        assert "Personal_Info" in msg

    @pytest.mark.unit()
    def test_none_category_returns_false(self):
        """Test that none category returns false."""
        from src.dashboard.shiny_utils.utils_reporting import (
            validate_client_data_category_name,
        )

        is_valid, msg = validate_client_data_category_name(data_category = None)

        assert is_valid is False
        assert "None" in msg

    @pytest.mark.unit()
    def test_empty_string_returns_false(self):
        """Test that empty string returns false."""
        from src.dashboard.shiny_utils.utils_reporting import (
            validate_client_data_category_name,
        )

        is_valid, msg = validate_client_data_category_name(data_category = "")

        assert is_valid is False
        assert "empty" in msg.lower()

    @pytest.mark.unit()
    def test_unknown_category_returns_false(self):
        """Test that unknown category returns false."""
        from src.dashboard.shiny_utils.utils_reporting import (
            validate_client_data_category_name,
        )

        is_valid, msg = validate_client_data_category_name(data_category = "Investments")

        assert is_valid is False
        assert "Investments" in msg


# ============================================================================
# 5. validate_data_results_in_reactives
# ============================================================================


@pytest.mark.unit()
class Test_Validate_Data_Results_In_Reactives:
    """Tests for ``validate_data_results_in_reactives``."""

    @pytest.mark.unit()
    def test_valid_structure_returns_true(self, reactives_with_results):
        """Test that valid structure returns true."""
        from src.dashboard.shiny_utils.utils_reporting import validate_data_results_in_reactives

        is_valid, msg = validate_data_results_in_reactives(reactives_shiny = reactives_with_results)

        assert is_valid is True
        assert msg == ""

    @pytest.mark.unit()
    def test_none_returns_false(self):
        """Test that none returns false."""
        from src.dashboard.shiny_utils.utils_reporting import validate_data_results_in_reactives

        is_valid, msg = validate_data_results_in_reactives(reactives_shiny = None)

        assert is_valid is False
        assert "None" in msg

    @pytest.mark.unit()
    def test_non_dict_returns_false(self):
        """Test that non dict returns false."""
        from src.dashboard.shiny_utils.utils_reporting import validate_data_results_in_reactives

        is_valid, msg = validate_data_results_in_reactives(reactives_shiny = "not a dict")

        assert is_valid is False
        assert "dictionary" in msg.lower()

    @pytest.mark.unit()
    def test_missing_data_results_key_returns_false(self):
        """Test that missing data results key returns false."""
        from src.dashboard.shiny_utils.utils_reporting import validate_data_results_in_reactives

        is_valid, msg = validate_data_results_in_reactives(reactives_shiny = {"Other_Category": {}})

        assert is_valid is False
        assert "Data_Results" in msg

    @pytest.mark.unit()
    def test_data_results_not_dict_returns_false(self):
        """Test that data results not dict returns false."""
        from src.dashboard.shiny_utils.utils_reporting import validate_data_results_in_reactives

        is_valid, msg = validate_data_results_in_reactives(reactives_shiny = {"Data_Results": "list-like"})

        assert is_valid is False
        assert "dictionary" in msg.lower()


# ============================================================================
# 6. validate_results_subtab_key
# ============================================================================


@pytest.mark.unit()
class Test_Validate_Results_Subtab_Key:
    """Tests for ``validate_results_subtab_key``."""

    @pytest.mark.parametrize(
        "key",
        [
            "Portfolio_Analysis_Inputs",
            "Portfolio_Analysis_Outputs",
            "Portfolio_Comparison_Inputs",
            "Portfolio_Comparison_Outputs",
            "Weights_Analysis_Inputs",
            "Weights_Analysis_Outputs",
            "Portfolio_Optimization_Skfolio_Inputs",
            "Portfolio_Optimization_Skfolio_Outputs",
            "Portfolio_Simulation_Inputs",
            "Portfolio_Simulation_Outputs",
        ],
    )
    @pytest.mark.unit()
    def test_all_valid_keys_return_true(self, key):
        """Test that all valid keys return true."""
        from src.dashboard.shiny_utils.utils_reporting import validate_results_subtab_key

        is_valid, msg = validate_results_subtab_key(subtab_key = key)

        assert is_valid is True
        assert msg == ""

    @pytest.mark.unit()
    def test_none_returns_false(self):
        """Test that none returns false."""
        from src.dashboard.shiny_utils.utils_reporting import validate_results_subtab_key

        is_valid, msg = validate_results_subtab_key(subtab_key = None)

        assert is_valid is False
        assert "None" in msg

    @pytest.mark.unit()
    def test_empty_string_returns_false(self):
        """Test that empty string returns false."""
        from src.dashboard.shiny_utils.utils_reporting import validate_results_subtab_key

        is_valid, msg = validate_results_subtab_key(subtab_key = "")

        assert is_valid is False
        assert "empty" in msg.lower()

    @pytest.mark.unit()
    def test_non_string_returns_false(self):
        """Test that non string returns false."""
        from src.dashboard.shiny_utils.utils_reporting import validate_results_subtab_key

        is_valid, msg = validate_results_subtab_key(subtab_key = 99)

        assert is_valid is False
        assert "string" in msg.lower()

    @pytest.mark.unit()
    def test_unknown_key_returns_false(self):
        """Test that unknown key returns false."""
        from src.dashboard.shiny_utils.utils_reporting import validate_results_subtab_key

        is_valid, msg = validate_results_subtab_key(subtab_key = "Unknown_Key")

        assert is_valid is False
        assert "Unknown_Key" in msg


# ============================================================================
# 7. get_single_or_couple_from_reactives
# ============================================================================


@pytest.mark.unit()
class Test_Get_Single_Or_Couple_From_Reactives:
    """Tests for ``get_single_or_couple_from_reactives``."""

    @pytest.mark.unit()
    def test_returns_single_when_stored(self, reactives_with_clients):
        """Test that returns single when stored."""
        from src.dashboard.shiny_utils.utils_reporting import (
            get_single_or_couple_from_reactives,
        )

        result = get_single_or_couple_from_reactives(reactives_shiny = reactives_with_clients)

        assert result == "Single"

    @pytest.mark.unit()
    def test_returns_couple_when_stored_couple(self, reactives_with_clients):
        """Test that returns couple when stored couple."""
        from src.dashboard.shiny_utils.utils_reporting import (
            get_single_or_couple_from_reactives,
        )

        reactives_with_clients["Data_Clients"]["Single_Or_Couple"].set("Couple")

        result = get_single_or_couple_from_reactives(reactives_shiny = reactives_with_clients)

        assert result == "Couple"

    @pytest.mark.unit()
    def test_returns_single_when_reactive_value_is_none(self, reactives_with_clients):
        """When the reactive holds None, the function defaults to 'Single'."""
        from src.dashboard.shiny_utils.utils_reporting import (
            get_single_or_couple_from_reactives,
        )

        reactives_with_clients["Data_Clients"]["Single_Or_Couple"].set(None)

        result = get_single_or_couple_from_reactives(reactives_shiny = reactives_with_clients)

        assert result == "Single"

    @pytest.mark.unit()
    def test_raises_value_error_when_structure_invalid(self):
        """Test that raises value error when structure invalid."""
        from src.dashboard.shiny_utils.utils_reporting import (
            get_single_or_couple_from_reactives,
        )

        with pytest.raises(Exception_Validation_Input):
            get_single_or_couple_from_reactives(reactives_shiny = None)

    @pytest.mark.unit()
    def test_raises_value_error_when_reactive_has_no_get(self, reactives_with_clients):
        """Test that raises value error when reactive has no get."""
        from src.dashboard.shiny_utils.utils_reporting import (
            get_single_or_couple_from_reactives,
        )

        # Replace with an object without .get()
        reactives_with_clients["Data_Clients"]["Single_Or_Couple"] = object()

        with pytest.raises(Exception_Validation_Input, match="'get' method"):
            get_single_or_couple_from_reactives(reactives_shiny = reactives_with_clients)

    @pytest.mark.unit()
    def test_raises_runtime_error_when_get_raises(self, reactives_with_clients):
        """Test that raises runtime error when get raises."""
        from src.dashboard.shiny_utils.utils_reporting import (
            get_single_or_couple_from_reactives,
        )

        reactives_with_clients["Data_Clients"]["Single_Or_Couple"] = (
            MockReactiveValueGetRaises()
        )

        with pytest.raises(Exception_Configuration):
            get_single_or_couple_from_reactives(reactives_shiny = reactives_with_clients)


# ============================================================================
# 8. update_single_or_couple_in_reactives
# ============================================================================


@pytest.mark.unit()
class Test_Update_Single_Or_Couple_In_Reactives:
    """Tests for ``update_single_or_couple_in_reactives``."""

    @pytest.mark.parametrize("value", ["Single", "Couple"])
    @pytest.mark.unit()
    def test_valid_values_update_and_return_reactives(self, reactives_with_clients, value):
        """Test that valid values update and return reactives."""
        from src.dashboard.shiny_utils.utils_reporting import (
            update_single_or_couple_in_reactives,
        )

        result = update_single_or_couple_in_reactives(reactives_shiny = reactives_with_clients, single_or_couple = value)

        assert result is reactives_with_clients
        assert reactives_with_clients["Data_Clients"]["Single_Or_Couple"].get() == value

    @pytest.mark.unit()
    def test_raises_value_error_for_none(self, reactives_with_clients):
        """Test that raises value error for none."""
        from src.dashboard.shiny_utils.utils_reporting import (
            update_single_or_couple_in_reactives,
        )

        with pytest.raises(Exception_Validation_Input):
            update_single_or_couple_in_reactives(reactives_shiny = reactives_with_clients, single_or_couple = None)

    @pytest.mark.unit()
    def test_raises_value_error_for_non_string(self, reactives_with_clients):
        """Test that raises value error for non string."""
        from src.dashboard.shiny_utils.utils_reporting import (
            update_single_or_couple_in_reactives,
        )

        with pytest.raises(Exception_Validation_Input):
            update_single_or_couple_in_reactives(reactives_shiny = reactives_with_clients, single_or_couple = 1)

    @pytest.mark.unit()
    def test_raises_value_error_for_invalid_value(self, reactives_with_clients):
        """Test that raises value error for invalid value."""
        from src.dashboard.shiny_utils.utils_reporting import (
            update_single_or_couple_in_reactives,
        )

        with pytest.raises(Exception_Validation_Input, match="Invalid"):
            update_single_or_couple_in_reactives(reactives_shiny = reactives_with_clients, single_or_couple = "Trio")

    @pytest.mark.unit()
    def test_raises_value_error_when_reactive_has_no_set(self, reactives_with_clients):
        """Test that raises value error when reactive has no set."""
        from src.dashboard.shiny_utils.utils_reporting import (
            update_single_or_couple_in_reactives,
        )

        reactives_with_clients["Data_Clients"]["Single_Or_Couple"] = object()

        with pytest.raises(Exception_Validation_Input, match="'set' method"):
            update_single_or_couple_in_reactives(reactives_shiny = reactives_with_clients, single_or_couple = "Single")

    @pytest.mark.unit()
    def test_raises_runtime_error_when_set_raises(self, reactives_with_clients):
        """Test that raises runtime error when set raises."""
        from src.dashboard.shiny_utils.utils_reporting import (
            update_single_or_couple_in_reactives,
        )

        reactives_with_clients["Data_Clients"]["Single_Or_Couple"] = (
            MockReactiveValueSetRaises("Single")
        )

        with pytest.raises(Exception_Configuration):
            update_single_or_couple_in_reactives(reactives_shiny = reactives_with_clients, single_or_couple = "Couple")


# ============================================================================
# 9. get_client_data_from_reactives
# ============================================================================


@pytest.mark.unit()
class Test_Get_Client_Data_From_Reactives:
    """Tests for ``get_client_data_from_reactives``."""

    @pytest.mark.unit()
    def test_returns_none_when_not_yet_populated(self, reactives_with_clients):
        """Test that returns none when not yet populated."""
        from src.dashboard.shiny_utils.utils_reporting import get_client_data_from_reactives

        result = get_client_data_from_reactives(
            reactives_shiny = reactives_with_clients, client_level = "Client_Primary", data_category = "Personal_Info"
        )

        assert result is None

    @pytest.mark.unit()
    def test_returns_stored_dataframe(self, reactives_with_clients, sample_df):
        """Test that returns stored dataframe."""
        from src.dashboard.shiny_utils.utils_reporting import get_client_data_from_reactives

        reactives_with_clients["Data_Clients"]["Client_Primary"]["Assets"].set(sample_df)

        result = get_client_data_from_reactives(
            reactives_shiny = reactives_with_clients, client_level = "Client_Primary", data_category = "Assets"
        )

        assert isinstance(result, pl.DataFrame)
        assert result.shape == sample_df.shape

    @pytest.mark.unit()
    def test_raises_for_invalid_structure(self):
        """Test that raises for invalid structure."""
        from src.dashboard.shiny_utils.utils_reporting import get_client_data_from_reactives

        with pytest.raises(Exception_Validation_Input):
            get_client_data_from_reactives(reactives_shiny = None, client_level = "Client_Primary", data_category = "Assets")

    @pytest.mark.unit()
    def test_raises_for_invalid_client_level(self, reactives_with_clients):
        """Test that raises for invalid client level."""
        from src.dashboard.shiny_utils.utils_reporting import get_client_data_from_reactives

        with pytest.raises(Exception_Validation_Input):
            get_client_data_from_reactives(
                reactives_shiny = reactives_with_clients, client_level = "Client_Nonexistent", data_category = "Assets"
            )

    @pytest.mark.unit()
    def test_raises_for_personal_info_on_clients_combined(self, reactives_with_clients):
        """Test that raises for personal info on clients combined."""
        from src.dashboard.shiny_utils.utils_reporting import get_client_data_from_reactives

        with pytest.raises(Exception_Validation_Input):
            get_client_data_from_reactives(
                reactives_shiny = reactives_with_clients, client_level = "Clients_Combined", data_category = "Personal_Info"
            )

    @pytest.mark.unit()
    def test_raises_key_error_when_category_missing_from_sub_level(
        self, reactives_with_clients
    ):
        """Test that raises key error when category missing from sub level."""
        from src.dashboard.shiny_utils.utils_reporting import get_client_data_from_reactives

        # Remove a key to simulate a misconfigured structure
        del reactives_with_clients["Data_Clients"]["Client_Primary"]["Income"]

        with pytest.raises(KeyError):
            get_client_data_from_reactives(
                reactives_shiny = reactives_with_clients, client_level = "Client_Primary", data_category = "Income"
            )

    @pytest.mark.unit()
    def test_raises_value_error_when_reactive_has_no_get(self, reactives_with_clients):
        """Test that raises value error when reactive has no get."""
        from src.dashboard.shiny_utils.utils_reporting import get_client_data_from_reactives

        reactives_with_clients["Data_Clients"]["Client_Primary"]["Goals"] = object()

        with pytest.raises(Exception_Validation_Input, match="'get' method"):
            get_client_data_from_reactives(
                reactives_shiny = reactives_with_clients, client_level = "Client_Primary", data_category = "Goals"
            )

    @pytest.mark.unit()
    def test_raises_runtime_error_when_get_raises(self, reactives_with_clients):
        """Test that raises runtime error when get raises."""
        from src.dashboard.shiny_utils.utils_reporting import get_client_data_from_reactives

        reactives_with_clients["Data_Clients"]["Client_Primary"]["Goals"] = (
            MockReactiveValueGetRaises()
        )

        with pytest.raises(Exception_Configuration):
            get_client_data_from_reactives(
                reactives_shiny = reactives_with_clients, client_level = "Client_Primary", data_category = "Goals"
            )


# ============================================================================
# 10. save_client_data_to_reactives
# ============================================================================


@pytest.mark.unit()
class Test_Save_Client_Data_To_Reactives:
    """Tests for ``save_client_data_to_reactives``."""

    @pytest.mark.unit()
    def test_saves_dataframe_and_returns_reactives(self, reactives_with_clients, sample_df):
        """Test that saves dataframe and returns reactives."""
        from src.dashboard.shiny_utils.utils_reporting import save_client_data_to_reactives

        result = save_client_data_to_reactives(
            reactives_shiny = reactives_with_clients, client_level = "Client_Primary", data_category = "Assets", data_value = sample_df
        )

        assert result is reactives_with_clients
        stored = reactives_with_clients["Data_Clients"]["Client_Primary"]["Assets"].get()
        assert isinstance(stored, pl.DataFrame)
        assert stored.shape == sample_df.shape

    @pytest.mark.unit()
    def test_saves_none_to_clear_entry(self, reactives_with_clients, sample_df):
        """Test that saves none to clear entry."""
        from src.dashboard.shiny_utils.utils_reporting import save_client_data_to_reactives

        # First set a value, then clear it
        reactives_with_clients["Data_Clients"]["Client_Primary"]["Assets"].set(sample_df)
        save_client_data_to_reactives(
            reactives_shiny = reactives_with_clients, client_level = "Client_Primary", data_category = "Assets", data_value = None
        )

        stored = reactives_with_clients["Data_Clients"]["Client_Primary"]["Assets"].get()
        assert stored is None

    @pytest.mark.unit()
    def test_raises_for_invalid_data_value_type(self, reactives_with_clients):
        """Test that raises for invalid data value type."""
        from src.dashboard.shiny_utils.utils_reporting import save_client_data_to_reactives

        with pytest.raises(Exception_Validation_Input, match="Polars DataFrame"):
            save_client_data_to_reactives(
                reactives_shiny = reactives_with_clients, client_level = "Client_Primary", data_category = "Assets", data_value = {"not": "a DataFrame"}
            )

    @pytest.mark.unit()
    def test_raises_for_invalid_structure(self):
        """Test that raises for invalid structure."""
        from src.dashboard.shiny_utils.utils_reporting import save_client_data_to_reactives

        with pytest.raises(Exception_Validation_Input):
            save_client_data_to_reactives(reactives_shiny = None, client_level = "Client_Primary", data_category = "Assets", data_value = None)

    @pytest.mark.unit()
    def test_raises_runtime_error_when_set_raises(self, reactives_with_clients):
        """Test that raises runtime error when set raises."""
        from src.dashboard.shiny_utils.utils_reporting import save_client_data_to_reactives

        reactives_with_clients["Data_Clients"]["Client_Primary"]["Assets"] = (
            MockReactiveValueSetRaises(None)
        )

        with pytest.raises(Exception_Configuration):
            save_client_data_to_reactives(
                reactives_shiny = reactives_with_clients, client_level = "Client_Primary", data_category = "Assets", data_value = None
            )


# ============================================================================
# 11. Data_Clients convenience wrappers
# ============================================================================


@pytest.mark.unit()
class Test_Client_Convenience_Wrappers:
    """Tests for the five save_client_* convenience wrappers."""

    @pytest.mark.unit()
    def test_save_client_personal_info_stores_data(self, reactives_with_clients, sample_df):
        """Test that save client personal info stores data."""
        from src.dashboard.shiny_utils.utils_reporting import (
            save_client_personal_info_to_reactives,
        )

        save_client_personal_info_to_reactives(reactives_shiny = reactives_with_clients, client_level = "Client_Primary", data_personal_info = sample_df)

        stored = reactives_with_clients["Data_Clients"]["Client_Primary"]["Personal_Info"].get()
        assert isinstance(stored, pl.DataFrame)

    @pytest.mark.unit()
    def test_save_client_personal_info_rejects_clients_combined(self, reactives_with_clients):
        """Test that save client personal info rejects clients combined."""
        from src.dashboard.shiny_utils.utils_reporting import (
            save_client_personal_info_to_reactives,
        )

        with pytest.raises(Exception_Validation_Input, match="Personal_Info"):
            save_client_personal_info_to_reactives(
                reactives_shiny = reactives_with_clients, client_level = "Clients_Combined", data_personal_info = None
            )

    @pytest.mark.unit()
    def test_save_client_assets_stores_data(self, reactives_with_clients, sample_df):
        """Test that save client assets stores data."""
        from src.dashboard.shiny_utils.utils_reporting import save_client_assets_to_reactives

        save_client_assets_to_reactives(reactives_shiny = reactives_with_clients, client_level = "Client_Partner", data_assets = sample_df)

        stored = reactives_with_clients["Data_Clients"]["Client_Partner"]["Assets"].get()
        assert isinstance(stored, pl.DataFrame)

    @pytest.mark.unit()
    def test_save_client_assets_works_for_clients_combined(self, reactives_with_clients, sample_df):
        """Test that save client assets works for clients combined."""
        from src.dashboard.shiny_utils.utils_reporting import save_client_assets_to_reactives

        save_client_assets_to_reactives(reactives_shiny = reactives_with_clients, client_level = "Clients_Combined", data_assets = sample_df)

        stored = reactives_with_clients["Data_Clients"]["Clients_Combined"]["Assets"].get()
        assert isinstance(stored, pl.DataFrame)

    @pytest.mark.unit()
    def test_save_client_goals_stores_data(self, reactives_with_clients, sample_df):
        """Test that save client goals stores data."""
        from src.dashboard.shiny_utils.utils_reporting import save_client_goals_to_reactives

        save_client_goals_to_reactives(reactives_shiny = reactives_with_clients, client_level = "Client_Primary", data_goals = sample_df)

        stored = reactives_with_clients["Data_Clients"]["Client_Primary"]["Goals"].get()
        assert isinstance(stored, pl.DataFrame)

    @pytest.mark.unit()
    def test_save_client_income_stores_data(self, reactives_with_clients, sample_df):
        """Test that save client income stores data."""
        from src.dashboard.shiny_utils.utils_reporting import save_client_income_to_reactives

        save_client_income_to_reactives(reactives_shiny = reactives_with_clients, client_level = "Clients_Combined", data_income = sample_df)

        stored = reactives_with_clients["Data_Clients"]["Clients_Combined"]["Income"].get()
        assert isinstance(stored, pl.DataFrame)

    @pytest.mark.unit()
    def test_save_clients_combined_data_stores_goals(self, reactives_with_clients, sample_df):
        """Test that save clients combined data stores goals."""
        from src.dashboard.shiny_utils.utils_reporting import (
            save_clients_combined_data_to_reactives,
        )

        save_clients_combined_data_to_reactives(reactives_shiny = reactives_with_clients, data_category = "Goals", data_value = sample_df)

        stored = reactives_with_clients["Data_Clients"]["Clients_Combined"]["Goals"].get()
        assert isinstance(stored, pl.DataFrame)

    @pytest.mark.unit()
    def test_save_clients_combined_data_rejects_personal_info(self, reactives_with_clients):
        """Test that save clients combined data rejects personal info."""
        from src.dashboard.shiny_utils.utils_reporting import (
            save_clients_combined_data_to_reactives,
        )

        with pytest.raises(Exception_Validation_Input):
            save_clients_combined_data_to_reactives(
                reactives_shiny = reactives_with_clients, data_category = "Personal_Info", data_value = None
            )


# ============================================================================
# 12. get_results_data_from_reactives
# ============================================================================


@pytest.mark.unit()
class Test_Get_Results_Data_From_Reactives:
    """Tests for ``get_results_data_from_reactives``."""

    @pytest.mark.unit()
    def test_returns_none_when_not_yet_populated(self, reactives_with_results):
        """Test that returns none when not yet populated."""
        from src.dashboard.shiny_utils.utils_reporting import get_results_data_from_reactives

        result = get_results_data_from_reactives(
            reactives_shiny = reactives_with_results, subtab_key = "Portfolio_Analysis_Inputs"
        )

        assert result is None

    @pytest.mark.unit()
    def test_returns_stored_dict(self, reactives_with_results):
        """Test that returns stored dict."""
        from src.dashboard.shiny_utils.utils_reporting import get_results_data_from_reactives

        data = {"metric": 42}
        reactives_with_results["Data_Results"]["Portfolio_Analysis_Inputs"].set(data)

        result = get_results_data_from_reactives(
            reactives_shiny = reactives_with_results, subtab_key = "Portfolio_Analysis_Inputs"
        )

        assert result == data

    @pytest.mark.unit()
    def test_returns_stored_dataframe(self, reactives_with_results, sample_df):
        """Test that returns stored dataframe."""
        from src.dashboard.shiny_utils.utils_reporting import get_results_data_from_reactives

        reactives_with_results["Data_Results"]["Weights_Analysis_Outputs"].set(sample_df)

        result = get_results_data_from_reactives(
            reactives_shiny = reactives_with_results, subtab_key = "Weights_Analysis_Outputs"
        )

        assert isinstance(result, pl.DataFrame)

    @pytest.mark.unit()
    def test_raises_for_invalid_structure(self):
        """Test that raises for invalid structure."""
        from src.dashboard.shiny_utils.utils_reporting import get_results_data_from_reactives

        with pytest.raises(Exception_Validation_Input):
            get_results_data_from_reactives(reactives_shiny = None, subtab_key = "Portfolio_Analysis_Inputs")

    @pytest.mark.unit()
    def test_raises_for_invalid_subtab_key(self, reactives_with_results):
        """Test that raises for invalid subtab key."""
        from src.dashboard.shiny_utils.utils_reporting import get_results_data_from_reactives

        with pytest.raises(Exception_Validation_Input):
            get_results_data_from_reactives(reactives_shiny = reactives_with_results, subtab_key = "Unknown_Key")

    @pytest.mark.unit()
    def test_raises_runtime_error_when_get_raises(self, reactives_with_results):
        """Test that raises runtime error when get raises."""
        from src.dashboard.shiny_utils.utils_reporting import get_results_data_from_reactives

        reactives_with_results["Data_Results"]["Portfolio_Analysis_Inputs"] = (
            MockReactiveValueGetRaises()
        )

        with pytest.raises(Exception_Configuration):
            get_results_data_from_reactives(
                reactives_shiny = reactives_with_results, subtab_key = "Portfolio_Analysis_Inputs"
            )


# ============================================================================
# 13. save_results_data_to_reactives
# ============================================================================


@pytest.mark.unit()
class Test_Save_Results_Data_To_Reactives:
    """Tests for ``save_results_data_to_reactives``."""

    @pytest.mark.unit()
    def test_saves_dict_and_returns_reactives(self, reactives_with_results):
        """Test that saves dict and returns reactives."""
        from src.dashboard.shiny_utils.utils_reporting import save_results_data_to_reactives

        data = {"sharpe": 1.5}
        result = save_results_data_to_reactives(
            reactives_shiny = reactives_with_results, subtab_key = "Portfolio_Analysis_Inputs", data_value = data
        )

        assert result is reactives_with_results
        stored = reactives_with_results["Data_Results"]["Portfolio_Analysis_Inputs"].get()
        assert stored == data

    @pytest.mark.unit()
    def test_saves_dataframe(self, reactives_with_results, sample_df):
        """Test that saves dataframe."""
        from src.dashboard.shiny_utils.utils_reporting import save_results_data_to_reactives

        save_results_data_to_reactives(
            reactives_shiny = reactives_with_results, subtab_key = "Weights_Analysis_Outputs", data_value = sample_df
        )

        stored = reactives_with_results["Data_Results"]["Weights_Analysis_Outputs"].get()
        assert isinstance(stored, pl.DataFrame)

    @pytest.mark.unit()
    def test_saves_none_to_clear(self, reactives_with_results, sample_df):
        """Test that saves none to clear."""
        from src.dashboard.shiny_utils.utils_reporting import save_results_data_to_reactives

        reactives_with_results["Data_Results"]["Portfolio_Analysis_Inputs"].set(sample_df)
        save_results_data_to_reactives(
            reactives_shiny = reactives_with_results, subtab_key = "Portfolio_Analysis_Inputs", data_value = None
        )

        stored = reactives_with_results["Data_Results"]["Portfolio_Analysis_Inputs"].get()
        assert stored is None

    @pytest.mark.unit()
    def test_raises_for_invalid_structure(self):
        """Test that raises for invalid structure."""
        from src.dashboard.shiny_utils.utils_reporting import save_results_data_to_reactives

        with pytest.raises(Exception_Validation_Input):
            save_results_data_to_reactives(reactives_shiny = None, subtab_key = "Portfolio_Analysis_Inputs", data_value = None)

    @pytest.mark.unit()
    def test_raises_for_invalid_subtab_key(self, reactives_with_results):
        """Test that raises for invalid subtab key."""
        from src.dashboard.shiny_utils.utils_reporting import save_results_data_to_reactives

        with pytest.raises(Exception_Validation_Input):
            save_results_data_to_reactives(reactives_shiny = reactives_with_results, subtab_key = "Wrong_Key", data_value = None)

    @pytest.mark.unit()
    def test_raises_runtime_error_when_set_raises(self, reactives_with_results):
        """Test that raises runtime error when set raises."""
        from src.dashboard.shiny_utils.utils_reporting import save_results_data_to_reactives

        reactives_with_results["Data_Results"]["Portfolio_Analysis_Inputs"] = (
            MockReactiveValueSetRaises(None)
        )

        with pytest.raises(Exception_Configuration):
            save_results_data_to_reactives(
                reactives_shiny = reactives_with_results, subtab_key = "Portfolio_Analysis_Inputs", data_value = None
            )


# ============================================================================
# 14. Data_Results convenience wrappers
# ============================================================================


@pytest.mark.unit()
class Test_Results_Convenience_Wrappers:
    """Sample tests for each of the 10 save_*_to_reactives convenience wrappers.

    Each wrapper delegates to ``save_results_data_to_reactives`` with a fixed
    subtab_key; the tests verify (a) correct delegation and (b) that the wrapper
    rejects invalid structures.
    """

    @pytest.mark.parametrize(
        ("func_name", "expected_key"),
        [
            (
                "save_portfolio_analysis_inputs_to_reactives",
                "Portfolio_Analysis_Inputs",
            ),
            (
                "save_portfolio_analysis_outputs_to_reactives",
                "Portfolio_Analysis_Outputs",
            ),
            (
                "save_portfolio_comparison_inputs_to_reactives",
                "Portfolio_Comparison_Inputs",
            ),
            (
                "save_portfolio_comparison_outputs_to_reactives",
                "Portfolio_Comparison_Outputs",
            ),
            (
                "save_weights_analysis_inputs_to_reactives",
                "Weights_Analysis_Inputs",
            ),
            (
                "save_weights_analysis_outputs_to_reactives",
                "Weights_Analysis_Outputs",
            ),
            (
                "save_portfolio_optimization_skfolio_inputs_to_reactives",
                "Portfolio_Optimization_Skfolio_Inputs",
            ),
            (
                "save_portfolio_optimization_skfolio_outputs_to_reactives",
                "Portfolio_Optimization_Skfolio_Outputs",
            ),
            (
                "save_portfolio_simulation_inputs_to_reactives",
                "Portfolio_Simulation_Inputs",
            ),
            (
                "save_portfolio_simulation_outputs_to_reactives",
                "Portfolio_Simulation_Outputs",
            ),
        ],
    )
    @pytest.mark.unit()
    def test_wrapper_stores_data_at_correct_key(
        self, reactives_with_results, func_name, expected_key
    ):
        """Test that wrapper stores data at correct key."""
        import importlib

        module = importlib.import_module("src.dashboard.shiny_utils.utils_reporting")
        func = getattr(module, func_name)
        data = {"key": "value"}

        func(reactives_shiny=reactives_with_results, data_value=data)

        stored = reactives_with_results["Data_Results"][expected_key].get()
        assert stored == data

    @pytest.mark.parametrize(
        "func_name",
        [
            "save_portfolio_analysis_inputs_to_reactives",
            "save_portfolio_simulation_outputs_to_reactives",
        ],
    )
    @pytest.mark.unit()
    def test_wrapper_raises_for_invalid_structure(self, func_name):
        """Test that wrapper raises for invalid structure."""
        import importlib

        module = importlib.import_module("src.dashboard.shiny_utils.utils_reporting")
        func = getattr(module, func_name)

        with pytest.raises(Exception_Validation_Input):
            func(reactives_shiny=None, data_value=None)


# ============================================================================
# 15. _coerce_results_value_to_json
# ============================================================================


@pytest.mark.unit()
class Test_Coerce_Results_Value_To_Json:
    """Tests for ``_coerce_results_value_to_json`` (private helper, tested directly)."""

    @pytest.mark.unit()
    def test_none_returns_empty_dict(self):
        """Test that none returns empty dict."""
        from src.dashboard.shiny_utils.utils_reporting import _coerce_results_value_to_json

        result = _coerce_results_value_to_json(data = None)

        assert result == {}

    @pytest.mark.unit()
    def test_dict_returned_as_is(self):
        """Test that dict returned as is."""
        from src.dashboard.shiny_utils.utils_reporting import _coerce_results_value_to_json

        data = {"metric": 1.5, "label": "sharpe"}
        result = _coerce_results_value_to_json(data = data)

        assert result is data

    @pytest.mark.unit()
    def test_polars_dataframe_converted_to_records(self):
        """Test that polars dataframe converted to records."""
        from src.dashboard.shiny_utils.utils_reporting import _coerce_results_value_to_json

        df = pl.DataFrame({"a": [1, 2], "b": ["x", "y"]})
        result = _coerce_results_value_to_json(data = df)

        assert "records" in result
        assert len(result["records"]) == 2

    @pytest.mark.unit()
    def test_list_wrapped_in_records_key(self):
        """Test that list wrapped in records key."""
        from src.dashboard.shiny_utils.utils_reporting import _coerce_results_value_to_json

        data = [1, 2, 3]
        result = _coerce_results_value_to_json(data = data)

        assert "records" in result
        assert result["records"] == [1, 2, 3]

    @pytest.mark.unit()
    def test_unknown_type_converted_to_str(self):
        """Test that unknown type converted to str."""
        from src.dashboard.shiny_utils.utils_reporting import _coerce_results_value_to_json

        class _Custom:
            """Tests for Custom."""
            def __str__(self):
                """Str."""
                return "custom_obj"

        result = _coerce_results_value_to_json(data = _Custom())

        assert "value" in result
        assert result["value"] == "custom_obj"

    @pytest.mark.unit()
    def test_integer_converted_to_str(self):
        """Test that integer converted to str."""
        from src.dashboard.shiny_utils.utils_reporting import _coerce_results_value_to_json

        result = _coerce_results_value_to_json(data = 42)

        assert "value" in result
        assert result["value"] == "42"


# ============================================================================
# 16. build_results_data_json_from_reactives
# ============================================================================


@pytest.mark.unit()
class Test_Build_Results_Data_Json_From_Reactives:
    """Tests for ``build_results_data_json_from_reactives``."""

    @pytest.mark.unit()
    def test_returns_empty_dict_when_value_is_none(self, reactives_with_results):
        """Test that returns empty dict when value is none."""
        from src.dashboard.shiny_utils.utils_reporting import (
            build_results_data_json_from_reactives,
        )

        result = build_results_data_json_from_reactives(
            reactives_shiny = reactives_with_results, subtab_key = "Portfolio_Analysis_Inputs"
        )

        assert result == {}

    @pytest.mark.unit()
    def test_returns_dict_when_dict_stored(self, reactives_with_results):
        """Test that returns dict when dict stored."""
        from src.dashboard.shiny_utils.utils_reporting import (
            build_results_data_json_from_reactives,
        )

        data = {"total_return": 0.15}
        reactives_with_results["Data_Results"]["Portfolio_Analysis_Inputs"].set(data)

        result = build_results_data_json_from_reactives(
            reactives_shiny = reactives_with_results, subtab_key = "Portfolio_Analysis_Inputs"
        )

        assert result == data

    @pytest.mark.unit()
    def test_returns_records_when_dataframe_stored(self, reactives_with_results, sample_df):
        """Test that returns records when dataframe stored."""
        from src.dashboard.shiny_utils.utils_reporting import (
            build_results_data_json_from_reactives,
        )

        reactives_with_results["Data_Results"]["Weights_Analysis_Outputs"].set(sample_df)

        result = build_results_data_json_from_reactives(
            reactives_shiny = reactives_with_results, subtab_key = "Weights_Analysis_Outputs"
        )

        assert "records" in result
        assert len(result["records"]) == len(sample_df)

    @pytest.mark.unit()
    def test_raises_value_error_for_invalid_structure(self):
        """Test that raises value error for invalid structure."""
        from src.dashboard.shiny_utils.utils_reporting import (
            build_results_data_json_from_reactives,
        )

        with pytest.raises(Exception_Validation_Input):
            build_results_data_json_from_reactives(reactives_shiny = None, subtab_key = "Portfolio_Analysis_Inputs")

    @pytest.mark.unit()
    def test_raises_value_error_for_invalid_subtab_key(self, reactives_with_results):
        """Test that raises value error for invalid subtab key."""
        from src.dashboard.shiny_utils.utils_reporting import (
            build_results_data_json_from_reactives,
        )

        with pytest.raises(Exception_Validation_Input):
            build_results_data_json_from_reactives(reactives_shiny = reactives_with_results, subtab_key = "Bad_Key")

    @pytest.mark.unit()
    def test_returns_empty_dict_when_get_raises(self, reactives_with_results):
        """RuntimeError from reactive.get() should be swallowed, returning {}."""
        from src.dashboard.shiny_utils.utils_reporting import (
            build_results_data_json_from_reactives,
        )

        reactives_with_results["Data_Results"]["Portfolio_Analysis_Inputs"] = (
            MockReactiveValueGetRaises()
        )

        result = build_results_data_json_from_reactives(
            reactives_shiny = reactives_with_results, subtab_key = "Portfolio_Analysis_Inputs"
        )

        assert result == {}

    @pytest.mark.unit()
    def test_skfolio_outputs_preserve_statistics_comparison_dict(self, reactives_with_results):
        """Skfolio outputs dict should preserve statistics_comparison payload."""
        from src.dashboard.shiny_utils.utils_reporting import (
            build_results_data_json_from_reactives,
        )

        skfolio_payload = {
            "weights_comparison": [
                {"asset": "VTI", "equal_weighted": 0.5, "mean_risk": 0.4},
            ],
            "statistics_comparison": [
                {
                    "metric": "CAGR",
                    "method1": 0.082,
                    "method2": 0.091,
                    "difference": 0.009,
                    "format": "pct",
                },
            ],
            "performance_summary": {
                "method1": {
                    "label": "Portfolio 1",
                    "annualized_return": 0.082,
                    "volatility": 0.11,
                    "sharpe_ratio": 0.56,
                },
                "method2": {
                    "label": "Portfolio 2",
                    "annualized_return": 0.091,
                    "volatility": 0.12,
                    "sharpe_ratio": 0.59,
                },
            },
        }

        reactives_with_results["Data_Results"]["Portfolio_Optimization_Skfolio_Outputs"].set(
            skfolio_payload,
        )

        result = build_results_data_json_from_reactives(
            reactives_shiny = reactives_with_results,
            subtab_key = "Portfolio_Optimization_Skfolio_Outputs",
        )

        assert "statistics_comparison" in result
        assert isinstance(result["statistics_comparison"], list)
        assert result["statistics_comparison"][0]["metric"] == "CAGR"


# ============================================================================
# 17. build_client_info_json_from_reactives
# ============================================================================


@pytest.mark.unit()
class Test_Build_Client_Info_Json_From_Reactives:
    """Tests for ``build_client_info_json_from_reactives``."""

    @pytest.mark.unit()
    def test_returns_dict_with_expected_top_level_keys(self, reactives_with_clients):
        """Test that returns dict with expected top level keys."""
        from src.dashboard.shiny_utils.utils_reporting import (
            build_client_info_json_from_reactives,
        )

        result = build_client_info_json_from_reactives(reactives_shiny = reactives_with_clients)

        assert isinstance(result, dict)
        assert "single_or_couple" in result
        assert "personal_info" in result
        assert "assets" in result
        assert "goals" in result
        assert "income" in result

    @pytest.mark.unit()
    def test_single_or_couple_reflects_reactive_value(self, reactives_with_clients):
        """Test that single or couple reflects reactive value."""
        from src.dashboard.shiny_utils.utils_reporting import (
            build_client_info_json_from_reactives,
        )

        reactives_with_clients["Data_Clients"]["Single_Or_Couple"].set("Couple")

        result = build_client_info_json_from_reactives(reactives_shiny = reactives_with_clients)

        assert result["single_or_couple"] == "Couple"

    @pytest.mark.unit()
    def test_returns_defaults_when_dataframes_are_none(self, reactives_with_clients):
        """When no DataFrames have been saved, numeric fields default to 0.0."""
        from src.dashboard.shiny_utils.utils_reporting import (
            build_client_info_json_from_reactives,
        )

        result = build_client_info_json_from_reactives(reactives_shiny = reactives_with_clients)

        # assets.primary.total should default to 0.0
        assert result["assets"]["primary"]["total"] == pytest.approx(0.0)

    @pytest.mark.unit()
    def test_assets_dict_has_primary_partner_combined_keys(self, reactives_with_clients):
        """Test that assets dict has primary partner combined keys."""
        from src.dashboard.shiny_utils.utils_reporting import (
            build_client_info_json_from_reactives,
        )

        result = build_client_info_json_from_reactives(reactives_shiny = reactives_with_clients)

        assert "primary" in result["assets"]
        assert "partner" in result["assets"]
        assert "combined" in result["assets"]

    @pytest.mark.unit()
    def test_returns_dict_for_none_input(self):
        """build_client_info_json_from_reactives swallows errors internally and returns defaults."""
        from src.dashboard.shiny_utils.utils_reporting import (
            build_client_info_json_from_reactives,
        )

        # The function uses _get_df which catches all exceptions – passing None
        # does NOT raise; it returns a default dict with zeroed-out fields.
        result = build_client_info_json_from_reactives(reactives_shiny = None)

        assert isinstance(result, dict)
        assert "single_or_couple" in result

    @pytest.mark.unit()
    def test_goals_dict_has_primary_partner_combined_keys(self, reactives_with_clients):
        """Test that goals dict has primary partner combined keys."""
        from src.dashboard.shiny_utils.utils_reporting import (
            build_client_info_json_from_reactives,
        )

        result = build_client_info_json_from_reactives(reactives_shiny = reactives_with_clients)

        assert "primary" in result["goals"]
        assert "partner" in result["goals"]
        assert "combined" in result["goals"]

    @pytest.mark.unit()
    def test_income_dict_has_primary_partner_combined_keys(self, reactives_with_clients):
        """Test that income dict has primary partner combined keys."""
        from src.dashboard.shiny_utils.utils_reporting import (
            build_client_info_json_from_reactives,
        )

        result = build_client_info_json_from_reactives(reactives_shiny = reactives_with_clients)

        assert "primary" in result["income"]
        assert "partner" in result["income"]
        assert "combined" in result["income"]

    @pytest.mark.unit()
    def test_personal_info_has_primary_and_partner_keys(self, reactives_with_clients):
        """Test that personal info has primary and partner keys."""
        from src.dashboard.shiny_utils.utils_reporting import (
            build_client_info_json_from_reactives,
        )

        result = build_client_info_json_from_reactives(reactives_shiny = reactives_with_clients)

        assert "primary" in result["personal_info"]
        assert "partner" in result["personal_info"]

    @pytest.mark.unit()
    def test_mocked_single_or_couple_uses_mock(self):
        """Test using MagicMock matches existing test style from test_unit_reactives_shiny."""
        from src.dashboard.shiny_utils.utils_reporting import (
            build_client_info_json_from_reactives,
        )

        mock_reactive = MagicMock()
        mock_reactive.get.return_value = "Single"

        reactives = {
            "Data_Clients": {
                "Single_Or_Couple": mock_reactive,
                "Client_Primary": {
                    "Personal_Info": MagicMock(**{"get.return_value": None}),
                    "Assets": MagicMock(**{"get.return_value": None}),
                    "Goals": MagicMock(**{"get.return_value": None}),
                    "Income": MagicMock(**{"get.return_value": None}),
                },
                "Client_Partner": {
                    "Personal_Info": MagicMock(**{"get.return_value": None}),
                    "Assets": MagicMock(**{"get.return_value": None}),
                    "Goals": MagicMock(**{"get.return_value": None}),
                    "Income": MagicMock(**{"get.return_value": None}),
                },
                "Clients_Combined": {
                    "Assets": MagicMock(**{"get.return_value": None}),
                    "Goals": MagicMock(**{"get.return_value": None}),
                    "Income": MagicMock(**{"get.return_value": None}),
                },
            }
        }

        result = build_client_info_json_from_reactives(reactives_shiny = reactives)

        assert result["single_or_couple"] == "Single"


# ============================================================================
# Additional tests to cover previously-missing branches
# ============================================================================


@pytest.mark.unit()
class Class_Test_Validate_Client_Data_Category_Name_NonString:
    """Line 215 — non-string data_category triggers early return."""

    @pytest.mark.unit()
    def Test_non_string_returns_false(self):
        """validate_client_data_category_name with integer input returns False."""
        from src.dashboard.shiny_utils.utils_reporting import validate_client_data_category_name

        result, msg = validate_client_data_category_name(data_category = 42)
        assert result is False
        assert "string" in msg.lower()

    @pytest.mark.unit()
    def Test_none_returns_false(self):
        """validate_client_data_category_name with None returns False."""
        from src.dashboard.shiny_utils.utils_reporting import validate_client_data_category_name

        result, msg = validate_client_data_category_name(data_category = None)
        assert result is False


@pytest.mark.unit()
class Class_Test_Get_Single_Or_Couple_Reactive_None:
    """Lines 270-275 — Single_Or_Couple key is Python None (not a reactive)."""

    @pytest.mark.unit()
    def Test_single_or_couple_key_is_none_raises(self, data_clients_structure):
        """When Single_Or_Couple dict value is None, raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.utils_reporting import get_single_or_couple_from_reactives

        data_clients_structure["Single_Or_Couple"] = None
        reactives = {"Data_Clients": data_clients_structure}
        with pytest.raises(Exception_Validation_Input):
            get_single_or_couple_from_reactives(reactives_shiny = reactives)


@pytest.mark.unit()
class Class_Test_Update_Single_Or_Couple_Invalid_Structure:
    """Lines 325-327 — invalid reactives triggers validation failure."""

    @pytest.mark.unit()
    def Test_none_reactives_raises(self):
        """update_single_or_couple_in_reactives(None, ...) raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.utils_reporting import update_single_or_couple_in_reactives

        with pytest.raises(Exception_Validation_Input):
            update_single_or_couple_in_reactives(reactives_shiny = None, single_or_couple = "Single")


@pytest.mark.unit()
class Class_Test_Get_Client_Data_Reactive_Is_None:
    """Lines 442-447 — reactive_variable is None raises."""

    @pytest.mark.unit()
    def Test_reactive_none_raises(self, data_clients_structure):
        """get_client_data_from_reactives raises when reactive_variable is None."""
        from src.dashboard.shiny_utils.utils_reporting import get_client_data_from_reactives

        data_clients_structure["Client_Primary"]["Assets"] = None
        reactives = {"Data_Clients": data_clients_structure}
        with pytest.raises(Exception_Validation_Input):
            get_client_data_from_reactives(reactives_shiny = reactives, client_level = "Client_Primary", data_category = "Assets")

    @pytest.mark.unit()
    def Test_reactive_no_get_method_raises(self, data_clients_structure):
        """get_client_data_from_reactives raises when reactive has no .get()."""
        from src.dashboard.shiny_utils.utils_reporting import get_client_data_from_reactives

        data_clients_structure["Client_Primary"]["Assets"] = object()
        reactives = {"Data_Clients": data_clients_structure}
        with pytest.raises(Exception_Validation_Input):
            get_client_data_from_reactives(reactives_shiny = reactives, client_level = "Client_Primary", data_category = "Assets")


@pytest.mark.unit()
class Class_Test_Save_Client_Data_Extra_Branches:
    """Lines 519-569 — save_client_data_to_reactives edge cases."""

    @pytest.mark.unit()
    def Test_reactive_none_raises(self, data_clients_structure):
        """save_client_data_to_reactives raises when reactive_variable is None."""
        from src.dashboard.shiny_utils.utils_reporting import save_client_data_to_reactives

        data_clients_structure["Client_Primary"]["Assets"] = None
        reactives = {"Data_Clients": data_clients_structure}
        with pytest.raises(Exception_Validation_Input):
            save_client_data_to_reactives(reactives_shiny = reactives, client_level = "Client_Primary", data_category = "Assets", data_value = None)

    @pytest.mark.unit()
    def Test_reactive_no_set_method_raises(self, data_clients_structure):
        """save_client_data_to_reactives raises when reactive has no .set()."""
        from src.dashboard.shiny_utils.utils_reporting import save_client_data_to_reactives

        data_clients_structure["Client_Primary"]["Assets"] = object()
        reactives = {"Data_Clients": data_clients_structure}
        with pytest.raises(Exception_Validation_Input):
            save_client_data_to_reactives(reactives_shiny = reactives, client_level = "Client_Primary", data_category = "Assets", data_value = None)

    @pytest.mark.unit()
    def Test_set_raises_propagates(self, data_clients_structure, sample_df):
        """save_client_data_to_reactives re-raises when reactive.set() raises."""
        from src.dashboard.shiny_utils.utils_reporting import save_client_data_to_reactives

        data_clients_structure["Client_Primary"]["Assets"] = MockReactiveValueSetRaises()
        reactives = {"Data_Clients": data_clients_structure}
        with pytest.raises(Exception_Configuration):
            save_client_data_to_reactives(reactives_shiny = reactives, client_level = "Client_Primary", data_category = "Assets", data_value = sample_df)

    @pytest.mark.unit()
    def Test_successful_save_returns_reactives(self, data_clients_structure, sample_df):
        """save_client_data_to_reactives returns reactives on success (debug logging path)."""
        from src.dashboard.shiny_utils.utils_reporting import save_client_data_to_reactives

        reactives = {"Data_Clients": data_clients_structure}
        result = save_client_data_to_reactives(reactives_shiny = reactives, client_level = "Client_Primary", data_category = "Assets", data_value = sample_df)
        assert result is reactives


@pytest.mark.unit()
class Class_Test_Build_Client_Info_Json_Inner_Helpers:
    """Lines 854-904 — _get_ui / _flt_ui / _int_ui inner helpers."""

    def _make_reactives(self, user_inputs_dict):
        """Build reactives with User_Inputs_Shiny and minimal Data_Clients."""
        return {
            "User_Inputs_Shiny": user_inputs_dict,
            "Data_Clients": {
                "Single_Or_Couple": MockReactiveValue("Single"),
                "Client_Primary": {
                    "Personal_Info": MockReactiveValue(None),
                    "Assets": MockReactiveValue(None),
                    "Goals": MockReactiveValue(None),
                    "Income": MockReactiveValue(None),
                },
                "Client_Partner": {
                    "Personal_Info": MockReactiveValue(None),
                    "Assets": MockReactiveValue(None),
                    "Goals": MockReactiveValue(None),
                    "Income": MockReactiveValue(None),
                },
                "Clients_Combined": {
                    "Assets": MockReactiveValue(None),
                    "Goals": MockReactiveValue(None),
                    "Income": MockReactiveValue(None),
                },
            },
        }

    @pytest.mark.unit()
    def Test_str_ui_returns_string_value(self):
        """_str_ui reads a string from User_Inputs_Shiny via reactive."""
        from src.dashboard.shiny_utils.utils_reporting import build_client_info_json_from_reactives

        key = "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Name"
        reactives = self._make_reactives({key: MockReactiveValue("Alice")})
        result = build_client_info_json_from_reactives(reactives_shiny = reactives)
        assert result["personal_info"]["primary"]["name"] == "Alice"

    @pytest.mark.unit()
    def Test_flt_ui_returns_float_value(self):
        """_flt_ui reads a float from User_Inputs_Shiny via reactive."""
        from src.dashboard.shiny_utils.utils_reporting import build_client_info_json_from_reactives

        key = "Input_Tab_clients_Subtab_clients_Assets_client_Primary_Assets_Taxable"
        reactives = self._make_reactives({key: MockReactiveValue(250000.0)})
        result = build_client_info_json_from_reactives(reactives_shiny = reactives)
        assert result["assets"]["primary"]["taxable"] == 250000.0

    @pytest.mark.unit()
    def Test_flt_ui_non_convertible_returns_default(self):
        """_flt_ui returns 0.0 when value is not convertible to float."""
        from src.dashboard.shiny_utils.utils_reporting import build_client_info_json_from_reactives

        key = "Input_Tab_clients_Subtab_clients_Assets_client_Primary_Assets_Taxable"
        reactives = self._make_reactives({key: MockReactiveValue("not_a_number")})
        result = build_client_info_json_from_reactives(reactives_shiny = reactives)
        assert result["assets"]["primary"]["taxable"] == 0.0

    @pytest.mark.unit()
    def Test_flt_ui_boolean_returns_default(self):
        """_flt_ui keeps boolean values on the existing 0.0 default path."""
        from src.dashboard.shiny_utils.utils_reporting import build_client_info_json_from_reactives

        key = "Input_Tab_clients_Subtab_clients_Assets_client_Primary_Assets_Taxable"
        reactives = self._make_reactives({key: MockReactiveValue(True)})

        result = build_client_info_json_from_reactives(reactives_shiny = reactives)

        assert result["assets"]["primary"]["taxable"] == 0.0
        assert result["assets"]["primary"]["total"] == 0.0

    @pytest.mark.unit()
    def Test_int_ui_converts_float_to_int(self):
        """_int_ui truncates float (e.g. 60.0) to int."""
        from src.dashboard.shiny_utils.utils_reporting import build_client_info_json_from_reactives

        key = "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Age_Current"
        reactives = self._make_reactives({key: MockReactiveValue(60.0)})
        result = build_client_info_json_from_reactives(reactives_shiny = reactives)
        assert result["personal_info"]["primary"]["age_current"] == 60
        assert isinstance(result["personal_info"]["primary"]["age_current"], int)

    @pytest.mark.unit()
    def Test_int_ui_boolean_returns_default(self):
        """_int_ui keeps boolean values on the existing integer default path."""
        from src.dashboard.shiny_utils.utils_reporting import build_client_info_json_from_reactives

        key = "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Age_Current"
        reactives = self._make_reactives({key: MockReactiveValue(True)})

        result = build_client_info_json_from_reactives(reactives_shiny = reactives)

        assert result["personal_info"]["primary"]["age_current"] == 0
        assert isinstance(result["personal_info"]["primary"]["age_current"], int)

    @pytest.mark.unit()
    def Test_get_raises_returns_none_for_key(self):
        """_get_ui returns None when reactive.get() raises an exception."""
        from src.dashboard.shiny_utils.utils_reporting import build_client_info_json_from_reactives

        key = "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Name"
        reactives = self._make_reactives({key: MockReactiveValueGetRaises()})
        result = build_client_info_json_from_reactives(reactives_shiny = reactives)
        # name should fall back to default (non-empty default_name)
        assert isinstance(result["personal_info"]["primary"]["name"], str)


@pytest.mark.unit()
class Class_Test_Validate_Data_Results_Missing_Subtab_Key:
    """Lines 1110-1111 — Data_Results dict missing a required subtab key."""

    @pytest.mark.unit()
    def Test_partial_keys_returns_false(self):
        """validate_data_results_in_reactives returns False when a subtab key is absent."""
        from src.dashboard.shiny_utils.utils_reporting import (
            validate_data_results_in_reactives,
            VALID_RESULTS_SUBTAB_KEYS,
        )

        # Build a Data_Results with only the first 3 keys
        partial_keys = list(sorted(VALID_RESULTS_SUBTAB_KEYS))[:3]
        data_results = {k: MockReactiveValue(None) for k in partial_keys}
        reactives = {"Data_Results": data_results}
        result, msg = validate_data_results_in_reactives(reactives_shiny = reactives)
        assert result is False
        assert "not found" in msg.lower() or "subtab key" in msg.lower()


@pytest.mark.unit()
class Class_Test_Get_Results_Data_Extra_Branches:
    """Lines 1278-1302 — get_results_data_from_reactives edge cases."""

    @pytest.mark.unit()
    def Test_reactive_none_raises(self, reactives_with_results):
        """get_results_data_from_reactives raises when reactive_variable is None."""
        from src.dashboard.shiny_utils.utils_reporting import get_results_data_from_reactives

        reactives_with_results["Data_Results"]["Portfolio_Analysis_Inputs"] = None
        with pytest.raises(Exception_Validation_Input):
            get_results_data_from_reactives(reactives_shiny = reactives_with_results, subtab_key = "Portfolio_Analysis_Inputs")

    @pytest.mark.unit()
    def Test_reactive_no_get_raises(self, reactives_with_results):
        """get_results_data_from_reactives raises when reactive has no .get()."""
        from src.dashboard.shiny_utils.utils_reporting import get_results_data_from_reactives

        reactives_with_results["Data_Results"]["Portfolio_Analysis_Inputs"] = object()
        with pytest.raises(Exception_Validation_Input):
            get_results_data_from_reactives(reactives_shiny = reactives_with_results, subtab_key = "Portfolio_Analysis_Inputs")

    @pytest.mark.unit()
    def Test_successful_get_returns_value(self, reactives_with_results):
        """get_results_data_from_reactives returns the reactive value on success."""
        from src.dashboard.shiny_utils.utils_reporting import get_results_data_from_reactives

        reactives_with_results["Data_Results"]["Portfolio_Analysis_Inputs"] = MockReactiveValue(
            {"key": "value"}
        )
        result = get_results_data_from_reactives(
            reactives_shiny = reactives_with_results, subtab_key = "Portfolio_Analysis_Inputs"
        )
        assert result == {"key": "value"}

    @pytest.mark.unit()
    def Test_get_raises_propagates(self, reactives_with_results):
        """get_results_data_from_reactives raises Exception_Configuration when get() raises."""
        from src.dashboard.shiny_utils.utils_reporting import get_results_data_from_reactives

        reactives_with_results["Data_Results"]["Portfolio_Analysis_Inputs"] = (
            MockReactiveValueGetRaises()
        )
        with pytest.raises(Exception_Configuration):
            get_results_data_from_reactives(reactives_shiny = reactives_with_results, subtab_key = "Portfolio_Analysis_Inputs")


@pytest.mark.unit()
class Class_Test_Save_Results_Data_Extra_Branches:
    """Lines 1288-1320 — save_results_data_to_reactives reactive None / no-set."""

    @pytest.mark.unit()
    def Test_reactive_none_raises(self, reactives_with_results):
        """save_results_data_to_reactives raises when reactive_variable is None."""
        from src.dashboard.shiny_utils.utils_reporting import save_results_data_to_reactives

        reactives_with_results["Data_Results"]["Portfolio_Analysis_Inputs"] = None
        with pytest.raises(Exception_Validation_Input):
            save_results_data_to_reactives(
                reactives_shiny = reactives_with_results, subtab_key = "Portfolio_Analysis_Inputs", data_value = None
            )

    @pytest.mark.unit()
    def Test_reactive_no_set_raises(self, reactives_with_results):
        """save_results_data_to_reactives raises when reactive has no .set()."""
        from src.dashboard.shiny_utils.utils_reporting import save_results_data_to_reactives

        reactives_with_results["Data_Results"]["Portfolio_Analysis_Inputs"] = object()
        with pytest.raises(Exception_Validation_Input):
            save_results_data_to_reactives(
                reactives_shiny = reactives_with_results, subtab_key = "Portfolio_Analysis_Inputs", data_value = None
            )

    @pytest.mark.unit()
    def Test_set_raises_propagates(self, reactives_with_results):
        """save_results_data_to_reactives raises Exception_Configuration when set() raises."""
        from src.dashboard.shiny_utils.utils_reporting import save_results_data_to_reactives

        reactives_with_results["Data_Results"]["Portfolio_Analysis_Inputs"] = (
            MockReactiveValueSetRaises()
        )
        with pytest.raises(Exception_Configuration):
            save_results_data_to_reactives(
                reactives_shiny = reactives_with_results, subtab_key = "Portfolio_Analysis_Inputs", data_value = {"x": 1}
            )


@pytest.mark.unit()
class Class_Test_OptimalPortfolios_Wrappers:
    """Lines 1581, 1610 — two missing convenience wrapper functions."""

    @pytest.mark.unit()
    def Test_save_optimalportfolios_inputs(self, reactives_with_results):
        """save_portfolio_optimization_optimalportfolios_inputs_to_reactives stores data."""
        from src.dashboard.shiny_utils.utils_reporting import (
            save_portfolio_optimization_optimalportfolios_inputs_to_reactives,
        )

        payload = {"tickers": ["A", "B"]}
        result = save_portfolio_optimization_optimalportfolios_inputs_to_reactives(
            reactives_shiny = reactives_with_results, data_value = payload
        )
        assert result is reactives_with_results
        assert (
            reactives_with_results["Data_Results"][
                "Portfolio_Optimization_OptimalPortfolios_Inputs"
            ].get()
            == payload
        )

    @pytest.mark.unit()
    def Test_save_optimalportfolios_outputs(self, reactives_with_results):
        """save_portfolio_optimization_optimalportfolios_outputs_to_reactives stores data."""
        from src.dashboard.shiny_utils.utils_reporting import (
            save_portfolio_optimization_optimalportfolios_outputs_to_reactives,
        )

        payload = {"weights": [0.5, 0.5]}
        result = save_portfolio_optimization_optimalportfolios_outputs_to_reactives(
            reactives_shiny = reactives_with_results, data_value = payload
        )
        assert result is reactives_with_results
        assert (
            reactives_with_results["Data_Results"][
                "Portfolio_Optimization_OptimalPortfolios_Outputs"
            ].get()
            == payload
        )


@pytest.mark.unit()
class Class_Test_Export_Visual_Objects_To_Svg:
    """Lines 1846-1941 — export_visual_objects_to_svg full coverage."""

    @pytest.mark.unit()
    def Test_none_reactives_returns_none_dict(self):
        """None reactives returns dict with all None values."""
        from src.dashboard.shiny_utils.utils_reporting import export_visual_objects_to_svg

        result = export_visual_objects_to_svg(reactives_shiny = None)
        assert isinstance(result, dict)
        assert all(v is None for v in result.values())

    @pytest.mark.unit()
    def Test_non_dict_reactives_returns_none_dict(self):
        """Non-dict reactives returns dict with all None values."""
        from src.dashboard.shiny_utils.utils_reporting import export_visual_objects_to_svg

        result = export_visual_objects_to_svg(reactives_shiny = "not_a_dict")
        assert isinstance(result, dict)
        assert all(v is None for v in result.values())

    @pytest.mark.unit()
    def Test_missing_visual_objects_shiny_returns_none_dict(self, tmp_path):
        """Missing Visual_Objects_Shiny key returns dict with all None values."""
        from src.dashboard.shiny_utils.utils_reporting import export_visual_objects_to_svg

        reactives = {"Data_Clients": {}}
        result = export_visual_objects_to_svg(reactives_shiny = reactives, output_dir=tmp_path)
        assert isinstance(result, dict)
        assert all(v is None for v in result.values())

    @pytest.mark.unit()
    def Test_non_dict_visual_objects_shiny_returns_none_dict(self, tmp_path):
        """Non-dict Visual_Objects_Shiny returns dict with all None values."""
        from src.dashboard.shiny_utils.utils_reporting import export_visual_objects_to_svg

        reactives = {"Visual_Objects_Shiny": "bad_type"}
        result = export_visual_objects_to_svg(reactives_shiny = reactives, output_dir=tmp_path)
        assert isinstance(result, dict)
        assert all(v is None for v in result.values())

    @pytest.mark.unit()
    def Test_output_dir_creation_failure_returns_none_dict(self):
        """OSError on mkdir returns dict with all None values."""
        import pathlib
        from unittest.mock import patch
        from src.dashboard.shiny_utils.utils_reporting import export_visual_objects_to_svg

        fake_dir = MagicMock(spec=pathlib.Path)
        fake_dir.__truediv__ = lambda self, other: pathlib.Path("/tmp") / other
        fake_dir.mkdir.side_effect = OSError("permission denied")
        reactives = {"Visual_Objects_Shiny": {}}
        result = export_visual_objects_to_svg(reactives_shiny = reactives, output_dir=fake_dir)
        assert isinstance(result, dict)
        assert all(v is None for v in result.values())

    @pytest.mark.unit()
    def Test_reactive_value_none_skips_chart(self, tmp_path):
        """chart_key with None reactive value is skipped (result remains None)."""
        from src.dashboard.shiny_utils.utils_reporting import (
            export_visual_objects_to_svg,
            _VISUAL_OBJECT_SVG_FILENAMES,
        )

        chart_key = next(iter(_VISUAL_OBJECT_SVG_FILENAMES))
        reactives = {"Visual_Objects_Shiny": {chart_key: None}}
        result = export_visual_objects_to_svg(reactives_shiny = reactives, output_dir=tmp_path)
        svg_filename = _VISUAL_OBJECT_SVG_FILENAMES[chart_key]
        assert result[svg_filename] is None

    @pytest.mark.unit()
    def Test_reactive_get_raises_skips_chart(self, tmp_path):
        """Exception from reactive.get() is caught and chart is skipped."""
        from src.dashboard.shiny_utils.utils_reporting import (
            export_visual_objects_to_svg,
            _VISUAL_OBJECT_SVG_FILENAMES,
        )

        chart_key = next(iter(_VISUAL_OBJECT_SVG_FILENAMES))
        reactives = {"Visual_Objects_Shiny": {chart_key: MockReactiveValueGetRaises()}}
        result = export_visual_objects_to_svg(reactives_shiny = reactives, output_dir=tmp_path)
        svg_filename = _VISUAL_OBJECT_SVG_FILENAMES[chart_key]
        assert result[svg_filename] is None

    @pytest.mark.unit()
    def Test_figure_none_after_get_skips_chart(self, tmp_path):
        """Fig is None after reactive.get() — chart is skipped."""
        from src.dashboard.shiny_utils.utils_reporting import (
            export_visual_objects_to_svg,
            _VISUAL_OBJECT_SVG_FILENAMES,
        )

        chart_key = next(iter(_VISUAL_OBJECT_SVG_FILENAMES))
        reactives = {"Visual_Objects_Shiny": {chart_key: MockReactiveValue(None)}}
        result = export_visual_objects_to_svg(reactives_shiny = reactives, output_dir=tmp_path)
        svg_filename = _VISUAL_OBJECT_SVG_FILENAMES[chart_key]
        assert result[svg_filename] is None

    @pytest.mark.unit()
    def Test_plotnine_figure_save_method(self, tmp_path):
        """Figure with .save() method (plotnine) is exported correctly."""
        from src.dashboard.shiny_utils.utils_reporting import (
            export_visual_objects_to_svg,
            _VISUAL_OBJECT_SVG_FILENAMES,
        )

        chart_key = next(iter(_VISUAL_OBJECT_SVG_FILENAMES))
        svg_filename = _VISUAL_OBJECT_SVG_FILENAMES[chart_key]
        svg_path = tmp_path / svg_filename

        mock_fig = MagicMock()
        mock_fig.save = MagicMock()
        # Make .save() create the file so stat() works
        def _fake_save(path, **kwargs):
            import pathlib
            pathlib.Path(path).touch()

        mock_fig.save.side_effect = _fake_save

        reactives = {"Visual_Objects_Shiny": {chart_key: MockReactiveValue(mock_fig)}}
        result = export_visual_objects_to_svg(reactives_shiny = reactives, output_dir=tmp_path)
        mock_fig.save.assert_called_once()
        assert result[svg_filename] == svg_path

    @pytest.mark.unit()
    def Test_plotly_figure_write_image_method(self, tmp_path):
        """Figure without .save() uses .write_image() (Plotly) path."""
        from src.dashboard.shiny_utils.utils_reporting import (
            export_visual_objects_to_svg,
            _VISUAL_OBJECT_SVG_FILENAMES,
        )

        chart_key = next(iter(_VISUAL_OBJECT_SVG_FILENAMES))
        svg_filename = _VISUAL_OBJECT_SVG_FILENAMES[chart_key]
        svg_path = tmp_path / svg_filename

        mock_fig = MagicMock(spec=[])  # spec=[] means hasattr(fig, 'save') is False
        mock_fig.write_image = MagicMock()

        def _fake_write_image(path, **kwargs):
            import pathlib
            pathlib.Path(path).touch()

        mock_fig.write_image.side_effect = _fake_write_image

        reactives = {"Visual_Objects_Shiny": {chart_key: MockReactiveValue(mock_fig)}}
        result = export_visual_objects_to_svg(reactives_shiny = reactives, output_dir=tmp_path)
        mock_fig.write_image.assert_called_once()
        assert result[svg_filename] == svg_path

    @pytest.mark.unit()
    def Test_save_raises_returns_none_for_chart(self, tmp_path):
        """Exception from fig.save() is caught and chart result is None."""
        from src.dashboard.shiny_utils.utils_reporting import (
            export_visual_objects_to_svg,
            _VISUAL_OBJECT_SVG_FILENAMES,
        )

        chart_key = next(iter(_VISUAL_OBJECT_SVG_FILENAMES))
        svg_filename = _VISUAL_OBJECT_SVG_FILENAMES[chart_key]

        mock_fig = MagicMock()
        mock_fig.save.side_effect = RuntimeError("kaleido not installed")

        reactives = {"Visual_Objects_Shiny": {chart_key: MockReactiveValue(mock_fig)}}
        result = export_visual_objects_to_svg(reactives_shiny = reactives, output_dir=tmp_path)
        assert result[svg_filename] is None

    @pytest.mark.unit()
    def Test_plain_reactive_value_used_directly(self, tmp_path):
        """Reactive without .get() method uses object directly as fig."""
        from src.dashboard.shiny_utils.utils_reporting import (
            export_visual_objects_to_svg,
            _VISUAL_OBJECT_SVG_FILENAMES,
        )

        chart_key = next(iter(_VISUAL_OBJECT_SVG_FILENAMES))
        svg_filename = _VISUAL_OBJECT_SVG_FILENAMES[chart_key]
        svg_path = tmp_path / svg_filename

        # Object with .save() but no .get() — used directly as the figure
        class _DirectFig:
            def save(self, path, **kwargs):
                import pathlib
                pathlib.Path(path).touch()

        direct_fig = _DirectFig()
        reactives = {"Visual_Objects_Shiny": {chart_key: direct_fig}}
        result = export_visual_objects_to_svg(reactives_shiny = reactives, output_dir=tmp_path)
        assert result[svg_filename] == svg_path


# ============================================================================
# Additional targeted tests for remaining missing branches
# ============================================================================


@pytest.mark.unit()
class Class_Test_Save_Client_Data_Invalid_Level_And_DataValue:
    """Lines 519-521, 544-550 — save_client_data_to_reactives invalid level & data_value."""

    @pytest.mark.unit()
    def Test_invalid_client_level_raises(self, data_clients_structure):
        """save_client_data_to_reactives raises when client_level is invalid (lines 519-521)."""
        from src.dashboard.shiny_utils.utils_reporting import save_client_data_to_reactives

        reactives = {"Data_Clients": data_clients_structure}
        with pytest.raises(Exception_Validation_Input):
            save_client_data_to_reactives(reactives_shiny = reactives, client_level = "Invalid_Level", data_category = "Assets", data_value = None)

    @pytest.mark.unit()
    def Test_invalid_data_value_type_raises(self, data_clients_structure):
        """save_client_data_to_reactives raises when data_value is not DataFrame or None (544-550)."""
        from src.dashboard.shiny_utils.utils_reporting import save_client_data_to_reactives

        reactives = {"Data_Clients": data_clients_structure}
        with pytest.raises(Exception_Validation_Input):
            save_client_data_to_reactives(reactives_shiny = reactives, client_level = "Client_Primary", data_category = "Assets", data_value = "bad_type")


@pytest.mark.unit()
class Class_Test_Get_Results_Data_Key_Not_In_Data_Results:
    """Defensive: get_results_data_from_reactives missing key (covered by pragma no cover in source)."""

    @pytest.mark.unit()
    def Test_reactive_none_raises_validation_input(self, reactives_with_results):
        """get_results_data_from_reactives raises when reactive_variable is None."""
        from src.dashboard.shiny_utils.utils_reporting import get_results_data_from_reactives

        reactives_with_results["Data_Results"]["Portfolio_Analysis_Inputs"] = None
        with pytest.raises(Exception_Validation_Input):
            get_results_data_from_reactives(
                reactives_shiny = reactives_with_results, subtab_key = "Portfolio_Analysis_Inputs"
            )


@pytest.mark.unit()
class Class_Test_Save_Results_Data_Key_Not_In_Data_Results:
    """Defensive: save_results_data_to_reactives missing key (covered by pragma no cover in source)."""

    @pytest.mark.unit()
    def Test_reactive_none_raises_validation_input(self, reactives_with_results):
        """save_results_data_to_reactives raises when reactive_variable is None."""
        from src.dashboard.shiny_utils.utils_reporting import save_results_data_to_reactives

        reactives_with_results["Data_Results"]["Portfolio_Analysis_Inputs"] = None
        with pytest.raises(Exception_Validation_Input):
            save_results_data_to_reactives(
                reactives_shiny = reactives_with_results, subtab_key = "Portfolio_Analysis_Inputs", data_value = None
            )


@pytest.mark.unit()
class Class_Test_Build_Client_Info_Json_Get_Raises_And_Int_NonConvertible:
    """Lines 862, 903-904 — _get_ui except branch and _int_ui non-convertible."""

    def _make_reactives(self, user_inputs_dict):
        return {
            "User_Inputs_Shiny": user_inputs_dict,
            "Data_Clients": {
                "Single_Or_Couple": MockReactiveValue("Single"),
                "Client_Primary": {
                    "Personal_Info": MockReactiveValue(None),
                    "Assets": MockReactiveValue(None),
                    "Goals": MockReactiveValue(None),
                    "Income": MockReactiveValue(None),
                },
                "Client_Partner": {
                    "Personal_Info": MockReactiveValue(None),
                    "Assets": MockReactiveValue(None),
                    "Goals": MockReactiveValue(None),
                    "Income": MockReactiveValue(None),
                },
                "Clients_Combined": {
                    "Assets": MockReactiveValue(None),
                    "Goals": MockReactiveValue(None),
                    "Income": MockReactiveValue(None),
                },
            },
        }

    @pytest.mark.unit()
    def Test_get_ui_reactive_get_raises_returns_default(self):
        """_get_ui catches exception from reactive.get() and returns None (line 862)."""
        from src.dashboard.shiny_utils.utils_reporting import build_client_info_json_from_reactives

        # Use the age field (int) with a reactive that raises on get
        key = "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Age_Current"
        reactives = self._make_reactives({key: MockReactiveValueGetRaises()})
        result = build_client_info_json_from_reactives(reactives_shiny = reactives)
        # _int_ui will receive None from _get_ui (exception caught at line 862)
        assert result["personal_info"]["primary"]["age_current"] == 0

    @pytest.mark.unit()
    def Test_int_ui_non_convertible_returns_default(self):
        """_int_ui returns default int when value is not convertible (lines 903-904)."""
        from src.dashboard.shiny_utils.utils_reporting import build_client_info_json_from_reactives

        key = "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Age_Current"
        reactives = self._make_reactives({key: MockReactiveValue("not_an_int")})
        result = build_client_info_json_from_reactives(reactives_shiny = reactives)
        assert result["personal_info"]["primary"]["age_current"] == 0

    @pytest.mark.unit()
    def Test_get_ui_plain_value_returned_directly(self):
        """_get_ui returns plain value directly when object has no .get() method (line 862)."""
        from src.dashboard.shiny_utils.utils_reporting import build_client_info_json_from_reactives

        key = "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Name"
        # Store a plain string (no .get method) directly in User_Inputs_Shiny
        reactives = self._make_reactives({key: "PlainStringValue"})
        result = build_client_info_json_from_reactives(reactives_shiny = reactives)
        assert result["personal_info"]["primary"]["name"] == "PlainStringValue"

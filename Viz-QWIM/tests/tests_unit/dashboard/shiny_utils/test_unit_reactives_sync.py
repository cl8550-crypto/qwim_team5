"""Unit tests for reactives_sync module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Configuration,
    Exception_Validation_Input,
)


@pytest.mark.unit()
class Test_Reactives_Sync_Module_Imports:
    """Tests that reactives_sync exports the expected names."""

    @pytest.mark.unit()
    def test_portfolio_subtab_results_key_map_importable(self):
        """Test that portfolio subtab results key map importable."""
        from src.dashboard.shiny_utils.reactives_sync import _PORTFOLIO_SUBTAB_RESULTS_KEY_MAP

        assert isinstance(_PORTFOLIO_SUBTAB_RESULTS_KEY_MAP, dict)

    @pytest.mark.unit()
    def test_reactive_key_to_input_id_importable(self):
        """Test that reactive key to input id importable."""
        from src.dashboard.shiny_utils.reactives_sync import _reactive_key_to_input_id

        assert callable(_reactive_key_to_input_id)

    @pytest.mark.unit()
    def test_register_client_input_observers_importable(self):
        """Test that register client input observers importable."""
        from src.dashboard.shiny_utils.reactives_sync import register_client_input_observers

        assert callable(register_client_input_observers)

    @pytest.mark.unit()
    def test_register_portfolio_results_observers_importable(self):
        """Test that register portfolio results observers importable."""
        from src.dashboard.shiny_utils.reactives_sync import register_portfolio_results_observers

        assert callable(register_portfolio_results_observers)


@pytest.mark.unit()
class Test_Portfolio_Subtab_Results_Key_Map:
    """Tests for _PORTFOLIO_SUBTAB_RESULTS_KEY_MAP constant."""

    @pytest.mark.unit()
    def test_has_five_entries(self):
        """Test that has five entries."""
        from src.dashboard.shiny_utils.reactives_sync import _PORTFOLIO_SUBTAB_RESULTS_KEY_MAP

        assert len(_PORTFOLIO_SUBTAB_RESULTS_KEY_MAP) == 5

    @pytest.mark.unit()
    def test_contains_portfolios_analysis_prefix(self):
        """Test that contains portfolios analysis prefix."""
        from src.dashboard.shiny_utils.reactives_sync import _PORTFOLIO_SUBTAB_RESULTS_KEY_MAP

        keys = list(_PORTFOLIO_SUBTAB_RESULTS_KEY_MAP.keys())
        assert any("Portfolios_Analysis" in k for k in keys)

    @pytest.mark.unit()
    def test_contains_simulation_prefix(self):
        """Test that contains simulation prefix."""
        from src.dashboard.shiny_utils.reactives_sync import _PORTFOLIO_SUBTAB_RESULTS_KEY_MAP

        keys = list(_PORTFOLIO_SUBTAB_RESULTS_KEY_MAP.keys())
        assert any("Simulation" in k for k in keys)

    @pytest.mark.unit()
    def test_all_values_are_strings(self):
        """Test that all values are strings."""
        from src.dashboard.shiny_utils.reactives_sync import _PORTFOLIO_SUBTAB_RESULTS_KEY_MAP

        for k, v in _PORTFOLIO_SUBTAB_RESULTS_KEY_MAP.items():
            assert isinstance(k, str), f"Key {k!r} is not a string"
            assert isinstance(v, str), f"Value {v!r} for key {k!r} is not a string"


@pytest.mark.unit()
class Test_Reactive_Key_To_Input_Id:
    """Tests for _reactive_key_to_input_id."""

    @pytest.mark.unit()
    def test_invalid_prefix_raises_value_error(self):
        """Test that invalid prefix raises value error."""
        from src.dashboard.shiny_utils.reactives_sync import _reactive_key_to_input_id

        with pytest.raises(Exception_Validation_Input, match=r"reactive_key must start with"):
            _reactive_key_to_input_id(reactive_key = "Unknown_Prefix_Key")

    @pytest.mark.unit()
    def test_valid_prefix_returns_lowercase_id(self):
        """Test that valid prefix returns lowercase id."""
        from src.dashboard.shiny_utils.reactives_sync import (
            _PORTFOLIO_SUBTAB_RESULTS_KEY_MAP,
            _reactive_key_to_input_id,
        )

        # Use first registered prefix
        prefix = next(iter(_PORTFOLIO_SUBTAB_RESULTS_KEY_MAP))
        reactive_key = f"{prefix}Time_Period"
        result = _reactive_key_to_input_id(reactive_key = reactive_key)
        assert isinstance(result, str)
        assert len(result) > 0


@pytest.mark.unit()
class Test_Register_Client_Input_Observers:
    """Tests for register_client_input_observers."""

    @pytest.mark.unit()
    def test_none_shiny_input_raises_value_error(self):
        """Test that none shiny input raises value error."""
        from src.dashboard.shiny_utils.reactives_sync import register_client_input_observers

        with pytest.raises((ValueError, Exception)):
            register_client_input_observers(input = None, reactives_shiny = {})

    @pytest.mark.unit()
    def test_invalid_reactives_shiny_raises(self):
        """Test that invalid reactives shiny raises."""
        from src.dashboard.shiny_utils.reactives_sync import register_client_input_observers

        with pytest.raises((ValueError, Exception)):
            register_client_input_observers(input = MagicMock(), reactives_shiny = None)


@pytest.mark.unit()
class Test_Register_Portfolio_Results_Observers:
    """Tests for register_portfolio_results_observers."""

    @pytest.mark.unit()
    def test_none_shiny_input_raises(self):
        """Test that none shiny input raises."""
        from src.dashboard.shiny_utils.reactives_sync import register_portfolio_results_observers

        with pytest.raises((ValueError, Exception)):
            register_portfolio_results_observers(input = None, reactives_shiny = {})

    @pytest.mark.unit()
    def test_invalid_reactives_shiny_raises(self):
        """Test that invalid reactives shiny raises."""
        from src.dashboard.shiny_utils.reactives_sync import register_portfolio_results_observers


        with pytest.raises((ValueError, Exception)):
            register_portfolio_results_observers(input = MagicMock(), reactives_shiny = None)


# ---------------------------------------------------------------------------
# Module-level helper
# ---------------------------------------------------------------------------

def _make_valid_reactives_shiny(
    user_inputs: dict | None = None,
    data_results: dict | None = None,
) -> dict:
    """Return a minimal reactives_shiny dict that passes validate_reactives_shiny_structure."""
    return {
        "User_Inputs_Shiny": user_inputs if user_inputs is not None else {},
        "Inner_Variables_Shiny": {},
        "Triggers_Shiny": {},
        "Visual_Objects_Shiny": {},
        "Data_Clients": {},
        "Data_Results": data_results if data_results is not None else {},
    }


@pytest.mark.unit()
class Test_Register_Single_Input_Observer:
    """Tests for _register_single_input_observer (lines 95-106)."""

    @pytest.mark.unit()
    def test_missing_reactive_key_logs_warning_and_returns(self):
        """target_reactive is None → warning logged, early return, no exception."""
        from src.dashboard.shiny_utils.reactives_sync import _register_single_input_observer

        reactives = _make_valid_reactives_shiny(user_inputs={})
        # reactive_key not in User_Inputs_Shiny → get() returns None
        _register_single_input_observer(
            input=MagicMock(),
            reactives_shiny=reactives,
            input_id="input_ID_tab_clients_subtab_clients_name",
            reactive_key="Input_Tab_clients_Subtab_clients_Name",
        )

    @pytest.mark.unit()
    def test_valid_reactive_key_registers_observer(self):
        """target_reactive present → @reactive.effect registered without Shiny session."""
        from unittest.mock import patch

        from src.dashboard.shiny_utils.reactives_sync import _register_single_input_observer

        target = MagicMock()
        reactives = _make_valid_reactives_shiny(
            user_inputs={"Input_Tab_clients_Subtab_clients_Name": target}
        )
        with patch("shiny.reactive.effect", lambda f: f):
            _register_single_input_observer(
                input=MagicMock(),
                reactives_shiny=reactives,
                input_id="input_ID_tab_clients_subtab_clients_name",
                reactive_key="Input_Tab_clients_Subtab_clients_Name",
            )


@pytest.mark.unit()
class Test_Register_Client_Input_Observers_Body:
    """Tests for register_client_input_observers main body (lines 196-228)."""

    @pytest.mark.unit()
    def test_no_client_keys_logs_warning_and_returns(self):
        """User_Inputs_Shiny has no Input_Tab_clients_* keys → warning + early return."""
        from src.dashboard.shiny_utils.reactives_sync import register_client_input_observers

        reactives = _make_valid_reactives_shiny(
            user_inputs={"Input_Tab_portfolios_Something": MagicMock()}
        )
        register_client_input_observers(input = MagicMock(), reactives_shiny = reactives)

    @pytest.mark.unit()
    def test_with_client_keys_registers_observers(self):
        """Main loop executed with one client key → observer registered."""
        from unittest.mock import patch

        from src.dashboard.shiny_utils.reactives_sync import register_client_input_observers

        target = MagicMock()
        reactives = _make_valid_reactives_shiny(
            user_inputs={"Input_Tab_clients_Subtab_clients_Name": target}
        )
        with patch("shiny.reactive.effect", lambda f: f):
            register_client_input_observers(input = MagicMock(), reactives_shiny = reactives)


@pytest.mark.unit()
class Test_Register_Subtab_Snapshot_Observer:
    """Tests for _register_subtab_snapshot_observer (lines 268-292)."""

    @pytest.mark.unit()
    def test_missing_data_results_key_logs_warning_and_returns(self):
        """Data_Results key not found → warning logged, early return, no exception."""
        from src.dashboard.shiny_utils.reactives_sync import _register_subtab_snapshot_observer

        reactives = _make_valid_reactives_shiny(data_results={})
        _register_subtab_snapshot_observer(
            input=MagicMock(),
            reactives_shiny=reactives,
            group_keys=["Input_Tab_Portfolios_Subtab_Comparison_Time_Period"],
            results_base_key="Portfolio_Comparison",
        )

    @pytest.mark.unit()
    def test_valid_data_results_key_registers_snapshot_observer(self):
        """Data_Results key present → input_id_pairs built, @reactive.effect registered."""
        from unittest.mock import patch

        from src.dashboard.shiny_utils.reactives_sync import _register_subtab_snapshot_observer

        target = MagicMock()
        reactives = _make_valid_reactives_shiny(
            data_results={"Portfolio_Comparison_Inputs": target}
        )
        with patch("shiny.reactive.effect", lambda f: f):
            _register_subtab_snapshot_observer(
                input=MagicMock(),
                reactives_shiny=reactives,
                group_keys=["Input_Tab_Portfolios_Subtab_Comparison_Time_Period"],
                results_base_key="Portfolio_Comparison",
            )


@pytest.mark.unit()
class Test_Register_Portfolio_Results_Observers_Body:
    """Tests for register_portfolio_results_observers main body (lines 395-456)."""

    @pytest.mark.unit()
    def test_no_portfolio_keys_skips_all_groups(self):
        """All subtab groups empty → debug log per group, no observers registered."""
        from unittest.mock import patch

        from src.dashboard.shiny_utils.reactives_sync import register_portfolio_results_observers

        reactives = _make_valid_reactives_shiny(
            user_inputs={"Input_Tab_clients_Something": MagicMock()},
            data_results={},
        )
        with patch("shiny.reactive.effect", lambda f: f):
            register_portfolio_results_observers(input = MagicMock(), reactives_shiny = reactives)

    @pytest.mark.unit()
    def test_missing_data_results_key_logs_warning_no_snapshot(self):
        """Portfolio key present but Data_Results key absent → warning, per-input observer only."""
        from unittest.mock import patch

        from src.dashboard.shiny_utils.reactives_sync import register_portfolio_results_observers

        target_reactive = MagicMock()
        reactives = _make_valid_reactives_shiny(
            user_inputs={
                "Input_Tab_Portfolios_Subtab_Comparison_Time_Period": target_reactive,
            },
            data_results={},  # Portfolio_Comparison_Inputs absent → warning branch
        )
        with patch("shiny.reactive.effect", lambda f: f):
            register_portfolio_results_observers(input = MagicMock(), reactives_shiny = reactives)

    @pytest.mark.unit()
    def test_with_portfolio_keys_and_data_results_registers_both_observers(self):
        """Full happy path: snapshot + per-input observers registered for one subtab."""
        from unittest.mock import patch

        from src.dashboard.shiny_utils.reactives_sync import register_portfolio_results_observers

        target_reactive = MagicMock()
        target_inputs = MagicMock()
        reactives = _make_valid_reactives_shiny(
            user_inputs={
                "Input_Tab_Portfolios_Subtab_Comparison_Time_Period": target_reactive,
            },
            data_results={
                "Portfolio_Comparison_Inputs": target_inputs,
            },
        )
        with patch("shiny.reactive.effect", lambda f: f):
            register_portfolio_results_observers(input = MagicMock(), reactives_shiny = reactives)

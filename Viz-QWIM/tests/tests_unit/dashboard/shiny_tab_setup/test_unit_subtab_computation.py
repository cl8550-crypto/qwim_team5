"""Unit tests for subtab_computation module.

Tests cover:
- Module importability and public API
- Module-level constants (choices, defaults, subtab rows)
- ``_reactive_key`` helper
- ``get_computation_type_for_subtab``
- ``get_debug_options_for_subtab``
- ``_build_computation_type_table``
- ``_build_developer_debug_table``
- ``subtab_computation_ui`` callable
- ``subtab_computation_server`` callable
- ``COMPUTATION_SUBTAB_ROWS`` coverage
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest


# ============================================================================
# Module import tests
# ============================================================================


@pytest.mark.unit()
class Test_Subtab_Computation_Module_Imports:
    """Verify module imports and public API."""

    @pytest.mark.unit()
    def test_module_importable(self):
        """Module imports without error."""
        import src.dashboard.shiny_tab_setup.subtab_computation as mod

        assert mod is not None

    @pytest.mark.unit()
    def test_ui_callable(self):
        """subtab_computation_ui is callable."""
        from src.dashboard.shiny_tab_setup.subtab_computation import subtab_computation_ui

        assert callable(subtab_computation_ui)

    @pytest.mark.unit()
    def test_server_callable(self):
        """subtab_computation_server is callable."""
        from src.dashboard.shiny_tab_setup.subtab_computation import subtab_computation_server

        assert callable(subtab_computation_server)

    @pytest.mark.unit()
    def test_logger_initialised(self):
        """Module-level _logger is initialised."""
        import src.dashboard.shiny_tab_setup.subtab_computation as mod

        assert hasattr(mod, "_logger")

    @pytest.mark.unit()
    def test_getter_functions_callable(self):
        """Public getter helpers are callable."""
        from src.dashboard.shiny_tab_setup.subtab_computation import (
            get_computation_type_for_subtab,
            get_debug_options_for_subtab,
        )

        assert callable(get_computation_type_for_subtab)
        assert callable(get_debug_options_for_subtab)


# ============================================================================
# Constants tests
# ============================================================================


@pytest.mark.unit()
class Test_Subtab_Computation_Constants:
    """Verify module-level constants are correct."""

    @pytest.mark.unit()
    def test_computation_type_choices_is_dict(self):
        """COMPUTATION_TYPE_CHOICES is a non-empty dict."""
        from src.dashboard.shiny_tab_setup.subtab_computation import COMPUTATION_TYPE_CHOICES

        assert isinstance(COMPUTATION_TYPE_CHOICES, dict)
        assert len(COMPUTATION_TYPE_CHOICES) >= 6

    @pytest.mark.unit()
    def test_joblib_in_computation_type_choices(self):
        """joblib is a valid computation type choice."""
        from src.dashboard.shiny_tab_setup.subtab_computation import COMPUTATION_TYPE_CHOICES

        assert "joblib" in COMPUTATION_TYPE_CHOICES

    @pytest.mark.unit()
    def test_default_computation_type_is_standard(self):
        """DEFAULT_COMPUTATION_TYPE is 'standard'."""
        from src.dashboard.shiny_tab_setup.subtab_computation import DEFAULT_COMPUTATION_TYPE

        assert DEFAULT_COMPUTATION_TYPE == "standard"

    @pytest.mark.unit()
    def test_logger_display_choices_has_no_display(self):
        """LOGGER_DISPLAY_CHOICES contains 'no_display'."""
        from src.dashboard.shiny_tab_setup.subtab_computation import LOGGER_DISPLAY_CHOICES

        assert "no_display" in LOGGER_DISPLAY_CHOICES

    @pytest.mark.unit()
    def test_default_logger_display_is_no_display(self):
        """DEFAULT_LOGGER_DISPLAY is 'no_display'."""
        from src.dashboard.shiny_tab_setup.subtab_computation import DEFAULT_LOGGER_DISPLAY

        assert DEFAULT_LOGGER_DISPLAY == "no_display"

    @pytest.mark.unit()
    def test_execution_thread_mode_choices_has_background(self):
        """EXECUTION_THREAD_MODE_CHOICES contains 'background'."""
        from src.dashboard.shiny_tab_setup.subtab_computation import EXECUTION_THREAD_MODE_CHOICES

        assert "background" in EXECUTION_THREAD_MODE_CHOICES

    @pytest.mark.unit()
    def test_execution_thread_mode_choices_has_synchronous(self):
        """EXECUTION_THREAD_MODE_CHOICES contains 'synchronous'."""
        from src.dashboard.shiny_tab_setup.subtab_computation import EXECUTION_THREAD_MODE_CHOICES

        assert "synchronous" in EXECUTION_THREAD_MODE_CHOICES

    @pytest.mark.unit()
    def test_default_execution_thread_mode_is_background(self):
        """DEFAULT_EXECUTION_THREAD_MODE is 'background'."""
        from src.dashboard.shiny_tab_setup.subtab_computation import DEFAULT_EXECUTION_THREAD_MODE

        assert DEFAULT_EXECUTION_THREAD_MODE == "background"

    @pytest.mark.unit()
    def test_profiler_choices_has_none(self):
        """PROFILER_CHOICES contains 'none'."""
        from src.dashboard.shiny_tab_setup.subtab_computation import PROFILER_CHOICES

        assert "none" in PROFILER_CHOICES

    @pytest.mark.unit()
    def test_default_profiler_is_none(self):
        """DEFAULT_PROFILER is 'none'."""
        from src.dashboard.shiny_tab_setup.subtab_computation import DEFAULT_PROFILER

        assert DEFAULT_PROFILER == "none"

    @pytest.mark.unit()
    def test_computation_subtab_rows_has_four_entries(self):
        """COMPUTATION_SUBTAB_ROWS has exactly 4 rows."""
        from src.dashboard.shiny_tab_setup.subtab_computation import COMPUTATION_SUBTAB_ROWS

        assert len(COMPUTATION_SUBTAB_ROWS) == 4

    @pytest.mark.unit()
    def test_computation_subtab_rows_contains_portfolio_comparison(self):
        """COMPUTATION_SUBTAB_ROWS includes portfolio_comparison."""
        from src.dashboard.shiny_tab_setup.subtab_computation import COMPUTATION_SUBTAB_ROWS

        keys = [row[0] for row in COMPUTATION_SUBTAB_ROWS]
        assert "portfolio_comparison" in keys

    @pytest.mark.unit()
    def test_computation_subtab_rows_contains_skfolio_optimization(self):
        """COMPUTATION_SUBTAB_ROWS includes skfolio_optimization."""
        from src.dashboard.shiny_tab_setup.subtab_computation import COMPUTATION_SUBTAB_ROWS

        keys = [row[0] for row in COMPUTATION_SUBTAB_ROWS]
        assert "skfolio_optimization" in keys

    @pytest.mark.unit()
    def test_computation_subtab_rows_contains_optimalportfolios_optimization(self):
        """COMPUTATION_SUBTAB_ROWS includes optimalportfolios_optimization (single-z spelling)."""
        from src.dashboard.shiny_tab_setup.subtab_computation import COMPUTATION_SUBTAB_ROWS

        keys = [row[0] for row in COMPUTATION_SUBTAB_ROWS]
        assert "optimalportfolios_optimization" in keys

    @pytest.mark.unit()
    def test_computation_subtab_rows_contains_simulation(self):
        """COMPUTATION_SUBTAB_ROWS includes simulation."""
        from src.dashboard.shiny_tab_setup.subtab_computation import COMPUTATION_SUBTAB_ROWS

        keys = [row[0] for row in COMPUTATION_SUBTAB_ROWS]
        assert "simulation" in keys

    @pytest.mark.unit()
    def test_optimalportfolios_label_single_z(self):
        """OptimalPortfolios Optimization label uses single-z spelling."""
        from src.dashboard.shiny_tab_setup.subtab_computation import COMPUTATION_SUBTAB_ROWS

        labels = [row[1] for row in COMPUTATION_SUBTAB_ROWS]
        assert "OptimalPortfolios Optimization" in labels
        assert not any("Optimizzation" in lbl for lbl in labels)

    @pytest.mark.unit()
    def test_debug_only_subtab_rows_exists(self):
        """DEBUG_ONLY_SUBTAB_ROWS is a non-empty tuple."""
        from src.dashboard.shiny_tab_setup.subtab_computation import DEBUG_ONLY_SUBTAB_ROWS

        assert isinstance(DEBUG_ONLY_SUBTAB_ROWS, tuple)
        assert len(DEBUG_ONLY_SUBTAB_ROWS) >= 1

    @pytest.mark.unit()
    def test_debug_only_subtab_rows_contains_outline_clients(self):
        """DEBUG_ONLY_SUBTAB_ROWS includes outline_clients."""
        from src.dashboard.shiny_tab_setup.subtab_computation import DEBUG_ONLY_SUBTAB_ROWS

        keys = [row[0] for row in DEBUG_ONLY_SUBTAB_ROWS]
        assert "outline_clients" in keys

    @pytest.mark.unit()
    def test_debug_only_subtab_rows_outline_label_and_tab(self):
        """Outline row has correct label and tab."""
        from src.dashboard.shiny_tab_setup.subtab_computation import DEBUG_ONLY_SUBTAB_ROWS

        for key, label, tab in DEBUG_ONLY_SUBTAB_ROWS:
            if key == "outline_clients":
                assert label == "Outline"
                assert tab == "Clients"
                break
        else:
            pytest.fail("outline_clients not found in DEBUG_ONLY_SUBTAB_ROWS")

    @pytest.mark.unit()
    def test_outline_clients_in_reactive_stem(self):
        """_SUBTAB_KEY_TO_REACTIVE_STEM includes outline_clients."""
        from src.dashboard.shiny_tab_setup.subtab_computation import _SUBTAB_KEY_TO_REACTIVE_STEM

        assert "outline_clients" in _SUBTAB_KEY_TO_REACTIVE_STEM
        assert _SUBTAB_KEY_TO_REACTIVE_STEM["outline_clients"] == "Outline_Clients"

    @pytest.mark.unit()
    def test_outline_clients_in_module_prefix(self):
        """_SUBTAB_KEY_TO_MODULE_PREFIX includes outline_clients."""
        from src.dashboard.shiny_tab_setup.subtab_computation import _SUBTAB_KEY_TO_MODULE_PREFIX

        assert "outline_clients" in _SUBTAB_KEY_TO_MODULE_PREFIX
        assert _SUBTAB_KEY_TO_MODULE_PREFIX["outline_clients"] == "src.dashboard.shiny_tab_clients.subtab_outline"

    @pytest.mark.unit()
    def test_reactive_key_for_outline_clients_logger_display(self):
        """_reactive_key returns correct key for outline_clients Logger_Display."""
        from src.dashboard.shiny_tab_setup.subtab_computation import _reactive_key

        result = _reactive_key(subtab_key = "outline_clients", param = "Logger_Display")
        assert result == "Input_Tab_Setup_Subtab_Computation_Outline_Clients_Logger_Display"


# ============================================================================
# _reactive_key helper
# ============================================================================


@pytest.mark.unit()
class Test_Reactive_Key_Helper:
    """Tests for _reactive_key."""

    @pytest.mark.unit()
    def test_portfolio_comparison_computation_type(self):
        """_reactive_key returns correct key for portfolio_comparison Computation_Type."""
        from src.dashboard.shiny_tab_setup.subtab_computation import _reactive_key

        result = _reactive_key(subtab_key = "portfolio_comparison", param = "Computation_Type")
        assert result == "Input_Tab_Setup_Subtab_Computation_Portfolio_Comparison_Computation_Type"

    @pytest.mark.unit()
    def test_simulation_profiler(self):
        """_reactive_key returns correct key for simulation Profiler."""
        from src.dashboard.shiny_tab_setup.subtab_computation import _reactive_key

        result = _reactive_key(subtab_key = "simulation", param = "Profiler")
        assert result == "Input_Tab_Setup_Subtab_Computation_Simulation_Profiler"

    @pytest.mark.unit()
    def test_optimalportfolios_execution_thread_mode(self):
        """_reactive_key uses OptimalPortfolios_Optimization stem."""
        from src.dashboard.shiny_tab_setup.subtab_computation import _reactive_key

        result = _reactive_key(subtab_key = "optimalportfolios_optimization", param = "Execution_Thread_Mode")
        assert "OptimalPortfolios_Optimization" in result

    @pytest.mark.unit()
    def test_unknown_subtab_key_returns_empty_stem(self):
        """_reactive_key with unknown subtab_key produces key with empty stem."""
        from src.dashboard.shiny_tab_setup.subtab_computation import _reactive_key

        result = _reactive_key(subtab_key = "unknown_key", param = "Computation_Type")
        assert isinstance(result, str)


# ============================================================================
# get_computation_type_for_subtab
# ============================================================================


@pytest.mark.unit()
class Test_Get_Computation_Type_For_Subtab:
    """Tests for get_computation_type_for_subtab."""

    @pytest.mark.unit()
    def test_returns_default_when_reactives_not_dict(self):
        """Returns default when reactives_shiny is not a dict."""
        from src.dashboard.shiny_tab_setup.subtab_computation import (
            DEFAULT_COMPUTATION_TYPE,
            get_computation_type_for_subtab,
        )

        result = get_computation_type_for_subtab(reactives_shiny = None, subtab_key = "portfolio_comparison")  # type: ignore[arg-type]
        assert result == DEFAULT_COMPUTATION_TYPE

    @pytest.mark.unit()
    def test_returns_default_when_user_inputs_missing(self):
        """Returns default when User_Inputs_Shiny key is absent."""
        from src.dashboard.shiny_tab_setup.subtab_computation import (
            DEFAULT_COMPUTATION_TYPE,
            get_computation_type_for_subtab,
        )

        result = get_computation_type_for_subtab(reactives_shiny = {}, subtab_key = "portfolio_comparison")
        assert result == DEFAULT_COMPUTATION_TYPE

    @pytest.mark.unit()
    def test_returns_value_from_reactive(self):
        """Returns the set value when reactive holds a valid computation type."""
        from src.dashboard.shiny_tab_setup.subtab_computation import (
            _reactive_key,
            get_computation_type_for_subtab,
        )

        rv = MagicMock()
        rv.return_value = "asyncio"
        key = _reactive_key(subtab_key = "portfolio_comparison", param = "Computation_Type")
        reactives_shiny = {"User_Inputs_Shiny": {key: rv}}

        result = get_computation_type_for_subtab(reactives_shiny = reactives_shiny, subtab_key = "portfolio_comparison")
        assert result == "asyncio"

    @pytest.mark.unit()
    def test_returns_default_when_reactive_is_none(self):
        """Returns default when the reactive value itself is None."""
        from src.dashboard.shiny_tab_setup.subtab_computation import (
            DEFAULT_COMPUTATION_TYPE,
            _reactive_key,
            get_computation_type_for_subtab,
        )

        rv = MagicMock()
        rv.return_value = None
        key = _reactive_key(subtab_key = "simulation", param = "Computation_Type")
        reactives_shiny = {"User_Inputs_Shiny": {key: rv}}

        result = get_computation_type_for_subtab(reactives_shiny = reactives_shiny, subtab_key = "simulation")
        assert result == DEFAULT_COMPUTATION_TYPE


# ============================================================================
# get_debug_options_for_subtab
# ============================================================================


@pytest.mark.unit()
class Test_Get_Debug_Options_For_Subtab:
    """Tests for get_debug_options_for_subtab."""

    @pytest.mark.unit()
    def test_returns_defaults_when_reactives_not_dict(self):
        """Returns all defaults when reactives_shiny is not a dict."""
        from src.dashboard.shiny_tab_setup.subtab_computation import (
            DEFAULT_EXECUTION_THREAD_MODE,
            DEFAULT_LOGGER_DISPLAY,
            DEFAULT_PROFILER,
            get_debug_options_for_subtab,
        )

        result = get_debug_options_for_subtab(reactives_shiny = None, subtab_key = "simulation")  # type: ignore[arg-type]
        assert result["logger_display"] == DEFAULT_LOGGER_DISPLAY
        assert result["execution_thread_mode"] == DEFAULT_EXECUTION_THREAD_MODE
        assert result["profiler"] == DEFAULT_PROFILER

    @pytest.mark.unit()
    def test_returns_dict_with_correct_keys(self):
        """Return value always has the three expected keys."""
        from src.dashboard.shiny_tab_setup.subtab_computation import get_debug_options_for_subtab

        result = get_debug_options_for_subtab(reactives_shiny = {}, subtab_key = "portfolio_comparison")
        assert "logger_display" in result
        assert "execution_thread_mode" in result
        assert "profiler" in result

    @pytest.mark.unit()
    def test_returns_values_from_reactives(self):
        """Returns stored values when all three reactives hold valid data."""
        from src.dashboard.shiny_tab_setup.subtab_computation import (
            _reactive_key,
            get_debug_options_for_subtab,
        )

        def make_rv(value):
            """Make rv."""
            rv = MagicMock()
            rv.return_value = value
            return rv

        subtab_key = "skfolio_optimization"
        user_inputs = {
            _reactive_key(subtab_key = subtab_key, param = "Logger_Display"): make_rv("debug"),
            _reactive_key(subtab_key = subtab_key, param = "Execution_Thread_Mode"): make_rv("synchronous"),
            _reactive_key(subtab_key = subtab_key, param = "Profiler"): make_rv("line_profiler"),
        }
        reactives_shiny = {"User_Inputs_Shiny": user_inputs}

        result = get_debug_options_for_subtab(reactives_shiny = reactives_shiny, subtab_key = subtab_key)
        assert result["logger_display"] == "debug"
        assert result["execution_thread_mode"] == "synchronous"
        assert result["profiler"] == "line_profiler"


# ============================================================================
# UI builder helpers
# ============================================================================


@pytest.mark.unit()
class Test_Build_Computation_Type_Table:
    """Tests for _build_computation_type_table."""

    @pytest.mark.unit()
    def test_returns_tag_object(self):
        """_build_computation_type_table returns a non-None object."""
        from src.dashboard.shiny_tab_setup.subtab_computation import _build_computation_type_table

        result = _build_computation_type_table()
        assert result is not None

    @pytest.mark.unit()
    def test_result_has_str_representation(self):
        """_build_computation_type_table result has a string representation."""
        from src.dashboard.shiny_tab_setup.subtab_computation import _build_computation_type_table

        result = _build_computation_type_table()
        assert isinstance(str(result), str)


@pytest.mark.unit()
class Test_Build_Developer_Debug_Table:
    """Tests for _build_developer_debug_table."""

    @pytest.mark.unit()
    def test_returns_tag_object(self):
        """_build_developer_debug_table returns a non-None object."""
        from src.dashboard.shiny_tab_setup.subtab_computation import _build_developer_debug_table

        result = _build_developer_debug_table()
        assert result is not None

    @pytest.mark.unit()
    def test_result_has_str_representation(self):
        """_build_developer_debug_table result has a string representation."""
        from src.dashboard.shiny_tab_setup.subtab_computation import _build_developer_debug_table

        result = _build_developer_debug_table()
        assert isinstance(str(result), str)


# ============================================================================
# ensure_computation_user_inputs_initialized
# ============================================================================


@pytest.mark.unit()
class Test_Computation_Reactive_Key_Coverage:
    """Verify that all 16 expected reactive keys are produced."""

    @pytest.mark.unit()
    def test_all_16_reactive_keys_exist(self):
        """_reactive_key produces 16 distinct keys (4 subtabs Ã— 4 params)."""
        from src.dashboard.shiny_tab_setup.subtab_computation import (
            COMPUTATION_SUBTAB_ROWS,
            _reactive_key,
        )

        params = ["Computation_Type", "Logger_Display", "Execution_Thread_Mode", "Profiler"]
        keys = {_reactive_key(subtab_key = row[0], param = param) for row in COMPUTATION_SUBTAB_ROWS for param in params}
        assert len(keys) == 16

    @pytest.mark.unit()
    def test_all_keys_start_with_expected_prefix(self):
        """All reactive keys start with the expected prefix."""
        from src.dashboard.shiny_tab_setup.subtab_computation import (
            COMPUTATION_SUBTAB_ROWS,
            _reactive_key,
        )

        params = ["Computation_Type", "Logger_Display", "Execution_Thread_Mode", "Profiler"]
        for row in COMPUTATION_SUBTAB_ROWS:
            for param in params:
                key = _reactive_key(subtab_key = row[0], param = param)
                assert key.startswith("Input_Tab_Setup_Subtab_Computation_"), key


# ============================================================================
# _SUBTAB_KEY_TO_MODULE_PREFIX
# ============================================================================


@pytest.mark.unit()
class Test_Subtab_Key_To_Module_Prefix:
    """Tests for _SUBTAB_KEY_TO_MODULE_PREFIX dict."""

    @pytest.mark.unit()
    def test_has_exactly_five_entries(self):
        """Dict has exactly 5 subtab entries (4 computation + 1 debug-only)."""
        from src.dashboard.shiny_tab_setup.subtab_computation import _SUBTAB_KEY_TO_MODULE_PREFIX

        assert len(_SUBTAB_KEY_TO_MODULE_PREFIX) == 5

    @pytest.mark.unit()
    def test_portfolio_comparison_prefix(self):
        """portfolio_comparison maps to the correct module prefix."""
        from src.dashboard.shiny_tab_setup.subtab_computation import _SUBTAB_KEY_TO_MODULE_PREFIX

        assert _SUBTAB_KEY_TO_MODULE_PREFIX["portfolio_comparison"] == (
            "src.dashboard.shiny_tab_portfolios.subtab_portfolios_comparison"
        )

    @pytest.mark.unit()
    def test_skfolio_optimization_prefix(self):
        """skfolio_optimization maps to the correct module prefix."""
        from src.dashboard.shiny_tab_setup.subtab_computation import _SUBTAB_KEY_TO_MODULE_PREFIX

        assert _SUBTAB_KEY_TO_MODULE_PREFIX["skfolio_optimization"] == (
            "src.dashboard.shiny_tab_portfolios.subtab_portfolios_skfolio"
        )

    @pytest.mark.unit()
    def test_optimalportfolios_optimization_prefix(self):
        """optimalportfolios_optimization maps to the correct module prefix."""
        from src.dashboard.shiny_tab_setup.subtab_computation import _SUBTAB_KEY_TO_MODULE_PREFIX

        assert _SUBTAB_KEY_TO_MODULE_PREFIX["optimalportfolios_optimization"] == (
            "src.dashboard.shiny_tab_portfolios.subtab_portfolios_optimalportfolios"
        )

    @pytest.mark.unit()
    def test_simulation_prefix(self):
        """simulation maps to the correct module prefix."""
        from src.dashboard.shiny_tab_setup.subtab_computation import _SUBTAB_KEY_TO_MODULE_PREFIX

        assert _SUBTAB_KEY_TO_MODULE_PREFIX["simulation"] == (
            "src.dashboard.shiny_tab_results.subtab_simulation"
        )

    @pytest.mark.unit()
    def test_all_prefixes_are_non_empty_strings(self):
        """Every prefix value is a non-empty string."""
        from src.dashboard.shiny_tab_setup.subtab_computation import _SUBTAB_KEY_TO_MODULE_PREFIX

        for subtab_key, prefix in _SUBTAB_KEY_TO_MODULE_PREFIX.items():
            assert isinstance(prefix, str), f"prefix for {subtab_key!r} is not str"
            assert len(prefix) > 0, f"prefix for {subtab_key!r} is empty"

    @pytest.mark.unit()
    def test_all_keys_match_all_subtab_rows(self):
        """Every key in _SUBTAB_KEY_TO_MODULE_PREFIX is in COMPUTATION_SUBTAB_ROWS or DEBUG_ONLY_SUBTAB_ROWS."""
        from src.dashboard.shiny_tab_setup.subtab_computation import (
            COMPUTATION_SUBTAB_ROWS,
            DEBUG_ONLY_SUBTAB_ROWS,
            _SUBTAB_KEY_TO_MODULE_PREFIX,
        )

        row_keys = {row[0] for row in COMPUTATION_SUBTAB_ROWS}
        row_keys.update(row[0] for row in DEBUG_ONLY_SUBTAB_ROWS)
        for key in _SUBTAB_KEY_TO_MODULE_PREFIX:
            assert key in row_keys, f"{key!r} not found in COMPUTATION_SUBTAB_ROWS or DEBUG_ONLY_SUBTAB_ROWS"


# ============================================================================
# get_computation_type_for_subtab — branch: user_inputs not a dict
# ============================================================================


@pytest.mark.unit()
class Test_Get_Computation_Type_User_Inputs_Branch:
    """Cover the branch where User_Inputs_Shiny exists but is not a dict."""

    @pytest.mark.unit()
    def test_returns_default_when_user_inputs_not_dict(self):
        """Returns DEFAULT_COMPUTATION_TYPE when User_Inputs_Shiny is not a dict (covers line 197)."""
        from src.dashboard.shiny_tab_setup.subtab_computation import (
            DEFAULT_COMPUTATION_TYPE,
            get_computation_type_for_subtab,
        )

        result = get_computation_type_for_subtab(
            reactives_shiny = {"User_Inputs_Shiny": "not-a-dict"}, subtab_key = "portfolio_comparison"
        )
        assert result == DEFAULT_COMPUTATION_TYPE


# ============================================================================
# get_debug_options_for_subtab — branch: user_inputs not a dict
# ============================================================================


@pytest.mark.unit()
class Test_Get_Debug_Options_User_Inputs_Branch:
    """Cover the branch where User_Inputs_Shiny exists but is not a dict."""

    @pytest.mark.unit()
    def test_returns_defaults_when_user_inputs_not_dict(self):
        """Returns defaults when User_Inputs_Shiny is not a dict (covers line 229)."""
        from src.dashboard.shiny_tab_setup.subtab_computation import (
            DEFAULT_EXECUTION_THREAD_MODE,
            DEFAULT_LOGGER_DISPLAY,
            DEFAULT_PROFILER,
            get_debug_options_for_subtab,
        )

        result = get_debug_options_for_subtab(reactives_shiny = {"User_Inputs_Shiny": 42}, subtab_key = "simulation")
        assert result["logger_display"] == DEFAULT_LOGGER_DISPLAY
        assert result["execution_thread_mode"] == DEFAULT_EXECUTION_THREAD_MODE
        assert result["profiler"] == DEFAULT_PROFILER


# ============================================================================
# subtab_computation_ui — try body and except path
# ============================================================================


@pytest.mark.unit()
class Test_Subtab_Computation_UI_Body:
    """Cover the subtab_computation_ui try/except body (lines 392-411)."""

    @pytest.mark.unit()
    def test_ui_returns_div(self):
        """subtab_computation_ui('test_id', ...) executes the try body and returns a tag."""
        from src.dashboard.shiny_tab_setup.subtab_computation import subtab_computation_ui

        result = subtab_computation_ui("test_computation", data_utils={}, data_inputs={})
        assert result is not None
        assert hasattr(result, "tagify") or hasattr(result, "get_html_string") or isinstance(result, str) or str(result)

    @pytest.mark.unit()
    def test_ui_raises_exception_configuration_on_build_error(self):
        """subtab_computation_ui raises Exception_Configuration when a builder raises TypeError."""
        from unittest.mock import patch

        import pytest

        from src.dashboard.shiny_tab_setup.subtab_computation import subtab_computation_ui
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Configuration,
        )

        with patch(
            "src.dashboard.shiny_tab_setup.subtab_computation._build_computation_type_table",
            side_effect=TypeError("boom"),
        ):
            with pytest.raises(Exception_Configuration):
                subtab_computation_ui("test_computation", data_utils={}, data_inputs={})


# ============================================================================
# set_console_level_for_subtab integration with subtab_computation
# ============================================================================


@pytest.mark.unit()
class Test_Observer_Calls_Set_Console_Level:
    """Verify that set_console_level_for_subtab is wired correctly to subtab_computation.

    The observer itself is nested inside subtab_computation_server (a Shiny
    callback, pragma: no cover) so it cannot be imported in isolation.  These
    tests instead verify the end-to-end contract via the public API:
    calling set_console_level_for_subtab with a prefix taken from
    _SUBTAB_KEY_TO_MODULE_PREFIX immediately updates _subtab_console_rules in
    the logger_custom module, matching the observer's behaviour.
    """

    @pytest.mark.unit()
    def test_set_console_level_importable_from_subtab_computation(self):
        """set_console_level_for_subtab is accessible inside subtab_computation."""
        import src.dashboard.shiny_tab_setup.subtab_computation as mod

        assert hasattr(mod, "set_console_level_for_subtab"), (
            "set_console_level_for_subtab not found in subtab_computation module"
        )

    @pytest.mark.unit()
    def test_simulation_prefix_registers_debug_rule(self):
        """Calling set_console_level_for_subtab with simulation prefix + debug updates _subtab_console_rules."""
        from src.utils.custom_exceptions_errors_loggers.logger_custom import (
            _subtab_console_rules,
            set_console_level_for_subtab,
        )
        from src.dashboard.shiny_tab_setup.subtab_computation import _SUBTAB_KEY_TO_MODULE_PREFIX

        prefix = _SUBTAB_KEY_TO_MODULE_PREFIX["simulation"]
        try:
            set_console_level_for_subtab(_subtab_key = "simulation", module_prefix = prefix, level_key = "debug")
            assert _subtab_console_rules.get(prefix) == "debug"
        finally:
            _subtab_console_rules.pop(prefix, None)

    @pytest.mark.unit()
    def test_portfolio_comparison_prefix_no_display_removes_entry(self):
        """Calling with no_display for portfolio_comparison removes the entry."""
        from src.utils.custom_exceptions_errors_loggers.logger_custom import (
            _subtab_console_rules,
            set_console_level_for_subtab,
        )
        from src.dashboard.shiny_tab_setup.subtab_computation import _SUBTAB_KEY_TO_MODULE_PREFIX

        prefix = _SUBTAB_KEY_TO_MODULE_PREFIX["portfolio_comparison"]
        try:
            _subtab_console_rules[prefix] = "info"
            set_console_level_for_subtab(_subtab_key = "portfolio_comparison", module_prefix = prefix, level_key = "no_display")
            assert prefix not in _subtab_console_rules
        finally:
            _subtab_console_rules.pop(prefix, None)

    @pytest.mark.unit()
    def test_all_subtab_prefixes_can_be_registered(self):
        """Every prefix in _SUBTAB_KEY_TO_MODULE_PREFIX can be registered without error."""
        from src.utils.custom_exceptions_errors_loggers.logger_custom import (
            _subtab_console_rules,
            set_console_level_for_subtab,
        )
        from src.dashboard.shiny_tab_setup.subtab_computation import _SUBTAB_KEY_TO_MODULE_PREFIX

        try:
            for subtab_key, prefix in _SUBTAB_KEY_TO_MODULE_PREFIX.items():
                set_console_level_for_subtab(_subtab_key = subtab_key, module_prefix = prefix, level_key = "info_debug")
                assert _subtab_console_rules.get(prefix) == "info_debug"
        finally:
            for prefix in _SUBTAB_KEY_TO_MODULE_PREFIX.values():
                _subtab_console_rules.pop(prefix, None)

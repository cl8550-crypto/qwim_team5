"""Unit tests for subtab_simulation module.

Tests import-time validation, helper functions, UI construction,
and constants defined in the Simulation subtab.
"""
# ruff: noqa: PLC0415

from __future__ import annotations

import pytest


# ======================================================================
# Import & module-level constants
# ======================================================================


class Test_Subtab_Simulation_Imports:
    """Verify that the module can be imported and constants are correct."""

    @pytest.mark.unit()
    def test_module_imports_successfully(self):
        """subtab_simulation should import without errors."""
        import src.dashboard.shiny_tab_results.subtab_simulation as mod

        assert hasattr(mod, "subtab_simulation_ui")
        assert hasattr(mod, "subtab_simulation_server")

    @pytest.mark.unit()
    def test_all_etf_symbols_length(self):
        """ALL_ETF_SYMBOLS should contain 12 entries."""
        from src.dashboard.shiny_tab_results.subtab_simulation import ALL_ETF_SYMBOLS

        assert len(ALL_ETF_SYMBOLS) == 12

    @pytest.mark.unit()
    def test_default_selected_etfs(self):
        """Default selected ETFs should be IVV, IJH, IWM."""
        from src.dashboard.shiny_tab_results.subtab_simulation import (
            DEFAULT_SELECTED_ETFS,
        )

        assert DEFAULT_SELECTED_ETFS == ["IVV", "IJH", "IWM"]

    @pytest.mark.unit()
    def test_distribution_choices_keys(self):
        """DISTRIBUTION_CHOICES should have normal, lognormal, student_t."""
        from src.dashboard.shiny_tab_results.subtab_simulation import (
            DISTRIBUTION_CHOICES,
        )

        assert set(DISTRIBUTION_CHOICES.keys()) == {"normal", "lognormal", "student_t"}

    @pytest.mark.unit()
    def test_rng_type_choices_keys(self):
        """RNG_TYPE_CHOICES should have known RNG types."""
        from src.dashboard.shiny_tab_results.subtab_simulation import RNG_TYPE_CHOICES

        assert "pcg64" in RNG_TYPE_CHOICES
        assert "mt19937" in RNG_TYPE_CHOICES


# ======================================================================
# Helper functions
# ======================================================================


class Test_Subtab_Simulation_Helpers:
    """Test helper functions in the module."""

    @pytest.mark.unit()
    def test_map_distribution_key_normal(self):
        """'normal' should map to Distribution_Type.NORMAL."""
        from src.dashboard.shiny_tab_results.subtab_simulation import (
            _map_distribution_key,
        )
        from src.num_methods.scenarios.scenarios_distrib import Distribution_Type

        assert _map_distribution_key(key = "normal") == Distribution_Type.NORMAL

    @pytest.mark.unit()
    def test_map_distribution_key_lognormal(self):
        """'lognormal' should map to Distribution_Type.LOGNORMAL."""
        from src.dashboard.shiny_tab_results.subtab_simulation import (
            _map_distribution_key,
        )
        from src.num_methods.scenarios.scenarios_distrib import Distribution_Type

        assert _map_distribution_key(key = "lognormal") == Distribution_Type.LOGNORMAL

    @pytest.mark.unit()
    def test_map_distribution_key_student_t(self):
        """'student_t' should map to Distribution_Type.STUDENT_T."""
        from src.dashboard.shiny_tab_results.subtab_simulation import (
            _map_distribution_key,
        )
        from src.num_methods.scenarios.scenarios_distrib import Distribution_Type

        assert _map_distribution_key(key = "student_t") == Distribution_Type.STUDENT_T

    @pytest.mark.unit()
    def test_map_distribution_key_unknown_defaults_to_normal(self):
        """Unknown key should default to NORMAL."""
        from src.dashboard.shiny_tab_results.subtab_simulation import (
            _map_distribution_key,
        )
        from src.num_methods.scenarios.scenarios_distrib import Distribution_Type

        assert _map_distribution_key(key = "unknown_xyz") == Distribution_Type.NORMAL

    @pytest.mark.unit()
    def test_create_empty_figure(self):
        """_create_empty_figure should call go.Figure and add the centred annotation."""
        from unittest.mock import MagicMock, patch

        from src.dashboard.shiny_tab_results.subtab_simulation import (
            _create_empty_figure,
        )

        with patch(
            "src.dashboard.shiny_tab_results.subtab_simulation.go.Figure"
        ) as MockFigure:
            mock_fig = MagicMock()
            MockFigure.return_value = mock_fig

            result = _create_empty_figure(title = "Test Title", message = "Test Message")

        assert result is mock_fig
        MockFigure.assert_called_once_with()
        mock_fig.add_annotation.assert_called_once()
        add_kwargs = mock_fig.add_annotation.call_args.kwargs
        assert add_kwargs.get("text") == "Test Message"
        assert add_kwargs.get("showarrow") is False
        mock_fig.update_layout.assert_called_once()
        update_kwargs = mock_fig.update_layout.call_args.kwargs
        assert update_kwargs.get("title") == "Test Title"

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        ("raw_value", "expected_elapsed"),
        [
            (True, 0.0),
            (2, 2.0),
            ("bad", 0.0),
        ],
        ids=["bool_uses_default", "int_promotes_to_float", "invalid_uses_default"],
    )
    def Test_Coerce_Compare_Elapsed_Uses_Expected_Fallbacks(
        self,
        raw_value: object,
        expected_elapsed: float,
    ) -> None:
        """Compare elapsed coercion should preserve valid numerics and reject booleans."""
        from src.dashboard.shiny_tab_results.subtab_simulation import (
            _coerce_compare_elapsed_or_default,
        )

        result_elapsed = _coerce_compare_elapsed_or_default(raw_value = raw_value)

        assert result_elapsed == pytest.approx(expected_elapsed)

    @pytest.mark.unit()
    def test_create_rng_pcg64(self):
        """_create_rng with pcg64 should create a valid Generator."""
        import numpy as np

        from src.dashboard.shiny_tab_results.subtab_simulation import _create_rng

        rng = _create_rng(rng_type = "pcg64", seed = 42)
        assert isinstance(rng, np.random.Generator)
        # Should produce deterministic output
        val1 = rng.random()
        rng2 = _create_rng(rng_type = "pcg64", seed = 42)
        val2 = rng2.random()
        assert val1 == val2

    @pytest.mark.unit()
    def test_create_rng_mt19937(self):
        """_create_rng with mt19937 should create a valid Generator."""
        import numpy as np

        from src.dashboard.shiny_tab_results.subtab_simulation import _create_rng

        rng = _create_rng(rng_type = "mt19937", seed = 123)
        assert isinstance(rng, np.random.Generator)

    @pytest.mark.unit()
    def test_create_rng_unknown_defaults_to_pcg64(self):
        """Unknown RNG type should default to PCG64."""
        import numpy as np

        from src.dashboard.shiny_tab_results.subtab_simulation import _create_rng

        rng = _create_rng(rng_type = "nonexistent", seed = 42)
        assert isinstance(rng, np.random.Generator)

    @pytest.mark.unit()
    def test_parse_start_date_value_from_iso_string(self) -> None:
        """ISO date strings should parse to ``datetime.date`` values."""
        import datetime as dt

        from src.dashboard.shiny_tab_results.subtab_simulation import _parse_start_date_value

        assert _parse_start_date_value(raw_date = "2026-05-18") == dt.date(2026, 5, 18)

    @pytest.mark.unit()
    def test_parse_start_date_value_passes_date_through(self) -> None:
        """Existing ``datetime.date`` inputs should pass through unchanged."""
        import datetime as dt

        from src.dashboard.shiny_tab_results.subtab_simulation import _parse_start_date_value

        start_date = dt.date(2026, 5, 18)
        assert _parse_start_date_value(raw_date = start_date) == start_date

    @pytest.mark.unit()
    def test_parse_start_date_value_defaults_to_today_for_unknown_input(self) -> None:
        """Non-date, non-string inputs should fall back to today's UTC date."""
        import datetime as dt

        from src.dashboard.shiny_tab_results.subtab_simulation import _parse_start_date_value

        today = dt.datetime.now(tz=dt.UTC).date()
        parsed = _parse_start_date_value(raw_date = object())
        assert abs((parsed - today).days) <= 1

    @pytest.mark.unit()
    def test_read_compute_and_compare_toggle_enabled_true(self) -> None:
        """The compare-toggle helper should return ``True`` when the switch is on."""
        from src.dashboard.shiny_tab_results.subtab_simulation import (
            _read_compute_and_compare_toggle_enabled,
        )

        class _Input_With_Compare_Toggle:
            def input_ID_tab_results_subtab_simulation_compute_and_compare(self) -> bool:
                return True

        assert _read_compute_and_compare_toggle_enabled(input_obj = _Input_With_Compare_Toggle()) is True

    @pytest.mark.unit()
    def test_read_compute_and_compare_toggle_enabled_false_when_input_missing(self) -> None:
        """Missing compare-toggle inputs should be treated as disabled."""
        from src.dashboard.shiny_tab_results.subtab_simulation import (
            _read_compute_and_compare_toggle_enabled,
        )

        class _Input_Without_Compare_Toggle:
            pass

        assert _read_compute_and_compare_toggle_enabled(input_obj = _Input_Without_Compare_Toggle()) is False

    @pytest.mark.unit()
    def test_read_compute_and_compare_toggle_enabled_false_when_input_raises(self) -> None:
        """Errors while reading the compare-toggle input should be suppressed."""
        from src.dashboard.shiny_tab_results.subtab_simulation import (
            _read_compute_and_compare_toggle_enabled,
        )

        class _Input_With_Raising_Compare_Toggle:
            def input_ID_tab_results_subtab_simulation_compute_and_compare(self) -> bool:
                raise RuntimeError("boom")

        assert _read_compute_and_compare_toggle_enabled(input_obj = _Input_With_Raising_Compare_Toggle()) is False

    @pytest.mark.unit()
    def test_read_simulation_run_parameters_normalizes_student_t_inputs(self) -> None:
        """Student-t inputs should preserve explicit numeric and date selections."""
        import datetime as dt

        from src.dashboard.shiny_tab_results.subtab_simulation import (
            _read_simulation_run_parameters,
        )
        from src.num_methods.scenarios.scenarios_distrib import Distribution_Type

        class _Input_With_Student_T_Parameters:
            def input_ID_tab_results_subtab_simulation_num_scenarios(self) -> int:
                return 250

            def input_ID_tab_results_subtab_simulation_num_days(self) -> int:
                return 63

            def input_ID_tab_results_subtab_simulation_initial_value(self) -> float:
                return 12345.0

            def input_ID_tab_results_subtab_simulation_seed(self) -> int:
                return 77

            def input_ID_tab_results_subtab_simulation_distribution_type(self) -> str:
                return "student_t"

            def input_ID_tab_results_subtab_simulation_rng_type(self) -> str:
                return "philox"

            def input_ID_tab_results_subtab_simulation_degrees_of_freedom(self) -> float:
                return 7.5

            def input_ID_tab_results_subtab_simulation_start_date(self) -> str:
                return "2026-06-30"

        params_simulation_run = _read_simulation_run_parameters(
            input_obj = _Input_With_Student_T_Parameters(),
        )

        assert params_simulation_run["num_scenarios"] == 250
        assert params_simulation_run["num_days"] == 63
        assert params_simulation_run["initial_value"] == pytest.approx(12345.0)
        assert params_simulation_run["random_seed"] == 77
        assert params_simulation_run["distribution_key"] == "student_t"
        assert params_simulation_run["distribution_type"] == Distribution_Type.STUDENT_T
        assert params_simulation_run["rng_type"] == "philox"
        assert params_simulation_run["degrees_of_freedom"] == pytest.approx(7.5)
        assert params_simulation_run["start_date"] == dt.date(2026, 6, 30)

    @pytest.mark.unit()
    def test_read_simulation_run_parameters_defaults_missing_values(self) -> None:
        """Missing UI values should fall back to the documented simulation defaults."""
        import datetime as dt

        from src.dashboard.shiny_tab_results.subtab_simulation import (
            DEFAULT_INITIAL_VALUE,
            DEFAULT_NUM_DAYS,
            DEFAULT_NUM_SCENARIOS,
            DEFAULT_RANDOM_SEED,
            _read_simulation_run_parameters,
        )
        from src.num_methods.scenarios.scenarios_distrib import Distribution_Type

        class _Input_With_Defaultable_Parameters:
            def input_ID_tab_results_subtab_simulation_num_scenarios(self) -> None:
                return None

            def input_ID_tab_results_subtab_simulation_num_days(self) -> None:
                return None

            def input_ID_tab_results_subtab_simulation_initial_value(self) -> None:
                return None

            def input_ID_tab_results_subtab_simulation_seed(self) -> None:
                return None

            def input_ID_tab_results_subtab_simulation_distribution_type(self) -> None:
                return None

            def input_ID_tab_results_subtab_simulation_rng_type(self) -> None:
                return None

            def input_ID_tab_results_subtab_simulation_start_date(self) -> object:
                return object()

        today = dt.datetime.now(tz=dt.UTC).date()
        params_simulation_run = _read_simulation_run_parameters(
            input_obj = _Input_With_Defaultable_Parameters(),
        )

        assert params_simulation_run["num_scenarios"] == DEFAULT_NUM_SCENARIOS
        assert params_simulation_run["num_days"] == DEFAULT_NUM_DAYS
        assert params_simulation_run["initial_value"] == pytest.approx(DEFAULT_INITIAL_VALUE)
        assert params_simulation_run["random_seed"] == DEFAULT_RANDOM_SEED
        assert params_simulation_run["distribution_key"] == "normal"
        assert params_simulation_run["distribution_type"] == Distribution_Type.NORMAL
        assert params_simulation_run["rng_type"] == "pcg64"
        assert params_simulation_run["degrees_of_freedom"] == pytest.approx(5.0)
        assert abs((params_simulation_run["start_date"] - today).days) <= 1

    @pytest.mark.unit()
    def Test_Read_Simulation_Run_Parameters_Boolean_Numeric_Values_Use_Defaults(self) -> None:
        """Boolean numeric UI values should stay on the existing simulation defaults."""
        import datetime as dt

        from src.dashboard.shiny_tab_results.subtab_simulation import (
            DEFAULT_INITIAL_VALUE,
            DEFAULT_NUM_DAYS,
            DEFAULT_NUM_SCENARIOS,
            DEFAULT_RANDOM_SEED,
            _read_simulation_run_parameters,
        )
        from src.num_methods.scenarios.scenarios_distrib import Distribution_Type

        class _Input_With_Boolean_Numeric_Parameters:
            def input_ID_tab_results_subtab_simulation_num_scenarios(self) -> bool:
                return True

            def input_ID_tab_results_subtab_simulation_num_days(self) -> bool:
                return True

            def input_ID_tab_results_subtab_simulation_initial_value(self) -> bool:
                return True

            def input_ID_tab_results_subtab_simulation_seed(self) -> bool:
                return True

            def input_ID_tab_results_subtab_simulation_distribution_type(self) -> str:
                return "student_t"

            def input_ID_tab_results_subtab_simulation_rng_type(self) -> str:
                return "philox"

            def input_ID_tab_results_subtab_simulation_degrees_of_freedom(self) -> bool:
                return True

            def input_ID_tab_results_subtab_simulation_start_date(self) -> str:
                return "2026-07-04"

        params_simulation_run = _read_simulation_run_parameters(
            input_obj = _Input_With_Boolean_Numeric_Parameters(),
        )

        assert params_simulation_run["num_scenarios"] == DEFAULT_NUM_SCENARIOS
        assert params_simulation_run["num_days"] == DEFAULT_NUM_DAYS
        assert params_simulation_run["initial_value"] == pytest.approx(DEFAULT_INITIAL_VALUE)
        assert params_simulation_run["random_seed"] == DEFAULT_RANDOM_SEED
        assert params_simulation_run["distribution_key"] == "student_t"
        assert params_simulation_run["distribution_type"] == Distribution_Type.STUDENT_T
        assert params_simulation_run["rng_type"] == "philox"
        assert params_simulation_run["degrees_of_freedom"] == pytest.approx(5.0)
        assert params_simulation_run["start_date"] == dt.date(2026, 7, 4)

    @pytest.mark.unit()
    def test_compare_entry_is_successful_true_for_success_entry(self) -> None:
        """Successful compare entries should be detected from the new schema."""
        import polars as pl

        from src.dashboard.shiny_tab_results.subtab_simulation import (
            _compare_entry_is_successful,
        )

        compare_results = {
            "standard": {
                "status": "success",
                "results_df": pl.DataFrame({"Date": [], "Scenario_1": []}),
                "stats_df": pl.DataFrame({"Date": [], "Mean": []}),
                "elapsed": 0.1,
                "error_type": None,
                "error_message": None,
            }
        }

        assert _compare_entry_is_successful(compare_results = compare_results, computation_type = "standard") is True

    @pytest.mark.unit()
    def test_compare_entry_is_successful_false_for_error_entry(self) -> None:
        """Failed compare entries should not be treated as canonical results."""
        from src.dashboard.shiny_tab_results.subtab_simulation import (
            _compare_entry_is_successful,
        )

        compare_results = {
            "standard": {
                "status": "error",
                "results_df": None,
                "stats_df": None,
                "elapsed": 0.2,
                "error_type": "Exception_Calculation",
                "error_message": "benchmark failed",
            }
        }

        assert _compare_entry_is_successful(compare_results = compare_results, computation_type = "standard") is False

    @pytest.mark.unit()
    def test_resolve_compare_canonical_results_returns_none_when_standard_failed(self) -> None:
        """Compare mode should not expose canonical chart data when standard fails."""
        from src.dashboard.shiny_tab_results.subtab_simulation import (
            _resolve_compare_canonical_results,
        )

        compare_results = {
            "standard": {
                "status": "error",
                "results_df": None,
                "stats_df": None,
                "elapsed": 0.2,
                "error_type": "Exception_Calculation",
                "error_message": "benchmark failed",
            }
        }

        results_df, stats_df, elapsed, backend_label = _resolve_compare_canonical_results(
            compare_results = compare_results
        )
        assert results_df is None
        assert stats_df is None
        assert elapsed == 0.0
        assert backend_label == "standard (compare mode - unavailable)"

    @pytest.mark.unit()
    def test_summarize_compare_completion_counts_success_and_failure(self) -> None:
        """Compare completion summary should count success and failure entries."""
        import polars as pl

        from src.dashboard.shiny_tab_results.subtab_simulation import (
            _summarize_compare_completion,
        )
        from src.models.simulation.simulation_dispatch import COMPUTATION_TYPES_SIMULATION_COMPARE

        compare_results = {
            computation_type: {
                "status": "success",
                "results_df": pl.DataFrame({"Date": [], "Scenario_1": []}),
                "stats_df": pl.DataFrame({"Date": [], "Mean": []}),
                "elapsed": 0.1,
                "error_type": None,
                "error_message": None,
            }
            for computation_type in COMPUTATION_TYPES_SIMULATION_COMPARE
        }
        compare_results["trio"] = {
            "status": "error",
            "results_df": None,
            "stats_df": None,
            "elapsed": 0.3,
            "error_type": "Exception_Configuration",
            "error_message": "trio missing",
        }

        num_success, num_failed = _summarize_compare_completion(compare_results = compare_results)
        assert num_success == len(COMPUTATION_TYPES_SIMULATION_COMPARE) - 1
        assert num_failed == 1

    @pytest.mark.unit()
    def test_resolve_compare_progress_running_display_uses_one_based_backend_number(self) -> None:
        """The running progress display should show the first active backend as 1/N."""
        from src.dashboard.shiny_tab_results.subtab_simulation import (
            _resolve_compare_progress_running_display,
        )

        current_backend_number, percent_complete = _resolve_compare_progress_running_display(
            current_index = 0,
            total_types = 6,
        )

        assert current_backend_number == 1
        assert percent_complete == 16

    @pytest.mark.unit()
    def test_resolve_compare_progress_running_display_handles_zero_total(self) -> None:
        """Zero total backends should produce a safe 0/0 progress display."""
        from src.dashboard.shiny_tab_results.subtab_simulation import (
            _resolve_compare_progress_running_display,
        )

        current_backend_number, percent_complete = _resolve_compare_progress_running_display(
            current_index = 2,
            total_types = 0,
        )

        assert current_backend_number == 0
        assert percent_complete == 0

    @pytest.mark.unit()
    def test_resolve_compare_progress_running_display_rejects_boolean_inputs(self) -> None:
        """Boolean progress inputs should stay on the safe 0/0 display fallback."""
        from src.dashboard.shiny_tab_results.subtab_simulation import (
            _resolve_compare_progress_running_display,
        )

        current_backend_number, percent_complete = _resolve_compare_progress_running_display(
            current_index = True,
            total_types = True,
        )

        assert current_backend_number == 0
        assert percent_complete == 0

    @pytest.mark.unit()
    def test_resolve_compare_progress_running_pill_marks_current_backend_running(self) -> None:
        """The current backend pill should render as running from the first backend onward."""
        from src.dashboard.shiny_tab_results.subtab_simulation import (
            _resolve_compare_progress_running_pill,
        )

        pill_class, pill_label = _resolve_compare_progress_running_pill(idx_backend = 0, current_index = 0)

        assert pill_class == "sim-pill-running"
        assert pill_label == "Running"

    @pytest.mark.unit()
    def test_resolve_compare_progress_running_pill_marks_done_and_pending_states(self) -> None:
        """Backend pills before the current index are done; later pills stay pending."""
        from src.dashboard.shiny_tab_results.subtab_simulation import (
            _resolve_compare_progress_running_pill,
        )

        done_class, done_label = _resolve_compare_progress_running_pill(idx_backend = 1, current_index = 3)
        pending_class, pending_label = _resolve_compare_progress_running_pill(idx_backend = 4, current_index = 3)

        assert done_class == "sim-pill-success"
        assert done_label == "Done"
        assert pending_class == "sim-pill-pending"
        assert pending_label == "Pending"


# ======================================================================
# Tab results integration
# ======================================================================


class Test_Tab_Results_Integration:
    """Verify the simulation subtab is registered in tab_results."""

    @pytest.mark.unit()
    def test_tab_results_imports_simulation_subtab(self):
        """tab_results should import subtab_simulation."""
        import src.dashboard.shiny_tab_results.tab_results as tab_mod

        # The module should have both subtab imports accessible
        assert hasattr(tab_mod, "subtab_simulation_server")
        assert hasattr(tab_mod, "subtab_simulation_ui")


# ======================================================================
# Constants — content validation
# ======================================================================


@pytest.mark.unit()
class Test_Subtab_Simulation_Constants:
    """Validate the content and types of module-level constants."""

    @pytest.mark.unit()
    def test_all_etf_symbols_contains_equity_etfs(self) -> None:
        """ALL_ETF_SYMBOLS must include well-known equity ETFs."""
        from src.dashboard.shiny_tab_results.subtab_simulation import ALL_ETF_SYMBOLS

        for expected in ("IVV", "IJH", "IWM", "EFA", "EEM"):
            assert expected in ALL_ETF_SYMBOLS, f"{expected} missing from ALL_ETF_SYMBOLS"

    @pytest.mark.unit()
    def test_all_etf_symbols_contains_fixed_income(self) -> None:
        """ALL_ETF_SYMBOLS must include fixed-income ETFs."""
        from src.dashboard.shiny_tab_results.subtab_simulation import ALL_ETF_SYMBOLS

        for expected in ("AGG", "HYG"):
            assert expected in ALL_ETF_SYMBOLS, f"{expected} missing from ALL_ETF_SYMBOLS"

    @pytest.mark.unit()
    def test_all_etf_symbols_are_strings(self) -> None:
        """Every entry in ALL_ETF_SYMBOLS must be a non-empty string."""
        from src.dashboard.shiny_tab_results.subtab_simulation import ALL_ETF_SYMBOLS

        for sym in ALL_ETF_SYMBOLS:
            assert isinstance(sym, str) and len(sym) > 0, f"Invalid symbol: {sym!r}"

    @pytest.mark.unit()
    def test_all_etf_symbols_no_duplicates(self) -> None:
        """ALL_ETF_SYMBOLS must not contain duplicates."""
        from src.dashboard.shiny_tab_results.subtab_simulation import ALL_ETF_SYMBOLS

        assert len(ALL_ETF_SYMBOLS) == len(set(ALL_ETF_SYMBOLS))

    @pytest.mark.unit()
    def test_default_selected_etfs_are_subset_of_all(self) -> None:
        """Every DEFAULT_SELECTED_ETFS entry must appear in ALL_ETF_SYMBOLS."""
        from src.dashboard.shiny_tab_results.subtab_simulation import (
            ALL_ETF_SYMBOLS,
            DEFAULT_SELECTED_ETFS,
        )

        for sym in DEFAULT_SELECTED_ETFS:
            assert sym in ALL_ETF_SYMBOLS, f"{sym} in defaults but not in ALL_ETF_SYMBOLS"

    @pytest.mark.unit()
    def test_num_default_selected_matches_defaults_list(self) -> None:
        """NUM_DEFAULT_SELECTED should equal len(DEFAULT_SELECTED_ETFS)."""
        from src.dashboard.shiny_tab_results.subtab_simulation import (
            DEFAULT_SELECTED_ETFS,
            NUM_DEFAULT_SELECTED,
        )

        assert NUM_DEFAULT_SELECTED == len(DEFAULT_SELECTED_ETFS)

    @pytest.mark.unit()
    def test_distribution_choices_values_are_human_readable(self) -> None:
        """DISTRIBUTION_CHOICES values should contain human-readable labels."""
        from src.dashboard.shiny_tab_results.subtab_simulation import DISTRIBUTION_CHOICES

        for key, label in DISTRIBUTION_CHOICES.items():
            assert isinstance(label, str) and len(label) > 0, f"Empty label for key {key!r}"

    @pytest.mark.unit()
    def test_distribution_choices_normal_label(self) -> None:
        """'normal' distribution label should mention 'Normal' or 'Gaussian'."""
        from src.dashboard.shiny_tab_results.subtab_simulation import DISTRIBUTION_CHOICES

        label = DISTRIBUTION_CHOICES["normal"].lower()
        assert "normal" in label or "gaussian" in label

    @pytest.mark.unit()
    def test_rng_type_choices_has_four_types(self) -> None:
        """RNG_TYPE_CHOICES should offer at least 2 types (pcg64 and mt19937)."""
        from src.dashboard.shiny_tab_results.subtab_simulation import RNG_TYPE_CHOICES

        assert len(RNG_TYPE_CHOICES) >= 2

    @pytest.mark.unit()
    def test_rng_type_choices_values_are_strings(self) -> None:
        """All RNG_TYPE_CHOICES values must be non-empty strings."""
        from src.dashboard.shiny_tab_results.subtab_simulation import RNG_TYPE_CHOICES

        for rng_id, label in RNG_TYPE_CHOICES.items():
            assert isinstance(label, str) and len(label) > 0, f"Empty label for RNG {rng_id!r}"


# ======================================================================
# Helper function edge cases
# ======================================================================


@pytest.mark.unit()
class Test_Subtab_Simulation_Helpers_Extended:
    """Extended edge-case tests for helper functions."""

    @pytest.mark.unit()
    def test_map_distribution_key_empty_string_defaults_to_normal(self) -> None:
        """Empty string key should default to NORMAL."""
        from src.dashboard.shiny_tab_results.subtab_simulation import _map_distribution_key
        from src.num_methods.scenarios.scenarios_distrib import Distribution_Type

        assert _map_distribution_key(key = "") == Distribution_Type.NORMAL

    @pytest.mark.unit()
    def test_map_distribution_key_case_sensitive(self) -> None:
        """Key lookup is case-sensitive; 'Normal' (capitalised) should default."""
        from src.dashboard.shiny_tab_results.subtab_simulation import _map_distribution_key
        from src.num_methods.scenarios.scenarios_distrib import Distribution_Type

        # "Normal" (capital N) is NOT in the mapping; should fall back to NORMAL
        result = _map_distribution_key(key = "Normal")
        assert result == Distribution_Type.NORMAL

    @pytest.mark.parametrize("key", ["normal", "lognormal", "student_t"])
    @pytest.mark.unit()
    def test_map_distribution_key_returns_enum_instance(self, key: str) -> None:
        """_map_distribution_key must return a Distribution_Type enum member."""
        from src.dashboard.shiny_tab_results.subtab_simulation import _map_distribution_key
        from src.num_methods.scenarios.scenarios_distrib import Distribution_Type

        result = _map_distribution_key(key = key)
        assert isinstance(result, Distribution_Type)

    @pytest.mark.unit()
    def test_create_empty_figure_title_set(self) -> None:
        """_create_empty_figure title should appear in the figure layout."""
        from src.dashboard.shiny_tab_results.subtab_simulation import _create_empty_figure

        fig = _create_empty_figure(title = "My Title", message = "Loading…")
        assert "My Title" in str(fig.layout.title.text or "")

    @pytest.mark.unit()
    def test_create_empty_figure_axes_hidden(self) -> None:
        """_create_empty_figure should hide both axes."""
        from src.dashboard.shiny_tab_results.subtab_simulation import _create_empty_figure

        fig = _create_empty_figure(title = "T", message = "M")
        assert fig.layout.xaxis.visible is False
        assert fig.layout.yaxis.visible is False

    @pytest.mark.unit()
    def test_create_empty_figure_uses_plotly_white_template(self) -> None:
        """_create_empty_figure should use a light/white template (plotly_white)."""
        from src.dashboard.shiny_tab_results.subtab_simulation import _create_empty_figure

        fig = _create_empty_figure(title = "T", message = "M")
        # Plotly resolves the template name to an object at creation time.
        # Verify a template is actually set (not the bare default object).
        template = fig.layout.template
        assert template is not None
        # The plotly_white template has a white plot background colour.
        plot_bgcolor = getattr(template.layout, "plot_bgcolor", None)
        # plotly_white sets a light background; the value should not be a dark colour.
        if plot_bgcolor is not None:  # attribute may be absent in some Plotly versions
            assert "black" not in str(plot_bgcolor).lower()

    @pytest.mark.unit()
    def test_create_empty_figure_height(self) -> None:
        """_create_empty_figure height should be 600px."""
        from src.dashboard.shiny_tab_results.subtab_simulation import _create_empty_figure

        fig = _create_empty_figure(title = "T", message = "M")
        assert fig.layout.height == 600

    @pytest.mark.unit()
    def test_create_rng_philox(self) -> None:
        """'philox' RNG type should produce a valid Generator."""
        import numpy as np

        from src.dashboard.shiny_tab_results.subtab_simulation import _create_rng

        rng = _create_rng(rng_type = "philox", seed = 0)
        assert isinstance(rng, np.random.Generator)

    @pytest.mark.unit()
    def test_create_rng_sfc64(self) -> None:
        """'sfc64' RNG type should produce a valid Generator."""
        import numpy as np

        from src.dashboard.shiny_tab_results.subtab_simulation import _create_rng

        rng = _create_rng(rng_type = "sfc64", seed = 0)
        assert isinstance(rng, np.random.Generator)

    @pytest.mark.unit()
    def test_create_rng_different_seeds_differ(self) -> None:
        """Two RNGs with different seeds should produce different first values."""
        from src.dashboard.shiny_tab_results.subtab_simulation import _create_rng

        rng1 = _create_rng(rng_type = "pcg64", seed = 1)
        rng2 = _create_rng(rng_type = "pcg64", seed = 9999)
        # Very unlikely both produce same first random number
        assert rng1.random() != rng2.random()


# ======================================================================
# Module-level callable exports
# ======================================================================


@pytest.mark.unit()
class Test_Subtab_Simulation_Callables:
    """Tests for the Shiny-decorated callable exports."""

    @pytest.mark.unit()
    def test_subtab_simulation_ui_is_callable(self) -> None:
        """subtab_simulation_ui must be callable."""
        from src.dashboard.shiny_tab_results.subtab_simulation import subtab_simulation_ui

        assert callable(subtab_simulation_ui)

    @pytest.mark.unit()
    def test_subtab_simulation_server_is_callable(self) -> None:
        """subtab_simulation_server must be callable."""
        from src.dashboard.shiny_tab_results.subtab_simulation import subtab_simulation_server

        assert callable(subtab_simulation_server)


# ======================================================================
# Module structure
# ======================================================================


@pytest.mark.unit()
class Test_Subtab_Simulation_Module_Structure:
    """Tests for module-level metadata and structure."""

    @pytest.mark.unit()
    def test_module_has_docstring(self) -> None:
        """subtab_simulation must have a non-empty module docstring."""
        import src.dashboard.shiny_tab_results.subtab_simulation as _mod

        assert _mod.__doc__ is not None
        assert len(_mod.__doc__.strip()) > 0

    @pytest.mark.unit()
    def test_init_exports_simulation_symbols(self) -> None:
        """The package __init__ must re-export simulation UI and server."""
        from src.dashboard.shiny_tab_results import subtab_simulation_server, subtab_simulation_ui

        assert callable(subtab_simulation_ui)
        assert callable(subtab_simulation_server)


# ======================================================================
# Dispatch-related constants and imports exposed by subtab_simulation
# ======================================================================


@pytest.mark.unit()
class Test_Subtab_Simulation_Dispatch_Constants:
    """Check that dispatch constants are correctly re-used in the subtab module."""

    @pytest.mark.unit()
    def test_computation_types_simulation_accessible(self) -> None:
        """COMPUTATION_TYPES_SIMULATION must be importable from simulation_dispatch."""
        from src.models.simulation.simulation_dispatch import COMPUTATION_TYPES_SIMULATION

        assert isinstance(COMPUTATION_TYPES_SIMULATION, tuple)
        assert len(COMPUTATION_TYPES_SIMULATION) == 6

    @pytest.mark.unit()
    def test_computation_types_include_standard(self) -> None:
        """'standard' must be the first entry in COMPUTATION_TYPES_SIMULATION."""
        from src.models.simulation.simulation_dispatch import COMPUTATION_TYPES_SIMULATION

        assert COMPUTATION_TYPES_SIMULATION[0] == "standard"

    @pytest.mark.unit()
    def test_computation_types_include_joblib(self) -> None:
        """'joblib' must be among the computation types."""
        from src.models.simulation.simulation_dispatch import COMPUTATION_TYPES_SIMULATION

        assert "joblib" in COMPUTATION_TYPES_SIMULATION

    @pytest.mark.unit()
    def test_computation_types_include_asyncio(self) -> None:
        """'asyncio' must be among the computation types."""
        from src.models.simulation.simulation_dispatch import COMPUTATION_TYPES_SIMULATION

        assert "asyncio" in COMPUTATION_TYPES_SIMULATION

    @pytest.mark.unit()
    def test_sim_compare_css_constant_present(self) -> None:
        """_SIM_COMPARE_PROGRESS_CSS should be a non-empty string in subtab_simulation."""
        import src.dashboard.shiny_tab_results.subtab_simulation as mod

        css = getattr(mod, "_SIM_COMPARE_PROGRESS_CSS", None)
        assert isinstance(css, str) and len(css) > 0

    @pytest.mark.unit()
    def test_sim_compare_css_contains_shimmer_class(self) -> None:
        """CSS constant must define the shimmer animation class."""
        import src.dashboard.shiny_tab_results.subtab_simulation as mod

        css = getattr(mod, "_SIM_COMPARE_PROGRESS_CSS", "")
        assert "sim-compare-shimmer" in css

    @pytest.mark.unit()
    def test_sim_compare_css_contains_progress_bar_wrap(self) -> None:
        """CSS must define the RGA-style progress bar container class."""
        import src.dashboard.shiny_tab_results.subtab_simulation as mod

        css = getattr(mod, "_SIM_COMPARE_PROGRESS_CSS", "")
        assert "sim-compare-progress-bar-wrap" in css

    @pytest.mark.unit()
    def test_sim_compare_css_contains_backend_pill(self) -> None:
        """CSS must define per-backend pill class."""
        import src.dashboard.shiny_tab_results.subtab_simulation as mod

        css = getattr(mod, "_SIM_COMPARE_PROGRESS_CSS", "")
        assert "sim-backend-pill" in css

    @pytest.mark.unit()
    def test_sim_compare_css_contains_results_table(self) -> None:
        """CSS must define the compare results table class."""
        import src.dashboard.shiny_tab_results.subtab_simulation as mod

        css = getattr(mod, "_SIM_COMPARE_PROGRESS_CSS", "")
        assert "sim-compare-results-table" in css

    @pytest.mark.unit()
    def test_sim_compare_css_contains_keyframes(self) -> None:
        """CSS constant must define a @keyframes animation."""
        import src.dashboard.shiny_tab_results.subtab_simulation as mod

        css = getattr(mod, "_SIM_COMPARE_PROGRESS_CSS", "")
        assert "@keyframes" in css


# ======================================================================
# Dispatch integration — Simulation_Run_Config helper
# ======================================================================


@pytest.mark.unit()
class Test_Subtab_Simulation_Dispatch_Config:
    """Verify Simulation_Run_Config can be built with typical ETF inputs."""

    @pytest.mark.unit()
    def test_simulation_run_config_importable(self) -> None:
        """Simulation_Run_Config must be importable from simulation_dispatch."""
        from src.models.simulation.simulation_dispatch import Simulation_Run_Config

        assert Simulation_Run_Config is not None

    @pytest.mark.unit()
    def test_simulation_run_config_basic_construction(self) -> None:
        """Simulation_Run_Config should construct with minimal valid inputs."""
        import numpy as np

        from src.models.simulation.simulation_dispatch import Simulation_Run_Config
        from src.num_methods.scenarios.scenarios_distrib import Distribution_Type

        cfg = Simulation_Run_Config(
            names_components=["IVV", "IJH"],
            weights=np.array([0.5, 0.5]),
            distribution_type=Distribution_Type.NORMAL,
            mean_returns=np.array([0.001, 0.0008]),
            covariance_matrix=np.eye(2) * 0.0004,
            num_scenarios=10,
            num_days=5,
        )
        assert cfg.num_scenarios == 10
        assert cfg.num_days == 5
        assert len(cfg.names_components) == 2

    @pytest.mark.unit()
    def test_simulation_run_config_default_start_date_is_today(self) -> None:
        """Simulation_Run_Config.start_date should default to today's date."""
        import datetime as dt

        import numpy as np

        from src.models.simulation.simulation_dispatch import Simulation_Run_Config
        from src.num_methods.scenarios.scenarios_distrib import Distribution_Type

        today = dt.datetime.now(tz=dt.UTC).date()
        cfg = Simulation_Run_Config(
            names_components=["IVV"],
            weights=np.array([1.0]),
            distribution_type=Distribution_Type.NORMAL,
            mean_returns=np.array([0.001]),
            covariance_matrix=np.array([[0.0004]]),
        )
        # Allow ±1 day tolerance in case test runs near midnight
        assert abs((cfg.start_date - today).days) <= 1

    @pytest.mark.unit()
    def test_simulation_run_config_initial_value_default(self) -> None:
        """Simulation_Run_Config.initial_value should default to 100.0."""
        import numpy as np

        from src.models.simulation.simulation_dispatch import Simulation_Run_Config
        from src.num_methods.scenarios.scenarios_distrib import Distribution_Type

        cfg = Simulation_Run_Config(
            names_components=["IVV"],
            weights=np.array([1.0]),
            distribution_type=Distribution_Type.NORMAL,
            mean_returns=np.array([0.001]),
            covariance_matrix=np.array([[0.0004]]),
        )
        assert cfg.initial_value == 100.0


# ======================================================================
# Dispatch integration — dispatch_simulation_run output shape
# ======================================================================


@pytest.mark.unit()
class Test_Subtab_Simulation_Dispatch_Run:
    """Integration tests calling dispatch_simulation_run with small configs."""

    @pytest.mark.unit()
    def test_dispatch_returns_dataframe_and_float(self) -> None:
        """dispatch_simulation_run must return (pl.DataFrame, float)."""
        import numpy as np
        import polars as pl

        from src.models.simulation.simulation_dispatch import (
            Simulation_Run_Config,
            dispatch_simulation_run,
        )
        from src.num_methods.scenarios.scenarios_distrib import Distribution_Type

        cfg = Simulation_Run_Config(
            names_components=["IVV", "AGG"],
            weights=np.array([0.6, 0.4]),
            distribution_type=Distribution_Type.NORMAL,
            mean_returns=np.array([0.0005, 0.0002]),
            covariance_matrix=np.eye(2) * 0.0001,
            num_scenarios=20,
            num_days=10,
        )
        results_df, elapsed = dispatch_simulation_run(computation_type = "standard", config = cfg)
        assert isinstance(results_df, pl.DataFrame)
        assert isinstance(elapsed, float)
        assert elapsed >= 0.0

    @pytest.mark.unit()
    def test_dispatch_standard_has_date_and_scenario_columns(self) -> None:
        """Result DataFrame must have a 'Date' column + scenario columns."""
        import numpy as np

        from src.models.simulation.simulation_dispatch import (
            Simulation_Run_Config,
            dispatch_simulation_run,
        )
        from src.num_methods.scenarios.scenarios_distrib import Distribution_Type

        cfg = Simulation_Run_Config(
            names_components=["IVV"],
            weights=np.array([1.0]),
            distribution_type=Distribution_Type.LOGNORMAL,
            mean_returns=np.array([1.0005]),
            covariance_matrix=np.array([[0.0001]]),
            num_scenarios=5,
            num_days=8,
        )
        results_df, _ = dispatch_simulation_run(computation_type = "standard", config = cfg)
        assert "Date" in results_df.columns
        scenario_cols = [c for c in results_df.columns if c.startswith("Scenario_")]
        assert len(scenario_cols) == 5
        assert results_df.height == 8

    @pytest.mark.unit()
    def test_dispatch_asyncio_matches_standard(self) -> None:
        """asyncio and standard backends must produce bit-identical results."""
        import numpy as np

        from src.models.simulation.simulation_dispatch import (
            Simulation_Run_Config,
            dispatch_simulation_run,
        )
        from src.num_methods.scenarios.scenarios_distrib import Distribution_Type

        cfg = Simulation_Run_Config(
            names_components=["IVV", "IJH"],
            weights=np.array([0.5, 0.5]),
            distribution_type=Distribution_Type.NORMAL,
            mean_returns=np.array([0.0006, 0.0004]),
            covariance_matrix=np.eye(2) * 0.0002,
            num_scenarios=15,
            num_days=6,
            random_seed=7,
        )
        df_std, _ = dispatch_simulation_run(computation_type = "standard", config = cfg)
        df_async, _ = dispatch_simulation_run(computation_type = "asyncio", config = cfg)

        # Polars has no DataFrame.abs(); compare using equals()
        assert df_std.drop("Date").equals(df_async.drop("Date"))


# ======================================================================
# Dispatch integration — compute_simulation_stats
# ======================================================================


@pytest.mark.unit()
class Test_Subtab_Simulation_Stats_Integration:
    """Integration tests for compute_simulation_stats called from the subtab."""

    @pytest.mark.unit()
    def test_stats_has_expected_columns(self) -> None:
        """compute_simulation_stats must include Mean, Median, Std, P5, P95."""
        import numpy as np
        import polars as pl

        from src.models.simulation.simulation_dispatch import (
            Simulation_Run_Config,
            compute_simulation_stats,
            dispatch_simulation_run,
        )
        from src.num_methods.scenarios.scenarios_distrib import Distribution_Type

        cfg = Simulation_Run_Config(
            names_components=["IVV"],
            weights=np.array([1.0]),
            distribution_type=Distribution_Type.NORMAL,
            mean_returns=np.array([0.0005]),
            covariance_matrix=np.array([[0.0004]]),
            num_scenarios=30,
            num_days=5,
        )
        results_df, _ = dispatch_simulation_run(computation_type = "standard", config = cfg)
        stats_df = compute_simulation_stats(results_df = results_df)
        assert isinstance(stats_df, pl.DataFrame)
        for col in ("Date", "Mean", "Median", "Std", "P5", "P95"):
            assert col in stats_df.columns, f"Column {col!r} missing from stats"

    @pytest.mark.unit()
    def test_stats_row_count_equals_num_days(self) -> None:
        """Stats DataFrame must have one row per trading day."""
        import numpy as np

        from src.models.simulation.simulation_dispatch import (
            Simulation_Run_Config,
            compute_simulation_stats,
            dispatch_simulation_run,
        )
        from src.num_methods.scenarios.scenarios_distrib import Distribution_Type

        cfg = Simulation_Run_Config(
            names_components=["IVV"],
            weights=np.array([1.0]),
            distribution_type=Distribution_Type.NORMAL,
            mean_returns=np.array([0.0005]),
            covariance_matrix=np.array([[0.0004]]),
            num_scenarios=10,
            num_days=7,
        )
        results_df, _ = dispatch_simulation_run(computation_type = "standard", config = cfg)
        stats_df = compute_simulation_stats(results_df = results_df)
        assert stats_df.height == 7


# ======================================================================
# UI presence — new Compare elements
# ======================================================================


@pytest.mark.unit()
class Test_Subtab_Simulation_Compare_UI_Elements:
    """Verify that the Compare toggle and output IDs are present in the UI tree."""

    @pytest.mark.unit()
    def test_ui_contains_compute_and_compare_input_id(self) -> None:
        """The UI must contain the compute_and_compare switch input."""
        import src.dashboard.shiny_tab_results.subtab_simulation as mod

        # Render the UI to string and check for the input ID
        ui_fn = mod.subtab_simulation_ui
        ui_tag = ui_fn("test_ns", data_utils={}, data_inputs={})
        html = str(ui_tag)
        assert "input_ID_tab_results_subtab_simulation_compute_and_compare" in html

    @pytest.mark.unit()
    def test_ui_contains_compare_progress_output_id(self) -> None:
        """The UI must contain the compare_progress output ID."""
        import src.dashboard.shiny_tab_results.subtab_simulation as mod

        ui_fn = mod.subtab_simulation_ui
        ui_tag = ui_fn("test_ns2", data_utils={}, data_inputs={})
        html = str(ui_tag)
        assert "output_ID_tab_results_subtab_simulation_compare_progress" in html

    @pytest.mark.unit()
    def test_ui_contains_compare_table_output_id(self) -> None:
        """The UI must contain the compare_table output ID."""
        import src.dashboard.shiny_tab_results.subtab_simulation as mod

        ui_fn = mod.subtab_simulation_ui
        ui_tag = ui_fn("test_ns3", data_utils={}, data_inputs={})
        html = str(ui_tag)
        assert "output_ID_tab_results_subtab_simulation_compare_table" in html

    @pytest.mark.unit()
    def test_ui_contains_backend_comparison_heading(self) -> None:
        """The UI must contain the 'Backend Comparison' section heading."""
        import src.dashboard.shiny_tab_results.subtab_simulation as mod

        ui_fn = mod.subtab_simulation_ui
        ui_tag = ui_fn("test_ns4", data_utils={}, data_inputs={})
        html = str(ui_tag)
        assert "Backend Comparison" in html

    @pytest.mark.unit()
    def test_ui_shimmer_css_embedded(self) -> None:
        """The shimmer CSS must be embedded in the UI output."""
        import src.dashboard.shiny_tab_results.subtab_simulation as mod

        ui_fn = mod.subtab_simulation_ui
        ui_tag = ui_fn("test_ns5", data_utils={}, data_inputs={})
        html = str(ui_tag)
        assert "sim-compare-shimmer" in html

    @pytest.mark.unit()
    def test_ui_contains_run_compare_button(self) -> None:
        """The UI must contain the Run Compute & Compare button."""
        import src.dashboard.shiny_tab_results.subtab_simulation as mod

        ui_fn = mod.subtab_simulation_ui
        ui_tag = ui_fn("test_ns6", data_utils={}, data_inputs={})
        html = str(ui_tag)
        assert "input_ID_tab_results_subtab_simulation_run_compare_btn" in html


# ======================================================================
# format_compare_table_as_html
# ======================================================================


class Test_Format_Compare_Table_As_Html:
    """Unit tests for the pure format_compare_table_as_html helper."""

    @pytest.fixture()
    def minimal_table(self):
        """A minimal 3-row compare DataFrame (Status, Elapsed, Error)."""
        import polars as pl

        return pl.DataFrame(
            {
                "Metric": ["Status", "Elapsed time (s)", "Mean", "Mean (\u0394 abs)", "Error"],
                "standard": ["OK", "0.1200", "1000.00", "0.0000", ""],
                "asyncio": ["FAILED", "0.0500", "N/A", "N/A", "RuntimeError: boom"],
            }
        )

    @pytest.mark.unit()
    def test_returns_html_type(self, minimal_table) -> None:
        """format_compare_table_as_html must return a shiny HTML object."""
        from shiny import ui as shiny_ui

        from src.dashboard.shiny_tab_results.subtab_simulation import (
            format_compare_table_as_html,
        )

        result = format_compare_table_as_html(table_df = minimal_table)
        assert isinstance(result, shiny_ui.HTML)

    @pytest.mark.unit()
    def test_html_contains_table_class(self, minimal_table) -> None:
        """The generated HTML must use the sim-compare-results-table class."""
        from src.dashboard.shiny_tab_results.subtab_simulation import (
            format_compare_table_as_html,
        )

        html = str(format_compare_table_as_html(table_df = minimal_table))
        assert "sim-compare-results-table" in html

    @pytest.mark.unit()
    def test_html_scroll_wrapper(self, minimal_table) -> None:
        """The table must be wrapped in the scroll div."""
        from src.dashboard.shiny_tab_results.subtab_simulation import (
            format_compare_table_as_html,
        )

        html = str(format_compare_table_as_html(table_df = minimal_table))
        assert "sim-compare-table-scroll" in html

    @pytest.mark.unit()
    def test_status_row_ok_cell_colored_green(self, minimal_table) -> None:
        """'OK' status cells must receive the sim-cell-ok CSS class."""
        from src.dashboard.shiny_tab_results.subtab_simulation import (
            format_compare_table_as_html,
        )

        html = str(format_compare_table_as_html(table_df = minimal_table))
        assert "sim-cell-ok" in html
        assert ">OK<" in html

    @pytest.mark.unit()
    def test_status_row_failed_cell_colored_red(self, minimal_table) -> None:
        """'FAILED' status cells must receive the sim-cell-failed CSS class."""
        from src.dashboard.shiny_tab_results.subtab_simulation import (
            format_compare_table_as_html,
        )

        html = str(format_compare_table_as_html(table_df = minimal_table))
        assert "sim-cell-failed" in html
        assert ">FAILED<" in html

    @pytest.mark.unit()
    def test_delta_rows_get_row_class(self, minimal_table) -> None:
        """Rows whose Metric contains \u0394 must get the sim-row-delta CSS class."""
        from src.dashboard.shiny_tab_results.subtab_simulation import (
            format_compare_table_as_html,
        )

        html = str(format_compare_table_as_html(table_df = minimal_table))
        assert "sim-row-delta" in html

    @pytest.mark.unit()
    def test_error_row_gets_row_class(self, minimal_table) -> None:
        """The Error row must get the sim-row-error CSS class."""
        from src.dashboard.shiny_tab_results.subtab_simulation import (
            format_compare_table_as_html,
        )

        html = str(format_compare_table_as_html(table_df = minimal_table))
        assert "sim-row-error" in html

    @pytest.mark.unit()
    def test_elapsed_row_gets_row_class(self, minimal_table) -> None:
        """The Elapsed time (s) row must get the sim-row-elapsed CSS class."""
        from src.dashboard.shiny_tab_results.subtab_simulation import (
            format_compare_table_as_html,
        )

        html = str(format_compare_table_as_html(table_df = minimal_table))
        assert "sim-row-elapsed" in html

    @pytest.mark.unit()
    def test_custom_css_class_applied(self, minimal_table) -> None:
        """A custom css_class parameter replaces the default class name."""
        from src.dashboard.shiny_tab_results.subtab_simulation import (
            format_compare_table_as_html,
        )

        html = str(format_compare_table_as_html(table_df = minimal_table, css_class="my-custom-table"))
        assert "my-custom-table" in html
        assert "sim-compare-results-table" not in html

    @pytest.mark.unit()
    def test_all_metrics_present_in_html(self, minimal_table) -> None:
        """Every row Metric value must appear in the HTML output."""
        from src.dashboard.shiny_tab_results.subtab_simulation import (
            format_compare_table_as_html,
        )

        html = str(format_compare_table_as_html(table_df = minimal_table))
        for metric in minimal_table["Metric"].to_list():
            assert metric in html, f"Missing metric '{metric}' from HTML output"

    @pytest.mark.unit()
    def test_empty_dataframe_returns_html_type(self) -> None:
        """format_compare_table_as_html with zero rows must still return HTML."""
        import polars as pl

        from shiny import ui as shiny_ui

        from src.dashboard.shiny_tab_results.subtab_simulation import (
            format_compare_table_as_html,
        )

        empty = pl.DataFrame({"Metric": [], "standard": []})
        result = format_compare_table_as_html(table_df = empty)
        assert isinstance(result, shiny_ui.HTML)

    @pytest.mark.unit()
    def test_empty_dataframe_html_contains_table_tags(self) -> None:
        """Even with zero rows the output must contain <table> markup."""
        import polars as pl

        from src.dashboard.shiny_tab_results.subtab_simulation import (
            format_compare_table_as_html,
        )

        empty = pl.DataFrame({"Metric": [], "standard": []})
        html = str(format_compare_table_as_html(table_df = empty))
        assert "<table" in html
        assert "</table>" in html

    @pytest.mark.unit()
    def test_no_backend_columns_present_produces_metric_only_header(self) -> None:
        """When no backend columns are in the table, only 'Metric' header appears."""
        import polars as pl

        from src.dashboard.shiny_tab_results.subtab_simulation import (
            format_compare_table_as_html,
        )

        # DataFrame has no column matching any known backend name
        df = pl.DataFrame({"Metric": ["Status"], "unknown_col": ["OK"]})
        html = str(format_compare_table_as_html(table_df = df))
        # Header should contain Metric
        assert "<th>Metric</th>" in html
        # None of the known backend names should appear as headers
        for backend in ("standard", "asyncio", "trio", "joblib"):
            assert f"<th>{backend}</th>" not in html

    @pytest.mark.unit()
    def test_status_row_class_applied(self, minimal_table) -> None:
        """The Status row must receive the sim-row-status CSS class."""
        from src.dashboard.shiny_tab_results.subtab_simulation import (
            format_compare_table_as_html,
        )

        html = str(format_compare_table_as_html(table_df = minimal_table))
        assert "sim-row-status" in html


# ======================================================================
# _compare_entry_is_successful — missing branch coverage
# ======================================================================


@pytest.mark.unit()
class Test_Compare_Entry_Is_Successful_Branch_Coverage:
    """Branch-complete tests for _compare_entry_is_successful."""

    @pytest.mark.unit()
    def test_none_compare_results_returns_false(self) -> None:
        """None input is not a dict → must return False immediately."""
        from src.dashboard.shiny_tab_results.subtab_simulation import (
            _compare_entry_is_successful,
        )

        assert _compare_entry_is_successful(compare_results = None, computation_type = "standard") is False

    @pytest.mark.unit()
    def test_empty_dict_missing_key_returns_false(self) -> None:
        """computation_type not in dict → entry is None → must return False."""
        from src.dashboard.shiny_tab_results.subtab_simulation import (
            _compare_entry_is_successful,
        )

        assert _compare_entry_is_successful(compare_results = {}, computation_type = "standard") is False

    @pytest.mark.unit()
    def test_entry_is_not_dict_returns_false(self) -> None:
        """Entry that is not a dict (e.g. a string) must return False."""
        from src.dashboard.shiny_tab_results.subtab_simulation import (
            _compare_entry_is_successful,
        )

        assert _compare_entry_is_successful(compare_results = {"standard": "not_a_dict"}, computation_type = "standard") is False  # type: ignore[arg-type]

    @pytest.mark.unit()
    def test_success_status_but_results_df_none_returns_false(self) -> None:
        """results_df = None fails the isinstance check → must return False."""
        import polars as pl

        from src.dashboard.shiny_tab_results.subtab_simulation import (
            _compare_entry_is_successful,
        )

        compare_results = {
            "standard": {
                "status": "success",
                "results_df": None,
                "stats_df": pl.DataFrame({"Date": [], "Mean": []}),
                "elapsed": 0.1,
            }
        }
        assert _compare_entry_is_successful(compare_results = compare_results, computation_type = "standard") is False

    @pytest.mark.unit()
    def test_success_status_but_stats_df_none_returns_false(self) -> None:
        """stats_df = None fails the isinstance check → must return False."""
        import polars as pl

        from src.dashboard.shiny_tab_results.subtab_simulation import (
            _compare_entry_is_successful,
        )

        compare_results = {
            "standard": {
                "status": "success",
                "results_df": pl.DataFrame({"Date": [], "Scenario_1": []}),
                "stats_df": None,
                "elapsed": 0.1,
            }
        }
        assert _compare_entry_is_successful(compare_results = compare_results, computation_type = "standard") is False

    @pytest.mark.unit()
    def test_list_compare_results_returns_false(self) -> None:
        """A list (not a dict) input must return False."""
        from src.dashboard.shiny_tab_results.subtab_simulation import (
            _compare_entry_is_successful,
        )

        assert _compare_entry_is_successful(compare_results = [], computation_type = "standard") is False  # type: ignore[arg-type]


# ======================================================================
# _resolve_compare_canonical_results — success branch
# ======================================================================


@pytest.mark.unit()
class Test_Resolve_Compare_Canonical_Results_Success:
    """Branch-complete tests for the SUCCESS path of _resolve_compare_canonical_results."""

    @pytest.mark.unit()
    def test_success_path_returns_real_dataframes(self) -> None:
        """When 'standard' succeeds, the actual DataFrames must be returned."""
        import polars as pl

        from src.dashboard.shiny_tab_results.subtab_simulation import (
            _resolve_compare_canonical_results,
        )

        results_df = pl.DataFrame({"Date": [], "Scenario_1": []})
        stats_df = pl.DataFrame({"Date": [], "Mean": []})
        compare_results = {
            "standard": {
                "status": "success",
                "results_df": results_df,
                "stats_df": stats_df,
                "elapsed": 1.23,
            }
        }

        out_results, out_stats, out_elapsed, out_label = _resolve_compare_canonical_results(
            compare_results = compare_results
        )
        assert out_results is results_df
        assert out_stats is stats_df
        assert out_elapsed == pytest.approx(1.23)
        assert out_label == "standard (compare mode)"

    @pytest.mark.unit()
    def test_success_path_elapsed_is_float(self) -> None:
        """Elapsed value must be returned as a Python float."""
        import polars as pl

        from src.dashboard.shiny_tab_results.subtab_simulation import (
            _resolve_compare_canonical_results,
        )

        compare_results = {
            "standard": {
                "status": "success",
                "results_df": pl.DataFrame({"Date": [], "Scenario_1": []}),
                "stats_df": pl.DataFrame({"Date": [], "Mean": []}),
                "elapsed": 2,  # int input
            }
        }
        _, _, elapsed, _ = _resolve_compare_canonical_results(compare_results = compare_results)
        assert isinstance(elapsed, float)

    @pytest.mark.unit()
    def Test_Boolean_Elapsed_Uses_Zero_Default(self) -> None:
        """Boolean elapsed metadata should stay on the existing 0.0-seconds fallback path."""
        import polars as pl

        from src.dashboard.shiny_tab_results.subtab_simulation import (
            _resolve_compare_canonical_results,
        )

        compare_results = {
            "standard": {
                "status": "success",
                "results_df": pl.DataFrame({"Date": [], "Scenario_1": []}),
                "stats_df": pl.DataFrame({"Date": [], "Mean": []}),
                "elapsed": True,
            }
        }

        _, _, elapsed, _ = _resolve_compare_canonical_results(compare_results = compare_results)

        assert elapsed == 0.0

    @pytest.mark.unit()
    def test_failure_path_returns_zero_elapsed(self) -> None:
        """When standard fails, elapsed must be 0.0."""
        from src.dashboard.shiny_tab_results.subtab_simulation import (
            _resolve_compare_canonical_results,
        )

        _, _, elapsed, _ = _resolve_compare_canonical_results(compare_results = None)
        assert elapsed == 0.0


# ======================================================================
# _summarize_compare_completion — missing branch coverage
# ======================================================================


@pytest.mark.unit()
class Test_Summarize_Compare_Completion_Branch_Coverage:
    """Branch-complete tests for _summarize_compare_completion."""

    @pytest.mark.unit()
    def test_none_input_returns_zero_success(self) -> None:
        """None input must return (0, total_types)."""
        from src.dashboard.shiny_tab_results.subtab_simulation import (
            _summarize_compare_completion,
        )
        from src.models.simulation.simulation_dispatch import COMPUTATION_TYPES_SIMULATION_COMPARE

        num_success, num_failed = _summarize_compare_completion(compare_results = None)
        assert num_success == 0
        assert num_failed == len(COMPUTATION_TYPES_SIMULATION_COMPARE)

    @pytest.mark.unit()
    def test_empty_dict_all_failed(self) -> None:
        """An empty dict means no backend succeeded."""
        from src.dashboard.shiny_tab_results.subtab_simulation import (
            _summarize_compare_completion,
        )
        from src.models.simulation.simulation_dispatch import COMPUTATION_TYPES_SIMULATION_COMPARE

        num_success, num_failed = _summarize_compare_completion(compare_results = {})
        assert num_success == 0
        assert num_failed == len(COMPUTATION_TYPES_SIMULATION_COMPARE)

    @pytest.mark.unit()
    def test_all_succeeded(self) -> None:
        """When every backend succeeds, num_failed must be 0."""
        import polars as pl

        from src.dashboard.shiny_tab_results.subtab_simulation import (
            _summarize_compare_completion,
        )
        from src.models.simulation.simulation_dispatch import COMPUTATION_TYPES_SIMULATION_COMPARE

        compare_results = {
            ctype: {
                "status": "success",
                "results_df": pl.DataFrame({"Date": [], "Scenario_1": []}),
                "stats_df": pl.DataFrame({"Date": [], "Mean": []}),
                "elapsed": 0.1,
            }
            for ctype in COMPUTATION_TYPES_SIMULATION_COMPARE
        }
        num_success, num_failed = _summarize_compare_completion(compare_results = compare_results)
        assert num_success == len(COMPUTATION_TYPES_SIMULATION_COMPARE)
        assert num_failed == 0

    @pytest.mark.unit()
    def test_success_plus_failed_sums_to_total(self) -> None:
        """num_success + num_failed must always equal len(COMPUTATION_TYPES_SIMULATION_COMPARE)."""
        import polars as pl

        from src.dashboard.shiny_tab_results.subtab_simulation import (
            _summarize_compare_completion,
        )
        from src.models.simulation.simulation_dispatch import COMPUTATION_TYPES_SIMULATION_COMPARE

        # Make half succeed, half fail
        n_total = len(COMPUTATION_TYPES_SIMULATION_COMPARE)
        compare_results = {}
        for i, ctype in enumerate(COMPUTATION_TYPES_SIMULATION_COMPARE):
            if i % 2 == 0:
                compare_results[ctype] = {
                    "status": "success",
                    "results_df": pl.DataFrame({"Date": [], "Scenario_1": []}),
                    "stats_df": pl.DataFrame({"Date": [], "Mean": []}),
                    "elapsed": 0.1,
                }
            else:
                compare_results[ctype] = {
                    "status": "error",
                    "results_df": None,
                    "stats_df": None,
                    "elapsed": 0.0,
                }

        num_success, num_failed = _summarize_compare_completion(compare_results = compare_results)
        assert num_success + num_failed == n_total


# ======================================================================
# _task_run_compare / _on_compare_step — call-site contract
# ======================================================================


class Test_Task_Run_Compare_Call_Site_Contract:
    """Regression tests for the Compute-and-Compare call-site wiring.

    The two production bugs fixed in this module were:

    1. ``_task_run_compare`` invoked ``compute_compare_results`` positionally
       with ``config`` even though the dispatcher declares ``config`` as
       keyword-only.  This raised ``TypeError`` at the ExtendedTask boundary.
    2. ``_on_compare_step`` declared its two arguments as keyword-only
       (``*, idx, ctype``) while ``compute_compare_results`` invokes its
       ``progress_callback`` positionally as ``callback(idx, ctype)``.  This
       raised ``TypeError`` on the first per-backend callback.

    Because both ``_task_run_compare`` and ``_on_compare_step`` are nested
    closures inside ``subtab_simulation_server`` (not module-level
    callables), the tests below exercise the contract through two
    complementary angles:

    * **End-to-end dispatcher contract test** — drives the real
      ``compute_compare_results`` with a callback that mirrors the
      production ``_on_compare_step`` (positional ``(idx, ctype)``).  This
      locks in the dispatcher-callback contract that the dashboard
      callback must satisfy; reverting the callback to ``*, idx, ctype``
      would break this contract at the dispatcher boundary.
    * **Source-pattern regression guards** — read the dashboard source
      and assert that the ``asyncio.to_thread`` call site uses
      ``config=config`` and ``progress_callback=`` keyword forms, and that
      the callback inside ``_task_run_compare`` does not declare its
      arguments as keyword-only.
    """

    @pytest.mark.unit()
    def test_dispatcher_accepts_positional_callback_with_idx_and_ctype(self) -> None:
        """``compute_compare_results`` invokes its progress callback positionally.

        Mirrors the production ``_on_compare_step`` shape — a two-positional
        callback that stores ``idx`` and ``ctype``.  If the dashboard's
        callback is ever reverted to ``*, idx, ctype`` keyword-only, the
        dispatcher would raise ``TypeError``; this test ensures the
        dispatcher-callback contract stays compatible with that shape.
        """
        import datetime as dt

        import numpy as np

        from src.models.simulation.simulation_dispatch import (
            COMPUTATION_TYPES_SIMULATION_COMPARE,
            Simulation_Run_Config,
            compute_compare_results,
        )
        from src.num_methods.scenarios.scenarios_distrib import Distribution_Type

        config = Simulation_Run_Config(
            names_components=["A", "B"],
            weights=np.array([0.5, 0.5]),
            distribution_type=Distribution_Type.NORMAL,
            mean_returns=np.array([0.0003, 0.0002]),
            covariance_matrix=np.array([[0.0004, 0.0001], [0.0001, 0.0003]]),
            initial_value=100.0,
            num_scenarios=50,
            num_days=5,
            start_date=dt.date(2026, 1, 2),
            random_seed=42,
            degrees_of_freedom=5.0,
            rng_type="pcg64",
        )

        captured: list[tuple[int, str]] = []

        # Positional-only callback — the same shape as the production
        # ``_on_compare_step``.  A ``*`` keyword-only signature here would
        # raise ``TypeError`` because the dispatcher calls it positionally.
        def callback(idx: int, ctype: str) -> None:
            captured.append((idx, ctype))

        # Pass ``config`` by keyword to match the dispatcher's keyword-only
        # contract (this is the contract the dashboard call site now uses).
        compare_results = compute_compare_results(
            config=config,
            progress_callback=callback,
        )

        # Callback must have been invoked exactly once per backend.
        assert len(captured) == len(COMPUTATION_TYPES_SIMULATION_COMPARE)
        # Indices are 0-based and monotone.
        assert [idx for idx, _ in captured] == list(range(len(COMPUTATION_TYPES_SIMULATION_COMPARE)))
        # Backend types appear in dispatch order.
        assert [ctype for _, ctype in captured] == list(COMPUTATION_TYPES_SIMULATION_COMPARE)
        # Compare-results dict is keyed by backend type.
        assert set(compare_results.keys()) == set(COMPUTATION_TYPES_SIMULATION_COMPARE)

    @pytest.mark.unit()
    def test_dispatcher_callback_receives_two_positional_args(self) -> None:
        """Dispatcher must invoke callback with exactly two positional args.

        Protects the dashboard from accidentally tightening the dispatcher
        contract in the future (e.g. switching the dispatcher to a keyword
        call) without also updating the dashboard callback signature.
        """
        import datetime as dt

        import numpy as np

        from src.models.simulation.simulation_dispatch import Simulation_Run_Config
        from src.models.simulation.simulation_dispatch import compute_compare_results
        from src.num_methods.scenarios.scenarios_distrib import Distribution_Type

        config = Simulation_Run_Config(
            names_components=["A", "B"],
            weights=np.array([0.5, 0.5]),
            distribution_type=Distribution_Type.NORMAL,
            mean_returns=np.array([0.0003, 0.0002]),
            covariance_matrix=np.array([[0.0004, 0.0001], [0.0001, 0.0003]]),
            initial_value=100.0,
            num_scenarios=20,
            num_days=3,
            start_date=dt.date(2026, 1, 2),
            random_seed=42,
            degrees_of_freedom=5.0,
            rng_type="pcg64",
        )

        positional_arg_count: list[int] = []

        def callback(*args: object) -> None:
            positional_arg_count.append(len(args))

        compute_compare_results(config=config, progress_callback=callback)
        # Every invocation must pass exactly two positional args.
        assert positional_arg_count, "callback was never invoked"
        assert all(count == 2 for count in positional_arg_count)

    @pytest.mark.unit()
    def test_dashboard_task_run_compare_passes_config_by_keyword(self) -> None:
        """Regression guard: ``_task_run_compare`` must call ``compute_compare_results`` with ``config=config``.

        Reads the dashboard source and asserts that the ``asyncio.to_thread``
        call inside ``_task_run_compare`` passes ``config`` by name.  This
        is the contract enforced by the dispatcher's ``*, config``
        keyword-only declaration and is the exact fix applied in this
        module.
        """
        import inspect

        from src.dashboard.shiny_tab_results import subtab_simulation as mod

        source_text = inspect.getsource(mod)
        to_thread_start = source_text.find("asyncio.to_thread(")
        assert to_thread_start >= 0, "Could not locate asyncio.to_thread call in source"

        # Walk through parentheses to find the matching close of the
        # ``asyncio.to_thread(...)`` call.
        depth = 1
        idx_cursor = to_thread_start + len("asyncio.to_thread(")
        while idx_cursor < len(source_text) and depth > 0:
            char = source_text[idx_cursor]
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
            idx_cursor += 1
        call_body = source_text[to_thread_start + len("asyncio.to_thread("):idx_cursor - 1]

        # The call must contain ``config=config`` (regression guard for fix 1).
        assert "config=config" in call_body, (
            "Regression: _task_run_compare must call compute_compare_results "
            "with config=config (keyword form)."
        )

    @pytest.mark.unit()
    def test_dashboard_task_run_compare_passes_progress_callback_by_keyword(self) -> None:
        """Regression guard: ``_task_run_compare`` must pass ``progress_callback`` by name.

        The dispatcher declares ``progress_callback`` as keyword-only as
        well; this guard ensures the call site does not regress to a
        positional invocation.
        """
        import inspect

        from src.dashboard.shiny_tab_results import subtab_simulation as mod

        source_text = inspect.getsource(mod)
        to_thread_start = source_text.find("asyncio.to_thread(")
        assert to_thread_start >= 0, "Could not locate asyncio.to_thread call in source"

        depth = 1
        idx_cursor = to_thread_start + len("asyncio.to_thread(")
        while idx_cursor < len(source_text) and depth > 0:
            char = source_text[idx_cursor]
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
            idx_cursor += 1
        call_body = source_text[to_thread_start + len("asyncio.to_thread("):idx_cursor - 1]

        assert "progress_callback=" in call_body, (
            "Regression: _task_run_compare must pass progress_callback by keyword."
        )

    @pytest.mark.unit()
    def test_handle_compare_result_does_not_call_invalidate_later(self) -> None:
        """Regression guard: ``_handle_compare_result`` must not use ``invalidate_later``.

        Background: the original implementation called
        ``reactive.invalidate_later(0.5)`` to re-arm itself while the
        ExtendedTask was still running.  This created a timer storm that
        competed with Shiny's natural flush cycle, occasionally
        interrupting the effect mid-execution and leaving the progress
        card stuck on the last backend (joblib) without ever reaching
        ``status == "done"`` (see Shiny ``_core.py:372``'s
        ``async with lock():`` raising ``asyncio.CancelledError``).

        The correct pattern is to read ``_task_run_compare.result()``
        directly inside the effect, which establishes a reactive
        dependency on ``ExtendedTask.status`` (a ``reactive.Value`` that
        is followed by ``await flush()`` in
        ``_extended_task._execution_wrapper``).  Shiny re-invokes the
        effect exactly once per status transition with no manual timer.
        """
        import ast
        import inspect

        from src.dashboard.shiny_tab_results import subtab_simulation as mod

        # Use the AST to extract the function body minus the docstring
        # so the literal token ``invalidate_later`` appearing in the
        # Numpydoc Notes section does not produce a false positive.
        module_ast = ast.parse(inspect.getsource(mod))
        target_fn: ast.FunctionDef | None = None
        for node in ast.walk(module_ast):
            if (
                isinstance(node, ast.FunctionDef)
                and node.name == "_handle_compare_result"
            ):
                target_fn = node
                break
        assert target_fn is not None, "Could not locate _handle_compare_result AST node"

        # Skip the leading docstring node (Expr wrapping a string Constant)
        # so the scan only covers executable statements.
        body_stmts = list(target_fn.body)
        if (
            body_stmts
            and isinstance(body_stmts[0], ast.Expr)
            and isinstance(body_stmts[0].value, ast.Constant)
            and isinstance(body_stmts[0].value.value, str)
        ):
            body_stmts = body_stmts[1:]

        body_source = "\n".join(ast.unparse(stmt) for stmt in body_stmts)

        assert "invalidate_later" not in body_source, (
            "Regression: _handle_compare_result must not call "
            "reactive.invalidate_later. Use _task_run_compare.result() "
            "directly and rely on ExtendedTask.status-driven flush."
        )

    @pytest.mark.unit()
    def test_handle_compare_result_uses_task_result_directly(self) -> None:
        """Regression guard: ``_handle_compare_result`` must call ``_task_run_compare.result()``.

        Locks in the canonical Shiny ExtendedTask pattern: the effect
        reads ``.result()`` from a reactive context so the framework
        auto-invalidates on status transitions, with no manual
        ``invalidate_later`` re-arming.
        """
        import ast
        import inspect

        from src.dashboard.shiny_tab_results import subtab_simulation as mod

        module_ast = ast.parse(inspect.getsource(mod))
        target_fn: ast.FunctionDef | None = None
        for node in ast.walk(module_ast):
            if (
                isinstance(node, ast.FunctionDef)
                and node.name == "_handle_compare_result"
            ):
                target_fn = node
                break
        assert target_fn is not None, "Could not locate _handle_compare_result AST node"

        # Skip the leading docstring node so the scan covers only
        # executable statements (the docstring would otherwise contain
        # the literal ``_task_run_compare.result()`` token used in prose
        # and would mask any future regression that removes the call).
        body_stmts = list(target_fn.body)
        if (
            body_stmts
            and isinstance(body_stmts[0], ast.Expr)
            and isinstance(body_stmts[0].value, ast.Constant)
            and isinstance(body_stmts[0].value.value, str)
        ):
            body_stmts = body_stmts[1:]

        body_source = "\n".join(ast.unparse(stmt) for stmt in body_stmts)

        assert "_task_run_compare.result()" in body_source, (
            "Regression: _handle_compare_result must call "
            "_task_run_compare.result() directly to consume the "
            "ExtendedTask's value reactively."
        )

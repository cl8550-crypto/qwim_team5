"""Unit tests for private Simulation subtab rendering helpers.

These tests cover the extracted helper module used by the public
Simulation subtab facade.
"""

from __future__ import annotations

import datetime as dt

from pathlib import Path
from unittest.mock import patch

import numpy as np
import polars as pl
import pytest

from shiny import ui

from src.dashboard.shiny_tab_results import _subtab_simulation_rendering as sim_render
from src.num_methods.scenarios.scenarios_distrib import Distribution_Type


@pytest.fixture()
def fixture_etf_prices_dataframe() -> pl.DataFrame:
    """Return a small ETF price frame for Simulation helper tests."""
    return pl.DataFrame(
        {
            "Date": [
                dt.date(2026, 1, 1),
                dt.date(2026, 1, 2),
                dt.date(2026, 1, 3),
            ],
            "IVV": [100.0, 101.0, 103.0],
            "AGG": [50.0, 50.5, 50.25],
        },
    )


@pytest.fixture()
def fixture_stats_dataframe() -> pl.DataFrame:
    """Return a small stats frame for Simulation chart tests."""
    return pl.DataFrame(
        {
            "Date": [
                dt.date(2026, 1, 1),
                dt.date(2026, 1, 2),
                dt.date(2026, 1, 3),
            ],
            "P5": [90.0, 92.0, 94.0],
            "P25": [95.0, 97.0, 99.0],
            "Median": [100.0, 102.0, 104.0],
            "Mean": [100.0, 102.5, 104.5],
            "P75": [105.0, 107.0, 109.0],
            "P95": [110.0, 112.0, 114.0],
        },
    )


@pytest.fixture()
def fixture_results_dataframe() -> pl.DataFrame:
    """Return a small Simulation results frame for rendering tests."""
    return pl.DataFrame(
        {
            "Date": [
                dt.date(2026, 1, 1),
                dt.date(2026, 1, 2),
                dt.date(2026, 1, 3),
            ],
            "Scenario_1": [100.0, 102.0, 104.0],
            "Scenario_2": [100.0, 101.0, 103.0],
        },
    )


class _Input_Select_All_Enabled:
    def input_ID_tab_results_subtab_simulation_select_all_components(self) -> bool:
        return True


class _Input_Select_All_Missing:
    pass


class _Input_Component_Selection:
    def __init__(self, selected_components: set[str], *, raise_for: set[str] | None = None) -> None:
        self._selected_components = selected_components
        self._raise_for = raise_for or set()

    def input_ID_tab_results_subtab_simulation_select_all_components(self) -> bool:
        return False

    def __getitem__(self, item_key: str):
        component_name = item_key.rsplit("_", 1)[-1]
        if component_name in self._raise_for:
            raise RuntimeError("component read failed")

        return lambda: component_name in self._selected_components


class Class_Test_Subtab_Simulation_Rendering_Loaders:
    """Tests for ETF data loading and component resolution helpers."""

    @pytest.mark.unit()
    def Test_Load_Returns_Data_Inputs_Frame(
        self,
        fixture_etf_prices_dataframe: pl.DataFrame,
    ) -> None:
        """Dashboard ETF inputs should be returned directly when present."""
        result_data_frame = sim_render.load_etf_price_data_for_simulation(
            data_inputs = {"ETF_Prices": fixture_etf_prices_dataframe},
            module_file_path=__file__,
        )

        assert result_data_frame is fixture_etf_prices_dataframe

    @pytest.mark.unit()
    def Test_Load_Ignores_Empty_Frame_Without_CSV(self) -> None:
        """Empty ETF input frames should fall through to the fallback path."""
        result_data_frame = sim_render.load_etf_price_data_for_simulation(
            data_inputs = {"ETF_Prices": pl.DataFrame()},
            module_file_path=str(Path(__file__).resolve()),
        )

        assert result_data_frame is None

    @pytest.mark.unit()
    def Test_Load_Falls_Back_To_CSV_And_Renames_Date(self, tmp_path: Path) -> None:
        """The CSV fallback should be loaded and normalised to ``Date``."""
        inputs_path = tmp_path / "inputs" / "raw"
        inputs_path.mkdir(parents=True)
        csv_path = inputs_path / "data_ETFs.csv"
        csv_path.write_text(
            "date,IVV,AGG\n2026-01-01,100.0,50.0\n2026-01-02,101.0,50.5\n",
            encoding="utf-8",
        )
        module_file_path = tmp_path / "pkg1" / "pkg2" / "pkg3" / "dummy_module.py"
        module_file_path.parent.mkdir(parents=True)

        result_data_frame = sim_render.load_etf_price_data_for_simulation(
            data_inputs = {},
            module_file_path=str(module_file_path),
        )

        assert result_data_frame is not None
        assert result_data_frame.columns[0] == "Date"

    @pytest.mark.unit()
    def Test_Load_Falls_Back_To_CSV_Without_Rename_When_Date_Already_Present(
        self,
        tmp_path: Path,
    ) -> None:
        """A CSV that already uses ``Date`` should bypass the rename branch."""
        inputs_path = tmp_path / "inputs" / "raw"
        inputs_path.mkdir(parents=True)
        csv_path = inputs_path / "data_ETFs.csv"
        csv_path.write_text(
            "Date,IVV,AGG\n2026-01-01,100.0,50.0\n2026-01-02,101.0,50.5\n",
            encoding="utf-8",
        )
        module_file_path = tmp_path / "pkg1" / "pkg2" / "pkg3" / "dummy_module.py"
        module_file_path.parent.mkdir(parents=True)

        result_data_frame = sim_render.load_etf_price_data_for_simulation(
            data_inputs = {},
            module_file_path=str(module_file_path),
        )

        assert result_data_frame is not None
        assert result_data_frame.columns == ["Date", "IVV", "AGG"]

    @pytest.mark.unit()
    def Test_Load_Returns_None_When_CSV_Read_Fails(self, tmp_path: Path) -> None:
        """A CSV read failure should be handled and return ``None``."""
        inputs_path = tmp_path / "inputs" / "raw"
        inputs_path.mkdir(parents=True)
        (inputs_path / "data_ETFs.csv").write_text("bad", encoding="utf-8")
        module_file_path = tmp_path / "pkg1" / "pkg2" / "pkg3" / "dummy_module.py"
        module_file_path.parent.mkdir(parents=True)

        with patch(
            "src.dashboard.shiny_tab_results._subtab_simulation_rendering.pl.read_csv",
            side_effect=RuntimeError("csv failure"),
        ):
            result_data_frame = sim_render.load_etf_price_data_for_simulation(
                data_inputs = {},
                module_file_path=str(module_file_path),
            )

        assert result_data_frame is None

    @pytest.mark.unit()
    def Test_Resolve_Available_Returns_Defaults_When_No_Data(self) -> None:
        """No ETF data should fall back to the documented ETF symbol list."""
        result_components = sim_render.resolve_available_etf_components_for_simulation(
            data_inputs = {},
            module_file_path=__file__,
        )

        assert result_components == sim_render.ALL_ETF_SYMBOLS

    @pytest.mark.unit()
    def Test_Resolve_Available_Excludes_Date_Columns(
        self,
        fixture_etf_prices_dataframe: pl.DataFrame,
    ) -> None:
        """Available ETF components should exclude ``Date`` columns."""
        result_components = sim_render.resolve_available_etf_components_for_simulation(
            data_inputs = {"ETF_Prices": fixture_etf_prices_dataframe},
            module_file_path=__file__,
        )

        assert result_components == ["IVV", "AGG"]

    @pytest.mark.unit()
    def Test_Resolve_Selected_Returns_Empty_When_No_Available(self) -> None:
        """No available components should produce an empty selection."""
        result_components = sim_render.resolve_selected_etf_components_for_simulation(
            input_obj = _Input_Select_All_Enabled(),
            available_components = [],
            num_default_selected = 3,
        )

        assert result_components == []

    @pytest.mark.unit()
    def Test_Resolve_Selected_Defaults_When_Toggle_Missing(self) -> None:
        """Missing toggle inputs should fall back to the default selection count."""
        available_components = ["IVV", "AGG", "GLD", "DBC"]
        result_components = sim_render.resolve_selected_etf_components_for_simulation(
            input_obj = _Input_Select_All_Missing(),
            available_components = available_components,
            num_default_selected = 2,
        )

        assert result_components == ["IVV", "AGG"]

    @pytest.mark.unit()
    def Test_Resolve_Selected_Returns_All_When_Select_All_Enabled(self) -> None:
        """Enabled select-all input should return every available component."""
        available_components = ["IVV", "AGG", "GLD"]
        result_components = sim_render.resolve_selected_etf_components_for_simulation(
            input_obj = _Input_Select_All_Enabled(),
            available_components = available_components,
            num_default_selected = 2,
        )

        assert result_components == available_components

    @pytest.mark.unit()
    def Test_Resolve_Selected_Uses_Checked_Component_Inputs(self) -> None:
        """Checked per-component inputs should define the selection list."""
        available_components = ["IVV", "AGG", "GLD"]
        result_components = sim_render.resolve_selected_etf_components_for_simulation(
            input_obj = _Input_Component_Selection({"IVV", "GLD"}),
            available_components = available_components,
            num_default_selected = 2,
        )

        assert result_components == ["IVV", "GLD"]

    @pytest.mark.unit()
    def Test_Resolve_Selected_Skips_Component_Read_Errors(self) -> None:
        """Per-component input errors should be skipped instead of failing selection."""
        available_components = ["IVV", "AGG", "GLD"]
        result_components = sim_render.resolve_selected_etf_components_for_simulation(
            input_obj = _Input_Component_Selection({"GLD"}, raise_for={"AGG"}),
            available_components = available_components,
            num_default_selected = 2,
        )

        assert result_components == ["GLD"]

    @pytest.mark.unit()
    def Test_Resolve_Selected_Defaults_When_None_Checked(self) -> None:
        """No checked component inputs should fall back to defaults."""
        available_components = ["IVV", "AGG", "GLD"]
        result_components = sim_render.resolve_selected_etf_components_for_simulation(
            input_obj = _Input_Component_Selection(set()),
            available_components = available_components,
            num_default_selected = 2,
        )

        assert result_components == ["IVV", "AGG"]


class Class_Test_Subtab_Simulation_Rendering_Config:
    """Tests for Simulation run-config construction."""

    @pytest.mark.unit()
    def Test_Config_Uses_Fallback_Statistics_When_No_Data(self) -> None:
        """Missing ETF data should produce zero means and diagonal covariance."""
        config_simulation = sim_render.build_simulation_run_config_for_subtab(
            data_inputs={},
            degrees_of_freedom=5.0,
            distribution_type=Distribution_Type.NORMAL,
            initial_value=100.0,
            module_file_path=__file__,
            num_days=5,
            num_scenarios=10,
            rng_type="pcg64",
            seed=42,
            selected_components=["IVV", "AGG"],
            start_date=dt.date(2026, 1, 1),
        )

        assert config_simulation.names_components == ["IVV", "AGG"]
        assert np.allclose(config_simulation.mean_returns, np.array([0.0, 0.0]))
        assert np.allclose(config_simulation.covariance_matrix, np.eye(2) * 0.0004)
        assert np.allclose(config_simulation.weights, np.array([0.5, 0.5]))

    @pytest.mark.unit()
    def Test_Config_Filters_Missing_Selected_Columns(
        self,
        fixture_etf_prices_dataframe: pl.DataFrame,
    ) -> None:
        """Missing selected ETF columns should be filtered from the config."""
        config_simulation = sim_render.build_simulation_run_config_for_subtab(
            data_inputs={"ETF_Prices": fixture_etf_prices_dataframe},
            degrees_of_freedom=5.0,
            distribution_type=Distribution_Type.NORMAL,
            initial_value=100.0,
            module_file_path=__file__,
            num_days=5,
            num_scenarios=10,
            rng_type="pcg64",
            seed=42,
            selected_components=["IVV", "GLD"],
            start_date=dt.date(2026, 1, 1),
        )

        assert config_simulation.names_components == ["IVV"]
        assert np.allclose(config_simulation.weights, np.array([1.0]))

    @pytest.mark.unit()
    def Test_Config_Uses_Lognormal_Mean_Shift(
        self,
        fixture_etf_prices_dataframe: pl.DataFrame,
    ) -> None:
        """Lognormal configs should shift estimated means by ``1.0``."""
        config_simulation = sim_render.build_simulation_run_config_for_subtab(
            data_inputs={"ETF_Prices": fixture_etf_prices_dataframe},
            degrees_of_freedom=5.0,
            distribution_type=Distribution_Type.LOGNORMAL,
            initial_value=100.0,
            module_file_path=__file__,
            num_days=5,
            num_scenarios=10,
            rng_type="pcg64",
            seed=42,
            selected_components=["IVV", "AGG"],
            start_date=dt.date(2026, 1, 1),
        )

        assert np.all(config_simulation.mean_returns > 0.99)

    @pytest.mark.unit()
    def Test_Config_Uses_Fallback_When_No_Selected_Columns_Present(
        self,
        fixture_etf_prices_dataframe: pl.DataFrame,
    ) -> None:
        """No matching ETF columns should fall back to zero means and identity covariance."""
        config_simulation = sim_render.build_simulation_run_config_for_subtab(
            data_inputs={"ETF_Prices": fixture_etf_prices_dataframe},
            degrees_of_freedom=5.0,
            distribution_type=Distribution_Type.NORMAL,
            initial_value=100.0,
            module_file_path=__file__,
            num_days=5,
            num_scenarios=10,
            rng_type="pcg64",
            seed=42,
            selected_components=["GLD", "DBC"],
            start_date=dt.date(2026, 1, 1),
        )

        assert config_simulation.names_components == ["GLD", "DBC"]
        assert np.allclose(config_simulation.mean_returns, np.array([0.0, 0.0]))
        assert np.allclose(config_simulation.covariance_matrix, np.eye(2) * 0.0004)

    @pytest.mark.unit()
    def Test_Config_Boolean_ETF_Price_Columns_Use_Fallback_Statistics(self) -> None:
        """Boolean ETF price columns should not be treated as numeric return inputs."""
        bool_price_frame = pl.DataFrame(
            {
                "Date": [dt.date(2026, 1, 1), dt.date(2026, 1, 2), dt.date(2026, 1, 3)],
                "IVV": [True, False, True],
                "AGG": [False, True, False],
            },
        )

        config_simulation = sim_render.build_simulation_run_config_for_subtab(
            data_inputs={"ETF_Prices": bool_price_frame},
            degrees_of_freedom=5.0,
            distribution_type=Distribution_Type.NORMAL,
            initial_value=100.0,
            module_file_path=__file__,
            num_days=5,
            num_scenarios=10,
            rng_type="pcg64",
            seed=42,
            selected_components=["IVV", "AGG"],
            start_date=dt.date(2026, 1, 1),
        )

        assert config_simulation.names_components == ["IVV", "AGG"]
        assert np.allclose(config_simulation.mean_returns, np.array([0.0, 0.0]))
        assert np.allclose(config_simulation.covariance_matrix, np.eye(2) * 0.0004)


class Class_Test_Subtab_Simulation_Rendering_Figures:
    """Tests for the extracted chart rendering helpers."""

    @pytest.mark.unit()
    def Test_Fan_Chart_Uses_Empty_Figure_Callback_When_Data_Missing(self) -> None:
        """Missing stats or results should use the provided empty-figure callback."""
        sentinel_figure = object()

        result_figure = sim_render.build_fan_chart_figure_for_simulation(
            create_empty_figure=lambda *, title, message, **___: sentinel_figure,
            reactives_shiny={},
            results_df=None,
            stats_df=None,
        )

        assert result_figure is sentinel_figure

    @pytest.mark.unit()
    def Test_Fan_Chart_Builds_Traces_And_Updates_Reactives(
        self,
        fixture_results_dataframe: pl.DataFrame,
        fixture_stats_dataframe: pl.DataFrame,
    ) -> None:
        """Valid stats and results should build the fan chart and update reactives."""
        with patch(
            "src.dashboard.shiny_tab_results._subtab_simulation_rendering.build_plotnine_simulation_fan_chart",
            return_value="plotnine_fan",
        ) as mock_plotnine, patch(
            "src.dashboard.shiny_tab_results._subtab_simulation_rendering.update_visual_object_in_reactives",
        ) as mock_update:
            result_figure = sim_render.build_fan_chart_figure_for_simulation(
                create_empty_figure=lambda *, title, message, **___: go.Figure(),
                reactives_shiny={},
                results_df=fixture_results_dataframe,
                stats_df=fixture_stats_dataframe,
            )

        assert isinstance(result_figure, sim_render.go.Figure)
        assert len(result_figure.data) == 6
        assert result_figure.layout.height == 600
        mock_plotnine.assert_called_once_with(results_df=fixture_results_dataframe)
        mock_update.assert_called_once()

    @pytest.mark.unit()
    def Test_Fan_Chart_Boolean_Scenario_Columns_Use_Empty_Figure_Callback(self) -> None:
        """Boolean scenario columns should not be rendered as numeric fan-chart paths."""
        sentinel_figure = object()
        results_df = pl.DataFrame(
            {
                "Date": [1, 2],
                "Scenario_1": [True, False],
                "Scenario_2": [False, True],
            },
        )
        stats_df = pl.DataFrame(
            {
                "Date": [1, 2],
                "P95": [101.0, 102.0],
                "P5": [99.0, 98.0],
                "P75": [100.5, 101.5],
                "P25": [99.5, 98.5],
                "Median": [100.0, 100.0],
                "Mean": [100.0, 100.0],
            },
        )

        result_figure = sim_render.build_fan_chart_figure_for_simulation(
            create_empty_figure=lambda *, title, message, **___: sentinel_figure,
            reactives_shiny={},
            results_df=results_df,
            stats_df=stats_df,
        )

        assert result_figure is sentinel_figure

    @pytest.mark.unit()
    def Test_Histogram_Uses_Empty_Figure_Callback_When_Data_Missing(self) -> None:
        """Missing results should use the provided empty-figure callback."""
        sentinel_figure = object()

        result_figure = sim_render.build_histogram_figure_for_simulation(
            create_empty_figure=lambda *, title, message, **___: sentinel_figure,
            reactives_shiny={},
            results_df=None,
        )

        assert result_figure is sentinel_figure

    @pytest.mark.unit()
    def Test_Histogram_Builds_Figure_And_Updates_Reactives(
        self,
        fixture_results_dataframe: pl.DataFrame,
    ) -> None:
        """Valid results should build the histogram figure and update reactives."""
        with patch(
            "src.dashboard.shiny_tab_results._subtab_simulation_rendering.build_plotnine_simulation_terminal_value_distribution",
            return_value="plotnine_hist",
        ) as mock_plotnine, patch(
            "src.dashboard.shiny_tab_results._subtab_simulation_rendering.update_visual_object_in_reactives",
        ) as mock_update:
            result_figure = sim_render.build_histogram_figure_for_simulation(
                create_empty_figure=lambda *, title, message, **___: go.Figure(),
                reactives_shiny={},
                results_df=fixture_results_dataframe,
            )

        assert isinstance(result_figure, sim_render.go.Figure)
        assert len(result_figure.data) == 1
        assert len(result_figure.layout.shapes) == 2
        mock_plotnine.assert_called_once()
        mock_update.assert_called_once()

    @pytest.mark.unit()
    def Test_Histogram_Boolean_Scenario_Columns_Use_Empty_Figure_Callback(self) -> None:
        """Boolean scenario columns should not be rendered as numeric histogram inputs."""
        sentinel_figure = object()
        results_df = pl.DataFrame(
            {
                "Date": [1, 2],
                "Scenario_1": [True, False],
                "Scenario_2": [False, True],
            },
        )

        result_figure = sim_render.build_histogram_figure_for_simulation(
            create_empty_figure=lambda *, title, message, **___: sentinel_figure,
            reactives_shiny={},
            results_df=results_df,
        )

        assert result_figure is sentinel_figure


class Class_Test_Subtab_Simulation_Rendering_UI:
    """Tests for the extracted compare and stats UI helpers."""

    @pytest.mark.unit()
    def Test_Compare_Progress_Returns_Empty_When_Disabled(self) -> None:
        """Disabled compare mode should render an empty container."""
        result_ui = sim_render.build_compare_progress_ui_for_simulation(
            do_compare_enabled=False,
            progress_state={},
        )

        assert str(result_ui) == str(ui.div())

    @pytest.mark.unit()
    def Test_Compare_Progress_Renders_Idle_Message(self) -> None:
        """Idle compare state should render the benchmark instruction text."""
        result_ui = sim_render.build_compare_progress_ui_for_simulation(
            do_compare_enabled=True,
            progress_state={"status": "idle"},
        )

        assert "benchmark all 5 backends" in str(result_ui)

    @pytest.mark.unit()
    def Test_Compare_Progress_Renders_Failed_Message(self) -> None:
        """Failed compare state should render the failure card."""
        result_ui = sim_render.build_compare_progress_ui_for_simulation(
            do_compare_enabled=True,
            progress_state={"status": "failed"},
        )

        assert "Failed" in str(result_ui)

    @pytest.mark.unit()
    def Test_Compare_Progress_Renders_Done_Success_State(self) -> None:
        """A successful done state should render a completed progress card."""
        result_ui = sim_render.build_compare_progress_ui_for_simulation(
            do_compare_enabled=True,
            progress_state={
                "status": "done",
                "total_types": 2,
                "completed": [
                    {"type": "standard", "ok": True, "elapsed": 0.1},
                    {"type": "asyncio", "ok": True, "elapsed": 0.2},
                ],
            },
        )

        result_html = str(result_ui)
        assert "completed successfully" in result_html
        assert "100%" in result_html

    @pytest.mark.unit()
    def Test_Compare_Progress_Renders_Done_With_Failures(self) -> None:
        """A partially failed done state should render the warning completion text."""
        result_ui = sim_render.build_compare_progress_ui_for_simulation(
            do_compare_enabled=True,
            progress_state={
                "status": "done",
                "total_types": 2,
                "completed": [
                    {"type": "standard", "ok": True, "elapsed": 0.1},
                    {"type": "asyncio", "ok": False, "elapsed": 0.0},
                ],
            },
        )

        assert "1/2 backends succeeded" in str(result_ui)

    @pytest.mark.unit()
    def Test_Compare_Progress_Done_Boolean_Elapsed_Uses_Default(self) -> None:
        """Boolean elapsed values should stay on the existing 0.0-second fallback path."""
        result_ui = sim_render.build_compare_progress_ui_for_simulation(
            do_compare_enabled=True,
            progress_state={
                "status": "done",
                "total_types": 1,
                "completed": [
                    {"type": "standard", "ok": True, "elapsed": True},
                ],
            },
        )

        result_html = str(result_ui)
        assert "0.000s" in result_html
        assert "1.000s" not in result_html

    @pytest.mark.unit()
    def Test_Compare_Progress_Done_Ignores_Non_Dict_Entries(self) -> None:
        """Non-dict completed entries should be ignored instead of breaking the card."""
        result_ui = sim_render.build_compare_progress_ui_for_simulation(
            do_compare_enabled=True,
            progress_state={
                "status": "done",
                "total_types": 2,
                "completed": [
                    "unexpected_entry",
                    {"type": "standard", "ok": True, "elapsed": 0.1},
                ],
            },
        )

        result_html = str(result_ui)
        assert "completed successfully" in result_html
        assert "unexpected_entry" not in result_html

    @pytest.mark.unit()
    def Test_Compare_Progress_Renders_Running_State(self) -> None:
        """A running compare state should render current backend progress."""
        result_ui = sim_render.build_compare_progress_ui_for_simulation(
            do_compare_enabled=True,
            progress_state={
                "status": "running",
                "current_index": 1,
                "current_type": "asyncio",
                "total_types": len(sim_render.COMPUTATION_TYPES_SIMULATION_COMPARE),
            },
        )

        result_html = str(result_ui)
        assert "Running backend 2/5: asyncio" in result_html
        assert "40%" in result_html

    @pytest.mark.unit()
    def Test_Compare_Progress_Running_Boolean_Numeric_State_Uses_Defaults(self) -> None:
        """Boolean running-state counters should fall back to the documented defaults."""
        result_ui = sim_render.build_compare_progress_ui_for_simulation(
            do_compare_enabled=True,
            progress_state={
                "status": "running",
                "current_index": True,
                "current_type": "asyncio",
                "total_types": True,
            },
        )

        result_html = str(result_ui)
        assert "Running backend 1/5: asyncio" in result_html
        assert "20%" in result_html

    @pytest.mark.unit()
    def Test_Compare_Table_Returns_Empty_When_Disabled(self) -> None:
        """Disabled compare mode should render an empty compare table container."""
        result_ui = sim_render.build_compare_table_ui_for_simulation(
            compare_results_payload=None,
            do_compare_enabled=False,
            progress_state={},
        )

        assert str(result_ui) == str(ui.div())

    @pytest.mark.unit()
    def Test_Compare_Table_Renders_Idle_Message_When_No_Results(self) -> None:
        """No compare results in idle state should render the idle helper text."""
        result_ui = sim_render.build_compare_table_ui_for_simulation(
            compare_results_payload=None,
            do_compare_enabled=True,
            progress_state={"status": "idle"},
        )

        assert "No comparison results yet" in str(result_ui)

    @pytest.mark.unit()
    def Test_Compare_Table_Renders_Running_Message_When_No_Results(self) -> None:
        """Running compare state without results should show current backend progress."""
        result_ui = sim_render.build_compare_table_ui_for_simulation(
            compare_results_payload=None,
            do_compare_enabled=True,
            progress_state={
                "status": "running",
                "current_index": 1,
                "current_type": "asyncio",
                "total_types": 5,
            },
        )

        assert "Running backend 2/5: asyncio" in str(result_ui)

    @pytest.mark.unit()
    def Test_Compare_Table_Running_Boolean_Numeric_State_Uses_Defaults(self) -> None:
        """Boolean running-state counters should use the existing compare-table defaults."""
        result_ui = sim_render.build_compare_table_ui_for_simulation(
            compare_results_payload=None,
            do_compare_enabled=True,
            progress_state={
                "status": "running",
                "current_index": True,
                "current_type": "asyncio",
                "total_types": True,
            },
        )

        assert "Running backend 1/5: asyncio" in str(result_ui)

    @pytest.mark.unit()
    def Test_Compare_Table_Renders_Table_When_Results_Available(self) -> None:
        """Available compare results should be converted into the styled HTML table."""
        compare_table_frame = pl.DataFrame(
            {
                "Metric": ["Status"],
                "standard": ["OK"],
            },
        )
        with patch(
            "src.dashboard.shiny_tab_results._subtab_simulation_rendering.build_compare_summary_table",
            return_value=compare_table_frame,
        ):
            result_ui = sim_render.build_compare_table_ui_for_simulation(
                compare_results_payload={"standard": {}},
                do_compare_enabled=True,
                progress_state={"status": "done"},
            )

        assert "sim-compare-results-table" in str(result_ui)

    @pytest.mark.unit()
    def Test_Stats_Table_Renders_Empty_Message_When_Data_Missing(self) -> None:
        """Missing stats or results should render the empty statistics message."""
        result_ui = sim_render.build_stats_table_ui_for_simulation(
            results_df=None,
            stats_df=None,
        )

        assert "Run a simulation to see statistics" in str(result_ui)

    @pytest.mark.unit()
    def Test_Stats_Table_Renders_Metrics_When_Data_Available(
        self,
        fixture_results_dataframe: pl.DataFrame,
        fixture_stats_dataframe: pl.DataFrame,
    ) -> None:
        """Available results should render the summary statistics table."""
        result_ui = sim_render.build_stats_table_ui_for_simulation(
            results_df=fixture_results_dataframe,
            stats_df=fixture_stats_dataframe,
        )

        result_html = str(result_ui)
        assert "Number of Scenarios" in result_html
        assert "Prob(Loss)" in result_html
        assert "table table-striped table-hover table-sm" in result_html

    @pytest.mark.unit()
    def Test_Stats_Table_Boolean_Scenario_Columns_Return_Empty_Message(self) -> None:
        """Boolean scenario columns should not be rendered as numeric simulation statistics."""
        results_df = pl.DataFrame(
            {
                "Date": [1, 2],
                "Scenario_1": [True, False],
                "Scenario_2": [False, True],
            },
        )
        stats_df = pl.DataFrame({"Metric": ["Mean"], "Value": [1.0]})

        result_ui = sim_render.build_stats_table_ui_for_simulation(
            results_df=results_df,
            stats_df=stats_df,
        )

        assert "Run a simulation to see statistics" in str(result_ui)
"""Focused unit tests for extracted weights-analysis helper modules."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import polars as pl
import pytest

from src.dashboard.shiny_tab_portfolios._subtab_weights_analysis_data import (
    normalize_weights_source_frame,
)
from src.dashboard.shiny_tab_portfolios._subtab_weights_analysis_rendering import (
    _build_display_weights_frame,
    build_component_checkboxes_ui,
    build_selected_components_count_text,
    build_weights_data_info_ui,
    build_weights_loading_status_ui,
    build_weights_main_figure,
    build_weights_secondary_figure,
    build_weights_summary_table_ui,
    register_weights_analysis_outputs,
)


@pytest.fixture()
def fixture_weights_frame_large() -> pl.DataFrame:
    """Return a large source dataframe for weights-helper tests."""
    base_datetime = datetime(2024, 1, 1, tzinfo=UTC)
    date_values = [
        (base_datetime + timedelta(days=idx_day)).strftime("%Y-%m-%d")
        for idx_day in range(260)
    ]
    return pl.DataFrame(
        {
            "Date": date_values,
            "VTI": [0.40 + idx_day * 0.0001 for idx_day in range(260)],
            "VXUS": [0.30 for _ in range(260)],
            "BND": [0.20 for _ in range(260)],
            "VNQ": [0.10 - idx_day * 0.0001 for idx_day in range(260)],
        },
    )


@pytest.fixture()
def fixture_weights_frame_normalized(
    fixture_weights_frame_large: pl.DataFrame,
) -> pl.DataFrame:
    """Return the normalized weights dataframe used in helper tests."""
    return normalize_weights_source_frame(weights_source = fixture_weights_frame_large)


@pytest.fixture()
def fixture_reactives_shiny() -> dict[str, Any]:
    """Return a minimal shared-reactives mapping for rendering tests."""
    return {"Visual_Objects_Shiny": {}, "Data_Results": {}}


class Class_Test_Subtab_Weights_Analysis_Rendering_Helpers:
    """Unit tests for weights-analysis rendering helpers."""

    @pytest.mark.unit()
    def Test_Build_Component_Checkboxes_UI_Handles_Empty_Components(self) -> None:
        """The checkbox renderer should provide a no-components fallback."""
        checkbox_ui = build_component_checkboxes_ui(available_components = [])

        assert checkbox_ui is not None

    @pytest.mark.unit()
    def Test_Build_Component_Checkboxes_UI_Builds_Checkboxes_For_Available_Components(
        self,
    ) -> None:
        """The checkbox renderer should build a populated container for components."""
        checkbox_ui = build_component_checkboxes_ui(available_components = ["VTI", "VXUS", "BND", "VNQ"])

        assert checkbox_ui is not None

    @pytest.mark.unit()
    def Test_Build_Weights_Loading_Status_UI_Success_And_Warning_States(self) -> None:
        """The loading-status helper should build both success and warning UI blocks."""
        success_ui = build_weights_loading_status_ui(selected_row_count = 25, selected_component_count = 3)
        warning_ui = build_weights_loading_status_ui(selected_row_count = 0, selected_component_count = 0)

        assert success_ui is not None
        assert warning_ui is not None

    @pytest.mark.unit()
    def Test_Build_Weights_Loading_Status_UI_Warns_When_Only_Component_Count_Is_Zero(
        self,
    ) -> None:
        """The loading-status warning branch should also trigger on zero components alone."""
        warning_ui = build_weights_loading_status_ui(selected_row_count = 12, selected_component_count = 0)

        assert warning_ui is not None

    @pytest.mark.unit()
    def Test_Build_Selected_Components_Count_Text_Uses_Current_Selection(self) -> None:
        """The selected-components label should reflect the active selection count."""
        count_text = build_selected_components_count_text(
            available_components = ["VTI", "VXUS", "BND", "VNQ"],
            selected_components = ["VTI", "BND"],
        )

        assert count_text == "Selected: 2 of 4 components"

    @pytest.mark.unit()
    def Test_Build_Weights_Data_Info_UI_Handles_Filtered_And_Selected_Empty_States(
        self,
        fixture_weights_frame_normalized: pl.DataFrame,
    ) -> None:
        """The data-info helper should handle empty filtered and selected frames."""
        info_ui = build_weights_data_info_ui(
            weights_frame_original = fixture_weights_frame_normalized,
            weights_frame_filtered = fixture_weights_frame_normalized.head(0),
            weights_frame_selected = fixture_weights_frame_normalized.head(0),
            available_components = ["VTI", "VXUS", "BND", "VNQ"],
            selected_components = [],
        )

        assert info_ui is not None

    @pytest.mark.unit()
    def Test_Build_Weights_Data_Info_UI_Handles_Empty_Original_Frame(self) -> None:
        """The data-info helper should render the empty-original-data fallback."""
        empty_frame = pl.DataFrame(
            schema={"Date": pl.Datetime, "VTI": pl.Float64, "VXUS": pl.Float64},
        )
        info_ui = build_weights_data_info_ui(
            weights_frame_original = empty_frame,
            weights_frame_filtered = empty_frame,
            weights_frame_selected = empty_frame,
            available_components = ["VTI", "VXUS"],
            selected_components = [],
        )

        assert info_ui is not None

    @pytest.mark.unit()
    def Test_Build_Weights_Data_Info_UI_Handles_Non_Empty_Filtered_And_Selected_Frames(
        self,
        fixture_weights_frame_normalized: pl.DataFrame,
    ) -> None:
        """The data-info helper should render the ready-for-analysis branch."""
        frame_subset = fixture_weights_frame_normalized.head(10)
        info_ui = build_weights_data_info_ui(
            weights_frame_original = fixture_weights_frame_normalized,
            weights_frame_filtered = frame_subset,
            weights_frame_selected = frame_subset.select(["Date", "VTI", "VXUS"]),
            available_components = ["VTI", "VXUS", "BND", "VNQ"],
            selected_components = ["VTI", "VXUS"],
        )

        assert info_ui is not None

    @pytest.mark.unit()
    def Test_Build_Display_Weights_Frame_Applies_Percentage_And_Sorting(
        self,
        fixture_weights_frame_normalized: pl.DataFrame,
    ) -> None:
        """The display-frame helper should convert to percentages and sort by mean weight."""
        display_frame, component_columns = _build_display_weights_frame(
            weights_frame = fixture_weights_frame_normalized.head(5),
            show_percentage=True,
            sort_components=True,
        )

        first_row_total = sum(
            float(display_frame.get_column(component_name)[0])
            for component_name in component_columns
        )

        assert component_columns[0] == "VTI"
        assert first_row_total == pytest.approx(100.0)

    @pytest.mark.unit()
    def Test_Build_Weights_Main_Figure_Supports_Bar_And_Heatmap(
        self,
        fixture_weights_frame_normalized: pl.DataFrame,
        fixture_reactives_shiny: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The main-figure helper should support the public bar and heatmap options."""
        monkeypatch.setattr(
            "src.dashboard.shiny_tab_portfolios._subtab_weights_analysis_rendering.build_plotnine_weights_analysis_distribution_over_time",
            lambda *, weights_df: {"frame_height": weights_df.height},
        )
        monkeypatch.setattr(
            "src.dashboard.shiny_tab_portfolios._subtab_weights_analysis_rendering.update_visual_object_in_reactives",
            lambda *, reactives_shiny, chart_key, figure: reactives_shiny["Visual_Objects_Shiny"].update({chart_key: figure}),
        )

        frame_plot = fixture_weights_frame_normalized.head(20)
        bar_figure = build_weights_main_figure(
            weights_frame_selected = frame_plot,
            viz_type="bar",
            show_percentage=True,
            sort_components=True,
            reactives_shiny=fixture_reactives_shiny,
        )
        heatmap_figure = build_weights_main_figure(
            weights_frame_selected = frame_plot,
            viz_type="heatmap",
            show_percentage=False,
            sort_components=False,
            reactives_shiny=fixture_reactives_shiny,
        )

        assert all(trace.type == "bar" for trace in bar_figure.data)
        assert heatmap_figure.data[0].type == "heatmap"
        assert "Chart_Weights_Analysis_Portfolio_Weight_Distribution_Over_Time" in fixture_reactives_shiny["Visual_Objects_Shiny"]

    @pytest.mark.unit()
    def Test_Build_Weights_Main_Figure_Supports_Line_And_Default_Area(
        self,
        fixture_weights_frame_normalized: pl.DataFrame,
        fixture_reactives_shiny: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The main-figure helper should support line and fallback area charts."""
        monkeypatch.setattr(
            "src.dashboard.shiny_tab_portfolios._subtab_weights_analysis_rendering.build_plotnine_weights_analysis_distribution_over_time",
            lambda *, weights_df: {"frame_height": weights_df.height},
        )
        monkeypatch.setattr(
            "src.dashboard.shiny_tab_portfolios._subtab_weights_analysis_rendering.update_visual_object_in_reactives",
            lambda *, reactives_shiny, chart_key, figure: reactives_shiny["Visual_Objects_Shiny"].update({chart_key: figure}),
        )

        frame_plot = fixture_weights_frame_normalized.head(15)
        line_figure = build_weights_main_figure(
            weights_frame_selected = frame_plot,
            viz_type="line",
            show_percentage=False,
            sort_components=False,
            reactives_shiny=fixture_reactives_shiny,
        )
        area_figure = build_weights_main_figure(
            weights_frame_selected = frame_plot,
            viz_type="unexpected-option",
            show_percentage=False,
            sort_components=False,
            reactives_shiny=fixture_reactives_shiny,
        )

        assert all(trace.type == "scatter" for trace in line_figure.data)
        assert all(trace.mode == "lines+markers" for trace in line_figure.data)
        assert all(trace.stackgroup == "one" for trace in area_figure.data)
        assert area_figure.layout.xaxis.rangeslider.visible is True

    @pytest.mark.unit()
    def Test_Build_Weights_Main_And_Secondary_Figures_Return_Error_Fallbacks(
        self,
        fixture_weights_frame_normalized: pl.DataFrame,
        fixture_reactives_shiny: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Empty frames and missing components should return error-figure fallbacks."""
        monkeypatch.setattr(
            "src.dashboard.shiny_tab_portfolios._subtab_weights_analysis_rendering.create_error_figure",
            lambda *, title_text, message_text, **___: {
                "title": title_text,
                "message": message_text,
            },
        )

        empty_frame = fixture_weights_frame_normalized.head(0)
        date_only_frame = fixture_weights_frame_normalized.select("Date")

        empty_main = build_weights_main_figure(
            weights_frame_selected = empty_frame,
            viz_type="area",
            show_percentage=True,
            sort_components=True,
            reactives_shiny=fixture_reactives_shiny,
        )
        empty_secondary = build_weights_secondary_figure(
            weights_frame_selected = empty_frame,
            reactives_shiny=fixture_reactives_shiny,
        )
        no_component_main = build_weights_main_figure(
            weights_frame_selected = date_only_frame,
            viz_type="area",
            show_percentage=True,
            sort_components=True,
            reactives_shiny=fixture_reactives_shiny,
        )
        no_component_secondary = build_weights_secondary_figure(
            weights_frame_selected = date_only_frame,
            reactives_shiny=fixture_reactives_shiny,
        )

        assert empty_main["message"] == "No Data Available"
        assert empty_secondary["message"] == "No Data Available"
        assert no_component_main["message"] == "No Components Selected"
        assert no_component_secondary["message"] == "No Components Selected"

    @pytest.mark.unit()
    def Test_Build_Weights_Secondary_Figure_Updates_Shared_Snapshot(
        self,
        fixture_weights_frame_normalized: pl.DataFrame,
        fixture_reactives_shiny: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The secondary pie-chart helper should update the shared reactive snapshot."""
        monkeypatch.setattr(
            "src.dashboard.shiny_tab_portfolios._subtab_weights_analysis_rendering.build_plotnine_weights_analysis_current_composition",
            lambda *, labels, values: {"labels": labels, "values": values},
        )
        monkeypatch.setattr(
            "src.dashboard.shiny_tab_portfolios._subtab_weights_analysis_rendering.update_visual_object_in_reactives",
            lambda *, reactives_shiny, chart_key, figure: reactives_shiny["Visual_Objects_Shiny"].update({chart_key: figure}),
        )

        figure_plot = build_weights_secondary_figure(
            weights_frame_selected = fixture_weights_frame_normalized.head(10),
            reactives_shiny=fixture_reactives_shiny,
        )

        assert figure_plot.data[0].type == "pie"
        assert "Chart_Weights_Analysis_Portfolio_Current_Composition" in fixture_reactives_shiny["Visual_Objects_Shiny"]

    @pytest.mark.unit()
    def Test_Build_Weights_Summary_Table_UI_Persists_Report_Payload(
        self,
        fixture_weights_frame_normalized: pl.DataFrame,
        fixture_reactives_shiny: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The summary-table helper should persist report-compatible statistics."""
        monkeypatch.setattr(
            "src.dashboard.shiny_tab_portfolios._subtab_weights_analysis_rendering.save_weights_analysis_outputs_to_reactives",
            lambda *, reactives_shiny, data_value, **___: reactives_shiny["Data_Results"].update(data_value),
        )

        summary_ui = build_weights_summary_table_ui(
            weights_frame_selected = fixture_weights_frame_normalized.head(10),
            reactives_shiny=fixture_reactives_shiny,
        )

        assert summary_ui is not None
        assert "weight_statistics" in fixture_reactives_shiny["Data_Results"]

    @pytest.mark.unit()
    def Test_Build_Weights_Summary_Table_UI_Handles_Empty_Frame_And_Save_Failure(
        self,
        fixture_weights_frame_normalized: pl.DataFrame,
        fixture_reactives_shiny: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The summary-table helper should tolerate empty data and save failures."""
        empty_summary_ui = build_weights_summary_table_ui(
            weights_frame_selected = fixture_weights_frame_normalized.head(0),
            reactives_shiny=fixture_reactives_shiny,
        )

        monkeypatch.setattr(
            "src.dashboard.shiny_tab_portfolios._subtab_weights_analysis_rendering.save_weights_analysis_outputs_to_reactives",
            lambda *, reactives_shiny, payload_outputs, **___: (_ for _ in ()).throw(RuntimeError("persist failed")),
        )
        populated_summary_ui = build_weights_summary_table_ui(
            weights_frame_selected = fixture_weights_frame_normalized.head(10),
            reactives_shiny=fixture_reactives_shiny,
        )

        assert empty_summary_ui is not None
        assert populated_summary_ui is not None

    @pytest.mark.unit()
    def Test_Register_Weights_Analysis_Outputs_Uses_Default_Input_Fallbacks(
        self,
        fixture_weights_frame_normalized: pl.DataFrame,
        fixture_reactives_shiny: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Output registration should fall back cleanly when optional inputs are missing."""

        class FakeInput:
            def input_ID_tab_portfolios_subtab_weights_analysis_time_period(self):
                raise RuntimeError("time period unavailable")

            def input_ID_tab_portfolios_subtab_weights_analysis_date_range(self):
                raise RuntimeError("date range unavailable")

            def input_ID_tab_portfolios_subtab_weights_analysis_select_all_components(self):
                raise RuntimeError("select-all unavailable")

            def input_ID_tab_portfolios_subtab_weights_analysis_viz_type(self):
                raise RuntimeError("viz type unavailable")

            def input_ID_tab_portfolios_subtab_weights_analysis_show_pct(self):
                raise RuntimeError("show-pct unavailable")

            def input_ID_tab_portfolios_subtab_weights_analysis_sort_components(self):
                raise RuntimeError("sort unavailable")

            def __getitem__(self, key: str):
                raise KeyError(key)

        registered_outputs: dict[str, Any] = {}

        def identity_decorator(func):
            return func

        def capture_output(func):
            registered_outputs[func.__name__] = func
            return func

        monkeypatch.setattr(
            "src.dashboard.shiny_tab_portfolios._subtab_weights_analysis_rendering.reactive.calc",
            identity_decorator,
        )
        monkeypatch.setattr(
            "src.dashboard.shiny_tab_portfolios._subtab_weights_analysis_rendering.render.ui",
            identity_decorator,
        )
        monkeypatch.setattr(
            "src.dashboard.shiny_tab_portfolios._subtab_weights_analysis_rendering.render.text",
            identity_decorator,
        )
        monkeypatch.setattr(
            "src.dashboard.shiny_tab_portfolios._subtab_weights_analysis_rendering.render_widget",
            identity_decorator,
        )
        monkeypatch.setattr(
            "src.dashboard.shiny_tab_portfolios._subtab_weights_analysis_rendering.build_component_checkboxes_ui",
            lambda *, available_components, select_all=False, **kwargs: {"available_components": available_components},
        )
        monkeypatch.setattr(
            "src.dashboard.shiny_tab_portfolios._subtab_weights_analysis_rendering.build_selected_components_count_text",
            lambda available_components, selected_components: f"{len(selected_components)}/{len(available_components)}",
        )
        monkeypatch.setattr(
            "src.dashboard.shiny_tab_portfolios._subtab_weights_analysis_rendering.build_weights_calculated_date_range_text",
            lambda *, start_datetime, end_datetime: f"{start_datetime.date()}->{end_datetime.date()}",
        )
        monkeypatch.setattr(
            "src.dashboard.shiny_tab_portfolios._subtab_weights_analysis_rendering.build_weights_loading_status_ui",
            lambda *, selected_row_count, selected_component_count: {"rows": selected_row_count, "components": selected_component_count},
        )
        monkeypatch.setattr(
            "src.dashboard.shiny_tab_portfolios._subtab_weights_analysis_rendering.build_weights_data_info_ui",
            lambda *, weights_frame_original, weights_frame_filtered, weights_frame_selected, available_components, selected_components: {
                "original_rows": weights_frame_original.height,
                "filtered_rows": weights_frame_filtered.height,
                "selected_rows": weights_frame_selected.height,
                "available_components": available_components,
                "selected_components": selected_components,
            },
        )
        monkeypatch.setattr(
            "src.dashboard.shiny_tab_portfolios._subtab_weights_analysis_rendering.build_weights_main_figure",
            lambda *, weights_frame_selected, **kwargs: {"rows": weights_frame_selected.height, **kwargs},
        )
        monkeypatch.setattr(
            "src.dashboard.shiny_tab_portfolios._subtab_weights_analysis_rendering.build_weights_secondary_figure",
            lambda *, weights_frame_selected, **kwargs: {"rows": weights_frame_selected.height, **kwargs},
        )
        monkeypatch.setattr(
            "src.dashboard.shiny_tab_portfolios._subtab_weights_analysis_rendering.build_weights_summary_table_ui",
            lambda *, weights_frame_selected, **kwargs: {"rows": weights_frame_selected.height, **kwargs},
        )

        register_weights_analysis_outputs(
            input=FakeInput(),
            output=capture_output,
            data_utils={},
            weights_frame=fixture_weights_frame_normalized,
            reactives_shiny=fixture_reactives_shiny,
        )

        component_checkboxes = registered_outputs[
            "output_ID_tab_portfolios_subtab_weights_analysis_component_checkboxes"
        ]()
        count_text = registered_outputs[
            "output_ID_tab_portfolios_subtab_weights_analysis_selected_components_count"
        ]()
        calculated_date_range = registered_outputs[
            "output_ID_tab_portfolios_subtab_weights_analysis_calculated_date_range"
        ]()
        loading_status = registered_outputs[
            "output_ID_tab_portfolios_subtab_weights_analysis_loading_status"
        ]()
        data_info = registered_outputs[
            "output_ID_tab_portfolios_subtab_weights_analysis_data_info"
        ]()
        plot_main = registered_outputs[
            "output_ID_tab_portfolios_subtab_weights_analysis_plot_main"
        ]()
        plot_secondary = registered_outputs[
            "output_ID_tab_portfolios_subtab_weights_analysis_plot_secondary"
        ]()
        table_summary = registered_outputs[
            "output_ID_tab_portfolios_subtab_weights_analysis_table_summary"
        ]()

        assert component_checkboxes["available_components"] == ["VTI", "VXUS", "BND", "VNQ"]
        assert count_text == "3/4"
        assert calculated_date_range == "2019-09-18->2024-09-16"
        assert loading_status["components"] == 3
        assert data_info["selected_components"] == ["VTI", "VXUS", "BND"]
        assert plot_main["viz_type"] == "area"
        assert plot_main["show_percentage"] is True
        assert plot_main["sort_components"] is True
        assert plot_secondary["rows"] > 0
        assert table_summary["rows"] > 0

    @pytest.mark.unit()
    def Test_Register_Weights_Analysis_Outputs_Handles_No_Available_Components(
        self,
        fixture_weights_frame_normalized: pl.DataFrame,
        fixture_reactives_shiny: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Output registration should handle frames without ETF component columns."""

        class FakeInput:
            def input_ID_tab_portfolios_subtab_weights_analysis_time_period(self):
                return "5y"

            def input_ID_tab_portfolios_subtab_weights_analysis_date_range(self):
                return None

            def __getitem__(self, key: str):
                raise KeyError(key)

        registered_outputs: dict[str, Any] = {}

        def identity_decorator(func):
            return func

        def capture_output(func):
            registered_outputs[func.__name__] = func
            return func

        monkeypatch.setattr(
            "src.dashboard.shiny_tab_portfolios._subtab_weights_analysis_rendering.reactive.calc",
            identity_decorator,
        )
        monkeypatch.setattr(
            "src.dashboard.shiny_tab_portfolios._subtab_weights_analysis_rendering.render.ui",
            identity_decorator,
        )
        monkeypatch.setattr(
            "src.dashboard.shiny_tab_portfolios._subtab_weights_analysis_rendering.render.text",
            identity_decorator,
        )
        monkeypatch.setattr(
            "src.dashboard.shiny_tab_portfolios._subtab_weights_analysis_rendering.render_widget",
            identity_decorator,
        )
        monkeypatch.setattr(
            "src.dashboard.shiny_tab_portfolios._subtab_weights_analysis_rendering.build_selected_components_count_text",
            lambda available_components, selected_components: f"{len(selected_components)}/{len(available_components)}",
        )

        date_only_frame = fixture_weights_frame_normalized.select(["Date"])
        register_weights_analysis_outputs(
            input=FakeInput(),
            output=capture_output,
            data_utils={},
            weights_frame=date_only_frame,
            reactives_shiny=fixture_reactives_shiny,
        )

        count_text = registered_outputs[
            "output_ID_tab_portfolios_subtab_weights_analysis_selected_components_count"
        ]()

        assert count_text == "0/0"
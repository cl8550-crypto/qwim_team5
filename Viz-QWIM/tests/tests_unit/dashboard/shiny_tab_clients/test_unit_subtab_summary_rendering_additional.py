"""Additional unit tests for private client summary rendering fallback and observer helpers."""

from __future__ import annotations

from typing import Any

import polars as pl
import pytest

from src.dashboard.shiny_tab_clients import _subtab_summary_rendering as summary_render
from tests.tests_unit.dashboard.shiny_tab_clients.test_unit_subtab_summary_rendering import (
    _Reactive_Value_Test,
    _Table_HTML_Fake,
    _build_reactives_shiny_summary,
    fixture_captured_summary_outputs,
)


def _patch_observer_dependencies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        summary_render.summary_data,
        "calc_table_summary_clients_assets",
        lambda reactives_shiny: pl.DataFrame(
            {
                "Asset_Category": ["Taxable"],
                "client_Primary": [100000.0],
                "client_Partner": [50000.0],
                "Combined_Total": [150000.0],
            },
        ),
    )
    monkeypatch.setattr(
        summary_render.summary_data,
        "calc_table_summary_clients_personal_info",
        lambda reactives_shiny: pl.DataFrame(
            {
                "Information_Category": ["Name"],
                "Primary_client": ["Jane Client"],
                "Partner_client": ["John Client"],
            },
        ),
    )
    monkeypatch.setattr(
        summary_render.summary_data,
        "calc_table_summary_clients_goals",
        lambda reactives_shiny: pl.DataFrame(
            {
                "Goal_Category": ["Essential"],
                "client_Primary": [80000.0],
                "client_Partner": [60000.0],
                "Combined_Total": [140000.0],
            },
        ),
    )
    monkeypatch.setattr(
        summary_render.summary_data,
        "calc_table_summary_clients_income",
        lambda reactives_shiny: pl.DataFrame(
            {
                "Income_Category": ["Social Security"],
                "client_Primary": [36000.0],
                "client_Partner": [24000.0],
                "Combined_Total": [60000.0],
            },
        ),
    )
    monkeypatch.setattr(
        summary_render,
        "create_enhanced_summary_table_multi_column",
        lambda **kwargs: _Table_HTML_Fake(f"<table>{kwargs['table_title']}</table>"),
    )


class Class_Test_Subtab_Summary_Rendering_Additional:
    """Additional tests for hard-to-hit summary-rendering fallback and observer paths."""

    @pytest.mark.unit()
    def Test_Assets_Output_Fallback_Formats_Invalid_Currency_As_Zero(
        self,
        fixture_captured_summary_outputs: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        reactives_shiny = _build_reactives_shiny_summary(
            include_partner=True,
            include_personal_data=True,
        )

        monkeypatch.setattr(
            summary_render.summary_data,
            "calc_table_summary_clients_assets",
            lambda reactives_shiny: pl.DataFrame(
                {
                    "Field Name": ["Taxable"],
                    "Client Primary": ["invalid"],
                    "Client Partner": ["invalid"],
                    "Combined Total": ["invalid"],
                },
            ),
        )
        monkeypatch.setattr(
            summary_render,
            "create_enhanced_summary_table_multi_column",
            lambda **kwargs: (_ for _ in ()).throw(RuntimeError("table builder failed")),
        )

        summary_render.register_clients_summary_server_outputs(
            _input_events=None,
            output=fixture_captured_summary_outputs["decorator_output"],
            reactives_shiny=reactives_shiny,
        )

        value_output = fixture_captured_summary_outputs[
            "output_ID_tab_clients_subtab_clients_summary_table_assets"
        ]()

        assert "Financial Assets Summary" in str(value_output)
        assert str(value_output).count("$0") >= 3

    @pytest.mark.unit()
    def Test_Goals_Output_Returns_Data_Processing_Error_When_Fallback_Fails(
        self,
        fixture_captured_summary_outputs: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        reactives_shiny = _build_reactives_shiny_summary(
            include_partner=True,
            include_personal_data=True,
        )

        monkeypatch.setattr(
            summary_render.summary_data,
            "calc_table_summary_clients_goals",
            lambda reactives_shiny: pl.DataFrame(
                {
                    "Goal_Category": ["Essential"],
                    "client_Primary": [80000.0],
                },
            ),
        )
        monkeypatch.setattr(
            summary_render,
            "create_enhanced_summary_table_multi_column",
            lambda **kwargs: (_ for _ in ()).throw(RuntimeError("table builder failed")),
        )

        summary_render.register_clients_summary_server_outputs(
            _input_events=None,
            output=fixture_captured_summary_outputs["decorator_output"],
            reactives_shiny=reactives_shiny,
        )

        value_output = fixture_captured_summary_outputs[
            "output_ID_tab_clients_subtab_clients_summary_table_goals"
        ]()

        assert "Goals Table - Data Processing Error" in str(value_output)
        assert "Fallback error" in str(value_output)

    @pytest.mark.unit()
    def Test_Goals_Output_Fallback_Formats_Invalid_Currency_As_Zero(
        self,
        fixture_captured_summary_outputs: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        reactives_shiny = _build_reactives_shiny_summary(
            include_partner=True,
            include_personal_data=True,
        )

        monkeypatch.setattr(
            summary_render.summary_data,
            "calc_table_summary_clients_goals",
            lambda reactives_shiny: pl.DataFrame(
                {
                    "Field Name": ["Essential"],
                    "Client Primary": ["invalid"],
                    "Client Partner": ["invalid"],
                    "Combined Total": ["invalid"],
                },
            ),
        )
        monkeypatch.setattr(
            summary_render,
            "create_enhanced_summary_table_multi_column",
            lambda **kwargs: (_ for _ in ()).throw(RuntimeError("table builder failed")),
        )

        summary_render.register_clients_summary_server_outputs(
            _input_events=None,
            output=fixture_captured_summary_outputs["decorator_output"],
            reactives_shiny=reactives_shiny,
        )

        value_output = fixture_captured_summary_outputs[
            "output_ID_tab_clients_subtab_clients_summary_table_goals"
        ]()

        assert "Financial Goals Summary" in str(value_output)
        assert str(value_output).count("$0") >= 3

    @pytest.mark.unit()
    def Test_Income_Output_Falls_Back_When_Enhanced_Table_Returns_None(
        self,
        fixture_captured_summary_outputs: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        reactives_shiny = _build_reactives_shiny_summary(
            include_partner=True,
            include_personal_data=True,
        )

        monkeypatch.setattr(
            summary_render,
            "create_enhanced_summary_table_multi_column",
            lambda **kwargs: None,
        )

        summary_render.register_clients_summary_server_outputs(
            _input_events=None,
            output=fixture_captured_summary_outputs["decorator_output"],
            reactives_shiny=reactives_shiny,
        )

        value_output = fixture_captured_summary_outputs[
            "output_ID_tab_clients_subtab_clients_summary_table_income"
        ]()

        assert "Income Sources Summary" in str(value_output)
        assert "Annual income projections from all sources for retirement planning" in str(value_output)

    @pytest.mark.unit()
    def Test_Income_Output_Returns_Data_Processing_Error_When_Fallback_Fails(
        self,
        fixture_captured_summary_outputs: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        reactives_shiny = _build_reactives_shiny_summary(
            include_partner=True,
            include_personal_data=True,
        )

        monkeypatch.setattr(
            summary_render.summary_data,
            "calc_table_summary_clients_income",
            lambda reactives_shiny: pl.DataFrame(
                {
                    "Income_Category": ["Pension"],
                    "client_Primary": [12000.0],
                },
            ),
        )
        monkeypatch.setattr(
            summary_render,
            "create_enhanced_summary_table_multi_column",
            lambda **kwargs: (_ for _ in ()).throw(RuntimeError("table builder failed")),
        )

        summary_render.register_clients_summary_server_outputs(
            _input_events=None,
            output=fixture_captured_summary_outputs["decorator_output"],
            reactives_shiny=reactives_shiny,
        )

        value_output = fixture_captured_summary_outputs[
            "output_ID_tab_clients_subtab_clients_summary_table_income"
        ]()

        assert "Income Table - Data Processing Error" in str(value_output)
        assert "Fallback error" in str(value_output)

    @pytest.mark.unit()
    def Test_Income_Output_Fallback_Formats_Invalid_Currency_As_Zero(
        self,
        fixture_captured_summary_outputs: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        reactives_shiny = _build_reactives_shiny_summary(
            include_partner=True,
            include_personal_data=True,
        )

        monkeypatch.setattr(
            summary_render.summary_data,
            "calc_table_summary_clients_income",
            lambda reactives_shiny: pl.DataFrame(
                {
                    "Field Name": ["Pension"],
                    "Client Primary": ["invalid"],
                    "Client Partner": ["invalid"],
                    "Combined Total": ["invalid"],
                },
            ),
        )
        monkeypatch.setattr(
            summary_render,
            "create_enhanced_summary_table_multi_column",
            lambda **kwargs: (_ for _ in ()).throw(RuntimeError("table builder failed")),
        )

        summary_render.register_clients_summary_server_outputs(
            _input_events=None,
            output=fixture_captured_summary_outputs["decorator_output"],
            reactives_shiny=reactives_shiny,
        )

        value_output = fixture_captured_summary_outputs[
            "output_ID_tab_clients_subtab_clients_summary_table_income"
        ]()

        assert "Income Sources Summary" in str(value_output)
        assert str(value_output).count("$0") >= 3

    @pytest.mark.unit()
    def Test_Observer_Ignores_Empty_Reactives_Mapping(
        self,
        fixture_captured_summary_outputs: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        reactives_shiny: dict[str, Any] = {}

        _patch_observer_dependencies(monkeypatch)

        summary_render.register_clients_summary_server_outputs(
            _input_events=None,
            output=fixture_captured_summary_outputs["decorator_output"],
            reactives_shiny=reactives_shiny,
        )

        result_effect = fixture_captured_summary_outputs["effect_functions"][
            "observer_update_shared_reactives_shiny_summary"
        ]()

        assert result_effect is None

    @pytest.mark.unit()
    def Test_Observer_Ignores_Non_Dict_Shared_Categories(
        self,
        fixture_captured_summary_outputs: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        reactives_shiny = {
            "Visual_Objects_Shiny": ["not-a-dict"],
            "Inner_Variables_Shiny": None,
        }

        _patch_observer_dependencies(monkeypatch)

        summary_render.register_clients_summary_server_outputs(
            _input_events=None,
            output=fixture_captured_summary_outputs["decorator_output"],
            reactives_shiny=reactives_shiny,
        )

        result_effect = fixture_captured_summary_outputs["effect_functions"][
            "observer_update_shared_reactives_shiny_summary"
        ]()

        assert result_effect is None

    @pytest.mark.unit()
    def Test_Observer_Updates_Only_Valid_Reactive_Targets(
        self,
        fixture_captured_summary_outputs: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        table_goals_reactive = _Reactive_Value_Test(None)
        data_income_reactive = _Reactive_Value_Test(None)
        reactives_shiny = {
            "Visual_Objects_Shiny": {
                "Table_Assets": None,
                "Table_Personal_Info": object(),
                "Table_Goals": table_goals_reactive,
            },
            "Inner_Variables_Shiny": {
                "Data_Assets_DF": None,
                "Data_Personal_Info_DF": object(),
                "Data_Income_DF": data_income_reactive,
            },
        }

        _patch_observer_dependencies(monkeypatch)

        summary_render.register_clients_summary_server_outputs(
            _input_events=None,
            output=fixture_captured_summary_outputs["decorator_output"],
            reactives_shiny=reactives_shiny,
        )

        fixture_captured_summary_outputs["effect_functions"][
            "observer_update_shared_reactives_shiny_summary"
        ]()

        assert table_goals_reactive.get().as_raw_html() == "<table>Financial Goals Summary</table>"
        assert isinstance(data_income_reactive.get(), pl.DataFrame)
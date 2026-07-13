"""Unit tests for private client summary rendering fallback and observer helpers."""

from __future__ import annotations

from typing import Any

import polars as pl
import pytest

from src.dashboard.shiny_tab_clients import _subtab_summary_rendering as summary_render


class _Reactive_Value_Test:
    def __init__(
        self,
        value_current: Any = None,
    ) -> None:
        self._value_current = value_current

    def get(self) -> Any:
        return self._value_current

    def set(
        self,
        value_new: Any,
    ) -> None:
        self._value_current = value_new


class _Table_HTML_Fake:
    def __init__(
        self,
        value_html: str,
    ) -> None:
        self._value_html = value_html

    def as_raw_html(self) -> str:
        return self._value_html



def _build_reactives_shiny_summary(
    *,
    include_partner: bool,
    include_personal_data: bool,
) -> dict[str, Any]:
    def create_reactive_value(
        value_current: Any,
    ) -> _Reactive_Value_Test:
        return _Reactive_Value_Test(value_current)

    if include_personal_data:
        value_primary_name = "Jane Client"
        value_primary_age_current = 65
        value_primary_age_retirement = 67
        value_primary_age_income_starting = 67
        value_primary_status_marital = "Married"
        value_primary_gender = "Female"
        value_primary_tolerance_risk = "Moderate"
        value_primary_state = "CA"
        value_primary_code_zip = "90210"
        value_partner_name = "John Client"
        value_partner_age_current = 63
        value_partner_age_retirement = 65
        value_partner_age_income_starting = 65
        value_partner_status_marital = "Married"
        value_partner_gender = "Male"
        value_partner_tolerance_risk = "Balanced"
        value_partner_state = "CA"
        value_partner_code_zip = "90210"
    else:
        value_primary_name = None
        value_primary_age_current = None
        value_primary_age_retirement = None
        value_primary_age_income_starting = None
        value_primary_status_marital = None
        value_primary_gender = None
        value_primary_tolerance_risk = None
        value_primary_state = None
        value_primary_code_zip = None
        value_partner_name = None
        value_partner_age_current = None
        value_partner_age_retirement = None
        value_partner_age_income_starting = None
        value_partner_status_marital = None
        value_partner_gender = None
        value_partner_tolerance_risk = None
        value_partner_state = None
        value_partner_code_zip = None

    return {
        "User_Inputs_Shiny": {
            "Input_Tab_clients_Subtab_clients_Personal_Info_Include_Partner_In_Analysis": create_reactive_value(include_partner),
            "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Name": create_reactive_value(value_primary_name),
            "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Age_Current": create_reactive_value(value_primary_age_current),
            "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Age_Retirement": create_reactive_value(value_primary_age_retirement),
            "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Age_Income_Starting": create_reactive_value(value_primary_age_income_starting),
            "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Status_Marital": create_reactive_value(value_primary_status_marital),
            "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Gender": create_reactive_value(value_primary_gender),
            "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Tolerance_Risk": create_reactive_value(value_primary_tolerance_risk),
            "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_State": create_reactive_value(value_primary_state),
            "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Code_Zip": create_reactive_value(value_primary_code_zip),
            "Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Name": create_reactive_value(value_partner_name),
            "Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Age_Current": create_reactive_value(value_partner_age_current),
            "Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Age_Retirement": create_reactive_value(value_partner_age_retirement),
            "Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Age_Income_Starting": create_reactive_value(value_partner_age_income_starting),
            "Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Status_Marital": create_reactive_value(value_partner_status_marital),
            "Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Gender": create_reactive_value(value_partner_gender),
            "Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Tolerance_Risk": create_reactive_value(value_partner_tolerance_risk),
            "Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_State": create_reactive_value(value_partner_state),
            "Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Code_Zip": create_reactive_value(value_partner_code_zip),
            "Input_Tab_clients_Subtab_clients_Assets_client_Primary_Assets_Taxable": create_reactive_value(100000.0),
            "Input_Tab_clients_Subtab_clients_Assets_client_Primary_Assets_Tax_Deferred": create_reactive_value(200000.0),
            "Input_Tab_clients_Subtab_clients_Assets_client_Primary_Assets_Tax_Free": create_reactive_value(300000.0),
            "Input_Tab_clients_Subtab_clients_Assets_client_Partner_Assets_Taxable": create_reactive_value(40000.0),
            "Input_Tab_clients_Subtab_clients_Assets_client_Partner_Assets_Tax_Deferred": create_reactive_value(50000.0),
            "Input_Tab_clients_Subtab_clients_Assets_client_Partner_Assets_Tax_Free": create_reactive_value(60000.0),
            "Input_Tab_clients_Subtab_clients_Goals_client_Primary_Goal_Essential": create_reactive_value(80000.0),
            "Input_Tab_clients_Subtab_clients_Goals_client_Primary_Goal_Important": create_reactive_value(25000.0),
            "Input_Tab_clients_Subtab_clients_Goals_client_Primary_Goal_Aspirational": create_reactive_value(15000.0),
            "Input_Tab_clients_Subtab_clients_Goals_client_Partner_Goal_Essential": create_reactive_value(60000.0),
            "Input_Tab_clients_Subtab_clients_Goals_client_Partner_Goal_Important": create_reactive_value(10000.0),
            "Input_Tab_clients_Subtab_clients_Goals_client_Partner_Goal_Aspirational": create_reactive_value(5000.0),
            "Input_Tab_clients_Subtab_clients_Income_client_Primary_Income_Social_Security": create_reactive_value(36000.0),
            "Input_Tab_clients_Subtab_clients_Income_client_Primary_Income_Pension": create_reactive_value(12000.0),
            "Input_Tab_clients_Subtab_clients_Income_client_Primary_Income_Annuity_Existing": create_reactive_value(9000.0),
            "Input_Tab_clients_Subtab_clients_Income_client_Primary_Income_Other": create_reactive_value(3000.0),
            "Input_Tab_clients_Subtab_clients_Income_client_Partner_Income_Social_Security": create_reactive_value(24000.0),
            "Input_Tab_clients_Subtab_clients_Income_client_Partner_Income_Pension": create_reactive_value(8000.0),
            "Input_Tab_clients_Subtab_clients_Income_client_Partner_Income_Annuity_Existing": create_reactive_value(4000.0),
            "Input_Tab_clients_Subtab_clients_Income_client_Partner_Income_Other": create_reactive_value(2000.0),
        },
        "Inner_Variables_Shiny": {
            "Data_Assets_DF": create_reactive_value(None),
            "Data_Personal_Info_DF": create_reactive_value(None),
            "Data_Goals_DF": create_reactive_value(None),
            "Data_Income_DF": create_reactive_value(None),
        },
        "Triggers_Shiny": {},
        "Visual_Objects_Shiny": {
            "Table_Assets": create_reactive_value(None),
            "Table_Personal_Info": create_reactive_value(None),
            "Table_Goals": create_reactive_value(None),
            "Table_Income": create_reactive_value(None),
        },
        "Data_Clients": {},
        "Data_Results": {},
    }


@pytest.fixture()
def fixture_captured_summary_outputs(
    monkeypatch: pytest.MonkeyPatch,
) -> dict[str, Any]:
    monkeypatch.setattr(summary_render.reactive, "calc", lambda function: function)
    monkeypatch.setattr(summary_render.render, "ui", lambda function: function)

    dict_output_captured: dict[str, Any] = {}
    dict_effect_captured: dict[str, Any] = {}

    def decorator_output(function: Any) -> Any:
        dict_output_captured[function.__name__] = function
        return function

    def decorator_effect(function: Any) -> Any:
        dict_effect_captured[function.__name__] = function
        return function

    monkeypatch.setattr(summary_render.reactive, "effect", decorator_effect)

    dict_output_captured["decorator_output"] = decorator_output
    dict_output_captured["effect_functions"] = dict_effect_captured
    return dict_output_captured


class Class_Test_Subtab_Summary_Rendering:
    """Tests for the extracted private summary rendering helpers."""

    @pytest.mark.unit()
    def Test_Register_Server_Outputs_Captures_All_Summary_Functions(
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
            lambda **kwargs: _Table_HTML_Fake(kwargs["table_title"]),
        )

        summary_render.register_clients_summary_server_outputs(
            _input_events=None,
            output=fixture_captured_summary_outputs["decorator_output"],
            reactives_shiny=reactives_shiny,
        )

        assert "output_ID_tab_clients_subtab_clients_summary_table_personal_info" in fixture_captured_summary_outputs
        assert "output_ID_tab_clients_subtab_clients_summary_table_assets" in fixture_captured_summary_outputs
        assert "output_ID_tab_clients_subtab_clients_summary_table_goals" in fixture_captured_summary_outputs
        assert "output_ID_tab_clients_subtab_clients_summary_table_income" in fixture_captured_summary_outputs
        assert "observer_update_shared_reactives_shiny_summary" in fixture_captured_summary_outputs["effect_functions"]

    @pytest.mark.unit()
    def Test_Personal_Info_Output_Returns_No_Data_Message(
        self,
        fixture_captured_summary_outputs: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        reactives_shiny = _build_reactives_shiny_summary(
            include_partner=False,
            include_personal_data=False,
        )

        monkeypatch.setattr(
            summary_render,
            "create_enhanced_summary_table_multi_column",
            lambda **kwargs: _Table_HTML_Fake(kwargs["table_title"]),
        )

        summary_render.register_clients_summary_server_outputs(
            _input_events=None,
            output=fixture_captured_summary_outputs["decorator_output"],
            reactives_shiny=reactives_shiny,
        )

        value_output = fixture_captured_summary_outputs[
            "output_ID_tab_clients_subtab_clients_summary_table_personal_info"
        ]()

        assert "No personal information has been entered yet" in str(value_output)

    @pytest.mark.unit()
    def Test_Personal_Info_Output_Returns_Error_UI_When_Data_Is_None(
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
            "calc_table_summary_clients_personal_info",
            lambda reactives_shiny: None,
        )

        summary_render.register_clients_summary_server_outputs(
            _input_events=None,
            output=fixture_captured_summary_outputs["decorator_output"],
            reactives_shiny=reactives_shiny,
        )

        value_output = fixture_captured_summary_outputs[
            "output_ID_tab_clients_subtab_clients_summary_table_personal_info"
        ]()

        assert "data_Personal_Info_DF is None" in str(value_output)

    @pytest.mark.unit()
    def Test_Personal_Info_Output_Returns_Error_UI_When_Data_Is_Empty(
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
            "calc_table_summary_clients_personal_info",
            lambda reactives_shiny: pl.DataFrame(
                {
                    "Field Name": [],
                    "Client Primary": [],
                    "Client Partner": [],
                },
            ),
        )

        summary_render.register_clients_summary_server_outputs(
            _input_events=None,
            output=fixture_captured_summary_outputs["decorator_output"],
            reactives_shiny=reactives_shiny,
        )

        value_output = fixture_captured_summary_outputs[
            "output_ID_tab_clients_subtab_clients_summary_table_personal_info"
        ]()

        assert "data_Personal_Info_DF is empty" in str(value_output)

    @pytest.mark.unit()
    def Test_Personal_Info_Output_Returns_Normalization_Error_UI(
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
            "normalize_data_personal_info_summary",
            lambda *, data_personal_info_df, **___: (_ for _ in ()).throw(
                summary_render.Exception_Validation_Input("missing primary column"),
            ),
        )

        summary_render.register_clients_summary_server_outputs(
            _input_events=None,
            output=fixture_captured_summary_outputs["decorator_output"],
            reactives_shiny=reactives_shiny,
        )

        value_output = fixture_captured_summary_outputs[
            "output_ID_tab_clients_subtab_clients_summary_table_personal_info"
        ]()

        assert "Primary client column is missing" in str(value_output)

    @pytest.mark.unit()
    def Test_Personal_Info_Output_Falls_Back_When_Enhanced_Table_Returns_None(
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
            "output_ID_tab_clients_subtab_clients_summary_table_personal_info"
        ]()

        assert "Personal Information Summary" in str(value_output)
        assert "fallback table format" in str(value_output)

    @pytest.mark.unit()
    def Test_Personal_Info_Output_Uses_Enhanced_Table_When_Available(
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
            lambda **kwargs: _Table_HTML_Fake("<table>Personal Information Summary</table>"),
        )

        summary_render.register_clients_summary_server_outputs(
            _input_events=None,
            output=fixture_captured_summary_outputs["decorator_output"],
            reactives_shiny=reactives_shiny,
        )

        value_output = fixture_captured_summary_outputs[
            "output_ID_tab_clients_subtab_clients_summary_table_personal_info"
        ]()

        assert "Personal Information Summary" in str(value_output)

    @pytest.mark.unit()
    def Test_Assets_Output_Uses_Enhanced_Table_For_Single_Client(
        self,
        fixture_captured_summary_outputs: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        reactives_shiny = _build_reactives_shiny_summary(
            include_partner=False,
            include_personal_data=True,
        )
        list_table_calls: list[dict[str, Any]] = []

        def build_table_fake(**kwargs: Any) -> _Table_HTML_Fake:
            list_table_calls.append(kwargs)
            return _Table_HTML_Fake(f"<table>{kwargs['table_title']}</table>")

        monkeypatch.setattr(
            summary_render,
            "create_enhanced_summary_table_multi_column",
            build_table_fake,
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
        assert "Client Partner" not in list_table_calls[0]["dataframe_input"].columns
        assert list_table_calls[0]["currency_columns"] == ["Client Primary", "Combined Total"]

    @pytest.mark.unit()
    def Test_Assets_Output_Falls_Back_To_HTML_Table_When_Enhanced_Table_Fails(
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
        assert "Combined Total" in str(value_output)

    @pytest.mark.unit()
    def Test_Assets_Output_Returns_Data_Processing_Error_When_Fallback_Fails(
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
                {"Field Name": ["Taxable"], "Client Primary": [100000.0]},
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

        assert "Assets Table - Data Processing Error" in str(value_output)
        assert "Fallback error" in str(value_output)

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        ("assets_frame", "expected_fragment"),
        [
            (None, "data_Assets_DF is None"),
            (
                pl.DataFrame(
                    {
                        "Field Name": [],
                        "Client Primary": [],
                        "Client Partner": [],
                        "Combined Total": [],
                    },
                ),
                "data_Assets_DF is empty",
            ),
        ],
    )
    def Test_Assets_Output_Returns_Error_UI_When_Data_Is_None_Or_Empty(
        self,
        assets_frame: pl.DataFrame | None,
        expected_fragment: str,
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
            lambda reactives_shiny: assets_frame,
        )

        summary_render.register_clients_summary_server_outputs(
            _input_events=None,
            output=fixture_captured_summary_outputs["decorator_output"],
            reactives_shiny=reactives_shiny,
        )

        value_output = fixture_captured_summary_outputs[
            "output_ID_tab_clients_subtab_clients_summary_table_assets"
        ]()

        assert "Assets Table Generation Error" in str(value_output)
        assert expected_fragment in str(value_output)

    @pytest.mark.unit()
    def Test_Assets_Output_Falls_Back_When_Enhanced_Table_Returns_None(
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
            "output_ID_tab_clients_subtab_clients_summary_table_assets"
        ]()

        assert "Financial Assets Summary" in str(value_output)
        assert "Current asset values organized by tax treatment and client" in str(value_output)


    @pytest.mark.unit()
    def Test_Goals_Output_Falls_Back_To_HTML_Table_When_Enhanced_Table_Fails(
        self,
        fixture_captured_summary_outputs: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        reactives_shiny = _build_reactives_shiny_summary(
            include_partner=True,
            include_personal_data=True,
        )

        def raise_table_error(**kwargs: Any) -> _Table_HTML_Fake:
            raise RuntimeError("table builder failed")

        monkeypatch.setattr(
            summary_render,
            "create_enhanced_summary_table_multi_column",
            raise_table_error,
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
        assert "client Partner" in str(value_output)
        assert "$140,000" in str(value_output)

    @pytest.mark.unit()
    def Test_Goals_Output_Falls_Back_When_Enhanced_Table_Returns_None(
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
            "output_ID_tab_clients_subtab_clients_summary_table_goals"
        ]()

        assert "Financial Goals Summary" in str(value_output)
        assert "$140,000" in str(value_output)

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        ("goals_frame", "expected_fragment"),
        [
            (None, "data_Goals_DF is None"),
            (
                pl.DataFrame(
                    {
                        "Field Name": [],
                        "Client Primary": [],
                        "Client Partner": [],
                        "Combined Total": [],
                    },
                ),
                "data_Goals_DF is empty",
            ),
        ],
    )
    def Test_Goals_Output_Returns_Error_UI_When_Data_Is_None_Or_Empty(
        self,
        goals_frame: pl.DataFrame | None,
        expected_fragment: str,
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
            lambda reactives_shiny: goals_frame,
        )

        summary_render.register_clients_summary_server_outputs(
            _input_events=None,
            output=fixture_captured_summary_outputs["decorator_output"],
            reactives_shiny=reactives_shiny,
        )

        value_output = fixture_captured_summary_outputs[
            "output_ID_tab_clients_subtab_clients_summary_table_goals"
        ]()

        assert "Goals Table Generation Error" in str(value_output)
        assert expected_fragment in str(value_output)

    @pytest.mark.unit()
    def Test_Goals_Output_Uses_Enhanced_Table_When_Available(
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
            lambda **kwargs: _Table_HTML_Fake("<table>Financial Goals Summary</table>"),
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


    @pytest.mark.unit()
    def Test_Income_Output_Falls_Back_To_HTML_Table_When_Enhanced_Table_Fails(
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
        assert "Combined Total" in str(value_output)

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        ("income_frame", "expected_fragment"),
        [
            (None, "data_Income_DF is None"),
            (
                pl.DataFrame(
                    {
                        "Field Name": [],
                        "Client Primary": [],
                        "Client Partner": [],
                        "Combined Total": [],
                    },
                ),
                "data_Income_DF is empty",
            ),
        ],
    )
    def Test_Income_Output_Returns_Error_UI_When_Data_Is_None_Or_Empty(
        self,
        income_frame: pl.DataFrame | None,
        expected_fragment: str,
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
            lambda reactives_shiny: income_frame,
        )

        summary_render.register_clients_summary_server_outputs(
            _input_events=None,
            output=fixture_captured_summary_outputs["decorator_output"],
            reactives_shiny=reactives_shiny,
        )

        value_output = fixture_captured_summary_outputs[
            "output_ID_tab_clients_subtab_clients_summary_table_income"
        ]()

        assert "Income Table Generation Error" in str(value_output)
        assert expected_fragment in str(value_output)

    @pytest.mark.unit()
    def Test_Income_Output_Uses_Enhanced_Table_When_Available(
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
            lambda **kwargs: _Table_HTML_Fake("<table>Income Sources Summary</table>"),
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


    @pytest.mark.unit()
    def Test_Observer_Updates_Shared_Reactive_Values(
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
            lambda **kwargs: _Table_HTML_Fake(f"<table>{kwargs['table_title']}</table>"),
        )

        summary_render.register_clients_summary_server_outputs(
            _input_events=None,
            output=fixture_captured_summary_outputs["decorator_output"],
            reactives_shiny=reactives_shiny,
        )

        fixture_captured_summary_outputs["effect_functions"][
            "observer_update_shared_reactives_shiny_summary"
        ]()

        assert isinstance(
            reactives_shiny["Inner_Variables_Shiny"]["Data_Assets_DF"].get(),
            pl.DataFrame,
        )
        assert "Client Partner" in reactives_shiny["Inner_Variables_Shiny"]["Data_Goals_DF"].get().columns
        assert (
            reactives_shiny["Visual_Objects_Shiny"]["Table_Income"].get().as_raw_html()
            == "<table>Income Sources Summary</table>"
        )


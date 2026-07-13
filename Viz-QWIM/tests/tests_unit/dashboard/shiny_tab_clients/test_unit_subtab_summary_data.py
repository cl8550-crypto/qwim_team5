"""Unit tests for private client summary data helpers."""

from __future__ import annotations

from typing import Any

import polars as pl
import pytest

from src.dashboard.shiny_tab_clients import _subtab_summary_data as summary_data
from src.dashboard.shiny_utils import reactives_shiny as reactives_shiny_module
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)
from tests.tests_unit.dashboard.shiny_tab_clients.test_unit_subtab_summary_rendering import (
    _build_reactives_shiny_summary,
)


class _Data_Frame_Fake:
    def __init__(
        self,
        columns: list[str],
        height: int,
    ) -> None:
        self.columns = columns
        self.height = height


def _set_user_input_value(
    reactives_shiny: dict[str, Any],
    key_name: str,
    value_new: Any,
) -> None:
    reactives_shiny["User_Inputs_Shiny"][key_name].set(value_new)


class Class_Test_Subtab_Summary_Data:
    """Tests for the private summary dataframe builders."""

    @pytest.mark.unit()
    def Test_Calc_Table_Summary_Clients_Assets_Includes_Partner_And_Clamps_Negatives(
        self,
    ) -> None:
        reactives_shiny = _build_reactives_shiny_summary(
            include_partner=True,
            include_personal_data=True,
        )

        _set_user_input_value(
            reactives_shiny,
            "Input_Tab_clients_Subtab_clients_Assets_client_Primary_Assets_Taxable",
            -10.0,
        )
        _set_user_input_value(
            reactives_shiny,
            "Input_Tab_clients_Subtab_clients_Assets_client_Partner_Assets_Tax_Free",
            -5.0,
        )

        result = summary_data.calc_table_summary_clients_assets(reactives_shiny = reactives_shiny)

        assert result.columns == [
            "Field Name",
            "Client Primary",
            "Client Partner",
            "Combined Total",
        ]
        assert result["Client Primary"].to_list()[0] == 0.0
        assert result["Client Partner"].to_list()[2] == 0.0
        assert result["Combined Total"].to_list()[-1] == 590000.0

    @pytest.mark.unit()
    def Test_Calc_Table_Summary_Clients_Assets_Returns_Error_Frame_On_Helper_Failure(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            summary_data,
            "get_value_from_reactives_shiny",
            lambda **kwargs: (_ for _ in ()).throw(TypeError("boom")),
        )

        result = summary_data.calc_table_summary_clients_assets(reactives_shiny = {})

        assert result["Field Name"].to_list() == ["Error"]
        assert result["Combined Total"].to_list() == [0.0]

    @pytest.mark.unit()
    def Test_Calc_Table_Summary_Clients_Assets_Builds_Single_Client_Output(
        self,
    ) -> None:
        reactives_shiny = _build_reactives_shiny_summary(
            include_partner=False,
            include_personal_data=True,
        )
        _set_user_input_value(
            reactives_shiny,
            "Input_Tab_clients_Subtab_clients_Assets_client_Partner_Assets_Taxable",
            0.0,
        )
        _set_user_input_value(
            reactives_shiny,
            "Input_Tab_clients_Subtab_clients_Assets_client_Partner_Assets_Tax_Deferred",
            0.0,
        )
        _set_user_input_value(
            reactives_shiny,
            "Input_Tab_clients_Subtab_clients_Assets_client_Partner_Assets_Tax_Free",
            0.0,
        )

        result = summary_data.calc_table_summary_clients_assets(reactives_shiny = reactives_shiny)

        assert result.columns == [
            "Field Name",
            "Client Primary",
            "Combined Total",
        ]
        assert "Client Partner" not in result.columns
        assert result["Combined Total"].to_list()[-1] == 600000.0

    @pytest.mark.unit()
    def Test_Calc_Table_Summary_Clients_Assets_Returns_Error_Frame_When_Frame_Is_Empty(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        reactives_shiny = _build_reactives_shiny_summary(
            include_partner=False,
            include_personal_data=True,
        )
        original_data_frame = summary_data.pl.DataFrame

        def build_data_frame(
            values: dict[str, list[Any]],
        ) -> pl.DataFrame | _Data_Frame_Fake:
            if values.get("Field Name") == ["Error"]:
                return original_data_frame(values)
            return _Data_Frame_Fake(
                ["Field Name", "Client Primary", "Combined Total"],
                0,
            )

        monkeypatch.setattr(
            summary_data.pl,
            "DataFrame",
            build_data_frame,
        )

        result = summary_data.calc_table_summary_clients_assets(reactives_shiny = reactives_shiny)

        assert result["Field Name"].to_list() == ["Error"]
        assert result["Combined Total"].to_list() == [0.0]

    @pytest.mark.unit()
    def Test_Calc_Table_Summary_Clients_Personal_Info_Validation_Failure_Raises(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            reactives_shiny_module,
            "validate_reactives_shiny_structure",
            lambda reactives_shiny: (False, "bad structure"),
        )

        with pytest.raises(Exception_Validation_Input, match="bad structure"):
            summary_data.calc_table_summary_clients_personal_info(reactives_shiny = {})

    @pytest.mark.unit()
    def Test_Calc_Table_Summary_Clients_Personal_Info_Raises_When_User_Inputs_Missing(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            reactives_shiny_module,
            "validate_reactives_shiny_structure",
            lambda reactives_shiny: (True, ""),
        )

        with pytest.raises(KeyError, match="User_Inputs_Shiny"):
            summary_data.calc_table_summary_clients_personal_info(
                reactives_shiny = {"Inner_Variables_Shiny": {}},
            )

    @pytest.mark.unit()
    def Test_Calc_Table_Summary_Clients_Personal_Info_Builds_Partner_Output(
        self,
    ) -> None:
        reactives_shiny = _build_reactives_shiny_summary(
            include_partner=True,
            include_personal_data=True,
        )

        result = summary_data.calc_table_summary_clients_personal_info(reactives_shiny = reactives_shiny)

        assert result.columns == [
            "Field Name",
            "Client Primary",
            "Client Partner",
        ]
        assert result["Client Primary"].to_list()[1] == "65 years"
        assert result["Client Partner"].to_list()[0] == "John Client"

    @pytest.mark.unit()
    def Test_Calc_Table_Summary_Clients_Personal_Info_Builds_Single_Client_Output(
        self,
    ) -> None:
        reactives_shiny = _build_reactives_shiny_summary(
            include_partner=False,
            include_personal_data=True,
        )

        result = summary_data.calc_table_summary_clients_personal_info(reactives_shiny = reactives_shiny)

        assert result.columns == ["Field Name", "Client Primary"]
        assert result["Client Primary"].to_list()[0] == "Jane Client"

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        ("include_partner", "key_name", "column_name", "row_index"),
        [
            pytest.param(
                False,
                "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Age_Current",
                "Client Primary",
                1,
                id="primary_current_age_bool",
            ),
            pytest.param(
                False,
                "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Age_Retirement",
                "Client Primary",
                2,
                id="primary_retirement_age_bool",
            ),
            pytest.param(
                False,
                "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Age_Income_Starting",
                "Client Primary",
                3,
                id="primary_income_start_age_bool",
            ),
            pytest.param(
                True,
                "Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Age_Current",
                "Client Partner",
                1,
                id="partner_current_age_bool",
            ),
            pytest.param(
                True,
                "Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Age_Retirement",
                "Client Partner",
                2,
                id="partner_retirement_age_bool",
            ),
            pytest.param(
                True,
                "Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Age_Income_Starting",
                "Client Partner",
                3,
                id="partner_income_start_age_bool",
            ),
        ],
    )
    def Test_Calc_Table_Summary_Clients_Personal_Info_Treats_Boolean_Ages_As_Not_Specified(
        self,
        include_partner: bool,
        key_name: str,
        column_name: str,
        row_index: int,
    ) -> None:
        reactives_shiny = _build_reactives_shiny_summary(
            include_partner=include_partner,
            include_personal_data=True,
        )
        _set_user_input_value(
            reactives_shiny,
            key_name,
            True,
        )

        result = summary_data.calc_table_summary_clients_personal_info(reactives_shiny = reactives_shiny)

        assert result[column_name].to_list()[row_index] == "Not Specified"

    @pytest.mark.unit()
    def Test_Calc_Table_Summary_Clients_Personal_Info_Raises_When_Frame_Misses_Columns(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        reactives_shiny = _build_reactives_shiny_summary(
            include_partner=False,
            include_personal_data=True,
        )

        monkeypatch.setattr(
            summary_data.pl,
            "DataFrame",
            lambda values: _Data_Frame_Fake(["Field Name"], 1),
        )

        with pytest.raises(Exception_Validation_Input, match="missing expected columns"):
            summary_data.calc_table_summary_clients_personal_info(reactives_shiny = reactives_shiny)

    @pytest.mark.unit()
    def Test_Calc_Table_Summary_Clients_Personal_Info_Raises_When_Frame_Is_Empty(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        reactives_shiny = _build_reactives_shiny_summary(
            include_partner=False,
            include_personal_data=True,
        )

        monkeypatch.setattr(
            summary_data.pl,
            "DataFrame",
            lambda values: _Data_Frame_Fake(
                ["Field Name", "Client Primary"],
                0,
            ),
        )

        with pytest.raises(Exception_Validation_Input, match="Summary table is empty"):
            summary_data.calc_table_summary_clients_personal_info(reactives_shiny = reactives_shiny)

    @pytest.mark.unit()
    @pytest.mark.parametrize("include_partner", [True, False])
    def Test_Calc_Table_Summary_Clients_Goals_Builds_Expected_Frame(
        self,
        include_partner: bool,
    ) -> None:
        reactives_shiny = _build_reactives_shiny_summary(
            include_partner=include_partner,
            include_personal_data=True,
        )
        _set_user_input_value(
            reactives_shiny,
            "Input_Tab_clients_Subtab_clients_Goals_client_Primary_Goal_Essential",
            -1.0,
        )
        _set_user_input_value(
            reactives_shiny,
            "Input_Tab_clients_Subtab_clients_Goals_client_Partner_Goal_Aspirational",
            -2.0,
        )

        result = summary_data.calc_table_summary_clients_goals(reactives_shiny = reactives_shiny)

        assert result["Client Primary"].to_list()[0] == 0.0
        assert result["Combined Total"].to_list()[-1] == 110000.0
        assert ("Client Partner" in result.columns) is include_partner

    @pytest.mark.unit()
    def Test_Calc_Table_Summary_Clients_Goals_Raises_When_Frame_Is_Empty(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        reactives_shiny = _build_reactives_shiny_summary(
            include_partner=False,
            include_personal_data=True,
        )

        monkeypatch.setattr(
            summary_data.pl,
            "DataFrame",
            lambda values: _Data_Frame_Fake(
                ["Field Name", "Client Primary", "Combined Total"],
                0,
            ),
        )

        with pytest.raises(Exception_Validation_Input, match="Failed to create data_Goals_DF"):
            summary_data.calc_table_summary_clients_goals(reactives_shiny = reactives_shiny)

    @pytest.mark.unit()
    def Test_Calc_Table_Summary_Clients_Income_Includes_Partner_And_Clamps_Negatives(
        self,
    ) -> None:
        reactives_shiny = _build_reactives_shiny_summary(
            include_partner=True,
            include_personal_data=True,
        )
        _set_user_input_value(
            reactives_shiny,
            "Input_Tab_clients_Subtab_clients_Income_client_Primary_Income_Pension",
            -1.0,
        )
        _set_user_input_value(
            reactives_shiny,
            "Input_Tab_clients_Subtab_clients_Income_client_Partner_Income_Other",
            -1.0,
        )

        result = summary_data.calc_table_summary_clients_income(reactives_shiny = reactives_shiny)

        assert result.columns == [
            "Field Name",
            "Client Primary",
            "Client Partner",
            "Combined Total",
        ]
        assert result["Client Primary"].to_list()[1] == 0.0
        assert result["Client Partner"].to_list()[3] == 0.0
        assert result["Combined Total"].to_list()[-1] == 84000.0

    @pytest.mark.unit()
    def Test_Calc_Table_Summary_Clients_Income_Returns_Error_Frame_On_Helper_Failure(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            summary_data,
            "get_value_from_reactives_shiny",
            lambda **kwargs: (_ for _ in ()).throw(TypeError("boom")),
        )

        result = summary_data.calc_table_summary_clients_income(reactives_shiny = {})

        assert result["Field Name"].to_list() == ["Error"]
        assert result["Combined Total"].to_list() == [0.0]

    @pytest.mark.unit()
    def Test_Calc_Table_Summary_Clients_Income_Returns_Error_Frame_When_Frame_Is_Empty(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        reactives_shiny = _build_reactives_shiny_summary(
            include_partner=False,
            include_personal_data=True,
        )
        original_data_frame = summary_data.pl.DataFrame

        def build_data_frame(
            values: dict[str, list[Any]],
        ) -> pl.DataFrame | _Data_Frame_Fake:
            if values.get("Field Name") == ["Error"]:
                return original_data_frame(values)
            return _Data_Frame_Fake(
                ["Field Name", "Client Primary", "Combined Total"],
                0,
            )

        monkeypatch.setattr(
            summary_data.pl,
            "DataFrame",
            build_data_frame,
        )

        result = summary_data.calc_table_summary_clients_income(reactives_shiny = reactives_shiny)

        assert result["Field Name"].to_list() == ["Error"]
        assert result["Combined Total"].to_list() == [0.0]
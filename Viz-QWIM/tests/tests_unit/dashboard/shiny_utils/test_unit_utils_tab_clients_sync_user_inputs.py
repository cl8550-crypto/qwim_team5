"""Unit tests for sync_user_inputs_shiny_from_extracted_worksheet.

These tests verify the critical runtime fix where
``sync_user_inputs_shiny_from_extracted_worksheet`` now directly updates
``User_Inputs_Shiny`` reactive values so that the Summary subtab and
other downstream consumers see the imported values immediately — even
when the target subtab is hidden and ``ui.update_*`` calls are lost.

File: tests/tests_unit/dashboard/shiny_utils/test_unit_utils_tab_clients_sync_user_inputs.py
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Test: _build_input_id_to_reactive_key_map
# ---------------------------------------------------------------------------


@pytest.mark.unit()
class Test_Build_Input_Id_To_Reactive_Key_Map:
    """Tests for the reverse-lookup helper."""

    @pytest.mark.unit()
    def test_empty_user_inputs_returns_empty_map(self):
        """Empty user_inputs dict yields empty reverse map."""
        from src.dashboard.shiny_utils._utils_tab_clients_sync import (
            _build_input_id_to_reactive_key_map,
        )

        result = _build_input_id_to_reactive_key_map(user_inputs={})

        assert result == {}

    @pytest.mark.unit()
    def test_single_reactive_key_is_inverted_correctly(self):
        """A single reactive key is correctly converted to its input_id form."""
        from src.dashboard.shiny_utils._utils_tab_clients_sync import (
            _build_input_id_to_reactive_key_map,
        )

        user_inputs = {
            "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Name": MagicMock(),
        }

        result = _build_input_id_to_reactive_key_map(user_inputs=user_inputs)

        assert (
            result[
                "input_ID_tab_clients_subtab_clients_personal_info_client_primary_name"
            ]
            == "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Name"
        )

    @pytest.mark.unit()
    def test_multiple_reactive_keys_are_all_inverted(self):
        """All Input_Tab_ keys are inverted; non-matching keys are skipped."""
        from src.dashboard.shiny_utils._utils_tab_clients_sync import (
            _build_input_id_to_reactive_key_map,
        )

        user_inputs = {
            "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Age_Current": MagicMock(),
            "Input_Tab_clients_Subtab_clients_Assets_client_Primary_Assets_Taxable": MagicMock(),
            "Not_A_Reactive_Key": MagicMock(),
        }

        result = _build_input_id_to_reactive_key_map(user_inputs=user_inputs)

        assert len(result) == 2
        assert (
            "input_ID_tab_clients_subtab_clients_personal_info_client_primary_age_current"
            in result
        )
        assert (
            "input_ID_tab_clients_subtab_clients_assets_client_primary_assets_taxable"
            in result
        )


# ---------------------------------------------------------------------------
# Test: _update_user_inputs_shiny_from_mapped_values
# ---------------------------------------------------------------------------


@pytest.mark.unit()
class Test_Update_User_Inputs_Shiny_From_Mapped_Values:
    """Tests for the helper that writes mapped values into User_Inputs_Shiny."""

    @pytest.mark.unit()
    def test_none_reactives_shiny_returns_early(self):
        """None reactives_shiny is handled without crash."""
        from src.dashboard.shiny_utils._utils_tab_clients_sync import (
            _update_user_inputs_shiny_from_mapped_values,
        )

        # Should not raise
        _update_user_inputs_shiny_from_mapped_values(
            reactives_shiny=None,  # type: ignore[arg-type]
            mapped_values={"foo": "bar"},
        )

    @pytest.mark.unit()
    def test_missing_user_inputs_category_returns_early(self):
        """Missing User_Inputs_Shiny category is handled without crash."""
        from src.dashboard.shiny_utils._utils_tab_clients_sync import (
            _update_user_inputs_shiny_from_mapped_values,
        )

        reactives_shiny: dict[str, Any] = {}  # no User_Inputs_Shiny

        # Should not raise
        _update_user_inputs_shiny_from_mapped_values(
            reactives_shiny=reactives_shiny,
            mapped_values={"foo": "bar"},
        )

    @pytest.mark.unit()
    def test_mapped_value_calls_set_on_reactive(self):
        """A mapped value writes to the corresponding reactive via .set()."""
        from src.dashboard.shiny_utils._utils_tab_clients_sync import (
            _update_user_inputs_shiny_from_mapped_values,
        )

        mock_rv = MagicMock()
        user_inputs = {
            "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Name": mock_rv,
        }
        reactives_shiny: dict[str, Any] = {"User_Inputs_Shiny": user_inputs}

        _update_user_inputs_shiny_from_mapped_values(
            reactives_shiny=reactives_shiny,
            mapped_values={
                "input_ID_tab_clients_subtab_clients_personal_info_client_primary_name": "Alice",
            },
        )

        mock_rv.set.assert_called_once_with("Alice")

    @pytest.mark.unit()
    def test_unmatched_input_id_is_skipped(self):
        """Input IDs not in the reverse map are silently skipped."""
        from src.dashboard.shiny_utils._utils_tab_clients_sync import (
            _update_user_inputs_shiny_from_mapped_values,
        )

        mock_rv = MagicMock()
        user_inputs = {
            "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Name": mock_rv,
        }
        reactives_shiny: dict[str, Any] = {"User_Inputs_Shiny": user_inputs}

        _update_user_inputs_shiny_from_mapped_values(
            reactives_shiny=reactives_shiny,
            mapped_values={
                "input_ID_tab_clients_subtab_clients_personal_info_client_primary_name": "Alice",
                "input_ID_tab_clients_subtab_unknown_field": "ignored",
            },
        )

        mock_rv.set.assert_called_once_with("Alice")

    @pytest.mark.unit()
    def test_non_reactive_value_is_skipped(self):
        """Reactive values that lack .set() are skipped without crash."""
        from src.dashboard.shiny_utils._utils_tab_clients_sync import (
            _update_user_inputs_shiny_from_mapped_values,
        )

        # Plain dict has no .set() method
        user_inputs = {
            "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Name": {},
        }
        reactives_shiny: dict[str, Any] = {"User_Inputs_Shiny": user_inputs}

        # Should not raise
        _update_user_inputs_shiny_from_mapped_values(
            reactives_shiny=reactives_shiny,
            mapped_values={
                "input_ID_tab_clients_subtab_clients_personal_info_client_primary_name": "Alice",
            },
        )


# ---------------------------------------------------------------------------
# Test: sync_user_inputs_shiny_from_extracted_worksheet — full flow
# ---------------------------------------------------------------------------


@pytest.mark.unit()
class Test_Sync_User_Inputs_Shiny_Full_Flow:
    """End-to-end tests for the full sync function."""

    @pytest.mark.unit()
    def test_personal_info_section_updates_user_inputs_shiny(self):
        """A Personal_Info section updates the corresponding User_Inputs_Shiny keys."""
        from src.dashboard.shiny_utils.utils_tab_clients import (
            sync_user_inputs_shiny_from_extracted_worksheet,
        )

        mock_rv_name = MagicMock()
        mock_rv_age = MagicMock()
        user_inputs = {
            "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Name": mock_rv_name,
            "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Age_Current": mock_rv_age,
        }

        extracted_data = {
            "Personal_Info": {
                "client_primary": {
                    "name": "Alice",
                    "age_current": 55,
                },
            },
        }

        reactives_shiny: dict[str, Any] = {
            "User_Inputs_Shiny": user_inputs,
            "Inner_Variables_Shiny": {
                "Extracted_Worksheet_Data": MagicMock(),
            },
        }

        sync_user_inputs_shiny_from_extracted_worksheet(
            reactives_shiny=reactives_shiny,
            extracted_worksheet_data=extracted_data,
            has_client_partner=False,
        )

        # Verify .set() was called with the mapped values
        mock_rv_name.set.assert_called_with("Alice")
        # age_current maps to int via _coerce_numeric_or_none
        mock_rv_age.set.assert_called_with(55)

    @pytest.mark.unit()
    def test_assets_section_updates_user_inputs_shiny(self):
        """An Assets section updates the corresponding User_Inputs_Shiny keys."""
        from src.dashboard.shiny_utils.utils_tab_clients import (
            sync_user_inputs_shiny_from_extracted_worksheet,
        )

        mock_rv_taxable = MagicMock()
        user_inputs = {
            "Input_Tab_clients_Subtab_clients_Assets_client_Primary_Assets_Taxable": mock_rv_taxable,
        }

        extracted_data = {
            "Assets": {
                "client_primary": {
                    "assets_taxable": 100000,
                },
            },
        }

        reactives_shiny: dict[str, Any] = {
            "User_Inputs_Shiny": user_inputs,
            "Inner_Variables_Shiny": {
                "Extracted_Worksheet_Data": MagicMock(),
            },
        }

        sync_user_inputs_shiny_from_extracted_worksheet(
            reactives_shiny=reactives_shiny,
            extracted_worksheet_data=extracted_data,
            has_client_partner=False,
        )

        # Currency is stored as raw integer for downstream numeric consumers
        mock_rv_taxable.set.assert_called_with(100000)

    @pytest.mark.unit()
    def test_all_four_sections_are_synced(self):
        """All four sections (Personal_Info, Assets, Goals, Income) are synced in one call."""
        from src.dashboard.shiny_utils.utils_tab_clients import (
            sync_user_inputs_shiny_from_extracted_worksheet,
        )

        mock_rv_personal = MagicMock()
        mock_rv_assets = MagicMock()
        mock_rv_goals = MagicMock()
        mock_rv_income = MagicMock()

        user_inputs = {
            "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Name": mock_rv_personal,
            "Input_Tab_clients_Subtab_clients_Assets_client_Primary_Assets_Taxable": mock_rv_assets,
            "Input_Tab_clients_Subtab_clients_Goals_client_Primary_Goal_Essential": mock_rv_goals,
            "Input_Tab_clients_Subtab_clients_Income_client_Primary_Income_Social_Security": mock_rv_income,
        }

        extracted_data = {
            "Personal_Info": {"client_primary": {"name": "Bob"}},
            "Assets": {"client_primary": {"assets_taxable": 50000}},
            "Goals": {"client_primary": {"goal_essential": 40000}},
            "Income": {"client_primary": {"income_social_security": 20000}},
        }

        reactives_shiny: dict[str, Any] = {
            "User_Inputs_Shiny": user_inputs,
            "Inner_Variables_Shiny": {
                "Extracted_Worksheet_Data": MagicMock(),
            },
        }

        sync_user_inputs_shiny_from_extracted_worksheet(
            reactives_shiny=reactives_shiny,
            extracted_worksheet_data=extracted_data,
            has_client_partner=False,
        )

        mock_rv_personal.set.assert_called_with("Bob")
        mock_rv_assets.set.assert_called_with(50000)
        mock_rv_goals.set.assert_called_with(40000)
        mock_rv_income.set.assert_called_with(20000)

    @pytest.mark.unit()
    def test_inner_variables_extracted_data_is_stored_first(self):
        """The Extracted_Worksheet_Data reactive in Inner_Variables_Shiny is set before User_Inputs_Shiny."""
        from src.dashboard.shiny_utils.utils_tab_clients import (
            sync_user_inputs_shiny_from_extracted_worksheet,
        )

        mock_rv_inner = MagicMock()
        mock_rv_user = MagicMock()
        user_inputs = {
            "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Name": mock_rv_user,
        }

        extracted_data = {
            "Personal_Info": {"client_primary": {"name": "Carol"}},
        }

        reactives_shiny: dict[str, Any] = {
            "User_Inputs_Shiny": user_inputs,
            "Inner_Variables_Shiny": {
                "Extracted_Worksheet_Data": mock_rv_inner,
            },
        }

        sync_user_inputs_shiny_from_extracted_worksheet(
            reactives_shiny=reactives_shiny,
            extracted_worksheet_data=extracted_data,
            has_client_partner=False,
        )

        # Inner_Variables_Shiny["Extracted_Worksheet_Data"] was set
        mock_rv_inner.set.assert_called_once()
        # User_Inputs_Shiny was also set
        mock_rv_user.set.assert_called_with("Carol")

    @pytest.mark.unit()
    def test_empty_extracted_data_does_not_crash(self):
        """Empty extracted data is handled gracefully."""
        from src.dashboard.shiny_utils.utils_tab_clients import (
            sync_user_inputs_shiny_from_extracted_worksheet,
        )

        reactives_shiny: dict[str, Any] = {
            "User_Inputs_Shiny": {},
            "Inner_Variables_Shiny": {
                "Extracted_Worksheet_Data": MagicMock(),
            },
        }

        # Should not raise
        sync_user_inputs_shiny_from_extracted_worksheet(
            reactives_shiny=reactives_shiny,
            extracted_worksheet_data={},
            has_client_partner=False,
        )


# ---------------------------------------------------------------------------
# Test: sync_advisor_info_to_user_inputs_shiny_QWIM
# ---------------------------------------------------------------------------


@pytest.mark.unit()
class Test_Sync_Advisor_Info_To_User_Inputs_Shiny_QWIM:
    """Tests for the new advisor-section sync helper.

    Notes
    -----
    The helper is called from the Outline subtab server *after*
    :func:`sync_user_inputs_shiny_from_extracted_worksheet` to push the
    flat ``Advisor_Info`` section (name, firm, email, etc.) to the
    Setup > Advisor subtab's ``User_Inputs_Shiny`` reactives.  It
    returns the list of advisor fields for which the parser applied
    the default value (because the PDF omitted them) so the
    always-visible status banner can surface the firm default to the
    user.
    """

    @pytest.mark.unit()
    def test_adv_firm_default_flows_to_user_input_reactive(self) -> None:
        """The firm default 'QWIM AI Wealth Management' flows to the Advisor reactive."""
        from src.dashboard.shiny_utils._utils_tab_clients_sync import (
            sync_advisor_info_to_user_inputs_shiny_QWIM,
        )
        from src.dashboard.shiny_utils.reactives_initialization import (
            create_reactive_value_safely,
        )

        rv_firm = create_reactive_value_safely(initial_value="")
        reactives_shiny = {
            "User_Inputs_Shiny": {
                "Input_Tab_Setup_Subtab_advisor_info_firm": rv_firm,
            },
            "Inner_Variables_Shiny": {},
        }
        extracted = {
            "Advisor_Info": {
                # The parser pre-fills defaults when fields are empty.
                "firm": "QWIM AI Wealth Management",
            },
        }

        defaulted = sync_advisor_info_to_user_inputs_shiny_QWIM(
            reactives_shiny=reactives_shiny,
            extracted_worksheet_data=extracted,
        )

        assert rv_firm._value == "QWIM AI Wealth Management"
        assert "firm" in defaulted

    @pytest.mark.unit()
    def test_adv_pdfs_firm_value_overrides_default(self) -> None:
        """A non-empty firm value from the PDF overrides the default."""
        from src.dashboard.shiny_utils._utils_tab_clients_sync import (
            sync_advisor_info_to_user_inputs_shiny_QWIM,
        )
        from src.dashboard.shiny_utils.reactives_initialization import (
            create_reactive_value_safely,
        )

        rv_firm = create_reactive_value_safely(initial_value="")
        reactives_shiny = {
            "User_Inputs_Shiny": {
                "Input_Tab_Setup_Subtab_advisor_info_firm": rv_firm,
            },
            "Inner_Variables_Shiny": {},
        }
        extracted = {
            "Advisor_Info": {
                "firm": "Custom Wealth LLC",
            },
        }

        sync_advisor_info_to_user_inputs_shiny_QWIM(
            reactives_shiny=reactives_shiny,
            extracted_worksheet_data=extracted,
        )

        assert rv_firm._value == "Custom Wealth LLC"

    @pytest.mark.unit()
    def test_adv_returns_empty_list_when_advisor_section_missing(self) -> None:
        """Empty/missing Advisor_Info section returns an empty defaulted list."""
        from src.dashboard.shiny_utils._utils_tab_clients_sync import (
            sync_advisor_info_to_user_inputs_shiny_QWIM,
        )

        reactives_shiny = {
            "User_Inputs_Shiny": {},
            "Inner_Variables_Shiny": {},
        }
        defaulted = sync_advisor_info_to_user_inputs_shiny_QWIM(
            reactives_shiny=reactives_shiny,
            extracted_worksheet_data={},
        )
        assert defaulted == []

    @pytest.mark.unit()
    def test_adv_returns_empty_list_for_non_dict_extracted(self) -> None:
        """A non-dict extracted_worksheet_data returns an empty defaulted list (no raise)."""
        from src.dashboard.shiny_utils._utils_tab_clients_sync import (
            sync_advisor_info_to_user_inputs_shiny_QWIM,
        )

        reactives_shiny = {
            "User_Inputs_Shiny": {},
            "Inner_Variables_Shiny": {},
        }
        defaulted = sync_advisor_info_to_user_inputs_shiny_QWIM(
            reactives_shiny=reactives_shiny,
            extracted_worksheet_data="not_a_dict",  # type: ignore[arg-type]
        )
        assert defaulted == []

    @pytest.mark.unit()
    def test_adv_returns_empty_list_for_non_dict_reactives_shiny(self) -> None:
        """A non-dict reactives_shiny returns an empty defaulted list (no raise)."""
        from src.dashboard.shiny_utils._utils_tab_clients_sync import (
            sync_advisor_info_to_user_inputs_shiny_QWIM,
        )

        defaulted = sync_advisor_info_to_user_inputs_shiny_QWIM(
            reactives_shiny="not_a_dict",  # type: ignore[arg-type]
            extracted_worksheet_data={"Advisor_Info": {}},
        )
        assert defaulted == []

    @pytest.mark.unit()
    def test_adv_detects_all_defaulted_fields(self) -> None:
        """All advisor fields with non-empty values equal to the default are flagged."""
        from src.dashboard.shiny_utils._utils_tab_clients_sync import (
            sync_advisor_info_to_user_inputs_shiny_QWIM,
        )
        from src.clients_QWIM.utils_client import _ADVISOR_INFO_DEFAULT_VALUES

        # Provide a payload where every advisor field matches its
        # default (the parser pre-fills defaults, so this simulates a
        # PDF that omitted all advisor fields).
        advisor_section = dict(_ADVISOR_INFO_DEFAULT_VALUES)
        reactives_shiny = {
            "User_Inputs_Shiny": {},
            "Inner_Variables_Shiny": {},
        }
        defaulted = sync_advisor_info_to_user_inputs_shiny_QWIM(
            reactives_shiny=reactives_shiny,
            extracted_worksheet_data={"Advisor_Info": advisor_section},
        )
        # Every field in the default dict should be flagged.
        assert set(defaulted) == set(_ADVISOR_INFO_DEFAULT_VALUES.keys())

    @pytest.mark.unit()
    def test_adv_updates_all_advisor_reactives(self) -> None:
        """The helper updates all eight advisor reactives (name, title, etc.)."""
        from src.dashboard.shiny_utils._utils_tab_clients_sync import (
            sync_advisor_info_to_user_inputs_shiny_QWIM,
        )
        from src.dashboard.shiny_utils.reactives_initialization import (
            create_reactive_value_safely,
        )

        reactives_user_inputs: dict[str, Any] = {}
        for field_key in (
            "name", "title", "credentials", "team", "firm",
            "email", "phone_number", "address",
        ):
            reactives_user_inputs[f"Input_Tab_Setup_Subtab_advisor_info_{field_key}"] = (
                create_reactive_value_safely(initial_value="")
            )
        reactives_shiny = {
            "User_Inputs_Shiny": reactives_user_inputs,
            "Inner_Variables_Shiny": {},
        }
        extracted = {
            "Advisor_Info": {
                "name": "John Advisor",
                "firm": "QWIM AI Wealth Management",
                "email": "john@qwim.test",
            },
        }
        sync_advisor_info_to_user_inputs_shiny_QWIM(
            reactives_shiny=reactives_shiny,
            extracted_worksheet_data=extracted,
        )
        # Only firm, name, and email should have non-default values.
        assert reactives_user_inputs[
            "Input_Tab_Setup_Subtab_advisor_info_name"
        ]._value == "John Advisor"
        assert reactives_user_inputs[
            "Input_Tab_Setup_Subtab_advisor_info_firm"
        ]._value == "QWIM AI Wealth Management"
        assert reactives_user_inputs[
            "Input_Tab_Setup_Subtab_advisor_info_email"
        ]._value == "john@qwim.test"
        # Missing fields are blanked.
        assert reactives_user_inputs[
            "Input_Tab_Setup_Subtab_advisor_info_title"
        ]._value == ""

    @pytest.mark.unit()
    def test_adv_tolerates_non_dict_advisor_section(self) -> None:
        """A non-dict Advisor_Info value is tolerated (no raise, empty result)."""
        from src.dashboard.shiny_utils._utils_tab_clients_sync import (
            sync_advisor_info_to_user_inputs_shiny_QWIM,
        )

        reactives_shiny = {
            "User_Inputs_Shiny": {},
            "Inner_Variables_Shiny": {},
        }
        defaulted = sync_advisor_info_to_user_inputs_shiny_QWIM(
            reactives_shiny=reactives_shiny,
            extracted_worksheet_data={"Advisor_Info": "not_a_dict"},
        )
        assert defaulted == []


@pytest.mark.unit()
class Test_Sync_Advisor_Info_Defaulted_Fields_Edge_Cases:
    """Edge-case tests for the defaulted-fields detection logic."""

    @pytest.mark.unit()
    def test_adv_none_values_are_flagged_as_defaulted(self) -> None:
        """Advisor fields with ``None`` values are flagged as defaulted."""
        from src.dashboard.shiny_utils._utils_tab_clients_sync import (
            sync_advisor_info_to_user_inputs_shiny_QWIM,
        )

        reactives_shiny = {
            "User_Inputs_Shiny": {},
            "Inner_Variables_Shiny": {},
        }
        extracted = {
            "Advisor_Info": {
                "firm": None,
                "name": "Some Name",
            },
        }
        defaulted = sync_advisor_info_to_user_inputs_shiny_QWIM(
            reactives_shiny=reactives_shiny,
            extracted_worksheet_data=extracted,
        )
        assert "firm" in defaulted
        assert "name" not in defaulted

    @pytest.mark.unit()
    def test_adv_empty_string_firm_value_is_flagged_as_defaulted(self) -> None:
        """An empty-string ``firm`` value (the only field with a default) is flagged as defaulted."""
        from src.dashboard.shiny_utils._utils_tab_clients_sync import (
            sync_advisor_info_to_user_inputs_shiny_QWIM,
        )

        reactives_shiny = {
            "User_Inputs_Shiny": {},
            "Inner_Variables_Shiny": {},
        }
        extracted = {
            "Advisor_Info": {
                "firm": "",
            },
        }
        defaulted = sync_advisor_info_to_user_inputs_shiny_QWIM(
            reactives_shiny=reactives_shiny,
            extracted_worksheet_data=extracted,
        )
        assert "firm" in defaulted

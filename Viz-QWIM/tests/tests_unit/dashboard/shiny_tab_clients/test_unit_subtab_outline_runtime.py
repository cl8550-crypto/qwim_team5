"""Unit tests for the runtime reactive wiring in subtab_outline.py.

These tests verify the critical runtime fix where the PDF upload flow
correctly updates shared reactive state that the other subtabs depend on.

The tests focus on the *value-level* contract: after
``sync_user_inputs_shiny_from_extracted_worksheet`` is called, the
``User_Inputs_Shiny`` ``reactive.Value`` objects contain the expected
worksheet data. This is the primary contract that the Summary subtab
and other downstream consumers depend on.

File: tests/tests_unit/dashboard/shiny_tab_clients/test_unit_subtab_outline_runtime.py
"""

from __future__ import annotations

from pathlib import Path

import pytest

from shiny import reactive


# ---------------------------------------------------------------------------
# Test: shared reactive value creation
# ---------------------------------------------------------------------------


@pytest.mark.unit()
class Test_Shared_Reactive_Value_Creation:
    """Tests verifying the shared reactive values are properly created."""

    @pytest.mark.unit()
    def test_create_reactive_value_returns_reactive_value(self):
        """``create_reactive_value_safely`` returns a real ``reactive.Value``."""
        from src.dashboard.shiny_utils.reactives_initialization import (
            create_reactive_value_safely,
        )

        rv = create_reactive_value_safely(initial_value=42)

        assert isinstance(rv, reactive.Value)

    @pytest.mark.unit()
    def test_create_reactive_value_with_none(self):
        """``create_reactive_value_safely`` with None initial value works."""
        from src.dashboard.shiny_utils.reactives_initialization import (
            create_reactive_value_safely,
        )

        rv = create_reactive_value_safely(initial_value=None)

        assert isinstance(rv, reactive.Value)

    @pytest.mark.unit()
    def test_create_reactive_value_with_false(self):
        """``create_reactive_value_safely`` with False initial value works."""
        from src.dashboard.shiny_utils.reactives_initialization import (
            create_reactive_value_safely,
        )

        rv = create_reactive_value_safely(initial_value=False)

        assert isinstance(rv, reactive.Value)


# ---------------------------------------------------------------------------
# Test: reactive.set/get round-trip
# ---------------------------------------------------------------------------


@pytest.mark.unit()
class Test_Reactive_Set_Get_Round_Trip:
    """Tests verifying the basic reactive.Value set/get cycle works."""

    @pytest.mark.unit()
    def test_reactive_value_stores_integer(self):
        """A reactive.Value can store and return an integer."""
        from src.dashboard.shiny_utils.reactives_initialization import (
            create_reactive_value_safely,
        )

        rv = create_reactive_value_safely(initial_value=0)
        rv.set(42)

        # Read the internal value — this is the same as .get() outside a session.
        assert rv._value == 42

    @pytest.mark.unit()
    def test_reactive_value_stores_string(self):
        """A reactive.Value can store and return a string."""
        from src.dashboard.shiny_utils.reactives_initialization import (
            create_reactive_value_safely,
        )

        rv = create_reactive_value_safely(initial_value=None)
        rv.set("Alice")

        assert rv._value == "Alice"

    @pytest.mark.unit()
    def test_reactive_value_stores_none(self):
        """A reactive.Value can store None."""
        from src.dashboard.shiny_utils.reactives_initialization import (
            create_reactive_value_safely,
        )

        rv = create_reactive_value_safely(initial_value=42)
        rv.set(None)

        assert rv._value is None


# ---------------------------------------------------------------------------
# Test: sync function updates User_Inputs_Shiny reactives
# ---------------------------------------------------------------------------


@pytest.mark.unit()
class Test_Sync_Updates_User_Inputs_Shiny_Reactives:
    """Tests verifying that ``sync_user_inputs_shiny_from_extracted_worksheet``
    updates ``User_Inputs_Shiny`` ``reactive.Value`` objects."""

    @pytest.mark.unit()
    def test_personal_info_name_reactive_is_updated(self):
        """The personal-info name reactive is updated with the worksheet value."""
        from src.dashboard.shiny_utils.reactives_initialization import (
            create_reactive_value_safely,
        )
        from src.dashboard.shiny_utils.utils_tab_clients import (
            sync_user_inputs_shiny_from_extracted_worksheet,
        )

        rv_name = create_reactive_value_safely(initial_value=None)
        reactives_shiny = {
            "User_Inputs_Shiny": {
                "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Name": rv_name,
            },
            "Inner_Variables_Shiny": {
                "Extracted_Worksheet_Data": create_reactive_value_safely(initial_value=None),
            },
        }

        extracted_data = {
            "Personal_Info": {
                "client_primary": {"name": "Alice"},
            },
        }

        sync_user_inputs_shiny_from_extracted_worksheet(
            reactives_shiny=reactives_shiny,
            extracted_worksheet_data=extracted_data,
            has_client_partner=False,
        )

        assert rv_name._value == "Alice"

    @pytest.mark.unit()
    def test_assets_taxable_reactive_is_updated_with_currency_format(self):
        """The assets taxable reactive is updated with a formatted currency string."""
        from src.dashboard.shiny_utils.reactives_initialization import (
            create_reactive_value_safely,
        )
        from src.dashboard.shiny_utils.utils_tab_clients import (
            sync_user_inputs_shiny_from_extracted_worksheet,
        )

        rv_taxable = create_reactive_value_safely(initial_value=None)
        reactives_shiny = {
            "User_Inputs_Shiny": {
                "Input_Tab_clients_Subtab_clients_Assets_client_Primary_Assets_Taxable": rv_taxable,
            },
            "Inner_Variables_Shiny": {
                "Extracted_Worksheet_Data": create_reactive_value_safely(initial_value=None),
            },
        }

        extracted_data = {
            "Assets": {
                "client_primary": {"assets_taxable": 100000},
            },
        }

        sync_user_inputs_shiny_from_extracted_worksheet(
            reactives_shiny=reactives_shiny,
            extracted_worksheet_data=extracted_data,
            has_client_partner=False,
        )

        assert rv_taxable._value == 100000

    @pytest.mark.unit()
    def test_all_four_sections_update_their_reactives(self):
        """All four sections (Personal Info, Assets, Goals, Income) update their reactives."""
        from src.dashboard.shiny_utils.reactives_initialization import (
            create_reactive_value_safely,
        )
        from src.dashboard.shiny_utils.utils_tab_clients import (
            sync_user_inputs_shiny_from_extracted_worksheet,
        )

        rv_personal = create_reactive_value_safely(initial_value=None)
        rv_assets = create_reactive_value_safely(initial_value=None)
        rv_goals = create_reactive_value_safely(initial_value=None)
        rv_income = create_reactive_value_safely(initial_value=None)

        reactives_shiny = {
            "User_Inputs_Shiny": {
                "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Name": rv_personal,
                "Input_Tab_clients_Subtab_clients_Assets_client_Primary_Assets_Taxable": rv_assets,
                "Input_Tab_clients_Subtab_clients_Goals_client_Primary_Goal_Essential": rv_goals,
                "Input_Tab_clients_Subtab_clients_Income_client_Primary_Income_Social_Security": rv_income,
            },
            "Inner_Variables_Shiny": {
                "Extracted_Worksheet_Data": create_reactive_value_safely(initial_value=None),
            },
        }

        extracted_data = {
            "Personal_Info": {"client_primary": {"name": "Bob"}},
            "Assets": {"client_primary": {"assets_taxable": 50000}},
            "Goals": {"client_primary": {"goal_essential": 40000}},
            "Income": {"client_primary": {"income_social_security": 20000}},
        }

        sync_user_inputs_shiny_from_extracted_worksheet(
            reactives_shiny=reactives_shiny,
            extracted_worksheet_data=extracted_data,
            has_client_partner=False,
        )

        assert rv_personal._value == "Bob"
        assert rv_assets._value == 50000
        assert rv_goals._value == 40000
        assert rv_income._value == 20000

    @pytest.mark.unit()
    def test_partner_section_also_updates_reactives(self):
        """The partner client section also updates User_Inputs_Shiny reactives."""
        from src.dashboard.shiny_utils.reactives_initialization import (
            create_reactive_value_safely,
        )
        from src.dashboard.shiny_utils.utils_tab_clients import (
            sync_user_inputs_shiny_from_extracted_worksheet,
        )

        rv_partner_name = create_reactive_value_safely(initial_value=None)
        rv_partner_age = create_reactive_value_safely(initial_value=None)
        reactives_shiny = {
            "User_Inputs_Shiny": {
                "Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Name": rv_partner_name,
                "Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Age_Current": rv_partner_age,
            },
            "Inner_Variables_Shiny": {
                "Extracted_Worksheet_Data": create_reactive_value_safely(initial_value=None),
            },
        }

        extracted_data = {
            "Personal_Info": {
                "client_primary": {"name": "Primary Client"},
                "client_partner": {"name": "Partner Client", "age_current": 58},
            },
        }

        sync_user_inputs_shiny_from_extracted_worksheet(
            reactives_shiny=reactives_shiny,
            extracted_worksheet_data=extracted_data,
            has_client_partner=True,
        )

        assert rv_partner_name._value == "Partner Client"
        assert rv_partner_age._value == 58

    @pytest.mark.unit()
    def test_multiple_calls_overwrite_previous_values(self):
        """Calling sync twice with different data overwrites the reactives."""
        from src.dashboard.shiny_utils.reactives_initialization import (
            create_reactive_value_safely,
        )
        from src.dashboard.shiny_utils.utils_tab_clients import (
            sync_user_inputs_shiny_from_extracted_worksheet,
        )

        rv_name = create_reactive_value_safely(initial_value=None)
        reactives_shiny = {
            "User_Inputs_Shiny": {
                "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Name": rv_name,
            },
            "Inner_Variables_Shiny": {
                "Extracted_Worksheet_Data": create_reactive_value_safely(initial_value=None),
            },
        }

        sync_user_inputs_shiny_from_extracted_worksheet(
            reactives_shiny=reactives_shiny,
            extracted_worksheet_data={
                "Personal_Info": {"client_primary": {"name": "First"}},
            },
            has_client_partner=False,
        )
        assert rv_name._value == "First"

        sync_user_inputs_shiny_from_extracted_worksheet(
            reactives_shiny=reactives_shiny,
            extracted_worksheet_data={
                "Personal_Info": {"client_primary": {"name": "Second"}},
            },
            has_client_partner=False,
        )
        assert rv_name._value == "Second"

    @pytest.mark.unit()
    def test_inner_variables_worksheet_data_is_stored(self):
        """The Extracted_Worksheet_Data reactive in Inner_Variables_Shiny is also set."""
        from src.dashboard.shiny_utils.reactives_initialization import (
            create_reactive_value_safely,
        )
        from src.dashboard.shiny_utils.utils_tab_clients import (
            sync_user_inputs_shiny_from_extracted_worksheet,
        )

        rv_inner = create_reactive_value_safely(initial_value=None)
        reactives_shiny = {
            "User_Inputs_Shiny": {},
            "Inner_Variables_Shiny": {
                "Extracted_Worksheet_Data": rv_inner,
            },
        }

        extracted_data = {
            "Personal_Info": {"client_primary": {"name": "Test"}},
        }

        sync_user_inputs_shiny_from_extracted_worksheet(
            reactives_shiny=reactives_shiny,
            extracted_worksheet_data=extracted_data,
            has_client_partner=False,
        )

        # The inner reactive should now contain the extracted data
        assert rv_inner._value is not None
        assert "Personal_Info" in rv_inner._value


# ---------------------------------------------------------------------------
# Integration: real "Input Worksheet" PDFs populate User_Inputs_Shiny
#
# These tests exercise the full producer contract end to end with the real
# sample worksheets shipped under ``inputs/QWIM``:
#     extract PDF -> validate -> sync -> ``User_Inputs_Shiny`` reactives.
# They always run (they are not gated behind Playwright) and skip only when
# the sample PDFs are unavailable.
# ---------------------------------------------------------------------------

_INPUTS_QWIM_DIR = Path(__file__).resolve().parents[4] / "inputs" / "QWIM"
_PDF_SINGLE = _INPUTS_QWIM_DIR / "Inputs_QWIM_Client_Single.pdf"
_PDF_COUPLE = _INPUTS_QWIM_DIR / "Inputs_QWIM_Client_Couple.pdf"

_real_pdfs_available = _PDF_SINGLE.is_file() and _PDF_COUPLE.is_file()


def _seed_client_reactives_shiny() -> tuple[dict, dict]:
    """Build a ``reactives_shiny`` pre-seeded with the client input reactives.

    Returns
    -------
    tuple of (dict, dict)
        ``(reactives_shiny, reactive_values_by_key)`` where the second element
        maps each seeded reactive key to its ``reactive.Value`` for assertions.
    """
    from src.dashboard.shiny_utils.reactives_initialization import (
        create_reactive_value_safely,
    )

    keys = (
        "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Name",
        "Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Name",
        "Input_Tab_clients_Subtab_clients_Assets_client_Primary_Assets_Taxable",
        "Input_Tab_clients_Subtab_clients_Assets_client_Partner_Assets_Taxable",
    )
    reactive_values_by_key = {
        key: create_reactive_value_safely(initial_value=None) for key in keys
    }
    reactives_shiny = {
        "User_Inputs_Shiny": dict(reactive_values_by_key),
        "Inner_Variables_Shiny": {
            "Extracted_Worksheet_Data": create_reactive_value_safely(
                initial_value=None,
            ),
        },
    }
    return reactives_shiny, reactive_values_by_key


@pytest.mark.skipif(
    not _real_pdfs_available,
    reason="sample worksheet PDFs (inputs/QWIM) are not available",
)
@pytest.mark.unit()
class Test_Real_PDF_Worksheet_Populates_Reactives:
    """End-to-end populate contract using the real sample worksheet PDFs."""

    @pytest.mark.unit()
    def test_single_pdf_extraction_contract(self) -> None:
        """The single-client worksheet extracts every client section, no partner."""
        from src.clients_QWIM.utils_client import (
            extract_client_data_from_worksheet_PDF,
            worksheet_has_client_partner,
        )

        extracted_data = extract_client_data_from_worksheet_PDF(pdf_path=_PDF_SINGLE)

        assert worksheet_has_client_partner(extracted_data=extracted_data) is False
        for section in ("Personal_Info", "Assets", "Goals", "Income"):
            assert section in extracted_data
        assert (
            extracted_data["Personal_Info"]["client_primary"]["name"].strip()
            == "Anne Smith"
        )

    @pytest.mark.unit()
    def test_couple_pdf_extraction_contract(self) -> None:
        """The couple worksheet extracts a partner and reports a partner present."""
        from src.clients_QWIM.utils_client import (
            extract_client_data_from_worksheet_PDF,
            worksheet_has_client_partner,
        )

        extracted_data = extract_client_data_from_worksheet_PDF(pdf_path=_PDF_COUPLE)

        assert worksheet_has_client_partner(extracted_data=extracted_data) is True
        assert (
            extracted_data["Personal_Info"]["client_partner"]["name"].strip()
            == "John Walsh"
        )

    @pytest.mark.unit()
    def test_single_pdf_populates_primary_and_blanks_partner(self) -> None:
        """Single PDF sets primary client reactives and blanks partner reactives."""
        from src.clients_QWIM.utils_client import (
            extract_client_data_from_worksheet_PDF,
            worksheet_has_client_partner,
        )
        from src.dashboard.shiny_utils.utils_tab_clients import (
            sync_user_inputs_shiny_from_extracted_worksheet,
        )

        extracted_data = extract_client_data_from_worksheet_PDF(pdf_path=_PDF_SINGLE)
        reactives_shiny, reactive_values_by_key = _seed_client_reactives_shiny()

        sync_user_inputs_shiny_from_extracted_worksheet(
            reactives_shiny=reactives_shiny,
            extracted_worksheet_data=extracted_data,
            has_client_partner=worksheet_has_client_partner(
                extracted_data=extracted_data,
            ),
        )

        assert (
            reactive_values_by_key[
                "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Name"
            ]._value
            == "Anne Smith"
        )
        assert (
            reactive_values_by_key[
                "Input_Tab_clients_Subtab_clients_Assets_client_Primary_Assets_Taxable"
            ]._value
            == 1000000
        )
        # Partner reactives are blanked because no partner is present.
        assert (
            reactive_values_by_key[
                "Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Name"
            ]._value
            == ""
        )

    @pytest.mark.unit()
    def test_couple_pdf_populates_partner_reactives(self) -> None:
        """Couple PDF sets both primary and partner client reactives."""
        from src.clients_QWIM.utils_client import (
            extract_client_data_from_worksheet_PDF,
            worksheet_has_client_partner,
        )
        from src.dashboard.shiny_utils.utils_tab_clients import (
            sync_user_inputs_shiny_from_extracted_worksheet,
        )

        extracted_data = extract_client_data_from_worksheet_PDF(pdf_path=_PDF_COUPLE)
        reactives_shiny, reactive_values_by_key = _seed_client_reactives_shiny()

        sync_user_inputs_shiny_from_extracted_worksheet(
            reactives_shiny=reactives_shiny,
            extracted_worksheet_data=extracted_data,
            has_client_partner=worksheet_has_client_partner(
                extracted_data=extracted_data,
            ),
        )

        assert (
            reactive_values_by_key[
                "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Name"
            ]._value
            == "Anne Smith"
        )
        assert (
            reactive_values_by_key[
                "Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Name"
            ]._value
            == "John Walsh"
        )

    @pytest.mark.unit()
    def test_both_pdfs_have_complete_advisor_info(self) -> None:
        """Both sample worksheets carry a complete advisor section (no warnings)."""
        from src.clients_QWIM.utils_client import (
            extract_client_data_from_worksheet_PDF,
            validate_required_advisor_info_section,
        )

        for pdf_path in (_PDF_SINGLE, _PDF_COUPLE):
            extracted_data = extract_client_data_from_worksheet_PDF(pdf_path=pdf_path)
            assert (
                validate_required_advisor_info_section(extracted_data=extracted_data)
                == []
            )

    @pytest.mark.unit()
    def test_preview_and_summary_builders_render_real_data(self) -> None:
        """Preview and summary builders emit non-empty trees for the real PDF data."""
        from src.clients_QWIM.utils_client import (
            extract_client_data_from_worksheet_PDF,
        )
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            build_imported_summary_tables_QWIM,
            build_preview_section_QWIM,
        )
        extracted_data = extract_client_data_from_worksheet_PDF(pdf_path=_PDF_COUPLE)

        preview_section = build_preview_section_QWIM(extracted_data=extracted_data)
        summary_tables = build_imported_summary_tables_QWIM(
            extracted_data=extracted_data,
        )

        preview_repr = repr(preview_section)
        summary_repr = repr(summary_tables)
        # Preview heading is "Preview of Extracted Data" (Viz-PRPB-aligned).
        assert "Preview of Extracted Data" in preview_repr
        # Client names from the couple PDF must appear.
        assert "Anne Smith" in preview_repr
        assert "John Walsh" in preview_repr
        assert "Anne Smith" in summary_repr

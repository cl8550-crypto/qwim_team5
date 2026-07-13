"""Pure-function integration tests for the advisor-info sync helper.

These tests do not require ``shiny.testing`` and are placed in the
integration test suite because they verify the cross-module contract
between the worksheet parser, the dashboard reactive state, and the
new ``sync_advisor_info_to_user_inputs_shiny_QWIM`` helper.

File: tests/tests_integration/dashboard/shiny_tab_clients/test_integration_advisor_sync_default_firm.py
"""

from __future__ import annotations

from typing import Any

import pytest


def _seed_advisor_reactives_shiny() -> tuple[dict, dict]:
    """Build a ``reactives_shiny`` pre-seeded with the Advisor input reactives.

    Returns
    -------
    tuple of (dict, dict)
        ``(reactives_shiny, reactive_values_by_key)`` where the second
        element maps each seeded reactive key to its ``reactive.Value``
        for assertions.
    """
    from src.dashboard.shiny_utils.reactives_initialization import (
        create_reactive_value_safely,
    )

    keys = (
        "Input_Tab_Setup_Subtab_advisor_info_name",
        "Input_Tab_Setup_Subtab_advisor_info_firm",
        "Input_Tab_Setup_Subtab_advisor_info_email",
        "Input_Tab_Setup_Subtab_advisor_info_title",
        "Input_Tab_Setup_Subtab_advisor_info_team",
        "Input_Tab_Setup_Subtab_advisor_info_credentials",
        "Input_Tab_Setup_Subtab_advisor_info_phone_number",
        "Input_Tab_Setup_Subtab_advisor_info_address",
    )
    reactive_values_by_key: dict[str, Any] = {
        key: create_reactive_value_safely(initial_value="") for key in keys
    }
    reactives_shiny = {
        "User_Inputs_Shiny": dict(reactive_values_by_key),
        "Inner_Variables_Shiny": {
            "Extracted_Worksheet_Data": create_reactive_value_safely(
                initial_value=None,
            ),
            "Extracted_Worksheet_Status_Messages": create_reactive_value_safely(
                initial_value=[],
            ),
            "Extracted_Worksheet_Defaulted_Fields": create_reactive_value_safely(
                initial_value=[],
            ),
            "Extracted_Worksheet_Warnings": create_reactive_value_safely(
                initial_value=None,
            ),
            "Extracted_Worksheet_Has_Client_Partner": create_reactive_value_safely(
                initial_value=True,
            ),
        },
        "Triggers_Shiny": {
            "Trigger_Populate_From_Worksheet": create_reactive_value_safely(
                initial_value=0,
            ),
        },
    }
    return reactives_shiny, reactive_values_by_key


@pytest.mark.integration()
class Test_Advisor_Sync_Default_Firm_Pure:
    """Pure-function tests for the new advisor-sync helper's default-firm contract.

    These tests do not require a Shiny session; they verify the
    cross-module contract that the firm default
    ``"QWIM AI Wealth Management"`` flows to the Advisor subtab
    reactive when the uploaded PDF does not include a firm name.
    """

    @pytest.mark.integration()
    def test_firm_default_flows_to_advisor_reactive(self) -> None:
        """The firm default 'QWIM AI Wealth Management' is pushed to the Advisor reactive."""
        from src.dashboard.shiny_utils._utils_tab_clients_sync import (
            sync_advisor_info_to_user_inputs_shiny_QWIM,
        )

        reactives_shiny, reactive_values_by_key = _seed_advisor_reactives_shiny()
        # Simulate the parser pre-filling the firm default.
        extracted = {
            "Advisor_Info": {
                "name": "John Advisor",
                "firm": "QWIM AI Wealth Management",  # default
                "email": "john@qwim.test",
            },
        }
        sync_advisor_info_to_user_inputs_shiny_QWIM(
            reactives_shiny=reactives_shiny,
            extracted_worksheet_data=extracted,
        )
        assert (
            reactive_values_by_key[
                "Input_Tab_Setup_Subtab_advisor_info_firm"
            ]._value
            == "QWIM AI Wealth Management"
        )
        assert (
            reactive_values_by_key[
                "Input_Tab_Setup_Subtab_advisor_info_name"
            ]._value
            == "John Advisor"
        )
        assert (
            reactive_values_by_key[
                "Input_Tab_Setup_Subtab_advisor_info_email"
            ]._value
            == "john@qwim.test"
        )

    @pytest.mark.integration()
    def test_defaulted_fields_list_includes_firm(self) -> None:
        """The returned defaulted-fields list includes 'firm' when the PDF omits it."""
        from src.dashboard.shiny_utils._utils_tab_clients_sync import (
            sync_advisor_info_to_user_inputs_shiny_QWIM,
        )

        reactives_shiny, _ = _seed_advisor_reactives_shiny()
        extracted = {
            "Advisor_Info": {
                "firm": "QWIM AI Wealth Management",  # parser filled default
            },
        }
        defaulted = sync_advisor_info_to_user_inputs_shiny_QWIM(
            reactives_shiny=reactives_shiny,
            extracted_worksheet_data=extracted,
        )
        assert "firm" in defaulted

    @pytest.mark.integration()
    def test_real_couple_pdf_advisor_sync_uses_firm_default(self) -> None:
        """The real couple PDF yields a firm default of 'QWIM AI Wealth Management'.

        This integration test exercises the full cross-module contract
        using the real sample PDF shipped under ``inputs/QWIM/``.  It
        extracts the PDF, runs the new sync helper, and asserts that
        the firm reactive is set to the default.
        """
        from pathlib import Path

        from src.clients_QWIM.utils_client import (
            extract_client_data_from_worksheet_PDF,
        )
        from src.dashboard.shiny_utils._utils_tab_clients_sync import (
            sync_advisor_info_to_user_inputs_shiny_QWIM,
        )

        pdf_path = (
            Path(__file__).resolve().parents[4]
            / "inputs"
            / "QWIM"
            / "Inputs_QWIM_Client_Couple.pdf"
        )
        if not pdf_path.is_file():
            pytest.skip("Inputs_QWIM_Client_Couple.pdf is not available")

        extracted = extract_client_data_from_worksheet_PDF(pdf_path=pdf_path)
        reactives_shiny, reactive_values_by_key = _seed_advisor_reactives_shiny()

        sync_advisor_info_to_user_inputs_shiny_QWIM(
            reactives_shiny=reactives_shiny,
            extracted_worksheet_data=extracted,
        )

        # The couple PDF does not include a firm name, so the parser
        # fills in the default 'QWIM AI Wealth Management'.
        firm_value = reactive_values_by_key[
            "Input_Tab_Setup_Subtab_advisor_info_firm"
        ]._value
        assert firm_value == "QWIM AI Wealth Management", (
            f"Expected firm default 'QWIM AI Wealth Management', got: {firm_value!r}"
        )


# ---------------------------------------------------------------------------
# New section: "Preview of Client Inputs"
# ---------------------------------------------------------------------------


@pytest.mark.integration()
class Test_Build_Preview_Section_Of_Client_Inputs_Pure:
    """Pure integration tests for the new "Preview of Client Inputs" section.

    These tests verify the renderer emits the new heading text and
    the four core client sections (Personal Info, Assets, Goals,
    Income) for real PDF data, and does NOT emit advisor info or
    insurance sections.
    """

    @pytest.mark.integration()
    def test_real_couple_pdf_renders_new_heading_and_4_sections(self) -> None:
        """The real couple PDF yields the new heading and 4 client section tables."""
        from pathlib import Path

        from src.clients_QWIM.utils_client import (
            extract_client_data_from_worksheet_PDF,
        )
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            build_preview_section_QWIM,
        )

        pdf_path = (
            Path(__file__).resolve().parents[4]
            / "inputs"
            / "QWIM"
            / "Inputs_QWIM_Client_Couple.pdf"
        )
        if not pdf_path.is_file():
            pytest.skip("Inputs_QWIM_Client_Couple.pdf is not available")

        extracted = extract_client_data_from_worksheet_PDF(pdf_path=pdf_path)
        preview = build_preview_section_QWIM(extracted_data=extracted)
        rendered_repr = repr(preview)

        # Current heading is emitted.
        assert "Preview of Extracted Data" in rendered_repr, (
            f"renderer must emit 'Preview of Extracted Data' heading; "
            f"got: {rendered_repr[:200]}"
        )
        # Old heading is NOT emitted.
        assert "Preview of Client Inputs" not in rendered_repr, (
            "renderer must NOT emit the old 'Preview of Client Inputs' heading"
        )
        # Both client names from the couple PDF are in the output.
        assert "Anne Smith" in rendered_repr
        assert "John Walsh" in rendered_repr
        # All four client section titles are present.
        assert "Personal Information" in rendered_repr
        assert "Assets" in rendered_repr
        assert "Goals" in rendered_repr
        assert "Income" in rendered_repr
        # Advisor and insurance sections are NOT rendered.
        assert "Advisor Information" not in rendered_repr
        assert "LTC Insurance" not in rendered_repr
        assert "Life Insurance" not in rendered_repr
        assert "Contingency" not in rendered_repr

    @pytest.mark.integration()
    def test_real_single_pdf_renders_new_heading(self) -> None:
        """The real single PDF also yields the new heading."""
        from pathlib import Path

        from src.clients_QWIM.utils_client import (
            extract_client_data_from_worksheet_PDF,
        )
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            build_preview_section_QWIM,
        )

        pdf_path = (
            Path(__file__).resolve().parents[4]
            / "inputs"
            / "QWIM"
            / "Inputs_QWIM_Client_Single.pdf"
        )
        if not pdf_path.is_file():
            pytest.skip("Inputs_QWIM_Client_Single.pdf is not available")

        extracted = extract_client_data_from_worksheet_PDF(pdf_path=pdf_path)
        preview = build_preview_section_QWIM(extracted_data=extracted)
        rendered_repr = repr(preview)

        assert "Preview of Extracted Data" in rendered_repr
        # Single PDF has no partner, so the partner name must not appear.
        assert "John Walsh" not in rendered_repr
        # The primary client name IS in the output.
        assert "Anne Smith" in rendered_repr

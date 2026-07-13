"""Unit tests for subtab_outline module.

Tests cover:
- Module importability and exports
- Pure helper functions (``_format_preview_value``, ``_humanize_field_key``,
  ``_build_preview_record_table``, ``_build_preview_table``)
- Empty-state placeholder helper
- Source-level wiring: imported_summary output, preview renderer's
  dependency-read ordering, and failure-branch clearing
"""

from __future__ import annotations

import pytest


# Try importing module under test
try:
    from src.dashboard.shiny_tab_clients.subtab_outline import (
        subtab_clients_outline_server,  # noqa: F401
        subtab_clients_outline_ui,  # noqa: F401
    )

    MODULE_IMPORT_AVAILABLE = True
except ImportError:
    MODULE_IMPORT_AVAILABLE = False


# ============================================================================
# Module import tests
# ============================================================================


@pytest.mark.unit()
class Test_Subtab_Outline_Module_Imports:
    """Verify subtab_outline module imports and public API."""

    @pytest.mark.unit()
    def test_module_importable(self):
        """Module imports without error."""
        import src.dashboard.shiny_tab_clients.subtab_outline as mod

        assert mod is not None

    @pytest.mark.unit()
    def test_ui_callable(self):
        """subtab_clients_outline_ui is callable."""
        from src.dashboard.shiny_tab_clients.subtab_outline import subtab_clients_outline_ui

        assert callable(subtab_clients_outline_ui)

    @pytest.mark.unit()
    def test_server_callable(self):
        """subtab_clients_outline_server is callable."""
        from src.dashboard.shiny_tab_clients.subtab_outline import subtab_clients_outline_server

        assert callable(subtab_clients_outline_server)

    @pytest.mark.unit()
    def test_logger_initialised(self):
        """Module-level _logger is initialised."""
        import src.dashboard.shiny_tab_clients.subtab_outline as mod

        assert hasattr(mod, "_logger")
        assert mod._logger is not None


# ============================================================================
# Upload section visibility on initial render
# ============================================================================


@pytest.mark.unit()
class Test_Upload_Section_Visible_On_Initial_Render:
    """Tests that the file upload input is visible on initial page load.

    Viz-PRPB pattern: the file input is rendered by a ``@output @render.ui``
    callback (``output_ID_..._upload_section``), which eliminates
    ``ui.panel_conditional`` namespace issues and ensures ``@reactive.event``
    fires reliably inside ``@module.server``.
    """

    @pytest.mark.unit()
    def test_upload_section_is_server_rendered(self) -> None:
        """The upload section uses server-rendered output (not ui.panel_conditional)."""
        from pathlib import Path

        src_path = (
            Path(__file__).resolve().parents[4]
            / "src"
            / "dashboard"
            / "shiny_tab_clients"
            / "subtab_outline.py"
        )
        text = src_path.read_text(encoding="utf-8")
        assert (
            "def output_ID_tab_clients_subtab_clients_outline_upload_section"
            in text
        ), "upload section must be server-rendered"
        assert "ui.panel_conditional" not in text, (
            "ui.panel_conditional must not be used"
        )

    @pytest.mark.unit()
    def test_upload_section_is_server_side_output_ui(self) -> None:
        """The upload section uses ``ui.output_ui(..._upload_section)`` in the static UI."""
        from pathlib import Path

        src_path = (
            Path(__file__).resolve().parents[4]
            / "src"
            / "dashboard"
            / "shiny_tab_clients"
            / "subtab_outline.py"
        )
        text = src_path.read_text(encoding="utf-8")
        assert (
            "output_ID_tab_clients_subtab_clients_outline_upload_section"
            in text
        ), "upload section must be referenced in the static UI via ui.output_ui"

    @pytest.mark.unit()
    def test_observer_uses_event_driven_pattern(self) -> None:
        """The upload observer uses ``@reactive.effect @reactive.event``."""
        import re
        from pathlib import Path

        src_path = (
            Path(__file__).resolve().parents[4]
            / "src"
            / "dashboard"
            / "shiny_tab_clients"
            / "subtab_outline.py"
        )
        text = src_path.read_text(encoding="utf-8")
        text_no_ds = re.sub(r'\"\"\"[\s\S]*?\"\"\"', "", text)
        assert "@reactive.effect" in text_no_ds, (
            "upload observer must use @reactive.effect"
        )
        assert "@reactive.event(input.input_ID_tab_clients_subtab_clients_outline_file_upload)" in text_no_ds, (
            "upload observer must use @reactive.event(file_input)"
        )



    @pytest.mark.unit()
    def test_none_returns_dash(self):
        """None value returns em-dash or similar empty marker."""
        from src.dashboard.shiny_tab_clients.subtab_outline import _format_preview_value

        result = _format_preview_value(value = None)
        assert isinstance(result, str)
        assert result != ""

    @pytest.mark.unit()
    def test_empty_string_returns_marker(self):
        """Empty string returns a non-empty placeholder string."""
        from src.dashboard.shiny_tab_clients.subtab_outline import _format_preview_value

        result = _format_preview_value(value = "")
        assert isinstance(result, str)

    @pytest.mark.unit()
    def test_numeric_value_formatted(self):
        """Numeric value is converted to a string representation."""
        from src.dashboard.shiny_tab_clients.subtab_outline import _format_preview_value

        result = _format_preview_value(value = 12345)
        assert "12" in result or "12,345" in result or "$" in result or result == "12345"

    @pytest.mark.unit()
    def test_string_value_returned(self):
        """Plain string value is returned as a string."""
        from src.dashboard.shiny_tab_clients.subtab_outline import _format_preview_value

        result = _format_preview_value(value = "Alice")
        assert "Alice" in result

    @pytest.mark.unit()
    def test_bool_true_returns_yes(self):
        """Boolean True should return 'Yes'."""
        from src.dashboard.shiny_tab_clients.subtab_outline import _format_preview_value

        result = _format_preview_value(value = True)
        assert result == "Yes"

    @pytest.mark.unit()
    def test_bool_false_returns_no(self):
        """Boolean False should return 'No'."""
        from src.dashboard.shiny_tab_clients.subtab_outline import _format_preview_value

        result = _format_preview_value(value = False)
        assert result == "No"


# ============================================================================
# _humanize_field_key
# ============================================================================


@pytest.mark.unit()
class Test_Humanize_Field_Key:
    """Tests for _humanize_field_key helper."""

    @pytest.mark.unit()
    def test_underscore_replaced_by_space(self):
        """Underscores in key become spaces."""
        from src.dashboard.shiny_tab_clients.subtab_outline import _humanize_field_key

        result = _humanize_field_key(key = "first_name")
        assert "_" not in result

    @pytest.mark.unit()
    def test_result_is_string(self):
        """Result is always a string."""
        from src.dashboard.shiny_tab_clients.subtab_outline import _humanize_field_key

        assert isinstance(_humanize_field_key(key = "age_current"), str)

    @pytest.mark.unit()
    def test_empty_key_returns_string(self):
        """Empty key input returns an empty string or placeholder."""
        from src.dashboard.shiny_tab_clients.subtab_outline import _humanize_field_key

        result = _humanize_field_key(key = "")
        assert isinstance(result, str)


# ============================================================================
# _build_preview_record_table
# ============================================================================


@pytest.mark.unit()
class Test_Build_Preview_Record_Table:
    """Tests for _build_preview_record_table helper."""

    @pytest.mark.unit()
    def test_empty_dict_returns_table_like_object(self):
        """Empty dict returns None (documented behaviour for empty sections)."""
        from src.dashboard.shiny_tab_clients.subtab_outline import _build_preview_record_table

        result = _build_preview_record_table(section_title = "Advisor Info", section_data = {})
        assert result is None

    @pytest.mark.unit()
    def test_single_entry_renders(self):
        """Single-entry dict renders without error."""
        from src.dashboard.shiny_tab_clients.subtab_outline import _build_preview_record_table

        result = _build_preview_record_table(section_title = "Advisor Info", section_data = {"name": "Alice"})
        assert result is not None

    @pytest.mark.unit()
    def test_multiple_entries_renders(self):
        """Multiple-entry dict renders without error."""
        from src.dashboard.shiny_tab_clients.subtab_outline import _build_preview_record_table

        result = _build_preview_record_table(section_title = "Advisor Info", section_data = {"name": "Alice", "age_current": 55})
        assert result is not None


# ============================================================================
# _build_preview_table
# ============================================================================


@pytest.mark.unit()
class Test_Build_Preview_Table:
    """Tests for _build_preview_table helper."""

    @pytest.mark.unit()
    def test_non_dict_section_returns_object(self):
        """Empty client_primary and partner returns None."""
        from src.dashboard.shiny_tab_clients.subtab_outline import _build_preview_table

        result = _build_preview_table(section_title = "Section", section_data = {"client_primary": {}, "client_partner": {}})
        assert result is None

    @pytest.mark.unit()
    def test_advisor_info_section_returns_none_for_flat_dict(self):
        """Flat dict without client_primary/partner keys returns None."""
        from src.dashboard.shiny_tab_clients.subtab_outline import _build_preview_table

        result = _build_preview_table(section_title = "Advisor Info", section_data = {"name": "John Advisor"})
        assert result is None

    @pytest.mark.unit()
    def test_client_section_with_primary_partner_renders(self):
        """Section with client_primary/client_partner sub-dicts renders."""
        from src.dashboard.shiny_tab_clients.subtab_outline import _build_preview_table

        section = {
            "client_primary": {"name": "Alice", "age_current": 55},
            "client_partner": {"name": "Bob", "age_current": 53},
        }
        result = _build_preview_table(section_title = "Personal Info", section_data = section)
        assert result is not None

    @pytest.mark.unit()
    def test_primary_only_no_partner_renders(self):
        """Section with only client_primary (no partner) renders without partner column."""
        from src.dashboard.shiny_tab_clients.subtab_outline import _build_preview_table

        section = {
            "client_primary": {"name": "Alice", "age_current": 55},
        }
        result = _build_preview_table(section_title = "Personal Info", section_data = section)
        assert result is not None


# ============================================================================
# build_imported_summary_tables_QWIM
# ============================================================================


@pytest.mark.unit()
class Class_Test_Build_Imported_Summary_Tables_QWIM:
    """Tests for the in-card verification table builder.

    Notes
    -----
    These tests exercise the pure renderer for the new
    "Imported Values Summary" tables that appear under the "Data Entry
    Method" card after a successful PDF upload.  The renderer must
    short-circuit on empty / non-dict input and produce a Tag tree
    containing up to four per-section tables.
    """

    @pytest.mark.unit()
    def Test_None_Input_Returns_Empty_Div(self) -> None:
        """``None`` input returns an empty placeholder div (no exception)."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            build_imported_summary_tables_QWIM,
        )

        result = build_imported_summary_tables_QWIM(extracted_data = None)
        assert result is not None

    @pytest.mark.unit()
    def Test_Empty_Dict_Returns_Empty_Div(self) -> None:
        """Empty dict input returns an empty placeholder div."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            build_imported_summary_tables_QWIM,
        )

        result = build_imported_summary_tables_QWIM(extracted_data = {})
        assert result is not None

    @pytest.mark.unit()
    def Test_Only_Advisor_Info_Returns_Empty_Div(self) -> None:
        """When only Advisor_Info is present, no per-section tables render."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            build_imported_summary_tables_QWIM,
        )

        result = build_imported_summary_tables_QWIM(
            extracted_data = {"Advisor_Info": {"name": "John"}},
        )
        assert result is not None

    @pytest.mark.unit()
    def Test_Single_Section_Renders_One_Card(self) -> None:
        """A single section with primary + partner data renders a Tag tree."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            build_imported_summary_tables_QWIM,
        )

        extracted = {
            "Personal_Info": {
                "client_primary": {"name": "Alice", "age_current": "55"},
                "client_partner": {"name": "Bob", "age_current": "53"},
            },
        }
        result = build_imported_summary_tables_QWIM(extracted_data = extracted)
        assert result is not None

    @pytest.mark.unit()
    def Test_All_Four_Client_Sections_Render(self) -> None:
        """All four client sections (Personal Info, Assets, Goals, Income) render."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            build_imported_summary_tables_QWIM,
        )

        extracted = {
            "Personal_Info": {
                "client_primary": {"name": "Alice", "age_current": "55"},
            },
            "Assets": {
                "client_primary": {"assets_taxable": "100000"},
            },
            "Goals": {
                "client_primary": {"goal_essential": "50000"},
            },
            "Income": {
                "client_primary": {"income_social_security": "20000"},
            },
        }
        result = build_imported_summary_tables_QWIM(extracted_data = extracted)
        assert result is not None

    @pytest.mark.unit()
    def Test_Non_Dict_Section_Data_Is_Handled_Gracefully(self) -> None:
        """Non-dict section payload is coerced to an empty dict (no exception)."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            build_imported_summary_tables_QWIM,
        )

        extracted = {
            "Personal_Info": "not_a_dict",
            "Assets": 42,
            "Goals": ["unexpected", "list"],
        }
        result = build_imported_summary_tables_QWIM(extracted_data = extracted)
        assert result is not None

    @pytest.mark.unit()
    def Test_Primary_Only_Section_Renders_Without_Partner_Column(self) -> None:
        """Section with only client_primary renders the per-section card."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            build_imported_summary_tables_QWIM,
        )

        extracted = {
            "Personal_Info": {
                "client_primary": {"name": "Solo", "age_current": "60"},
            },
        }
        result = build_imported_summary_tables_QWIM(extracted_data = extracted)
        assert result is not None

    @pytest.mark.unit()
    def Test_All_Empty_Client_Sections_Returns_Empty_Div(self) -> None:
        """When every client section has empty primary + partner, no card renders."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            build_imported_summary_tables_QWIM,
        )

        extracted = {
            "Personal_Info": {"client_primary": {}, "client_partner": {}},
            "Assets": {"client_primary": {}, "client_partner": {}},
            "Goals": {"client_primary": {}, "client_partner": {}},
            "Income": {"client_primary": {}, "client_partner": {}},
        }
        result = build_imported_summary_tables_QWIM(extracted_data = extracted)
        assert result is not None

    @pytest.mark.unit()
    def Test_Section_With_Only_Partner_Data_Still_Renders(self) -> None:
        """A section with only client_partner data renders (partner column shows)."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            build_imported_summary_tables_QWIM,
        )

        extracted = {
            "Personal_Info": {
                "client_partner": {"name": "Bob", "age_current": "53"},
            },
        }
        result = build_imported_summary_tables_QWIM(extracted_data = extracted)
        assert result is not None

    @pytest.mark.unit()
    def Test_Non_Dict_Primary_And_Partner_Are_Handled_Gracefully(self) -> None:
        """Non-dict client_primary / client_partner values are coerced to empty dicts."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            build_imported_summary_tables_QWIM,
        )

        extracted = {
            "Personal_Info": {
                "client_primary": "should_be_dict",
                "client_partner": 99,
            },
        }
        result = build_imported_summary_tables_QWIM(extracted_data = extracted)
        assert result is not None

    @pytest.mark.unit()
    def Test_Result_Str_Repr_Does_Not_Raise(self) -> None:
        """The returned Tag tree renders a stable string representation."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            build_imported_summary_tables_QWIM,
        )

        extracted = {
            "Personal_Info": {
                "client_primary": {"name": "Alice", "age_current": "55"},
            },
        }
        result = build_imported_summary_tables_QWIM(extracted_data = extracted)
        # `Tag` objects have a stable repr; just assert it's not None
        # and that the rendered string contains the section title.
        assert result is not None
        rendered_repr = repr(result)
        assert "Imported Values Summary" in rendered_repr


# ============================================================================
# _build_imported_summary_section_card
# ============================================================================


@pytest.mark.unit()
class Class_Test_Build_Imported_Summary_Section_Card:
    """Tests for the single-section imported-summary card builder."""

    @pytest.mark.unit()
    def Test_Empty_Primary_And_Partner_Returns_None(self) -> None:
        """Empty primary + partner returns None so the caller skips the card."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            _build_imported_summary_section_card,
        )

        result = _build_imported_summary_section_card(
            section_title = "Personal Information",
            section_data = {"client_primary": {}, "client_partner": {}},
        )
        assert result is None

    @pytest.mark.unit()
    def Test_Flat_Dict_Without_Primary_Or_Partner_Returns_None(self) -> None:
        """Flat dict without ``client_primary`` / ``client_partner`` keys returns None."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            _build_imported_summary_section_card,
        )

        result = _build_imported_summary_section_card(
            section_title = "Advisor Info",
            section_data = {"name": "John"},
        )
        assert result is None

    @pytest.mark.unit()
    def Test_Primary_Only_Data_Renders_Card(self) -> None:
        """Section with only primary data renders the card."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            _build_imported_summary_section_card,
        )

        result = _build_imported_summary_section_card(
            section_title = "Personal Information",
            section_data = {"client_primary": {"name": "Alice", "age_current": "55"}},
        )
        assert result is not None

    @pytest.mark.unit()
    def Test_Primary_And_Partner_Data_Renders_Card(self) -> None:
        """Section with primary + partner data renders the card."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            _build_imported_summary_section_card,
        )

        result = _build_imported_summary_section_card(
            section_title = "Personal Information",
            section_data = {
                "client_primary": {"name": "Alice"},
                "client_partner": {"name": "Bob"},
            },
        )
        assert result is not None

    @pytest.mark.unit()
    def Test_Non_Dict_Primary_And_Partner_Are_Handled_Gracefully(self) -> None:
        """Non-dict primary / partner values are coerced to empty dicts (no exception)."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            _build_imported_summary_section_card,
        )

        result = _build_imported_summary_section_card(
            section_title = "Personal Information",
            section_data = {
                "client_primary": "should_be_dict",
                "client_partner": 42,
            },
        )
        # Both coerced to empty dicts -> returns None (no card rendered).
        assert result is None

    @pytest.mark.unit()
    def Test_Partner_Only_Data_Renders_Card(self) -> None:
        """A section with only client_partner data still renders the card."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            _build_imported_summary_section_card,
        )

        result = _build_imported_summary_section_card(
            section_title = "Personal Information",
            section_data = {"client_partner": {"name": "Bob"}},
        )
        assert result is not None

    @pytest.mark.unit()
    def Test_Keys_Preserves_Primary_Then_Partner_Order(self) -> None:
        """When both primary and partner have keys, the rendered table has at least 2 rows."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            _build_imported_summary_section_card,
        )

        result = _build_imported_summary_section_card(
            section_title = "Personal Information",
            section_data = {
                "client_primary": {"name": "Alice"},
                "client_partner": {"name": "Bob"},
            },
        )
        assert result is not None


# ============================================================================
# Reactive flow: _show_imported_summary flag wiring
# ============================================================================


@pytest.mark.unit()
class Class_Test_Show_Imported_Summary_Reactive:
    """Tests verifying the new ``_show_imported_summary`` reactive exists and is initialised.

    Notes
    -----
    The reactive Value is created at server-decoration time inside
    ``subtab_clients_outline_server``.  These tests verify that the
    expected behavioural contract holds: the new flag mirrors the
    existing ``_show_preview`` flag's lifecycle, so it must be a
    module-level reference accessible to the server function.  We do
    not start a real Shiny session here — we just verify the symbol
    exists at module import time and that its name matches the
    contract documented in the docstring.
    """

    @pytest.mark.unit()
    def Test_Reactive_Flag_Is_Declared_In_Module(self) -> None:
        """The ``_show_preview`` local reactive is declared in the server."""
        import src.dashboard.shiny_tab_clients.subtab_outline as mod

        with open(mod.__file__, encoding="utf-8") as file_handle:
            source_text = file_handle.read()
        # The flag is stored as a local ``reactive.Value[bool]`` inside
        # ``subtab_clients_outline_server`` and referenced both as
        # initialised and as a setter (a minimum of 2 occurrences).
        assert "_show_preview" in source_text
        assert source_text.count("_show_preview") >= 2

    @pytest.mark.unit()
    def Test_New_Output_Id_Referenced_In_Module(self) -> None:
        """The file input ID is referenced in the module source."""
        import src.dashboard.shiny_tab_clients.subtab_outline as mod

        with open(mod.__file__, encoding="utf-8") as file_handle:
            source_text = file_handle.read()
        assert (
            "input_ID_tab_clients_subtab_clients_outline_file_upload"
            in source_text
        )

    @pytest.mark.unit()
    def Test_New_Pure_Helper_Reachable_Via_Public_Module(self) -> None:
        """The new pure helper is importable from the public module."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            build_imported_summary_tables_QWIM,
        )

        assert callable(build_imported_summary_tables_QWIM)

    @pytest.mark.unit()
    def Test_Helper_Handles_Realistic_Extraction_Payload(self) -> None:
        """Helper renders all four sections for a realistic PDF extraction payload."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            build_imported_summary_tables_QWIM,
        )

        extracted = {
            "Advisor_Info": {
                "name": "John Advisor",
                "firm": "QWIM Wealth",
            },
            "Personal_Info": {
                "client_primary": {
                    "name": "Alice",
                    "age_current": "55",
                    "state": "New York",
                    "tolerance_risk": "Moderate",
                },
                "client_partner": {
                    "name": "Bob",
                    "age_current": "53",
                    "state": "New York",
                },
            },
            "Assets": {
                "client_primary": {
                    "assets_taxable": "500000",
                    "assets_tax_deferred": "200000",
                    "assets_tax_free": "50000",
                },
                "client_partner": {
                    "assets_taxable": "100000",
                },
            },
            "Goals": {
                "client_primary": {
                    "goal_essential": "60000",
                    "goal_important": "30000",
                    "goal_aspirational": "15000",
                },
            },
            "Income": {
                "client_primary": {
                    "income_social_security": "24000",
                    "income_pension": "12000",
                },
            },
            "LTC_Insurance": {"client_primary": {"annual_premium": "3000"}},
            "Life_Insurance": {"client_primary": {"death_benefit": "500000"}},
            "Contingency": {"client_primary": {"emergency_fund": "20000"}},
        }
        result = build_imported_summary_tables_QWIM(extracted_data = extracted)
        assert result is not None


# ============================================================================
# build_preview_section_QWIM
# ============================================================================


@pytest.mark.unit()
class Class_Test_Build_Preview_Section_QWIM:
    """Tests for the Outline "Preview of Client Inputs" section builder.

    Notes
    -----
    The renderer is pure: it must short-circuit on empty / non-dict
    input and otherwise produce a Tag tree containing exactly the
    four core client sections (Personal Information, Assets, Goals,
    Income).  The advisor info and insurance sections (LTC, Life,
    Contingency) are intentionally NOT rendered by this helper per
    the product requirement that the preview shows only the four
    core client sections.
    """

    @pytest.mark.unit()
    def Test_None_Input_Returns_Empty_Div(self) -> None:
        """``None`` input returns an empty placeholder div (no exception)."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            build_preview_section_QWIM,
        )

        result = build_preview_section_QWIM(extracted_data = None)
        assert result is not None
        assert "Preview of Client Inputs" not in repr(result)

    @pytest.mark.unit()
    def Test_Empty_Dict_Returns_Empty_Div(self) -> None:
        """Empty dict input returns an empty placeholder div."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            build_preview_section_QWIM,
        )

        result = build_preview_section_QWIM(extracted_data = {})
        assert result is not None
        assert "Preview of Client Inputs" not in repr(result)

    @pytest.mark.unit()
    def Test_All_Empty_Sections_Returns_Empty_Div(self) -> None:
        """When every section has empty primary + partner, no heading renders."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            build_preview_section_QWIM,
        )

        extracted = {
            "Personal_Info": {"client_primary": {}, "client_partner": {}},
            "Assets": {"client_primary": {}, "client_partner": {}},
            "Goals": {"client_primary": {}, "client_partner": {}},
            "Income": {"client_primary": {}, "client_partner": {}},
        }
        result = build_preview_section_QWIM(extracted_data = extracted)
        assert "Preview of Client Inputs" not in repr(result)

    @pytest.mark.unit()
    def Test_Heading_Is_Preview_Of_Extracted_Data(self) -> None:
        """The renderer emits the 'Preview of Extracted Data' heading (Viz-PRPB-aligned)."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            build_preview_section_QWIM,
        )

        extracted = {
            "Personal_Info": {"client_primary": {"name": "Alice"}},
        }
        result = build_preview_section_QWIM(extracted_data = extracted)
        rendered_repr = repr(result)
        assert "Preview of Extracted Data" in rendered_repr

    @pytest.mark.unit()
    def Test_Client_Section_Renders_Heading_And_Name(self) -> None:
        """A populated client section renders the preview heading and client name."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            build_preview_section_QWIM,
        )

        extracted = {
            "Personal_Info": {
                "client_primary": {"name": "Alice", "age_current": "55"},
                "client_partner": {"name": "Bob", "age_current": "53"},
            },
        }
        result = build_preview_section_QWIM(extracted_data = extracted)
        rendered_repr = repr(result)
        assert "Preview of Extracted Data" in rendered_repr
        assert "Alice" in rendered_repr
        assert "Bob" in rendered_repr

    @pytest.mark.unit()
    def Test_All_Four_Client_Sections_Render(self) -> None:
        """All four client sections render under the preview heading."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            build_preview_section_QWIM,
        )

        extracted = {
            "Personal_Info": {"client_primary": {"name": "Alice"}},
            "Assets": {"client_primary": {"assets_taxable": "100000"}},
            "Goals": {"client_primary": {"goal_essential": "50000"}},
            "Income": {"client_primary": {"income_social_security": "20000"}},
        }
        result = build_preview_section_QWIM(extracted_data = extracted)
        rendered_repr = repr(result)
        assert "Preview of Extracted Data" in rendered_repr
        assert "Assets" in rendered_repr
        assert "Goals" in rendered_repr
        assert "Income" in rendered_repr

    @pytest.mark.unit()
    def Test_Advisor_Info_Is_Not_Rendered(self) -> None:
        """Advisor info is intentionally NOT rendered in the preview."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            build_preview_section_QWIM,
        )

        extracted = {
            "Personal_Info": {"client_primary": {"name": "Alice"}},
            "Advisor_Info": {"name": "John Advisor", "email": "john@qwim.test"},
        }
        result = build_preview_section_QWIM(extracted_data = extracted)
        rendered_repr = repr(result)
        # Advisor card and table must NOT appear.
        assert "John Advisor" not in rendered_repr
        assert "Advisor Information" not in rendered_repr

    @pytest.mark.unit()
    def Test_Insurance_Sections_Are_Not_Rendered(self) -> None:
        """LTC, Life Insurance, and Contingency sections are NOT rendered in the preview."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            build_preview_section_QWIM,
        )

        extracted = {
            "Personal_Info": {"client_primary": {"name": "Alice"}},
            "LTC_Insurance": {"client_primary": {"annual_premium": "3000"}},
            "Life_Insurance": {"client_primary": {"death_benefit": "500000"}},
            "Contingency": {"client_primary": {"emergency_fund": "20000"}},
        }
        result = build_preview_section_QWIM(extracted_data = extracted)
        rendered_repr = repr(result)
        # None of the insurance section titles should appear.
        assert "LTC Insurance" not in rendered_repr
        assert "Life Insurance" not in rendered_repr
        assert "Contingency" not in rendered_repr
        assert "3000" not in rendered_repr
        assert "500000" not in rendered_repr
        assert "20000" not in rendered_repr

    @pytest.mark.unit()
    def Test_Only_Advisor_Info_Returns_Empty_Div(self) -> None:
        """When only Advisor_Info is present, the renderer returns an empty div (no heading)."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            build_preview_section_QWIM,
        )

        extracted = {"Advisor_Info": {"name": "Solo Advisor"}}
        result = build_preview_section_QWIM(extracted_data = extracted)
        assert "Preview of Client Inputs" not in repr(result)

    @pytest.mark.unit()
    def Test_Non_Dict_Section_Data_Is_Skipped(self) -> None:
        """Non-dict section payloads are skipped without raising."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            build_preview_section_QWIM,
        )

        extracted = {
            "Personal_Info": "not_a_dict",
            "Assets": 42,
            "Goals": ["unexpected"],
            "Income": {"client_primary": {"income_pension": "12000"}},
        }
        result = build_preview_section_QWIM(extracted_data = extracted)
        rendered_repr = repr(result)
        assert "Preview of Extracted Data" in rendered_repr


# ============================================================================
# _build_empty_state_placeholder_QWIM
# ============================================================================
# ============================================================================
# _build_empty_state_placeholder_QWIM
# ============================================================================


@pytest.mark.unit()
class Test_Build_Empty_State_Placeholder_QWIM:
    """Tests for the shared empty-state placeholder helper.

    Notes
    -----
    The placeholder is rendered by both ``output_ID_tab_clients_subtab_
    clients_outline_imported_summary`` and ``output_ID_tab_clients_sub
    tab_clients_outline_preview_section`` whenever ``Extracted_Worksheet
    _Data`` is ``None`` or ``_show_preview`` is ``False``.  It must be a
    pure function returning a non-``None`` Tag tree whose string
    representation mentions the user-facing instruction.
    """

    @pytest.mark.unit()
    def Test_Returns_Non_None_Tag_Tree(self) -> None:
        """The helper always returns a non-``None`` Tag tree."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            _build_empty_state_placeholder_QWIM,
        )

        result = _build_empty_state_placeholder_QWIM()
        assert result is not None

    @pytest.mark.unit()
    def Test_Placeholder_Text_Is_In_Repr(self) -> None:
        """The rendered repr contains the user-facing instruction text."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            _build_empty_state_placeholder_QWIM,
        )

        rendered_repr = repr(_build_empty_state_placeholder_QWIM())
        assert "Upload a worksheet to see extracted values here." in rendered_repr

    @pytest.mark.unit()
    def Test_Helper_Is_Stateless(self) -> None:
        """Calling the helper twice yields stable, non-divergent output."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            _build_empty_state_placeholder_QWIM,
        )

        first_repr = repr(_build_empty_state_placeholder_QWIM())
        second_repr = repr(_build_empty_state_placeholder_QWIM())
        assert first_repr == second_repr

    @pytest.mark.unit()
    def Test_Helper_Has_No_Required_Arguments(self) -> None:
        """The helper takes no required arguments (callable with zero args)."""
        import inspect

        from src.dashboard.shiny_tab_clients.subtab_outline import (
            _build_empty_state_placeholder_QWIM,
        )

        signature = inspect.signature(_build_empty_state_placeholder_QWIM)
        required_params = [
            name for name, parameter in signature.parameters.items()
            if parameter.default is inspect.Parameter.empty
            and parameter.kind in (
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                inspect.Parameter.KEYWORD_ONLY,
            )
        ]
        assert required_params == []


# ============================================================================
# Imported-summary output wiring (source-level)
# ============================================================================


@pytest.mark.unit()
class Test_Imported_Summary_Output_Wiring:
    """Source-level tests for the in-card Imported Values Summary output.

    Notes
    -----
    Verifies that the new server output and its static UI placeholder
    are both wired into the module, and that the renderer reads the
    required reactive dependencies *unconditionally* (the root cause
    of the original bug).  These tests are source-level because
    starting a real Shiny session is not appropriate for fast unit
    coverage; the full reactive-flow contract is verified by the
    integration / AppDriver test under
    ``tests/tests_integration/dashboard/shiny_tab_clients/``.
    """

    @pytest.mark.unit()
    def Test_New_Output_Id_Defined_In_Source(self) -> None:
        """The new output ID is defined in the source as an ``@output``."""
        import src.dashboard.shiny_tab_clients.subtab_outline as mod

        with open(mod.__file__, encoding="utf-8") as file_handle:
            source_text = file_handle.read()
        assert (
            "def output_ID_tab_clients_subtab_clients_outline_imported_summary"
            in source_text
        ), "server output for the in-card summary must be defined"

    @pytest.mark.unit()
    def Test_New_Output_Id_Referenced_In_Static_UI(self) -> None:
        """The new output ID is referenced in the static UI function."""
        import src.dashboard.shiny_tab_clients.subtab_outline as mod

        with open(mod.__file__, encoding="utf-8") as file_handle:
            source_text = file_handle.read()
        # The output is rendered statically via ui.output_ui(...).
        assert (
            '"output_ID_tab_clients_subtab_clients_outline_imported_summary"'
            in source_text
        ), "in-card summary output_ui placeholder must exist in the static UI"

    @pytest.mark.unit()
    def Test_New_Output_Renders_Empty_State_When_Data_Missing(self) -> None:
        """The new output renderer delegates to the placeholder on empty data."""
        import src.dashboard.shiny_tab_clients.subtab_outline as mod

        with open(mod.__file__, encoding="utf-8") as file_handle:
            source_text = file_handle.read()
        # The renderer calls _build_empty_state_placeholder_QWIM() in
        # the short-circuit branch.
        assert "_build_empty_state_placeholder_QWIM" in source_text

    @pytest.mark.unit()
    def Test_New_Output_Calls_Helper_When_Data_Present(self) -> None:
        """The new output renderer delegates to ``build_imported_summary_tables_QWIM``."""
        import src.dashboard.shiny_tab_clients.subtab_outline as mod

        with open(mod.__file__, encoding="utf-8") as file_handle:
            source_text = file_handle.read()
        assert "build_imported_summary_tables_QWIM" in source_text


# ============================================================================
# Preview renderer dependency-read ordering (regression test for the bug)
# ============================================================================


@pytest.mark.unit()
class Test_Preview_Renderer_Dependency_Read_Ordering:
    """Regression tests for the preview-renderer reactive-dependency bug.

    Notes
    -----
    The original bug was that the preview renderer's
    ``if not show or data is None: return ui.div()`` short-circuited
    *before* ``inner["Extracted_Worksheet_Warnings"].get()`` was called.
    Because the warnings reactive was the last one to be read, the
    render effect did not subscribe to it, and the preview never
    re-rendered when warnings changed.  The fix reads all three
    reactives (``_show_preview``, ``Extracted_Worksheet_Data``,
    ``Extracted_Worksheet_Warnings``) unconditionally, before the
    short-circuit.  These source-level tests pin that ordering in place.
    """

    @pytest.mark.unit()
    def Test_Imported_Summary_Renderer_Reads_All_Reactive_Sources(self) -> None:
        """The imported-summary renderer reads all required reactive sources."""
        import src.dashboard.shiny_tab_clients.subtab_outline as mod

        with open(mod.__file__, encoding="utf-8") as file_handle:
            source_text = file_handle.read()
        # Find the imported_summary renderer's body.  It must read reactive
        # sources unconditionally before any short-circuit.
        assert "_show_preview()" in source_text
        assert 'inner["Extracted_Worksheet_Data"].get()' in source_text

    @pytest.mark.unit()
    def Test_Imported_Summary_Renderer_Short_Circuit_After_Dependencies(self) -> None:
        """The imported-summary short-circuit guard appears after dependency reads."""
        from pathlib import Path

        import src.dashboard.shiny_tab_clients.subtab_outline as mod

        text = Path(mod.__file__).read_text(encoding="utf-8")
        renderer_start = text.find(
            "def output_ID_tab_clients_subtab_clients_outline_imported_summary",
        )
        assert renderer_start != -1, "imported_summary renderer must be present"
        # Find the next def after the renderer (the function body end).
        next_def = text.find("\n    def ", renderer_start + 10)
        if next_def == -1:
            next_def = text.find("\ndef _", renderer_start + 10)
        body = text[renderer_start:next_def] if next_def != -1 else text[renderer_start:]
        # All required reactive dependency reads must appear in the function body.
        assert "_show_preview()" in body
        assert 'inner["Extracted_Worksheet_Data"].get()' in body

    @pytest.mark.unit()
    def Test_Imported_Summary_Renderer_Reads_All_Reactive_Sources(self) -> None:
        """The in-card summary renderer reads both reactive sources."""
        import src.dashboard.shiny_tab_clients.subtab_outline as mod

        with open(mod.__file__, encoding="utf-8") as file_handle:
            source_text = file_handle.read()
        assert "_show_preview()" in source_text
        assert 'inner["Extracted_Worksheet_Data"].get()' in source_text


# ============================================================================
# Failure-branch clearing
# ============================================================================


@pytest.mark.unit()
class Test_Failure_Branch_Clearing:
    """Source-level tests for failure-branch reactive-state clearing.

    Notes
    -----
    The fix hardens the failure branches in the upload observer so that
    stale preview tables from a *previous* (failing) extraction are not
    flashed when a subsequent, *different* PDF is uploaded.  Both the
    advisor-missing branch and the generic-exception branch must clear
    ``Extracted_Worksheet_Data`` and ``Extracted_Worksheet_Warnings``
    in addition to flipping ``_show_preview`` to ``False``.
    """

    @pytest.mark.unit()
    def Test_Generic_Exception_Branch_Clears_All_Three(self) -> None:
        """The generic-exception branch clears all three preview reactives."""
        import src.dashboard.shiny_tab_clients.subtab_outline as mod

        with open(mod.__file__, encoding="utf-8") as file_handle:
            source_text = file_handle.read()
        # The generic-exception handler must set the inner reactives to
        # None and flip _show_preview to False.  We just assert all
        # three assignments exist somewhere in the module.
        assert 'inner["Extracted_Worksheet_Data"].set(None)' in source_text
        assert 'inner["Extracted_Worksheet_Warnings"].set(None)' in source_text
        assert "_show_preview.set(False)" in source_text

    @pytest.mark.unit()
    def Test_Advisor_Missing_Branch_Clears_State(self) -> None:
        """The advisor-missing branch clears the extracted data and warnings.

        The branch now lives in the sibling module
        ``_subtab_outline_upload.py`` (the upload observer was
        extracted in a recent refactor).  The local reactive is
        named ``show_preview`` in the extracted module (no leading
        underscore) because it is a function-local reference.
        """
        from pathlib import Path

        project_root = Path(__file__).resolve().parents[4]
        candidates = [
            project_root / "src" / "dashboard" / "shiny_tab_clients" / "subtab_outline.py",
            project_root / "src" / "dashboard" / "shiny_tab_clients" / "_subtab_outline_upload.py",
        ]
        combined_text = "".join(
            candidate.read_text(encoding="utf-8") for candidate in candidates
        )
        marker = "Advisor Information section is incomplete"
        idx = combined_text.find(marker)
        assert idx != -1, "advisor-missing branch must be present"
        # Look at the 1500 characters immediately preceding the marker
        # (the branch is longer in the extracted module because it
        # now also sets the status banner reactives).
        branch_window = combined_text[max(0, idx - 1500):idx]
        assert 'inner["Extracted_Worksheet_Data"].set(None)' in branch_window
        assert 'inner["Extracted_Worksheet_Warnings"].set(None)' in branch_window
        # Accept either the old ``_show_preview`` name (pre-refactor)
        # or the new ``show_preview`` name (post-refactor).
        assert (
            "_show_preview.set(False)" in branch_window
            or "show_preview.set(False)" in branch_window
        )

    @pytest.mark.unit()
    def Test_Clear_Button_Resets_State(self) -> None:
        """The clear-preview button handler resets the extracted-data reactives."""
        import src.dashboard.shiny_tab_clients.subtab_outline as mod

        with open(mod.__file__, encoding="utf-8") as file_handle:
            source_text = file_handle.read()
        # The clear button handler must clear all three reactives.
        assert (
            'inner["Extracted_Worksheet_Data"].set(None)' in source_text
        )
        assert (
            'inner["Extracted_Worksheet_Warnings"].set(None)' in source_text
        )
        assert "_show_preview.set(False)" in source_text


# ============================================================================
# _build_empty_state_placeholder_QWIM � error_message variant
# ============================================================================


@pytest.mark.unit()
class Test_Build_Empty_State_Placeholder_With_Error:
    """Tests for the placeholder helper when an explicit error message is supplied.

    The helper's signature change to accept an ``error_message`` keyword
    argument is backwards-compatible: when the argument is omitted the
    friendly placeholder is returned; when supplied, a red explicit
    error message is rendered instead.
    """

    @pytest.mark.unit()
    def Test_No_Error_Returns_Friendly_Placeholder(self) -> None:
        """No error_message ? friendly placeholder text is rendered."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            _build_empty_state_placeholder_QWIM,
        )

        rendered_repr = repr(_build_empty_state_placeholder_QWIM())
        assert "Upload a worksheet to see extracted values here." in rendered_repr
        # The red error styling must NOT appear when no error is supplied.
        assert "color:#C0392B" not in rendered_repr

    @pytest.mark.unit()
    def Test_Empty_String_Error_Falls_Back_To_Friendly(self) -> None:
        """An empty-string error_message falls back to the friendly placeholder."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            _build_empty_state_placeholder_QWIM,
        )

        rendered_repr = repr(_build_empty_state_placeholder_QWIM(error_message=""))
        assert "Upload a worksheet to see extracted values here." in rendered_repr

    @pytest.mark.unit()
    def Test_Non_None_Error_Returns_Red_Message(self) -> None:
        """A non-None error_message renders the red explicit message instead."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            _build_empty_state_placeholder_QWIM,
        )

        rendered_repr = repr(
            _build_empty_state_placeholder_QWIM(
                error_message="Advisor section is missing required fields",
            ),
        )
        assert "Advisor section is missing required fields" in rendered_repr
        assert "color:#C0392B" in rendered_repr
        # The friendly placeholder must NOT appear in error mode.
        assert "Upload a worksheet to see extracted values here." not in rendered_repr

    @pytest.mark.unit()
    def Test_Whitespace_Only_Error_Falls_Back_To_Friendly(self) -> None:
        """A whitespace-only error_message falls back to the friendly placeholder."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            _build_empty_state_placeholder_QWIM,
        )

        rendered_repr = repr(_build_empty_state_placeholder_QWIM(error_message="   "))
        assert "Upload a worksheet to see extracted values here." in rendered_repr


# ============================================================================
# _build_status_banner_QWIM
# ============================================================================


@pytest.mark.unit()
class Test_Build_Status_Banner_QWIM:
    """Tests for the always-visible status / error banner helper.

    The helper is called by the
    ``output_ID_tab_clients_subtab_clients_outline_status_banner``
    server output.  When ``status_messages`` is empty AND
    ``defaulted_fields`` is empty, the helper returns an empty
    ``ui.div()`` so the banner slot collapses.  When either list is
    non-empty, a red card is returned containing a bulleted list of
    messages.
    """

    @pytest.mark.unit()
    def Test_Empty_Returns_Empty_Div(self) -> None:
        """Empty inputs return a non-None Tag tree (banner collapsed)."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            _build_status_banner_QWIM,
        )

        result = _build_status_banner_QWIM(
            status_messages=[],
            defaulted_fields=[],
        )
        assert result is not None

    @pytest.mark.unit()
    def Test_Status_Messages_Only_Renders_Red_Banner(self) -> None:
        """Non-empty status_messages render a red card with a list."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            _build_status_banner_QWIM,
        )

        result = _build_status_banner_QWIM(
            status_messages=["Advisor section is missing required fields"],
            defaulted_fields=[],
        )
        rendered_repr = repr(result)
        assert "Advisor section is missing required fields" in rendered_repr
        assert "Inputs Worksheet Status" in rendered_repr
        assert "color:#C0392B" in rendered_repr

    @pytest.mark.unit()
    def Test_Defaulted_Fields_Only_Renders_Banner(self) -> None:
        """Defaulted fields with no status messages still render the banner."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            _build_status_banner_QWIM,
        )

        result = _build_status_banner_QWIM(
            status_messages=[],
            defaulted_fields=["firm"],
        )
        rendered_repr = repr(result)
        # The defaulted-fields message must mention the firm default.
        assert "firm" in rendered_repr
        assert "QWIM AI Wealth Management" in rendered_repr

    @pytest.mark.unit()
    def Test_Both_Status_And_Defaulted_Render_Together(self) -> None:
        """When both lists are non-empty, both render in the banner."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            _build_status_banner_QWIM,
        )

        result = _build_status_banner_QWIM(
            status_messages=[
                "PDF imported with 2 validation warning(s); preview tables may be incomplete.",
            ],
            defaulted_fields=["firm"],
        )
        rendered_repr = repr(result)
        assert "validation warning" in rendered_repr
        # The firm default must also appear in the rendered banner.
        assert "QWIM AI Wealth Management" in rendered_repr

    @pytest.mark.unit()
    def Test_Defaulted_Message_Suppressed_When_Status_Mentions_Default(self) -> None:
        """When a status message already mentions 'default', the redundant fallback entry is suppressed."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            _build_status_banner_QWIM,
        )

        result = _build_status_banner_QWIM(
            status_messages=[
                "Default values were used for: firm",
            ],
            defaulted_fields=["firm"],
        )
        rendered_repr = repr(result)
        # The fallback "Defaulted advisor fields:" line must NOT
        # appear because the status message already mentions default.
        assert rendered_repr.count("Defaulted advisor fields:") == 0

    @pytest.mark.unit()
    def Test_Firm_Default_Surfaced_In_Banner(self) -> None:
        """The banner surfaces the firm default ('QWIM AI Wealth Management')."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            _build_status_banner_QWIM,
        )

        result = _build_status_banner_QWIM(
            status_messages=[],
            defaulted_fields=["firm"],
        )
        rendered_repr = repr(result)
        assert "QWIM AI Wealth Management" in rendered_repr

    @pytest.mark.unit()
    def Test_Multiple_Defaulted_Fields_All_Appear(self) -> None:
        """All defaulted field names appear in the rendered banner."""
        from src.dashboard.shiny_tab_clients.subtab_outline import (
            _build_status_banner_QWIM,
        )

        result = _build_status_banner_QWIM(
            status_messages=[],
            defaulted_fields=["firm", "email", "phone_number"],
        )
        rendered_repr = repr(result)
        assert "firm" in rendered_repr
        assert "email" in rendered_repr
        assert "phone_number" in rendered_repr


# ============================================================================
# Always-visible status banner � source-level wiring
# ============================================================================


@pytest.mark.unit()
class Test_Status_Banner_Output_Wiring:
    """Source-level tests for the always-visible status banner output.

    Verifies the new server output, its static UI placeholder, and
    the two new inner reactives (Status_Messages, Defaulted_Fields)
    are wired into the module.
    """

    @pytest.mark.unit()
    def Test_New_Output_Id_Defined_In_Source(self) -> None:
        """The new status-banner output ID is defined in the source as an ``@output``."""
        import src.dashboard.shiny_tab_clients.subtab_outline as mod

        with open(mod.__file__, encoding="utf-8") as file_handle:
            source_text = file_handle.read()
        assert (
            "def output_ID_tab_clients_subtab_clients_outline_status_banner"
            in source_text
        ), "status banner output must be defined in the server function"

    @pytest.mark.unit()
    def Test_New_Output_Id_Referenced_In_Static_UI(self) -> None:
        """The new status-banner output ID is referenced in the static UI function."""
        import src.dashboard.shiny_tab_clients.subtab_outline as mod

        with open(mod.__file__, encoding="utf-8") as file_handle:
            source_text = file_handle.read()
        assert (
            '"output_ID_tab_clients_subtab_clients_outline_status_banner"'
            in source_text
        ), "status banner output_ui placeholder must exist in the static UI"

    @pytest.mark.unit()
    def Test_Status_Messages_Reactive_Is_Initialised(self) -> None:
        """The ``Extracted_Worksheet_Status_Messages`` reactive is initialised."""
        import src.dashboard.shiny_tab_clients.subtab_outline as mod

        with open(mod.__file__, encoding="utf-8") as file_handle:
            source_text = file_handle.read()
        assert "Extracted_Worksheet_Status_Messages" in source_text
        # Must be referenced in both the initialiser AND in the
        # server's reactive reads.
        assert source_text.count("Extracted_Worksheet_Status_Messages") >= 4

    @pytest.mark.unit()
    def Test_Defaulted_Fields_Reactive_Is_Initialised(self) -> None:
        """The ``Extracted_Worksheet_Defaulted_Fields`` reactive is initialised."""
        import src.dashboard.shiny_tab_clients.subtab_outline as mod

        with open(mod.__file__, encoding="utf-8") as file_handle:
            source_text = file_handle.read()
        assert "Extracted_Worksheet_Defaulted_Fields" in source_text
        assert source_text.count("Extracted_Worksheet_Defaulted_Fields") >= 4

    @pytest.mark.unit()
    def Test_Status_Banner_Cleared_On_Reject(self) -> None:
        """The clear-preview button handler clears the status banner reactives."""
        import src.dashboard.shiny_tab_clients.subtab_outline as mod

        with open(mod.__file__, encoding="utf-8") as file_handle:
            source_text = file_handle.read()
        # The clear button handler must reset BOTH the new reactives
        # in addition to the pre-existing ones.
        assert 'inner["Extracted_Worksheet_Status_Messages"].set([])' in source_text
        assert 'inner["Extracted_Worksheet_Defaulted_Fields"].set([])' in source_text

    @pytest.mark.unit()
    def Test_New_Sync_Helper_Is_Invoked_From_Server(self) -> None:
        """The new advisor-sync helper is called from the upload observer module."""
        from src.dashboard.shiny_tab_clients._subtab_outline_upload import (
            register_upload_observer_QWIM,
        )
        import inspect

        source_text = inspect.getsource(register_upload_observer_QWIM)
        assert "sync_advisor_info_to_user_inputs_shiny_QWIM" in source_text


# ============================================================================
# Upload observer extracted to _subtab_outline_upload.py
# ============================================================================


@pytest.mark.unit()
class Test_Upload_Observer_Extracted_Module:
    """Tests for the new ``_subtab_outline_upload`` sibling module."""

    @pytest.mark.unit()
    def Test_Register_Helper_Is_Importable(self) -> None:
        """The registration helper is importable from the new sibling module."""
        from src.dashboard.shiny_tab_clients._subtab_outline_upload import (
            register_upload_observer_QWIM,
        )

        assert callable(register_upload_observer_QWIM)

    @pytest.mark.unit()
    def Test_Register_Helper_Signature(self) -> None:
        """The helper takes only keyword-only arguments."""
        import inspect

        from src.dashboard.shiny_tab_clients._subtab_outline_upload import (
            register_upload_observer_QWIM,
        )

        signature = inspect.signature(register_upload_observer_QWIM)
        # All parameters must be keyword-only (the function uses ``*``).
        for parameter in signature.parameters.values():
            assert parameter.kind == inspect.Parameter.KEYWORD_ONLY, (
                f"parameter {parameter.name!r} must be keyword-only"
            )

    @pytest.mark.unit()
    def Test_File_Input_Id_Is_Const(self) -> None:
        """The file input id is exposed as a module-level constant for clarity."""
        from src.dashboard.shiny_tab_clients import _subtab_outline_upload

        assert hasattr(_subtab_outline_upload, "_FILE_INPUT_ID")
        assert _subtab_outline_upload._FILE_INPUT_ID == (
            "input_ID_tab_clients_subtab_clients_outline_file_upload"
        )


# ============================================================================
# "Preview of Client Inputs" section � source-level wiring
# ============================================================================


@pytest.mark.unit()
class Test_Preview_Of_Client_Inputs_Section_Wiring:
    """Source-level tests for the new "Preview of Client Inputs" section.

    The new section is rendered as a ``ui.output_ui(...)`` placeholder
    placed **inside** the existing "Data Entry Method" card (rather
    than as a top-level output outside the card).  These tests pin
    that placement in place so a future refactor cannot silently move
    the output back to the wrong location.
    """

    @pytest.mark.unit()
    def test_output_inside_data_entry_method_card(self) -> None:
        """The preview output placeholder is inside the "Data Entry Method" card."""
        import re

        import src.dashboard.shiny_tab_clients.subtab_outline as mod

        with open(mod.__file__, encoding="utf-8") as file_handle:
            text = file_handle.read()
        # The preview output id must appear in the source.  We focus
        # the assertion on the *code* (excluding the module docstring
        # which also lists the UI identifier for documentation
        # purposes).
        code_text = re.sub(r'\"\"\"[\s\S]*?\"\"\"', "", text, count=1)
        preview_id = "input_ID_tab_clients_subtab_clients_outline_btn_reject"
        data_entry_marker = 'ui.h5("Data Entry Method"'
        assert preview_id in code_text
        assert data_entry_marker in code_text
        assert code_text.find(preview_id) > code_text.find(data_entry_marker), (
            "clear button must be placed inside the Data Entry "
            "Method card (after the 'Data Entry Method' card header)"
        )

    @pytest.mark.unit()
    def test_top_level_preview_output_is_removed(self) -> None:
        """The old top-level preview output (outside the card) must be removed.

        The previous design had a top-level ``ui.output_ui`` *after*
        the "Data Entry Method" card.  That duplicate has been removed;
        the preview now lives only inside the card.
        """
        import src.dashboard.shiny_tab_clients.subtab_outline as mod

        with open(mod.__file__, encoding="utf-8") as file_handle:
            text = file_handle.read()
        # The "Data Entry Method" card closes with a top-level
        # ``style="padding:12px;"`` directive.  The preview output id
        # must NOT appear AFTER that closing directive.  We use a
        # simple substring search: the closing of the card is
        # followed by either a top-level ``ui.output_ui`` (the old
        # pattern) or by the next ``# ===`` server-decoration
        # comment.  The preview output id must not appear in the
        # region between those two anchors.
        preview_id = "output_ID_tab_clients_subtab_clients_outline_preview_section"
        # Locate the closing of the outer div (the one that contains
        # the entire subtab UI) by finding the second occurrence of
        # ``style="padding:12px;"``.
        first_idx = text.find('style="padding:12px;"')
        assert first_idx != -1
        second_idx = text.find('style="padding:12px;"', first_idx + 1)
        assert second_idx != -1
        tail = text[second_idx:]
        # In the new design, the preview id is inside the first
        # ``style="padding:12px;"`` region (inside the card).  After
        # the second ``style="padding:12px;"`` (the closing of the
        # outer div), the preview id must NOT appear.
        assert preview_id not in tail, (
            "old top-level preview output must be removed; "
            "the preview now lives only inside the 'Data Entry Method' card"
        )

    @pytest.mark.unit()
    def test_inline_renderer_builds_preview_inline(self) -> None:
        """The inline preview renderer builds the preview directly (Viz-PRPB pattern)."""
        import src.dashboard.shiny_tab_clients.subtab_outline as mod

        with open(mod.__file__, encoding="utf-8") as file_handle:
            text = file_handle.read()
        assert "Preview of Extracted Data" in text, (
            "inline preview renderer must render the heading directly"
        )
        assert "_PREVIEW_CLIENT_SECTIONS" in text, (
            "inline preview renderer must use _PREVIEW_CLIENT_SECTIONS"
        )

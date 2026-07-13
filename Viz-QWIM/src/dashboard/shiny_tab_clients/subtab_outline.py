"""Client Outline Subtab Module.

Provides an introductory view for the Clients tab of the QWIM dashboard.
Users choose between manual data entry and uploading a pre-filled
Retirement Income Worksheet PDF.  When a PDF is uploaded, the extracted
data is validated and used to auto-populate the other subtab inputs.
Preview tables remain available for review after import.

UI Identifiers
--------------
- ``input_ID_tab_clients_subtab_clients_outline_input_mode`` — dropdown
- ``input_ID_tab_clients_subtab_clients_outline_file_upload`` — file input
- ``input_ID_tab_clients_subtab_clients_outline_btn_reject`` — reject button
- ``output_ID_tab_clients_subtab_clients_outline_imported_summary`` — in-card
  verification tables (Personal Info, Assets, Goals, Income) under the
  "Data Entry Method" card.  When no PDF has been uploaded, the renderer
  emits a one-line placeholder ("Upload a worksheet to see extracted
  values here.") instead of an empty ``ui.div``.
- ``output_ID_tab_clients_subtab_clients_outline_status_banner`` — always-visible
  red status / error banner rendered inside the "Data Entry Method" card.
  Hidden when no errors or warnings are present.
- ``output_ID_tab_clients_subtab_clients_outline_preview_section`` — full
  preview of the extracted data with per-section tables (Personal Info,
  Assets, Goals, Income), rendered as the "Preview of Client Inputs"
  section inside the "Data Entry Method" card.  Uses the friendly
  placeholder when no PDF has been uploaded.

Author
------
QWIM Team

Version
-------
0.6.0 (2026-04-04)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from shiny import module, reactive, render, ui

from src.clients_QWIM.utils_client import (
    _ADVISOR_INFO_DEFAULT_VALUES,
    extract_client_data_from_worksheet_PDF,
    validate_extracted_client_data,
    validate_required_advisor_info_section,
    worksheet_has_client_partner,
)
from src.dashboard.shiny_tab_setup.subtab_advisor_info import (
    DEFAULT_VALUES_ADVISOR_INFO,
)
from src.dashboard.shiny_utils._utils_tab_clients_sync import (
    sync_advisor_info_to_user_inputs_shiny_QWIM,
)
from src.dashboard.shiny_utils.reactives_initialization import (
    create_reactive_value_safely,
)
from src.dashboard.shiny_utils.utils_tab_clients import (
    sync_user_inputs_shiny_from_extracted_worksheet,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

_logger = get_logger(name = __name__)


# ===================================================================
# Internal helpers — pure functions (unit-testable, no Shiny context)
# ===================================================================


def _apply_default_firm_fallback_to_extracted_worksheet(
    *,
    extracted_worksheet_data: dict[str, Any],
    reactives_shiny: dict[str, Any],
) -> bool:
    """Populate ``Advisor_Info.firm`` with the dashboard's current default when missing.

    The Inputs Worksheet PDF does not include a ``Firm`` field; when the user
    uploads such a PDF, the blocking validator
    :func:`validate_required_advisor_info_section` would otherwise reject the
    import with *"Firm is missing"*.  This helper applies a fallback so the
    dashboard accepts the import and uses the firm the user has currently
    entered in **Setup -> Advisor Info**.
    """
    if not isinstance(extracted_worksheet_data, dict):
        return False

    advisor_info = extracted_worksheet_data.get("Advisor_Info")
    if not isinstance(advisor_info, dict):
        return False

    firm_existing = advisor_info.get("firm")
    if isinstance(firm_existing, str) and firm_existing.strip():
        return False

    firm_default: str = ""
    advisor_info_reactive_category = reactives_shiny.get("Advisor_Info")
    if isinstance(advisor_info_reactive_category, dict):
        firm_reactive = advisor_info_reactive_category.get("Firm")
        if firm_reactive is not None and hasattr(firm_reactive, "get"):
            try:
                firm_reactive_value = firm_reactive.get()
            except Exception:
                firm_reactive_value = None
            if isinstance(firm_reactive_value, str) and firm_reactive_value.strip():
                firm_default = firm_reactive_value.strip()

    if not firm_default:
        firm_default = DEFAULT_VALUES_ADVISOR_INFO.get("Firm", "").strip()

    if not firm_default:
        return False

    advisor_info["firm"] = firm_default
    return True


# ===================================================================
# UI
# ===================================================================

@module.ui
def subtab_clients_outline_ui(  # pragma: no cover
    data_utils: dict[str, Any],
    data_inputs: dict[str, Any],
) -> Any:
    """Build the UI for the Clients > Outline subtab.

    Parameters
    ----------
    data_utils : dict[str, Any]
        Shared data-utility objects for the dashboard.
    data_inputs : dict[str, Any]
        Default dashboard input values.

    Returns
    -------
    Any
        A Shiny UI element tree for the Outline subtab.
    """
    return ui.div(
        # --- Introduction ---
        ui.card(
            ui.card_header(
                ui.h4(
                    "Client Information Overview",
                    style="margin:0;color:#2C3E50;",
                ),
            ),
            ui.card_body(
                ui.markdown(
                    """
The **Clients** tab collects the information required to build a
personalised retirement income plan.  Four categories of data are
gathered across the subtabs that follow:

- **Personal Information** — names, ages, retirement age, annuity income starting age, marital status, risk tolerance, and location.
- **Assets** — investable, taxable, tax-deferred, and tax-free assets for each client.
- **Goals** — annual essential, important, and aspirational expense targets.
- **Income** — Social Security, pension, annuity, and other income sources with inflation-indexing flags.

You may enter this data **manually** in each subtab, or **upload a
completed Retirement Income Worksheet PDF** to pre-populate all fields
automatically.
""",
                ),
            ),
        ),
        # --- Input mode selector + file upload (side by side) ---
        ui.card(
            ui.card_header(
                ui.h5("Data Entry Method", style="margin:0;color:#2C3E50;"),
            ),
            ui.card_body(
                ui.layout_columns(
                    ui.input_select(
                        id="input_ID_tab_clients_subtab_clients_outline_input_mode",
                        label="How would you like to provide client information?",
                        choices={
                            "manual": "Manual Input (enter data in each subtab)",
                            "pdf_upload": "Upload Inputs Worksheet PDF",
                        },
                        selected="pdf_upload",
                        width="100%",
                    ),
                    # Conditional upload section (rendered server-side)
                    ui.output_ui(
                        "output_ID_tab_clients_subtab_clients_outline_upload_section",
                    ),
                    col_widths=(6, 6),
                ),
                # --- In-card verification / status ---
                ui.output_ui(
                    "output_ID_tab_clients_subtab_clients_outline_imported_summary",
                ),
                ui.output_ui(
                    "output_ID_tab_clients_subtab_clients_outline_status_banner",
                ),
            ),
        ),
        style="padding:12px;",
    )


# ===================================================================
# Server
# ===================================================================

@module.server
def subtab_clients_outline_server(  # pragma: no cover
    input: Any,
    output: Any,
    session: Any,
    data_utils: dict[str, Any],
    data_inputs: dict[str, Any],
    reactives_shiny: dict[str, Any],
) -> None:
    """Server logic for the Outline subtab.

    Handles file upload, extraction, validation, preview rendering, and
    auto-population of extracted data to ``reactives_shiny`` for
    consumption by other subtabs.
    """
    # --- Reactive initialisation ---
    inner = reactives_shiny.setdefault("Inner_Variables_Shiny", {})
    triggers = reactives_shiny.setdefault("Triggers_Shiny", {})

    if "Extracted_Worksheet_Data" not in inner:
        inner["Extracted_Worksheet_Data"] = create_reactive_value_safely(initial_value=None)
    if "Extracted_Worksheet_Warnings" not in inner:
        inner["Extracted_Worksheet_Warnings"] = create_reactive_value_safely(initial_value=None)
    if "Extracted_Worksheet_Has_Client_Partner" not in inner:
        inner["Extracted_Worksheet_Has_Client_Partner"] = create_reactive_value_safely(
            initial_value=True,
        )
    if "Extracted_Worksheet_Status_Messages" not in inner:
        inner["Extracted_Worksheet_Status_Messages"] = create_reactive_value_safely(
            initial_value=[],
        )
    if "Extracted_Worksheet_Defaulted_Fields" not in inner:
        inner["Extracted_Worksheet_Defaulted_Fields"] = create_reactive_value_safely(
            initial_value=[],
        )
    if "Trigger_Populate_From_Worksheet" not in triggers:
        triggers["Trigger_Populate_From_Worksheet"] = create_reactive_value_safely(initial_value=0)

    _show_preview: reactive.Value[bool] = reactive.Value(False)

    # ------------------------------------------------------------------
    # Conditional upload section (Viz-PRPB pattern — FIRST output)
    # ------------------------------------------------------------------
    @output
    @render.ui
    def output_ID_tab_clients_subtab_clients_outline_upload_section():
        mode = input.input_ID_tab_clients_subtab_clients_outline_input_mode()
        if mode != "pdf_upload":
            return ui.div()

        return ui.div(
            ui.input_file(
                id="input_ID_tab_clients_subtab_clients_outline_file_upload",
                label="Upload a completed Inputs Worksheet PDF:",
                accept=[".pdf"],
                multiple=False,
                width="100%",
            ),
        )

    # ------------------------------------------------------------------
    # Process uploaded file (Viz-PRPB pattern — effect after upload output)
    # ------------------------------------------------------------------
    @reactive.effect
    @reactive.event(input.input_ID_tab_clients_subtab_clients_outline_file_upload)
    def _on_file_upload():
        file_info = input.input_ID_tab_clients_subtab_clients_outline_file_upload()
        if file_info is None or len(file_info) == 0:
            return

        uploaded = file_info[0]
        file_path = Path(uploaded["datapath"])

        try:
            extracted = extract_client_data_from_worksheet_PDF(pdf_path=file_path)

            firm_fallback_applied = _apply_default_firm_fallback_to_extracted_worksheet(
                extracted_worksheet_data=extracted,
                reactives_shiny=reactives_shiny,
            )
            if firm_fallback_applied:
                _logger.info(
                    "Firm missing in uploaded PDF; applied default before advisor-info validation.",
                )

            advisor_info_validation_messages = validate_required_advisor_info_section(
                extracted_data=extracted,
            )
            if len(advisor_info_validation_messages) > 0:
                inner["Extracted_Worksheet_Data"].set(None)
                inner["Extracted_Worksheet_Warnings"].set(None)
                inner["Extracted_Worksheet_Status_Messages"].set(
                    list(advisor_info_validation_messages),
                )
                inner["Extracted_Worksheet_Defaulted_Fields"].set([])
                _show_preview.set(False)
                ui.modal_show(
                    ui.modal(
                        ui.p(
                            "The uploaded Inputs Worksheet PDF cannot be imported because the Advisor Information section is incomplete.",
                            style="font-size:1.0rem;",
                        ),
                        ui.tags.ul(
                            *[ui.tags.li(message) for message in advisor_info_validation_messages],
                        ),
                        title="Advisor Information Missing or Invalid",
                        easy_close=True,
                        footer=ui.modal_button("OK"),
                    ),
                )
                return

            is_valid, warnings = validate_extracted_client_data(extracted_data=extracted)
            has_client_partner = worksheet_has_client_partner(extracted_data=extracted)

            inner["Extracted_Worksheet_Data"].set(extracted)
            inner["Extracted_Worksheet_Warnings"].set(warnings)
            inner["Extracted_Worksheet_Has_Client_Partner"].set(has_client_partner)
            sync_user_inputs_shiny_from_extracted_worksheet(
                reactives_shiny=reactives_shiny,
                extracted_worksheet_data=extracted,
                has_client_partner=has_client_partner,
            )

            # Sync advisor info to User_Inputs_Shiny (Setup > Advisor Info tab)
            defaulted_fields = sync_advisor_info_to_user_inputs_shiny_QWIM(
                reactives_shiny=reactives_shiny,
                extracted_worksheet_data=extracted,
            )

            # Build status banner messages
            status_msgs: list[str] = []
            if not is_valid:
                status_msgs.append(
                    f"PDF imported with {len(warnings)} validation warning(s); "
                    "preview tables may be incomplete.",
                )
            if defaulted_fields:
                labels = [
                    f"{field_key} (used default '{_ADVISOR_INFO_DEFAULT_VALUES.get(field_key, '')}')"
                    for field_key in defaulted_fields
                ]
                status_msgs.append(
                    "Defaulted advisor fields (not in PDF): " + ", ".join(labels) + ".",
                )
            inner["Extracted_Worksheet_Status_Messages"].set(status_msgs)
            inner["Extracted_Worksheet_Defaulted_Fields"].set(defaulted_fields)
            _show_preview.set(True)

            current = triggers["Trigger_Populate_From_Worksheet"].get() or 0
            triggers["Trigger_Populate_From_Worksheet"].set(current + 1)

            if not is_valid:
                ui.notification_show(
                    f"PDF extracted with {len(warnings)} validation warning(s). "
                    "Dashboard inputs were populated. Please review the imported data.",
                    type="warning",
                    duration=8,
                )
            else:
                ui.notification_show(
                    "PDF data extracted successfully and dashboard inputs were populated.",
                    type="message",
                    duration=5,
                )

        except Exception as exc:
            _logger.opt(exception=True).error("PDF extraction failed: {}", exc)
            inner["Extracted_Worksheet_Data"].set(None)
            inner["Extracted_Worksheet_Warnings"].set(None)
            inner["Extracted_Worksheet_Defaulted_Fields"].set([])
            inner["Extracted_Worksheet_Status_Messages"].set(
                [f"Failed to extract data from PDF: {exc}"],
            )
            _show_preview.set(False)
            ui.notification_show(
                f"Failed to extract data from PDF: {exc}",
                type="error",
                duration=10,
            )

    # ------------------------------------------------------------------
    # Remaining @output definitions
    # ------------------------------------------------------------------

    # --- Imported Values Summary ---
    @output
    @render.ui
    def output_ID_tab_clients_subtab_clients_outline_imported_summary():
        show = _show_preview()
        data = inner["Extracted_Worksheet_Data"].get()
        if not show or data is None:
            return ui.div()
        return build_imported_summary_tables_QWIM(extracted_data=data)

    # --- Always-visible status banner ---
    @output
    @render.ui
    def output_ID_tab_clients_subtab_clients_outline_status_banner():
        status_messages = inner["Extracted_Worksheet_Status_Messages"].get() or []
        defaulted_fields = inner["Extracted_Worksheet_Defaulted_Fields"].get() or []
        return _build_status_banner_QWIM(
            status_messages=list(status_messages),
            defaulted_fields=list(defaulted_fields),
        )

    # ------------------------------------------------------------------
    # Clear preview handler
    # ------------------------------------------------------------------
    @reactive.effect
    @reactive.event(input.input_ID_tab_clients_subtab_clients_outline_btn_reject)
    def _on_reject():
        inner["Extracted_Worksheet_Data"].set(None)
        inner["Extracted_Worksheet_Warnings"].set(None)
        inner["Extracted_Worksheet_Status_Messages"].set([])
        inner["Extracted_Worksheet_Defaulted_Fields"].set([])
        _show_preview.set(False)
        ui.notification_show("Extracted data cleared.", type="message", duration=3)


# ===================================================================
# Internal helpers — preview table builder
# ===================================================================


def _build_empty_state_placeholder_QWIM(
    *,
    error_message: str | None = None,
) -> Any:
    """Build the shared empty-state placeholder for the Outline subtab previews.

    Parameters
    ----------
    error_message : str or None
        Optional explicit error / warning message to display instead
        of the friendly "upload a worksheet" prompt.  When supplied,
        the placeholder is rendered in red and contains the message
        verbatim.  When ``None`` (the default), the friendly
        placeholder is returned.  Used by the Outline subtab server
        to make the user-visible reason for a missing preview
        explicit.

    Returns
    -------
    shiny.ui.div
        A small placeholder Tag tree instructing the user either to
        upload an Inputs Worksheet PDF (default) or showing the
        explicit error / warning that prevented the preview from
        being rendered.  The same helper is used by both the in-card
        Imported Values Summary output and the larger Preview section
        output whenever ``Extracted_Worksheet_Data`` is ``None`` or
        the ``_show_preview`` flag is ``False``.

    Notes
    -----
    Pure function: it does not touch any reactive state, so it can be
    unit-tested in isolation by calling it directly and asserting on
    the returned Tag tree.  The function uses ``ui.p(...)`` (not
    ``ui.tags.p(...)``) and explicit inline styling so the rendered
    HTML is robust to Shiny 1.6.1 quirks where ``ui.tags.*`` may not
    serialise to a visible ``<p>`` element in all output contexts.
    """
    if error_message is not None and str(error_message).strip():
        return ui.div(
            ui.p(
                str(error_message),
                style=(
                    "font-size:0.85rem;color:#C0392B;margin:14px 0 6px 0;"
                    "font-weight:600;"
                ),
            ),
            style="padding:4px 0;",
        )
    return ui.div(
        ui.p(
            "Upload a worksheet to see extracted values here.",
            style=(
                "font-size:0.85rem;color:#566573;margin:14px 0 6px 0;"
                "font-style:italic;"
            ),
        ),
        style="padding:4px 0;",
    )


def _build_status_banner_QWIM(
    *,
    status_messages: list[str],
    defaulted_fields: list[str],
) -> Any:
    """Build the always-visible status / error banner for the Outline subtab.

    Parameters
    ----------
    status_messages : list[str]
        Human-readable error / warning messages collected during
        extraction.  Each message is rendered as a bullet point inside
        the red banner card.
    defaulted_fields : list[str]
        Names of advisor fields for which the parser applied the
        default value (because the PDF omitted them).  Used to
        explicitly surface the firm default ("QWIM AI Wealth
        Management") to the user.

    Returns
    -------
    shiny.ui.div or shiny.ui.card
        An empty ``ui.div()`` when there is nothing to report (so the
        banner slot collapses to zero height), or a red ``ui.card``
        with a bulleted list of messages.

    Notes
    -----
    Pure function: no reactive state is touched.  Used by the
    ``output_ID_tab_clients_subtab_clients_outline_status_banner``
    renderer in the Outline subtab server.  Extracted as a
    module-level helper to keep the server function under the 1000
    line cap and to make the banner construction directly
    unit-testable.
    """
    if not status_messages and not defaulted_fields:
        return ui.div()

    message_items: list[Any] = [
        ui.tags.li(message) for message in status_messages
    ]
    if defaulted_fields and not any(
        "default" in message.lower() for message in status_messages
    ):
        # Edge case: defaulted fields exist but the message list
        # was cleared (e.g. by a subsequent successful upload).  We
        # still want to surface the firm default explicitly because
        # the user explicitly requested it.
        default_labels = [
            f"{field_key} (default '{_ADVISOR_INFO_DEFAULT_VALUES.get(field_key, '')}')"
            for field_key in defaulted_fields
        ]
        message_items.append(
            ui.tags.li(
                "Defaulted advisor fields: " + ", ".join(default_labels),
            ),
        )

    return ui.card(
        ui.card_header(
            ui.h5(
                "Inputs Worksheet Status",
                style="margin:0;color:#E74C3C;",
            ),
        ),
        ui.card_body(
            ui.tags.ul(
                *message_items,
                style="color:#C0392B;font-size:0.9rem;margin-bottom:0;",
            ),
        ),
        style="border:1px solid #E74C3C;margin-top:8px;",
    )


def _build_preview_table(
    section_title: str,
    section_data: dict[str, Any],
) -> Any | None:
    """Build a card with an HTML table showing extracted field values.

    Parameters
    ----------
    section_title : str
        Display title for the section.
    section_data : dict
        ``{"client_primary": {...}, "client_partner": {...}}``.

    Returns
    -------
    ui.card or None
    """
    primary = section_data.get("client_primary", {})
    partner = section_data.get("client_partner", {})

    if not primary and not partner:
        return None

    all_keys = list(dict.fromkeys(list(primary.keys()) + list(partner.keys())))
    if not all_keys:  # pragma: no cover
        return None

    has_partner = bool(partner)

    # Build HTML table rows
    header_cols = [
        ui.tags.th("Field", style="text-align:left;padding:6px 10px;"),
        ui.tags.th("Client Primary", style="text-align:left;padding:6px 10px;"),
    ]
    if has_partner:
        header_cols.append(ui.tags.th("Client Partner", style="text-align:left;padding:6px 10px;"))

    rows = [ui.tags.tr(*header_cols, style="background-color:#E8EDF1;")]

    for key in all_keys:
        val_primary = _format_preview_value(primary.get(key))
        val_partner = _format_preview_value(partner.get(key)) if has_partner else None

        cells = [
            ui.tags.td(
                _humanize_field_key(key),
                style="padding:4px 10px;font-weight:500;",
            ),
            ui.tags.td(val_primary, style="padding:4px 10px;"),
        ]
        if has_partner:
            cells.append(ui.tags.td(val_partner, style="padding:4px 10px;"))

        rows.append(ui.tags.tr(*cells))

    table = ui.tags.table(
        *rows,
        style=("width:100%;border-collapse:collapse;border:1px solid #BDC3C7;font-size:0.92rem;"),
    )

    return ui.card(
        ui.card_header(
            ui.h5(section_title, style="margin:0;color:#2C3E50;"),
        ),
        ui.card_body(table),
    )


def _build_preview_record_table(
    section_title: str,
    section_data: dict[str, Any],
) -> Any | None:
    """Build a single-record preview table for sections like Advisor Information."""
    if not isinstance(section_data, dict) or len(section_data) == 0:
        return None

    rows = [
        ui.tags.tr(
            ui.tags.th("Field", style="text-align:left;padding:6px 10px;"),
            ui.tags.th("Value", style="text-align:left;padding:6px 10px;"),
            style="background-color:#E8EDF1;",
        ),
    ]

    for key, value in section_data.items():
        rows.append(
            ui.tags.tr(
                ui.tags.td(
                    _humanize_field_key(key),
                    style="padding:4px 10px;font-weight:500;",
                ),
                ui.tags.td(_format_preview_value(value), style="padding:4px 10px;"),
            ),
        )

    table = ui.tags.table(
        *rows,
        style=("width:100%;border-collapse:collapse;border:1px solid #BDC3C7;font-size:0.92rem;"),
    )

    return ui.card(
        ui.card_header(
            ui.h5(section_title, style="margin:0;color:#2C3E50;"),
        ),
        ui.card_body(table),
    )


def _format_preview_value(value: Any) -> str:
    """Convert a raw extracted value to a display string."""
    if value is None or value == "":
        return "—"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def _humanize_field_key(key: str) -> str:
    """Convert a snake_case field key to a human-readable label."""
    return (
        key.replace("_", " ")
        .replace("annuity existing", "existing annuity")
        .title()
        .replace("Zip", "ZIP")
    )


# ===================================================================
# Preview section builder (Outline subtab)
# ===================================================================

# Sections rendered as per-client (primary / partner) preview tables.
# Limited to the four core client sections (Personal Information,
# Assets, Goals, Income) per the user's product requirement; the
# advisor info, LTC insurance, life insurance, and contingency
# sections are intentionally omitted from the preview to reduce
# clutter in the Outline subtab.
_PREVIEW_CLIENT_SECTIONS: tuple[tuple[str, str], ...] = (
    ("Personal Information", "Personal_Info"),
    ("Assets", "Assets"),
    ("Goals", "Goals"),
    ("Income", "Income"),
)


def build_preview_section_QWIM(
    *,
    extracted_data: dict[str, Any] | None,
) -> Any:
    """Build the "Preview of Client Inputs" section for the Outline subtab.

    Parameters
    ----------
    extracted_data : dict or None
        The full extracted worksheet payload produced by
        :func:`extract_client_data_from_worksheet_PDF`.  When ``None``
        or empty, an empty placeholder ``ui.div`` is returned so the
        reactive renderer can short-circuit cleanly.

    Returns
    -------
    shiny.ui.Tag
        A vertical stack of preview cards — one per core client
        section (Personal Information, Assets, Goals, Income) —
        wrapped under a "Preview of Client Inputs" heading.  Sections
        with no data are skipped; when nothing can be rendered an
        empty ``ui.div`` is returned.

    Notes
    -----
    The function is pure with respect to its arguments — it does not
    mutate ``extracted_data`` and calls no Shiny reactive primitives,
    so it can be unit-tested in isolation by passing a plain ``dict``
    and asserting on the returned Tag tree.  The implementation
    reuses :func:`_build_preview_table` so display formatting stays
    in lockstep with the imported-summary tables.  Advisor info and
    insurance sections are intentionally omitted from this renderer
    per the user's product requirement; they live in their
    dedicated subtabs instead.
    """
    if not isinstance(extracted_data, dict) or len(extracted_data) == 0:
        return ui.div()

    preview_cards: list[Any] = []

    for section_title, section_key in _PREVIEW_CLIENT_SECTIONS:
        section_data = extracted_data.get(section_key, {})
        if not isinstance(section_data, dict):
            continue
        card_section = _build_preview_table(
            section_title = section_title,
            section_data = section_data,
        )
        if card_section is not None:
            preview_cards.append(card_section)

    if not preview_cards:
        return ui.div()

    return ui.div(
        ui.tags.h5(
            "Preview of Extracted Data",
            style="margin:14px 0 6px 0;color:#2C3E50;font-weight:600;",
        ),
        ui.tags.p(
            "The values below were read from the uploaded PDF and used to "
            "populate the Clients subtabs.",
            style="font-size:0.85rem;color:#566573;margin-bottom:8px;",
        ),
        *preview_cards,
        style="padding:12px;",
    )


# ===================================================================
# Internal helpers — imported values summary (in-card verification tables)
# ===================================================================

# The four client subtabs that have a per-client (primary / partner) layout
# and that are auto-populated by the PDF import flow.  These are the
# sections surfaced as summary tables under the "Data Entry Method" card.
_IMPORTED_SUMMARY_SECTIONS: tuple[tuple[str, str], ...] = (
    ("Personal Information", "Personal_Info"),
    ("Assets", "Assets"),
    ("Goals", "Goals"),
    ("Income", "Income"),
)


def build_imported_summary_tables_QWIM(
    *,
    extracted_data: dict[str, Any] | None,
) -> Any:
    """Build the in-card verification tables for the imported PDF values.

    Parameters
    ----------
    extracted_data : dict or None
        The full extracted worksheet payload as produced by
        :func:`extract_client_data_from_worksheet_PDF`.  When ``None``
        or empty, the function returns an empty placeholder ``ui.div``
        so the reactive renderer can short-circuit cleanly.

    Returns
    -------
    shiny.ui.div
        A vertical stack of four small tables — one per client subtab
        (Personal Information, Assets, Goals, Income) — wrapped in a
        card with the heading "Imported Values Summary".  The four
        tables show "Field / Client Primary / Client Partner" columns
        so the user can verify the imported data visually after
        uploading a PDF.

    Notes
    -----
    The function is pure with respect to its arguments — it does not
    mutate ``extracted_data`` and does not call any Shiny reactive
    primitives, which means it can be unit-tested in isolation by
    passing a plain ``dict`` and asserting on the returned Tag tree.
    The implementation reuses :func:`_format_preview_value` and
    :func:`_humanize_field_key` so display formatting stays in
    lockstep with the existing "Preview of Extracted Data" section.
    """
    if not isinstance(extracted_data, dict) or len(extracted_data) == 0:
        return ui.div()

    rendered_tables: list[Any] = []

    for section_title, section_key in _IMPORTED_SUMMARY_SECTIONS:
        section_data = extracted_data.get(section_key, {})
        if not isinstance(section_data, dict):
            section_data = {}
        table_card = _build_imported_summary_section_card(
            section_title = section_title,
            section_data = section_data,
        )
        if table_card is not None:
            rendered_tables.append(table_card)

    if not rendered_tables:
        return ui.div()

    return ui.div(
        ui.tags.h6(
            "Imported Values Summary",
            style="margin:14px 0 6px 0;color:#2C3E50;font-weight:600;",
        ),
        ui.tags.p(
            "Review the imported values below and confirm they match the entries in the uploaded PDF.",
            style="font-size:0.85rem;color:#566573;margin-bottom:8px;",
        ),
        *rendered_tables,
        ui.div(
            ui.input_action_button(
                id="input_ID_tab_clients_subtab_clients_outline_btn_reject",
                label="Clear Imported Preview",
                class_="btn btn-outline-danger",
            ),
            style="margin-top:16px;margin-bottom:16px;text-align:center;",
        ),
        style="margin-top:8px;",
    )


def _build_imported_summary_section_card(
    *,
    section_title: str,
    section_data: dict[str, Any],
) -> Any | None:
    """Build a single imported-summary card for one client subtab section.

    Parameters
    ----------
    section_title : str
        Human-readable title shown in the card header.
    section_data : dict
        The ``{"client_primary": {...}, "client_partner": {...}}`` sub-dict
        from the extracted worksheet payload.

    Returns
    -------
    shiny.ui.card or None
        A card with a ``Field / Client Primary / Client Partner`` table,
        or ``None`` when the section has neither primary nor partner
        data (so the caller can skip the empty card).
    """
    primary = section_data.get("client_primary", {})
    partner = section_data.get("client_partner", {})

    if not isinstance(primary, dict):
        primary = {}
    if not isinstance(partner, dict):
        partner = {}

    if not primary and not partner:
        return None

    all_keys: list[str] = list(dict.fromkeys(list(primary.keys()) + list(partner.keys())))
    if not all_keys:  # pragma: no cover
        # Unreachable: ``all_keys`` is the union of ``primary.keys()`` and
        # ``partner.keys()``; both being empty is already caught by the
        # ``if not primary and not partner`` guard above.  Kept as a
        # defensive check to mirror the original ``_build_preview_table``.
        return None

    has_partner = bool(partner)

    header_cells: list[Any] = [
        ui.tags.th("Field", style="text-align:left;padding:5px 8px;"),
        ui.tags.th("Client Primary", style="text-align:left;padding:5px 8px;"),
    ]
    if has_partner:
        header_cells.append(ui.tags.th("Client Partner", style="text-align:left;padding:5px 8px;"))

    rows: list[Any] = [
        ui.tags.tr(*header_cells, style="background-color:#E8EDF1;"),
    ]

    for key in all_keys:
        value_primary = _format_preview_value(value = primary.get(key))
        value_partner = _format_preview_value(value = partner.get(key)) if has_partner else None

        body_cells: list[Any] = [
            ui.tags.td(
                _humanize_field_key(key = key),
                style="padding:3px 8px;font-weight:500;",
            ),
            ui.tags.td(value_primary, style="padding:3px 8px;"),
        ]
        if has_partner:
            body_cells.append(ui.tags.td(value_partner, style="padding:3px 8px;"))

        rows.append(ui.tags.tr(*body_cells))

    table_widget = ui.tags.table(
        *rows,
        style=(
            "width:100%;border-collapse:collapse;"
            "border:1px solid #BDC3C7;font-size:0.85rem;margin-bottom:8px;"
        ),
    )

    return ui.card(
        ui.card_header(
            ui.tags.h6(section_title, style="margin:0;color:#2C3E50;font-weight:600;"),
        ),
        ui.card_body(table_widget, style="padding:6px 8px;"),
    )

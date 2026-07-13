"""Private upload-observer helpers for the Outline subtab.

This module is the extraction target for the file-upload observer that
previously lived inline inside
:func:`subtab_clients_outline_server`.  Splitting it out keeps
``subtab_outline.py`` under the project 1000-line cap and lets the
observer logic be tested in isolation.

Public API
----------
- :func:`register_upload_observer_QWIM` — registers the polling
  observer (``@reactive.effect`` + ``reactive.invalidate_later``)
  that watches the file input, extracts the PDF, validates, and
  updates the shared ``reactives_shiny`` state.

Notes
-----
The observer uses a polling pattern (``@reactive.effect`` +
``reactive.invalidate_later(0.5)`` + a sentinel ``reactive.Value``)
because ``@reactive.event`` on a file input inside a
``ui.panel_conditional`` inside ``@module.server`` does not fire
reliably in Shiny 1.6.3.  The ``@reactive.event`` approach was
attempted (2026-06-06) but reverted after it failed to trigger at
runtime — the root cause could not be fully diagnosed without a
live Shiny debugging session; the polling pattern is the
defensive, proven-working fallback.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from shiny import reactive, ui

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
from src.dashboard.shiny_utils.utils_tab_clients import (
    sync_user_inputs_shiny_from_extracted_worksheet,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name = __name__)


#: Poll interval (seconds) for the file-input observer.
_FILE_OBSERVER_POLL_INTERVAL_SECONDS: float = 0.5

#: Shiny input id for the file upload input (must match the static UI).
_FILE_INPUT_ID: str = (
    "input_ID_tab_clients_subtab_clients_outline_file_upload"
)


# ===================================================================
# Internal helpers
# ===================================================================


def _apply_firm_fallback_QWIM(
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

    Parameters
    ----------
    extracted_worksheet_data : dict
        Nested dictionary returned by
        :func:`extract_client_data_from_worksheet_PDF`.  Must contain the
        ``Advisor_Info`` key (a dict).
    reactives_shiny : dict
        Shared reactive state dictionary.  When present, the live value at
        ``reactives_shiny["Advisor_Info"]["Firm"]`` is preferred.

    Returns
    -------
    bool
        ``True`` when the fallback was applied, ``False`` otherwise.
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


def register_upload_observer_QWIM(
    *,
    input: Any,
    reactives_shiny: dict[str, Any],
    show_preview_reactive: reactive.Value[bool],
    last_uploaded_datapath_reactive: reactive.Value[str | None],
) -> None:
    """Register the file-upload observer for the Outline subtab.

    Parameters
    ----------
    input : shiny.Inputs
        The Shiny input object for the current session / module.
    reactives_shiny : dict
        The shared reactive state dictionary (the same one passed to
        :func:`subtab_clients_outline_server`).
    show_preview_reactive : reactive.Value[bool]
        Local reactive controlling preview visibility.  Mutated
        in-place to ``True`` after a successful upload and to
        ``False`` after every failure branch.
    last_uploaded_datapath_reactive : reactive.Value[str | None]
        Local reactive that records the last uploaded datapath so
        the polling observer can detect a *new* upload and avoid
        re-processing the same file.

    Returns
    -------
    None
        Side effect: registers a ``@reactive.effect`` in the current
        Shiny session that polls the file input on a 0.5s interval.

    Notes
    -----
    The observer performs these steps on each tick:

    1. Read the file input.  Skip if empty.
    2. Compare the current datapath with the sentinel; skip if equal.
    3. Extract the PDF via
       :func:`extract_client_data_from_worksheet_PDF`.
    4. Validate the required advisor section.  On failure, set
       ``Extracted_Worksheet_Status_Messages``, hide the preview,
       and show a modal.
    5. Validate client data; populate the four per-section
       ``User_Inputs_Shiny`` reactives via
       :func:`sync_user_inputs_shiny_from_extracted_worksheet`.
    6. Sync the ``Advisor_Info`` section via
       :func:`sync_advisor_info_to_user_inputs_shiny_QWIM` so the
       Setup > Advisor subtab inputs (including the default firm
       name ``"QWIM AI Wealth Management"``) are populated.
    7. Capture the actual exception in
       ``Extracted_Worksheet_Status_Messages`` on any failure so the
       always-visible status banner surfaces it to the user.
    """
    inner = reactives_shiny.setdefault("Inner_Variables_Shiny", {})
    triggers = reactives_shiny.setdefault("Triggers_Shiny", {})

    # Local references for closure-binding clarity.
    file_input = getattr(input, _FILE_INPUT_ID)
    show_preview = show_preview_reactive
    last_datapath = last_uploaded_datapath_reactive

    @reactive.effect
    def _on_file_upload():  # pragma: no cover
        """Polling upload observer body.

        The body of this ``@reactive.effect`` is excluded from unit
        coverage (``# pragma: no cover``) because it can only execute
        inside a live Shiny session.  The behaviour is verified
        end-to-end by the AppDriver test in
        ``tests/tests_integration/dashboard/shiny_tab_clients/test_
        integration_subtab_outline_preview_e2e.py`` (skipped when
        ``shiny[testing]`` is not installed) and by the pure-function
        tests of the helpers invoked from this body.
        """
        # Poll every 0.5s so we re-check the file input.  This is
        # the defensive, proven-working pattern for file inputs
        # inside ``ui.panel_conditional`` inside ``@module.server``.
        reactive.invalidate_later(_FILE_OBSERVER_POLL_INTERVAL_SECONDS)

        file_info = file_input()
        if file_info is None or len(file_info) == 0:
            return

        uploaded = file_info[0]
        file_path = Path(uploaded["datapath"])

        # Only process the upload if the datapath has changed since
        # the last time this observer ticked.  Without this sentinel,
        # every poll tick re-processes the same file.
        current_datapath = str(file_path)
        if last_datapath() == current_datapath:
            return
        last_datapath.set(current_datapath)

        try:
            extracted = extract_client_data_from_worksheet_PDF(pdf_path=file_path)

            # --- Apply dashboard's default Firm before blocking validation ---
            # The Inputs Worksheet PDF does not include a Firm field, so the
            # validator would otherwise block the import.  Fall back to the
            # live value in Setup -> Advisor Info (or its static default).
            firm_fallback_applied = _apply_firm_fallback_QWIM(
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
                show_preview.set(False)
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
            defaulted_fields = sync_advisor_info_to_user_inputs_shiny_QWIM(
                reactives_shiny=reactives_shiny,
                extracted_worksheet_data=extracted,
            )
            inner["Extracted_Worksheet_Defaulted_Fields"].set(defaulted_fields)

            status_messages: list[str] = []
            if not is_valid:
                status_messages.append(
                    f"PDF imported with {len(warnings)} validation warning(s); "
                    "preview tables may be incomplete. See the Preview section for details.",
                )
            if defaulted_fields:
                default_labels = [
                    f"{field_key} (used default '{_ADVISOR_INFO_DEFAULT_VALUES.get(field_key, '')}')"
                    for field_key in defaulted_fields
                ]
                status_messages.append(
                    "The uploaded PDF did not include the following advisor fields; "
                    "default values were used: " + ", ".join(default_labels) + ".",
                )
            inner["Extracted_Worksheet_Status_Messages"].set(status_messages)
            show_preview.set(True)

            current = triggers["Trigger_Populate_From_Worksheet"].get() or 0
            triggers["Trigger_Populate_From_Worksheet"].set(current + 1)

            if not is_valid:
                ui.notification_show(
                    f"Upload Complete — {len(warnings)} validation warning(s). "
                    "Dashboard inputs were populated. Please review the imported data.",
                    type="warning",
                    duration=8,
                )
            else:
                ui.notification_show(
                    "Upload Complete — PDF data extracted successfully and "
                    "dashboard inputs were populated.",
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
            show_preview.set(False)
            ui.notification_show(
                f"Failed to extract data from PDF: {exc}",
                type="error",
                duration=10,
            )

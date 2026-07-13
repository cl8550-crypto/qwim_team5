"""Advisor information subtab for the QWIM dashboard setup area.

This module provides the ``Advisor Info`` subtab under the dashboard ``Setup``
tab. It captures a single advisor record for dashboard display and downstream
reporting use.

The subtab includes editable entry boxes for:

- Name
- Credentials
- Title
- Team
- Firm
- Email
- Address
- Phone number

All input identifiers follow the required pattern:

- ``input_ID_tab_setup_subtab_advisor_info_name``
- ``input_ID_tab_setup_subtab_advisor_info_credentials``
- ``input_ID_tab_setup_subtab_advisor_info_title``
- ``input_ID_tab_setup_subtab_advisor_info_team``
- ``input_ID_tab_setup_subtab_advisor_info_firm``
- ``input_ID_tab_setup_subtab_advisor_info_email``
- ``input_ID_tab_setup_subtab_advisor_info_address``
- ``input_ID_tab_setup_subtab_advisor_info_phone_number``

The server logic stores normalized advisor values in the top-level
``reactives_shiny["Advisor_Info"]`` category using ``reactive.Value`` objects.
Trademark markers such as ``(R)``, ``(TM)``, and ``(SM)`` are normalized to the
Unicode symbols ``®``, ``™``, and ``℠`` so that dashboard and PDF output can
render them consistently.
"""

from __future__ import annotations

import re
import typing

from typing import Any

from shiny import module, reactive, ui

from src.dashboard.shiny_utils.reactives_shiny import (
    create_reactive_value_safely,
    safe_get_value_from_shiny_input_text,
)
from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
    create_enhanced_card_section,
    create_enhanced_text_input,
)
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Configuration,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name = __name__)


DEFAULT_VALUES_ADVISOR_INFO: dict[str, str] = {
    "Name": "Sylvia Advisor",
    "Credentials": "CFP®, CFPA®, CRPC™, CFA®, CPWA®, ChFC®",
    "Title": "Financial Advisor",
    "Team": "Number One Team",
    "Firm": "QWIM AI Wealth Management",
    "Email": "sylvia_advisor@QWIM.AI",
    "Address": "123 Main St, New York, NY, 10027",
    "Phone_Number": "212-123-4567",
}


FIELD_CONFIG_ADVISOR_INFO: dict[str, dict[str, str | int]] = {
    "Name": {
        "input_id": "input_ID_tab_setup_subtab_advisor_info_name",
        "field_key": "name",
        "label_text": "Name",
        "placeholder_text": "First Last or Last, First",
        "tooltip_text": "Enter advisor name as First Last or Last, First",
        "max_length": 120,
    },
    "Credentials": {
        "input_id": "input_ID_tab_setup_subtab_advisor_info_credentials",
        "field_key": "credentials",
        "label_text": "Credentials",
        "placeholder_text": "CFP®, CFA®",
        "tooltip_text": "Enter advisor credentials and designations",
        "max_length": 255,
        "input_type": "text_area",
        "rows": 3,
    },
    "Title": {
        "input_id": "input_ID_tab_setup_subtab_advisor_info_title",
        "field_key": "title",
        "label_text": "Title",
        "placeholder_text": "Financial Advisor",
        "tooltip_text": "Enter advisor title",
        "max_length": 120,
    },
    "Team": {
        "input_id": "input_ID_tab_setup_subtab_advisor_info_team",
        "field_key": "team",
        "label_text": "Team",
        "placeholder_text": "Enter team name",
        "tooltip_text": "Enter advisor team name",
        "max_length": 120,
    },
    "Firm": {
        "input_id": "input_ID_tab_setup_subtab_advisor_info_firm",
        "field_key": "firm",
        "label_text": "Firm",
        "placeholder_text": "Enter firm name",
        "tooltip_text": "Enter advisor firm name",
        "max_length": 160,
    },
    "Email": {
        "input_id": "input_ID_tab_setup_subtab_advisor_info_email",
        "field_key": "email",
        "label_text": "Email",
        "placeholder_text": "advisor@example.com",
        "tooltip_text": "Enter advisor email address",
        "max_length": 254,
    },
    "Address": {
        "input_id": "input_ID_tab_setup_subtab_advisor_info_address",
        "field_key": "address",
        "label_text": "Address",
        "placeholder_text": "Street, City, State, ZIP",
        "tooltip_text": "Enter advisor office address",
        "max_length": 255,
    },
    "Phone_Number": {
        "input_id": "input_ID_tab_setup_subtab_advisor_info_phone_number",
        "field_key": "phone_number",
        "label_text": "Phone number",
        "placeholder_text": "212-555-1234",
        "tooltip_text": "Enter advisor US phone number",
        "max_length": 32,
    },
}


def _coerce_advisor_info_config_int_or_default(
    *, raw_value: Any, default_value: int) -> int:
    """Coerce advisor UI config integers while keeping booleans on the default path."""
    if isinstance(raw_value, bool):
        return default_value

    return int(raw_value)


REGEX_PATTERN_EMAIL_LIGHT = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
REGEX_PATTERN_MARK_REGISTERED = re.compile(r"\(\s*r\s*\)", re.IGNORECASE)
REGEX_PATTERN_MARK_SERVICE = re.compile(r"\(\s*sm\s*\)", re.IGNORECASE)
REGEX_PATTERN_MARK_TRADEMARK = re.compile(r"\(\s*tm\s*\)", re.IGNORECASE)
REGEX_PATTERN_PHONE_NUMBER_DIGITS = re.compile(r"\D+")


def normalize_text_trademark_symbols(
    *, value_text: str) -> str:
    """Normalize textual trademark markers to Unicode symbols."""
    value_text_normalized = value_text.strip()
    value_text_normalized = REGEX_PATTERN_MARK_REGISTERED.sub("®", value_text_normalized)
    value_text_normalized = REGEX_PATTERN_MARK_TRADEMARK.sub("™", value_text_normalized)
    value_text_normalized = REGEX_PATTERN_MARK_SERVICE.sub("℠", value_text_normalized)
    return value_text_normalized


def normalize_text_phone_number_US(
    *, value_text: str) -> str | None:
    """Normalize a US phone number to ``NNN-NNN-NNNN`` format."""
    value_text_normalized = normalize_text_trademark_symbols(value_text = value_text)
    if len(value_text_normalized) == 0:
        return ""

    digits_phone_number = REGEX_PATTERN_PHONE_NUMBER_DIGITS.sub("", value_text_normalized)
    if len(digits_phone_number) == 11 and digits_phone_number.startswith("1"):
        digits_phone_number = digits_phone_number[1:]

    if len(digits_phone_number) != 10:
        return None

    return f"{digits_phone_number[0:3]}-{digits_phone_number[3:6]}-{digits_phone_number[6:10]}"


def normalize_text_advisor_field(
    *, field_key_name: str, value_text: str) -> tuple[str | None, str | None]:
    """Normalize one advisor field and optionally return a UI replacement value."""
    value_text_stripped = value_text.strip()
    value_text_normalized = normalize_text_trademark_symbols(value_text = value_text_stripped)

    if field_key_name == "email":
        if len(value_text_normalized) == 0:
            return "", None
        if REGEX_PATTERN_EMAIL_LIGHT.fullmatch(value_text_normalized) is None:
            return None, None
        value_text_for_input = (
            value_text_normalized if value_text_normalized != value_text_stripped else None
        )
        return value_text_normalized, value_text_for_input

    if field_key_name == "phone_number":
        value_phone_number = normalize_text_phone_number_US(value_text = value_text_normalized)
        if value_phone_number is None:
            return None, None
        value_text_for_input = (
            value_phone_number if value_phone_number != value_text_stripped else None
        )
        return value_phone_number, value_text_for_input

    value_text_for_input = (
        value_text_normalized if value_text_normalized != value_text_stripped else None
    )
    return value_text_normalized, value_text_for_input


def ensure_category_advisor_info_initialized(
    *, reactives_shiny: dict[str, Any]) -> dict[str, Any]:
    """Ensure the ``Advisor_Info`` category exists with all required fields."""
    advisor_info_category = reactives_shiny.get("Advisor_Info")
    if not isinstance(advisor_info_category, dict):
        advisor_info_category = {}
        reactives_shiny["Advisor_Info"] = advisor_info_category

    for reactive_key_name, default_value in DEFAULT_VALUES_ADVISOR_INFO.items():
        reactive_value_current = advisor_info_category.get(reactive_key_name)
        if reactive_value_current is None or not hasattr(reactive_value_current, "set"):
            advisor_info_category[reactive_key_name] = create_reactive_value_safely(initial_value = default_value)

    return advisor_info_category


@module.ui
def subtab_advisor_info_ui(  # pragma: no cover
    *, data_utils: dict[str, Any], data_inputs: dict[str, Any]) -> Any:
    """Create the advisor information setup subtab UI."""
    try:
        content_advisor_info = []
        for reactive_key_name, field_config in FIELD_CONFIG_ADVISOR_INFO.items():
            if field_config.get("input_type") == "text_area":
                content_advisor_info.append(
                    ui.div(
                        ui.tags.label(
                            str(field_config["label_text"]),
                            class_="form-label fw-semibold",
                        ),
                        ui.input_text_area(
                            id=str(field_config["input_id"]),
                            label=None,
                            value=DEFAULT_VALUES_ADVISOR_INFO[reactive_key_name],
                            placeholder=str(field_config["placeholder_text"]),
                            rows=_coerce_advisor_info_config_int_or_default(
                                raw_value = field_config.get("rows", 3),
                                default_value = 3,
                            ),
                            width="100%",
                        ),
                        class_="form-group mb-3",
                        title=str(field_config["tooltip_text"]),
                    ),
                )
                continue

            content_advisor_info.append(
                create_enhanced_text_input(
                    input_ID=str(field_config["input_id"]),
                    label_text=str(field_config["label_text"]),
                    default_value=DEFAULT_VALUES_ADVISOR_INFO[reactive_key_name],
                    placeholder_text=str(field_config["placeholder_text"]),
                    tooltip_text=str(field_config["tooltip_text"]),
                    required_field=False,
                    max_length=_coerce_advisor_info_config_int_or_default(
                        raw_value = field_config["max_length"],
                        default_value = 255,
                    ),
                    input_width="100%",
                ),
            )

        return ui.div(
            ui.h3("Advisor Information", class_="text-center mb-4"),
            ui.row(
                ui.column(
                    12,
                    create_enhanced_card_section(
                        title="Advisor Info",
                        content=content_advisor_info,
                        icon_class="fas fa-user-tie",
                        card_class="border-secondary",
                    ),
                ),
            ),
            ui.tags.style("""
			.form-group {
				margin-bottom: 0.75rem !important;
			}

			.card-body {
				padding: 1rem !important;
			}

            textarea.form-control {
                min-height: 5.5rem;
                resize: vertical;
            }

			.form-control {
				border-radius: 0.375rem;
				border: 1px solid #ced4da;
				transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
			}

			.form-control:focus {
				border-color: #86b7fe;
				box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
			}
			"""),
        )

    except (TypeError, ValueError, AttributeError, KeyError) as exc_error:
        error_message = f"Unexpected error creating advisor info subtab UI: {exc_error}"
        raise Exception_Configuration(error_message) from exc_error


@module.server
def subtab_advisor_info_server(  # pragma: no cover
    input: typing.Any,
    output: typing.Any,
    session: typing.Any,
    data_utils: dict[str, Any],
    data_inputs: dict[str, Any],
    reactives_shiny: dict[str, Any],
) -> None:
    """Synchronize advisor input fields into ``reactives_shiny["Advisor_Info"]``."""
    if not isinstance(reactives_shiny, dict):
        _logger.error(
            "VALIDATION_ERROR: reactives_shiny is not a dict",
            extra={"event_type": "validation_error", "subtab": "advisor_info"},
        )
        return

    advisor_info_category = ensure_category_advisor_info_initialized(reactives_shiny = reactives_shiny)
    triggers_category = reactives_shiny.get("Triggers_Shiny")
    if not isinstance(triggers_category, dict):
        triggers_category = {}
        reactives_shiny["Triggers_Shiny"] = triggers_category

    if "Trigger_Populate_From_Worksheet" not in triggers_category:
        triggers_category["Trigger_Populate_From_Worksheet"] = create_reactive_value_safely(initial_value = 0)

    _logger.info(
        "SERVER_INIT: Advisor Info subtab server",
        extra={"event_type": "server_init", "subtab": "advisor_info"},
    )

    @reactive.effect
    def observer_update_shared_reactives_shiny_advisor_info() -> None:
        """Keep the shared advisor reactive values synchronized with UI inputs."""
        for reactive_key_name, field_config in FIELD_CONFIG_ADVISOR_INFO.items():
            input_id_field = str(field_config["input_id"])
            field_key_name = str(field_config["field_key"])
            value_text_raw = safe_get_value_from_shiny_input_text(
                input_reactive_object = input[input_id_field],
                default_value="",
            )
            value_text_normalized, value_text_for_input = normalize_text_advisor_field(
                field_key_name = field_key_name,
                value_text = value_text_raw,
            )

            if value_text_normalized is None:
                continue

            reactive_value_current = advisor_info_category.get(reactive_key_name)
            if reactive_value_current is None or not hasattr(reactive_value_current, "set"):
                advisor_info_category[reactive_key_name] = create_reactive_value_safely(
                    initial_value = value_text_normalized,
                )
            else:
                reactive_value_current.set(value_text_normalized)

            if value_text_for_input is not None and value_text_for_input != value_text_raw:
                try:
                    if field_config.get("input_type") == "text_area":
                        ui.update_text_area(input_id_field, value=value_text_for_input)
                    else:
                        ui.update_text(input_id_field, value=value_text_for_input)
                except (AttributeError, RuntimeError, TypeError, ValueError):
                    _logger.debug(
                        "Unable to update advisor input '%s' with normalized value",
                        input_id_field,
                    )

    # -----------------------------------------------------------------------
    # Populate from uploaded worksheet PDF
    # -----------------------------------------------------------------------
    # Using @reactive.poll because @reactive.effect inside @module.server
    # does NOT re-execute when reactive.Value changes.
    # -----------------------------------------------------------------------

    def _poll_extracted_worksheet_for_advisor():
        inner = reactives_shiny.get("Inner_Variables_Shiny", {})
        extracted_rv = inner.get("Extracted_Worksheet_Data")
        if extracted_rv is None:
            return None
        try:
            return extracted_rv.get()
        except Exception:
            return None

    @reactive.poll(_poll_extracted_worksheet_for_advisor, interval_secs=0.5)
    def _poll_advisor_data():
        return _poll_extracted_worksheet_for_advisor()

    @reactive.effect
    def observer_populate_advisor_info_from_worksheet() -> None:
        """Populate advisor info inputs from the extracted worksheet data.

        Uses :func:`map_advisor_info_worksheet_to_inputs` for pure mapping
        logic; this observer dispatches ``ui.update_text`` / ``ui.update_text_area``
        and syncs reactive values.

        Notes
        -----
        The observer depends on a @reactive.poll of ``Extracted_Worksheet_Data``
        so that it fires reliably even inside @module.server.
        """
        data = _poll_advisor_data()
        _logger.warning("advisor_populate: FIRED | data_is_dict=%s", isinstance(data, dict))
        if data is None or not isinstance(data, dict):
            return

        advisor_info_data = data.get("Advisor_Info", {})
        if not isinstance(advisor_info_data, dict):
            _logger.warning("advisor_populate: Advisor_Info section missing")
            return

        _logger.warning(
            "advisor_populate: processing",
            extra={"event_type": "worksheet_import", "subtab": "advisor_info"},
        )

        from src.dashboard.shiny_utils._utils_tab_clients_populate import (
            map_advisor_info_worksheet_to_inputs,
        )

        mapped = map_advisor_info_worksheet_to_inputs(
            advisor_section = advisor_info_data,
        )

        for reactive_key_name, field_config in FIELD_CONFIG_ADVISOR_INFO.items():
            input_id_field = str(field_config["input_id"])
            value_mapped = mapped.get(input_id_field, "")

            # Sync reactive value
            reactive_value_current = advisor_info_category.get(reactive_key_name)
            if reactive_value_current is not None and hasattr(reactive_value_current, "set"):
                reactive_value_current.set(value_mapped)

            # Update UI widget
            if not value_mapped:
                continue
            try:
                if field_config.get("input_type") == "text_area":
                    ui.update_text_area(input_id_field, value = value_mapped)
                else:
                    ui.update_text(input_id_field, value = value_mapped)
            except (AttributeError, RuntimeError, TypeError, ValueError):
                _logger.debug(
                    "Unable to populate advisor input '%s' from worksheet data",
                    input_id_field,
                )

    # ------------------------------------------------------------------
    # Deferred populate — re-runs when the subtab becomes visible.
    # ------------------------------------------------------------------
    @reactive.effect
    def observer_deferred_populate_advisor_info() -> None:  # pragma: no cover
        """Re-populate advisor info inputs when the subtab becomes visible."""
        inner = reactives_shiny.get("Inner_Variables_Shiny", {})
        extracted_rv = inner.get("Extracted_Worksheet_Data")
        if extracted_rv is None:
            return

        data = extracted_rv.get()
        if data is None:
            return

        advisor_info_data = data.get("Advisor_Info", {})
        if not isinstance(advisor_info_data, dict):
            return

        triggers = reactives_shiny.get("Triggers_Shiny", {})
        trigger_rv = triggers.get("Trigger_Populate_From_Worksheet")
        if trigger_rv is not None:
            trigger_rv.get()

        from src.dashboard.shiny_utils._utils_tab_clients_populate import (
            map_advisor_info_worksheet_to_inputs,
        )

        mapped = map_advisor_info_worksheet_to_inputs(
            advisor_section = advisor_info_data,
        )

        for reactive_key_name, field_config in FIELD_CONFIG_ADVISOR_INFO.items():
            input_id_field = str(field_config["input_id"])
            value_mapped = mapped.get(input_id_field, "")

            if not value_mapped:
                continue
            try:
                if field_config.get("input_type") == "text_area":
                    ui.update_text_area(input_id_field, value = value_mapped)
                else:
                    ui.update_text(input_id_field, value = value_mapped)
            except (AttributeError, RuntimeError, TypeError, ValueError):
                _logger.debug(
                    "Unable to deferred-populate advisor input '%s'",
                    input_id_field,
                )

        _logger.info(
            "Advisor info inputs deferred-populated from worksheet PDF",
            extra={"event_type": "worksheet_import", "subtab": "advisor_info", "deferred": True},
        )

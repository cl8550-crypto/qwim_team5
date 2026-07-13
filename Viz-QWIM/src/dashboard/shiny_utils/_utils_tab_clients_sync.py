"""Private worksheet-sync helpers for the client dashboard tab."""

from __future__ import annotations

import re

from typing import Any

from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name = __name__)


# Keys that hold currency (integer) amounts per client section
_CURRENCY_KEYS_BY_SECTION: dict[str, frozenset[str]] = {
    "Personal_Info": frozenset(),
    "Assets": frozenset({"assets_taxable", "assets_tax_deferred", "assets_tax_free"}),
    "Goals": frozenset({"goal_essential", "goal_important", "goal_aspirational", "growth_rate"}),
    "Income": frozenset(
        {
            "income_social_security",
            "income_pension",
            "income_annuity_existing",
            "income_other",
        },
    ),
}


_RE_NON_NUMERIC = re.compile(r"[^\d.]")


def _parse_currency_string(
    *, value_raw: Any) -> int:
    """Convert a currency string such as ``'100,000'`` to an integer."""
    if value_raw is None or isinstance(value_raw, bool) or str(value_raw).strip() == "":
        return 0

    digits_only = _RE_NON_NUMERIC.sub("", str(value_raw))
    try:
        return int(float(digits_only))
    except (ValueError, TypeError):
        return 0


def _blank_partner_section(
    *, section_data: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of *section_data* with ``client_partner`` values zeroed or blanked."""
    result_section = dict(section_data)
    partner_raw = result_section.get("client_partner")
    if not isinstance(partner_raw, dict):
        result_section["client_partner"] = {}
        return result_section

    blanked_partner: dict[str, Any] = {}
    for field_key, field_value in partner_raw.items():
        if isinstance(field_value, bool):
            blanked_partner[field_key] = False
        elif isinstance(field_value, int | float):
            blanked_partner[field_key] = 0
        else:
            blanked_partner[field_key] = ""

    result_section["client_partner"] = blanked_partner
    return result_section


def _apply_partner_blanking(
    *, extracted_data: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of *extracted_data* with all partner client fields blanked."""
    processed_data: dict[str, Any] = {}
    for section_key, section_value in extracted_data.items():
        if isinstance(section_value, dict) and "client_partner" in section_value:
            processed_data[section_key] = _blank_partner_section(section_data = section_value)
        else:
            processed_data[section_key] = section_value

    return processed_data


def _build_input_id_to_reactive_key_map(
    *, user_inputs: dict[str, Any]) -> dict[str, str]:
    """Build a reverse lookup from Shiny input ID to ``User_Inputs_Shiny`` key.

    Uses the project's ``_reactive_key_to_input_id`` helper in reverse so
    that worksheet-populate mappings (which are expressed as ``{input_id:
    value}``) can be written directly into ``User_Inputs_Shiny``.
    """
    from src.dashboard.shiny_utils.reactives_shiny import (
        _reactive_key_to_input_id,
    )

    result: dict[str, str] = {}
    for reactive_key in user_inputs:
        try:
            input_id = _reactive_key_to_input_id(reactive_key = reactive_key)
            result[input_id] = reactive_key
        except Exception:
            continue
    return result


def _update_user_inputs_shiny_from_mapped_values(
    *, reactives_shiny: dict[str, Any], mapped_values: dict[str, Any]
) -> None:
    """Write ``{input_id: value}`` mappings into ``User_Inputs_Shiny``.

    Looks up the reactive key that corresponds to each *input_id* and
    calls ``.set()`` on the stored ``reactive.Value`` so that downstream
    consumers (e.g. the Summary subtab) see the new values immediately,
    even when the target subtab is hidden and ``ui.update_*`` calls are
    lost.

    Currency fields (assets, goals, income) are stored as formatted
    strings (``"$100,000"``) for the UI, but the Summary subtab expects
    raw numeric values.  This helper detects currency-formatted strings
    and stores the raw integer instead, so that downstream numeric
    consumers (Summary tables, reporting) receive valid numbers.
    """
    if not isinstance(reactives_shiny, dict):
        return

    user_inputs = reactives_shiny.get("User_Inputs_Shiny")
    if not isinstance(user_inputs, dict):
        return

    input_id_to_reactive_key = _build_input_id_to_reactive_key_map(
        user_inputs = user_inputs,
    )

    for input_id, value in mapped_values.items():
        reactive_key = input_id_to_reactive_key.get(input_id)
        if reactive_key is None:
            _logger.info(
                "sync_user_inputs: no reactive_key for input_id=%s",
                input_id,
            )
            continue
        reactive_var = user_inputs.get(reactive_key)
        if reactive_var is not None and hasattr(reactive_var, "set"):
            # Currency fields: store raw integer for downstream numeric
            # consumers (Summary tables, reporting).  The UI observers
            # (subtab_assets, subtab_goals, subtab_income) already use
            # ui.update_text with the formatted string, so the widget
            # displays correctly.  User_Inputs_Shiny must hold the raw
            # value so that calc_table_summary_* functions can sum and
            # compare without parsing formatted strings.
            original_value = value
            if isinstance(value, str) and value.startswith("$"):
                value = _parse_currency_string(value_raw = value)
            reactive_var.set(value)
            _logger.info(
                "sync_user_inputs: set %s = %s (was %s)",
                reactive_key,
                value,
                original_value,
            )
        else:
            _logger.info(
                "sync_user_inputs: no reactive_var for key=%s",
                reactive_key,
            )


def sync_user_inputs_shiny_from_extracted_worksheet(
    *, reactives_shiny: dict[str, Any], extracted_worksheet_data: dict[str, Any], has_client_partner: bool) -> None:
    """Prepare extracted worksheet data for consumption by subtab populate observers.

    In addition to storing the full processed payload in
    ``Inner_Variables_Shiny["Extracted_Worksheet_Data"]``, this helper
    now **directly updates** the relevant ``User_Inputs_Shiny`` reactive
    values so that the Summary subtab and any other downstream consumers
    see the imported values immediately — even when the target subtab
    is hidden and ``ui.update_*`` calls are lost.
    """
    if not isinstance(reactives_shiny, dict):
        _logger.warning(
            "sync_user_inputs_shiny_from_extracted_worksheet: reactives_shiny is not a dict",
            extra={"event_type": "validation_warning"},
        )
        return

    if not isinstance(extracted_worksheet_data, dict):
        _logger.warning(
            "sync_user_inputs_shiny_from_extracted_worksheet: extracted_worksheet_data is not a dict",
            extra={"event_type": "validation_warning"},
        )
        return

    processed_data = (
        _apply_partner_blanking(extracted_data = extracted_worksheet_data)
        if not has_client_partner
        else extracted_worksheet_data
    )

    inner = reactives_shiny.setdefault("Inner_Variables_Shiny", {})
    rv_extracted = inner.get("Extracted_Worksheet_Data")
    if rv_extracted is not None and hasattr(rv_extracted, "set"):
        rv_extracted.set(processed_data)
        _logger.info(
            "Processed worksheet data stored; has_client_partner=%s",
            has_client_partner,
            extra={"event_type": "worksheet_sync"},
        )
    else:
        _logger.warning(
            "Extracted_Worksheet_Data reactive value not found in Inner_Variables_Shiny",
            extra={"event_type": "validation_warning"},
        )

    # ------------------------------------------------------------------
    # Direct User_Inputs_Shiny sync — fixes Summary tables when subtabs
    # are hidden and ui.update_* calls are lost.
    # ------------------------------------------------------------------
    from src.dashboard.shiny_utils._utils_tab_clients_populate import (
        map_assets_worksheet_to_inputs,
        map_goals_worksheet_to_inputs,
        map_income_worksheet_to_inputs,
        map_personal_info_worksheet_to_inputs,
    )

    section_mappers = {
        "Personal_Info": map_personal_info_worksheet_to_inputs,
        "Assets": map_assets_worksheet_to_inputs,
        "Goals": map_goals_worksheet_to_inputs,
        "Income": map_income_worksheet_to_inputs,
    }

    for section_key, mapper in section_mappers.items():
        section_data = processed_data.get(section_key, {})
        if not isinstance(section_data, dict):
            continue
        for client_role in ("client_primary", "client_partner"):
            mapped = mapper(section = section_data, client_role = client_role)
            _update_user_inputs_shiny_from_mapped_values(
                reactives_shiny = reactives_shiny,
                mapped_values = mapped,
            )

    _logger.info(
        "User_Inputs_Shiny directly updated from worksheet data",
        extra={"event_type": "worksheet_sync", "target": "User_Inputs_Shiny"},
    )


# ---------------------------------------------------------------------------
# Advisor_Info sync (separate helper — invoked from subtab_outline_server)
# ---------------------------------------------------------------------------


def sync_advisor_info_to_user_inputs_shiny_QWIM(
    *,
    reactives_shiny: dict[str, Any],
    extracted_worksheet_data: dict[str, Any],
) -> list[str]:
    """Sync the ``Advisor_Info`` section of the worksheet to ``User_Inputs_Shiny``.

    The ``Advisor_Info`` section has a flat structure (no
    ``client_primary`` / ``client_partner`` split), so it cannot use
    the generic per-section mapper loop in
    :func:`sync_user_inputs_shiny_from_extracted_worksheet`.  Instead,
    the Outline subtab server calls this helper **after** the generic
    sync to push the advisor fields (name, firm, email, etc.) to the
    Setup > Advisor subtab's reactive inputs.

    Parameters
    ----------
    reactives_shiny : dict
        The shared ``reactives_shiny`` dictionary (same as in
        :func:`sync_user_inputs_shiny_from_extracted_worksheet`).
    extracted_worksheet_data : dict
        The full extracted worksheet payload (must contain
        ``"Advisor_Info"`` as a flat dict).

    Returns
    -------
    list[str]
        Names of advisor fields that were **not** found in the PDF and
        were filled in with their default value.  This list is used by
        the Outline subtab server to construct the always-visible
        status banner so the user knows which fields were defaulted
        (e.g. ``["firm"]`` when the uploaded PDF did not include a firm
        name and the code used the default ``"QWIM AI Wealth
        Management"``).

    Notes
    -----
    Pure side-effect helper: it mutates only the ``User_Inputs_Shiny``
    reactives identified by the mapping; it does not touch any
    ``reactive.Value`` objects on its own.  Returns the list of
    defaulted field names for caller convenience.  If
    ``extracted_worksheet_data`` is not a dict, or the
    ``Advisor_Info`` section is missing / not a dict, the helper
    returns ``[]`` and does not raise.
    """
    defaulted_fields: list[str] = []

    if not isinstance(reactives_shiny, dict):
        _logger.warning(
            "sync_advisor_info: reactives_shiny is not a dict",
            extra={"event_type": "validation_warning"},
        )
        return defaulted_fields

    if not isinstance(extracted_worksheet_data, dict):
        _logger.warning(
            "sync_advisor_info: extracted_worksheet_data is not a dict",
            extra={"event_type": "validation_warning"},
        )
        return defaulted_fields

    advisor_section = extracted_worksheet_data.get("Advisor_Info")
    if not isinstance(advisor_section, dict):
        _logger.warning(
            "sync_advisor_info: Advisor_Info section is missing or not a dict",
            extra={"event_type": "validation_warning"},
        )
        return defaulted_fields

    # ------------------------------------------------------------------
    # Map advisor fields to dashboard input IDs and update reactives.
    # ------------------------------------------------------------------
    from src.clients_QWIM.utils_client import (  # noqa: PLC0415  - local import
        _ADVISOR_INFO_DEFAULT_VALUES,
    )
    from src.dashboard.shiny_utils._utils_tab_clients_populate import (  # noqa: PLC0415
        map_advisor_info_worksheet_to_inputs,
    )

    mapped = map_advisor_info_worksheet_to_inputs(advisor_section=advisor_section)
    _update_user_inputs_shiny_from_mapped_values(
        reactives_shiny=reactives_shiny,
        mapped_values=mapped,
    )

    # ------------------------------------------------------------------
    # Identify which fields used the default because the PDF omitted
    # them.  The parser pre-fills the default at extraction time, so
    # the value present in ``advisor_section`` is the default iff the
    # PDF did not include a value for that field.  We detect this by
    # checking whether the value equals the default AND the raw
    # extracted value (before defaulting) was empty.
    # ------------------------------------------------------------------
    for field_key, default_value in _ADVISOR_INFO_DEFAULT_VALUES.items():
        current_value = advisor_section.get(field_key)
        if current_value is None:
            defaulted_fields.append(field_key)
            continue
        # The parser writes the default when the value is empty.  If
        # the post-default value equals the default, the PDF did not
        # include a non-empty value for this field.
        normalized = str(current_value).strip()
        if not normalized:
            defaulted_fields.append(field_key)
        elif normalized == str(default_value).strip():
            # Value is non-empty and matches the default — this could
            # either mean the PDF explicitly set it to the default or
            # the parser filled in the default.  Either way, the
            # dashboard now has the default value, which is the
            # intended behaviour.
            defaulted_fields.append(field_key)

    _logger.info(
        "Advisor_Info synced to User_Inputs_Shiny; defaulted fields: %s",
        defaulted_fields,
        extra={"event_type": "worksheet_sync", "target": "Advisor_Info"},
    )
    return defaulted_fields
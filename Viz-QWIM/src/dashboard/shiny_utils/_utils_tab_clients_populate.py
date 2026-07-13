"""Pure mapping helpers for populating dashboard inputs from worksheet PDF data.

This module provides stateless, side-effect-free functions that convert
extracted worksheet data (from ``extract_client_data_from_worksheet_PDF``)
into ``{input_id: value}`` dictionaries suitable for dispatching
``ui.update_*`` calls in Shiny reactive observers.

All functions use keyword-only arguments and return plain ``dict`` values
(no Shiny imports), making them fully unit-testable without a Shiny runtime.

Notes
-----
- Field-name contract: the PDF builder emits ``{section}.{client_role}.{key}``
  and the parser returns the same structure.
- State mapping: the PDF stores full US state names (e.g. ``"Texas"``);
  the dashboard select widget uses 2-letter postal codes (e.g. ``"TX"``).
  ``build_state_name_to_postal_code_map`` inverts ``STATE_CHOICES_QWIM``.
- The ``age_annuity_income_starting`` key in the worksheet maps to the
  ``age_income_starting`` widget suffix (the observer previously used the
  wrong suffix, causing a silent no-op).
- Currency fields are formatted as ``"$N,NNN"`` strings for text-input widgets.
- Blank policy: text → ``""``, numeric → ``None``, select → unset (omitted),
  checkbox → ``False``.
"""

from __future__ import annotations

from typing import Any

from src.dashboard.shiny_tab_clients._subtab_personal_info_tables import (
    STATE_CHOICES_QWIM,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name = __name__)


# ---------------------------------------------------------------------------
# Widget ID prefix constants
# ---------------------------------------------------------------------------

_ID_PREFIX_PERSONAL_INFO = "input_ID_tab_clients_subtab_clients_personal_info"
_ID_PREFIX_ASSETS = "input_ID_tab_clients_subtab_clients_assets"
_ID_PREFIX_GOALS = "input_ID_tab_clients_subtab_clients_goals"
_ID_PREFIX_INCOME = "input_ID_tab_clients_subtab_clients_income"
_ID_PREFIX_ADVISOR = "input_ID_tab_setup_subtab_advisor_info"

_ID_INCLUDE_PARTNER = (
    "input_ID_tab_clients_subtab_clients_personal_info_include_partner_in_analysis"
)

# ---------------------------------------------------------------------------
# Field lists per section
# ---------------------------------------------------------------------------

_PERSONAL_INFO_TEXT_FIELDS: tuple[str, ...] = ("name",)

_PERSONAL_INFO_NUMERIC_FIELDS: tuple[str, ...] = (
    "age_current",
    "age_retirement",
    "age_income_starting",
    "code_zip",
)

_PERSONAL_INFO_SELECT_FIELDS: tuple[str, ...] = (
    "status_marital",
    "gender",
    "tolerance_risk",
    "state",
)

_ASSETS_FIELDS: tuple[str, ...] = (
    "assets_taxable",
    "assets_tax_deferred",
    "assets_tax_free",
)

_GOALS_FIELDS: tuple[str, ...] = (
    "goal_essential",
    "goal_important",
    "goal_aspirational",
)

_INCOME_FIELDS: tuple[str, ...] = (
    "income_social_security",
    "income_pension",
    "income_annuity_existing",
    "income_other",
)

_ADVISOR_FIELDS: tuple[tuple[str, str, str], ...] = (
    ("name", "Name", "text"),
    ("title", "Title", "text"),
    ("credentials", "Credentials", "text_area"),
    ("team", "Team", "text"),
    ("firm", "Firm", "text"),
    ("email", "Email", "text"),
    ("phone_number", "Phone_Number", "text"),
    ("address", "Address", "text"),
)

# ---------------------------------------------------------------------------
# State reverse-map
# ---------------------------------------------------------------------------


def build_state_name_to_postal_code_map() -> dict[str, str]:
    """Build a full-name → 2-letter postal code lookup from ``STATE_CHOICES_QWIM``.

    Returns
    -------
    dict[str, str]
        Mapping where keys are full state names (e.g. ``"Texas"``) and values
        are 2-letter postal codes (e.g. ``"TX"``).  Also includes self-mappings
        for already-2-letter inputs so the function is idempotent.

    Notes
    -----
    The source ``STATE_CHOICES_QWIM`` maps postal code → full name.  This
    function inverts it.  The self-mapping handles the case where a PDF
    already stores a 2-letter code (defensive).
    """
    result: dict[str, str] = {}
    for code, name in STATE_CHOICES_QWIM.items():
        result[name] = code
        result[code] = code  # idempotent: already-2-letter passes through
    return result


# Lazily computed at module level — computed once on first access.
_STATE_NAME_TO_POSTAL: dict[str, str] = {}


def _get_state_reverse_map() -> dict[str, str]:
    """Return the cached state reverse map, building it on first call."""
    if not _STATE_NAME_TO_POSTAL:
        _STATE_NAME_TO_POSTAL.update(build_state_name_to_postal_code_map())
    return _STATE_NAME_TO_POSTAL


# ---------------------------------------------------------------------------
# Per-widget blank policy helpers
# ---------------------------------------------------------------------------


def _blank_text() -> str:
    """Return the blank value for text inputs."""
    return ""


def _format_currency(
    *, amount: int) -> str:
    """Format an integer amount as a currency string for text-input widgets.

    Parameters
    ----------
    amount : int
        Whole-dollar amount.

    Returns
    -------
    str
        Formatted string such as ``"$100,000"`` or ``"$0"``.
    """
    return f"${amount:,}"


def _coerce_int_or_zero(
    *, raw_value: Any) -> int:
    """Coerce a raw worksheet value to an integer, defaulting to 0.

    Parameters
    ----------
    raw_value : Any
        Raw value from the worksheet parser (may be ``str``, ``int``,
        ``float``, ``None``, or ``bool``).

    Returns
    -------
    int
        Integer value, or 0 if the input is not coercible.
    """
    if raw_value is None or isinstance(raw_value, bool):
        return 0
    if isinstance(raw_value, int):
        return raw_value
    if isinstance(raw_value, float):
        return int(raw_value)
    try:
        cleaned = str(raw_value).replace(",", "").replace("$", "").strip()
        if cleaned == "":
            return 0
        return int(float(cleaned))
    except (ValueError, TypeError):
        return 0


def _coerce_numeric_or_none(
    *, raw_value: Any) -> int | None:
    """Coerce a raw worksheet value to an integer, returning ``None`` for blanks.

    Parameters
    ----------
    raw_value : Any
        Raw value from the worksheet parser.

    Returns
    -------
    int or None
        Integer value, or ``None`` when the input is empty / non-coercible.
    """
    if raw_value is None or raw_value == "":
        return None
    if isinstance(raw_value, bool):
        return None
    if isinstance(raw_value, int):
        return raw_value
    if isinstance(raw_value, float):
        return int(raw_value)
    try:
        cleaned = str(raw_value).replace(",", "").replace("$", "").strip()
        if cleaned == "":
            return None
        return int(float(cleaned))
    except (ValueError, TypeError):
        return None


def _normalize_select_value(
    *, raw_label: str, field_key: str) -> str | None:
    """Normalize a worksheet select-field label to the dashboard choice key.

    Parameters
    ----------
    raw_label : str
        Raw label from the worksheet (e.g. ``"Moderate Conservative"``,
        ``"Texas"``).
    field_key : str
        The field key (``"status_marital"``, ``"gender"``,
        ``"tolerance_risk"``, or ``"state"``).

    Returns
    -------
    str or None
        Normalized choice key for ``ui.update_select``, or ``None`` when
        the label cannot be mapped.
    """
    if not raw_label or not raw_label.strip():
        return None

    if field_key == "state":
        reverse_map = _get_state_reverse_map()
        return reverse_map.get(raw_label.strip())

    # marital, gender, risk: lowercase, replace spaces/hyphens with underscores
    return raw_label.strip().lower().replace(" ", "_").replace("-", "_")


# ---------------------------------------------------------------------------
# Section mappers
# ---------------------------------------------------------------------------


def map_personal_info_worksheet_to_inputs(
    *,
    section: dict[str, Any],
    client_role: str,
) -> dict[str, str | int | None | bool]:
    """Map a Personal_Info worksheet section to dashboard input IDs.

    Parameters
    ----------
    section : dict
        The ``Personal_Info`` section from extracted worksheet data,
        containing ``client_primary`` and ``client_partner`` sub-dicts.
    client_role : str
        Either ``"client_primary"`` or ``"client_partner"``.

    Returns
    -------
    dict
        Mapping from full Shiny input IDs to values.  Every target input
        is present; missing fields receive blank values.  The
        ``include_partner_in_analysis`` checkbox is included only for
        ``client_partner``.

    Notes
    -----
    The worksheet key ``age_annuity_income_starting`` is mapped to the
    widget suffix ``age_income_starting`` (the observer previously used
    the wrong suffix).
    """
    fields: dict[str, Any] = section.get(client_role, {})
    if not isinstance(fields, dict):
        fields = {}

    prefix = client_role
    result: dict[str, str | int | None | bool] = {}

    # --- Text fields ---
    for text_key in _PERSONAL_INFO_TEXT_FIELDS:
        input_id = f"{_ID_PREFIX_PERSONAL_INFO}_{prefix}_{text_key}"
        raw_val = fields.get(text_key)
        result[input_id] = str(raw_val) if raw_val is not None and str(raw_val).strip() else _blank_text()

    # --- Numeric fields (with age_annuity_income_starting → age_income_starting fix) ---
    _WORKSHEET_TO_WIDGET_NUMERIC: dict[str, str] = {
        "age_current": "age_current",
        "age_retirement": "age_retirement",
        "age_annuity_income_starting": "age_income_starting",
        "code_zip": "code_zip",
    }
    for worksheet_key, widget_suffix in _WORKSHEET_TO_WIDGET_NUMERIC.items():
        input_id = f"{_ID_PREFIX_PERSONAL_INFO}_{prefix}_{widget_suffix}"
        raw_val = fields.get(worksheet_key)
        result[input_id] = _coerce_numeric_or_none(raw_value = raw_val)

    # --- Select fields ---
    for select_key in _PERSONAL_INFO_SELECT_FIELDS:
        input_id = f"{_ID_PREFIX_PERSONAL_INFO}_{prefix}_{select_key}"
        raw_label = str(fields.get(select_key) or "")
        choice_key = _normalize_select_value(raw_label = raw_label, field_key = select_key)
        if choice_key:
            result[input_id] = choice_key

    # --- Include partner checkbox (client_partner only) ---
    if client_role == "client_partner":
        partner_name = str(fields.get("name") or "").strip()
        result[_ID_INCLUDE_PARTNER] = bool(partner_name)

    return result


def map_assets_worksheet_to_inputs(
    *,
    section: dict[str, Any],
    client_role: str,
) -> dict[str, str]:
    """Map an Assets worksheet section to dashboard input IDs.

    Parameters
    ----------
    section : dict
        The ``Assets`` section from extracted worksheet data.
    client_role : str
        Either ``"client_primary"`` or ``"client_partner"``.

    Returns
    -------
    dict
        Mapping from full Shiny input IDs to formatted currency strings
        (e.g. ``"$100,000"``).  Every target input is present; missing
        fields receive ``"$0"``.
    """
    fields: dict[str, Any] = section.get(client_role, {})
    if not isinstance(fields, dict):
        fields = {}

    prefix = client_role
    result: dict[str, str] = {}

    for asset_key in _ASSETS_FIELDS:
        input_id = f"{_ID_PREFIX_ASSETS}_{prefix}_{asset_key}"
        raw_val = fields.get(asset_key)
        amount = _coerce_int_or_zero(raw_value = raw_val)
        result[input_id] = _format_currency(amount = amount)

    return result


def map_goals_worksheet_to_inputs(
    *,
    section: dict[str, Any],
    client_role: str,
) -> dict[str, str]:
    """Map a Goals worksheet section to dashboard input IDs.

    Parameters
    ----------
    section : dict
        The ``Goals`` section from extracted worksheet data.
    client_role : str
        Either ``"client_primary"`` or ``"client_partner"``.

    Returns
    -------
    dict
        Mapping from full Shiny input IDs to formatted currency strings.
        Every target input is present; missing fields receive ``"$0"``.
    """
    fields: dict[str, Any] = section.get(client_role, {})
    if not isinstance(fields, dict):
        fields = {}

    prefix = client_role
    result: dict[str, str] = {}

    for goal_key in _GOALS_FIELDS:
        input_id = f"{_ID_PREFIX_GOALS}_{prefix}_{goal_key}"
        raw_val = fields.get(goal_key)
        amount = _coerce_int_or_zero(raw_value = raw_val)
        result[input_id] = _format_currency(amount = amount)

    return result


def map_income_worksheet_to_inputs(
    *,
    section: dict[str, Any],
    client_role: str,
) -> dict[str, str]:
    """Map an Income worksheet section to dashboard input IDs.

    Parameters
    ----------
    section : dict
        The ``Income`` section from extracted worksheet data.
    client_role : str
        Either ``"client_primary"`` or ``"client_partner"``.

    Returns
    -------
    dict
        Mapping from full Shiny input IDs to formatted currency strings.
        Every target input is present; missing fields receive ``"$0"``.
    """
    fields: dict[str, Any] = section.get(client_role, {})
    if not isinstance(fields, dict):
        fields = {}

    prefix = client_role
    result: dict[str, str] = {}

    for income_key in _INCOME_FIELDS:
        input_id = f"{_ID_PREFIX_INCOME}_{prefix}_{income_key}"
        raw_val = fields.get(income_key)
        amount = _coerce_int_or_zero(raw_value = raw_val)
        result[input_id] = _format_currency(amount = amount)

    return result


def map_advisor_info_worksheet_to_inputs(
    *,
    advisor_section: dict[str, Any],
) -> dict[str, str]:
    """Map an Advisor_Info worksheet section to dashboard input IDs.

    Parameters
    ----------
    advisor_section : dict
        The ``Advisor_Info`` section from extracted worksheet data
        (flat dict, not nested by client role).

    Returns
    -------
    dict
        Mapping from full Shiny input IDs to normalized text values.
        Every target input is present; missing fields receive ``""``.
    """
    if not isinstance(advisor_section, dict):
        advisor_section = {}

    result: dict[str, str] = {}

    for field_key, _reactive_key, _input_type in _ADVISOR_FIELDS:
        input_id = f"{_ID_PREFIX_ADVISOR}_{field_key}"
        raw_val = advisor_section.get(field_key)
        if raw_val is not None and str(raw_val).strip():
            result[input_id] = str(raw_val).strip()
        else:
            result[input_id] = _blank_text()

    return result

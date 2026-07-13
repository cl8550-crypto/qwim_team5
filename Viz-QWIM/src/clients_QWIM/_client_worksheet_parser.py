"""PDF extraction, normalization, and RGA conversion helpers.

Functions
---------
extract_client_data_from_worksheet_PDF
_parse_field_into_result
_normalize_extracted_advisor_info_section
worksheet_has_client_partner
convert_worksheet_data_to_RGA_format
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

from ._client_constants import (
    _ADVISOR_INFO_DEFAULT_VALUES,
    REGEX_PATTERN_MARK_REGISTERED,
    REGEX_PATTERN_MARK_SERVICE,
    REGEX_PATTERN_MARK_TRADEMARK,
    REGEX_PATTERN_PHONE_NUMBER_DIGITS,
)
from ._client_formatters import (
    _safe_numeric,
    _safe_whole_dollar_numeric,
)


_logger = get_logger(name = __name__)


FITZ_WIDGET_TYPE_CHECKBOX = getattr(fitz, "PDF_WIDGET_TYPE_CHECKBOX", 2)


def extract_client_data_from_worksheet_PDF(
    *, pdf_path: Path) -> dict[str, Any]:
    """Read a completed retirement income worksheet PDF and extract client data."""
    if not isinstance(pdf_path, Path):
        pdf_path = Path(pdf_path)

    if not pdf_path.is_file():
        raise Exception_Validation_Input(
            f"PDF file not found: {pdf_path}",
        )

    _logger.info("Extracting client data from PDF: %s", pdf_path)

    result: dict[str, Any] = {
        "Header": {},
        "Advisor_Info": {},
        "Personal_Info": {"client_primary": {}, "client_partner": {}},
        "Assets": {"client_primary": {}, "client_partner": {}},
        "Goals": {"client_primary": {}, "client_partner": {}},
        "Income": {"client_primary": {}, "client_partner": {}},
        "Contingency": {"client_primary": {}, "client_partner": {}},
        "LTC_Insurance": {"client_primary": {}, "client_partner": {}},
        "Life_Insurance": {"client_primary": {}, "client_partner": {}},
    }

    doc = fitz.open(str(pdf_path))
    try:
        for page in doc:
            for widget in page.widgets():
                widget_current: Any = widget
                field_name = widget_current.field_name
                field_value = widget_current.field_value

                if field_name is None:  # pragma: no cover
                    continue  # pragma: no cover

                if widget_current.field_type == FITZ_WIDGET_TYPE_CHECKBOX:
                    field_value = field_value in ("Yes", "/Yes", "On", "/On", True)

                _parse_field_into_result(result = result, field_name = field_name, field_value = field_value)
    finally:
        doc.close()

    _normalize_extracted_advisor_info_section(result = result)

    advisor_info_extracted: dict[str, Any] = result.get("Advisor_Info", {})
    for field_key, default_value in _ADVISOR_INFO_DEFAULT_VALUES.items():
        existing_value = advisor_info_extracted.get(field_key)
        if existing_value is None or str(existing_value).strip() == "":
            advisor_info_extracted[field_key] = default_value
            _logger.debug(
                "Advisor_Info.%s not found in PDF; using default value.",
                field_key,
            )

    _logger.info("Extraction complete - sections found: %s", list(result.keys()))
    return result


def _parse_field_into_result(
    *, result: dict[str, Any], field_name: str, field_value: Any) -> None:
    """Parse a dot-delimited field name and store value in *result* dict."""
    parts = field_name.split(".")

    if len(parts) == 2 and parts[0] in {"Header", "Advisor_Info"}:
        result.setdefault(parts[0], {})[parts[1]] = field_value

    elif len(parts) == 3:
        section_key = parts[0]
        client_role = parts[1]
        field_key = parts[2]

        known_sections = {
            "Personal_Info",
            "Assets",
            "Goals",
            "Income",
            "Contingency",
            "LTC_Insurance",
            "Life_Insurance",
        }
        if section_key in known_sections and section_key in result:
            if client_role in result[section_key]:
                result[section_key][client_role][field_key] = field_value
            else:
                _logger.warning("Unknown client role '%s' in field: %s", client_role, field_name)
        else:
            _logger.warning("Unknown field structure: %s", field_name)
    else:
        _logger.warning("Unrecognised PDF field name: %s", field_name)


def _normalize_text_trademark_symbols(*, value_text: str) -> str:
    """Normalize ASCII trademark markers to Unicode symbols."""
    return REGEX_PATTERN_MARK_SERVICE.sub(
        "℠",
        REGEX_PATTERN_MARK_TRADEMARK.sub(
            "™",
            REGEX_PATTERN_MARK_REGISTERED.sub("®", value_text.strip()),
        ),
    )


def _normalize_phone_number_US(*, value_text: str) -> str:
    """Normalize a US phone number to ``NNN-NNN-NNNN`` when possible."""
    digits_phone_number = REGEX_PATTERN_PHONE_NUMBER_DIGITS.sub("", value_text)
    if len(digits_phone_number) == 11 and digits_phone_number.startswith("1"):
        digits_phone_number = digits_phone_number[1:]

    if len(digits_phone_number) != 10:
        return value_text.strip()

    return f"{digits_phone_number[0:3]}-{digits_phone_number[3:6]}-{digits_phone_number[6:10]}"


def _normalize_extracted_advisor_info_section(*, result: dict[str, Any]) -> None:
    """Normalize extracted advisor info values in-place."""
    advisor_info = result.get("Advisor_Info")
    if not isinstance(advisor_info, dict):
        return

    for field_key, value_current in list(advisor_info.items()):
        if value_current is None:
            continue

        value_text = str(value_current).strip()
        if field_key == "phone_number":
            advisor_info[field_key] = _normalize_phone_number_US(value_text = value_text)
            continue

        if field_key == "email":
            advisor_info[field_key] = value_text
            continue

        advisor_info[field_key] = _normalize_text_trademark_symbols(value_text = value_text)


def worksheet_has_client_partner(*, extracted_data: dict[str, Any]) -> bool:
    """Return ``True`` when the worksheet contains populated partner-client data."""
    if not isinstance(extracted_data, dict):
        return False

    for section_key in ("Personal_Info", "Assets", "Goals", "Income"):
        section_data = extracted_data.get(section_key, {})
        if not isinstance(section_data, dict):
            continue

        partner_fields = section_data.get("client_partner", {})
        if not isinstance(partner_fields, dict):
            continue

        for value_current in partner_fields.values():
            if isinstance(value_current, bool):
                continue
            if value_current is None:
                continue
            if isinstance(value_current, str):
                if value_current.strip():
                    return True
                continue
            return True

    return False


def convert_worksheet_data_to_RGA_format(
    *, extracted_data: dict[str, Any]) -> dict[str, Any]:
    """Convert PDF-extracted worksheet data to RGA-normalized client format."""
    if not isinstance(extracted_data, dict):
        raise Exception_Validation_Input(
            "extracted_data must be a dictionary",
            field_name="extracted_data",
            expected_type=dict,
            actual_value=type(extracted_data).__name__,
        )

    pi_primary = extracted_data.get("Personal_Info", {}).get("client_primary", {})

    if not pi_primary:
        raise Exception_Validation_Input(
            "extracted_data missing Personal_Info.client_primary",
        )

    is_couple = worksheet_has_client_partner(extracted_data = extracted_data)

    age_primary = int(_safe_numeric(value = pi_primary.get("age_current"), default = 0))
    retirement_age = int(_safe_numeric(value = pi_primary.get("age_retirement"), default = age_primary))
    income_start_age = int(
        _safe_numeric(value = pi_primary.get("age_annuity_income_starting"), default = retirement_age),
    )
    gender_primary = str(pi_primary.get("gender", "")).strip()
    marital_status = str(pi_primary.get("status_marital", "")).strip()
    risk_tolerance = str(pi_primary.get("tolerance_risk", "Moderate")).strip()

    if is_couple:
        client_group = "Joint"
    elif gender_primary.lower().startswith("f"):
        client_group = "Female"
    else:
        client_group = "Male"

    def _sum_whole_dollar_fields(
        *, section_data: dict[str, Any], field_keys: tuple[str, ...]) -> float:
        """Return the sum of individually normalized whole-dollar fields."""
        return sum(
            _safe_whole_dollar_numeric(value = section_data.get(field_key))
            for field_key in field_keys
        )

    assets_primary = extracted_data.get("Assets", {}).get("client_primary", {})
    assets_partner = extracted_data.get("Assets", {}).get("client_partner", {})
    asset_field_keys = (
        "assets_taxable",
        "assets_tax_deferred",
        "assets_tax_free",
    )
    initial_wealth = _sum_whole_dollar_fields(
        section_data = assets_primary,
        field_keys = asset_field_keys,
    ) + _sum_whole_dollar_fields(
        section_data = assets_partner,
        field_keys = asset_field_keys,
    )

    goals_primary = extracted_data.get("Goals", {}).get("client_primary", {})
    goals_partner = extracted_data.get("Goals", {}).get("client_partner", {})
    goals = {
        "essential": _safe_whole_dollar_numeric(value = goals_primary.get("goal_essential"))
        + _safe_whole_dollar_numeric(value = goals_partner.get("goal_essential")),
        "important": _safe_whole_dollar_numeric(value = goals_primary.get("goal_important"))
        + _safe_whole_dollar_numeric(value = goals_partner.get("goal_important")),
        "aspirational": _safe_whole_dollar_numeric(value = goals_primary.get("goal_aspirational"))
        + _safe_whole_dollar_numeric(value = goals_partner.get("goal_aspirational")),
    }

    income_primary = extracted_data.get("Income", {}).get("client_primary", {})
    income_partner = extracted_data.get("Income", {}).get("client_partner", {})

    ss_primary = _safe_whole_dollar_numeric(value = income_primary.get("income_social_security"))
    ss_partner = _safe_whole_dollar_numeric(value = income_partner.get("income_social_security"))
    social_security_total = ss_primary + ss_partner

    pension_primary = _safe_whole_dollar_numeric(value = income_primary.get("income_pension"))
    pension_partner = _safe_whole_dollar_numeric(value = income_partner.get("income_pension"))

    annuity_primary = _safe_whole_dollar_numeric(value = income_primary.get("income_annuity_existing"))
    annuity_partner = _safe_whole_dollar_numeric(value = income_partner.get("income_annuity_existing"))

    other_primary = _safe_whole_dollar_numeric(value = income_primary.get("income_other"))
    other_partner = _safe_whole_dollar_numeric(value = income_partner.get("income_other"))

    income_secured_total = (
        social_security_total
        + pension_primary
        + pension_partner
        + annuity_primary
        + annuity_partner
    )
    income_unsecured_total = other_primary + other_partner
    income_total = income_secured_total + income_unsecured_total

    return {
        "age_primary": age_primary,
        "gender_primary": gender_primary or client_group,
        "client_group": client_group,
        "income_start_age": income_start_age,
        "retirement_age": retirement_age,
        "marital_status": marital_status,
        "risk_tolerance": risk_tolerance,
        "initial_wealth": float(initial_wealth),
        "income_total": float(income_total),
        "income_secured_total": float(income_secured_total),
        "income_unsecured_total": float(income_unsecured_total),
        "social_security_total": float(social_security_total),
        "goals": goals,
    }

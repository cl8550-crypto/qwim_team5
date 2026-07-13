"""Validation helpers for worksheet client data.

No PDF library imports (fitz / reportlab).

Functions
---------
validate_required_advisor_info_section
validate_extracted_client_data
build_checkbox_fields_by_section
_validate_choice_field
_validate_numeric_range
"""

from __future__ import annotations

from typing import Any

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)

from ._client_constants import (
    _ADVISOR_INFO_DEFAULT_VALUES,
    _ADVISOR_INFO_FIELD_LABELS,
    _SECTIONS,
    REGEX_PATTERN_EMAIL_LIGHT,
    REGEX_PATTERN_PHONE_NUMBER_DIGITS,
    VALID_GENDER,
    VALID_MARITAL_STATUS,
    VALID_RISK_TOLERANCE,
    VALID_US_STATES,
)
from ._client_formatters import _parse_whole_dollar_amount


def validate_required_advisor_info_section(
    *, extracted_data: dict[str, Any]) -> list[str]:
    """Return missing or invalid Advisor Info fields required for dashboard import."""
    if not isinstance(extracted_data, dict):
        raise Exception_Validation_Input("extracted_data must be a dictionary")

    advisor_info = extracted_data.get("Advisor_Info")
    if not isinstance(advisor_info, dict):
        return ["Advisor Information section is missing"]

    validation_messages: list[str] = []

    for field_key, field_label in _ADVISOR_INFO_FIELD_LABELS.items():
        if field_key in _ADVISOR_INFO_DEFAULT_VALUES:
            continue

        value_current = advisor_info.get(field_key)
        value_text = "" if value_current is None else str(value_current).strip()

        if len(value_text) == 0:
            validation_messages.append(f"{field_label} is missing")
            continue

        if field_key == "email" and REGEX_PATTERN_EMAIL_LIGHT.fullmatch(value_text) is None:
            validation_messages.append(f"{field_label} has invalid format")

        if field_key == "phone_number":
            digits_phone_number = REGEX_PATTERN_PHONE_NUMBER_DIGITS.sub("", value_text)
            if len(digits_phone_number) == 11 and digits_phone_number.startswith("1"):
                digits_phone_number = digits_phone_number[1:]
            if len(digits_phone_number) != 10:
                validation_messages.append(f"{field_label} has invalid format")

    return validation_messages


def validate_extracted_client_data(
    *, extracted_data: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate extracted worksheet data against acceptable values."""
    warnings_list: list[str] = []
    checkbox_fields_by_section = build_checkbox_fields_by_section()

    for client_role in ("client_primary", "client_partner"):
        personal_info_section = extracted_data.get("Personal_Info", {}).get(client_role, {})
        if not personal_info_section:
            continue

        _validate_choice_field(
            section = personal_info_section,
            field_key = "status_marital",
            valid_choices = VALID_MARITAL_STATUS,
            client_role = client_role,
            warnings_list = warnings_list,
        )
        _validate_choice_field(
            section = personal_info_section,
            field_key = "gender",
            valid_choices = VALID_GENDER,
            client_role = client_role,
            warnings_list = warnings_list,
        )
        _validate_choice_field(
            section = personal_info_section,
            field_key = "tolerance_risk",
            valid_choices = VALID_RISK_TOLERANCE,
            client_role = client_role,
            warnings_list = warnings_list,
        )
        _validate_choice_field(
            section = personal_info_section,
            field_key = "state",
            valid_choices = VALID_US_STATES,
            client_role = client_role,
            warnings_list = warnings_list,
        )
        _validate_numeric_range(
            section = personal_info_section,
            field_key = "age_current",
            min_val = 18,
            max_val = 100,
            client_role = client_role,
            warnings_list = warnings_list,
        )
        _validate_numeric_range(
            section = personal_info_section,
            field_key = "age_retirement",
            min_val = 50,
            max_val = 80,
            client_role = client_role,
            warnings_list = warnings_list,
        )
        _validate_numeric_range(
            section = personal_info_section,
            field_key = "age_annuity_income_starting",
            min_val = 16,
            max_val = 70,
            client_role = client_role,
            warnings_list = warnings_list,
        )
        _validate_numeric_range(
            section = personal_info_section,
            field_key = "code_zip",
            min_val = 10000,
            max_val = 99999,
            client_role = client_role,
            warnings_list = warnings_list,
        )

    for section_key in ("Assets", "Goals", "Income"):
        for client_role in ("client_primary", "client_partner"):
            section = extracted_data.get(section_key, {}).get(client_role, {})
            if not section:
                continue
            checkbox_fields = checkbox_fields_by_section.get(section_key, set())
            for field_key, value in section.items():
                if field_key in checkbox_fields:
                    continue
                if field_key.endswith(("_inflation_indexed", "_flag")):
                    continue
                if field_key == "growth_rate":
                    continue
                if value is None or value == "":
                    continue
                amount_value = _parse_whole_dollar_amount(value = value)
                if amount_value is None:
                    warnings_list.append(
                        f"{client_role}.{section_key}.{field_key}: not a valid whole-dollar amount ('{value}')",
                    )
                    continue

                if amount_value < 0:
                    warnings_list.append(
                        f"{client_role}.{section_key}.{field_key}: negative value ({amount_value})",
                    )

    is_valid = len(warnings_list) == 0
    return is_valid, warnings_list


def build_checkbox_fields_by_section() -> dict[str, set[str]]:
    """Return checkbox-only field keys grouped by worksheet section title."""
    return {
        str(section_def["title"]): {
            str(row_def["key"])
            for row_def in section_def["rows"]
            if bool(row_def.get("is_checkbox", False))
        }
        for section_def in _SECTIONS
    }


def _validate_choice_field(
    *, section: dict[str, Any], field_key: str, valid_choices: list[str], client_role: str, warnings_list: list[str]) -> None:
    """Append a warning if *field_key* value is not in *valid_choices*."""
    value = section.get(field_key)
    if value is None or value == "":
        return

    value_str = str(value).strip()
    valid_choices_lower = [value_choice.lower() for value_choice in valid_choices]
    if value_str.lower() not in valid_choices_lower:
        warnings_list.append(
            f"{client_role}.Personal_Info.{field_key}: "
            f"'{value_str}' is not a recognised value. "
            f"Expected one of: {valid_choices}",
        )


def _validate_numeric_range(
    *, section: dict[str, Any], field_key: str, min_val: float, max_val: float, client_role: str, warnings_list: list[str]) -> None:
    """Append a warning if *field_key* is outside [min_val, max_val]."""
    value = section.get(field_key)
    if value is None or value == "":
        return
    if isinstance(value, bool):
        warnings_list.append(
            f"{client_role}.Personal_Info.{field_key}: '{value}' is not a valid number",
        )
        return
    try:
        value_numeric = float(str(value).replace(",", "").strip())
    except (ValueError, TypeError):
        warnings_list.append(
            f"{client_role}.Personal_Info.{field_key}: '{value}' is not a valid number",
        )
        return
    if value_numeric < min_val or value_numeric > max_val:
        warnings_list.append(
            f"{client_role}.Personal_Info.{field_key}: "
            f"{value_numeric} is outside valid range [{min_val}, {max_val}]",
        )

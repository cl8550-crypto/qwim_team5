"""
Robot Framework keyword library for utils_client formatting, validation and worksheet helpers.
==============================================================================================

Covers:
    - ``_normalize_phone_number_US``  : phone number normalization
    - ``_normalize_text_trademark_symbols`` : trademark symbol replacement
    - ``_safe_numeric``               : safe float conversion
    - ``validate_required_advisor_info_section`` : advisor field validation
    - ``validate_extracted_client_data``         : extracted data validation
    - ``build_checkbox_fields_by_section``       : checkbox field map
    - ``worksheet_has_client_partner``           : partner presence detection

Author:     QWIM Development Team
Version:    1.0.0
"""

from __future__ import annotations

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Project root on sys.path so src packages resolve correctly
# ---------------------------------------------------------------------------
_PROJECT_ROOT: Path = Path(__file__).resolve().parents[3]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Conditional imports with module availability guard
# ---------------------------------------------------------------------------
MODULE_IMPORT_AVAILABLE: bool = True
_import_error_message: str = ""

try:
    from src.clients_QWIM.utils_client import (
        _is_currency_field_name,
        _normalize_phone_number_US,
        _normalize_text_trademark_symbols,
        _safe_numeric,
        build_checkbox_fields_by_section,
        validate_extracted_client_data,
        validate_required_advisor_info_section,
        worksheet_has_client_partner,
    )
except ImportError as _exc:
    MODULE_IMPORT_AVAILABLE = False
    _import_error_message = str(_exc)


def _require_imports() -> None:
    """Raise RuntimeError when required imports are unavailable."""
    if not MODULE_IMPORT_AVAILABLE:
        raise RuntimeError(
            f"Required imports not available: {_import_error_message}"
        )


# ---------------------------------------------------------------------------
# Shared fixture data helpers
# ---------------------------------------------------------------------------

_COMPLETE_ADVISOR_INFO: dict = {
    "name": "Jane Smith",
    "title": "CFP",
    "credentials": "CFP, CFA",
    "team": "Wealth Advisory",
    "email": "jane.smith@example.com",
    "phone_number": "212-555-1234",
    "address": "123 Main St, New York, NY",
}

_VALID_SINGLE_CLIENT_DATA: dict = {
    "Advisor_Info": _COMPLETE_ADVISOR_INFO,
    "Personal_Info": {
        "client_primary": {
            "status_marital": "Married",
            "gender": "Male",
            "tolerance_risk": "Moderate",
            "state": "California",
            "age_current": "55",
            "age_retirement": "65",
            "age_annuity_income_starting": "65",
            "code_zip": "90210",
        }
    },
    "Assets": {
        "client_primary": {
            "assets_taxable": "250000",
        }
    },
    "Goals": {
        "client_primary": {
            "goal_essential": "60000",
        }
    },
    "Income": {
        "client_primary": {
            "income_social_security": "24000",
        }
    },
}


# ---------------------------------------------------------------------------
# Phone normalization keywords
# ---------------------------------------------------------------------------


def normalize_phone_number(phone_input: str) -> str:
    """Normalize a US phone number and return the formatted result.

    Arguments:
    - phone_input -- raw phone number string

    Returns: normalized phone string (NNN-NNN-NNNN when possible)
    """
    _require_imports()
    return _normalize_phone_number_US(value_text = phone_input)


def phone_result_should_equal(actual: str, expected: str) -> None:
    """Assert that *actual* phone string equals *expected*.

    Arguments:
    - actual   -- the normalized phone number
    - expected -- expected formatted value

    Raises AssertionError on mismatch.
    """
    assert actual == expected, f"Phone mismatch: got '{actual}', expected '{expected}'"


# ---------------------------------------------------------------------------
# Trademark normalization keywords
# ---------------------------------------------------------------------------


def normalize_trademark_symbols(text_input: str) -> str:
    """Normalize ASCII trademark markers in *text_input* to Unicode symbols.

    Arguments:
    - text_input -- raw text that may contain (SM), (TM), (R) markers

    Returns: normalized text
    """
    _require_imports()
    return _normalize_text_trademark_symbols(value_text = text_input)


# ---------------------------------------------------------------------------
# Safe numeric keywords
# ---------------------------------------------------------------------------


def safe_numeric_value(value_input: object) -> float:
    """Convert *value_input* to float safely.

    Arguments:
    - value_input -- any value (None, str, int, float)

    Returns: float result
    """
    _require_imports()
    return _safe_numeric(value = value_input)


def numeric_result_should_equal(actual: float, expected: float) -> None:
    """Assert *actual* float equals *expected*.

    Arguments:
    - actual   -- float value
    - expected -- expected float

    Raises AssertionError on mismatch.
    """
    assert actual == expected, f"Numeric mismatch: got {actual}, expected {expected}"


# ---------------------------------------------------------------------------
# Advisor info validation keywords
# ---------------------------------------------------------------------------


def build_complete_advisor_extracted_data() -> dict:
    """Return a complete advisor info extracted dict for validation tests.

    Returns: dict with ``Advisor_Info`` sub-dict fully populated.
    """
    _require_imports()
    return {"Advisor_Info": dict(_COMPLETE_ADVISOR_INFO)}


def build_advisor_extracted_data_missing_name() -> dict:
    """Return advisor info extracted dict with the name field removed.

    Returns: dict with ``Advisor_Info`` missing the ``name`` key.
    """
    _require_imports()
    info = {k: v for k, v in _COMPLETE_ADVISOR_INFO.items() if k != "name"}
    return {"Advisor_Info": info}


def build_advisor_extracted_data_invalid_email(email_input: str) -> dict:
    """Return advisor info extracted dict with an invalid email.

    Arguments:
    - email_input -- bad email string to inject

    Returns: dict with ``Advisor_Info`` containing the bad email.
    """
    _require_imports()
    info = dict(_COMPLETE_ADVISOR_INFO)
    info["email"] = email_input
    return {"Advisor_Info": info}


def build_advisor_extracted_data_invalid_phone(phone_input: str) -> dict:
    """Return advisor info extracted dict with an invalid phone number.

    Arguments:
    - phone_input -- bad phone string to inject

    Returns: dict with ``Advisor_Info`` containing the bad phone.
    """
    _require_imports()
    info = dict(_COMPLETE_ADVISOR_INFO)
    info["phone_number"] = phone_input
    return {"Advisor_Info": info}


def validate_advisor_info(extracted_advisor: dict) -> list[str]:
    """Run ``validate_required_advisor_info_section`` and return messages.

    Arguments:
    - extracted_advisor -- dict containing ``Advisor_Info`` sub-dict

    Returns: list of validation warning strings (empty means valid)
    """
    _require_imports()
    return validate_required_advisor_info_section(extracted_data = extracted_advisor)


def advisor_validation_should_have_no_warnings(messages: list[str]) -> None:
    """Assert the advisor validation messages list is empty.

    Arguments:
    - messages -- list returned by ``validate_advisor_info``

    Raises AssertionError when messages is non-empty.
    """
    assert messages == [], f"Expected no warnings; got: {messages}"


def advisor_validation_should_mention(messages: list[str], keyword: str) -> None:
    """Assert at least one message contains *keyword* (case-insensitive).

    Arguments:
    - messages -- list returned by ``validate_advisor_info``
    - keyword  -- text fragment that must appear in at least one message

    Raises AssertionError when no message matches.
    """
    matches = [m for m in messages if keyword.lower() in m.lower()]
    assert len(matches) >= 1, (
        f"No warning mentioning '{keyword}'. Messages: {messages}"
    )


# ---------------------------------------------------------------------------
# Extracted client data validation keywords
# ---------------------------------------------------------------------------


def validate_single_client_data() -> tuple[bool, list[str]]:
    """Run ``validate_extracted_client_data`` on built-in valid data.

    Returns: (is_valid, warnings) tuple
    """
    _require_imports()
    return validate_extracted_client_data(extracted_data = _VALID_SINGLE_CLIENT_DATA)


def validate_extracted_data(extracted_data: dict) -> tuple[bool, list[str]]:
    """Run ``validate_extracted_client_data`` on *extracted_data*.

    Arguments:
    - extracted_data -- full extracted worksheet data dict

    Returns: (is_valid, warnings) tuple
    """
    _require_imports()
    return validate_extracted_client_data(extracted_data = extracted_data)


def extracted_data_should_be_valid(validation_result: tuple) -> None:
    """Assert is_valid is True.

    Arguments:
    - validation_result -- (is_valid, warnings) tuple

    Raises AssertionError when is_valid is False.
    """
    is_valid, warnings_list = validation_result
    assert is_valid is True, f"Expected valid; warnings: {warnings_list}"


def extracted_data_should_be_invalid(validation_result: tuple) -> None:
    """Assert is_valid is False.

    Arguments:
    - validation_result -- (is_valid, warnings) tuple

    Raises AssertionError when is_valid is True.
    """
    is_valid, _ = validation_result
    assert is_valid is False, "Expected invalid but got valid"


def validation_warnings_should_be_empty(validation_result: tuple) -> None:
    """Assert warnings list is empty.

    Arguments:
    - validation_result -- (is_valid, warnings) tuple

    Raises AssertionError when warnings is non-empty.
    """
    _, warnings_list = validation_result
    assert warnings_list == [], f"Expected empty warnings; got: {warnings_list}"


def validation_warnings_should_mention(validation_result: tuple, keyword: str) -> None:
    """Assert at least one warning mentions *keyword*.

    Arguments:
    - validation_result -- (is_valid, warnings) tuple
    - keyword           -- text fragment that must appear in at least one warning

    Raises AssertionError when no warning matches.
    """
    _, warnings_list = validation_result
    matches = [w for w in warnings_list if keyword.lower() in w.lower()]
    assert len(matches) >= 1, (
        f"No warning mentioning '{keyword}'. Warnings: {warnings_list}"
    )


# ---------------------------------------------------------------------------
# Checkbox fields keywords
# ---------------------------------------------------------------------------


def get_checkbox_fields_by_section() -> dict:
    """Return the checkbox field map from ``build_checkbox_fields_by_section``.

    Returns: dict mapping section titles to sets of checkbox field keys
    """
    _require_imports()
    return build_checkbox_fields_by_section()


def checkbox_fields_should_be_dict(checkbox_fields: dict) -> None:
    """Assert *checkbox_fields* is a dict.

    Arguments:
    - checkbox_fields -- result from ``get_checkbox_fields_by_section``

    Raises AssertionError when type is not dict.
    """
    assert isinstance(checkbox_fields, dict), (
        f"Expected dict, got {type(checkbox_fields)}"
    )


def checkbox_fields_values_should_be_sets(checkbox_fields: dict) -> None:
    """Assert every value in *checkbox_fields* is a set.

    Arguments:
    - checkbox_fields -- result from ``get_checkbox_fields_by_section``

    Raises AssertionError when any value is not a set.
    """
    for key, value in checkbox_fields.items():
        assert isinstance(value, set), (
            f"Value for section '{key}' is not a set: {type(value)}"
        )


# ---------------------------------------------------------------------------
# worksheet_has_client_partner keywords
# ---------------------------------------------------------------------------


def check_worksheet_has_client_partner(extracted_data: dict) -> bool:
    """Return whether *extracted_data* contains a partner client section.

    Arguments:
    - extracted_data -- full extracted worksheet data dict

    Returns: True when a non-empty client_partner section is present
    """
    _require_imports()
    return worksheet_has_client_partner(extracted_data = extracted_data)


def worksheet_partner_result_should_be_false(result: bool) -> None:
    """Assert *result* is False.

    Arguments:
    - result -- value returned by ``check_worksheet_has_client_partner``

    Raises AssertionError when result is True.
    """
    assert result is False, f"Expected False, got {result}"


def worksheet_partner_result_should_be_true(result: bool) -> None:
    """Assert *result* is True.

    Arguments:
    - result -- value returned by ``check_worksheet_has_client_partner``

    Raises AssertionError when result is False.
    """
    assert result is True, f"Expected True, got {result}"


# ---------------------------------------------------------------------------
# Currency field name keywords
# ---------------------------------------------------------------------------


def check_is_currency_field_name(field_name: str) -> bool:
    """Return whether *field_name* identifies a currency field.

    Arguments:
    - field_name -- dot-separated field name string

    Returns: True when the name is a recognised currency field
    """
    _require_imports()
    return _is_currency_field_name(field_name = field_name)

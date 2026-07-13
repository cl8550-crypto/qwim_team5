"""Behave step definitions for utils_client formatting, validation and worksheet helpers.

Covers:
    - ``_normalize_phone_number_US`` — phone normalisation
    - ``_normalize_text_trademark_symbols`` — trademark symbol replacement
    - ``_safe_numeric`` — safe float conversion
    - ``validate_required_advisor_info_section`` — advisor field validation
    - ``validate_extracted_client_data`` — full extracted data validation
    - ``build_checkbox_fields_by_section`` — checkbox field map construction
    - ``worksheet_has_client_partner`` — partner presence detection

Author:         QWIM Development Team
Version:        1.0.0
"""

from __future__ import annotations

import sys
from pathlib import Path

from behave import given, then, when

# ---------------------------------------------------------------------------
# Project root on sys.path
# ---------------------------------------------------------------------------
_PROJECT_ROOT: Path = Path(__file__).resolve().parents[4]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Module-level import guard
# ---------------------------------------------------------------------------
MODULE_IMPORT_AVAILABLE: bool = True
_import_error_message: str = ""

try:
    from src.clients_QWIM.utils_client import (
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
            f"utils_client source modules could not be imported: {_import_error_message}"
        )


# ---------------------------------------------------------------------------
# Shared fixture helpers
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

_VALID_PERSONAL_INFO: dict = {
    "status_marital": "Married",
    "gender": "Male",
    "tolerance_risk": "Moderate",
    "state": "California",
    "age_current": "55",
    "age_retirement": "65",
    "age_annuity_income_starting": "65",
    "code_zip": "90210",
}

_VALID_SINGLE_CLIENT_DATA: dict = {
    "Advisor_Info": _COMPLETE_ADVISOR_INFO,
    "Personal_Info": {
        "client_primary": _VALID_PERSONAL_INFO,
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


# ===========================================================================
# When — phone normalization
# ===========================================================================


@when(u'I normalize phone number "{phone_input}"')
def step_normalize_phone_number(context, phone_input: str) -> None:
    """Call _normalize_phone_number_US with the provided input."""
    _require_imports()
    context.result_str = _normalize_phone_number_US(value_text = phone_input)


# ===========================================================================
# When — trademark symbol normalization
# ===========================================================================


@when(u'I normalize trademark symbols in "{text_input}"')
def step_normalize_trademark_symbols(context, text_input: str) -> None:
    """Call _normalize_text_trademark_symbols with the provided text."""
    _require_imports()
    context.result_str = _normalize_text_trademark_symbols(value_text = text_input)


# ===========================================================================
# When — safe numeric
# ===========================================================================


@when(u'I call safe numeric on "{value_input}"')
def step_safe_numeric_string(context, value_input: str) -> None:
    """Call _safe_numeric with a string value."""
    _require_imports()
    context.result_float = _safe_numeric(value = value_input)


@when(u"I call safe numeric on none")
def step_safe_numeric_none(context) -> None:
    """Call _safe_numeric with None."""
    _require_imports()
    context.result_float = _safe_numeric(value = None)


# ===========================================================================
# Given — advisor info setups
# ===========================================================================


@given(u"a complete advisor info section")
def step_given_complete_advisor_info(context) -> None:
    """Create a complete advisor info extracted dict."""
    _require_imports()
    context.extracted_advisor = {"Advisor_Info": dict(_COMPLETE_ADVISOR_INFO)}


@given(u"an advisor info section missing name")
def step_given_advisor_missing_name(context) -> None:
    """Create an advisor info dict with name field absent."""
    _require_imports()
    advisor_without_name = {k: v for k, v in _COMPLETE_ADVISOR_INFO.items() if k != "name"}
    context.extracted_advisor = {"Advisor_Info": advisor_without_name}


@given(u'an advisor info section with invalid email "{email_input}"')
def step_given_advisor_invalid_email(context, email_input: str) -> None:
    """Create an advisor info dict with a bad email."""
    _require_imports()
    info = dict(_COMPLETE_ADVISOR_INFO)
    info["email"] = email_input
    context.extracted_advisor = {"Advisor_Info": info}


@given(u'an advisor info section with invalid phone "{phone_input}"')
def step_given_advisor_invalid_phone(context, phone_input: str) -> None:
    """Create an advisor info dict with a bad phone number."""
    _require_imports()
    info = dict(_COMPLETE_ADVISOR_INFO)
    info["phone_number"] = phone_input
    context.extracted_advisor = {"Advisor_Info": info}


# ===========================================================================
# When — advisor validation
# ===========================================================================


@when(u"I validate the advisor info section")
def step_validate_advisor_info(context) -> None:
    """Run validate_required_advisor_info_section on context.extracted_advisor."""
    _require_imports()
    context.advisor_validation_messages = validate_required_advisor_info_section(
        extracted_data = context.extracted_advisor
    )


# ===========================================================================
# Then — advisor validation assertions
# ===========================================================================


@then(u"the advisor validation should produce no warnings")
def step_advisor_no_warnings(context) -> None:
    """Assert no warnings were produced."""
    assert context.advisor_validation_messages == [], (
        f"Expected no warnings, got: {context.advisor_validation_messages}"
    )


@then(u"the advisor validation should report missing name")
def step_advisor_missing_name_reported(context) -> None:
    """Assert at least one warning mentions 'Name' (or 'name')."""
    messages = context.advisor_validation_messages
    matching = [m for m in messages if "name" in m.lower()]
    assert len(matching) >= 1, f"No 'name' warning found in: {messages}"


@then(u"the advisor validation should report invalid email format")
def step_advisor_invalid_email_reported(context) -> None:
    """Assert at least one warning mentions email format."""
    messages = context.advisor_validation_messages
    matching = [m for m in messages if "email" in m.lower()]
    assert len(matching) >= 1, f"No email warning found in: {messages}"


@then(u"the advisor validation should report invalid phone format")
def step_advisor_invalid_phone_reported(context) -> None:
    """Assert at least one warning mentions phone format."""
    messages = context.advisor_validation_messages
    matching = [m for m in messages if "phone" in m.lower()]
    assert len(matching) >= 1, f"No phone warning found in: {messages}"


# ===========================================================================
# Given — extracted client data setups
# ===========================================================================


@given(u"a valid single-client extracted data dict")
def step_given_valid_single_client_data(context) -> None:
    """Use the standard valid single-client data dict."""
    _require_imports()
    context.extracted_data = _VALID_SINGLE_CLIENT_DATA


@given(u'extracted data with marital status "{status}"')
def step_given_invalid_marital_status(context, status: str) -> None:
    """Create extracted data with an invalid marital status."""
    _require_imports()
    import copy
    data = copy.deepcopy(_VALID_SINGLE_CLIENT_DATA)
    data["Personal_Info"]["client_primary"]["status_marital"] = status
    context.extracted_data = data


@given(u"extracted data with a negative asset value")
def step_given_negative_asset(context) -> None:
    """Create extracted data with a negative asset value."""
    _require_imports()
    import copy
    data = copy.deepcopy(_VALID_SINGLE_CLIENT_DATA)
    data["Assets"]["client_primary"]["assets_taxable"] = "-50000"
    context.extracted_data = data


@given(u"extracted data with no partner section")
def step_given_no_partner_section(context) -> None:
    """Create extracted data that has no client_partner data."""
    _require_imports()
    context.extracted_data = {
        "Personal_Info": {
            "client_primary": {"name": "John"},
        }
    }


@given(u"extracted data with a filled partner section")
def step_given_filled_partner_section(context) -> None:
    """Create extracted data that includes a non-empty client_partner section."""
    _require_imports()
    context.extracted_data = {
        "Personal_Info": {
            "client_primary": {"name": "John"},
            "client_partner": {"name": "Jane"},
        }
    }


# ===========================================================================
# When — extracted client data validation
# ===========================================================================


@when(u"I validate the extracted client data")
def step_validate_extracted_data(context) -> None:
    """Run validate_extracted_client_data on context.extracted_data."""
    _require_imports()
    context.is_valid, context.validation_warnings = validate_extracted_client_data(
        extracted_data = context.extracted_data
    )


# ===========================================================================
# Then — extracted client data assertions
# ===========================================================================


@then(u"validation is_valid should be True")
def step_validation_is_valid_true(context) -> None:
    """Assert is_valid is True."""
    assert context.is_valid is True, f"Expected True but got: {context.is_valid}. Warnings: {context.validation_warnings}"


@then(u"validation is_valid should be False")
def step_validation_is_valid_false(context) -> None:
    """Assert is_valid is False."""
    assert context.is_valid is False, f"Expected False but got: {context.is_valid}"


@then(u"validation warnings should be empty")
def step_validation_warnings_empty(context) -> None:
    """Assert warnings list is empty."""
    assert context.validation_warnings == [], (
        f"Expected empty warnings, got: {context.validation_warnings}"
    )


@then(u'validation warnings should mention "{keyword}"')
def step_validation_warnings_mention(context, keyword: str) -> None:
    """Assert at least one warning contains the given keyword."""
    matches = [w for w in context.validation_warnings if keyword.lower() in w.lower()]
    assert len(matches) >= 1, (
        f"No warning mentioning '{keyword}' found. Warnings: {context.validation_warnings}"
    )


# ===========================================================================
# When — build_checkbox_fields_by_section
# ===========================================================================


@when(u"I call build_checkbox_fields_by_section")
def step_call_build_checkbox_fields(context) -> None:
    """Call build_checkbox_fields_by_section and store result."""
    _require_imports()
    context.checkbox_fields_result = build_checkbox_fields_by_section()


# ===========================================================================
# Then — build_checkbox_fields_by_section assertions
# ===========================================================================


@then(u"the result should be a dictionary")
def step_result_is_dict(context) -> None:
    """Assert result is a dict."""
    assert isinstance(context.checkbox_fields_result, dict)


@then(u"every value in the result should be a set")
def step_result_values_are_sets(context) -> None:
    """Assert every value in result is a set."""
    for key, value in context.checkbox_fields_result.items():
        assert isinstance(value, set), f"Value for key '{key}' is not a set: {type(value)}"


# ===========================================================================
# When — worksheet_has_client_partner
# ===========================================================================


@when(u"I call worksheet_has_client_partner")
def step_call_worksheet_has_client_partner(context) -> None:
    """Call worksheet_has_client_partner on context.extracted_data."""
    _require_imports()
    context.result_bool = worksheet_has_client_partner(extracted_data = context.extracted_data)


# ===========================================================================
# Then — shared assertions
# ===========================================================================


@then(u'the result should be "{expected_str}"')
def step_result_equals_string(context, expected_str: str) -> None:
    """Assert the stored string result equals expected_str."""
    assert context.result_str == expected_str, (
        f"Expected '{expected_str}', got '{context.result_str}'"
    )


@then(u"the result should be False")
def step_result_is_false(context) -> None:
    """Assert the stored boolean result is False."""
    assert context.result_bool is False, f"Expected False, got {context.result_bool}"


@then(u"the result should be True")
def step_result_is_true(context) -> None:
    """Assert the stored boolean result is True."""
    assert context.result_bool is True, f"Expected True, got {context.result_bool}"


@then(u"the numeric result should equal {expected_value:g}")
def step_numeric_result_equals(context, expected_value: float) -> None:
    """Assert the stored float result equals expected_value."""
    assert context.result_float == expected_value, (
        f"Expected {expected_value}, got {context.result_float}"
    )

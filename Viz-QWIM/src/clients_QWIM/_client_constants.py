"""Shared constants for utils_client sub-modules.

Contains no PDF library imports (fitz / reportlab).
All constants used by validators, formatters, and worksheet parser are here.
"""

from __future__ import annotations

import re

from typing import Any


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

REGEX_PATTERN_EMAIL_LIGHT = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
REGEX_PATTERN_MARK_REGISTERED = re.compile(r"\(\s*r\s*\)", re.IGNORECASE)
REGEX_PATTERN_MARK_SERVICE = re.compile(r"\(\s*sm\s*\)", re.IGNORECASE)
REGEX_PATTERN_MARK_TRADEMARK = re.compile(r"\(\s*tm\s*\)", re.IGNORECASE)
REGEX_PATTERN_PHONE_NUMBER_DIGITS = re.compile(r"\D+")
REGEX_PATTERN_WHOLE_DOLLAR_AMOUNT = re.compile(r"^-?(?:\d{1,3}(?:,\d{3})+|\d+)$")

# Fitz widget type constant (PDF_WIDGET_TYPE_CHECKBOX == 2 in PyMuPDF)
FITZ_WIDGET_TYPE_CHECKBOX: int = 2

# ---------------------------------------------------------------------------
# Advisor info
# ---------------------------------------------------------------------------

_ADVISOR_INFO_FIELDS_LEFT: list[dict[str, str]] = [
    {"key": "Advisor_Info.name", "field_key": "name", "label": "Name"},
    {"key": "Advisor_Info.title", "field_key": "title", "label": "Title"},
    {"key": "Advisor_Info.credentials", "field_key": "credentials", "label": "Credentials"},
    {"key": "Advisor_Info.team", "field_key": "team", "label": "Team"},
]

_ADVISOR_INFO_FIELDS_RIGHT: list[dict[str, str]] = [
    {"key": "Advisor_Info.firm", "field_key": "firm", "label": "Firm"},
    {"key": "Advisor_Info.email", "field_key": "email", "label": "Email"},
    {"key": "Advisor_Info.phone_number", "field_key": "phone_number", "label": "Phone number"},
    {"key": "Advisor_Info.address", "field_key": "address", "label": "Address"},
]

_ADVISOR_INFO_FIELD_LABELS: dict[str, str] = {
    "name": "Name",
    "title": "Title",
    "credentials": "Credentials",
    "team": "Team",
    "firm": "Firm",
    "email": "Email",
    "phone_number": "Phone number",
    "address": "Address",
}

_ADVISOR_INFO_DEFAULT_VALUES: dict[str, str] = {
    "firm": "QWIM AI Wealth Management",
}

# ---------------------------------------------------------------------------
# Section field definitions (used for checkbox detection)
# ---------------------------------------------------------------------------

_HEADER_FIELDS: list[dict[str, str]] = [
    {"key": "Header.date", "label": "Date (MM/DD/YYYY)"},
]

_PERSONAL_INFO_ROWS: list[dict[str, str | bool]] = [
    {"key": "name", "label": "Name", "is_checkbox": False},
    {"key": "age_current", "label": "Current Age", "is_checkbox": False},
    {"key": "age_retirement", "label": "Retirement Age", "is_checkbox": False},
    {
        "key": "age_annuity_income_starting",
        "label": "Annuity Income Starting Age",
        "is_checkbox": False,
    },
    {"key": "status_marital", "label": "Marital Status", "is_checkbox": False},
    {"key": "gender", "label": "Gender", "is_checkbox": False},
    {"key": "tolerance_risk", "label": "Risk Tolerance", "is_checkbox": False},
    {"key": "state", "label": "State", "is_checkbox": False},
    {"key": "code_zip", "label": "ZIP Code", "is_checkbox": False},
]

_ASSETS_ROWS: list[dict[str, str | bool]] = [
    {"key": "assets_taxable", "label": "Taxable Assets ($)", "is_checkbox": False},
    {"key": "assets_tax_deferred", "label": "Tax-Deferred Assets ($)", "is_checkbox": False},
    {"key": "assets_tax_free", "label": "Tax-Free Assets ($)", "is_checkbox": False},
]

_GOALS_ROWS: list[dict[str, str | bool]] = [
    {"key": "goal_essential", "label": "Essential Annual Expenses ($)", "is_checkbox": False},
    {"key": "goal_important", "label": "Important Annual Expenses ($)", "is_checkbox": False},
    {"key": "goal_aspirational", "label": "Aspirational Annual Expenses ($)", "is_checkbox": False},
    {
        "key": "growth_rate_flag",
        "label": "Apply annual growth rate to expenses?",
        "is_checkbox": True,
    },
    {
        "key": "growth_rate_same_as_inflation_flag",
        "label": "  Is growth rate the same as inflation rate?",
        "is_checkbox": True,
    },
    {"key": "growth_rate", "label": "  Expenses Growth Rate (%)", "is_checkbox": False},
]

_INCOME_ROWS: list[dict[str, str | bool]] = [
    {"key": "income_social_security", "label": "Social Security Income ($)", "is_checkbox": False},
    {
        "key": "social_security_cola_indexed",
        "label": "  Is Social Security COLA-indexed?",
        "is_checkbox": True,
    },
    {"key": "income_pension", "label": "Pension Income ($)", "is_checkbox": False},
    {
        "key": "income_pension_inflation_indexed",
        "label": "  Is pension income inflation-indexed?",
        "is_checkbox": True,
    },
    {
        "key": "income_annuity_existing",
        "label": "Existing Annuity Income ($)",
        "is_checkbox": False,
    },
    {
        "key": "income_annuity_existing_inflation_indexed",
        "label": "  Is existing annuity income inflation-indexed?",
        "is_checkbox": True,
    },
    {"key": "income_other", "label": "Annual Income from Other Sources($)", "is_checkbox": False},
    {
        "key": "income_other_inflation_indexed",
        "label": "  Is income from other sources inflation-indexed?",
        "is_checkbox": True,
    },
]

_SECTIONS: list[dict[str, Any]] = [
    {"title": "Personal Information", "rows": _PERSONAL_INFO_ROWS},
    {"title": "Assets", "rows": _ASSETS_ROWS},
    {"title": "Goals (Annual Expenses)", "rows": _GOALS_ROWS},
    {"title": "Income", "rows": _INCOME_ROWS},
]

_SECTION_KEY_MAP: dict[str, str] = {
    "Personal Information": "Personal_Info",
    "Assets": "Assets",
    "Goals (Annual Expenses)": "Goals",
    "Income": "Income",
}

# ---------------------------------------------------------------------------
# Currency field keys
# ---------------------------------------------------------------------------

_CURRENCY_FIELD_KEYS_BY_SECTION: dict[str, frozenset[str]] = {
    "Assets": frozenset(
        {
            "assets_taxable",
            "assets_tax_deferred",
            "assets_tax_free",
        },
    ),
    "Goals": frozenset(
        {
            "goal_essential",
            "goal_important",
            "goal_aspirational",
        },
    ),
    "Income": frozenset(
        {
            "income_social_security",
            "income_pension",
            "income_annuity_existing",
            "income_other",
        },
    ),
}

_WS_CURRENCY_FIELD_KEYS_CONTINGENCY: dict[str, frozenset[str]] = {
    "LTC_Insurance": frozenset(
        {
            "ltc_benefit_amount",
            "ltc_death_benefit",
            "ltc_amount_to_insure",
            "ltc_amount_inhome_care",
            "ltc_amount_community_assisted",
            "ltc_amount_nursing_care",
        },
    ),
    "Life_Insurance": frozenset(
        {
            "life_insurance_death_benefit",
        },
    ),
}

_CURRENCY_FIELD_TEXT_MAXLEN = 15

_CURRENCY_FIELD_SCRIPT_STROKE = (
    "if (event.change && /[^0-9,]/.test(event.change)) {\n    event.rc = false;\n}\n"
)

_CURRENCY_FIELD_SCRIPT_FORMAT = (
    "if (event.value === null || event.value === undefined || event.value === '') {\n"
    "    event.value = '';\n"
    "} else {\n"
    "    var raw = String(event.value).replace(/[$,\\s]/g, '');\n"
    "    if (!/^\\d+$/.test(raw)) {\n"
    "        event.value = '';\n"
    "    } else {\n"
    "        event.value = raw.replace(/\\B(?=(\\d{3})+(?!\\d))/g, ',');\n"
    "    }\n"
    "}\n"
)

# ---------------------------------------------------------------------------
# Validation choice lists
# ---------------------------------------------------------------------------

VALID_MARITAL_STATUS: list[str] = [
    "Single",
    "Married",
    "Divorced",
    "Widowed",
    "Separated",
    "Domestic Partnership",
]

VALID_GENDER: list[str] = ["Male", "Female", "Other", "Prefer Not to Say"]

VALID_RISK_TOLERANCE: list[str] = [
    "Conservative",
    "Moderate Conservative",
    "Moderate",
    "Moderate Aggressive",
    "Aggressive",
]

VALID_US_STATES: list[str] = [
    "Alabama",
    "Alaska",
    "Arizona",
    "Arkansas",
    "California",
    "Colorado",
    "Connecticut",
    "Delaware",
    "Florida",
    "Georgia",
    "Hawaii",
    "Idaho",
    "Illinois",
    "Indiana",
    "Iowa",
    "Kansas",
    "Kentucky",
    "Louisiana",
    "Maine",
    "Maryland",
    "Massachusetts",
    "Michigan",
    "Minnesota",
    "Mississippi",
    "Missouri",
    "Montana",
    "Nebraska",
    "Nevada",
    "New Hampshire",
    "New Jersey",
    "New Mexico",
    "New York",
    "North Carolina",
    "North Dakota",
    "Ohio",
    "Oklahoma",
    "Oregon",
    "Pennsylvania",
    "Rhode Island",
    "South Carolina",
    "South Dakota",
    "Tennessee",
    "Texas",
    "Utah",
    "Vermont",
    "Virginia",
    "Washington",
    "West Virginia",
    "Wisconsin",
    "Wyoming",
    "District of Columbia",
]

# ---------------------------------------------------------------------------
# New 3-page Inputs Worksheet (generate_inputs_worksheet_PDF)
# ---------------------------------------------------------------------------

_WS_ADVISOR_ROWS: list[dict[str, str]] = [
    {"key": "Advisor_Info.name", "field_key": "name", "label": "Name"},
    {"key": "Advisor_Info.title", "field_key": "title", "label": "Title"},
    {"key": "Advisor_Info.credentials", "field_key": "credentials", "label": "Credentials"},
    {"key": "Advisor_Info.team", "field_key": "team", "label": "Team"},
    {"key": "Advisor_Info.phone_number", "field_key": "phone_number", "label": "Phone Number"},
    {"key": "Advisor_Info.email", "field_key": "email", "label": "Email address"},
    {"key": "Advisor_Info.address", "field_key": "address", "label": "Address"},
]

_WS_PERSONAL_INFO_ROWS: list[dict[str, str | bool]] = [
    {"key": "name", "label": "Name", "is_checkbox": False},
    {"key": "age_current", "label": "Current Age", "is_checkbox": False},
    {"key": "age_retirement", "label": "Retirement Age", "is_checkbox": False},
    {
        "key": "age_annuity_income_starting",
        "label": "Annuity Income Starting Age",
        "is_checkbox": False,
    },
    {"key": "status_marital", "label": "Marital Status", "is_checkbox": False},
    {"key": "gender", "label": "Gender", "is_checkbox": False},
    {"key": "tolerance_risk", "label": "Risk Tolerance", "is_checkbox": False},
    {"key": "state", "label": "State", "is_checkbox": False},
    {"key": "code_zip", "label": "ZIP Code", "is_checkbox": False},
]

_WS_ASSETS_ROWS: list[dict[str, str | bool]] = [
    {"key": "assets_taxable", "label": "Total taxable assets ($)", "is_checkbox": False},
    {"key": "assets_tax_deferred", "label": "Total tax-deferred assets ($)", "is_checkbox": False},
    {"key": "assets_tax_free", "label": "Total tax-free assets ($)", "is_checkbox": False},
]

_WS_EXPENSES_ROWS: list[dict[str, str | bool]] = [
    {"key": "goal_essential", "label": "Essential Annual Expenses ($)", "is_checkbox": False},
    {"key": "goal_important", "label": "Important Annual Expenses ($)", "is_checkbox": False},
    {"key": "goal_aspirational", "label": "Aspirational Annual Expenses ($)", "is_checkbox": False},
    {
        "key": "growth_rate_flag",
        "label": "Apply annual growth rate to expenses?",
        "is_checkbox": True,
    },
    {
        "key": "growth_rate_same_as_inflation_flag",
        "label": "Is growth rate the same as inflation rate?",
        "is_checkbox": True,
    },
    {"key": "growth_rate", "label": "Expenses Growth Rate (%)", "is_checkbox": False},
]

_WS_INCOME_ROWS: list[dict[str, str | bool]] = [
    {
        "key": "income_social_security",
        "label": "Annual Social Security Income ($)",
        "is_checkbox": False,
    },
    {
        "key": "social_security_cola_indexed",
        "label": "Is Social Security COLA-indexed?",
        "is_checkbox": True,
    },
    {"key": "income_pension", "label": "Annual Pension Income ($)", "is_checkbox": False},
    {
        "key": "income_pension_inflation_indexed",
        "label": "Is pension income inflation-indexed?",
        "is_checkbox": True,
    },
    {
        "key": "income_annuity_existing",
        "label": "Annual Income from Existing Annuity ($)",
        "is_checkbox": False,
    },
    {
        "key": "income_annuity_existing_inflation_indexed",
        "label": "Is existing annuity income inflation-indexed?",
        "is_checkbox": True,
    },
    {"key": "income_other", "label": "Annual Income from Other Sources ($)", "is_checkbox": False},
    {
        "key": "income_other_inflation_indexed",
        "label": "Is income from other sources inflation-indexed?",
        "is_checkbox": True,
    },
]

_WS_LTC_ROWS: list[dict[str, str | bool]] = [
    {
        "key": "ltc_existing",
        "label": "Does client have existing LTC insurance?",
        "is_checkbox": True,
        "indent": False,
    },
    {
        "key": "ltc_benefit_amount",
        "label": "Existing Benefit Amount ($)",
        "is_checkbox": False,
        "indent": False,
    },
    {
        "key": "ltc_death_benefit",
        "label": "Existing Death Benefit ($)",
        "is_checkbox": False,
        "indent": False,
    },
    {
        "key": "ltc_amount_to_insure",
        "label": "Amount to Insure ($)",
        "is_checkbox": False,
        "indent": False,
    },
    {
        "key": "ltc_granular_types_flag",
        "label": "Use more granular LTC types?",
        "is_checkbox": True,
        "indent": False,
    },
    {
        "key": "ltc_include_inhome_care",
        "label": "Include LTC in-home care?",
        "is_checkbox": True,
        "indent": True,
    },
    {
        "key": "ltc_amount_inhome_care",
        "label": "Amount In-Home Care ($)",
        "is_checkbox": False,
        "indent": True,
    },
    {
        "key": "ltc_include_community_assisted",
        "label": "Include LTC community assisted living?",
        "is_checkbox": True,
        "indent": True,
    },
    {
        "key": "ltc_amount_community_assisted",
        "label": "Amount Community Assisted Living ($)",
        "is_checkbox": False,
        "indent": True,
    },
    {
        "key": "ltc_include_nursing_care",
        "label": "Include LTC nursing care?",
        "is_checkbox": True,
        "indent": True,
    },
    {
        "key": "ltc_amount_nursing_care",
        "label": "Amount Nursing Care ($)",
        "is_checkbox": False,
        "indent": True,
    },
    {"key": "ltc_state", "label": "State", "is_checkbox": False, "indent": False},
    {"key": "ltc_code_zip", "label": "ZIP Code", "is_checkbox": False, "indent": False},
]

_WS_LIFE_INSURANCE_ROWS: list[dict[str, str | bool]] = [
    {
        "key": "life_insurance_existing",
        "label": "Does client have existing life insurance?",
        "is_checkbox": True,
        "indent": False,
    },
    {
        "key": "life_insurance_death_benefit",
        "label": "Existing Death Benefit ($)",
        "is_checkbox": False,
        "indent": False,
    },
]

_WS_HEALTH_STATUS_CHOICES: list[str] = ["Excellent", "Good", "Fair", "Poor"]

_WS_ROW_HEIGHT = 17
_WS_SECTION_HEADER_HEIGHT = 18
_WS_SECTION_GAP = 9
_WS_FONT_SIZE = 9
_WS_FIELD_HEIGHT = 15
_WS_CHECKBOX_SIZE = 10
_WS_INDENT_PT = 14

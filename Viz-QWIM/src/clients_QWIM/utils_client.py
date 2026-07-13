"""
Client utility functions for QWIM (Quantitative Wealth and Investment Management).

Thin facade — imports and re-exports all public and private symbols from
sub-modules for backward compatibility.

Sub-modules
-----------
_client_constants   : shared constants (regex, field definitions, validation lists)
_client_formatters  : pure Python formatting/normalization helpers
_client_validators  : data validation helpers
_client_worksheet_parser : PDF extraction, normalization, RGA conversion
_client_pdf_builder : PDF generation (reportlab + fitz)

Author
------
QWIM Team

Version
-------
0.8.0 (2026-05-27)
"""

from __future__ import annotations

import fitz  # noqa: F401  # tests patch src.clients_QWIM.utils_client.fitz.open

# ---------------------------------------------------------------------------
# Re-export everything from sub-modules for backward compatibility.
# All public and private symbols remain importable from this module.
# ---------------------------------------------------------------------------
from ._client_constants import (  # noqa: F401
    _ADVISOR_INFO_DEFAULT_VALUES,
    _ADVISOR_INFO_FIELD_LABELS,
    _ADVISOR_INFO_FIELDS_LEFT,
    _ADVISOR_INFO_FIELDS_RIGHT,
    _ASSETS_ROWS,
    _CURRENCY_FIELD_KEYS_BY_SECTION,
    _CURRENCY_FIELD_SCRIPT_FORMAT,
    _CURRENCY_FIELD_SCRIPT_STROKE,
    _CURRENCY_FIELD_TEXT_MAXLEN,
    _GOALS_ROWS,
    _HEADER_FIELDS,
    _INCOME_ROWS,
    _PERSONAL_INFO_ROWS,
    _SECTION_KEY_MAP,
    _SECTIONS,
    _WS_ADVISOR_ROWS,
    _WS_ASSETS_ROWS,
    _WS_CHECKBOX_SIZE,
    _WS_CURRENCY_FIELD_KEYS_CONTINGENCY,
    _WS_EXPENSES_ROWS,
    _WS_FIELD_HEIGHT,
    _WS_FONT_SIZE,
    _WS_HEALTH_STATUS_CHOICES,
    _WS_INCOME_ROWS,
    _WS_INDENT_PT,
    _WS_LIFE_INSURANCE_ROWS,
    _WS_LTC_ROWS,
    _WS_PERSONAL_INFO_ROWS,
    _WS_ROW_HEIGHT,
    _WS_SECTION_GAP,
    _WS_SECTION_HEADER_HEIGHT,
    FITZ_WIDGET_TYPE_CHECKBOX,
    REGEX_PATTERN_EMAIL_LIGHT,
    REGEX_PATTERN_MARK_REGISTERED,
    REGEX_PATTERN_MARK_SERVICE,
    REGEX_PATTERN_MARK_TRADEMARK,
    REGEX_PATTERN_PHONE_NUMBER_DIGITS,
    REGEX_PATTERN_WHOLE_DOLLAR_AMOUNT,
    VALID_GENDER,
    VALID_MARITAL_STATUS,
    VALID_RISK_TOLERANCE,
    VALID_US_STATES,
)
from ._client_formatters import (  # noqa: F401
    _is_currency_field_name,
    _normalize_phone_number_US,
    _normalize_text_trademark_symbols,
    _parse_whole_dollar_amount,
    _safe_numeric,
    _safe_whole_dollar_numeric,
)
from ._client_pdf_builder import (  # noqa: F401
    _apply_currency_field_formatting,
    _build_inputs_worksheet_PDF,
    _build_worksheet_PDF,
    _default_output_dir,
    _draw_advisor_info_section,
    _draw_description,
    _draw_header_fields,
    _draw_section,
    _draw_title,
    _ws_draw_3col_table,
    _ws_draw_advisor_info_section,
    _ws_draw_page1,
    _ws_draw_page2,
    _ws_draw_page3,
    _zip_longest_pairs,
    generate_inputs_worksheet_PDF,
    generate_worksheet_PDF_couple,
    generate_worksheet_PDF_single,
)
from ._client_validators import (  # noqa: F401
    _validate_choice_field,
    _validate_numeric_range,
    build_checkbox_fields_by_section,
    validate_extracted_client_data,
    validate_required_advisor_info_section,
)
from ._client_worksheet_parser import (  # noqa: F401
    _normalize_extracted_advisor_info_section,
    _parse_field_into_result,
    convert_worksheet_data_to_RGA_format,
    extract_client_data_from_worksheet_PDF,
    worksheet_has_client_partner,
)


__all__ = [
    "FITZ_WIDGET_TYPE_CHECKBOX",
    "REGEX_PATTERN_EMAIL_LIGHT",
    "REGEX_PATTERN_MARK_REGISTERED",
    "REGEX_PATTERN_MARK_SERVICE",
    "REGEX_PATTERN_MARK_TRADEMARK",
    "REGEX_PATTERN_PHONE_NUMBER_DIGITS",
    "REGEX_PATTERN_WHOLE_DOLLAR_AMOUNT",
    "VALID_GENDER",
    "VALID_MARITAL_STATUS",
    "VALID_RISK_TOLERANCE",
    "VALID_US_STATES",
    "build_checkbox_fields_by_section",
    "convert_worksheet_data_to_RGA_format",
    "extract_client_data_from_worksheet_PDF",
    "generate_inputs_worksheet_PDF",
    "generate_worksheet_PDF_couple",
    "generate_worksheet_PDF_single",
    "validate_extracted_client_data",
    "validate_required_advisor_info_section",
    "worksheet_has_client_partner",
]


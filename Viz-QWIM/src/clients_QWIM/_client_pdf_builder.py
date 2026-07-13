"""PDF generation helpers for client worksheets.

Functions
---------
generate_worksheet_PDF_single
generate_worksheet_PDF_couple
generate_inputs_worksheet_PDF
_default_output_dir
_build_worksheet_PDF
_build_inputs_worksheet_PDF
_draw_*  (internal drawing helpers)
_ws_draw_*  (new-worksheet drawing helpers)
_apply_currency_field_formatting
_is_currency_field_name
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

from reportlab.lib import colors as rl_colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas as rl_canvas

from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

from ._client_constants import (
    _ADVISOR_INFO_DEFAULT_VALUES,
    _ADVISOR_INFO_FIELDS_LEFT,
    _ADVISOR_INFO_FIELDS_RIGHT,
    _CURRENCY_FIELD_KEYS_BY_SECTION,
    _CURRENCY_FIELD_SCRIPT_FORMAT,
    _CURRENCY_FIELD_SCRIPT_STROKE,
    _CURRENCY_FIELD_TEXT_MAXLEN,
    _HEADER_FIELDS,
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
)


_logger = get_logger(name = __name__)

# ---------------------------------------------------------------------------
# PDF layout constants (depend on reportlab / letter page size)
# ---------------------------------------------------------------------------

_PAGE_WIDTH, _PAGE_HEIGHT = letter  # 612 x 792 points
_MARGIN_LEFT = 50
_MARGIN_RIGHT = 50
_MARGIN_TOP = 50
_MARGIN_BOTTOM = 50
_USABLE_WIDTH = _PAGE_WIDTH - _MARGIN_LEFT - _MARGIN_RIGHT
_ROW_HEIGHT = 20
_SECTION_HEADER_HEIGHT = 24
_SECTION_GAP = 12
_FIELD_HEIGHT = 16
_CHECKBOX_SIZE = 12

_COLOR_HEADER_BG = rl_colors.HexColor("#2C3E50")
_COLOR_HEADER_TEXT = rl_colors.white
_COLOR_SECTION_BG = rl_colors.HexColor("#E8EDF1")
_COLOR_BORDER = rl_colors.HexColor("#BDC3C7")
_COLOR_FIELD_BG = rl_colors.HexColor("#FAFBFC")


# ===================================================================
# Public API — PDF Generation
# ===================================================================


def generate_worksheet_PDF_single(
    *, output_path: Path | None = None) -> Path:
    """Generate a single-client retirement income worksheet as a fillable PDF."""
    if output_path is None:
        output_path = _default_output_dir() / "Inputs_QWIM.pdf"

    return _build_worksheet_PDF(output_path=output_path, is_couple=False)


def generate_worksheet_PDF_couple(
    *, output_path: Path | None = None) -> Path:
    """Generate a couple (primary + partner) retirement income worksheet as a fillable PDF."""
    if output_path is None:
        output_path = _default_output_dir() / "Inputs_QWIM.pdf"

    return _build_worksheet_PDF(output_path=output_path, is_couple=True)


def generate_inputs_worksheet_PDF(
    *, output_path: Path | None = None) -> Path:
    """Generate the 3-page QWIM Input Worksheet PDF."""
    if output_path is None:
        output_path = _default_output_dir() / "Inputs_QWIM.pdf"

    return _build_inputs_worksheet_PDF(output_path=output_path)


# ===================================================================
# Internal helpers — PDF generation
# ===================================================================


def _default_output_dir() -> Path:
    """Return the default output directory ``inputs/QWIM/``."""
    project_root = Path(__file__).resolve().parents[2]
    output_dir = project_root / "inputs" / "QWIM"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _build_worksheet_PDF(*, output_path: Path, is_couple: bool) -> Path:
    """Build the actual PDF with AcroForm fields."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    c = rl_canvas.Canvas(str(output_path), pagesize=letter)
    c.setTitle("Retirement Income Planning Worksheet")

    y = _PAGE_HEIGHT - _MARGIN_TOP

    y = _draw_title(c = c, y = y)
    y = _draw_description(c = c, y = y)
    y = _draw_header_fields(c = c, y = y, is_couple = is_couple)

    needed_advisor_info = (
        _SECTION_HEADER_HEIGHT + len(_ADVISOR_INFO_FIELDS_LEFT) * _ROW_HEIGHT + _SECTION_GAP
    )
    if y - needed_advisor_info < _MARGIN_BOTTOM:  # pragma: no branch
        c.showPage()  # pragma: no cover
        y = _PAGE_HEIGHT - _MARGIN_TOP  # pragma: no cover
    y = _draw_advisor_info_section(c = c, y = y)

    for section_def in _SECTIONS:
        title = section_def["title"]
        rows = section_def["rows"]
        section_dict_key = _SECTION_KEY_MAP[title]

        needed = _SECTION_HEADER_HEIGHT + _ROW_HEIGHT + len(rows) * _ROW_HEIGHT + _SECTION_GAP
        if y - needed < _MARGIN_BOTTOM:
            c.showPage()
            y = _PAGE_HEIGHT - _MARGIN_TOP

        y = _draw_section(c = c, y = y, title = title, rows = rows, section_dict_key = section_dict_key, is_couple = is_couple)

    c.save()

    _apply_currency_field_formatting(output_path = output_path)

    _logger.info("PDF worksheet generated: %s", output_path)
    return output_path.resolve()


def _draw_title(*, c: Any, y: float) -> float:
    """Draw centred title and return new y position."""
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(rl_colors.HexColor("#1A252F"))
    c.drawCentredString(_PAGE_WIDTH / 2, y, "Retirement Income Planning Worksheet")
    y -= 24
    return y


def _draw_description(*, c: Any, y: float) -> float:
    """Draw description paragraph and return new y position."""
    c.setFont("Helvetica", 9)
    c.setFillColor(rl_colors.black)
    lines = [
        "This worksheet is designed to assist you and your advisor with the process of estimating your retirement income needs.",
        " Please take a few minutes to fill in as much information as possible and make note of any special situations,",
        " priorities or questions for discussion.",
    ]
    for line in lines:
        c.drawString(_MARGIN_LEFT, y, line)
        y -= 13
    y -= 6
    return y


def _draw_header_fields(*, c: Any, y: float, is_couple: bool) -> float:
    """Draw the date header field above the Advisor Information section."""
    del is_couple

    header_field = _HEADER_FIELDS[0]
    label_width = 130
    field_x = _MARGIN_LEFT + label_width
    field_width = _USABLE_WIDTH - label_width

    c.setFont("Helvetica", 9)
    c.setFillColor(rl_colors.black)
    c.drawString(_MARGIN_LEFT, y + 3, header_field["label"] + ":")
    c.acroForm.textfield(
        name=header_field["key"],
        x=field_x,
        y=y - 2,
        width=field_width,
        height=_FIELD_HEIGHT,
        borderColor=_COLOR_BORDER,
        fillColor=_COLOR_FIELD_BG,
        textColor=rl_colors.black,
        fontSize=9,
        fieldFlags="",
        forceBorder=True,
    )

    y -= _ROW_HEIGHT + 4
    y -= 8
    return y


def _draw_advisor_info_section(*, c: Any, y: float) -> float:
    """Draw the Advisor Information section above Personal Information."""
    label_width = 72
    gap_between_columns = 16
    field_width = (_USABLE_WIDTH - (label_width * 2) - gap_between_columns) / 2

    x_left_label = _MARGIN_LEFT
    x_left_field = x_left_label + label_width
    x_right_label = x_left_field + field_width + gap_between_columns
    x_right_field = x_right_label + label_width

    c.setFillColor(_COLOR_HEADER_BG)
    c.rect(
        _MARGIN_LEFT,
        y - _SECTION_HEADER_HEIGHT + 4,
        _USABLE_WIDTH,
        _SECTION_HEADER_HEIGHT,
        fill=1,
        stroke=0,
    )
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(_COLOR_HEADER_TEXT)
    c.drawString(_MARGIN_LEFT + 6, y - _SECTION_HEADER_HEIGHT + 11, "Advisor Information")
    y -= _SECTION_HEADER_HEIGHT

    for left_field, right_field in _zip_longest_pairs(
        left = _ADVISOR_INFO_FIELDS_LEFT,
        right = _ADVISOR_INFO_FIELDS_RIGHT,
    ):
        c.setFillColor(rl_colors.white)
        c.rect(_MARGIN_LEFT, y - _ROW_HEIGHT + 4, _USABLE_WIDTH, _ROW_HEIGHT, fill=1, stroke=0)

        c.setStrokeColor(_COLOR_BORDER)
        c.line(_MARGIN_LEFT, y - _ROW_HEIGHT + 4, _MARGIN_LEFT + _USABLE_WIDTH, y - _ROW_HEIGHT + 4)

        for field_def, x_label, x_field in (
            (left_field, x_left_label, x_left_field),
            (right_field, x_right_label, x_right_field),
        ):
            if field_def is None:  # pragma: no cover
                continue  # pragma: no cover

            field_key_name = field_def["field_key"]
            default_value = _ADVISOR_INFO_DEFAULT_VALUES.get(field_key_name, "")

            c.setFont("Helvetica", 9)
            c.setFillColor(rl_colors.black)
            c.drawString(x_label, y - _ROW_HEIGHT + 9, field_def["label"])
            c.acroForm.textfield(
                name=field_def["key"],
                value=default_value,
                x=x_field,
                y=y - _ROW_HEIGHT + 5,
                width=field_width - 6,
                height=_FIELD_HEIGHT,
                borderColor=_COLOR_BORDER,
                fillColor=_COLOR_FIELD_BG,
                textColor=rl_colors.black,
                fontSize=9,
                fieldFlags="",
                forceBorder=True,
            )

        y -= _ROW_HEIGHT

    y -= _SECTION_GAP
    return y


def _draw_section(
    *, c: Any, y: float, title: str, rows: list[dict[str, Any]], section_dict_key: str, is_couple: bool) -> float:
    """Draw one section (header row + data rows with form fields)."""
    if is_couple:
        col_label_w = _USABLE_WIDTH * 0.40
        col_val_w = _USABLE_WIDTH * 0.30
    else:
        col_label_w = _USABLE_WIDTH * 0.55
        col_val_w = _USABLE_WIDTH * 0.45

    x_label = _MARGIN_LEFT
    x_primary = x_label + col_label_w
    x_partner = x_primary + col_val_w if is_couple else None

    c.setFillColor(_COLOR_HEADER_BG)
    c.rect(
        x_label,
        y - _SECTION_HEADER_HEIGHT + 4,
        _USABLE_WIDTH,
        _SECTION_HEADER_HEIGHT,
        fill=1,
        stroke=0,
    )
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(_COLOR_HEADER_TEXT)
    c.drawString(x_label + 6, y - _SECTION_HEADER_HEIGHT + 11, title)
    y -= _SECTION_HEADER_HEIGHT

    c.setFillColor(_COLOR_SECTION_BG)
    c.rect(x_label, y - _ROW_HEIGHT + 4, _USABLE_WIDTH, _ROW_HEIGHT, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(rl_colors.black)
    c.drawString(x_label + 4, y - _ROW_HEIGHT + 9, "Field")
    c.drawString(x_primary + 4, y - _ROW_HEIGHT + 9, "Client Primary")
    if is_couple and x_partner is not None:
        c.drawString(x_partner + 4, y - _ROW_HEIGHT + 9, "Client Partner")
    y -= _ROW_HEIGHT

    for row_def in rows:
        key = row_def["key"]
        label = row_def["label"]
        is_cb = row_def.get("is_checkbox", False)

        c.setFillColor(rl_colors.white)
        c.rect(x_label, y - _ROW_HEIGHT + 4, _USABLE_WIDTH, _ROW_HEIGHT, fill=1, stroke=0)

        c.setStrokeColor(_COLOR_BORDER)
        c.line(x_label, y - _ROW_HEIGHT + 4, x_label + _USABLE_WIDTH, y - _ROW_HEIGHT + 4)

        c.setFont("Helvetica", 9)
        c.setFillColor(rl_colors.black)
        c.drawString(x_label + 6, y - _ROW_HEIGHT + 9, label)

        clients = ["client_primary"]
        x_positions = [x_primary]
        if is_couple and x_partner is not None:
            clients.append("client_partner")
            x_positions.append(x_partner)

        for client_role, x_pos in zip(clients, x_positions, strict=True):
            field_name = f"{section_dict_key}.{client_role}.{key}"
            if is_cb:
                cb_x = x_pos + (col_val_w - _CHECKBOX_SIZE) / 2
                c.acroForm.checkbox(
                    name=field_name,
                    x=cb_x,
                    y=y - _ROW_HEIGHT + 6,
                    size=_CHECKBOX_SIZE,
                    checked=False,
                    buttonStyle="check",
                    borderColor=_COLOR_BORDER,
                    fillColor=_COLOR_FIELD_BG,
                    forceBorder=True,
                )
            else:
                fw = col_val_w - 10
                c.acroForm.textfield(
                    name=field_name,
                    x=x_pos + 4,
                    y=y - _ROW_HEIGHT + 5,
                    width=fw,
                    height=_FIELD_HEIGHT,
                    borderColor=_COLOR_BORDER,
                    fillColor=_COLOR_FIELD_BG,
                    textColor=rl_colors.black,
                    fontSize=9,
                    fieldFlags="",
                    forceBorder=True,
                )

        y -= _ROW_HEIGHT

    y -= _SECTION_GAP
    return y


def _zip_longest_pairs(
    *, left: list[Any], right: list[Any]) -> list[tuple[Any, Any]]:
    """Pair up two lists, padding the shorter one with None."""
    max_len = max(len(left), len(right))
    result = []
    for i in range(max_len):
        l_item = left[i] if i < len(left) else None
        r_item = right[i] if i < len(right) else None
        result.append((l_item, r_item))
    return result


# ===================================================================
# Internal helpers — New 3-page Inputs Worksheet PDF generation
# ===================================================================


def _build_inputs_worksheet_PDF(*, output_path: Path) -> Path:
    """Build the 3-page QWIMInputs Worksheet PDF."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    c = rl_canvas.Canvas(str(output_path), pagesize=letter)
    c.setTitle("QWIM Inputs Worksheet")

    _ws_draw_page1(c = c)
    c.showPage()

    _ws_draw_page2(c = c)
    c.showPage()

    _ws_draw_page3(c = c)

    c.save()

    _apply_currency_field_formatting(output_path = output_path)

    _logger.info("Inputs worksheet PDF generated: %s", output_path)
    return output_path.resolve()


def _ws_draw_page1(*, c: Any) -> None:
    """Draw page 1: title, subtitle, date field, Advisor Information table."""
    y = _PAGE_HEIGHT - _MARGIN_TOP

    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(rl_colors.HexColor("#1A252F"))
    c.drawCentredString(_PAGE_WIDTH / 2, y, "QWIM Inputs Worksheet")
    y -= 20

    c.setFont("Helvetica", 9)
    c.setFillColor(rl_colors.black)
    c.drawString(
        _MARGIN_LEFT,
        y,
        "Use the worksheet below to upload information into the QWIM dashboard.",
    )
    y -= 28

    label_width_date = 110
    c.setFont("Helvetica", 9)
    c.drawString(_MARGIN_LEFT, y + 3, "Date (MM/DD/YYYY):")
    c.acroForm.textfield(
        name="Header.date",
        x=_MARGIN_LEFT + label_width_date,
        y=y - 2,
        width=_USABLE_WIDTH - label_width_date,
        height=_FIELD_HEIGHT,
        borderColor=_COLOR_BORDER,
        fillColor=_COLOR_FIELD_BG,
        textColor=rl_colors.black,
        fontSize=9,
        fieldFlags="",
        forceBorder=True,
    )
    y -= _ROW_HEIGHT + 28

    _ws_draw_advisor_info_section(c = c, y = y)


def _ws_draw_advisor_info_section(*, c: Any, y: float) -> float:
    """Draw the Advisor Information table for the new worksheet (2-column layout)."""
    label_col_w = 130
    field_col_w = _USABLE_WIDTH - label_col_w

    c.setFillColor(_COLOR_HEADER_BG)
    c.rect(
        _MARGIN_LEFT,
        y - _SECTION_HEADER_HEIGHT + 4,
        _USABLE_WIDTH,
        _SECTION_HEADER_HEIGHT,
        fill=1,
        stroke=0,
    )
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(_COLOR_HEADER_TEXT)
    c.drawString(_MARGIN_LEFT + 6, y - _SECTION_HEADER_HEIGHT + 11, "Advisor Information")
    y -= _SECTION_HEADER_HEIGHT

    for row_def in _WS_ADVISOR_ROWS:
        c.setFillColor(rl_colors.white)
        c.rect(_MARGIN_LEFT, y - _ROW_HEIGHT + 4, _USABLE_WIDTH, _ROW_HEIGHT, fill=1, stroke=0)
        c.setStrokeColor(_COLOR_BORDER)
        c.line(_MARGIN_LEFT, y - _ROW_HEIGHT + 4, _MARGIN_LEFT + _USABLE_WIDTH, y - _ROW_HEIGHT + 4)

        c.setFont("Helvetica", 9)
        c.setFillColor(rl_colors.black)
        c.drawString(_MARGIN_LEFT + 6, y - _ROW_HEIGHT + 9, row_def["label"])

        c.acroForm.textfield(
            name=row_def["key"],
            x=_MARGIN_LEFT + label_col_w,
            y=y - _ROW_HEIGHT + 5,
            width=field_col_w - 6,
            height=_FIELD_HEIGHT,
            borderColor=_COLOR_BORDER,
            fillColor=_COLOR_FIELD_BG,
            textColor=rl_colors.black,
            fontSize=9,
            fieldFlags="",
            forceBorder=True,
        )
        y -= _ROW_HEIGHT

    return y


def _ws_draw_page2(*, c: Any) -> None:
    """Draw page 2: Client Information (4 tables)."""
    y = _PAGE_HEIGHT - _MARGIN_TOP

    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(rl_colors.HexColor("#1A252F"))
    c.drawCentredString(_PAGE_WIDTH / 2, y, "Client Information")
    y -= 42

    col_label_w = _USABLE_WIDTH * 0.44
    col_val_w = (_USABLE_WIDTH - col_label_w) / 2
    x_label = _MARGIN_LEFT
    x_primary = x_label + col_label_w
    x_partner = x_primary + col_val_w

    y = _ws_draw_3col_table(
        c = c,
        y = y,
        title="Personal Information",
        rows=_WS_PERSONAL_INFO_ROWS,
        section_dict_key="Personal_Info",
        col_label_w=col_label_w,
        col_val_w=col_val_w,
        x_label=x_label,
        x_primary=x_primary,
        x_partner=x_partner,
    )
    y -= 20

    y = _ws_draw_3col_table(
        c = c,
        y = y,
        title="Assets",
        rows=_WS_ASSETS_ROWS,
        section_dict_key="Assets",
        col_label_w=col_label_w,
        col_val_w=col_val_w,
        x_label=x_label,
        x_primary=x_primary,
        x_partner=x_partner,
    )
    y -= 20

    y = _ws_draw_3col_table(
        c = c,
        y = y,
        title="Expenses in Retirement",
        rows=_WS_EXPENSES_ROWS,
        section_dict_key="Goals",
        col_label_w=col_label_w,
        col_val_w=col_val_w,
        x_label=x_label,
        x_primary=x_primary,
        x_partner=x_partner,
    )
    y -= 20

    y = _ws_draw_3col_table(
        c = c,
        y = y,
        title="Income in Retirement",
        rows=_WS_INCOME_ROWS,
        section_dict_key="Income",
        col_label_w=col_label_w,
        col_val_w=col_val_w,
        x_label=x_label,
        x_primary=x_primary,
        x_partner=x_partner,
    )
    y -= 10

    c.setFont("Helvetica-Oblique", 7)
    c.setFillColor(rl_colors.HexColor("#555555"))
    note_text = (
        "Note: Other income sources include wages, business income and rental income. "
        "Please do not include dividend or interest income."
    )
    c.drawString(_MARGIN_LEFT, y, note_text)


def _ws_draw_page3(*, c: Any) -> None:
    """Draw page 3: Contingency Planning (health status, LTC, Life Insurance)."""
    y = _PAGE_HEIGHT - _MARGIN_TOP

    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(rl_colors.HexColor("#1A252F"))
    c.drawCentredString(_PAGE_WIDTH / 2, y, "Contingency planning")
    y -= 28

    c.setFont("Helvetica", 9)
    c.setFillColor(rl_colors.black)
    health_line_text = (
        "Please ask client(s) to describe their health relative to people in their age group"
    )
    c.drawString(_MARGIN_LEFT, y + 3, health_line_text)

    text_w = c.stringWidth(health_line_text, "Helvetica", 9)
    combo_gap = 8
    combo_w = (_USABLE_WIDTH - text_w - 2 * combo_gap) / 2
    combo_x_primary = _MARGIN_LEFT + text_w + combo_gap
    combo_x_partner = combo_x_primary + combo_w + combo_gap

    for field_name, x_pos in (
        ("Contingency.client_primary.health_status", combo_x_primary),
        ("Contingency.client_partner.health_status", combo_x_partner),
    ):
        c.acroForm.listbox(
            name=field_name,
            x=x_pos,
            y=y - 2,
            width=max(combo_w, 60),
            height=_FIELD_HEIGHT + 2,
            options=_WS_HEALTH_STATUS_CHOICES,
            value=_WS_HEALTH_STATUS_CHOICES[1],
            borderColor=_COLOR_BORDER,
            fillColor=_COLOR_FIELD_BG,
            textColor=rl_colors.black,
            fontSize=9,
            fieldFlags="",
            forceBorder=True,
        )

    y -= _ROW_HEIGHT + 28

    col_label_w = _USABLE_WIDTH * 0.44
    col_val_w = (_USABLE_WIDTH - col_label_w) / 2
    x_label = _MARGIN_LEFT
    x_primary = x_label + col_label_w
    x_partner = x_primary + col_val_w

    y = _ws_draw_3col_table(
        c = c,
        y = y,
        title="Long-Term Care (LTC) Insurance Information",
        rows=_WS_LTC_ROWS,
        section_dict_key="LTC_Insurance",
        col_label_w=col_label_w,
        col_val_w=col_val_w,
        x_label=x_label,
        x_primary=x_primary,
        x_partner=x_partner,
    )
    y -= 28

    _ws_draw_3col_table(
        c = c,
        y = y,
        title="Life Insurance Information",
        rows=_WS_LIFE_INSURANCE_ROWS,
        section_dict_key="Life_Insurance",
        col_label_w=col_label_w,
        col_val_w=col_val_w,
        x_label=x_label,
        x_primary=x_primary,
        x_partner=x_partner,
    )


def _ws_draw_3col_table(
    *, c: Any, y: float, title: str, rows: list[dict[str, Any]], section_dict_key: str, col_label_w: float, col_val_w: float, x_label: float, x_primary: float, x_partner: float) -> float:
    """Draw a compact 3-column table (label | Client Primary | Client Partner)."""
    c.setFillColor(_COLOR_HEADER_BG)
    c.rect(
        x_label,
        y - _WS_SECTION_HEADER_HEIGHT + 4,
        _USABLE_WIDTH,
        _WS_SECTION_HEADER_HEIGHT,
        fill=1,
        stroke=0,
    )
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(_COLOR_HEADER_TEXT)
    c.drawString(x_label + 6, y - _WS_SECTION_HEADER_HEIGHT + 7, title)
    y -= _WS_SECTION_HEADER_HEIGHT

    c.setFillColor(_COLOR_SECTION_BG)
    c.rect(x_label, y - _WS_ROW_HEIGHT + 4, _USABLE_WIDTH, _WS_ROW_HEIGHT, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", _WS_FONT_SIZE)
    c.setFillColor(rl_colors.black)
    c.drawString(x_primary + 4, y - _WS_ROW_HEIGHT + 5, "Client Primary")
    c.drawString(x_partner + 4, y - _WS_ROW_HEIGHT + 5, "Client Partner")
    y -= _WS_ROW_HEIGHT

    for row_def in rows:
        key = row_def["key"]
        label = str(row_def["label"])
        is_cb = bool(row_def.get("is_checkbox", False))
        indent = bool(row_def.get("indent", False))

        c.setFillColor(rl_colors.white)
        c.rect(x_label, y - _WS_ROW_HEIGHT + 4, _USABLE_WIDTH, _WS_ROW_HEIGHT, fill=1, stroke=0)
        c.setStrokeColor(_COLOR_BORDER)
        c.line(x_label, y - _WS_ROW_HEIGHT + 4, x_label + _USABLE_WIDTH, y - _WS_ROW_HEIGHT + 4)

        x_label_text = x_label + 6 + (_WS_INDENT_PT if indent else 0)
        c.setFont("Helvetica", _WS_FONT_SIZE)
        c.setFillColor(rl_colors.black)
        label_y = y - _WS_ROW_HEIGHT + 4 + ((_WS_ROW_HEIGHT - _WS_FONT_SIZE) / 2)
        c.drawString(x_label_text, label_y, label)

        for client_role, x_pos in (
            ("client_primary", x_primary),
            ("client_partner", x_partner),
        ):
            field_name = f"{section_dict_key}.{client_role}.{key}"
            if is_cb:
                cb_x = x_pos + (col_val_w - _WS_CHECKBOX_SIZE) / 2
                c.acroForm.checkbox(
                    name=field_name,
                    x=cb_x,
                    y=y - _WS_ROW_HEIGHT + 4,
                    size=_WS_CHECKBOX_SIZE,
                    checked=False,
                    buttonStyle="check",
                    borderColor=_COLOR_BORDER,
                    fillColor=_COLOR_FIELD_BG,
                    forceBorder=True,
                )
            else:
                fw = col_val_w - 8
                c.acroForm.textfield(
                    name=field_name,
                    x=x_pos + 4,
                    y=y - _WS_ROW_HEIGHT + 3,
                    width=fw,
                    height=_WS_FIELD_HEIGHT,
                    borderColor=_COLOR_BORDER,
                    fillColor=_COLOR_FIELD_BG,
                    textColor=rl_colors.black,
                    fontSize=_WS_FONT_SIZE,
                    fieldFlags="",
                    forceBorder=True,
                )

        y -= _WS_ROW_HEIGHT

    y -= _WS_SECTION_GAP
    return y


def _apply_currency_field_formatting(*, output_path: Path) -> None:
    """Attach comma-formatting scripts to all currency text fields in *output_path*."""
    if not isinstance(output_path, Path):
        output_path = Path(output_path)

    if not output_path.is_file():
        return

    doc = fitz.open(str(output_path))
    try:
        modified = False
        for page in doc:
            for widget in page.widgets():
                widget_any: Any = widget
                field_name = widget_any.field_name
                if field_name is None or not _is_currency_field_name(field_name = field_name):
                    continue

                widget_any.script_format = _CURRENCY_FIELD_SCRIPT_FORMAT
                widget_any.script_blur = _CURRENCY_FIELD_SCRIPT_FORMAT
                widget_any.script_stroke = _CURRENCY_FIELD_SCRIPT_STROKE
                widget_any.text_maxlen = _CURRENCY_FIELD_TEXT_MAXLEN
                widget_any.update()
                modified = True

        if modified:
            doc.saveIncr()
    finally:
        doc.close()


def _is_currency_field_name(*, field_name: str) -> bool:
    """Return True when *field_name* identifies a dollar amount text field."""
    parts = field_name.split(".")
    if len(parts) != 3:
        return False

    section_key = parts[0]
    field_key = parts[2]

    if field_key in _CURRENCY_FIELD_KEYS_BY_SECTION.get(section_key, frozenset()):
        return True

    return field_key in _WS_CURRENCY_FIELD_KEYS_CONTINGENCY.get(section_key, frozenset())

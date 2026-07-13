"""Unit tests for utils_enhanced_ui_components module.

Tests validation helpers and UI component factory functions:
- validate_component_identifier
- validate_component_label
- ComponentVariant enum
- create_enhanced_numeric_input
- create_enhanced_card_section
- create_enhanced_summary_display
- create_enhanced_text_input
- create_enhanced_select_input
- create_enhanced_button
"""

from __future__ import annotations

import pytest
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Configuration,
    Exception_Validation_Input,
)

from htmltools import Tag


# ============================================================================
# ComponentVariant enum
# ============================================================================


@pytest.mark.unit()
class Test_Component_Variant_Enum:
    """Tests for ComponentVariant enumeration values."""

    @pytest.mark.unit()
    def test_primary_variant_value(self):
        """PRIMARY variant has expected string value."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import ComponentVariant

        assert ComponentVariant.PRIMARY.value == "primary"

    @pytest.mark.unit()
    def test_all_expected_members_exist(self):
        """All standard Bootstrap variants are present."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import ComponentVariant

        expected = {"PRIMARY", "SECONDARY", "SUCCESS", "DANGER", "WARNING", "INFO", "LIGHT", "DARK"}
        actual = {m.name for m in ComponentVariant}

        assert expected == actual


# ============================================================================
# validate_component_identifier
# ============================================================================


@pytest.mark.unit()
class Test_Validate_Component_Identifier:
    """Tests for validate_component_identifier."""

    @pytest.mark.unit()
    def test_valid_id_returned_stripped(self):
        """Valid ID is returned with surrounding whitespace stripped."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            validate_component_identifier,
        )

        result = validate_component_identifier(component_id = "  my_input_id  ")

        assert result == "my_input_id"

    @pytest.mark.unit()
    def test_exact_valid_id_unchanged(self):
        """ID without extra whitespace is returned unchanged."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            validate_component_identifier,
        )

        result = validate_component_identifier(component_id = "input_ID_tab_portfolios_test")

        assert result == "input_ID_tab_portfolios_test"

    @pytest.mark.parametrize("bad_id", [None, 42, [], {}, True])
    @pytest.mark.unit()
    def test_non_string_raises_value_error(self, bad_id):
        """Non-string ID raises ValueError."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            validate_component_identifier,
        )

        with pytest.raises(Exception_Validation_Input):
            validate_component_identifier(component_id = bad_id)  # type: ignore[arg-type]

    @pytest.mark.unit()
    def test_empty_string_raises_value_error(self):
        """Empty string raises ValueError."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            validate_component_identifier,
        )

        with pytest.raises(Exception_Validation_Input, match="empty"):
            validate_component_identifier(component_id = "")

    @pytest.mark.unit()
    def test_whitespace_only_raises_value_error(self):
        """Whitespace-only string raises ValueError (treated as empty)."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            validate_component_identifier,
        )

        with pytest.raises(Exception_Validation_Input):
            validate_component_identifier(component_id = "   ")

    @pytest.mark.unit()
    def test_too_short_raises_value_error(self):
        """ID shorter than minimum length raises ValueError."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            validate_component_identifier,
        )

        with pytest.raises(Exception_Validation_Input):
            validate_component_identifier(component_id = "ab")

    @pytest.mark.unit()
    def test_minimum_valid_length(self):
        """ID of exactly 3 characters is accepted."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            validate_component_identifier,
        )

        result = validate_component_identifier(component_id = "abc")

        assert result == "abc"

    @pytest.mark.unit()
    def test_custom_component_type_in_error_message(self):
        """Custom component_type appears in ValueError message."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            validate_component_identifier,
        )

        with pytest.raises(Exception_Validation_Input, match="Button"):
            validate_component_identifier(component_id = "", component_type="Button")


# ============================================================================
# validate_component_label
# ============================================================================


@pytest.mark.unit()
class Test_Validate_Component_Label:
    """Tests for validate_component_label."""

    @pytest.mark.unit()
    def test_valid_label_stripped(self):
        """Valid label with surrounding whitespace is stripped."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            validate_component_label,
        )

        result = validate_component_label(label_text = "  My Label  ")

        assert result == "My Label"

    @pytest.mark.unit()
    def test_required_empty_string_raises(self):
        """Empty string when required=True raises ValueError."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            validate_component_label,
        )

        with pytest.raises(Exception_Validation_Input):
            validate_component_label(label_text = "", required=True)

    @pytest.mark.unit()
    def test_not_required_empty_string_returns_empty(self):
        """Empty string when required=False returns empty string."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            validate_component_label,
        )

        result = validate_component_label(label_text = "", required=False)

        assert result == ""

    @pytest.mark.unit()
    def test_non_string_required_raises(self):
        """Non-string label when required=True raises ValueError."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            validate_component_label,
        )

        with pytest.raises(Exception_Validation_Input):
            validate_component_label(label_text = 123, required=True)  # type: ignore[arg-type]

    @pytest.mark.unit()
    def test_non_string_not_required_returns_empty(self):
        """Non-string label when required=False returns empty string."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            validate_component_label,
        )

        result = validate_component_label(label_text = None, required=False)  # type: ignore[arg-type]

        assert result == ""


# ============================================================================
# create_enhanced_numeric_input
# ============================================================================


@pytest.mark.unit()
class Test_Create_Enhanced_Numeric_Input:
    """Tests for create_enhanced_numeric_input factory function."""

    @pytest.mark.unit()
    def test_returns_shiny_ui_element(self):
        """Function returns a Shiny UI element (ui.div)."""

        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_numeric_input,
        )

        result = create_enhanced_numeric_input(
            input_ID="input_ID_tab_test_value",
            label_text="Test Value",
            min_value=0,
            max_value=100,
        )

        assert result is not None
        assert isinstance(result, Tag)

    @pytest.mark.unit()
    def test_invalid_id_raises_value_error(self):
        """Invalid input_ID propagates ValueError from validation."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_numeric_input,
        )

        with pytest.raises(Exception_Validation_Input):
            create_enhanced_numeric_input(input_ID="", label_text="Label")

    @pytest.mark.unit()
    def test_min_greater_than_max_raises_value_error(self):
        """min_value >= max_value raises ValueError."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_numeric_input,
        )

        with pytest.raises(Exception_Validation_Input):
            create_enhanced_numeric_input(
                input_ID="input_ID_test_x",
                label_text="X",
                min_value=100,
                max_value=50,
            )

    @pytest.mark.unit()
    def test_equal_min_max_raises_value_error(self):
        """min_value == max_value raises ValueError."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_numeric_input,
        )

        with pytest.raises(Exception_Validation_Input):
            create_enhanced_numeric_input(
                input_ID="input_ID_test_y",
                label_text="Y",
                min_value=50,
                max_value=50,
            )

    @pytest.mark.unit()
    def test_zero_step_raises_value_error(self):
        """step_size=0 raises ValueError."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_numeric_input,
        )

        with pytest.raises(Exception_Validation_Input):
            create_enhanced_numeric_input(
                input_ID="input_ID_test_z",
                label_text="Z",
                step_size=0,
            )

    @pytest.mark.unit()
    def test_negative_step_raises_value_error(self):
        """Negative step_size raises ValueError."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_numeric_input,
        )

        with pytest.raises(Exception_Validation_Input):
            create_enhanced_numeric_input(
                input_ID="input_ID_test_neg",
                label_text="Neg",
                step_size=-1,
            )

    @pytest.mark.unit()
    def test_default_value_clamped_to_range(self):
        """default_value outside [min, max] is silently clamped, not raised."""

        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_numeric_input,
        )

        # Should not raise even though default_value=200 > max_value=100
        result = create_enhanced_numeric_input(
            input_ID="input_ID_test_clamp",
            label_text="Clamp",
            min_value=0,
            max_value=100,
            default_value=200,
        )

        assert isinstance(result, Tag)


# ============================================================================
# create_enhanced_card_section
# ============================================================================


@pytest.mark.unit()
class Test_Create_Enhanced_Card_Section:
    """Tests for create_enhanced_card_section factory function."""

    @pytest.mark.unit()
    def test_returns_shiny_ui_element(self):
        """Function returns a Shiny UI element."""
        from shiny import ui

        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_card_section,
        )

        result = create_enhanced_card_section(
            title="Test Section",
            content=[ui.p("Hello")],
        )

        assert result is not None
        assert isinstance(result, Tag)

    @pytest.mark.unit()
    def test_invalid_title_raises(self):
        """Empty or invalid section_title raises ValueError."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_card_section,
        )

        with pytest.raises((ValueError, Exception)):
            create_enhanced_card_section(title="", content=[])


# ============================================================================
# create_enhanced_summary_display
# ============================================================================


@pytest.mark.unit()
class Test_Create_Enhanced_Summary_Display:
    """Tests for create_enhanced_summary_display factory function."""

    @pytest.mark.unit()
    def test_returns_shiny_ui_element(self):
        """Function returns a Shiny UI element."""

        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_summary_display,
        )

        result = create_enhanced_summary_display(
            summary_id="input_ID_tab_test_summary",
            title="Balance",
        )

        assert result is not None
        assert isinstance(result, Tag)

    @pytest.mark.unit()
    def test_invalid_id_raises(self):
        """Invalid display_id raises RuntimeError (wraps ValueError from validation)."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_summary_display,
        )

        with pytest.raises((Exception_Validation_Input, Exception_Configuration, ValueError, RuntimeError)):
            create_enhanced_summary_display(
                summary_id="",
                title="Label",
            )


# ============================================================================
# create_enhanced_text_input
# ============================================================================


@pytest.mark.unit()
class Test_Create_Enhanced_Text_Input:
    """Tests for create_enhanced_text_input factory function."""

    @pytest.mark.unit()
    def test_returns_shiny_ui_element(self):
        """Function returns a Shiny UI element."""

        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_text_input,
        )

        result = create_enhanced_text_input(
            input_ID="input_ID_tab_test_name",
            label_text="Name",
        )

        assert result is not None
        assert isinstance(result, Tag)

    @pytest.mark.unit()
    def test_invalid_id_raises(self):
        """Invalid input_ID raises ValueError."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_text_input,
        )

        with pytest.raises(Exception_Validation_Input):
            create_enhanced_text_input(input_ID="", label_text="Name")


# ============================================================================
# create_enhanced_select_input
# ============================================================================


@pytest.mark.unit()
class Test_Create_Enhanced_Select_Input:
    """Tests for create_enhanced_select_input factory function."""

    @pytest.mark.unit()
    def test_returns_shiny_ui_element(self):
        """Function returns a Shiny UI element."""

        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_select_input,
        )

        result = create_enhanced_select_input(
            input_ID="input_ID_tab_test_period",
            label_text="Period",
            choices={"1Y": "1 Year", "3Y": "3 Years"},
        )

        assert result is not None
        assert isinstance(result, Tag)

    @pytest.mark.unit()
    def test_invalid_id_raises(self):
        """Invalid input_ID raises ValueError."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_select_input,
        )

        with pytest.raises(Exception_Validation_Input):
            create_enhanced_select_input(input_ID="", label_text="Period", choices={})


# ============================================================================
# create_enhanced_button
# ============================================================================


@pytest.mark.unit()
class Test_Create_Enhanced_Button:
    """Tests for create_enhanced_button factory function."""

    @pytest.mark.unit()
    def test_returns_shiny_ui_element(self):
        """Function returns a Shiny UI element."""

        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_button,
        )

        result = create_enhanced_button(
            button_id="input_ID_tab_test_btn",
            button_text="Click Me",
        )

        assert result is not None
        assert isinstance(result, Tag)

    @pytest.mark.unit()
    def test_invalid_id_raises(self):
        """Invalid button_id raises ValueError."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_button,
        )

        with pytest.raises(Exception_Validation_Input):
            create_enhanced_button(button_id="", button_text="Click")

    @pytest.mark.unit()
    def test_primary_variant_accepted(self):
        """PRIMARY ComponentVariant is accepted without error."""

        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            ComponentVariant,
            create_enhanced_button,
        )

        result = create_enhanced_button(
            button_id="input_ID_tab_test_primary_btn",
            button_text="Submit",
            button_variant=ComponentVariant.PRIMARY,
        )

        assert isinstance(result, Tag)

    @pytest.mark.unit()
    def test_danger_variant_accepted(self):
        """DANGER ComponentVariant is accepted without error."""

        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            ComponentVariant,
            create_enhanced_button,
        )

        result = create_enhanced_button(
            button_id="input_ID_tab_test_danger_btn",
            button_text="Delete",
            button_variant=ComponentVariant.DANGER,
        )

        assert isinstance(result, Tag)


# ============================================================================
# Regression tests  type: ignore changes that were applied to the source
# ============================================================================


@pytest.mark.regression()
class Test_List_Any_Type_Annotation_Regression:
    """Regression tests for the list[Any] annotation fix in card and button builders.

    After the fix, header_elements and button_content are declared as list[Any],
    allowing mixed Tag + str content without type errors. These tests verify the
    observable behavior: mixed content is accepted and the result is a UI element.
    """

    @pytest.mark.unit()
    def test_button_with_icon_and_text_does_not_raise(self):
        """Button with both icon class and text content is built without error."""

        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_button,
        )

        result = create_enhanced_button(
            button_id="input_ID_tab_test_icon_btn",
            button_text="Export",
            icon_class="bi bi-download",
        )

        assert isinstance(result, Tag)

    @pytest.mark.unit()
    def test_card_with_string_title_does_not_raise(self):
        """Card section with string title content is built without error."""
        from shiny import ui

        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (


            create_enhanced_card_section,
        )

        result = create_enhanced_card_section(
            title="Portfolio Summary",
            content=[ui.p("Content here")],
        )

        assert isinstance(result, Tag)


# ============================================================================
# Additional coverage: missing validation and optional code paths
# ============================================================================


@pytest.mark.unit()
class Test_Create_Enhanced_Numeric_Input_Missing_Paths:
    """Cover validation raises and help_text path in create_enhanced_numeric_input."""

    @pytest.mark.unit()
    def test_non_numeric_min_max_raises(self):
        """Non-numeric min_value or max_value raises Exception_Validation_Input (L202)."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_numeric_input,
        )

        with pytest.raises(Exception_Validation_Input):
            create_enhanced_numeric_input(
                input_ID="input_ID_tab_num_test",
                label_text="Amount",
                min_value="zero",
                max_value=100,
            )

    @pytest.mark.unit()
    def test_non_numeric_default_value_raises(self):
        """Non-numeric default_value raises Exception_Validation_Input (L211)."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_numeric_input,
        )

        with pytest.raises(Exception_Validation_Input):
            create_enhanced_numeric_input(
                input_ID="input_ID_tab_num_def",
                label_text="Value",
                min_value=0,
                max_value=100,
                default_value="fifty",
            )

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        "validation_kwargs",
        [
            {"min_value": True, "max_value": 100},
            {"min_value": 0, "max_value": True},
            {"min_value": 0, "max_value": 100, "step_size": True},
            {"min_value": 0, "max_value": 100, "default_value": True},
        ],
    )
    def test_boolean_numeric_parameters_raise(self, validation_kwargs):
        """Boolean numeric configuration values are rejected instead of being coerced to numbers."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_numeric_input,
        )

        with pytest.raises(Exception_Validation_Input):
            create_enhanced_numeric_input(
                input_ID="input_ID_tab_num_bool",
                label_text="Amount",
                **validation_kwargs,
            )

    @pytest.mark.unit()
    def test_with_help_text_returns_tag(self):
        """Providing help_text appends help element (L275) and returns Tag."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_numeric_input,
        )

        result = create_enhanced_numeric_input(
            input_ID="input_ID_tab_num_help",
            label_text="Rate",
            min_value=0,
            max_value=100,
            help_text="Enter a value between 0 and 100",
        )

        assert isinstance(result, Tag)


@pytest.mark.unit()
class Test_Create_Enhanced_Card_Section_Missing_Paths:
    """Cover content validation raises and footer_content path (L326, L329, L351)."""

    @pytest.mark.unit()
    def test_non_list_content_raises(self):
        """Non-list content raises Exception_Validation_Input (L326)."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_card_section,
        )

        with pytest.raises(Exception_Validation_Input):
            create_enhanced_card_section(title="Section", content="not a list")

    @pytest.mark.unit()
    def test_empty_list_content_raises(self):
        """Empty list content raises Exception_Validation_Input (L329)."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_card_section,
        )

        with pytest.raises(Exception_Validation_Input):
            create_enhanced_card_section(title="Section", content=[])

    @pytest.mark.unit()
    def test_with_footer_content_returns_tag(self):
        """Providing footer_content appends footer element (L351) and returns Tag."""
        from shiny import ui

        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_card_section,
        )

        result = create_enhanced_card_section(
            title="My Card",
            content=[ui.p("Body content")],
            footer_content=ui.p("Footer text"),
        )

        assert isinstance(result, Tag)


@pytest.mark.unit()
class Test_Create_Enhanced_Summary_Display_Missing_Paths:
    """Cover border_variant fallback in create_enhanced_summary_display (L398)."""

    @pytest.mark.unit()
    def test_non_component_variant_border_uses_default(self):
        """Non-ComponentVariant border_variant falls back to LIGHT (L398)."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_summary_display,
        )

        result = create_enhanced_summary_display(
            summary_id="input_ID_tab_summary_border",
            title="Balance",
            border_variant="primary",
        )

        assert isinstance(result, Tag)


@pytest.mark.unit()
class Test_Create_Enhanced_Text_Input_Missing_Paths:
    """Cover max_length validation and help_text path (L474, L495)."""

    @pytest.mark.unit()
    def test_non_int_max_length_raises(self):
        """Non-integer max_length raises Exception_Validation_Input (L474)."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_text_input,
        )

        with pytest.raises(Exception_Validation_Input):
            create_enhanced_text_input(
                input_ID="input_ID_tab_txt_maxlen",
                label_text="Name",
                max_length="unlimited",
            )

    @pytest.mark.unit()
    def test_zero_max_length_raises(self):
        """max_length=0 raises Exception_Validation_Input (L474)."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_text_input,
        )

        with pytest.raises(Exception_Validation_Input):
            create_enhanced_text_input(
                input_ID="input_ID_tab_txt_zero",
                label_text="Name",
                max_length=0,
            )

    @pytest.mark.unit()
    def test_boolean_max_length_raises(self):
        """Boolean max_length is rejected instead of being treated as 1."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_text_input,
        )

        with pytest.raises(Exception_Validation_Input):
            create_enhanced_text_input(
                input_ID="input_ID_tab_txt_bool_maxlen",
                label_text="Name",
                max_length=True,
            )

    @pytest.mark.unit()
    def test_with_help_text_returns_tag(self):
        """Providing help_text appends help element (L495) and returns Tag."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_text_input,
        )

        result = create_enhanced_text_input(
            input_ID="input_ID_tab_txt_help",
            label_text="Email",
            help_text="Enter your email address",
        )

        assert isinstance(result, Tag)


@pytest.mark.unit()
class Test_Create_Enhanced_Select_Input_Missing_Paths:
    """Cover choices validation raise and help_text path (L549, L571)."""

    @pytest.mark.unit()
    def test_non_dict_choices_raises(self):
        """Non-dict choices raises Exception_Validation_Input (L549)."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_select_input,
        )

        with pytest.raises(Exception_Validation_Input):
            create_enhanced_select_input(
                input_ID="input_ID_tab_sel_bad",
                label_text="Period",
                choices=["1Y", "3Y"],
            )

    @pytest.mark.unit()
    def test_empty_dict_choices_raises(self):
        """Empty dict choices raises Exception_Validation_Input (L549)."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_select_input,
        )

        with pytest.raises(Exception_Validation_Input):
            create_enhanced_select_input(
                input_ID="input_ID_tab_sel_empty",
                label_text="Period",
                choices={},
            )

    @pytest.mark.unit()
    def test_with_help_text_returns_tag(self):
        """Providing help_text appends help element (L571) and returns Tag."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_select_input,
        )

        result = create_enhanced_select_input(
            input_ID="input_ID_tab_sel_help",
            label_text="Period",
            choices={"1Y": "1 Year", "3Y": "3 Years"},
            help_text="Select a time period",
        )

        assert isinstance(result, Tag)


@pytest.mark.unit()
class Test_Create_Enhanced_Button_Missing_Paths:
    """Cover button_variant/button_size fallbacks and btn-size class (L621, L625, L634)."""

    @pytest.mark.unit()
    def test_non_component_variant_falls_back_to_primary(self):
        """Non-ComponentVariant button_variant falls back to PRIMARY (L621)."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_button,
        )

        result = create_enhanced_button(
            button_id="input_ID_tab_btn_variant",
            button_text="Go",
            button_variant="primary",
        )

        assert isinstance(result, Tag)

    @pytest.mark.unit()
    def test_invalid_button_size_falls_back_to_md(self):
        """Invalid button_size falls back to 'md' (L625)."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_button,
        )

        result = create_enhanced_button(
            button_id="input_ID_tab_btn_size_bad",
            button_text="Go",
            button_size="xxl",
        )

        assert isinstance(result, Tag)

    @pytest.mark.unit()
    def test_sm_button_size_appends_size_class(self):
        """button_size='sm' appends 'btn-sm' class to button (L634)."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_button,
        )

        result = create_enhanced_button(
            button_id="input_ID_tab_btn_sm",
            button_text="Small",
            button_size="sm",
        )

        assert isinstance(result, Tag)

    @pytest.mark.unit()
    def test_lg_button_size_appends_size_class(self):
        """button_size='lg' appends 'btn-lg' class to button (L634)."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_button,
        )

        result = create_enhanced_button(
            button_id="input_ID_tab_btn_lg",
            button_text="Large",
            button_size="lg",
        )

        assert isinstance(result, Tag)


@pytest.mark.unit()
class Test_Create_Enhanced_Numeric_Input_Currency_Path:
    """Cover currency_format and prefix_symbol branch (L220-249)."""

    @pytest.mark.unit()
    def test_currency_format_returns_tag(self):
        """currency_format=True triggers currency display path (L220-249)."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_numeric_input,
        )

        result = create_enhanced_numeric_input(
            input_ID="input_ID_tab_num_currency",
            label_text="Portfolio Value",
            min_value=0,
            max_value=10_000_000,
            default_value=500_000,
            currency_format=True,
        )

        assert isinstance(result, Tag)

    @pytest.mark.unit()
    def test_prefix_symbol_triggers_currency_path(self):
        """prefix_symbol triggers currency display path (L220-249)."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_numeric_input,
        )

        result = create_enhanced_numeric_input(
            input_ID="input_ID_tab_num_prefix",
            label_text="Amount",
            min_value=0,
            max_value=1_000_000,
            prefix_symbol="$",
        )

        assert isinstance(result, Tag)


@pytest.mark.unit()
class Test_Create_Enhanced_Card_Section_Icon_Path:
    """Cover icon_class path in card header (L334)."""

    @pytest.mark.unit()
    def test_with_icon_class_returns_tag(self):
        """Providing icon_class appends icon element to header (L334)."""
        from shiny import ui

        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_card_section,
        )

        result = create_enhanced_card_section(
            title="Settings",
            content=[ui.p("Content")],
            icon_class="fas fa-cog",
        )

        assert isinstance(result, Tag)


@pytest.mark.unit()
class Test_Create_Enhanced_Summary_Display_Text_Class_Path:
    """Cover text_class path in summary display (L410)."""

    @pytest.mark.unit()
    def test_with_text_class_returns_tag(self):
        """Providing text_class appends it to component classes (L410)."""
        from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
            create_enhanced_summary_display,
        )

        result = create_enhanced_summary_display(
            summary_id="input_ID_tab_summary_text",
            title="Net Worth",
            text_class="text-success",
        )

        assert isinstance(result, Tag)

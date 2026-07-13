"""Unit tests for reactives_access module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest


@pytest.mark.unit()
class Test_Reactives_Access_Module_Imports:
    """Tests that reactives_access exports the expected names."""

    @pytest.mark.unit()
    def test_safe_get_shiny_input_value_importable(self):
        """Test that safe get shiny input value importable."""
        from src.dashboard.shiny_utils.reactives_access import safe_get_shiny_input_value

        assert callable(safe_get_shiny_input_value)

    @pytest.mark.unit()
    def test_safe_get_reactive_value_importable(self):
        """Test that safe get reactive value importable."""
        from src.dashboard.shiny_utils.reactives_access import safe_get_reactive_value

        assert callable(safe_get_reactive_value)

    @pytest.mark.unit()
    def test_safe_get_value_from_shiny_input_text_importable(self):
        """Test that safe get value from shiny input text importable."""
        from src.dashboard.shiny_utils.reactives_access import safe_get_value_from_shiny_input_text

        assert callable(safe_get_value_from_shiny_input_text)

    @pytest.mark.unit()
    def test_safe_get_value_from_shiny_input_numeric_importable(self):
        """Test that safe get value from shiny input numeric importable."""
        from src.dashboard.shiny_utils.reactives_access import (
            safe_get_value_from_shiny_input_numeric,
        )

        assert callable(safe_get_value_from_shiny_input_numeric)

    @pytest.mark.unit()
    def test_get_value_from_shiny_input_text_importable(self):
        """Test that get value from shiny input text importable."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_shiny_input_text

        assert callable(get_value_from_shiny_input_text)

    @pytest.mark.unit()
    def test_get_value_from_shiny_input_numeric_importable(self):
        """Test that get value from shiny input numeric importable."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_shiny_input_numeric

        assert callable(get_value_from_shiny_input_numeric)

    @pytest.mark.unit()
    def test_get_value_from_reactives_shiny_importable(self):
        """Test that get value from reactives shiny importable."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_reactives_shiny

        assert callable(get_value_from_reactives_shiny)

    @pytest.mark.unit()
    def test_set_value_to_reactives_shiny_importable(self):
        """Test that set value to reactives shiny importable."""
        from src.dashboard.shiny_utils.reactives_access import set_value_to_reactives_shiny

        assert callable(set_value_to_reactives_shiny)

    @pytest.mark.unit()
    def test_update_visual_object_in_reactives_importable(self):
        """Test that update visual object in reactives importable."""
        from src.dashboard.shiny_utils.reactives_access import update_visual_object_in_reactives

        assert callable(update_visual_object_in_reactives)


@pytest.mark.unit()
class Test_Safe_Get_Shiny_Input_Value_Direct:
    """Tests for safe_get_shiny_input_value from reactives_access."""

    @pytest.mark.unit()
    def test_none_input_returns_none(self):
        """Test that none input returns none."""
        from src.dashboard.shiny_utils.reactives_access import safe_get_shiny_input_value

        result = safe_get_shiny_input_value(input_events = None, input_identifier = "some_id")
        assert result is None

    @pytest.mark.unit()
    def test_non_string_identifier_returns_none(self):
        """Test that non string identifier returns none."""
        from src.dashboard.shiny_utils.reactives_access import safe_get_shiny_input_value

        result = safe_get_shiny_input_value(input_events = MagicMock(), input_identifier = 123)
        assert result is None

    @pytest.mark.unit()
    def test_valid_input_with_callable_attribute(self):
        """Test that valid input with callable attribute."""
        from src.dashboard.shiny_utils.reactives_access import safe_get_shiny_input_value

        mock_input = MagicMock()
        mock_input.my_input_id = MagicMock(return_value="test_value")
        result = safe_get_shiny_input_value(input_events = mock_input, input_identifier = "my_input_id")
        assert result == "test_value"


@pytest.mark.unit()
class Test_Safe_Get_Reactive_Value_Direct:
    """Tests for safe_get_reactive_value from reactives_access."""

    @pytest.mark.unit()
    def test_none_reactive_input_returns_default(self):
        """Test that none reactive input returns default."""
        from src.dashboard.shiny_utils.reactives_access import safe_get_reactive_value

        result = safe_get_reactive_value(reactive_input = None, default_value="fallback")
        assert result == "fallback"

    @pytest.mark.unit()
    def test_callable_reactive_returns_value(self):
        """Test that callable reactive returns value."""
        from src.dashboard.shiny_utils.reactives_access import safe_get_reactive_value

        mock_reactive = MagicMock(return_value="reactive_result")
        result = safe_get_reactive_value(reactive_input = mock_reactive, default_value="fallback")
        assert result == "reactive_result"

    @pytest.mark.unit()
    def test_exception_in_reactive_returns_default(self):
        """Test that exception in reactive returns default."""
        from src.dashboard.shiny_utils.reactives_access import safe_get_reactive_value

        mock_reactive = MagicMock(side_effect=RuntimeError("reactive error"))
        result = safe_get_reactive_value(reactive_input = mock_reactive, default_value="fallback")
        assert result == "fallback"


@pytest.mark.unit()
class Test_Update_Visual_Object_In_Reactives_Direct:
    """Tests for update_visual_object_in_reactives from reactives_access."""

    @pytest.mark.unit()
    def test_none_reactives_shiny_returns_early(self):
        """Test that none reactives shiny returns early."""
        from src.dashboard.shiny_utils.reactives_access import update_visual_object_in_reactives

        # Should not raise
        update_visual_object_in_reactives(reactives_shiny = None, chart_key = "Chart_Portfolio_Analysis_Returns_Distribution", figure = MagicMock())

    @pytest.mark.unit()
    def test_none_figure_returns_early(self):
        """Test that none figure returns early."""
        from src.dashboard.shiny_utils.reactives_access import update_visual_object_in_reactives

        reactives = {"Visual_Objects_Shiny": {"Chart_Portfolio_Analysis_Returns_Distribution": MagicMock()}}
        # Should not raise
        update_visual_object_in_reactives(reactives_shiny = reactives, chart_key = "Chart_Portfolio_Analysis_Returns_Distribution", figure = None)

    @pytest.mark.unit()
    def test_valid_update_calls_set(self):
        """Test that valid update calls set."""
        from src.dashboard.shiny_utils.reactives_access import update_visual_object_in_reactives

        mock_reactive = MagicMock()
        reactives = {"Visual_Objects_Shiny": {"Chart_Portfolio_Analysis_Returns_Distribution": mock_reactive}}
        figure = MagicMock()
        update_visual_object_in_reactives(reactives_shiny = reactives, chart_key = "Chart_Portfolio_Analysis_Returns_Distribution", figure = figure)
        mock_reactive.set.assert_called_once_with(figure)


def _make_valid_reactives() -> dict:
    """Build a minimal reactives_shiny structure that passes structure validation."""
    return {
        "User_Inputs_Shiny": {},
        "Inner_Variables_Shiny": {},
        "Triggers_Shiny": {},
        "Visual_Objects_Shiny": {},
        "Data_Clients": {},
        "Data_Results": {},
    }


@pytest.mark.unit()
class Test_Safe_Get_Shiny_Input_Value_Extended:
    """Additional branch coverage for safe_get_shiny_input_value."""

    @pytest.mark.unit()
    def test_empty_identifier_returns_none(self):
        """Test that empty identifier returns none."""
        from src.dashboard.shiny_utils.reactives_access import safe_get_shiny_input_value

        result = safe_get_shiny_input_value(input_events = MagicMock(), input_identifier = "   ")
        assert result is None

    @pytest.mark.unit()
    def test_hasattr_false_returns_none(self):
        """Test that hasattr false returns none."""
        from src.dashboard.shiny_utils.reactives_access import safe_get_shiny_input_value

        class _NoAttr:
            pass

        result = safe_get_shiny_input_value(input_events = _NoAttr(), input_identifier = "some_input_id")
        assert result is None

    @pytest.mark.unit()
    def test_non_callable_attribute_returns_value(self):
        """Test that non callable attribute returns value."""
        from src.dashboard.shiny_utils.reactives_access import safe_get_shiny_input_value

        mock_input = MagicMock()
        mock_input.my_id = "direct_value"
        result = safe_get_shiny_input_value(input_events = mock_input, input_identifier = "my_id")
        assert result == "direct_value"

    @pytest.mark.unit()
    def test_callable_raises_type_error_returns_none(self):
        """Test that callable raises type error returns none."""
        from src.dashboard.shiny_utils.reactives_access import safe_get_shiny_input_value

        mock_input = MagicMock()
        mock_input.my_id = MagicMock(side_effect=TypeError("err"))
        result = safe_get_shiny_input_value(input_events = mock_input, input_identifier = "my_id")
        assert result is None

    @pytest.mark.unit()
    def test_callable_raises_runtime_error_returns_none(self):
        """Test that callable raises runtime error returns none."""
        from src.dashboard.shiny_utils.reactives_access import safe_get_shiny_input_value

        mock_input = MagicMock()
        mock_input.my_id = MagicMock(side_effect=RuntimeError("err"))
        result = safe_get_shiny_input_value(input_events = mock_input, input_identifier = "my_id")
        assert result is None


@pytest.mark.unit()
class Test_Safe_Get_Reactive_Value_Extended:
    """Additional branch coverage for safe_get_reactive_value."""

    @pytest.mark.unit()
    def test_callable_returning_none_returns_default(self):
        """Test that callable returning none returns default."""
        from src.dashboard.shiny_utils.reactives_access import safe_get_reactive_value

        mock_reactive = MagicMock(return_value=None)
        result = safe_get_reactive_value(reactive_input = mock_reactive, default_value="fallback")
        assert result == "fallback"


@pytest.mark.unit()
class Test_Safe_Get_Value_From_Shiny_Input_Text:
    """Tests for safe_get_value_from_shiny_input_text."""

    @pytest.mark.unit()
    def test_none_input_returns_default(self):
        """Test that none input returns default."""
        from src.dashboard.shiny_utils.reactives_access import safe_get_value_from_shiny_input_text

        result = safe_get_value_from_shiny_input_text(input_reactive_object = None)
        assert result == ""

    @pytest.mark.unit()
    def test_none_input_with_custom_default(self):
        """Test that none input with custom default returns custom default."""
        from src.dashboard.shiny_utils.reactives_access import safe_get_value_from_shiny_input_text

        result = safe_get_value_from_shiny_input_text(input_reactive_object = None, default_value="N/A")
        assert result == "N/A"

    @pytest.mark.unit()
    def test_callable_returning_none_returns_default(self):
        """Test that callable returning none returns default."""
        from src.dashboard.shiny_utils.reactives_access import safe_get_value_from_shiny_input_text

        result = safe_get_value_from_shiny_input_text(input_reactive_object = MagicMock(return_value=None))
        assert result == ""

    @pytest.mark.unit()
    def test_callable_returning_valid_string(self):
        """Test that callable returning valid string returns it."""
        from src.dashboard.shiny_utils.reactives_access import safe_get_value_from_shiny_input_text

        result = safe_get_value_from_shiny_input_text(input_reactive_object = MagicMock(return_value="hello"))
        assert result == "hello"

    @pytest.mark.unit()
    def test_callable_returning_string_with_whitespace(self):
        """Test that callable returning string with whitespace strips it."""
        from src.dashboard.shiny_utils.reactives_access import safe_get_value_from_shiny_input_text

        result = safe_get_value_from_shiny_input_text(input_reactive_object = MagicMock(return_value="  hello  "))
        assert result == "hello"

    @pytest.mark.unit()
    def test_callable_returning_non_string_converts(self):
        """Test that callable returning non string converts to string."""
        from src.dashboard.shiny_utils.reactives_access import safe_get_value_from_shiny_input_text

        result = safe_get_value_from_shiny_input_text(input_reactive_object = MagicMock(return_value=42))
        assert result == "42"

    @pytest.mark.unit()
    def test_callable_returning_empty_string_returns_default(self):
        """Test that callable returning empty string returns default."""
        from src.dashboard.shiny_utils.reactives_access import safe_get_value_from_shiny_input_text

        result = safe_get_value_from_shiny_input_text(input_reactive_object = MagicMock(return_value="   "))
        assert result == ""

    @pytest.mark.unit()
    def test_callable_raises_exception_returns_default(self):
        """Test that callable raises exception returns default."""
        from src.dashboard.shiny_utils.reactives_access import safe_get_value_from_shiny_input_text

        result = safe_get_value_from_shiny_input_text(input_reactive_object = MagicMock(side_effect=RuntimeError("err")))
        assert result == ""


@pytest.mark.unit()
class Test_Safe_Get_Value_From_Shiny_Input_Numeric:
    """Tests for safe_get_value_from_shiny_input_numeric."""

    @pytest.mark.unit()
    def test_none_input_returns_default(self):
        """Test that none input returns default."""
        from src.dashboard.shiny_utils.reactives_access import safe_get_value_from_shiny_input_numeric

        result = safe_get_value_from_shiny_input_numeric(input_reactive_object = None)
        assert result == 0.0

    @pytest.mark.unit()
    def test_callable_returning_none_returns_default(self):
        """Test that callable returning none returns default."""
        from src.dashboard.shiny_utils.reactives_access import safe_get_value_from_shiny_input_numeric

        result = safe_get_value_from_shiny_input_numeric(input_reactive_object = MagicMock(return_value=None))
        assert result == 0.0

    @pytest.mark.unit()
    def test_callable_returning_positive_float(self):
        """Test that callable returning positive float returns it."""
        from src.dashboard.shiny_utils.reactives_access import safe_get_value_from_shiny_input_numeric

        result = safe_get_value_from_shiny_input_numeric(input_reactive_object = MagicMock(return_value=3.5))
        assert result == 3.5

    @pytest.mark.unit()
    def test_callable_returning_negative_float_returns_zero(self):
        """Test that callable returning negative float returns zero."""
        from src.dashboard.shiny_utils.reactives_access import safe_get_value_from_shiny_input_numeric

        result = safe_get_value_from_shiny_input_numeric(input_reactive_object = MagicMock(return_value=-2.0))
        assert result == 0.0

    @pytest.mark.unit()
    def test_callable_returning_int(self):
        """Test that callable returning int converts to float."""
        from src.dashboard.shiny_utils.reactives_access import safe_get_value_from_shiny_input_numeric

        result = safe_get_value_from_shiny_input_numeric(input_reactive_object = MagicMock(return_value=10))
        assert result == 10.0

    @pytest.mark.unit()
    def test_callable_returning_bool_returns_default(self):
        """Boolean numeric inputs fall back to the safe default instead of being coerced to 1.0."""
        from src.dashboard.shiny_utils.reactives_access import safe_get_value_from_shiny_input_numeric

        result = safe_get_value_from_shiny_input_numeric(input_reactive_object = MagicMock(return_value=True))
        assert result == 0.0

    @pytest.mark.unit()
    def test_callable_returning_numeric_string(self):
        """Test that callable returning numeric string parses to float."""
        from src.dashboard.shiny_utils.reactives_access import safe_get_value_from_shiny_input_numeric

        result = safe_get_value_from_shiny_input_numeric(input_reactive_object = MagicMock(return_value="42.5"))
        assert result == 42.5

    @pytest.mark.unit()
    def test_callable_returning_currency_string(self):
        """Test that callable returning currency string parses correctly."""
        from src.dashboard.shiny_utils.reactives_access import safe_get_value_from_shiny_input_numeric

        result = safe_get_value_from_shiny_input_numeric(input_reactive_object = MagicMock(return_value="$1,234.56"))
        assert result == 1234.56

    @pytest.mark.unit()
    def test_callable_returning_empty_string_returns_default(self):
        """Test that callable returning empty string returns default."""
        from src.dashboard.shiny_utils.reactives_access import safe_get_value_from_shiny_input_numeric

        result = safe_get_value_from_shiny_input_numeric(input_reactive_object = MagicMock(return_value="  "))
        assert result == 0.0

    @pytest.mark.unit()
    def test_callable_returning_invalid_string_returns_default(self):
        """Test that callable returning invalid string returns default."""
        from src.dashboard.shiny_utils.reactives_access import safe_get_value_from_shiny_input_numeric

        result = safe_get_value_from_shiny_input_numeric(input_reactive_object = MagicMock(return_value="abc"))
        assert result == 0.0

    @pytest.mark.unit()
    def test_callable_returning_other_type_returns_default(self):
        """Test that callable returning other type returns default."""
        from src.dashboard.shiny_utils.reactives_access import safe_get_value_from_shiny_input_numeric

        result = safe_get_value_from_shiny_input_numeric(input_reactive_object = MagicMock(return_value=[1, 2, 3]))
        assert result == 0.0

    @pytest.mark.unit()
    def test_callable_raises_exception_returns_default(self):
        """Test that callable raises exception returns default."""
        from src.dashboard.shiny_utils.reactives_access import safe_get_value_from_shiny_input_numeric

        result = safe_get_value_from_shiny_input_numeric(input_reactive_object = MagicMock(side_effect=RuntimeError("err")))
        assert result == 0.0

    @pytest.mark.unit()
    def test_custom_default_value(self):
        """Test that custom default value is returned on failure."""
        from src.dashboard.shiny_utils.reactives_access import safe_get_value_from_shiny_input_numeric

        result = safe_get_value_from_shiny_input_numeric(input_reactive_object = None, default_value=99.0)
        assert result == 99.0


@pytest.mark.unit()
class Test_Get_Value_From_Shiny_Input_Text:
    """Tests for get_value_from_shiny_input_text."""

    @pytest.mark.unit()
    def test_none_raises(self):
        """Test that none raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_shiny_input_text
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Validation_Input

        with pytest.raises(Exception_Validation_Input):
            get_value_from_shiny_input_text(input_reactive_object = None)

    @pytest.mark.unit()
    def test_non_callable_raises(self):
        """Test that non callable raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_shiny_input_text
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Validation_Input

        with pytest.raises(Exception_Validation_Input):
            get_value_from_shiny_input_text(input_reactive_object = "not_callable")

    @pytest.mark.unit()
    def test_callable_returning_none_raises(self):
        """Test that callable returning none raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_shiny_input_text
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Validation_Input

        with pytest.raises(Exception_Validation_Input):
            get_value_from_shiny_input_text(input_reactive_object = MagicMock(return_value=None))

    @pytest.mark.unit()
    def test_callable_returning_empty_string_raises(self):
        """Test that callable returning empty string raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_shiny_input_text
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Validation_Input

        with pytest.raises(Exception_Validation_Input):
            get_value_from_shiny_input_text(input_reactive_object = MagicMock(return_value="   "))

    @pytest.mark.unit()
    def test_callable_returning_valid_string(self):
        """Test that callable returning valid string returns stripped value."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_shiny_input_text

        result = get_value_from_shiny_input_text(input_reactive_object = MagicMock(return_value="  hello  "))
        assert result == "hello"

    @pytest.mark.unit()
    def test_callable_raises_attribute_error(self):
        """Test that callable raises attribute error propagates as Exception_Configuration."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_shiny_input_text
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Configuration

        with pytest.raises(Exception_Configuration):
            get_value_from_shiny_input_text(input_reactive_object = MagicMock(side_effect=AttributeError("err")))

    @pytest.mark.unit()
    def test_callable_raises_runtime_error(self):
        """Test that callable raises runtime error propagates as Exception_Configuration."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_shiny_input_text
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Configuration

        with pytest.raises(Exception_Configuration):
            get_value_from_shiny_input_text(input_reactive_object = MagicMock(side_effect=RuntimeError("err")))

    @pytest.mark.unit()
    def test_callable_raises_unexpected_exception(self):
        """Test that callable raises unexpected exception propagates as Exception_Configuration."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_shiny_input_text
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Configuration

        with pytest.raises(Exception_Configuration):
            get_value_from_shiny_input_text(input_reactive_object = MagicMock(side_effect=OSError("err")))


@pytest.mark.unit()
class Test_Get_Value_From_Shiny_Input_Numeric:
    """Tests for get_value_from_shiny_input_numeric."""

    @pytest.mark.unit()
    def test_none_raises(self):
        """Test that none raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_shiny_input_numeric
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Validation_Input

        with pytest.raises(Exception_Validation_Input):
            get_value_from_shiny_input_numeric(input_reactive_object = None)

    @pytest.mark.unit()
    def test_non_callable_raises(self):
        """Test that non callable raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_shiny_input_numeric
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Validation_Input

        with pytest.raises(Exception_Validation_Input):
            get_value_from_shiny_input_numeric(input_reactive_object = "not_callable")

    @pytest.mark.unit()
    def test_callable_returning_none_raises(self):
        """Test that callable returning none raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_shiny_input_numeric
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Validation_Input

        with pytest.raises(Exception_Validation_Input):
            get_value_from_shiny_input_numeric(input_reactive_object = MagicMock(return_value=None))

    @pytest.mark.unit()
    def test_callable_returning_positive_float(self):
        """Test that callable returning positive float returns it."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_shiny_input_numeric

        result = get_value_from_shiny_input_numeric(input_reactive_object = MagicMock(return_value=5.0))
        assert result == 5.0

    @pytest.mark.unit()
    def test_callable_returning_negative_float_raises(self):
        """Test that callable returning negative float raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_shiny_input_numeric
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Validation_Input

        with pytest.raises(Exception_Validation_Input):
            get_value_from_shiny_input_numeric(input_reactive_object = MagicMock(return_value=-3.0))

    @pytest.mark.unit()
    def test_callable_returning_int(self):
        """Test that callable returning int returns float."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_shiny_input_numeric

        result = get_value_from_shiny_input_numeric(input_reactive_object = MagicMock(return_value=7))
        assert result == 7.0

    @pytest.mark.unit()
    def test_callable_returning_bool_raises(self):
        """Boolean numeric inputs are rejected instead of being coerced to 1.0."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_shiny_input_numeric

        with pytest.raises(TypeError):
            get_value_from_shiny_input_numeric(input_reactive_object = MagicMock(return_value=True))

    @pytest.mark.unit()
    def test_callable_returning_numeric_string(self):
        """Test that callable returning numeric string returns float."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_shiny_input_numeric

        result = get_value_from_shiny_input_numeric(input_reactive_object = MagicMock(return_value="42.5"))
        assert result == 42.5

    @pytest.mark.unit()
    def test_callable_returning_currency_string(self):
        """Test that callable returning currency string parses correctly."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_shiny_input_numeric

        result = get_value_from_shiny_input_numeric(input_reactive_object = MagicMock(return_value="$1,000.00"))
        assert result == 1000.0

    @pytest.mark.unit()
    def test_callable_returning_empty_string_raises(self):
        """Test that callable returning empty string raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_shiny_input_numeric
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Validation_Input

        with pytest.raises(Exception_Validation_Input):
            get_value_from_shiny_input_numeric(input_reactive_object = MagicMock(return_value="$,"))

    @pytest.mark.unit()
    def test_callable_returning_invalid_string_raises(self):
        """Test that callable returning invalid string raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_shiny_input_numeric
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Validation_Input

        with pytest.raises(Exception_Validation_Input):
            get_value_from_shiny_input_numeric(input_reactive_object = MagicMock(return_value="not_a_number"))

    @pytest.mark.unit()
    def test_callable_returning_negative_string_raises(self):
        """Test that callable returning negative string raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_shiny_input_numeric
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Validation_Input

        with pytest.raises(Exception_Validation_Input):
            get_value_from_shiny_input_numeric(input_reactive_object = MagicMock(return_value="-5.0"))

    @pytest.mark.unit()
    def test_callable_returning_unexpected_type_raises(self):
        """Test that callable returning unexpected type raises TypeError."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_shiny_input_numeric

        with pytest.raises(TypeError):
            get_value_from_shiny_input_numeric(input_reactive_object = MagicMock(return_value=[1, 2, 3]))

    @pytest.mark.unit()
    def test_callable_raises_attribute_error(self):
        """Test that callable raises attribute error propagates as Exception_Configuration."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_shiny_input_numeric
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Configuration

        with pytest.raises(Exception_Configuration):
            get_value_from_shiny_input_numeric(input_reactive_object = MagicMock(side_effect=AttributeError("err")))

    @pytest.mark.unit()
    def test_callable_raises_runtime_error(self):
        """Test that callable raises runtime error propagates as Exception_Configuration."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_shiny_input_numeric
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Configuration

        with pytest.raises(Exception_Configuration):
            get_value_from_shiny_input_numeric(input_reactive_object = MagicMock(side_effect=RuntimeError("err")))

    @pytest.mark.unit()
    def test_callable_raises_unexpected_exception(self):
        """Test that callable raises unexpected exception propagates as Exception_Configuration."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_shiny_input_numeric
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Configuration

        with pytest.raises(Exception_Configuration):
            get_value_from_shiny_input_numeric(input_reactive_object = MagicMock(side_effect=OSError("err")))


@pytest.mark.unit()
class Test_Get_Value_From_Reactives_Shiny:
    """Tests for get_value_from_reactives_shiny."""

    @pytest.mark.unit()
    def test_none_key_name_raises(self):
        """Test that none key_name raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_reactives_shiny
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Validation_Input

        with pytest.raises(Exception_Validation_Input):
            get_value_from_reactives_shiny(reactives_shiny = {}, key_name = None, key_category = "User_Inputs_Shiny")

    @pytest.mark.unit()
    def test_non_string_key_name_raises(self):
        """Test that non string key_name raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_reactives_shiny
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Validation_Input

        with pytest.raises(Exception_Validation_Input):
            get_value_from_reactives_shiny(reactives_shiny = {}, key_name = 123, key_category = "User_Inputs_Shiny")

    @pytest.mark.unit()
    def test_empty_key_name_raises(self):
        """Test that empty key_name raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_reactives_shiny
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Validation_Input

        with pytest.raises(Exception_Validation_Input):
            get_value_from_reactives_shiny(reactives_shiny = {}, key_name = "  ", key_category = "User_Inputs_Shiny")

    @pytest.mark.unit()
    def test_none_key_category_raises(self):
        """Test that none key_category raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_reactives_shiny
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Validation_Input

        with pytest.raises(Exception_Validation_Input):
            get_value_from_reactives_shiny(reactives_shiny = {}, key_name = "my_key", key_category = None)

    @pytest.mark.unit()
    def test_non_string_key_category_raises(self):
        """Test that non string key_category raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_reactives_shiny
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Validation_Input

        with pytest.raises(Exception_Validation_Input):
            get_value_from_reactives_shiny(reactives_shiny = {}, key_name = "my_key", key_category = 42)

    @pytest.mark.unit()
    def test_empty_key_category_raises(self):
        """Test that empty key_category raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_reactives_shiny
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Validation_Input

        with pytest.raises(Exception_Validation_Input):
            get_value_from_reactives_shiny(reactives_shiny = {}, key_name = "my_key", key_category = "  ")

    @pytest.mark.unit()
    def test_none_reactives_raises(self):
        """Test that none reactives raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_reactives_shiny
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Validation_Input

        with pytest.raises(Exception_Validation_Input):
            get_value_from_reactives_shiny(reactives_shiny = None, key_name = "my_key", key_category = "User_Inputs_Shiny")

    @pytest.mark.unit()
    def test_non_dict_reactives_raises(self):
        """Test that non dict reactives raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_reactives_shiny
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Validation_Input

        with pytest.raises(Exception_Validation_Input):
            get_value_from_reactives_shiny(reactives_shiny = "not_a_dict", key_name = "my_key", key_category = "User_Inputs_Shiny")

    @pytest.mark.unit()
    def test_invalid_key_category_raises(self):
        """Test that invalid key_category raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_reactives_shiny
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Validation_Input

        with pytest.raises(Exception_Validation_Input):
            get_value_from_reactives_shiny(reactives_shiny = _make_valid_reactives(), key_name = "my_key", key_category = "Invalid_Category")

    @pytest.mark.unit()
    def test_missing_required_category_raises(self):
        """Test that missing required category raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_reactives_shiny
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Validation_Input

        incomplete = {"User_Inputs_Shiny": {}}
        with pytest.raises(Exception_Validation_Input):
            get_value_from_reactives_shiny(reactives_shiny = incomplete, key_name = "my_key", key_category = "User_Inputs_Shiny")

    @pytest.mark.unit()
    def test_category_not_dict_raises(self):
        """Test that category not dict raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_reactives_shiny
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Validation_Input

        reactives = _make_valid_reactives()
        reactives["User_Inputs_Shiny"] = "not_a_dict"
        with pytest.raises(Exception_Validation_Input):
            get_value_from_reactives_shiny(reactives_shiny = reactives, key_name = "my_key", key_category = "User_Inputs_Shiny")

    @pytest.mark.unit()
    def test_key_not_in_empty_category_raises_key_error(self):
        """Test that key not in empty category raises KeyError."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_reactives_shiny

        reactives = _make_valid_reactives()
        with pytest.raises(KeyError):
            get_value_from_reactives_shiny(reactives_shiny = reactives, key_name = "missing_key", key_category = "User_Inputs_Shiny")

    @pytest.mark.unit()
    def test_key_not_found_with_similar_keys_raises_key_error(self):
        """Test that key not found with similar keys raises KeyError."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_reactives_shiny

        reactives = _make_valid_reactives()
        reactives["User_Inputs_Shiny"] = {"User_Age_Extended": MagicMock()}
        with pytest.raises(KeyError):
            get_value_from_reactives_shiny(reactives_shiny = reactives, key_name = "User_Age", key_category = "User_Inputs_Shiny")

    @pytest.mark.unit()
    def test_key_not_found_no_similar_raises_key_error(self):
        """Test that key not found no similar raises KeyError."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_reactives_shiny

        reactives = _make_valid_reactives()
        reactives["User_Inputs_Shiny"] = {"Completely_Different": MagicMock()}
        with pytest.raises(KeyError):
            get_value_from_reactives_shiny(reactives_shiny = reactives, key_name = "xyz_abc_def", key_category = "User_Inputs_Shiny")

    @pytest.mark.unit()
    def test_reactive_variable_none_raises(self):
        """Test that reactive variable none raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_reactives_shiny
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Validation_Input

        reactives = _make_valid_reactives()
        reactives["User_Inputs_Shiny"] = {"my_key": None}
        with pytest.raises(Exception_Validation_Input):
            get_value_from_reactives_shiny(reactives_shiny = reactives, key_name = "my_key", key_category = "User_Inputs_Shiny")

    @pytest.mark.unit()
    def test_reactive_no_get_method_raises_type_error(self):
        """Test that reactive no get method raises TypeError."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_reactives_shiny

        reactives = _make_valid_reactives()
        reactives["User_Inputs_Shiny"] = {"my_key": "no_get_attr"}
        with pytest.raises(TypeError):
            get_value_from_reactives_shiny(reactives_shiny = reactives, key_name = "my_key", key_category = "User_Inputs_Shiny")

    @pytest.mark.unit()
    def test_reactive_get_not_callable_raises_type_error(self):
        """Test that reactive get not callable raises TypeError."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_reactives_shiny

        class _BadReactive:
            get = "not_callable"

        reactives = _make_valid_reactives()
        reactives["User_Inputs_Shiny"] = {"my_key": _BadReactive()}
        with pytest.raises(TypeError):
            get_value_from_reactives_shiny(reactives_shiny = reactives, key_name = "my_key", key_category = "User_Inputs_Shiny")

    @pytest.mark.unit()
    def test_valid_get_returns_value(self):
        """Test that valid get returns value."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_reactives_shiny

        mock_rv = MagicMock()
        mock_rv.get.return_value = "the_value"
        reactives = _make_valid_reactives()
        reactives["User_Inputs_Shiny"] = {"my_key": mock_rv}
        result = get_value_from_reactives_shiny(reactives_shiny = reactives, key_name = "my_key", key_category = "User_Inputs_Shiny")
        assert result == "the_value"

    @pytest.mark.unit()
    def test_get_raises_attribute_error(self):
        """Test that get raises attribute error propagates as Exception_Configuration."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_reactives_shiny
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Configuration

        mock_rv = MagicMock()
        mock_rv.get.side_effect = AttributeError("err")
        reactives = _make_valid_reactives()
        reactives["User_Inputs_Shiny"] = {"my_key": mock_rv}
        with pytest.raises(Exception_Configuration):
            get_value_from_reactives_shiny(reactives_shiny = reactives, key_name = "my_key", key_category = "User_Inputs_Shiny")

    @pytest.mark.unit()
    def test_get_raises_runtime_error(self):
        """Test that get raises runtime error propagates as Exception_Configuration."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_reactives_shiny
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Configuration

        mock_rv = MagicMock()
        mock_rv.get.side_effect = RuntimeError("err")
        reactives = _make_valid_reactives()
        reactives["User_Inputs_Shiny"] = {"my_key": mock_rv}
        with pytest.raises(Exception_Configuration):
            get_value_from_reactives_shiny(reactives_shiny = reactives, key_name = "my_key", key_category = "User_Inputs_Shiny")

    @pytest.mark.unit()
    def test_get_raises_value_error(self):
        """Test that get raises value error propagates as Exception_Configuration."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_reactives_shiny
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Configuration

        mock_rv = MagicMock()
        mock_rv.get.side_effect = ValueError("err")
        reactives = _make_valid_reactives()
        reactives["User_Inputs_Shiny"] = {"my_key": mock_rv}
        with pytest.raises(Exception_Configuration):
            get_value_from_reactives_shiny(reactives_shiny = reactives, key_name = "my_key", key_category = "User_Inputs_Shiny")

    @pytest.mark.unit()
    def test_get_raises_type_error(self):
        """Test that get raises type error propagates as Exception_Configuration."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_reactives_shiny
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Configuration

        mock_rv = MagicMock()
        mock_rv.get.side_effect = TypeError("err")
        reactives = _make_valid_reactives()
        reactives["User_Inputs_Shiny"] = {"my_key": mock_rv}
        with pytest.raises(Exception_Configuration):
            get_value_from_reactives_shiny(reactives_shiny = reactives, key_name = "my_key", key_category = "User_Inputs_Shiny")

    @pytest.mark.unit()
    def test_get_raises_key_error(self):
        """Test that get raises key error propagates as Exception_Configuration."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_reactives_shiny
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Configuration

        mock_rv = MagicMock()
        mock_rv.get.side_effect = KeyError("err")
        reactives = _make_valid_reactives()
        reactives["User_Inputs_Shiny"] = {"my_key": mock_rv}
        with pytest.raises(Exception_Configuration):
            get_value_from_reactives_shiny(reactives_shiny = reactives, key_name = "my_key", key_category = "User_Inputs_Shiny")

    @pytest.mark.unit()
    def test_get_raises_unexpected_exception(self):
        """Test that get raises unexpected exception propagates as Exception_Configuration."""
        from src.dashboard.shiny_utils.reactives_access import get_value_from_reactives_shiny
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Configuration

        mock_rv = MagicMock()
        mock_rv.get.side_effect = OSError("err")
        reactives = _make_valid_reactives()
        reactives["User_Inputs_Shiny"] = {"my_key": mock_rv}
        with pytest.raises(Exception_Configuration):
            get_value_from_reactives_shiny(reactives_shiny = reactives, key_name = "my_key", key_category = "User_Inputs_Shiny")


@pytest.mark.unit()
class Test_Set_Value_To_Reactives_Shiny:
    """Tests for set_value_to_reactives_shiny."""

    @pytest.mark.unit()
    def test_none_reactives_raises(self):
        """Test that none reactives raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.reactives_access import set_value_to_reactives_shiny
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Validation_Input

        with pytest.raises(Exception_Validation_Input):
            set_value_to_reactives_shiny(reactives_shiny = None, key_name = "my_key", key_category = "User_Inputs_Shiny", input_value = "value")

    @pytest.mark.unit()
    def test_invalid_category_raises(self):
        """Test that invalid category raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.reactives_access import set_value_to_reactives_shiny
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Validation_Input

        with pytest.raises(Exception_Validation_Input):
            set_value_to_reactives_shiny(reactives_shiny = _make_valid_reactives(), key_name = "my_key", key_category = "Bad_Category", input_value = "value")

    @pytest.mark.unit()
    def test_category_missing_from_reactives_raises(self):
        """Test that category missing from reactives raises KeyError."""
        from src.dashboard.shiny_utils.reactives_access import set_value_to_reactives_shiny

        reactives = _make_valid_reactives()
        with pytest.raises(KeyError):
            set_value_to_reactives_shiny(reactives_shiny = reactives, key_name = "my_key", key_category = "Advisor_Info", input_value = "value")

    @pytest.mark.unit()
    def test_key_missing_from_category_raises(self):
        """Test that key missing from category raises KeyError."""
        from src.dashboard.shiny_utils.reactives_access import set_value_to_reactives_shiny

        with pytest.raises(KeyError):
            set_value_to_reactives_shiny(reactives_shiny = _make_valid_reactives(), key_name = "missing_key", key_category = "User_Inputs_Shiny", input_value = "value")

    @pytest.mark.unit()
    def test_reactive_variable_none_raises(self):
        """Test that reactive variable none raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.reactives_access import set_value_to_reactives_shiny
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Validation_Input

        reactives = _make_valid_reactives()
        reactives["User_Inputs_Shiny"] = {"my_key": None}
        with pytest.raises(Exception_Validation_Input):
            set_value_to_reactives_shiny(reactives_shiny = reactives, key_name = "my_key", key_category = "User_Inputs_Shiny", input_value = "value")

    @pytest.mark.unit()
    def test_no_set_method_raises(self):
        """Test that no set method raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.reactives_access import set_value_to_reactives_shiny
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Validation_Input

        reactives = _make_valid_reactives()
        reactives["User_Inputs_Shiny"] = {"my_key": "no_set_method"}
        with pytest.raises(Exception_Validation_Input):
            set_value_to_reactives_shiny(reactives_shiny = reactives, key_name = "my_key", key_category = "User_Inputs_Shiny", input_value = "value")

    @pytest.mark.unit()
    def test_valid_set_returns_reactives(self):
        """Test that valid set returns the reactives dictionary."""
        from src.dashboard.shiny_utils.reactives_access import set_value_to_reactives_shiny

        mock_rv = MagicMock()
        reactives = _make_valid_reactives()
        reactives["User_Inputs_Shiny"] = {"my_key": mock_rv}
        result = set_value_to_reactives_shiny(reactives_shiny = reactives, key_name = "my_key", key_category = "User_Inputs_Shiny", input_value = "new_value")
        mock_rv.set.assert_called_once_with("new_value")
        assert result is reactives

    @pytest.mark.unit()
    def test_set_raises_exception_propagates(self):
        """Test that set raises exception propagates as Exception_Configuration."""
        from src.dashboard.shiny_utils.reactives_access import set_value_to_reactives_shiny
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Configuration

        mock_rv = MagicMock()
        mock_rv.set.side_effect = RuntimeError("err")
        reactives = _make_valid_reactives()
        reactives["User_Inputs_Shiny"] = {"my_key": mock_rv}
        with pytest.raises(Exception_Configuration):
            set_value_to_reactives_shiny(reactives_shiny = reactives, key_name = "my_key", key_category = "User_Inputs_Shiny", input_value = "value")


@pytest.mark.unit()
class Test_Update_Visual_Object_In_Reactives_Extended:
    """Additional branch coverage for update_visual_object_in_reactives."""

    @pytest.mark.unit()
    def test_non_dict_reactives_returns_early(self):
        """Test that non dict reactives returns early."""
        from src.dashboard.shiny_utils.reactives_access import update_visual_object_in_reactives

        update_visual_object_in_reactives(reactives_shiny = "not_a_dict", chart_key = "my_chart", figure = MagicMock())

    @pytest.mark.unit()
    def test_empty_chart_key_returns_early(self):
        """Test that empty chart key returns early."""
        from src.dashboard.shiny_utils.reactives_access import update_visual_object_in_reactives

        update_visual_object_in_reactives(reactives_shiny = {"Visual_Objects_Shiny": {}}, chart_key = "", figure = MagicMock())

    @pytest.mark.unit()
    def test_non_string_chart_key_returns_early(self):
        """Test that non string chart key returns early."""
        from src.dashboard.shiny_utils.reactives_access import update_visual_object_in_reactives

        update_visual_object_in_reactives(reactives_shiny = {"Visual_Objects_Shiny": {}}, chart_key = 123, figure = MagicMock())

    @pytest.mark.unit()
    def test_visual_objects_not_dict_returns_early(self):
        """Test that visual objects not dict returns early."""
        from src.dashboard.shiny_utils.reactives_access import update_visual_object_in_reactives

        update_visual_object_in_reactives(reactives_shiny = {"Visual_Objects_Shiny": "not_dict"}, chart_key = "my_chart", figure = MagicMock())

    @pytest.mark.unit()
    def test_key_not_in_visual_objects_returns_early(self):
        """Test that key not in visual objects returns early."""
        from src.dashboard.shiny_utils.reactives_access import update_visual_object_in_reactives

        update_visual_object_in_reactives(reactives_shiny = {"Visual_Objects_Shiny": {}}, chart_key = "missing_key", figure = MagicMock())

    @pytest.mark.unit()
    def test_reactive_no_set_method_returns_early(self):
        """Test that reactive no set method returns early."""
        from src.dashboard.shiny_utils.reactives_access import update_visual_object_in_reactives

        update_visual_object_in_reactives(
            reactives_shiny = {"Visual_Objects_Shiny": {"my_chart": "no_set_attr"}},
            chart_key = "my_chart",
            figure = MagicMock(),
        )

    @pytest.mark.unit()
    def test_set_raises_exception_logs_warning(self):
        """Test that set raises exception logs warning but does not propagate."""
        from src.dashboard.shiny_utils.reactives_access import update_visual_object_in_reactives

        mock_rv = MagicMock()
        mock_rv.set.side_effect = RuntimeError("err")
        reactives = {"Visual_Objects_Shiny": {"my_chart": mock_rv}}
        update_visual_object_in_reactives(reactives_shiny = reactives, chart_key = "my_chart", figure = MagicMock())

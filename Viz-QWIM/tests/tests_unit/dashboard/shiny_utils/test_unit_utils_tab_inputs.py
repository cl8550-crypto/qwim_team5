from datetime import datetime, timedelta


def validate_module_inputs(data_utils=None, data_inputs=None, reactives_shiny=None):
    """Validate module server input parameters using defensive programming."""

    # Input validation with early returns
    if data_utils is None:
        return False, "data_utils parameter is required"

    if data_inputs is None:
        return False, "data_inputs parameter is required"

    if reactives_shiny is None:
        return False, "reactives_shiny parameter is required"

    # Configuration validation
    if not isinstance(data_utils, dict):
        return False, f"data_utils must be dict, got {type(data_utils).__name__}"

    if not isinstance(data_inputs, dict):
        return False, f"data_inputs must be dict, got {type(data_inputs).__name__}"

    if not isinstance(reactives_shiny, dict):
        return False, f"reactives_shiny must be dict, got {type(reactives_shiny).__name__}"

    # Business logic validation
    if "Time_Series_Sample" not in data_inputs:
        return False, "data_inputs missing required 'Time_Series_Sample' key"

    return True, ""


def validate_time_period_selection(time_period_value):
    """Validate time period selection using defensive programming."""

    # Input validation
    if time_period_value is None:
        return False, "Time period selection is None"

    if not isinstance(time_period_value, str):
        return False, f"Time period must be string, got {type(time_period_value).__name__}"

    # Configuration validation
    valid_time_periods = {
        "custom",
        "last_1_year",
        "last_3_years",
        "last_5_years",
        "last_10_years",
        "ytd",
    }

    if time_period_value not in valid_time_periods:
        return (
            False,
            f"Invalid time period: {time_period_value}. Must be one of {valid_time_periods}",
        )

    return True, ""


def validate_date_range_input(date_range_input, time_period_mode="preset"):
    """Validate date range input using defensive programming."""

    # Input validation with early returns
    if date_range_input is None:
        if time_period_mode == "custom":
            return False, "Custom mode requires date range input"
        return True, ""  # Preset modes can have None date range

    # Configuration validation
    if not isinstance(date_range_input, (list, tuple)):
        return False, f"Date range must be list or tuple, got {type(date_range_input).__name__}"

    if len(date_range_input) != 2:
        return False, f"Date range must have exactly 2 elements, got {len(date_range_input)}"

    # Business logic validation
    start_date = date_range_input[0]
    end_date = date_range_input[1]

    if start_date is None or end_date is None:
        return False, "Date range contains None values"

    # Defensive programming - safe date comparison
    if hasattr(start_date, "date") and hasattr(end_date, "date"):
        start_date_obj = start_date.date() if hasattr(start_date, "date") else start_date
        end_date_obj = end_date.date() if hasattr(end_date, "date") else end_date

        if start_date_obj > end_date_obj:
            return False, f"Start date {start_date_obj} cannot be after end date {end_date_obj}"

    return True, ""


def safe_get_input_value(input_object, input_identifier: str, default_value=None):
    """Safely get input value using defensive programming and project Shiny standards."""

    # Input validation
    if input_object is None:
        return default_value

    if not isinstance(input_identifier, str):
        return default_value

    if len(input_identifier.strip()) == 0:
        return default_value

    # Only use try-except for Shiny input access that might fail unpredictably
    try:
        # Use project standard: input[["identifier"]].get()
        result_value = input_object[[input_identifier]].get()
        return result_value if result_value is not None else default_value
    except Exception:
        return default_value


def find_date_column_name(data_frame):
    """Find the date column name using defensive programming."""

    # Input validation
    if data_frame is None:
        return None

    if not hasattr(data_frame, "columns"):
        return None

    # Configuration validation
    possible_date_columns = ["date", "Date", "DATE"]

    # Defensive programming - safe column checking
    for date_column_candidate in possible_date_columns:
        if date_column_candidate in data_frame.columns:
            return date_column_candidate

    return None


def calculate_preset_date_range(time_period_selection, max_date_available, min_date_available):
    """Calculate date range for preset time periods using defensive programming."""

    # Input validation
    if not isinstance(time_period_selection, str):
        return None, None

    if max_date_available is None or min_date_available is None:
        return None, None

    # Configuration validation
    preset_calculations = {
        "last_1_year": 365,
        "last_3_years": 365 * 3,
        "last_5_years": 365 * 5,
        "last_10_years": 365 * 10,
    }

    # Business logic validation
    if time_period_selection == "ytd":
        start_date = datetime(max_date_available.year, 1, 1).date()
        end_date = max_date_available
    elif time_period_selection in preset_calculations:
        days_back = preset_calculations[time_period_selection]
        start_date = max_date_available - timedelta(days=days_back)
        end_date = max_date_available
    else:
        # Fallback to full range
        start_date = min_date_available
        end_date = max_date_available

    # Defensive programming - ensure dates are within available range
    start_date = max(start_date, min_date_available)
    end_date = min(end_date, max_date_available)

    return start_date, end_date


# ============================================================================
# pytest imports (must follow all helper code above)
# ============================================================================
import pytest
from datetime import datetime, date


class Test_Validate_Module_Inputs:
    """Tests for validate_module_inputs in utils_tab_inputs."""

    @pytest.mark.unit()
    def test_none_data_utils_returns_false(self):
        """Test that none data utils returns false."""
        from src.dashboard.shiny_utils.utils_tab_inputs import validate_module_inputs

        result, msg = validate_module_inputs(data_utils = None, data_inputs = {}, reactives_shiny = {})
        assert result is False
        assert "data_utils" in msg

    @pytest.mark.unit()
    def test_none_data_inputs_returns_false(self):
        """Test that none data inputs returns false."""
        from src.dashboard.shiny_utils.utils_tab_inputs import validate_module_inputs

        result, msg = validate_module_inputs(data_utils = {}, data_inputs = None, reactives_shiny = {})
        assert result is False

    @pytest.mark.unit()
    def test_none_reactives_returns_false(self):
        """Test that none reactives returns false."""
        from src.dashboard.shiny_utils.utils_tab_inputs import validate_module_inputs

        result, msg = validate_module_inputs(data_utils = {}, data_inputs = {}, reactives_shiny = None)
        assert result is False

    @pytest.mark.unit()
    def test_non_dict_data_utils_returns_false(self):
        """Test that non dict data utils returns false."""
        from src.dashboard.shiny_utils.utils_tab_inputs import validate_module_inputs

        result, msg = validate_module_inputs(data_utils = "bad", data_inputs = {}, reactives_shiny = {})
        assert result is False

    @pytest.mark.unit()
    def test_non_dict_data_inputs_returns_false(self):
        """Test that non dict data inputs returns false."""
        from src.dashboard.shiny_utils.utils_tab_inputs import validate_module_inputs

        result, msg = validate_module_inputs(data_utils = {}, data_inputs = "bad", reactives_shiny = {})
        assert result is False
        assert "data_inputs" in msg

    @pytest.mark.unit()
    def test_non_dict_reactives_returns_false(self):
        """Test that non dict reactives returns false."""
        from src.dashboard.shiny_utils.utils_tab_inputs import validate_module_inputs

        result, msg = validate_module_inputs(data_utils = {}, data_inputs = {"Time_Series_Sample": None}, reactives_shiny = "bad")
        assert result is False
        assert "reactives_shiny" in msg

    @pytest.mark.unit()
    def test_missing_time_series_key_returns_false(self):
        """Test that missing time series key returns false."""
        from src.dashboard.shiny_utils.utils_tab_inputs import validate_module_inputs

        result, msg = validate_module_inputs(data_utils = {}, data_inputs = {}, reactives_shiny = {})
        assert result is False
        assert "Time_Series_Sample" in msg

    @pytest.mark.unit()
    def test_valid_inputs_returns_true(self):
        """Test that valid inputs returns true."""
        from src.dashboard.shiny_utils.utils_tab_inputs import validate_module_inputs

        result, msg = validate_module_inputs(
            data_utils={},
            data_inputs={"Time_Series_Sample": None},
            reactives_shiny={},
        )
        assert result is True
        assert msg == ""


class Test_Validate_Time_Period_Selection:
    """Tests for validate_time_period_selection in utils_tab_inputs."""

    @pytest.mark.unit()
    def test_none_returns_false(self):
        """Test that none returns false."""
        from src.dashboard.shiny_utils.utils_tab_inputs import validate_time_period_selection

        result, msg = validate_time_period_selection(time_period_value = None)
        assert result is False

    @pytest.mark.unit()
    def test_non_string_returns_false(self):
        """Test that non string returns false."""
        from src.dashboard.shiny_utils.utils_tab_inputs import validate_time_period_selection

        result, msg = validate_time_period_selection(time_period_value = 123)
        assert result is False

    @pytest.mark.unit()
    def test_invalid_period_string_returns_false(self):
        """Test that invalid period string returns false."""
        from src.dashboard.shiny_utils.utils_tab_inputs import validate_time_period_selection

        result, msg = validate_time_period_selection(time_period_value = "last_100_years")
        assert result is False

    @pytest.mark.unit()
    def test_last_1_year_valid(self):
        """Test that last 1 year valid."""
        from src.dashboard.shiny_utils.utils_tab_inputs import validate_time_period_selection

        result, msg = validate_time_period_selection(time_period_value = "last_1_year")
        assert result is True
        assert msg == ""

    @pytest.mark.unit()
    def test_ytd_valid(self):
        """Test that ytd valid."""
        from src.dashboard.shiny_utils.utils_tab_inputs import validate_time_period_selection

        result, msg = validate_time_period_selection(time_period_value = "ytd")
        assert result is True

    @pytest.mark.unit()
    def test_custom_valid(self):
        """Test that custom valid."""
        from src.dashboard.shiny_utils.utils_tab_inputs import validate_time_period_selection

        result, msg = validate_time_period_selection(time_period_value = "custom")
        assert result is True

    @pytest.mark.unit()
    def test_all_valid_periods_accepted(self):
        """Test that all valid periods accepted."""
        from src.dashboard.shiny_utils.utils_tab_inputs import validate_time_period_selection

        valid = ["custom", "last_1_year", "last_3_years", "last_5_years", "last_10_years", "ytd"]
        for period in valid:
            result, msg = validate_time_period_selection(time_period_value = period)
            assert result is True, f"Expected True for '{period}', got False: {msg}"


class Test_Validate_Date_Range_Input:
    """Tests for validate_date_range_input in utils_tab_inputs."""

    @pytest.mark.unit()
    def test_none_in_preset_mode_returns_true(self):
        """Test that none in preset mode returns true."""
        from src.dashboard.shiny_utils.utils_tab_inputs import validate_date_range_input

        result, msg = validate_date_range_input(date_range_input = None, time_period_mode="preset")
        assert result is True

    @pytest.mark.unit()
    def test_none_in_custom_mode_returns_false(self):
        """Test that none in custom mode returns false."""
        from src.dashboard.shiny_utils.utils_tab_inputs import validate_date_range_input

        result, msg = validate_date_range_input(date_range_input = None, time_period_mode="custom")
        assert result is False

    @pytest.mark.unit()
    def test_non_list_returns_false(self):
        """Test that non list returns false."""
        from src.dashboard.shiny_utils.utils_tab_inputs import validate_date_range_input

        result, msg = validate_date_range_input(date_range_input = "2023-01-01")
        assert result is False

    @pytest.mark.unit()
    def test_too_many_elements_returns_false(self):
        """Test that too many elements returns false."""
        from src.dashboard.shiny_utils.utils_tab_inputs import validate_date_range_input

        result, msg = validate_date_range_input(date_range_input = [date(2023, 1, 1), date(2023, 6, 1), date(2023, 12, 31)])
        assert result is False

    @pytest.mark.unit()
    def test_valid_date_range_returns_true(self):
        """Test that valid date range returns true."""
        from src.dashboard.shiny_utils.utils_tab_inputs import validate_date_range_input

        result, msg = validate_date_range_input(date_range_input = [date(2023, 1, 1), date(2023, 12, 31)])
        assert result is True

    @pytest.mark.unit()
    def test_valid_datetime_range_returns_true(self):
        """Test that ordered datetimes return true after comparison."""
        from src.dashboard.shiny_utils.utils_tab_inputs import validate_date_range_input

        start = datetime(2023, 1, 1)
        end = datetime(2023, 12, 31)
        result, msg = validate_date_range_input(date_range_input = [start, end])
        assert result is True
        assert msg == ""

    @pytest.mark.unit()
    def test_reversed_date_range_returns_false(self):
        """Test that reversed date range returns false."""
        from src.dashboard.shiny_utils.utils_tab_inputs import validate_date_range_input

        start = datetime(2023, 12, 31)
        end = datetime(2023, 1, 1)
        result, msg = validate_date_range_input(date_range_input = [start, end])
        assert result is False

    @pytest.mark.unit()
    def test_none_values_in_list_returns_false(self):
        """Test that none values in list returns false."""
        from src.dashboard.shiny_utils.utils_tab_inputs import validate_date_range_input

        result, msg = validate_date_range_input(date_range_input = [None, date(2023, 12, 31)])
        assert result is False


class Test_Safe_Get_Input_Value:
    """Tests for safe_get_input_value in utils_tab_inputs."""

    @pytest.mark.unit()
    def test_none_input_object_returns_default(self):
        """Test that none input object returns default."""
        from src.dashboard.shiny_utils.utils_tab_inputs import safe_get_input_value

        result = safe_get_input_value(input_object = None, input_identifier = "some_id", default_value=42)
        assert result == 42

    @pytest.mark.unit()
    def test_non_string_identifier_returns_default(self):
        """Test that non string identifier returns default."""
        from src.dashboard.shiny_utils.utils_tab_inputs import safe_get_input_value

        from unittest.mock import MagicMock

        result = safe_get_input_value(input_object = MagicMock(), input_identifier = 123, default_value=99)
        assert result == 99

    @pytest.mark.unit()
    def test_empty_identifier_returns_default(self):
        """Test that empty identifier returns default."""
        from src.dashboard.shiny_utils.utils_tab_inputs import safe_get_input_value

        from unittest.mock import MagicMock

        result = safe_get_input_value(input_object = MagicMock(), input_identifier = "   ", default_value="fallback")
        assert result == "fallback"

    @pytest.mark.unit()
    def test_valid_identifier_returns_lookup_value(self):
        """Test that valid identifier returns lookup value."""
        from src.dashboard.shiny_utils.utils_tab_inputs import safe_get_input_value

        class _ValueProxy:
            def get(self):
                return "resolved"

        class _InputProxy:
            def __getitem__(self, key):
                assert key == ["field_id"]
                return _ValueProxy()

        result = safe_get_input_value(input_object = _InputProxy(), input_identifier = "field_id", default_value="fallback")
        assert result == "resolved"

    @pytest.mark.unit()
    def test_lookup_none_returns_default(self):
        """Test that lookup returning none falls back to default."""
        from src.dashboard.shiny_utils.utils_tab_inputs import safe_get_input_value

        class _ValueProxy:
            def get(self):
                return None

        class _InputProxy:
            def __getitem__(self, key):
                assert key == ["field_id"]
                return _ValueProxy()

        result = safe_get_input_value(input_object = _InputProxy(), input_identifier = "field_id", default_value="fallback")
        assert result == "fallback"

    @pytest.mark.unit()
    def test_lookup_exception_returns_default(self):
        """Test that lookup exceptions return default."""
        from src.dashboard.shiny_utils.utils_tab_inputs import safe_get_input_value

        class _InputProxy:
            def __getitem__(self, key):
                raise KeyError(key)

        result = safe_get_input_value(input_object = _InputProxy(), input_identifier = "field_id", default_value="fallback")
        assert result == "fallback"


class Test_Find_Date_Column_Name:
    """Tests for find_date_column_name in utils_tab_inputs."""

    @pytest.mark.unit()
    def test_none_returns_none(self):
        """Test that none returns none."""
        from src.dashboard.shiny_utils.utils_tab_inputs import find_date_column_name

        result = find_date_column_name(data_frame = None)
        assert result is None

    @pytest.mark.unit()
    def test_no_columns_attr_returns_none(self):
        """Test that no columns attr returns none."""
        from src.dashboard.shiny_utils.utils_tab_inputs import find_date_column_name

        result = find_date_column_name(data_frame = 42)
        assert result is None

    @pytest.mark.unit()
    def test_lowercase_date_column_found(self):
        """Test that lowercase date column found."""
        import polars as pl
        from src.dashboard.shiny_utils.utils_tab_inputs import find_date_column_name

        df = pl.DataFrame({"date": [date(2023, 1, 1)], "v": [1.0]})
        result = find_date_column_name(data_frame = df)
        assert result == "date"

    @pytest.mark.unit()
    def test_titlecase_date_column_found(self):
        """Test that titlecase date column found."""
        import polars as pl
        from src.dashboard.shiny_utils.utils_tab_inputs import find_date_column_name

        df = pl.DataFrame({"Date": [date(2023, 1, 1)], "v": [1.0]})
        result = find_date_column_name(data_frame = df)
        assert result == "Date"

    @pytest.mark.unit()
    def test_no_date_column_returns_none(self):
        """Test that no date column returns none."""
        import polars as pl
        from src.dashboard.shiny_utils.utils_tab_inputs import find_date_column_name

        df = pl.DataFrame({"value": [1.0], "name": ["test"]})
        result = find_date_column_name(data_frame = df)
        assert result is None


class Test_Calculate_Preset_Date_Range:
    """Tests for calculate_preset_date_range in utils_tab_inputs."""

    @pytest.mark.unit()
    def test_non_string_returns_none_tuple(self):
        """Test that non string returns none tuple."""
        from src.dashboard.shiny_utils.utils_tab_inputs import calculate_preset_date_range

        start, end = calculate_preset_date_range(time_period_selection = 123, max_date_available = date(2023, 12, 31), min_date_available = date(2020, 1, 1))
        assert start is None
        assert end is None

    @pytest.mark.unit()
    def test_none_max_date_returns_none_tuple(self):
        """Test that none max date returns none tuple."""
        from src.dashboard.shiny_utils.utils_tab_inputs import calculate_preset_date_range

        start, end = calculate_preset_date_range(time_period_selection = "last_1_year", max_date_available = None, min_date_available = date(2020, 1, 1))
        assert start is None
        assert end is None

    @pytest.mark.unit()
    def test_last_1_year_returns_dates(self):
        """Test that last 1 year returns dates."""
        from src.dashboard.shiny_utils.utils_tab_inputs import calculate_preset_date_range

        max_d = date(2023, 12, 31)
        min_d = date(2015, 1, 1)
        start, end = calculate_preset_date_range(time_period_selection = "last_1_year", max_date_available = max_d, min_date_available = min_d)
        assert start is not None
        assert end is not None
        assert end == max_d

    @pytest.mark.unit()
    def test_ytd_returns_jan_1_to_max(self):
        """Test that ytd returns jan 1 to max."""
        from src.dashboard.shiny_utils.utils_tab_inputs import calculate_preset_date_range

        max_d = date(2023, 6, 30)
        min_d = date(2010, 1, 1)
        start, end = calculate_preset_date_range(time_period_selection = "ytd", max_date_available = max_d, min_date_available = min_d)
        assert start is not None
        assert start.month == 1
        assert start.day == 1
        assert start.year == 2023

    @pytest.mark.unit()
    def test_unknown_period_falls_back_to_full_range(self):
        """Test that unknown period falls back to full range."""
        from src.dashboard.shiny_utils.utils_tab_inputs import calculate_preset_date_range

        max_d = date(2023, 12, 31)
        min_d = date(2010, 1, 1)
        start, end = calculate_preset_date_range(time_period_selection = "unknown_period", max_date_available = max_d, min_date_available = min_d)
        assert start == min_d
        assert end == max_d


class Test_Utils_Tab_Inputs_Module_Structure:
    """Tests for the module-level structure of utils_tab_inputs."""

    @pytest.mark.unit()
    def test_module_importable(self):
        """Test that module importable."""
        import src.dashboard.shiny_utils.utils_tab_inputs as m

        assert m is not None

    @pytest.mark.unit()
    def test_all_expected_functions_present(self):
        """Test that all expected functions present."""
        from src.dashboard.shiny_utils import utils_tab_inputs

        expected = [
            "validate_module_inputs",
            "validate_time_period_selection",
            "validate_date_range_input",
            "safe_get_input_value",
            "find_date_column_name",
            "calculate_preset_date_range",
        ]
        for name in expected:
            assert hasattr(utils_tab_inputs, name), f"Missing: {name}"
            assert callable(getattr(utils_tab_inputs, name))


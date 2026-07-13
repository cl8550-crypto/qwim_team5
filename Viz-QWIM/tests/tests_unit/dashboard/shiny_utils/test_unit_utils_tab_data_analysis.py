def validate_data_analysis_parameters(data_utils=None, data_inputs=None, reactives_shiny=None):
    """Validate parameters for data analysis module using defensive programming."""

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


# ============================================================================
# pytest imports (must follow all helper code above)
# ============================================================================
import pytest


class Test_Validate_Data_Analysis_Parameters:
    """Tests for validate_data_analysis_parameters in utils_tab_data_analysis."""

    @pytest.mark.unit()
    def test_none_data_utils_returns_false(self):
        """Test that none data utils returns false."""
        from src.dashboard.shiny_utils.utils_tab_data_analysis import validate_data_analysis_parameters

        result, msg = validate_data_analysis_parameters(data_utils = None, data_inputs = {}, reactives_shiny = {})
        assert result is False
        assert "data_utils" in msg

    @pytest.mark.unit()
    def test_none_data_inputs_returns_false(self):
        """Test that none data inputs returns false."""
        from src.dashboard.shiny_utils.utils_tab_data_analysis import validate_data_analysis_parameters

        result, msg = validate_data_analysis_parameters(data_utils = {}, data_inputs = None, reactives_shiny = {})
        assert result is False
        assert "data_inputs" in msg

    @pytest.mark.unit()
    def test_none_reactives_shiny_returns_false(self):
        """Test that none reactives shiny returns false."""
        from src.dashboard.shiny_utils.utils_tab_data_analysis import validate_data_analysis_parameters

        result, msg = validate_data_analysis_parameters(data_utils = {}, data_inputs = {}, reactives_shiny = None)
        assert result is False
        assert "reactives_shiny" in msg

    @pytest.mark.unit()
    def test_non_dict_data_utils_returns_false(self):
        """Test that non dict data utils returns false."""
        from src.dashboard.shiny_utils.utils_tab_data_analysis import validate_data_analysis_parameters

        result, msg = validate_data_analysis_parameters(data_utils = "not_dict", data_inputs = {}, reactives_shiny = {})
        assert result is False

    @pytest.mark.unit()
    def test_non_dict_data_inputs_returns_false(self):
        """Test that non dict data inputs returns false."""
        from src.dashboard.shiny_utils.utils_tab_data_analysis import validate_data_analysis_parameters

        result, msg = validate_data_analysis_parameters(data_utils = {}, data_inputs = "not_dict", reactives_shiny = {})
        assert result is False

    @pytest.mark.unit()
    def test_non_dict_reactives_returns_false(self):
        """Test that non dict reactives returns false."""
        from src.dashboard.shiny_utils.utils_tab_data_analysis import validate_data_analysis_parameters

        result, msg = validate_data_analysis_parameters(data_utils = {}, data_inputs = {}, reactives_shiny = "not_dict")
        assert result is False

    @pytest.mark.unit()
    def test_missing_time_series_sample_returns_false(self):
        """Test that missing time series sample returns false."""
        from src.dashboard.shiny_utils.utils_tab_data_analysis import validate_data_analysis_parameters

        result, msg = validate_data_analysis_parameters(data_utils = {}, data_inputs = {}, reactives_shiny = {})
        assert result is False
        assert "Time_Series_Sample" in msg

    @pytest.mark.unit()
    def test_valid_inputs_returns_true(self):
        """Test that valid inputs returns true."""
        from src.dashboard.shiny_utils.utils_tab_data_analysis import validate_data_analysis_parameters

        result, msg = validate_data_analysis_parameters(
            data_utils={},
            data_inputs={"Time_Series_Sample": None},
            reactives_shiny={},
        )
        assert result is True
        assert msg == ""


class Test_Utils_Tab_Data_Analysis_Module_Structure:
    """Tests for the module-level structure of utils_tab_data_analysis."""

    @pytest.mark.unit()
    def test_module_importable(self):
        """Test that module importable."""
        import src.dashboard.shiny_utils.utils_tab_data_analysis as m

        assert m is not None

    @pytest.mark.unit()
    def test_validate_function_callable(self):
        """Test that validate function callable."""
        from src.dashboard.shiny_utils.utils_tab_data_analysis import validate_data_analysis_parameters

        assert callable(validate_data_analysis_parameters)


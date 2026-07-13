"""Unit tests for reactives_validation module."""

from __future__ import annotations

import pytest


@pytest.mark.unit()
class Test_Reactives_Validation_Module_Imports:
    """Tests that reactives_validation exports the expected names."""

    @pytest.mark.unit()
    def test_required_categories_constant_exists(self):
        """REQUIRED_CATEGORIES should be a non-empty list."""
        from src.dashboard.shiny_utils.reactives_validation import REQUIRED_CATEGORIES

        assert isinstance(REQUIRED_CATEGORIES, list)
        assert len(REQUIRED_CATEGORIES) > 0

    @pytest.mark.unit()
    def test_required_categories_includes_advisor_info(self):
        """Advisor_Info must be in REQUIRED_CATEGORIES."""
        from src.dashboard.shiny_utils.reactives_validation import REQUIRED_CATEGORIES

        assert "Advisor_Info" in REQUIRED_CATEGORIES

    @pytest.mark.unit()
    def test_validate_data_utils_parameter_importable(self):
        """validate_data_utils_parameter must be importable from reactives_validation."""
        from src.dashboard.shiny_utils.reactives_validation import validate_data_utils_parameter

        assert callable(validate_data_utils_parameter)

    @pytest.mark.unit()
    def test_validate_reactives_shiny_structure_importable(self):
        """validate_reactives_shiny_structure must be importable."""
        from src.dashboard.shiny_utils.reactives_validation import (
            validate_reactives_shiny_structure,
        )

        assert callable(validate_reactives_shiny_structure)

    @pytest.mark.unit()
    def test_validate_reactive_key_access_importable(self):
        """validate_reactive_key_access must be importable."""
        from src.dashboard.shiny_utils.reactives_validation import validate_reactive_key_access

        assert callable(validate_reactive_key_access)

    @pytest.mark.unit()
    def test_validate_category_name_importable(self):
        """validate_category_name must be importable."""
        from src.dashboard.shiny_utils.reactives_validation import validate_category_name

        assert callable(validate_category_name)


@pytest.mark.unit()
class Test_Validate_Data_Utils_Parameter_Direct:
    """Tests for validate_data_utils_parameter imported directly from split module."""

    @pytest.mark.unit()
    def test_none_returns_false(self):
        """None data_utils returns (False, message)."""
        from src.dashboard.shiny_utils.reactives_validation import validate_data_utils_parameter

        result, msg = validate_data_utils_parameter(data_utils = None)
        assert result is False
        assert msg

    @pytest.mark.unit()
    def test_non_dict_returns_false(self):
        """Non-dict data_utils returns (False, message)."""
        from src.dashboard.shiny_utils.reactives_validation import validate_data_utils_parameter

        result, msg = validate_data_utils_parameter(data_utils = "not-a-dict")
        assert result is False

    @pytest.mark.unit()
    def test_valid_dict_returns_true(self):
        """Valid dict data_utils returns (True, '')."""
        from src.dashboard.shiny_utils.reactives_validation import validate_data_utils_parameter

        result, msg = validate_data_utils_parameter(data_utils = {"key": "value"})
        assert result is True


@pytest.mark.unit()
class Test_Validate_Reactive_Key_Access_None_Key:
    """Tests for validate_reactive_key_access covering None/non-dict branches."""

    @pytest.mark.unit()
    def Test_None_Key_Name_Returns_False(self):
        """Passing key_name=None returns (False, message) without raising."""
        from src.dashboard.shiny_utils.reactives_validation import validate_reactive_key_access

        result, msg = validate_reactive_key_access(category_dict = {"a": 1}, key_name = None, category_name = "test_category")
        assert result is False
        assert "key_name" in msg.lower() or "none" in msg.lower()

    @pytest.mark.unit()
    def Test_Non_Dict_Category_Dict_Returns_False(self):
        """Passing a non-dict category_dict returns (False, message)."""
        from src.dashboard.shiny_utils.reactives_validation import validate_reactive_key_access

        result, msg = validate_reactive_key_access(category_dict = [1, 2, 3], key_name = "my_key", category_name = "test_category")
        assert result is False
        assert "not a dictionary" in msg.lower() or "dict" in msg.lower()


@pytest.mark.unit()
class Test_Validate_Category_Name_With_Advisor_Info:
    """Tests for validate_category_name with Advisor_Info included."""

    @pytest.mark.unit()
    def test_advisor_info_is_valid_category(self):
        """Advisor_Info must be accepted as a valid category name."""
        from src.dashboard.shiny_utils.reactives_validation import validate_category_name

        result, msg = validate_category_name(category_name = "Advisor_Info")
        assert result is True
        assert msg == ""

    @pytest.mark.unit()
    def test_invalid_category_returns_false(self):
        """Unknown category name returns (False, message)."""
        from src.dashboard.shiny_utils.reactives_validation import validate_category_name

        result, msg = validate_category_name(category_name = "Unknown_Category")
        assert result is False
        assert "Unknown_Category" in msg

    @pytest.mark.unit()
    def test_none_category_returns_false(self):
        """None category name returns (False, message)."""
        from src.dashboard.shiny_utils.reactives_validation import validate_category_name

        result, msg = validate_category_name(category_name = None)
        assert result is False

"""Unit tests for lightweight helper functions re-exported by utils_client.

The file covers formatter, validator, parser, and compatibility-facade helpers
that are imported through ``src.clients_QWIM.utils_client``.
"""

from __future__ import annotations

import pytest


@pytest.mark.unit()
class Test_Extract_Client_Data_Firm_Default_Injection:
    """Tests for Firm default injection in extract_client_data_from_worksheet_PDF."""

    @pytest.mark.unit()
    def test_firm_default_injected_when_absent(self, tmp_path):
        """Firm is injected from defaults when not present in extracted Advisor_Info."""
        from src.clients_QWIM.utils_client import _ADVISOR_INFO_DEFAULT_VALUES

        # Verify the default exists
        assert "firm" in _ADVISOR_INFO_DEFAULT_VALUES
        assert len(_ADVISOR_INFO_DEFAULT_VALUES["firm"]) > 0

    @pytest.mark.unit()
    def test_advisor_info_default_values_has_firm(self):
        """_ADVISOR_INFO_DEFAULT_VALUES must contain the firm key."""
        from src.clients_QWIM.utils_client import _ADVISOR_INFO_DEFAULT_VALUES

        assert "firm" in _ADVISOR_INFO_DEFAULT_VALUES
        assert _ADVISOR_INFO_DEFAULT_VALUES["firm"] == "QWIM AI Wealth Management"


@pytest.mark.unit()
class Class_Test_Validate_Required_Advisor_Info_Section:
    """Tests for validate_required_advisor_info_section."""

    @pytest.mark.unit()
    def Test_Firm_Is_Not_Required_When_Absent(self):
        """Firm should not appear in validation messages when absent — it has a default."""
        from src.clients_QWIM.utils_client import validate_required_advisor_info_section

        # All required non-default fields present, firm intentionally missing
        extracted = {
            "Advisor_Info": {
                "name": "Jane Advisor",
                "title": "CFP",
                "credentials": "CFP®",
                "team": "Team One",
                # firm deliberately absent
                "email": "jane@example.com",
                "phone_number": "2125551234",
                "address": "1 Main St, NY",
            }
        }
        messages = validate_required_advisor_info_section(extracted_data = extracted)
        firm_messages = [m for m in messages if "Firm" in m]
        assert firm_messages == [], f"Unexpected Firm validation error: {firm_messages}"

    @pytest.mark.unit()
    def Test_Missing_Name_Is_Reported(self):
        """Missing Name (non-default field) is still reported."""
        from src.clients_QWIM.utils_client import validate_required_advisor_info_section

        extracted = {
            "Advisor_Info": {
                "name": "",
                "title": "CFP",
                "credentials": "CFP®",
                "team": "Team One",
                "email": "jane@example.com",
                "phone_number": "2125551234",
                "address": "1 Main St, NY",
            }
        }
        messages = validate_required_advisor_info_section(extracted_data = extracted)
        name_messages = [m for m in messages if "Name" in m]
        assert len(name_messages) > 0

    @pytest.mark.unit()
    def Test_All_Fields_Present_Returns_Empty_List(self):
        """Valid complete Advisor_Info with no firm should return no errors."""
        from src.clients_QWIM.utils_client import validate_required_advisor_info_section

        extracted = {
            "Advisor_Info": {
                "name": "Jane Advisor",
                "title": "Financial Advisor",
                "credentials": "CFP®",
                "team": "Team One",
                "email": "jane@example.com",
                "phone_number": "2125551234",
                "address": "1 Main St, NY",
            }
        }
        messages = validate_required_advisor_info_section(extracted_data = extracted)
        assert messages == []

    @pytest.mark.unit()
    def Test_Missing_Advisor_Info_Section_Is_Reported(self):
        """Missing Advisor_Info section is reported as a single error."""
        from src.clients_QWIM.utils_client import validate_required_advisor_info_section

        messages = validate_required_advisor_info_section(extracted_data = {"Advisor_Info": None})
        assert len(messages) == 1
        assert "missing" in messages[0].lower()

    @pytest.mark.unit()
    def Test_Invalid_Extracted_Data_Raises_Exception(self):
        """Non-dict extracted_data raises Exception_Validation_Input."""
        from src.clients_QWIM.utils_client import validate_required_advisor_info_section
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            validate_required_advisor_info_section(extracted_data = "not-a-dict")


@pytest.mark.unit()
class Class_Test_Validate_Extracted_Client_Data_Checkbox_Fields:
    """Tests for checkbox boolean handling in validate_extracted_client_data."""

    @pytest.mark.unit()
    def Test_Checkbox_Field_Map_Includes_Income_Checkbox_Keys(self):
        """Checkbox field map should include boolean income flags by section."""
        from src.clients_QWIM.utils_client import build_checkbox_fields_by_section

        checkbox_fields = build_checkbox_fields_by_section()

        assert "Income" in checkbox_fields
        assert "social_security_cola_indexed" in checkbox_fields["Income"]
        assert "income_pension_inflation_indexed" in checkbox_fields["Income"]

    @pytest.mark.unit()
    def Test_Social_Security_COLA_Indexed_Flag_Is_Not_Treated_As_Amount(self):
        """Boolean COLA flags must not emit whole-dollar validation warnings."""
        from src.clients_QWIM.utils_client import validate_extracted_client_data

        extracted = {
            "Personal_Info": {
                "client_primary": {
                    "status_marital": "Single",
                    "gender": "Male",
                    "tolerance_risk": "Moderate",
                    "state": "California",
                    "age_current": 65,
                    "age_retirement": 67,
                    "age_annuity_income_starting": 67,
                    "code_zip": 90210,
                },
            },
            "Assets": {
                "client_primary": {
                    "assets_taxable": 100000,
                    "assets_tax_deferred": 200000,
                    "assets_tax_free": 50000,
                },
            },
            "Goals": {
                "client_primary": {
                    "goal_essential": 50000,
                    "goal_important": 10000,
                    "goal_aspirational": 5000,
                    "growth_rate_flag": True,
                    "growth_rate_same_as_inflation_flag": False,
                    "growth_rate": 2,
                },
            },
            "Income": {
                "client_primary": {
                    "income_social_security": 20000,
                    "social_security_cola_indexed": True,
                    "income_pension": 0,
                    "income_pension_inflation_indexed": False,
                    "income_annuity_existing": 0,
                    "income_annuity_existing_inflation_indexed": False,
                    "income_other": 0,
                    "income_other_inflation_indexed": False,
                },
                "client_partner": {
                    "income_social_security": 15000,
                    "social_security_cola_indexed": False,
                    "income_pension": 0,
                    "income_pension_inflation_indexed": False,
                    "income_annuity_existing": 0,
                    "income_annuity_existing_inflation_indexed": False,
                    "income_other": 0,
                    "income_other_inflation_indexed": False,
                },
            },
        }

        _, warnings_list = validate_extracted_client_data(extracted_data = extracted)

        assert all("social_security_cola_indexed" not in warning for warning in warnings_list)

    @pytest.mark.unit()
    def Test_Numeric_Income_Field_Is_Still_Validated_As_Amount(self):
        """Numeric income fields must still emit whole-dollar validation warnings when invalid."""
        from src.clients_QWIM.utils_client import validate_extracted_client_data

        extracted = {
            "Personal_Info": {
                "client_primary": {
                    "status_marital": "Single",
                    "gender": "Male",
                    "tolerance_risk": "Moderate",
                    "state": "California",
                    "age_current": 65,
                    "age_retirement": 67,
                    "age_annuity_income_starting": 67,
                    "code_zip": 90210,
                },
            },
            "Income": {
                "client_primary": {
                    "income_social_security": "12,000.50",
                    "social_security_cola_indexed": True,
                },
            },
        }

        _, warnings_list = validate_extracted_client_data(extracted_data = extracted)

        assert any("income_social_security" in warning for warning in warnings_list)


# ===========================================================================
# Class_Test_Safe_Numeric
# ===========================================================================


@pytest.mark.unit()
class Class_Test_Safe_Numeric:
    """Tests for _safe_numeric helper."""

    @pytest.mark.unit()
    def Test_None_Returns_Default_Zero(self):
        from src.clients_QWIM.utils_client import _safe_numeric
        assert _safe_numeric(value = None) == 0.0

    @pytest.mark.unit()
    def Test_Empty_String_Returns_Default_Zero(self):
        from src.clients_QWIM.utils_client import _safe_numeric
        assert _safe_numeric(value = "") == 0.0

    @pytest.mark.unit()
    def Test_Integer_String_Converts_To_Float(self):
        from src.clients_QWIM.utils_client import _safe_numeric
        assert _safe_numeric(value = "42") == 42.0

    @pytest.mark.unit()
    def Test_Dollar_And_Comma_Are_Stripped(self):
        from src.clients_QWIM.utils_client import _safe_numeric
        assert _safe_numeric(value = "$1,234.50") == pytest.approx(1234.50)

    @pytest.mark.unit()
    def Test_Invalid_String_Returns_Default_Zero(self):
        from src.clients_QWIM.utils_client import _safe_numeric
        assert _safe_numeric(value = "abc") == 0.0

    @pytest.mark.unit()
    def Test_Custom_Default_Is_Used_For_None(self):
        from src.clients_QWIM.utils_client import _safe_numeric
        assert _safe_numeric(value = None, default=99.0) == 99.0

    @pytest.mark.unit()
    def Test_Integer_Value_Converts_To_Float(self):
        from src.clients_QWIM.utils_client import _safe_numeric
        assert _safe_numeric(value = 5) == 5.0

    @pytest.mark.unit()
    def Test_Bool_Value_Uses_Default(self):
        from src.clients_QWIM.utils_client import _safe_numeric

        assert _safe_numeric(value = True, default=99.0) == 99.0


# ===========================================================================
# Class_Test_Parse_Whole_Dollar_Amount
# ===========================================================================


@pytest.mark.unit()
class Class_Test_Parse_Whole_Dollar_Amount:
    """Tests for _parse_whole_dollar_amount helper."""

    @pytest.mark.unit()
    def Test_None_Returns_None(self):
        from src.clients_QWIM.utils_client import _parse_whole_dollar_amount
        assert _parse_whole_dollar_amount(value = None) is None

    @pytest.mark.unit()
    def Test_Empty_String_Returns_None(self):
        from src.clients_QWIM.utils_client import _parse_whole_dollar_amount
        assert _parse_whole_dollar_amount(value = "") is None

    @pytest.mark.unit()
    def Test_Bool_True_Returns_None(self):
        from src.clients_QWIM.utils_client import _parse_whole_dollar_amount
        assert _parse_whole_dollar_amount(value = True) is None

    @pytest.mark.unit()
    def Test_Bool_False_Returns_None(self):
        from src.clients_QWIM.utils_client import _parse_whole_dollar_amount
        assert _parse_whole_dollar_amount(value = False) is None

    @pytest.mark.unit()
    def Test_Integer_Returns_Integer(self):
        from src.clients_QWIM.utils_client import _parse_whole_dollar_amount
        assert _parse_whole_dollar_amount(value = 500) == 500

    @pytest.mark.unit()
    def Test_Float_Integer_Value_Returns_Int(self):
        from src.clients_QWIM.utils_client import _parse_whole_dollar_amount
        assert _parse_whole_dollar_amount(value = 500.0) == 500

    @pytest.mark.unit()
    def Test_Float_Decimal_Returns_None(self):
        from src.clients_QWIM.utils_client import _parse_whole_dollar_amount
        assert _parse_whole_dollar_amount(value = 500.5) is None

    @pytest.mark.unit()
    def Test_Plain_Digit_String_Returns_Integer(self):
        from src.clients_QWIM.utils_client import _parse_whole_dollar_amount
        assert _parse_whole_dollar_amount(value = "12345") == 12345

    @pytest.mark.unit()
    def Test_Comma_Formatted_String_Returns_Integer(self):
        from src.clients_QWIM.utils_client import _parse_whole_dollar_amount
        assert _parse_whole_dollar_amount(value = "12,345") == 12345

    @pytest.mark.unit()
    def Test_Negative_String_Returns_Integer(self):
        from src.clients_QWIM.utils_client import _parse_whole_dollar_amount
        assert _parse_whole_dollar_amount(value = "-5000") == -5000

    @pytest.mark.unit()
    def Test_Dollar_Sign_Is_Stripped(self):
        from src.clients_QWIM.utils_client import _parse_whole_dollar_amount
        assert _parse_whole_dollar_amount(value = "$1000") == 1000

    @pytest.mark.unit()
    def Test_Whitespace_Only_String_Returns_None(self):
        from src.clients_QWIM.utils_client import _parse_whole_dollar_amount
        assert _parse_whole_dollar_amount(value = "   ") is None

    @pytest.mark.unit()
    def Test_Letters_String_Returns_None(self):
        from src.clients_QWIM.utils_client import _parse_whole_dollar_amount
        assert _parse_whole_dollar_amount(value = "abc") is None

    @pytest.mark.unit()
    def Test_Decimal_String_Returns_None(self):
        from src.clients_QWIM.utils_client import _parse_whole_dollar_amount
        assert _parse_whole_dollar_amount(value = "12.50") is None


# ===========================================================================
# Class_Test_Safe_Whole_Dollar_Numeric
# ===========================================================================


@pytest.mark.unit()
class Class_Test_Safe_Whole_Dollar_Numeric:
    """Tests for _safe_whole_dollar_numeric helper."""

    @pytest.mark.unit()
    def Test_Valid_Whole_Dollar_Converts_To_Float(self):
        from src.clients_QWIM.utils_client import _safe_whole_dollar_numeric
        assert _safe_whole_dollar_numeric(value = 1000) == 1000.0

    @pytest.mark.unit()
    def Test_Invalid_Value_Returns_Default_Zero(self):
        from src.clients_QWIM.utils_client import _safe_whole_dollar_numeric
        assert _safe_whole_dollar_numeric(value = None) == 0.0

    @pytest.mark.unit()
    def Test_Custom_Default_Is_Used_For_Invalid_Value(self):
        from src.clients_QWIM.utils_client import _safe_whole_dollar_numeric
        assert _safe_whole_dollar_numeric(value = "abc", default=5.0) == 5.0

    @pytest.mark.unit()
    def Test_Comma_Formatted_String_Converts_To_Float(self):
        from src.clients_QWIM.utils_client import _safe_whole_dollar_numeric
        assert _safe_whole_dollar_numeric(value = "50,000") == 50000.0


# ===========================================================================
# Class_Test_Validate_Choice_Field
# ===========================================================================


@pytest.mark.unit()
class Class_Test_Validate_Choice_Field:
    """Tests for _validate_choice_field helper."""

    @pytest.mark.unit()
    def Test_None_Value_Produces_No_Warning(self):
        from src.clients_QWIM.utils_client import _validate_choice_field
        warnings: list[str] = []
        _validate_choice_field(section = {"x": None}, field_key = "x", valid_choices = ["A", "B"], client_role = "primary", warnings_list = warnings)
        assert warnings == []

    @pytest.mark.unit()
    def Test_Empty_String_Produces_No_Warning(self):
        from src.clients_QWIM.utils_client import _validate_choice_field
        warnings: list[str] = []
        _validate_choice_field(section = {"x": ""}, field_key = "x", valid_choices = ["A", "B"], client_role = "primary", warnings_list = warnings)
        assert warnings == []

    @pytest.mark.unit()
    def Test_Valid_Value_Produces_No_Warning(self):
        from src.clients_QWIM.utils_client import _validate_choice_field
        warnings: list[str] = []
        _validate_choice_field(section = {"x": "A"}, field_key = "x", valid_choices = ["A", "B"], client_role = "primary", warnings_list = warnings)
        assert warnings == []

    @pytest.mark.unit()
    def Test_Case_Insensitive_Match_Produces_No_Warning(self):
        from src.clients_QWIM.utils_client import _validate_choice_field
        warnings: list[str] = []
        _validate_choice_field(section = {"x": "a"}, field_key = "x", valid_choices = ["A", "B"], client_role = "primary", warnings_list = warnings)
        assert warnings == []

    @pytest.mark.unit()
    def Test_Invalid_Value_Appends_Warning(self):
        from src.clients_QWIM.utils_client import _validate_choice_field
        warnings: list[str] = []
        _validate_choice_field(section = {"x": "C"}, field_key = "x", valid_choices = ["A", "B"], client_role = "primary", warnings_list = warnings)
        assert len(warnings) == 1
        assert "C" in warnings[0]

    @pytest.mark.unit()
    def Test_Missing_Key_Produces_No_Warning(self):
        from src.clients_QWIM.utils_client import _validate_choice_field
        warnings: list[str] = []
        _validate_choice_field(section = {}, field_key = "x", valid_choices = ["A", "B"], client_role = "primary", warnings_list = warnings)
        assert warnings == []


# ===========================================================================
# Class_Test_Validate_Numeric_Range
# ===========================================================================


@pytest.mark.unit()
class Class_Test_Validate_Numeric_Range:
    """Tests for _validate_numeric_range helper."""

    @pytest.mark.unit()
    def Test_None_Value_Produces_No_Warning(self):
        from src.clients_QWIM.utils_client import _validate_numeric_range
        warnings: list[str] = []
        _validate_numeric_range(section = {"x": None}, field_key = "x", min_val = 0, max_val = 100, client_role = "primary", warnings_list = warnings)
        assert warnings == []

    @pytest.mark.unit()
    def Test_Empty_String_Produces_No_Warning(self):
        from src.clients_QWIM.utils_client import _validate_numeric_range
        warnings: list[str] = []
        _validate_numeric_range(section = {"x": ""}, field_key = "x", min_val = 0, max_val = 100, client_role = "primary", warnings_list = warnings)
        assert warnings == []

    @pytest.mark.unit()
    def Test_Non_Numeric_String_Appends_Warning(self):
        from src.clients_QWIM.utils_client import _validate_numeric_range
        warnings: list[str] = []
        _validate_numeric_range(section = {"x": "abc"}, field_key = "x", min_val = 0, max_val = 100, client_role = "primary", warnings_list = warnings)
        assert len(warnings) == 1
        assert "not a valid number" in warnings[0]

    @pytest.mark.unit()
    def Test_Boolean_Value_Appends_Invalid_Number_Warning(self):
        from src.clients_QWIM.utils_client import _validate_numeric_range

        warnings: list[str] = []
        _validate_numeric_range(section = {"x": True}, field_key = "x", min_val = 0, max_val = 100, client_role = "primary", warnings_list = warnings)

        assert len(warnings) == 1
        assert "not a valid number" in warnings[0]

    @pytest.mark.unit()
    def Test_Value_In_Range_Produces_No_Warning(self):
        from src.clients_QWIM.utils_client import _validate_numeric_range
        warnings: list[str] = []
        _validate_numeric_range(section = {"x": "50"}, field_key = "x", min_val = 0, max_val = 100, client_role = "primary", warnings_list = warnings)
        assert warnings == []

    @pytest.mark.unit()
    def Test_Value_Below_Minimum_Appends_Warning(self):
        from src.clients_QWIM.utils_client import _validate_numeric_range
        warnings: list[str] = []
        _validate_numeric_range(section = {"x": "-5"}, field_key = "x", min_val = 0, max_val = 100, client_role = "primary", warnings_list = warnings)
        assert len(warnings) == 1
        assert "outside valid range" in warnings[0]

    @pytest.mark.unit()
    def Test_Value_Above_Maximum_Appends_Warning(self):
        from src.clients_QWIM.utils_client import _validate_numeric_range
        warnings: list[str] = []
        _validate_numeric_range(section = {"x": "150"}, field_key = "x", min_val = 0, max_val = 100, client_role = "primary", warnings_list = warnings)
        assert len(warnings) == 1
        assert "outside valid range" in warnings[0]

    @pytest.mark.unit()
    def Test_Missing_Key_Produces_No_Warning(self):
        from src.clients_QWIM.utils_client import _validate_numeric_range
        warnings: list[str] = []
        _validate_numeric_range(section = {}, field_key = "x", min_val = 0, max_val = 100, client_role = "primary", warnings_list = warnings)
        assert warnings == []


# ===========================================================================
# Class_Test_Is_Currency_Field_Name
# ===========================================================================


@pytest.mark.unit()
class Class_Test_Is_Currency_Field_Name:
    """Tests for _is_currency_field_name helper."""

    @pytest.mark.unit()
    def Test_Assets_Field_Is_Currency(self):
        from src.clients_QWIM.utils_client import _is_currency_field_name
        assert _is_currency_field_name(field_name = "Assets.client_primary.assets_taxable") is True

    @pytest.mark.unit()
    def Test_Income_Field_Is_Currency(self):
        from src.clients_QWIM.utils_client import _is_currency_field_name
        assert _is_currency_field_name(field_name = "Income.client_primary.income_social_security") is True

    @pytest.mark.unit()
    def Test_Goals_Field_Is_Currency(self):
        from src.clients_QWIM.utils_client import _is_currency_field_name
        assert _is_currency_field_name(field_name = "Goals.client_primary.goal_essential") is True

    @pytest.mark.unit()
    def Test_LTC_Contingency_Field_Is_Currency(self):
        from src.clients_QWIM.utils_client import _is_currency_field_name
        assert _is_currency_field_name(field_name = "LTC_Insurance.client_primary.ltc_benefit_amount") is True

    @pytest.mark.unit()
    def Test_Life_Insurance_Field_Is_Currency(self):
        from src.clients_QWIM.utils_client import _is_currency_field_name
        assert _is_currency_field_name(field_name = "Life_Insurance.client_primary.life_insurance_death_benefit") is True

    @pytest.mark.unit()
    def Test_Two_Parts_Is_Not_Currency(self):
        from src.clients_QWIM.utils_client import _is_currency_field_name
        assert _is_currency_field_name(field_name = "Header.date") is False

    @pytest.mark.unit()
    def Test_Four_Parts_Is_Not_Currency(self):
        from src.clients_QWIM.utils_client import _is_currency_field_name
        assert _is_currency_field_name(field_name = "A.B.C.D") is False

    @pytest.mark.unit()
    def Test_Unknown_Section_Is_Not_Currency(self):
        from src.clients_QWIM.utils_client import _is_currency_field_name
        assert _is_currency_field_name(field_name = "Personal_Info.client_primary.age_current") is False

    @pytest.mark.unit()
    def Test_Non_Currency_Assets_Field_Is_Not_Currency(self):
        from src.clients_QWIM.utils_client import _is_currency_field_name
        # Assets section exists but field is not in the currency set
        assert _is_currency_field_name(field_name = "Assets.client_primary.growth_rate") is False


# ===========================================================================
# Class_Test_Parse_Field_Into_Result
# ===========================================================================


@pytest.mark.unit()
class Class_Test_Parse_Field_Into_Result:
    """Tests for _parse_field_into_result helper."""

    @pytest.mark.unit()
    def Test_header_two_part_field(self):
        from src.clients_QWIM.utils_client import _parse_field_into_result
        result: dict = {"Header": {}}
        _parse_field_into_result(result = result, field_name = "Header.date", field_value = "01/01/2025")
        assert result["Header"]["date"] == "01/01/2025"

    @pytest.mark.unit()
    def Test_advisor_info_two_part_field(self):
        from src.clients_QWIM.utils_client import _parse_field_into_result
        result: dict = {"Advisor_Info": {}}
        _parse_field_into_result(result = result, field_name = "Advisor_Info.name", field_value = "John Doe")
        assert result["Advisor_Info"]["name"] == "John Doe"

    @pytest.mark.unit()
    def Test_three_part_known_section(self):
        from src.clients_QWIM.utils_client import _parse_field_into_result
        result: dict = {"Personal_Info": {"client_primary": {}, "client_partner": {}}}
        _parse_field_into_result(result = result, field_name = "Personal_Info.client_primary.age_current", field_value = "65")
        assert result["Personal_Info"]["client_primary"]["age_current"] == "65"

    @pytest.mark.unit()
    def Test_three_part_assets_section(self):
        from src.clients_QWIM.utils_client import _parse_field_into_result
        result: dict = {"Assets": {"client_primary": {}, "client_partner": {}}}
        _parse_field_into_result(result = result, field_name = "Assets.client_primary.assets_taxable", field_value = "100000")
        assert result["Assets"]["client_primary"]["assets_taxable"] == "100000"

    @pytest.mark.unit()
    def Test_three_part_unknown_client_role_not_stored(self):
        from src.clients_QWIM.utils_client import _parse_field_into_result
        result: dict = {"Personal_Info": {"client_primary": {}, "client_partner": {}}}
        _parse_field_into_result(result = result, field_name = "Personal_Info.client_unknown.age", field_value = "50")
        assert "client_unknown" not in result["Personal_Info"]

    @pytest.mark.unit()
    def Test_unknown_section_not_stored(self):
        from src.clients_QWIM.utils_client import _parse_field_into_result
        result: dict = {}
        _parse_field_into_result(result = result, field_name = "Unknown_Section.client_primary.field", field_value = "val")
        assert "Unknown_Section" not in result

    @pytest.mark.unit()
    def Test_one_part_field_not_stored(self):
        from src.clients_QWIM.utils_client import _parse_field_into_result
        result: dict = {}
        _parse_field_into_result(result = result, field_name = "singlepart", field_value = "val")
        assert result == {}

    @pytest.mark.unit()
    def Test_contingency_section_stored(self):
        from src.clients_QWIM.utils_client import _parse_field_into_result
        result: dict = {"Contingency": {"client_primary": {}, "client_partner": {}}}
        _parse_field_into_result(result = result, field_name = "Contingency.client_primary.health_status", field_value = "Good")
        assert result["Contingency"]["client_primary"]["health_status"] == "Good"

    @pytest.mark.unit()
    def Test_known_section_not_present_in_result(self):
        from src.clients_QWIM.utils_client import _parse_field_into_result
        # Section is known (Assets) but not pre-initialised in result dict
        result: dict = {}
        _parse_field_into_result(result = result, field_name = "Assets.client_primary.assets_taxable", field_value = "0")
        assert "Assets" not in result


# ===========================================================================
# Class_Test_Zip_Longest_Pairs
# ===========================================================================


@pytest.mark.unit()
class Class_Test_Zip_Longest_Pairs:
    """Tests for _zip_longest_pairs helper."""

    @pytest.mark.unit()
    def Test_equal_length_lists(self):
        from src.clients_QWIM.utils_client import _zip_longest_pairs
        result = _zip_longest_pairs(left = [1, 2], right = [3, 4])
        assert result == [(1, 3), (2, 4)]

    @pytest.mark.unit()
    def Test_left_longer(self):
        from src.clients_QWIM.utils_client import _zip_longest_pairs
        result = _zip_longest_pairs(left = [1, 2, 3], right = [4])
        assert result == [(1, 4), (2, None), (3, None)]

    @pytest.mark.unit()
    def Test_right_longer(self):
        from src.clients_QWIM.utils_client import _zip_longest_pairs
        result = _zip_longest_pairs(left = [1], right = [4, 5, 6])
        assert result == [(1, 4), (None, 5), (None, 6)]

    @pytest.mark.unit()
    def Test_both_empty(self):
        from src.clients_QWIM.utils_client import _zip_longest_pairs
        result = _zip_longest_pairs(left = [], right = [])
        assert result == []


# ===========================================================================
# Class_Test_Normalize_Trademark_Symbols
# ===========================================================================


@pytest.mark.unit()
class Class_Test_Normalize_Text_Trademark_Symbols:
    """Tests for _normalize_text_trademark_symbols helper."""

    @pytest.mark.unit()
    def Test_Registered_Mark_Is_Replaced(self):
        from src.clients_QWIM.utils_client import _normalize_text_trademark_symbols
        assert _normalize_text_trademark_symbols(value_text = "QWIM(r)") == "QWIM®"

    @pytest.mark.unit()
    def Test_Trademark_Mark_Is_Replaced(self):
        from src.clients_QWIM.utils_client import _normalize_text_trademark_symbols
        assert _normalize_text_trademark_symbols(value_text = "Brand(tm)") == "Brand™"

    @pytest.mark.unit()
    def Test_Service_Mark_Is_Replaced(self):
        from src.clients_QWIM.utils_client import _normalize_text_trademark_symbols
        assert _normalize_text_trademark_symbols(value_text = "Service(sm)") == "Service℠"

    @pytest.mark.unit()
    def Test_Text_With_No_Marks_Strips_Whitespace(self):
        from src.clients_QWIM.utils_client import _normalize_text_trademark_symbols
        assert _normalize_text_trademark_symbols(value_text = "  Hello  ") == "Hello"

    @pytest.mark.unit()
    def Test_Registered_Mark_Is_Case_Insensitive(self):
        from src.clients_QWIM.utils_client import _normalize_text_trademark_symbols
        assert _normalize_text_trademark_symbols(value_text = "QWIM(R)") == "QWIM®"


# ===========================================================================
# Class_Test_Normalize_Phone_Number_US
# ===========================================================================


@pytest.mark.unit()
class Class_Test_Normalize_Phone_Number_US:
    """Tests for _normalize_phone_number_US helper."""

    @pytest.mark.unit()
    def Test_Ten_Digit_Number_Is_Formatted(self):
        from src.clients_QWIM.utils_client import _normalize_phone_number_US
        assert _normalize_phone_number_US(value_text = "2125551234") == "212-555-1234"

    @pytest.mark.unit()
    def Test_Eleven_Digit_Number_With_Leading_One_Is_Stripped(self):
        from src.clients_QWIM.utils_client import _normalize_phone_number_US
        assert _normalize_phone_number_US(value_text = "12125551234") == "212-555-1234"

    @pytest.mark.unit()
    def Test_Formatted_Ten_Digit_Number_Remains_Normalized(self):
        from src.clients_QWIM.utils_client import _normalize_phone_number_US
        assert _normalize_phone_number_US(value_text = "(212) 555-1234") == "212-555-1234"

    @pytest.mark.unit()
    def Test_Invalid_Too_Short_Value_Returns_Stripped_Text(self):
        from src.clients_QWIM.utils_client import _normalize_phone_number_US
        result = _normalize_phone_number_US(value_text = "12345")
        assert result == "12345"

    @pytest.mark.unit()
    def Test_Eleven_Digit_Number_Without_Leading_One_Returns_Stripped_Text(self):
        from src.clients_QWIM.utils_client import _normalize_phone_number_US
        # 11 digits not starting with 1 → not stripped → len != 10 → return original stripped
        result = _normalize_phone_number_US(value_text = "22125551234")
        assert result == "22125551234"


# ===========================================================================
# Class_Test_Normalize_Extracted_Advisor_Info
# ===========================================================================


@pytest.mark.unit()
class Class_Test_Normalize_Extracted_Advisor_Info:
    """Tests for _normalize_extracted_advisor_info_section."""

    @pytest.mark.unit()
    def Test_no_advisor_info_key_returns_early(self):
        from src.clients_QWIM.utils_client import _normalize_extracted_advisor_info_section
        result = {"Header": {"date": "01/01/2025"}}
        _normalize_extracted_advisor_info_section(result = result)
        assert "Advisor_Info" not in result

    @pytest.mark.unit()
    def Test_non_dict_advisor_info_returns_early(self):
        from src.clients_QWIM.utils_client import _normalize_extracted_advisor_info_section
        result = {"Advisor_Info": "not-a-dict"}
        _normalize_extracted_advisor_info_section(result = result)
        assert result["Advisor_Info"] == "not-a-dict"

    @pytest.mark.unit()
    def Test_none_value_skipped(self):
        from src.clients_QWIM.utils_client import _normalize_extracted_advisor_info_section
        result = {"Advisor_Info": {"name": None, "email": "j@example.com"}}
        _normalize_extracted_advisor_info_section(result = result)
        assert result["Advisor_Info"]["name"] is None

    @pytest.mark.unit()
    def Test_phone_number_normalized(self):
        from src.clients_QWIM.utils_client import _normalize_extracted_advisor_info_section
        result = {"Advisor_Info": {"phone_number": "2125551234"}}
        _normalize_extracted_advisor_info_section(result = result)
        assert result["Advisor_Info"]["phone_number"] == "212-555-1234"

    @pytest.mark.unit()
    def Test_phone_number_with_country_code_normalized(self):
        from src.clients_QWIM.utils_client import _normalize_extracted_advisor_info_section
        result = {"Advisor_Info": {"phone_number": "12125551234"}}
        _normalize_extracted_advisor_info_section(result = result)
        assert result["Advisor_Info"]["phone_number"] == "212-555-1234"

    @pytest.mark.unit()
    def Test_email_stripped(self):
        from src.clients_QWIM.utils_client import _normalize_extracted_advisor_info_section
        result = {"Advisor_Info": {"email": "  jane@example.com  "}}
        _normalize_extracted_advisor_info_section(result = result)
        assert result["Advisor_Info"]["email"] == "jane@example.com"

    @pytest.mark.unit()
    def Test_other_key_trademark_normalized(self):
        from src.clients_QWIM.utils_client import _normalize_extracted_advisor_info_section
        result = {"Advisor_Info": {"name": "  QWIM(r) Wealth  "}}
        _normalize_extracted_advisor_info_section(result = result)
        assert result["Advisor_Info"]["name"] == "QWIM® Wealth"


# ===========================================================================
# Class_Test_Worksheet_Has_Client_Partner
# ===========================================================================


@pytest.mark.unit()
class Class_Test_Worksheet_Has_Client_Partner:
    """Tests for worksheet_has_client_partner."""

    @pytest.mark.unit()
    def Test_non_dict_returns_false(self):
        from src.clients_QWIM.utils_client import worksheet_has_client_partner
        assert worksheet_has_client_partner(extracted_data = "not-a-dict") is False

    @pytest.mark.unit()
    def Test_empty_partner_data_returns_false(self):
        from src.clients_QWIM.utils_client import worksheet_has_client_partner
        data = {"Personal_Info": {"client_primary": {"name": "Alice"}, "client_partner": {}}}
        assert worksheet_has_client_partner(extracted_data = data) is False

    @pytest.mark.unit()
    def Test_partner_has_string_value_returns_true(self):
        from src.clients_QWIM.utils_client import worksheet_has_client_partner
        data = {"Personal_Info": {"client_primary": {}, "client_partner": {"name": "Bob"}}}
        assert worksheet_has_client_partner(extracted_data = data) is True

    @pytest.mark.unit()
    def Test_partner_only_bool_values_returns_false(self):
        from src.clients_QWIM.utils_client import worksheet_has_client_partner
        data = {"Income": {"client_primary": {}, "client_partner": {"cola_indexed": True}}}
        assert worksheet_has_client_partner(extracted_data = data) is False

    @pytest.mark.unit()
    def Test_partner_only_none_values_returns_false(self):
        from src.clients_QWIM.utils_client import worksheet_has_client_partner
        data = {"Assets": {"client_primary": {}, "client_partner": {"assets_taxable": None}}}
        assert worksheet_has_client_partner(extracted_data = data) is False

    @pytest.mark.unit()
    def Test_partner_numeric_value_returns_true(self):
        from src.clients_QWIM.utils_client import worksheet_has_client_partner
        data = {"Assets": {"client_primary": {}, "client_partner": {"assets_taxable": 100000}}}
        assert worksheet_has_client_partner(extracted_data = data) is True

    @pytest.mark.unit()
    def Test_partner_empty_string_returns_false(self):
        from src.clients_QWIM.utils_client import worksheet_has_client_partner
        data = {"Personal_Info": {"client_primary": {}, "client_partner": {"name": ""}}}
        assert worksheet_has_client_partner(extracted_data = data) is False

    @pytest.mark.unit()
    def Test_section_not_dict_skipped(self):
        from src.clients_QWIM.utils_client import worksheet_has_client_partner
        data = {
            "Personal_Info": "not-a-dict",
            "Assets": {"client_primary": {}, "client_partner": {}},
        }
        assert worksheet_has_client_partner(extracted_data = data) is False

    @pytest.mark.unit()
    def Test_partner_not_dict_skipped(self):
        from src.clients_QWIM.utils_client import worksheet_has_client_partner
        data = {"Personal_Info": {"client_primary": {}, "client_partner": "not-a-dict"}}
        assert worksheet_has_client_partner(extracted_data = data) is False


# ===========================================================================
# Class_Test_Convert_Worksheet_Data_To_RGA
# ===========================================================================


@pytest.mark.unit()
class Class_Test_Convert_Worksheet_Data_To_RGA:
    """Tests for convert_worksheet_data_to_RGA_format."""

    def _make_single_client_data(self) -> dict:
        # Partner fields use empty strings so worksheet_has_client_partner returns False
        # and ""+""+"" arithmetic yields "" which _safe_whole_dollar_numeric → 0.0
        return {
            "Personal_Info": {
                "client_primary": {
                    "age_current": "65",
                    "age_retirement": "67",
                    "age_annuity_income_starting": "67",
                    "gender": "Male",
                    "status_marital": "Single",
                    "tolerance_risk": "Moderate",
                },
                "client_partner": {},
            },
            "Assets": {
                "client_primary": {
                    "assets_taxable": 100000,
                    "assets_tax_deferred": 200000,
                    "assets_tax_free": 50000,
                },
                "client_partner": {
                    "assets_taxable": "",
                    "assets_tax_deferred": "",
                    "assets_tax_free": "",
                },
            },
            "Goals": {
                "client_primary": {
                    "goal_essential": 40000,
                    "goal_important": 10000,
                    "goal_aspirational": 5000,
                },
                "client_partner": {
                    "goal_essential": "",
                    "goal_important": "",
                    "goal_aspirational": "",
                },
            },
            "Income": {
                "client_primary": {
                    "income_social_security": 20000,
                    "income_pension": 0,
                    "income_annuity_existing": 0,
                    "income_other": 5000,
                },
                "client_partner": {
                    "income_social_security": "",
                    "income_pension": "",
                    "income_annuity_existing": "",
                    "income_other": "",
                },
            },
        }

    @pytest.mark.unit()
    def Test_non_dict_raises_exception(self):
        from src.clients_QWIM.utils_client import convert_worksheet_data_to_RGA_format
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )
        with pytest.raises(Exception_Validation_Input):
            convert_worksheet_data_to_RGA_format(extracted_data = "not-a-dict")

    @pytest.mark.unit()
    def Test_missing_pi_primary_raises(self):
        from src.clients_QWIM.utils_client import convert_worksheet_data_to_RGA_format
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )
        with pytest.raises(Exception_Validation_Input):
            convert_worksheet_data_to_RGA_format(extracted_data = {"Personal_Info": {"client_primary": {}}})

    @pytest.mark.unit()
    def Test_single_male_client(self):
        from src.clients_QWIM.utils_client import convert_worksheet_data_to_RGA_format
        data = self._make_single_client_data()
        result = convert_worksheet_data_to_RGA_format(extracted_data = data)
        assert result["client_group"] == "Male"
        assert result["age_primary"] == 65
        assert result["retirement_age"] == 67
        assert result["income_start_age"] == 67
        assert result["initial_wealth"] == pytest.approx(350000.0)
        assert result["goals"]["essential"] == pytest.approx(40000.0)
        assert result["income_total"] == pytest.approx(25000.0)

    @pytest.mark.unit()
    def Test_boolean_asset_field_uses_existing_default_path(self):
        from src.clients_QWIM.utils_client import convert_worksheet_data_to_RGA_format

        data = self._make_single_client_data()
        data["Assets"]["client_primary"]["assets_tax_deferred"] = True

        result = convert_worksheet_data_to_RGA_format(extracted_data = data)

        assert result["initial_wealth"] == pytest.approx(150000.0)

    @pytest.mark.unit()
    def Test_single_female_client(self):
        from src.clients_QWIM.utils_client import convert_worksheet_data_to_RGA_format
        data = self._make_single_client_data()
        data["Personal_Info"]["client_primary"]["gender"] = "Female"
        result = convert_worksheet_data_to_RGA_format(extracted_data = data)
        assert result["client_group"] == "Female"

    @pytest.mark.unit()
    def Test_couple_joint_group(self):
        from src.clients_QWIM.utils_client import convert_worksheet_data_to_RGA_format
        data = self._make_single_client_data()
        data["Personal_Info"]["client_partner"]["name"] = "Partner"
        result = convert_worksheet_data_to_RGA_format(extracted_data = data)
        assert result["client_group"] == "Joint"

    @pytest.mark.unit()
    def Test_income_secured_and_unsecured_split(self):
        from src.clients_QWIM.utils_client import convert_worksheet_data_to_RGA_format
        data = self._make_single_client_data()
        result = convert_worksheet_data_to_RGA_format(extracted_data = data)
        assert result["income_secured_total"] == pytest.approx(20000.0)
        assert result["income_unsecured_total"] == pytest.approx(5000.0)

    @pytest.mark.unit()
    def Test_social_security_in_secured_total(self):
        from src.clients_QWIM.utils_client import convert_worksheet_data_to_RGA_format
        data = self._make_single_client_data()
        data["Income"]["client_primary"]["income_pension"] = 10000
        result = convert_worksheet_data_to_RGA_format(extracted_data = data)
        assert result["income_secured_total"] == pytest.approx(30000.0)


# ===========================================================================
# Class_Test_Validate_Advisor_Info_Extra_Branches
# ===========================================================================


@pytest.mark.unit()
class Class_Test_Validate_Advisor_Info_Extra_Branches:
    """Extra branch coverage for validate_required_advisor_info_section."""

    def _base_advisor_info(self) -> dict:
        return {
            "name": "Jane Advisor",
            "title": "CFP",
            "credentials": "CFP",
            "team": "Team One",
            "email": "jane@example.com",
            "phone_number": "2125551234",
            "address": "1 Main St, NY",
        }

    @pytest.mark.unit()
    def Test_invalid_email_format_reported(self):
        from src.clients_QWIM.utils_client import validate_required_advisor_info_section
        info = self._base_advisor_info()
        info["email"] = "not-an-email"
        messages = validate_required_advisor_info_section(extracted_data = {"Advisor_Info": info})
        assert any("Email" in m and "invalid" in m for m in messages)

    @pytest.mark.unit()
    def Test_phone_eleven_digits_with_country_code_valid(self):
        from src.clients_QWIM.utils_client import validate_required_advisor_info_section
        info = self._base_advisor_info()
        info["phone_number"] = "12125551234"  # 11 digits starting with 1 → valid
        messages = validate_required_advisor_info_section(extracted_data = {"Advisor_Info": info})
        phone_messages = [m for m in messages if "Phone" in m]
        assert phone_messages == []

    @pytest.mark.unit()
    def Test_phone_too_short_reported(self):
        from src.clients_QWIM.utils_client import validate_required_advisor_info_section
        info = self._base_advisor_info()
        info["phone_number"] = "12345"  # too short
        messages = validate_required_advisor_info_section(extracted_data = {"Advisor_Info": info})
        assert any("Phone" in m and "invalid" in m for m in messages)


# ===========================================================================
# Class_Test_Validate_Extracted_Data_Extra
# ===========================================================================


@pytest.mark.unit()
class Class_Test_Validate_Extracted_Data_Extra:
    """Extra branch coverage for validate_extracted_client_data."""

    @pytest.mark.unit()
    def Test_negative_asset_value_reported(self):
        from src.clients_QWIM.utils_client import validate_extracted_client_data
        extracted = {
            "Personal_Info": {"client_primary": {"status_marital": "Single"}},
            "Assets": {"client_primary": {"assets_taxable": "-500"}},
        }
        is_valid, warnings = validate_extracted_client_data(extracted_data = extracted)
        assert not is_valid
        assert any("negative" in w for w in warnings)

    @pytest.mark.unit()
    def Test_null_asset_value_skipped_no_warning(self):
        from src.clients_QWIM.utils_client import validate_extracted_client_data
        extracted = {
            "Personal_Info": {"client_primary": {}},
            "Assets": {"client_primary": {"assets_taxable": None}},
        }
        is_valid, warnings = validate_extracted_client_data(extracted_data = extracted)
        assert is_valid


# ===========================================================================
# Class_Test_Default_Output_Dir
# ===========================================================================


@pytest.mark.unit()
class Class_Test_Default_Output_Dir:
    """Tests for _default_output_dir helper."""

    @pytest.mark.unit()
    def Test_returns_path_instance(self):
        from pathlib import Path
        from src.clients_QWIM.utils_client import _default_output_dir
        result = _default_output_dir()
        assert isinstance(result, Path)

    @pytest.mark.unit()
    def Test_path_ends_with_inputs_qwim(self):
        from src.clients_QWIM.utils_client import _default_output_dir
        result = _default_output_dir()
        assert result.name == "QWIM"
        assert result.parent.name == "inputs"

    @pytest.mark.unit()
    def Test_directory_exists_after_call(self):
        from src.clients_QWIM.utils_client import _default_output_dir
        result = _default_output_dir()
        assert result.is_dir()


# ===========================================================================
# Class_Test_Generate_Worksheet_PDFs
# ===========================================================================


@pytest.mark.unit()
class Class_Test_Generate_Worksheet_PDFs:
    """Tests for PDF generation public API functions."""

    @pytest.mark.unit()
    def Test_single_worksheet_generates_file(self, tmp_path):
        from src.clients_QWIM.utils_client import generate_worksheet_PDF_single
        output = tmp_path / "single.pdf"
        result = generate_worksheet_PDF_single(output_path=output)
        assert result.is_file()
        assert result.suffix == ".pdf"

    @pytest.mark.unit()
    def Test_couple_worksheet_generates_file(self, tmp_path):
        from src.clients_QWIM.utils_client import generate_worksheet_PDF_couple
        output = tmp_path / "couple.pdf"
        result = generate_worksheet_PDF_couple(output_path=output)
        assert result.is_file()

    @pytest.mark.unit()
    def Test_inputs_worksheet_generates_file(self, tmp_path):
        from src.clients_QWIM.utils_client import generate_inputs_worksheet_PDF
        output = tmp_path / "inputs.pdf"
        result = generate_inputs_worksheet_PDF(output_path=output)
        assert result.is_file()

    @pytest.mark.unit()
    def Test_single_with_none_output_path(self, monkeypatch, tmp_path):
        import src.clients_QWIM.utils_client as mod
        from src.clients_QWIM.utils_client import generate_worksheet_PDF_single
        monkeypatch.setattr(mod, "_default_output_dir", lambda: tmp_path)
        result = generate_worksheet_PDF_single(output_path=None)
        assert result.is_file()

    @pytest.mark.unit()
    def Test_couple_with_none_output_path(self, monkeypatch, tmp_path):
        import src.clients_QWIM.utils_client as mod
        from src.clients_QWIM.utils_client import generate_worksheet_PDF_couple
        monkeypatch.setattr(mod, "_default_output_dir", lambda: tmp_path)
        result = generate_worksheet_PDF_couple(output_path=None)
        assert result.is_file()

    @pytest.mark.unit()
    def Test_inputs_with_none_output_path(self, monkeypatch, tmp_path):
        import src.clients_QWIM.utils_client as mod
        from src.clients_QWIM.utils_client import generate_inputs_worksheet_PDF
        monkeypatch.setattr(mod, "_default_output_dir", lambda: tmp_path)
        result = generate_inputs_worksheet_PDF(output_path=None)
        assert result.is_file()


# ===========================================================================
# Class_Test_Extract_Client_Data_PDF
# ===========================================================================


@pytest.mark.unit()
class Class_Test_Extract_Client_Data_PDF:
    """Tests for extract_client_data_from_worksheet_PDF."""

    @pytest.mark.unit()
    def Test_nonexistent_path_raises(self):
        from pathlib import Path
        from src.clients_QWIM.utils_client import extract_client_data_from_worksheet_PDF
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )
        with pytest.raises(Exception_Validation_Input):
            extract_client_data_from_worksheet_PDF(pdf_path = Path("/nonexistent/path.pdf"))

    @pytest.mark.unit()
    def Test_string_path_converted_and_raises_when_missing(self):
        from src.clients_QWIM.utils_client import extract_client_data_from_worksheet_PDF
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )
        with pytest.raises(Exception_Validation_Input):
            extract_client_data_from_worksheet_PDF(pdf_path = "/nonexistent/file.pdf")

    @pytest.mark.unit()
    def Test_real_generated_pdf_returns_dict(self, tmp_path):
        from src.clients_QWIM.utils_client import (
            extract_client_data_from_worksheet_PDF,
            generate_worksheet_PDF_single,
        )
        pdf_path = generate_worksheet_PDF_single(output_path=tmp_path / "test.pdf")
        result = extract_client_data_from_worksheet_PDF(pdf_path = pdf_path)
        assert isinstance(result, dict)
        assert "Header" in result
        assert "Advisor_Info" in result
        assert "Personal_Info" in result

    @pytest.mark.unit()
    def Test_inputs_worksheet_pdf_extraction(self, tmp_path):
        from src.clients_QWIM.utils_client import (
            extract_client_data_from_worksheet_PDF,
            generate_inputs_worksheet_PDF,
        )
        pdf_path = generate_inputs_worksheet_PDF(output_path=tmp_path / "inputs.pdf")
        result = extract_client_data_from_worksheet_PDF(pdf_path = pdf_path)
        assert isinstance(result, dict)
        assert "Advisor_Info" in result


# ===========================================================================
# Class_Test_Draw_Functions_With_Mock_Canvas
# ===========================================================================


@pytest.mark.unit()
class Class_Test_Draw_Functions_With_Mock_Canvas:
    """Tests for internal PDF drawing functions using a mock canvas."""

    @pytest.mark.unit()
    def Test_draw_title_returns_float(self):
        from unittest.mock import MagicMock
        from src.clients_QWIM.utils_client import _draw_title
        c = MagicMock()
        result = _draw_title(c = c, y = 700.0)
        assert isinstance(result, float)
        assert result < 700.0

    @pytest.mark.unit()
    def Test_draw_description_returns_float(self):
        from unittest.mock import MagicMock
        from src.clients_QWIM.utils_client import _draw_description
        c = MagicMock()
        result = _draw_description(c = c, y = 680.0)
        assert isinstance(result, float)

    @pytest.mark.unit()
    def Test_draw_header_fields_single(self):
        from unittest.mock import MagicMock
        from src.clients_QWIM.utils_client import _draw_header_fields
        c = MagicMock()
        result = _draw_header_fields(c = c, y = 660.0, is_couple=False)
        assert isinstance(result, float)

    @pytest.mark.unit()
    def Test_draw_header_fields_couple(self):
        from unittest.mock import MagicMock
        from src.clients_QWIM.utils_client import _draw_header_fields
        c = MagicMock()
        result = _draw_header_fields(c = c, y = 660.0, is_couple=True)
        assert isinstance(result, float)

    @pytest.mark.unit()
    def Test_draw_advisor_info_section(self):
        from unittest.mock import MagicMock
        from src.clients_QWIM.utils_client import _draw_advisor_info_section
        c = MagicMock()
        result = _draw_advisor_info_section(c = c, y = 640.0)
        assert isinstance(result, float)

    @pytest.mark.unit()
    def Test_draw_section_single_client(self):
        from unittest.mock import MagicMock
        from src.clients_QWIM.utils_client import _draw_section, _PERSONAL_INFO_ROWS
        c = MagicMock()
        result = _draw_section(
            c = c, y = 600.0, title = "Personal Information", rows = _PERSONAL_INFO_ROWS,
            section_dict_key = "Personal_Info", is_couple=False,
        )
        assert isinstance(result, float)

    @pytest.mark.unit()
    def Test_draw_section_couple(self):
        from unittest.mock import MagicMock
        from src.clients_QWIM.utils_client import _draw_section, _INCOME_ROWS
        c = MagicMock()
        result = _draw_section(
            c = c, y = 600.0, title = "Income", rows = _INCOME_ROWS,
            section_dict_key = "Income", is_couple=True,
        )
        assert isinstance(result, float)

    @pytest.mark.unit()
    def Test_draw_section_with_checkbox_row(self):
        from unittest.mock import MagicMock
        from src.clients_QWIM.utils_client import _draw_section, _GOALS_ROWS
        c = MagicMock()
        result = _draw_section(
            c = c, y = 600.0, title = "Goals (Annual Expenses)", rows = _GOALS_ROWS,
            section_dict_key = "Goals", is_couple=True,
        )
        assert isinstance(result, float)


# ===========================================================================
# Class_Test_WS_Draw_Functions_With_Mock_Canvas
# ===========================================================================


@pytest.mark.unit()
class Class_Test_WS_Draw_Functions_With_Mock_Canvas:
    """Tests for new worksheet draw functions using a mock canvas."""

    @pytest.mark.unit()
    def Test_ws_draw_page1(self):
        from unittest.mock import MagicMock
        from src.clients_QWIM.utils_client import _ws_draw_page1
        c = MagicMock()
        c.stringWidth.return_value = 300.0
        _ws_draw_page1(c = c)  # Should not raise

    @pytest.mark.unit()
    def Test_ws_draw_advisor_info_section(self):
        from unittest.mock import MagicMock
        from src.clients_QWIM.utils_client import _ws_draw_advisor_info_section
        c = MagicMock()
        result = _ws_draw_advisor_info_section(c = c, y = 700.0)
        assert isinstance(result, float)

    @pytest.mark.unit()
    def Test_ws_draw_page2(self):
        from unittest.mock import MagicMock
        from src.clients_QWIM.utils_client import _ws_draw_page2
        c = MagicMock()
        _ws_draw_page2(c = c)  # Should not raise

    @pytest.mark.unit()
    def Test_ws_draw_page3(self):
        from unittest.mock import MagicMock
        from src.clients_QWIM.utils_client import _ws_draw_page3
        c = MagicMock()
        c.stringWidth.return_value = 300.0
        _ws_draw_page3(c = c)  # Should not raise

    @pytest.mark.unit()
    def Test_ws_draw_3col_table_text_fields(self):
        from unittest.mock import MagicMock
        from src.clients_QWIM.utils_client import _ws_draw_3col_table, _WS_ASSETS_ROWS
        c = MagicMock()
        result = _ws_draw_3col_table(
            c = c, y = 700.0, title = "Assets", rows = _WS_ASSETS_ROWS, section_dict_key = "Assets",
            col_label_w=220.0, col_val_w=130.0,
            x_label=50.0, x_primary=270.0, x_partner=400.0,
        )
        assert isinstance(result, float)

    @pytest.mark.unit()
    def Test_ws_draw_3col_table_checkbox_and_indent_rows(self):
        from unittest.mock import MagicMock
        from src.clients_QWIM.utils_client import _ws_draw_3col_table, _WS_LTC_ROWS
        c = MagicMock()
        result = _ws_draw_3col_table(
            c = c, y = 700.0, title = "LTC Insurance", rows = _WS_LTC_ROWS, section_dict_key = "LTC_Insurance",
            col_label_w=220.0, col_val_w=130.0,
            x_label=50.0, x_primary=270.0, x_partner=400.0,
        )
        assert isinstance(result, float)


# ===========================================================================
# Class_Test_Apply_Currency_Field_Formatting
# ===========================================================================


@pytest.mark.unit()
class Class_Test_Apply_Currency_Field_Formatting:
    """Tests for _apply_currency_field_formatting."""

    @pytest.mark.unit()
    def Test_nonexistent_file_returns_early(self, tmp_path):
        from src.clients_QWIM.utils_client import _apply_currency_field_formatting
        # Should return without error for non-existent file
        _apply_currency_field_formatting(output_path = tmp_path / "missing.pdf")

    @pytest.mark.unit()
    def Test_non_path_input_converted(self, tmp_path):
        from src.clients_QWIM.utils_client import _apply_currency_field_formatting
        # String path to non-existent file should not raise
        _apply_currency_field_formatting(output_path = str(tmp_path / "missing.pdf"))

    @pytest.mark.unit()
    def Test_with_real_pdf_no_error(self, tmp_path):
        from src.clients_QWIM.utils_client import (
            _apply_currency_field_formatting,
            generate_worksheet_PDF_single,
        )
        pdf_path = generate_worksheet_PDF_single(output_path=tmp_path / "test.pdf")
        # Should not raise; currency scripts already applied during generation
        _apply_currency_field_formatting(output_path = pdf_path)

    @pytest.mark.unit()
    def Test_modified_true_calls_save_incr(self, tmp_path):
        """Cover the `if modified: doc.saveIncr()` True branch via mocking."""
        from unittest.mock import MagicMock, patch

        from src.clients_QWIM.utils_client import _apply_currency_field_formatting

        pdf_path = tmp_path / "mock.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n")  # file must exist for is_file() check

        mock_widget = MagicMock()
        mock_widget.field_name = "Assets.client_primary.assets_taxable"
        mock_widget.field_type = 7

        mock_page = MagicMock()
        mock_page.widgets.return_value = [mock_widget]

        mock_doc = MagicMock()
        mock_doc.__iter__.return_value = iter([mock_page])

        with patch("src.clients_QWIM.utils_client.fitz.open", return_value=mock_doc):
            _apply_currency_field_formatting(output_path = pdf_path)

        mock_doc.saveIncr.assert_called_once()
        mock_doc.close.assert_called_once()

    @pytest.mark.unit()
    def Test_no_currency_fields_no_save_incr(self, tmp_path):
        """Cover the `if modified:` False branch — no currency fields found."""
        from unittest.mock import MagicMock, patch

        from src.clients_QWIM.utils_client import _apply_currency_field_formatting

        pdf_path = tmp_path / "mock2.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n")

        # Non-currency field (2-part name, so _is_currency_field_name returns False)
        mock_widget = MagicMock()
        mock_widget.field_name = "Header.date"

        mock_page = MagicMock()
        mock_page.widgets.return_value = [mock_widget]

        mock_doc = MagicMock()
        mock_doc.__iter__.return_value = iter([mock_page])

        with patch("src.clients_QWIM.utils_client.fitz.open", return_value=mock_doc):
            _apply_currency_field_formatting(output_path = pdf_path)

        mock_doc.saveIncr.assert_not_called()
        mock_doc.close.assert_called_once()

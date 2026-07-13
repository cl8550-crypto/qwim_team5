"""Unit tests for worksheet-to-input mapping helpers.

Test file location: tests/tests_unit/dashboard/shiny_utils/test_unit_utils_tab_clients_populate.py
Mirrors source:    src/dashboard/shiny_utils/_utils_tab_clients_populate.py

Notes
-----
All tests are deterministic and Shiny-free.  The mappers return plain
``dict`` values, so no reactive runtime is needed.
"""

from __future__ import annotations

from typing import Any

import pytest

from src.dashboard.shiny_utils._utils_tab_clients_populate import (
    _ID_INCLUDE_PARTNER,
    _coerce_int_or_zero,
    _coerce_numeric_or_none,
    _format_currency,
    _normalize_select_value,
    build_state_name_to_postal_code_map,
    map_advisor_info_worksheet_to_inputs,
    map_assets_worksheet_to_inputs,
    map_goals_worksheet_to_inputs,
    map_income_worksheet_to_inputs,
    map_personal_info_worksheet_to_inputs,
)


# ---------------------------------------------------------------------------
# State reverse-map
# ---------------------------------------------------------------------------


class Class_Test_Build_State_Name_To_Postal_Code_Map:
    """Tests for ``build_state_name_to_postal_code_map``."""

    @pytest.mark.unit
    def Test_Returns_Texas_As_TX(self) -> None:
        """Full state name 'Texas' maps to 'TX'."""
        result = build_state_name_to_postal_code_map()
        assert result["Texas"] == "TX"

    @pytest.mark.unit
    def Test_Returns_New_York_As_NY(self) -> None:
        """Full state name 'New York' maps to 'NY'."""
        result = build_state_name_to_postal_code_map()
        assert result["New York"] == "NY"

    @pytest.mark.unit
    def Test_Returns_Arizona_As_AZ(self) -> None:
        """Full state name 'Arizona' maps to 'AZ' (not 'AR')."""
        result = build_state_name_to_postal_code_map()
        assert result["Arizona"] == "AZ"

    @pytest.mark.unit
    def Test_Returns_Missouri_As_MO(self) -> None:
        """Full state name 'Missouri' maps to 'MO' (not 'MI')."""
        result = build_state_name_to_postal_code_map()
        assert result["Missouri"] == "MO"

    @pytest.mark.unit
    def Test_Idempotent_For_Already_Two_Letter(self) -> None:
        """Already-2-letter codes pass through unchanged."""
        result = build_state_name_to_postal_code_map()
        assert result["TX"] == "TX"
        assert result["CA"] == "CA"
        assert result["FL"] == "FL"

    @pytest.mark.unit
    def Test_All_Fifty_States_Present(self) -> None:
        """All 50 US states have a reverse mapping."""
        result = build_state_name_to_postal_code_map()
        # 50 states = 50 full names + 50 self-mappings = 100
        assert len(result) >= 100


# ---------------------------------------------------------------------------
# Select normalization
# ---------------------------------------------------------------------------


class Class_Test_Normalize_Select_Value:
    """Tests for ``_normalize_select_value``."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("raw_label", "field_key", "expected"),
        [
            ("Texas", "state", "TX"),
            ("New York", "state", "NY"),
            ("Arizona", "state", "AZ"),
            ("Missouri", "state", "MO"),
            ("California", "state", "CA"),
            ("Florida", "state", "FL"),
            ("Married", "status_marital", "married"),
            ("Single", "status_marital", "single"),
            ("Male", "gender", "male"),
            ("Female", "gender", "female"),
            ("Conservative", "tolerance_risk", "conservative"),
            ("Moderate Conservative", "tolerance_risk", "moderate_conservative"),
            ("Moderate", "tolerance_risk", "moderate"),
            ("Aggressive", "tolerance_risk", "aggressive"),
        ],
        ids=[
            "state_TX", "state_NY", "state_AZ", "state_MO", "state_CA", "state_FL",
            "marital_married", "marital_single",
            "gender_male", "gender_female",
            "risk_conservative", "risk_moderate_conservative", "risk_moderate", "risk_aggressive",
        ],
    )
    def Test_Normalizes_Correctly(
        self,
        raw_label: str,
        field_key: str,
        expected: str,
    ) -> None:
        """Select labels normalize to the expected choice key."""
        result = _normalize_select_value(raw_label = raw_label, field_key = field_key)
        assert result == expected

    @pytest.mark.unit
    def Test_Returns_None_For_Empty_Label(self) -> None:
        """Empty label returns None."""
        assert _normalize_select_value(raw_label = "", field_key = "state") is None

    @pytest.mark.unit
    def Test_Returns_None_For_Unknown_State(self) -> None:
        """Unknown state name returns None."""
        assert _normalize_select_value(raw_label = "Atlantis", field_key = "state") is None


# ---------------------------------------------------------------------------
# Currency formatting
# ---------------------------------------------------------------------------


class Class_Test_Format_Currency:
    """Tests for ``_format_currency``."""

    @pytest.mark.unit
    def Test_Formats_Thousands(self) -> None:
        """Integer 100000 formats as '$100,000'."""
        assert _format_currency(amount = 100000) == "$100,000"

    @pytest.mark.unit
    def Test_Formats_Zero(self) -> None:
        """Zero formats as '$0'."""
        assert _format_currency(amount = 0) == "$0"

    @pytest.mark.unit
    def Test_Formats_Millions(self) -> None:
        """Large integer formats with commas."""
        assert _format_currency(amount = 5_000_000) == "$5,000,000"


# ---------------------------------------------------------------------------
# Coercion helpers
# ---------------------------------------------------------------------------


class Class_Test_Coerce_Int_Or_Zero:
    """Tests for ``_coerce_int_or_zero``."""

    @pytest.mark.unit
    def Test_Int_Passes_Through(self) -> None:
        """Integer passes through unchanged."""
        assert _coerce_int_or_zero(raw_value = 42) == 42

    @pytest.mark.unit
    def Test_String_Number_Coerces(self) -> None:
        """String '100' coerces to 100."""
        assert _coerce_int_or_zero(raw_value = "100") == 100

    @pytest.mark.unit
    def Test_Currency_String_Coerces(self) -> None:
        """Currency string '$100,000' coerces to 100000."""
        assert _coerce_int_or_zero(raw_value = "$100,000") == 100000

    @pytest.mark.unit
    def Test_None_Returns_Zero(self) -> None:
        """None returns 0."""
        assert _coerce_int_or_zero(raw_value = None) == 0

    @pytest.mark.unit
    def Test_Bool_Returns_Zero(self) -> None:
        """Boolean returns 0."""
        assert _coerce_int_or_zero(raw_value = True) == 0

    @pytest.mark.unit
    def Test_Empty_String_Returns_Zero(self) -> None:
        """Empty string returns 0."""
        assert _coerce_int_or_zero(raw_value = "") == 0

    @pytest.mark.unit
    def Test_Invalid_String_Returns_Zero(self) -> None:
        """Non-numeric string returns 0."""
        assert _coerce_int_or_zero(raw_value = "abc") == 0


class Class_Test_Coerce_Numeric_Or_None:
    """Tests for ``_coerce_numeric_or_none``."""

    @pytest.mark.unit
    def Test_Int_Passes_Through(self) -> None:
        """Integer passes through unchanged."""
        assert _coerce_numeric_or_none(raw_value = 42) == 42

    @pytest.mark.unit
    def Test_None_Returns_None(self) -> None:
        """None returns None."""
        assert _coerce_numeric_or_none(raw_value = None) is None

    @pytest.mark.unit
    def Test_Empty_String_Returns_None(self) -> None:
        """Empty string returns None."""
        assert _coerce_numeric_or_none(raw_value = "") is None

    @pytest.mark.unit
    def Test_Bool_Returns_None(self) -> None:
        """Boolean returns None."""
        assert _coerce_numeric_or_none(raw_value = False) is None

    @pytest.mark.unit
    def Test_String_Number_Coerces(self) -> None:
        """String '65' coerces to 65."""
        assert _coerce_numeric_or_none(raw_value = "65") == 65


# ---------------------------------------------------------------------------
# Personal Info mapper
# ---------------------------------------------------------------------------


class Class_Test_Map_Personal_Info_Worksheet_To_Inputs:
    """Tests for ``map_personal_info_worksheet_to_inputs``."""

    @pytest.mark.unit
    def Test_Maps_All_Fields_For_Primary(self) -> None:
        """All 9 fields + include_partner (only for partner) are present."""
        section = {
            "client_primary": {
                "name": "John Doe",
                "age_current": "45",
                "age_retirement": "65",
                "age_annuity_income_starting": "70",
                "code_zip": "10001",
                "status_marital": "Married",
                "gender": "Male",
                "tolerance_risk": "Moderate",
                "state": "New York",
            },
        }
        result = map_personal_info_worksheet_to_inputs(
            section = section,
            client_role = "client_primary",
        )
        # 9 fields for primary (no include_partner for primary)
        assert len(result) == 9
        assert result["input_ID_tab_clients_subtab_clients_personal_info_client_primary_name"] == "John Doe"
        assert result["input_ID_tab_clients_subtab_clients_personal_info_client_primary_age_current"] == 45
        assert result["input_ID_tab_clients_subtab_clients_personal_info_client_primary_age_retirement"] == 65
        # age_annuity_income_starting → age_income_starting widget suffix
        assert result["input_ID_tab_clients_subtab_clients_personal_info_client_primary_age_income_starting"] == 70
        assert result["input_ID_tab_clients_subtab_clients_personal_info_client_primary_code_zip"] == 10001
        assert result["input_ID_tab_clients_subtab_clients_personal_info_client_primary_state"] == "NY"
        assert result["input_ID_tab_clients_subtab_clients_personal_info_client_primary_status_marital"] == "married"

    @pytest.mark.unit
    def Test_Age_Annuity_Income_Starting_Maps_To_Age_Income_Starting(self) -> None:
        """The worksheet key 'age_annuity_income_starting' maps to widget suffix 'age_income_starting'."""
        section = {
            "client_primary": {"age_annuity_income_starting": "70"},
        }
        result = map_personal_info_worksheet_to_inputs(
            section = section,
            client_role = "client_primary",
        )
        assert result["input_ID_tab_clients_subtab_clients_personal_info_client_primary_age_income_starting"] == 70

    @pytest.mark.unit
    def Test_Blanks_Missing_Fields(self) -> None:
        """Missing fields receive blank values."""
        section: dict[str, dict[str, str]] = {"client_primary": {}}
        result = map_personal_info_worksheet_to_inputs(
            section = section,
            client_role = "client_primary",
        )
        assert result["input_ID_tab_clients_subtab_clients_personal_info_client_primary_name"] == ""
        assert result["input_ID_tab_clients_subtab_clients_personal_info_client_primary_age_current"] is None
        assert result["input_ID_tab_clients_subtab_clients_personal_info_client_primary_age_retirement"] is None

    @pytest.mark.unit
    def Test_Partner_Includes_Checkbox_When_Name_Present(self) -> None:
        """Partner with a name sets include_partner checkbox True."""
        section = {
            "client_partner": {"name": "Jane Doe"},
        }
        result = map_personal_info_worksheet_to_inputs(
            section = section,
            client_role = "client_partner",
        )
        assert result[_ID_INCLUDE_PARTNER] is True

    @pytest.mark.unit
    def Test_Partner_Checkbox_False_When_Name_Empty(self) -> None:
        """Partner with empty name sets include_partner checkbox False."""
        section = {
            "client_partner": {"name": ""},
        }
        result = map_personal_info_worksheet_to_inputs(
            section = section,
            client_role = "client_partner",
        )
        assert result[_ID_INCLUDE_PARTNER] is False

    @pytest.mark.unit
    def Test_State_Regression_Arizona_Not_Arkansas(self) -> None:
        """Arizona maps to AZ, not AR."""
        section = {
            "client_primary": {"state": "Arizona"},
        }
        result = map_personal_info_worksheet_to_inputs(
            section = section,
            client_role = "client_primary",
        )
        assert result["input_ID_tab_clients_subtab_clients_personal_info_client_primary_state"] == "AZ"

    @pytest.mark.unit
    def Test_State_Regression_Missouri_Not_Michigan(self) -> None:
        """Missouri maps to MO, not MI."""
        section = {
            "client_primary": {"state": "Missouri"},
        }
        result = map_personal_info_worksheet_to_inputs(
            section = section,
            client_role = "client_primary",
        )
        assert result["input_ID_tab_clients_subtab_clients_personal_info_client_primary_state"] == "MO"


# ---------------------------------------------------------------------------
# Assets mapper
# ---------------------------------------------------------------------------


class Class_Test_Map_Assets_Worksheet_To_Inputs:
    """Tests for ``map_assets_worksheet_to_inputs``."""

    @pytest.mark.unit
    def Test_Maps_All_Three_Fields(self) -> None:
        """All 3 asset fields are present with formatted values."""
        section = {
            "client_primary": {
                "assets_taxable": "500000",
                "assets_tax_deferred": "200000",
                "assets_tax_free": "50000",
            },
        }
        result = map_assets_worksheet_to_inputs(
            section = section,
            client_role = "client_primary",
        )
        assert len(result) == 3
        assert result["input_ID_tab_clients_subtab_clients_assets_client_primary_assets_taxable"] == "$500,000"
        assert result["input_ID_tab_clients_subtab_clients_assets_client_primary_assets_tax_deferred"] == "$200,000"
        assert result["input_ID_tab_clients_subtab_clients_assets_client_primary_assets_tax_free"] == "$50,000"

    @pytest.mark.unit
    def Test_Blanks_Missing_Fields_As_Zero(self) -> None:
        """Missing asset fields format as '$0'."""
        section: dict[str, dict[str, str]] = {"client_primary": {}}
        result = map_assets_worksheet_to_inputs(
            section = section,
            client_role = "client_primary",
        )
        assert result["input_ID_tab_clients_subtab_clients_assets_client_primary_assets_taxable"] == "$0"


# ---------------------------------------------------------------------------
# Goals mapper
# ---------------------------------------------------------------------------


class Class_Test_Map_Goals_Worksheet_To_Inputs:
    """Tests for ``map_goals_worksheet_to_inputs``."""

    @pytest.mark.unit
    def Test_Maps_All_Three_Fields(self) -> None:
        """All 3 goal fields are present with formatted values."""
        section = {
            "client_primary": {
                "goal_essential": "60000",
                "goal_important": "30000",
                "goal_aspirational": "20000",
            },
        }
        result = map_goals_worksheet_to_inputs(
            section = section,
            client_role = "client_primary",
        )
        assert len(result) == 3
        assert result["input_ID_tab_clients_subtab_clients_goals_client_primary_goal_essential"] == "$60,000"

    @pytest.mark.unit
    def Test_Blanks_Missing_Fields_As_Zero(self) -> None:
        """Missing goal fields format as '$0'."""
        section: dict[str, dict[str, str]] = {"client_primary": {}}
        result = map_goals_worksheet_to_inputs(
            section = section,
            client_role = "client_primary",
        )
        assert result["input_ID_tab_clients_subtab_clients_goals_client_primary_goal_essential"] == "$0"


# ---------------------------------------------------------------------------
# Income mapper
# ---------------------------------------------------------------------------


class Class_Test_Map_Income_Worksheet_To_Inputs:
    """Tests for ``map_income_worksheet_to_inputs``."""

    @pytest.mark.unit
    def Test_Maps_All_Four_Fields(self) -> None:
        """All 4 income fields are present with formatted values."""
        section = {
            "client_primary": {
                "income_social_security": "24000",
                "income_pension": "12000",
                "income_annuity_existing": "0",
                "income_other": "5000",
            },
        }
        result = map_income_worksheet_to_inputs(
            section = section,
            client_role = "client_primary",
        )
        assert len(result) == 4
        assert result["input_ID_tab_clients_subtab_clients_income_client_primary_income_social_security"] == "$24,000"

    @pytest.mark.unit
    def Test_Blanks_Missing_Fields_As_Zero(self) -> None:
        """Missing income fields format as '$0'."""
        section: dict[str, dict[str, str]] = {"client_primary": {}}
        result = map_income_worksheet_to_inputs(
            section = section,
            client_role = "client_primary",
        )
        assert result["input_ID_tab_clients_subtab_clients_income_client_primary_income_social_security"] == "$0"


# ---------------------------------------------------------------------------
# Advisor mapper
# ---------------------------------------------------------------------------


class Class_Test_Map_Advisor_Info_Worksheet_To_Inputs:
    """Tests for ``map_advisor_info_worksheet_to_inputs``."""

    @pytest.mark.unit
    def Test_Maps_All_Eight_Fields(self) -> None:
        """All 8 advisor fields are present."""
        advisor = {
            "name": "John Advisor",
            "title": "Financial Advisor",
            "credentials": "CFP",
            "team": "Alpha Team",
            "firm": "QWIM AI Wealth Management",
            "email": "john@example.com",
            "phone_number": "212-555-1234",
            "address": "123 Main St",
        }
        result = map_advisor_info_worksheet_to_inputs(advisor_section = advisor)
        assert len(result) == 8
        assert result["input_ID_tab_setup_subtab_advisor_info_name"] == "John Advisor"
        assert result["input_ID_tab_setup_subtab_advisor_info_firm"] == "QWIM AI Wealth Management"

    @pytest.mark.unit
    def Test_Blanks_Missing_Fields(self) -> None:
        """Missing advisor fields receive empty strings."""
        result = map_advisor_info_worksheet_to_inputs(advisor_section = {})
        assert result["input_ID_tab_setup_subtab_advisor_info_name"] == ""
        assert result["input_ID_tab_setup_subtab_advisor_info_email"] == ""

    @pytest.mark.unit
    def Test_Handles_Non_Dict_Input(self) -> None:
        """Non-dict advisor section treated as empty."""
        result = map_advisor_info_worksheet_to_inputs(advisor_section = None)  # type: ignore[arg-type]
        assert result["input_ID_tab_setup_subtab_advisor_info_name"] == ""


# ---------------------------------------------------------------------------
# Section mapper edge cases — non-dict role payload fallback path
# ---------------------------------------------------------------------------


class Class_Test_Section_Mapper_Non_Dict_Role:
    """Tests for the ``section[client_role]`` non-dict fallback in section mappers.

    Notes
    -----
    The personal-info, assets, goals, and income mappers all begin with
    ``fields = section.get(client_role, {})`` followed by
    ``if not isinstance(fields, dict): fields = {}``. These tests cover
    the non-dict path so that the defensive branch is exercised.
    """

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("section", "client_role"),
        [
            ({"client_primary": "not_a_dict"}, "client_primary"),
            ({"client_primary": 42}, "client_primary"),
            ({"client_partner": ["unexpected", "list"]}, "client_partner"),
        ],
        ids=["string_value", "int_value", "list_value"],
    )
    def Test_Personal_Info_Mapper_Handles_Non_Dict_Role(
        self,
        section: dict[str, Any],
        client_role: str,
    ) -> None:
        """Personal-info mapper falls back to empty fields when role payload is non-dict."""
        result = map_personal_info_worksheet_to_inputs(
            section = section,
            client_role = client_role,
        )
        # All required text/numeric/select inputs should be present, with blank values.
        assert result[
            f"input_ID_tab_clients_subtab_clients_personal_info_{client_role}_name"
        ] == ""
        assert result[
            f"input_ID_tab_clients_subtab_clients_personal_info_{client_role}_age_current"
        ] is None
        # Selects are not added when normalized value is None.
        assert (
            f"input_ID_tab_clients_subtab_clients_personal_info_{client_role}_state"
            not in result
        )

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("section", "client_role"),
        [
            ({"client_primary": "not_a_dict"}, "client_primary"),
            ({"client_partner": None}, "client_partner"),
        ],
        ids=["string_value", "none_value"],
    )
    def Test_Assets_Mapper_Handles_Non_Dict_Role(
        self,
        section: dict[str, Any],
        client_role: str,
    ) -> None:
        """Assets mapper falls back to "$0" for all three fields when role payload is non-dict."""
        result = map_assets_worksheet_to_inputs(
            section = section,
            client_role = client_role,
        )
        for asset_key in ("assets_taxable", "assets_tax_deferred", "assets_tax_free"):
            assert (
                result[
                    f"input_ID_tab_clients_subtab_clients_assets_{client_role}_{asset_key}"
                ]
                == "$0"
            )

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("section", "client_role"),
        [
            ({"client_primary": "not_a_dict"}, "client_primary"),
            ({"client_partner": None}, "client_partner"),
        ],
        ids=["string_value", "none_value"],
    )
    def Test_Goals_Mapper_Handles_Non_Dict_Role(
        self,
        section: dict[str, Any],
        client_role: str,
    ) -> None:
        """Goals mapper falls back to "$0" for all three fields when role payload is non-dict."""
        result = map_goals_worksheet_to_inputs(
            section = section,
            client_role = client_role,
        )
        for goal_key in ("goal_essential", "goal_important", "goal_aspirational"):
            assert (
                result[
                    f"input_ID_tab_clients_subtab_clients_goals_{client_role}_{goal_key}"
                ]
                == "$0"
            )

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("section", "client_role"),
        [
            ({"client_primary": "not_a_dict"}, "client_primary"),
            ({"client_partner": None}, "client_partner"),
        ],
        ids=["string_value", "none_value"],
    )
    def Test_Income_Mapper_Handles_Non_Dict_Role(
        self,
        section: dict[str, Any],
        client_role: str,
    ) -> None:
        """Income mapper falls back to "$0" for all four fields when role payload is non-dict."""
        result = map_income_worksheet_to_inputs(
            section = section,
            client_role = client_role,
        )
        for income_key in (
            "income_social_security",
            "income_pension",
            "income_annuity_existing",
            "income_other",
        ):
            assert (
                result[
                    f"input_ID_tab_clients_subtab_clients_income_{client_role}_{income_key}"
                ]
                == "$0"
            )


# ---------------------------------------------------------------------------
# Coercion helpers — type-coverage edge cases
# ---------------------------------------------------------------------------


class Class_Test_Coerce_All_Type_Branches:
    """Tests exercising remaining coercion branches to reach 100 % branch coverage.

    Notes
    -----
    The coercion helpers have explicit ``isinstance`` short-circuits for
    ``int`` and ``float`` to avoid the string-parsing try/except. These
    tests cover those short-circuits so the corresponding branches
    register as executed.
    """

    @pytest.mark.unit
    def Test_Coerce_Int_Or_Zero_Float_Input(self) -> None:
        """Float input is truncated to int."""
        assert _coerce_int_or_zero(raw_value = 42.7) == 42

    @pytest.mark.unit
    def Test_Coerce_Int_Or_Zero_Currency_String_With_Empty_After_Cleaning(self) -> None:
        """Currency string that becomes empty after cleaning returns 0."""
        assert _coerce_int_or_zero(raw_value = "$$$, ") == 0

    @pytest.mark.unit
    def Test_Coerce_Numeric_Or_None_Float_Input(self) -> None:
        """Float input is truncated to int (not None)."""
        assert _coerce_numeric_or_none(raw_value = 65.9) == 65

    @pytest.mark.unit
    def Test_Coerce_Numeric_Or_None_String_Float(self) -> None:
        """Numeric float string coerces to int via the try-branch."""
        assert _coerce_numeric_or_none(raw_value = "65.9") == 65

    @pytest.mark.unit
    def Test_Coerce_Numeric_Or_None_Currency_String_With_Dollar(self) -> None:
        """Currency string '$42' is cleaned and coerced."""
        assert _coerce_numeric_or_none(raw_value = "$42") == 42

    @pytest.mark.unit
    def Test_Coerce_Numeric_Or_None_Currency_String_Only_Nonsense(self) -> None:
        """String of only currency markers strips to empty and returns None."""
        assert _coerce_numeric_or_none(raw_value = "$ ,") is None

    @pytest.mark.unit
    def Test_Coerce_Numeric_Or_None_Non_Coercible_Object(self) -> None:
        """Non-coercible object falls through the except to return None."""
        assert _coerce_numeric_or_none(raw_value = object()) is None

    @pytest.mark.unit
    def Test_Coerce_Int_Or_Zero_Whitespace_String(self) -> None:
        """Whitespace-only string returns 0 after stripping."""
        assert _coerce_int_or_zero(raw_value = "   ") == 0

    @pytest.mark.unit
    def Test_Coerce_Int_Or_Zero_Currency_String_With_Whitespace(self) -> None:
        """Currency string with surrounding whitespace is coerced after strip."""
        assert _coerce_int_or_zero(raw_value = "  $ 100  ") == 100

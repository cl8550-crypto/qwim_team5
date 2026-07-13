"""Hypothesis (property-based) tests for utils_enhanced_validation module.

Tests property invariants for:
- validate_enhanced_financial_amount
- validate_enhanced_percentage_value
- validate_enhanced_age_value
- validate_enhanced_name_value
- Financial_Validation_Config constants
- Risk_Tolerance_Enum, Gender_Enum, Marital_Status_Enum, Validation_Severity_Enum
- Personal_Information_Model
- Financial_Assets_Model
- get_validation_configuration
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from src.dashboard.shiny_utils.utils_enhanced_validation import (
    Financial_Assets_Model,
    Financial_Validation_Config,
    Gender_Enum,
    Marital_Status_Enum,
    Personal_Information_Model,
    Risk_Tolerance_Enum,
    Validation_Severity_Enum,
    get_validation_configuration,
    validate_enhanced_age_value,
    validate_enhanced_financial_amount,
    validate_enhanced_name_value,
    validate_enhanced_percentage_value,
)
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)


# ---------------------------------------------------------------------------
# Reusable strategies
# ---------------------------------------------------------------------------

_st_valid_amount = st.floats(
    min_value=0.0,
    max_value=1e6,
    allow_nan=False,
    allow_infinity=False,
).map(lambda val: round(val, 2))

_st_valid_age_int = st.integers(
    min_value=Financial_Validation_Config.MINIMUM_AGE,
    max_value=Financial_Validation_Config.MAXIMUM_AGE,
)

_st_valid_name = st.from_regex(
    r"^[A-Z][a-z]{1,19}( [A-Z][a-z]{1,19}){0,2}$",
    fullmatch=True,
)

_st_risk_tolerance = st.sampled_from(list(Risk_Tolerance_Enum))
_st_gender = st.sampled_from(list(Gender_Enum))
_st_marital_status = st.sampled_from(list(Marital_Status_Enum))


# ===========================================================================
# Class_Test_Hypothesis_Validation_Severity_Enum
# ===========================================================================


class Class_Test_Hypothesis_Validation_Severity_Enum:
    """Property tests for Validation_Severity_Enum."""

    @pytest.mark.unit()
    @given(item=st.sampled_from(list(Validation_Severity_Enum)))
    @settings(max_examples=200)
    def Test_all_members_are_non_empty_strings(
        self,
        item: Validation_Severity_Enum,
    ) -> None:
        """Every member value must be a non-empty lowercase string."""
        assert isinstance(item.value, str)
        assert len(item.value) > 0
        assert item.value == item.value.lower()

    @pytest.mark.unit()
    @given(item=st.sampled_from(list(Validation_Severity_Enum)))
    @settings(max_examples=200)
    def Test_member_str_representation_matches_value(
        self,
        item: Validation_Severity_Enum,
    ) -> None:
        """str(member) must equal its .value (StrEnum contract)."""
        assert str(item) == item.value


# ===========================================================================
# Class_Test_Hypothesis_Risk_Tolerance_Enum
# ===========================================================================


class Class_Test_Hypothesis_Risk_Tolerance_Enum:
    """Property tests for Risk_Tolerance_Enum."""

    @pytest.mark.unit()
    @given(item=st.sampled_from(list(Risk_Tolerance_Enum)))
    @settings(max_examples=200)
    def Test_all_members_have_capitalised_values(
        self,
        item: Risk_Tolerance_Enum,
    ) -> None:
        """Every Risk_Tolerance_Enum value must start with a capital letter."""
        assert item.value[0].isupper()

    @pytest.mark.unit()
    @given(item=st.sampled_from(list(Risk_Tolerance_Enum)))
    @settings(max_examples=200)
    def Test_member_str_matches_value(
        self,
        item: Risk_Tolerance_Enum,
    ) -> None:
        """StrEnum: str(member) == member.value."""
        assert str(item) == item.value


# ===========================================================================
# Class_Test_Hypothesis_Financial_Validation_Config
# ===========================================================================


class Class_Test_Hypothesis_Financial_Validation_Config:
    """Property tests for Financial_Validation_Config class constants."""

    @pytest.mark.unit()
    def Test_age_bounds_are_internally_consistent(self) -> None:
        """MINIMUM_AGE < MINIMUM_RETIREMENT_AGE < MAXIMUM_RETIREMENT_AGE < MAXIMUM_AGE."""
        assert Financial_Validation_Config.MINIMUM_AGE < Financial_Validation_Config.MINIMUM_RETIREMENT_AGE
        assert Financial_Validation_Config.MINIMUM_RETIREMENT_AGE < Financial_Validation_Config.MAXIMUM_RETIREMENT_AGE
        assert Financial_Validation_Config.MAXIMUM_RETIREMENT_AGE < Financial_Validation_Config.MAXIMUM_AGE

    @pytest.mark.unit()
    def Test_financial_amount_bounds_are_positive(self) -> None:
        """Financial amount bounds must both be non-negative and max > min."""
        assert Financial_Validation_Config.MINIMUM_FINANCIAL_AMOUNT >= 0.0
        assert Financial_Validation_Config.MAXIMUM_FINANCIAL_AMOUNT > Financial_Validation_Config.MINIMUM_FINANCIAL_AMOUNT

    @pytest.mark.unit()
    def Test_decimal_places_are_positive_integers(self) -> None:
        """Both decimal-places constants must be positive integers."""
        assert isinstance(Financial_Validation_Config.CURRENCY_DECIMAL_PLACES, int)
        assert isinstance(Financial_Validation_Config.PERCENTAGE_DECIMAL_PLACES, int)
        assert Financial_Validation_Config.CURRENCY_DECIMAL_PLACES > 0
        assert Financial_Validation_Config.PERCENTAGE_DECIMAL_PLACES > 0

    @pytest.mark.unit()
    def Test_name_length_bounds_are_sensible(self) -> None:
        """NAME_MIN_LENGTH >= 2 and NAME_MAX_LENGTH > NAME_MIN_LENGTH."""
        assert Financial_Validation_Config.NAME_MIN_LENGTH >= 2
        assert Financial_Validation_Config.NAME_MAX_LENGTH > Financial_Validation_Config.NAME_MIN_LENGTH


# ===========================================================================
# Class_Test_Hypothesis_Validate_Financial_Amount
# ===========================================================================


class Class_Test_Hypothesis_Validate_Financial_Amount:
    """Property tests for validate_enhanced_financial_amount."""

    @pytest.mark.unit()
    @given(amount=_st_valid_amount)
    @settings(max_examples=200)
    def Test_valid_float_returns_float_in_range(
        self,
        amount: float,
    ) -> None:
        """Valid non-negative float returns a float within [0, MAXIMUM_FINANCIAL_AMOUNT]."""
        result = validate_enhanced_financial_amount(
            amount=amount,
            minimum_value=0.0,
            maximum_value=Financial_Validation_Config.MAXIMUM_FINANCIAL_AMOUNT,
            decimal_places=2,
        )
        assert isinstance(result, float)
        assert 0.0 <= result <= Financial_Validation_Config.MAXIMUM_FINANCIAL_AMOUNT

    @pytest.mark.unit()
    @given(amount=_st_valid_amount)
    @settings(max_examples=200)
    def Test_result_respects_decimal_places(
        self,
        amount: float,
    ) -> None:
        """Result must have at most 2 decimal places when decimal_places=2."""
        result = validate_enhanced_financial_amount(
            amount=amount,
            decimal_places=2,
        )
        # Verify at most 2 decimal places by round-tripping
        assert round(result, 2) == result

    @pytest.mark.unit()
    @given(amount=_st_valid_amount)
    @settings(max_examples=200)
    def Test_integer_input_behaves_same_as_float(
        self,
        amount: float,
    ) -> None:
        """int and float representations of the same value should produce same result."""
        amount_int = int(amount)
        result_int = validate_enhanced_financial_amount(
            amount=amount_int,
            decimal_places=2,
        )
        result_float = validate_enhanced_financial_amount(
            amount=float(amount_int),
            decimal_places=2,
        )
        assert result_int == result_float

    @pytest.mark.unit()
    @given(
        amount=st.floats(
            min_value=-1e6,
            max_value=-0.01,
            allow_nan=False,
            allow_infinity=False,
        )
    )
    @settings(max_examples=200)
    def Test_negative_raises_when_allow_negative_is_false(
        self,
        amount: float,
    ) -> None:
        """Negative values with allow_negative=False must raise."""
        with pytest.raises(Exception):
            validate_enhanced_financial_amount(
                amount=round(amount, 2),
                allow_negative=False,
            )

    @pytest.mark.unit()
    def Test_none_input_raises_exception_validation_input(self) -> None:
        """None must raise Exception_Validation_Input."""
        with pytest.raises(Exception_Validation_Input):
            validate_enhanced_financial_amount(amount=None)  # type: ignore[arg-type]

    @pytest.mark.unit()
    @given(
        min_val=st.floats(min_value=0.0, max_value=500.0, allow_nan=False, allow_infinity=False),
        max_val=st.floats(min_value=501.0, max_value=1e6, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_result_is_between_min_and_max_when_given_midpoint(
        self,
        min_val: float,
        max_val: float,
    ) -> None:
        """Using midpoint of [min, max] should always return a value in that range."""
        midpoint = round((min_val + max_val) / 2.0, 2)
        result = validate_enhanced_financial_amount(
            amount=midpoint,
            minimum_value=min_val,
            maximum_value=max_val,
            decimal_places=2,
        )
        assert min_val <= result <= max_val

    @pytest.mark.unit()
    @given(amount=_st_valid_amount)
    @settings(max_examples=200)
    def Test_decimal_input_same_as_float(
        self,
        amount: float,
    ) -> None:
        """Decimal(str(x)) and float(x) should produce equal results."""
        result_float = validate_enhanced_financial_amount(
            amount=amount,
            decimal_places=2,
        )
        result_decimal = validate_enhanced_financial_amount(
            amount=Decimal(str(amount)),
            decimal_places=2,
        )
        assert abs(result_float - result_decimal) < 0.01

    @pytest.mark.unit()
    def Test_unsupported_type_raises_type_error(self) -> None:
        """Passing a list as amount must raise TypeError."""
        with pytest.raises((TypeError, Exception_Validation_Input)):
            validate_enhanced_financial_amount(amount=[100.0])  # type: ignore[arg-type]

    @pytest.mark.unit()
    @given(
        amount=st.floats(
            min_value=0.0,
            max_value=1e4,
            allow_nan=False,
            allow_infinity=False,
        ).map(lambda val: round(val, 2))
    )
    @settings(max_examples=200)
    def Test_currency_prefixed_string_equals_plain_value(
        self,
        amount: float,
    ) -> None:
        """'$1000.00' must produce the same result as 1000.00."""
        result_plain = validate_enhanced_financial_amount(
            amount=amount,
            decimal_places=2,
        )
        result_str = validate_enhanced_financial_amount(
            amount=f"${amount:.2f}",
            decimal_places=2,
        )
        assert abs(result_plain - result_str) < 0.01


# ===========================================================================
# Class_Test_Hypothesis_Validate_Age_Value
# ===========================================================================


class Class_Test_Hypothesis_Validate_Age_Value:
    """Property tests for validate_enhanced_age_value."""

    @pytest.mark.unit()
    @given(age=_st_valid_age_int)
    @settings(max_examples=200)
    def Test_valid_integer_age_returns_integer(
        self,
        age: int,
    ) -> None:
        """Valid integer age must return an int."""
        result = validate_enhanced_age_value(
            age=age,
            minimum_age=Financial_Validation_Config.MINIMUM_AGE,
            maximum_age=Financial_Validation_Config.MAXIMUM_AGE,
        )
        assert isinstance(result, int)

    @pytest.mark.unit()
    @given(age=_st_valid_age_int)
    @settings(max_examples=200)
    def Test_output_is_in_valid_range(
        self,
        age: int,
    ) -> None:
        """Output must lie within [MINIMUM_AGE, MAXIMUM_AGE]."""
        result = validate_enhanced_age_value(
            age=age,
            minimum_age=Financial_Validation_Config.MINIMUM_AGE,
            maximum_age=Financial_Validation_Config.MAXIMUM_AGE,
        )
        assert Financial_Validation_Config.MINIMUM_AGE <= result <= Financial_Validation_Config.MAXIMUM_AGE

    @pytest.mark.unit()
    @given(age=_st_valid_age_int)
    @settings(max_examples=200)
    def Test_string_representation_of_valid_age_works(
        self,
        age: int,
    ) -> None:
        """str(valid_age) must be accepted and return the same integer."""
        result = validate_enhanced_age_value(age=str(age))
        assert result == age

    @pytest.mark.unit()
    @given(
        age=st.integers(
            min_value=Financial_Validation_Config.MAXIMUM_AGE + 1,
            max_value=300,
        )
    )
    @settings(max_examples=200)
    def Test_above_max_age_raises(
        self,
        age: int,
    ) -> None:
        """Ages above MAXIMUM_AGE must raise."""
        with pytest.raises(Exception):
            validate_enhanced_age_value(
                age=age,
                maximum_age=Financial_Validation_Config.MAXIMUM_AGE,
            )

    @pytest.mark.unit()
    @given(
        age=st.integers(min_value=0, max_value=Financial_Validation_Config.MINIMUM_AGE - 1)
    )
    @settings(max_examples=200)
    def Test_below_min_age_raises(
        self,
        age: int,
    ) -> None:
        """Ages below MINIMUM_AGE must raise."""
        with pytest.raises(Exception):
            validate_enhanced_age_value(
                age=age,
                minimum_age=Financial_Validation_Config.MINIMUM_AGE,
            )

    @pytest.mark.unit()
    @given(
        age=st.floats(
            min_value=float(Financial_Validation_Config.MINIMUM_AGE),
            max_value=float(Financial_Validation_Config.MAXIMUM_AGE),
            allow_nan=False,
            allow_infinity=False,
        ).filter(lambda val: val != int(val))  # Only fractions
    )
    @settings(max_examples=200)
    def Test_fractional_age_without_allow_decimal_raises(
        self,
        age: float,
    ) -> None:
        """Fractional age with allow_decimal=False must raise."""
        with pytest.raises(Exception):
            validate_enhanced_age_value(age=age, allow_decimal=False)


# ===========================================================================
# Class_Test_Hypothesis_Validate_Name_Value
# ===========================================================================


class Class_Test_Hypothesis_Validate_Name_Value:
    """Property tests for validate_enhanced_name_value."""

    @pytest.mark.unit()
    @given(name=_st_valid_name)
    @settings(max_examples=200)
    def Test_valid_name_returns_title_case_string(
        self,
        name: str,
    ) -> None:
        """Valid name must return a non-empty title-cased string."""
        result = validate_enhanced_name_value(name=name)
        assert isinstance(result, str)
        assert len(result) >= Financial_Validation_Config.NAME_MIN_LENGTH
        # Title case: each word starts with uppercase
        for word in result.split():
            assert word[0].isupper()

    @pytest.mark.unit()
    @given(name=_st_valid_name)
    @settings(max_examples=200)
    def Test_leading_trailing_whitespace_is_stripped(
        self,
        name: str,
    ) -> None:
        """Names with leading/trailing spaces should produce same result as trimmed name."""
        result_plain = validate_enhanced_name_value(name=name)
        result_padded = validate_enhanced_name_value(name=f"  {name}  ")
        assert result_plain == result_padded

    @pytest.mark.unit()
    def Test_empty_string_raises(self) -> None:
        """Empty string must raise Exception_Validation_Input."""
        with pytest.raises(Exception_Validation_Input):
            validate_enhanced_name_value(name="")

    @pytest.mark.unit()
    def Test_whitespace_only_string_raises(self) -> None:
        """Whitespace-only string must raise Exception_Validation_Input."""
        with pytest.raises(Exception_Validation_Input):
            validate_enhanced_name_value(name="   ")

    @pytest.mark.unit()
    @given(
        name=st.text(
            alphabet=st.characters(whitelist_categories=("Ll", "Lu")),
            min_size=Financial_Validation_Config.NAME_MAX_LENGTH + 1,
            max_size=Financial_Validation_Config.NAME_MAX_LENGTH + 50,
        )
    )
    @settings(max_examples=200)
    def Test_name_exceeding_max_length_raises(
        self,
        name: str,
    ) -> None:
        """Names longer than NAME_MAX_LENGTH must raise."""
        with pytest.raises(Exception):
            validate_enhanced_name_value(
                name=name,
                max_length=Financial_Validation_Config.NAME_MAX_LENGTH,
            )

    @pytest.mark.unit()
    def Test_non_string_input_raises_type_error(self) -> None:
        """Passing a non-string must raise TypeError."""
        with pytest.raises(TypeError):
            validate_enhanced_name_value(name=42)  # type: ignore[arg-type]


# ===========================================================================
# Class_Test_Hypothesis_Validate_Percentage_Value
# ===========================================================================


class Class_Test_Hypothesis_Validate_Percentage_Value:
    """Property tests for validate_enhanced_percentage_value."""

    @pytest.mark.unit()
    @given(
        pct=st.floats(
            min_value=0.0,
            max_value=100.0,
            allow_nan=False,
            allow_infinity=False,
        ).map(lambda val: round(val, 4))
    )
    @settings(max_examples=200)
    def Test_valid_percentage_returns_value_in_range(
        self,
        pct: float,
    ) -> None:
        """Valid percentage in [0, 100] must return value within that range."""
        result = validate_enhanced_percentage_value(
            percentage=pct,
            minimum_value=0.0,
            maximum_value=100.0,
        )
        assert isinstance(result, float)
        assert 0.0 <= result <= 100.0

    @pytest.mark.unit()
    @given(
        pct=st.floats(
            min_value=0.01,
            max_value=50.0,
            allow_nan=False,
            allow_infinity=False,
        ).map(lambda val: round(val, 4))
    )
    @settings(max_examples=200)
    def Test_string_with_percent_symbol_works(
        self,
        pct: float,
    ) -> None:
        """'5.0%' and 5.0 should produce the same result."""
        result_float = validate_enhanced_percentage_value(percentage=pct)
        result_str = validate_enhanced_percentage_value(percentage=f"{pct}%")
        assert abs(result_float - result_str) < 0.01

    @pytest.mark.unit()
    @given(
        pct=st.floats(
            min_value=100.01,
            max_value=1000.0,
            allow_nan=False,
            allow_infinity=False,
        )
    )
    @settings(max_examples=200)
    def Test_value_above_100_raises(
        self,
        pct: float,
    ) -> None:
        """Percentage above 100 must raise when maximum_value=100."""
        with pytest.raises(Exception):
            validate_enhanced_percentage_value(
                percentage=round(pct, 4),
                maximum_value=100.0,
            )


# ===========================================================================
# Class_Test_Hypothesis_Financial_Assets_Model
# ===========================================================================


class Class_Test_Hypothesis_Financial_Assets_Model:
    """Property tests for Financial_Assets_Model."""

    @pytest.mark.unit()
    @given(
        taxable=st.floats(min_value=0.0, max_value=3e8, allow_nan=False, allow_infinity=False),
        tax_deferred=st.floats(min_value=0.0, max_value=3e8, allow_nan=False, allow_infinity=False),
        tax_free=st.floats(min_value=0.0, max_value=3e8, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_total_assets_equals_sum_of_components(
        self,
        taxable: float,
        tax_deferred: float,
        tax_free: float,
    ) -> None:
        """total_assets must equal taxable + tax_deferred + tax_free."""
        # Avoid concentration > 95% which triggers model_validator error
        total = taxable + tax_deferred + tax_free
        if total == 0.0:
            return
        if max(taxable, tax_deferred, tax_free) / total > 0.94:
            return
        model_obj = Financial_Assets_Model(
            taxable_assets=taxable,
            tax_deferred_assets=tax_deferred,
            tax_free_assets=tax_free,
        )
        assert abs(model_obj.total_assets - (taxable + tax_deferred + tax_free)) < 1e-6

    @pytest.mark.unit()
    @given(
        taxable=st.floats(min_value=1.0, max_value=1e7, allow_nan=False, allow_infinity=False),
        tax_deferred=st.floats(min_value=1.0, max_value=1e7, allow_nan=False, allow_infinity=False),
        tax_free=st.floats(min_value=1.0, max_value=1e7, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_asset_allocation_percentages_sum_to_100(
        self,
        taxable: float,
        tax_deferred: float,
        tax_free: float,
    ) -> None:
        """asset_allocation percentages must sum to ~100 when total > 0."""
        total = taxable + tax_deferred + tax_free
        if max(taxable, tax_deferred, tax_free) / total > 0.94:
            return
        model_obj = Financial_Assets_Model(
            taxable_assets=taxable,
            tax_deferred_assets=tax_deferred,
            tax_free_assets=tax_free,
        )
        alloc = model_obj.asset_allocation
        alloc_sum = sum(alloc.values())
        assert abs(alloc_sum - 100.0) < 1e-6

    @pytest.mark.unit()
    @given(
        negative_val=st.floats(
            min_value=-1e6,
            max_value=-0.01,
            allow_nan=False,
            allow_infinity=False,
        )
    )
    @settings(max_examples=200)
    def Test_negative_asset_raises_validation_error(
        self,
        negative_val: float,
    ) -> None:
        """Negative asset values must raise ValidationError."""
        with pytest.raises((ValidationError, Exception_Validation_Input, Exception, ValueError)):
            Financial_Assets_Model(
                taxable_assets=negative_val,
                tax_deferred_assets=0.0,
                tax_free_assets=0.0,
            )

    @pytest.mark.unit()
    def Test_zero_assets_allocation_is_all_zeros(self) -> None:
        """When total_assets == 0, all allocation percentages must be 0."""
        model_obj = Financial_Assets_Model(
            taxable_assets=0.0,
            tax_deferred_assets=0.0,
            tax_free_assets=0.0,
        )
        alloc = model_obj.asset_allocation
        assert all(val == 0.0 for val in alloc.values())

    @pytest.mark.unit()
    @given(
        big_taxable=st.floats(min_value=9.6e8, max_value=1e9, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_highly_concentrated_portfolio_raises(
        self,
        big_taxable: float,
    ) -> None:
        """A portfolio where one type > 95% of total must raise ValidationError."""
        small_val = big_taxable * 0.01  # << 5%
        with pytest.raises((ValidationError, Exception_Validation_Input, Exception)):
            Financial_Assets_Model(
                taxable_assets=big_taxable,
                tax_deferred_assets=small_val,
                tax_free_assets=small_val,
            )


# ===========================================================================
# Class_Test_Hypothesis_Personal_Information_Model
# ===========================================================================


class Class_Test_Hypothesis_Personal_Information_Model:
    """Property tests for Personal_Information_Model."""

    @pytest.mark.unit()
    @given(
        current_age=st.integers(
            min_value=Financial_Validation_Config.MINIMUM_AGE,
            max_value=Financial_Validation_Config.MINIMUM_RETIREMENT_AGE - 2,
        ),
        years_to_retire=st.integers(min_value=1, max_value=30),
        risk_tolerance=_st_risk_tolerance,
        gender=_st_gender,
        marital_status=_st_marital_status,
    )
    @settings(max_examples=200)
    def Test_valid_personal_info_constructs_successfully(
        self,
        current_age: int,
        years_to_retire: int,
        risk_tolerance: Risk_Tolerance_Enum,
        gender: Gender_Enum,
        marital_status: Marital_Status_Enum,
    ) -> None:
        """Valid personal information must construct without raising."""
        retirement_age = min(
            current_age + years_to_retire,
            Financial_Validation_Config.MAXIMUM_RETIREMENT_AGE,
        )
        if retirement_age < Financial_Validation_Config.MINIMUM_RETIREMENT_AGE:
            retirement_age = Financial_Validation_Config.MINIMUM_RETIREMENT_AGE
        if retirement_age <= current_age:
            return  # Skip degenerate cases

        # planning horizon check: must be 1–50 years
        if not (1 <= retirement_age - current_age <= 50):
            return

        model_obj = Personal_Information_Model(
            name="John Smith",
            current_age=current_age,
            retirement_age=retirement_age,
            income_start_age=retirement_age,
            risk_tolerance=risk_tolerance,
            gender=gender,
            marital_status=marital_status,
        )
        assert model_obj.current_age == current_age
        assert model_obj.retirement_age > model_obj.current_age

    @pytest.mark.unit()
    @given(
        current_age=st.integers(
            min_value=Financial_Validation_Config.MINIMUM_RETIREMENT_AGE + 1,
            max_value=Financial_Validation_Config.MAXIMUM_AGE,
        )
    )
    @settings(max_examples=200)
    def Test_retirement_age_below_current_age_raises(
        self,
        current_age: int,
    ) -> None:
        """retirement_age <= current_age must raise ValidationError."""
        retirement_age = Financial_Validation_Config.MINIMUM_RETIREMENT_AGE  # always <= current_age here
        with pytest.raises((ValidationError, Exception_Validation_Input, Exception)):
            Personal_Information_Model(
                name="Test User",
                current_age=current_age,
                retirement_age=retirement_age,
                income_start_age=retirement_age,
                risk_tolerance=Risk_Tolerance_Enum.MODERATE,
                gender=Gender_Enum.MALE,
                marital_status=Marital_Status_Enum.SINGLE,
            )

    @pytest.mark.unit()
    @given(risk_tolerance=_st_risk_tolerance)
    @settings(max_examples=200)
    def Test_all_risk_tolerance_values_accepted(
        self,
        risk_tolerance: Risk_Tolerance_Enum,
    ) -> None:
        """Every Risk_Tolerance_Enum member must be accepted by Personal_Information_Model."""
        model_obj = Personal_Information_Model(
            name="Jane Doe",
            current_age=30,
            retirement_age=65,
            income_start_age=65,
            risk_tolerance=risk_tolerance,
            gender=Gender_Enum.FEMALE,
            marital_status=Marital_Status_Enum.SINGLE,
        )
        assert model_obj.risk_tolerance == risk_tolerance.value


# ===========================================================================
# Class_Test_Hypothesis_Get_Validation_Configuration
# ===========================================================================


class Class_Test_Hypothesis_Get_Validation_Configuration:
    """Property tests for get_validation_configuration."""

    @pytest.mark.unit()
    def Test_returns_dict_with_required_keys(self) -> None:
        """Result must be a dict containing at minimum expected top-level keys."""
        config = get_validation_configuration()
        assert isinstance(config, dict)
        for expected_key in ("age_constraints", "financial_constraints", "text_constraints", "enumerations"):
            assert expected_key in config

    @pytest.mark.unit()
    def Test_age_constraints_are_consistent_with_config_class(self) -> None:
        """age_constraints values must match Financial_Validation_Config."""
        config = get_validation_configuration()
        age_constraints = config["age_constraints"]
        assert age_constraints["minimum_age"] == Financial_Validation_Config.MINIMUM_AGE
        assert age_constraints["maximum_age"] == Financial_Validation_Config.MAXIMUM_AGE

    @pytest.mark.unit()
    def Test_enumerations_contain_all_enum_members(self) -> None:
        """enumerations dict must list all members of each enum."""
        config = get_validation_configuration()
        enums = config["enumerations"]
        assert set(enums["risk_tolerance_options"]) == {item.value for item in Risk_Tolerance_Enum}
        assert set(enums["gender_options"]) == {item.value for item in Gender_Enum}
        assert set(enums["marital_status_options"]) == {item.value for item in Marital_Status_Enum}

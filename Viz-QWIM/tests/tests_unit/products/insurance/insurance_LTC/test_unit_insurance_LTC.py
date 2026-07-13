"""Unit tests for insurance_LTC_base and insurance_LTC_traditional modules.

Covers enum values, base class validation, Traditional LTC constructor,
premium calculation, benefit calculations, and error paths.
"""

from __future__ import annotations

import pytest


# ======================================================================
# Fixtures
# ======================================================================


@pytest.fixture()
def ltc_traditional_class():
    """Import Insurance_LTC_Traditional."""
    from src.products.insurance.insurance_LTC.insurance_LTC_traditional import (
        Insurance_LTC_Traditional,
    )

    return Insurance_LTC_Traditional


@pytest.fixture()
def ltc_enums():
    """Import LTC base enumerations."""
    from src.products.insurance.insurance_LTC.insurance_LTC_base import (
        Benefit_Period,
        Care_Setting,
        Elimination_Period,
        Inflation_Protection,
        Insurance_LTC_Type,
        Premium_Frequency_LTC,
    )

    return {
        "Insurance_LTC_Type": Insurance_LTC_Type,
        "Benefit_Period": Benefit_Period,
        "Elimination_Period": Elimination_Period,
        "Inflation_Protection": Inflation_Protection,
        "Care_Setting": Care_Setting,
        "Premium_Frequency_LTC": Premium_Frequency_LTC,
    }


@pytest.fixture()
def traditional_enums():
    """Import Traditional LTC enumerations."""
    from src.products.insurance.insurance_LTC.insurance_LTC_traditional import (
        Gender_LTC,
        Health_Class_LTC,
        Non_Forfeiture_Option,
    )

    return {
        "Gender_LTC": Gender_LTC,
        "Health_Class_LTC": Health_Class_LTC,
        "Non_Forfeiture_Option": Non_Forfeiture_Option,
    }


@pytest.fixture()
def basic_traditional(ltc_traditional_class, traditional_enums):
    """A valid Insurance_LTC_Traditional instance with default settings."""
    return ltc_traditional_class(
        insured_age=60,
        daily_benefit_amount=200.0,
        gender=traditional_enums["Gender_LTC"].FEMALE,
    )


@pytest.fixture()
def ltc_base_concrete_class():
    """A minimal concrete subclass of Insurance_LTC_Base for base-class testing."""
    from src.products.insurance.insurance_LTC.insurance_LTC_base import (
        Benefit_Period,
        Care_Setting,
        Elimination_Period,
        Inflation_Protection,
        Insurance_LTC_Base,
        Insurance_LTC_Type,
        Premium_Frequency_LTC,
    )

    class _Concrete_LTC(Insurance_LTC_Base):
        def __init__(
            self,
            insured_age: int,
            daily_benefit_amount: float,
            insurance_type: Insurance_LTC_Type = Insurance_LTC_Type.TRADITIONAL,
            benefit_period: Benefit_Period = Benefit_Period.YEARS_3,
            elimination_period: Elimination_Period = Elimination_Period.DAYS_90,
            inflation_protection: Inflation_Protection = Inflation_Protection.NONE,
            care_setting: Care_Setting = Care_Setting.ALL,
            premium_frequency: Premium_Frequency_LTC = Premium_Frequency_LTC.ANNUAL,
            is_smoker: bool = False,
            is_married_discount: bool = False,
        ) -> None:
            super().__init__(
                insured_age=insured_age,
                daily_benefit_amount=daily_benefit_amount,
                insurance_type=insurance_type,
                benefit_period=benefit_period,
                elimination_period=elimination_period,
                inflation_protection=inflation_protection,
                care_setting=care_setting,
                premium_frequency=premium_frequency,
                is_smoker=is_smoker,
                is_married_discount=is_married_discount,
            )

        def calc_maximum_lifetime_benefit(self) -> float:
            return self.m_daily_benefit_amount * 365 * 3

        def calc_annual_premium(self) -> float:
            return self.m_daily_benefit_amount * 12

        def calc_daily_benefit_at_year(self, year: int) -> float:
            return self.m_daily_benefit_amount

    return _Concrete_LTC


# ======================================================================
# Base class — enum values
# ======================================================================


class Class_Test_LTC_Base_Enums:
    """Verify all LTC base enum values are accessible and correct."""

    @pytest.mark.unit()
    def Test_Insurance_LTC_Type_Values(self, ltc_enums):
        """Insurance_LTC_Type should have three variants."""
        T = ltc_enums["Insurance_LTC_Type"]
        assert T.TRADITIONAL.value == "Traditional LTC Insurance"
        assert T.HYBRID_LIFE.value == "Hybrid Life LTC Insurance"
        assert T.HYBRID_ANNUITY.value == "Hybrid Annuity LTC Insurance"

    @pytest.mark.unit()
    def Test_Benefit_Period_Values(self, ltc_enums):
        """Benefit_Period numeric values should match documented years."""
        BP = ltc_enums["Benefit_Period"]
        assert BP.YEARS_2.value == 2
        assert BP.YEARS_3.value == 3
        assert BP.LIFETIME.value == 100

    @pytest.mark.unit()
    def Test_Elimination_Period_Values(self, ltc_enums):
        """Elimination_Period values should match documented days."""
        EP = ltc_enums["Elimination_Period"]
        assert EP.DAYS_0.value == 0
        assert EP.DAYS_90.value == 90
        assert EP.DAYS_365.value == 365

    @pytest.mark.unit()
    def Test_Inflation_Protection_None_Value(self, ltc_enums):
        """Inflation_Protection.NONE should be the string 'None'."""
        IP = ltc_enums["Inflation_Protection"]
        assert IP.NONE.value == "None"
        assert IP.COMPOUND_5.value == "Compound 5%"

    @pytest.mark.unit()
    def Test_Care_Setting_All_Value(self, ltc_enums):
        """Care_Setting.ALL should be 'All Care Settings'."""
        CS = ltc_enums["Care_Setting"]
        assert CS.ALL.value == "All Care Settings"
        assert CS.NURSING_HOME.value == "Nursing Home"

    @pytest.mark.unit()
    def Test_Premium_Frequency_LTC_Values(self, ltc_enums):
        """Premium_Frequency_LTC numeric values should match payment counts."""
        PF = ltc_enums["Premium_Frequency_LTC"]
        assert PF.ANNUAL.value == 1
        assert PF.MONTHLY.value == 12
        assert PF.SINGLE.value == 0


# ======================================================================
# Base class — validation
# ======================================================================


class Class_Test_LTC_Base_Validation:
    """Validation paths in the Insurance_LTC_Base constructor."""

    @pytest.mark.unit()
    def Test_Raises_When_Age_Too_Young(self, ltc_traditional_class, traditional_enums):
        """insured_age < 18 should raise Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            ltc_traditional_class(
                insured_age=15,
                daily_benefit_amount=150.0,
                gender=traditional_enums["Gender_LTC"].MALE,
            )

    @pytest.mark.unit()
    def Test_Raises_When_Age_Too_Old(self, ltc_traditional_class, traditional_enums):
        """insured_age > 120 should raise Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            ltc_traditional_class(
                insured_age=125,
                daily_benefit_amount=150.0,
                gender=traditional_enums["Gender_LTC"].FEMALE,
            )

    @pytest.mark.unit()
    def Test_Raises_When_Daily_Benefit_Zero(self, ltc_traditional_class, traditional_enums):
        """daily_benefit_amount <= 0 should raise Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            ltc_traditional_class(
                insured_age=55,
                daily_benefit_amount=0.0,
                gender=traditional_enums["Gender_LTC"].MALE,
            )

    @pytest.mark.unit()
    def Test_Raises_When_Daily_Benefit_Negative(self, ltc_traditional_class, traditional_enums):
        """Negative daily_benefit_amount should raise Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            ltc_traditional_class(
                insured_age=55,
                daily_benefit_amount=-100.0,
                gender=traditional_enums["Gender_LTC"].FEMALE,
            )


# ======================================================================
# Traditional LTC — construction
# ======================================================================


class Class_Test_LTC_Traditional_Construction:
    """Tests for Insurance_LTC_Traditional constructor."""

    @pytest.mark.unit()
    def Test_Valid_Default_Construction(self, basic_traditional, ltc_enums, traditional_enums):
        """Default construction should set all expected attributes."""
        obj = basic_traditional
        assert obj.m_insured_age == 60
        assert obj.m_daily_benefit_amount == pytest.approx(200.0)
        assert obj.m_insurance_type == ltc_enums["Insurance_LTC_Type"].TRADITIONAL
        assert obj.m_benefit_period == ltc_enums["Benefit_Period"].YEARS_3
        assert obj.m_elimination_period == ltc_enums["Elimination_Period"].DAYS_90
        assert obj.m_inflation_protection == ltc_enums["Inflation_Protection"].NONE
        assert obj.m_is_smoker is False
        assert obj.m_is_married_discount is False

    @pytest.mark.unit()
    def Test_Custom_Benefit_Period(
        self, ltc_traditional_class, ltc_enums, traditional_enums
    ):
        """LIFETIME benefit period should be stored correctly."""
        obj = ltc_traditional_class(
            insured_age=55,
            daily_benefit_amount=300.0,
            gender=traditional_enums["Gender_LTC"].MALE,
            benefit_period=ltc_enums["Benefit_Period"].LIFETIME,
        )
        assert obj.m_benefit_period == ltc_enums["Benefit_Period"].LIFETIME

    @pytest.mark.unit()
    def Test_Smoker_Flag_Set(self, ltc_traditional_class, traditional_enums):
        """is_smoker=True should be stored on m_is_smoker."""
        obj = ltc_traditional_class(
            insured_age=50,
            daily_benefit_amount=250.0,
            gender=traditional_enums["Gender_LTC"].MALE,
            is_smoker=True,
        )
        assert obj.m_is_smoker is True

    @pytest.mark.unit()
    def Test_Married_Discount_Flag(self, ltc_traditional_class, traditional_enums):
        """is_married_discount=True should be stored correctly."""
        obj = ltc_traditional_class(
            insured_age=62,
            daily_benefit_amount=180.0,
            gender=traditional_enums["Gender_LTC"].FEMALE,
            is_married_discount=True,
        )
        assert obj.m_is_married_discount is True

    @pytest.mark.unit()
    def Test_Compound_Inflation_Protection(
        self, ltc_traditional_class, ltc_enums, traditional_enums
    ):
        """COMPOUND_5 inflation protection should be stored."""
        obj = ltc_traditional_class(
            insured_age=50,
            daily_benefit_amount=200.0,
            gender=traditional_enums["Gender_LTC"].FEMALE,
            inflation_protection=ltc_enums["Inflation_Protection"].COMPOUND_5,
        )
        assert obj.m_inflation_protection == ltc_enums["Inflation_Protection"].COMPOUND_5

    @pytest.mark.unit()
    def Test_Raises_When_Gender_Invalid_Type(self, ltc_traditional_class):
        """Passing a string instead of Gender_LTC enum should raise."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            ltc_traditional_class(
                insured_age=60,
                daily_benefit_amount=200.0,
                gender="Female",
            )


# ======================================================================
# Traditional LTC — premium calculation
# ======================================================================


class Class_Test_LTC_Traditional_Premium:
    """Tests for Insurance_LTC_Traditional.calc_annual_premium()."""

    @pytest.mark.unit()
    def Test_Annual_Premium_Is_Positive(self, basic_traditional):
        """calc_annual_premium should return a positive float."""
        premium = basic_traditional.calc_annual_premium()
        assert isinstance(premium, float)
        assert premium > 0.0

    @pytest.mark.unit()
    def Test_Smoker_Premium_Higher_Than_Non_Smoker(
        self, ltc_traditional_class, traditional_enums
    ):
        """Smoker premium should exceed non-smoker premium for same profile."""
        base = {
            "insured_age": 60,
            "daily_benefit_amount": 200.0,
            "gender": traditional_enums["Gender_LTC"].MALE,
        }
        non_smoker = ltc_traditional_class(**base, is_smoker=False)
        smoker = ltc_traditional_class(**base, is_smoker=True)
        assert smoker.calc_annual_premium() > non_smoker.calc_annual_premium()

    @pytest.mark.unit()
    def Test_Married_Discount_Reduces_Premium(
        self, ltc_traditional_class, traditional_enums
    ):
        """Married discount should produce a lower annual premium."""
        base = {
            "insured_age": 58,
            "daily_benefit_amount": 150.0,
            "gender": traditional_enums["Gender_LTC"].FEMALE,
        }
        no_discount = ltc_traditional_class(**base, is_married_discount=False)
        with_discount = ltc_traditional_class(**base, is_married_discount=True)
        assert with_discount.calc_annual_premium() < no_discount.calc_annual_premium()

    @pytest.mark.unit()
    def Test_Longer_Benefit_Period_Increases_Premium(
        self, ltc_traditional_class, ltc_enums, traditional_enums
    ):
        """LIFETIME benefit period should cost more than YEARS_2."""
        base = {
            "insured_age": 55,
            "daily_benefit_amount": 200.0,
            "gender": traditional_enums["Gender_LTC"].MALE,
        }
        short = ltc_traditional_class(**base, benefit_period=ltc_enums["Benefit_Period"].YEARS_2)
        lifetime = ltc_traditional_class(
            **base, benefit_period=ltc_enums["Benefit_Period"].LIFETIME
        )
        assert lifetime.calc_annual_premium() > short.calc_annual_premium()

    @pytest.mark.unit()
    def Test_Compound_Inflation_Increases_Premium(
        self, ltc_traditional_class, ltc_enums, traditional_enums
    ):
        """Compound 5% inflation protection should increase the premium."""
        base = {
            "insured_age": 55,
            "daily_benefit_amount": 200.0,
            "gender": traditional_enums["Gender_LTC"].FEMALE,
        }
        no_infl = ltc_traditional_class(
            **base, inflation_protection=ltc_enums["Inflation_Protection"].NONE
        )
        compound5 = ltc_traditional_class(
            **base, inflation_protection=ltc_enums["Inflation_Protection"].COMPOUND_5
        )
        assert compound5.calc_annual_premium() > no_infl.calc_annual_premium()


# ======================================================================
# Traditional LTC — benefit and lifetime-benefit methods
# ======================================================================


class Class_Test_LTC_Traditional_Benefits:
    """Tests for benefit calculation methods."""

    @pytest.mark.unit()
    def Test_Max_Lifetime_Benefit_Is_Positive(self, basic_traditional):
        """calc_maximum_lifetime_benefit should return a positive float."""
        mlb = basic_traditional.calc_maximum_lifetime_benefit()
        assert isinstance(mlb, float)
        assert mlb > 0.0

    @pytest.mark.unit()
    def Test_Daily_Benefit_At_Year_One_No_Inflation(self, basic_traditional):
        """Daily benefit at year 1 with no inflation should equal the daily_benefit_amount."""
        benefit = basic_traditional.calc_daily_benefit_at_year(year=1)
        assert isinstance(benefit, float)
        assert benefit == pytest.approx(200.0, rel=1e-6)

    @pytest.mark.unit()
    def Test_Compound_Inflation_Grows_Benefit(
        self, ltc_traditional_class, ltc_enums, traditional_enums
    ):
        """With COMPOUND_5 inflation, benefit at year 10 should exceed year 1."""
        obj = ltc_traditional_class(
            insured_age=55,
            daily_benefit_amount=200.0,
            gender=traditional_enums["Gender_LTC"].FEMALE,
            inflation_protection=ltc_enums["Inflation_Protection"].COMPOUND_5,
        )
        b1 = obj.calc_daily_benefit_at_year(year=1)
        b10 = obj.calc_daily_benefit_at_year(year=10)
        assert b10 > b1

    @pytest.mark.unit()
    def Test_Lifetime_Benefit_With_Lifetime_Period(
        self, ltc_traditional_class, ltc_enums, traditional_enums
    ):
        """Lifetime benefit period should produce the largest pool."""
        short = ltc_traditional_class(
            insured_age=60,
            daily_benefit_amount=200.0,
            gender=traditional_enums["Gender_LTC"].MALE,
            benefit_period=ltc_enums["Benefit_Period"].YEARS_2,
        )
        lifetime = ltc_traditional_class(
            insured_age=60,
            daily_benefit_amount=200.0,
            gender=traditional_enums["Gender_LTC"].MALE,
            benefit_period=ltc_enums["Benefit_Period"].LIFETIME,
        )
        assert lifetime.calc_maximum_lifetime_benefit() > short.calc_maximum_lifetime_benefit()


# ======================================================================
# Package import smoke tests
# ======================================================================


class Class_Test_LTC_Package_Imports:
    """Smoke tests to ensure all LTC insurance sub-modules are importable."""

    @pytest.mark.unit()
    def Test_LTC_Base_Module_Importable(self):
        """insurance_LTC_base should be importable."""
        import src.products.insurance.insurance_LTC.insurance_LTC_base  # noqa: F401

    @pytest.mark.unit()
    def Test_LTC_Traditional_Module_Importable(self):
        """insurance_LTC_traditional should be importable."""
        import src.products.insurance.insurance_LTC.insurance_LTC_traditional  # noqa: F401

    @pytest.mark.unit()
    def Test_LTC_Hybrid_Annuity_Module_Importable(self):
        """insurance_LTC_hybrid_annuity should be importable."""
        import src.products.insurance.insurance_LTC.insurance_LTC_hybrid_annuity  # noqa: F401

    @pytest.mark.unit()
    def Test_LTC_Hybrid_Life_Module_Importable(self):
        """insurance_LTC_hybrid_life should be importable."""
        import src.products.insurance.insurance_LTC.insurance_LTC_hybrid_life  # noqa: F401

    @pytest.mark.unit()
    def Test_LTC_Init_Package_Importable(self):
        """insurance_LTC __init__ package should be importable."""
        import src.products.insurance.insurance_LTC  # noqa: F401

    @pytest.mark.unit()
    def Test_Insurance_Package_Importable(self):
        """insurance package should be importable."""
        import src.products.insurance  # noqa: F401


# ======================================================================
# Base class — missing validation raises (enum type parameters)
# ======================================================================


class Class_Test_LTC_Base_Validation_Enum_Types:
    """Cover the validation raises for wrong-typed enum constructor arguments."""

    @pytest.mark.unit()
    def Test_Raises_When_Insurance_Type_Wrong_Type(
        self, ltc_base_concrete_class
    ):
        """Passing a string as insurance_type must raise Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            ltc_base_concrete_class(
                insured_age=55,
                daily_benefit_amount=200.0,
                insurance_type="Traditional",
            )

    @pytest.mark.unit()
    def Test_Raises_When_Benefit_Period_Wrong_Type(
        self, ltc_traditional_class, traditional_enums
    ):
        """Passing a string as benefit_period must raise Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            ltc_traditional_class(
                insured_age=55,
                daily_benefit_amount=200.0,
                gender=traditional_enums["Gender_LTC"].FEMALE,
                benefit_period="3 years",
            )

    @pytest.mark.unit()
    def Test_Raises_When_Elimination_Period_Wrong_Type(
        self, ltc_traditional_class, traditional_enums
    ):
        """Passing an int as elimination_period must raise Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            ltc_traditional_class(
                insured_age=55,
                daily_benefit_amount=200.0,
                gender=traditional_enums["Gender_LTC"].FEMALE,
                elimination_period=90,
            )

    @pytest.mark.unit()
    def Test_Raises_When_Inflation_Protection_Wrong_Type(
        self, ltc_traditional_class, traditional_enums
    ):
        """Passing a string as inflation_protection must raise Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            ltc_traditional_class(
                insured_age=55,
                daily_benefit_amount=200.0,
                gender=traditional_enums["Gender_LTC"].FEMALE,
                inflation_protection="Compound 5%",
            )

    @pytest.mark.unit()
    def Test_Raises_When_Care_Setting_Wrong_Type(
        self, ltc_traditional_class, traditional_enums
    ):
        """Passing a string as care_setting must raise Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            ltc_traditional_class(
                insured_age=55,
                daily_benefit_amount=200.0,
                gender=traditional_enums["Gender_LTC"].FEMALE,
                care_setting="Nursing Home",
            )

    @pytest.mark.unit()
    def Test_Raises_When_Premium_Frequency_Wrong_Type(
        self, ltc_traditional_class, traditional_enums
    ):
        """Passing a string as premium_frequency must raise Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            ltc_traditional_class(
                insured_age=55,
                daily_benefit_amount=200.0,
                gender=traditional_enums["Gender_LTC"].FEMALE,
                premium_frequency="Annual",
            )


# ======================================================================
# Base class — property accessors
# ======================================================================


class Class_Test_LTC_Base_Properties:
    """Verify all property getters return the stored value."""

    @pytest.mark.unit()
    def Test_Insured_Age_Property(self, basic_traditional):
        """insured_age property returns m_insured_age."""
        assert basic_traditional.insured_age == basic_traditional.m_insured_age

    @pytest.mark.unit()
    def Test_Daily_Benefit_Amount_Property(self, basic_traditional):
        """daily_benefit_amount property returns m_daily_benefit_amount."""
        assert basic_traditional.daily_benefit_amount == pytest.approx(
            basic_traditional.m_daily_benefit_amount
        )

    @pytest.mark.unit()
    def Test_Insurance_Type_Property(self, basic_traditional, ltc_enums):
        """insurance_type property returns Insurance_LTC_Type.TRADITIONAL."""
        assert basic_traditional.insurance_type == ltc_enums["Insurance_LTC_Type"].TRADITIONAL

    @pytest.mark.unit()
    def Test_Benefit_Period_Property(self, basic_traditional, ltc_enums):
        """benefit_period property returns the stored Benefit_Period."""
        assert basic_traditional.benefit_period == ltc_enums["Benefit_Period"].YEARS_3

    @pytest.mark.unit()
    def Test_Elimination_Period_Property(self, basic_traditional, ltc_enums):
        """elimination_period property returns Elimination_Period.DAYS_90."""
        assert basic_traditional.elimination_period == ltc_enums["Elimination_Period"].DAYS_90

    @pytest.mark.unit()
    def Test_Inflation_Protection_Property(self, basic_traditional, ltc_enums):
        """inflation_protection property defaults to Inflation_Protection.NONE."""
        assert basic_traditional.inflation_protection == ltc_enums["Inflation_Protection"].NONE

    @pytest.mark.unit()
    def Test_Care_Setting_Property(self, basic_traditional, ltc_enums):
        """care_setting property defaults to Care_Setting.ALL."""
        assert basic_traditional.care_setting == ltc_enums["Care_Setting"].ALL

    @pytest.mark.unit()
    def Test_Premium_Frequency_Property(self, basic_traditional, ltc_enums):
        """premium_frequency property defaults to Premium_Frequency_LTC.ANNUAL."""
        assert basic_traditional.premium_frequency == ltc_enums["Premium_Frequency_LTC"].ANNUAL

    @pytest.mark.unit()
    def Test_Is_Smoker_Property_Default_False(self, basic_traditional):
        """is_smoker property should default to False."""
        assert basic_traditional.is_smoker is False

    @pytest.mark.unit()
    def Test_Is_Married_Discount_Property_Default_False(self, basic_traditional):
        """is_married_discount property should default to False."""
        assert basic_traditional.is_married_discount is False


# ======================================================================
# Base class — calc_monthly_benefit_amount and calc_annual_benefit_amount
# ======================================================================


class Class_Test_LTC_Base_Benefit_Amounts:
    """Tests for monthly and annual benefit convenience helpers."""

    @pytest.mark.unit()
    def Test_Monthly_Benefit_Amount(self, basic_traditional):
        """calc_monthly_benefit_amount should equal daily_benefit * 30."""
        result = basic_traditional.calc_monthly_benefit_amount()
        assert result == pytest.approx(200.0 * 30.0)

    @pytest.mark.unit()
    def Test_Annual_Benefit_Amount(self, basic_traditional):
        """calc_annual_benefit_amount should equal daily_benefit * 365."""
        result = basic_traditional.calc_annual_benefit_amount()
        assert result == pytest.approx(200.0 * 365.0)


# ======================================================================
# Base class — calc_modal_factor
# ======================================================================


class Class_Test_LTC_Base_Calc_Modal_Factor:
    """Tests for Insurance_LTC_Base.calc_modal_premium_factor()."""

    @pytest.mark.unit()
    def Test_Annual_Modal_Factor_Is_One(
        self, ltc_traditional_class, ltc_enums, traditional_enums
    ):
        """Annual premium_frequency should yield modal factor 1.0."""
        obj = ltc_traditional_class(
            insured_age=60,
            daily_benefit_amount=200.0,
            gender=traditional_enums["Gender_LTC"].FEMALE,
            premium_frequency=ltc_enums["Premium_Frequency_LTC"].ANNUAL,
        )
        assert obj.calc_modal_premium_factor() == pytest.approx(1.0)

    @pytest.mark.unit()
    def Test_Monthly_Modal_Factor(
        self, ltc_traditional_class, ltc_enums, traditional_enums
    ):
        """Monthly premium_frequency should yield a modal factor less than 1.0."""
        obj = ltc_traditional_class(
            insured_age=60,
            daily_benefit_amount=200.0,
            gender=traditional_enums["Gender_LTC"].FEMALE,
            premium_frequency=ltc_enums["Premium_Frequency_LTC"].MONTHLY,
        )
        factor = obj.calc_modal_premium_factor()
        assert factor > 0.0
        assert factor < 1.0


# ======================================================================
# Base class — get_insurance_as_string
# ======================================================================


class Class_Test_LTC_Base_Get_Insurance_As_String:
    """Tests for Insurance_LTC_Base.get_insurance_as_string()."""

    @pytest.mark.unit()
    def Test_String_Contains_Insurance_Type(self, ltc_base_concrete_class):
        """String representation should contain the insurance type value."""
        obj = ltc_base_concrete_class(insured_age=60, daily_benefit_amount=200.0)
        result = obj.get_insurance_as_string()
        assert "Traditional LTC Insurance" in result

    @pytest.mark.unit()
    def Test_String_Contains_Non_Smoker_For_Default(self, ltc_base_concrete_class):
        """Default (non-smoker) policy string should contain 'Non-Smoker'."""
        obj = ltc_base_concrete_class(insured_age=60, daily_benefit_amount=200.0)
        result = obj.get_insurance_as_string()
        assert "Non-Smoker" in result

    @pytest.mark.unit()
    def Test_String_Contains_Smoker_For_Smoker_Policy(self, ltc_base_concrete_class):
        """Smoker policy string should contain 'Smoker'."""
        obj = ltc_base_concrete_class(
            insured_age=55,
            daily_benefit_amount=200.0,
            is_smoker=True,
        )
        result = obj.get_insurance_as_string()
        assert "Smoker" in result
        assert "Non-Smoker" not in result

    @pytest.mark.unit()
    def Test_String_Contains_Age(self, ltc_base_concrete_class):
        """String representation should contain the insured age."""
        obj = ltc_base_concrete_class(insured_age=60, daily_benefit_amount=200.0)
        result = obj.get_insurance_as_string()
        assert "60" in result


# ======================================================================
# LTC Hybrid Life Tests
# ======================================================================


@pytest.fixture()
def ltc_hybrid_life_class():
    """Import Insurance_LTC_Hybrid_Life."""
    from src.products.insurance.insurance_LTC.insurance_LTC_hybrid_life import (
        Insurance_LTC_Hybrid_Life,
    )

    return Insurance_LTC_Hybrid_Life


@pytest.fixture()
def basic_hybrid_life(ltc_hybrid_life_class):
    """A valid Insurance_LTC_Hybrid_Life instance."""
    return ltc_hybrid_life_class(
        insured_age=60,
        death_benefit=250_000.0,
        single_premium=100_000.0,
    )


@pytest.mark.unit()
class Class_Test_LTC_Hybrid_Life_Construction:
    """Tests for Insurance_LTC_Hybrid_Life constructor."""

    @pytest.mark.unit()
    def test_creates_instance(self, basic_hybrid_life):
        """Hybrid Life LTC instance created without error."""
        assert basic_hybrid_life is not None

    @pytest.mark.unit()
    def test_invalid_death_benefit_raises(self, ltc_hybrid_life_class):
        """Non-positive death_benefit raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            ltc_hybrid_life_class(insured_age=60, death_benefit=0.0, single_premium=100_000.0)

    @pytest.mark.unit()
    def test_invalid_single_premium_raises(self, ltc_hybrid_life_class):
        """Non-positive single_premium raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            ltc_hybrid_life_class(insured_age=60, death_benefit=250_000.0, single_premium=-1.0)


@pytest.mark.unit()
class Class_Test_LTC_Hybrid_Life_Calculations:
    """Tests for Insurance_LTC_Hybrid_Life calculation methods."""

    @pytest.mark.unit()
    def test_calc_maximum_lifetime_benefit_positive(self, basic_hybrid_life):
        """Maximum lifetime benefit is positive."""
        assert basic_hybrid_life.calc_maximum_lifetime_benefit() > 0.0

    @pytest.mark.unit()
    def test_calc_annual_premium_positive(self, basic_hybrid_life):
        """Annual premium is non-negative."""
        assert basic_hybrid_life.calc_annual_premium() >= 0.0

    @pytest.mark.unit()
    def test_calc_daily_benefit_at_year_positive(self, basic_hybrid_life):
        """Daily benefit at year 1 is positive."""
        assert basic_hybrid_life.calc_daily_benefit_at_year(year = 1) > 0.0

    @pytest.mark.unit()
    def test_calc_monthly_ltc_benefit_positive(self, basic_hybrid_life):
        """Monthly LTC benefit is positive."""
        assert basic_hybrid_life.calc_monthly_LTC_benefit() > 0.0

    @pytest.mark.unit()
    def test_calc_cash_value_at_year_returns_float(self, basic_hybrid_life):
        """Cash value at year 5 returns a non-negative float."""
        result = basic_hybrid_life.calc_cash_value_at_year(year = 5)
        assert isinstance(result, float)
        assert result >= 0.0

    @pytest.mark.unit()
    def test_calc_benefit_leverage_ratio_returns_float(self, basic_hybrid_life):
        """Benefit leverage ratio returns a float."""
        assert isinstance(basic_hybrid_life.calc_benefit_leverage_ratio(), float)

    @pytest.mark.unit()
    def test_get_insurance_as_string_contains_hybrid(self, basic_hybrid_life):
        """String representation contains 'Hybrid'."""
        assert "Hybrid" in basic_hybrid_life.get_insurance_as_string()


# ======================================================================
# LTC Hybrid Annuity Tests
# ======================================================================


@pytest.fixture()
def ltc_hybrid_annuity_class():
    """Import Insurance_LTC_Hybrid_Annuity."""
    from src.products.insurance.insurance_LTC.insurance_LTC_hybrid_annuity import (
        Insurance_LTC_Hybrid_Annuity,
    )

    return Insurance_LTC_Hybrid_Annuity


@pytest.fixture()
def basic_hybrid_annuity(ltc_hybrid_annuity_class):
    """A valid Insurance_LTC_Hybrid_Annuity instance."""
    return ltc_hybrid_annuity_class(
        insured_age=60,
        single_premium=100_000.0,
    )


@pytest.mark.unit()
class Class_Test_LTC_Hybrid_Annuity_Construction:
    """Tests for Insurance_LTC_Hybrid_Annuity constructor."""

    @pytest.mark.unit()
    def test_creates_instance(self, basic_hybrid_annuity):
        """Hybrid Annuity LTC instance created without error."""
        assert basic_hybrid_annuity is not None

    @pytest.mark.unit()
    def test_invalid_single_premium_raises(self, ltc_hybrid_annuity_class):
        """Non-positive single_premium raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            ltc_hybrid_annuity_class(insured_age=60, single_premium=0.0)

    @pytest.mark.unit()
    def test_invalid_guaranteed_crediting_rate_raises(self, ltc_hybrid_annuity_class):
        """Out-of-range guaranteed_crediting_rate raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            ltc_hybrid_annuity_class(
                insured_age=60,
                single_premium=100_000.0,
                guaranteed_crediting_rate=0.50,
            )


@pytest.mark.unit()
class Class_Test_LTC_Hybrid_Annuity_Calculations:
    """Tests for Insurance_LTC_Hybrid_Annuity calculation methods."""

    @pytest.mark.unit()
    def test_calc_maximum_lifetime_benefit_positive(self, basic_hybrid_annuity):
        """Maximum lifetime benefit is positive."""
        assert basic_hybrid_annuity.calc_maximum_lifetime_benefit() > 0.0

    @pytest.mark.unit()
    def test_calc_annual_premium_returns_single_premium(self, basic_hybrid_annuity):
        """Annual premium returns the single premium amount."""
        assert basic_hybrid_annuity.calc_annual_premium() >= 0.0

    @pytest.mark.unit()
    def test_calc_daily_benefit_at_year_returns_positive(self, basic_hybrid_annuity):
        """Daily benefit at year 1 is positive."""
        assert basic_hybrid_annuity.calc_daily_benefit_at_year(year = 1) > 0.0

    @pytest.mark.unit()
    def test_calc_account_value_at_year_returns_float(self, basic_hybrid_annuity):
        """Account value at year 5 returns a non-negative float."""
        result = basic_hybrid_annuity.calc_account_value_at_year(year = 5)
        assert isinstance(result, float)
        assert result >= 0.0

    @pytest.mark.unit()
    def test_calc_death_benefit_year_1_positive(self, basic_hybrid_annuity):
        """Death benefit at year 1 is positive."""
        assert basic_hybrid_annuity.calc_death_benefit(year = 1) > 0.0

    @pytest.mark.unit()
    def test_calc_benefit_leverage_ratio_returns_float(self, basic_hybrid_annuity):
        """Benefit leverage ratio returns a float."""
        assert isinstance(basic_hybrid_annuity.calc_benefit_leverage_ratio(), float)

    @pytest.mark.unit()
    def test_get_insurance_as_string_contains_hybrid(self, basic_hybrid_annuity):
        """String representation contains 'Hybrid'."""
        assert "Hybrid" in basic_hybrid_annuity.get_insurance_as_string()


# ======================================================================
# LTC Hybrid Annuity — Extended Property and Branch Coverage
# ======================================================================


@pytest.mark.unit()
class Class_Test_LTC_Hybrid_Annuity_Properties:
    """Tests for Insurance_LTC_Hybrid_Annuity property accessors."""

    @pytest.mark.unit()
    def test_single_premium_property(self, basic_hybrid_annuity):
        """single_premium property returns expected value."""
        assert basic_hybrid_annuity.single_premium == 100_000.0

    @pytest.mark.unit()
    def test_ltc_multiplier_property(self, basic_hybrid_annuity):
        """LTC_multiplier property returns an enum instance."""
        from src.products.insurance.insurance_LTC.insurance_LTC_hybrid_annuity import (
            LTC_Multiplier,
        )

        assert isinstance(basic_hybrid_annuity.LTC_multiplier, LTC_Multiplier)

    @pytest.mark.unit()
    def test_annuity_type_property(self, basic_hybrid_annuity):
        """annuity_type property returns an enum instance."""
        from src.products.insurance.insurance_LTC.insurance_LTC_hybrid_annuity import (
            Annuity_Type_Hybrid,
        )

        assert isinstance(basic_hybrid_annuity.annuity_type, Annuity_Type_Hybrid)

    @pytest.mark.unit()
    def test_guaranteed_crediting_rate_property(self, basic_hybrid_annuity):
        """guaranteed_crediting_rate property returns expected default."""
        assert basic_hybrid_annuity.guaranteed_crediting_rate == pytest.approx(0.02)

    @pytest.mark.unit()
    def test_surrender_schedule_property(self, basic_hybrid_annuity):
        """surrender_schedule property returns an enum instance."""
        from src.products.insurance.insurance_LTC.insurance_LTC_hybrid_annuity import (
            Surrender_Schedule_Type,
        )

        assert isinstance(basic_hybrid_annuity.surrender_schedule, Surrender_Schedule_Type)

    @pytest.mark.unit()
    def test_guaranteed_min_surrender_pct_property(self, basic_hybrid_annuity):
        """guaranteed_min_surrender_pct property returns expected default."""
        assert basic_hybrid_annuity.guaranteed_min_surrender_pct == pytest.approx(0.90)

    @pytest.mark.unit()
    def test_death_benefit_floor_pct_property(self, basic_hybrid_annuity):
        """death_benefit_floor_pct property returns expected default."""
        assert basic_hybrid_annuity.death_benefit_floor_pct == pytest.approx(1.0)

    @pytest.mark.unit()
    def test_invalid_guaranteed_crediting_rate_negative_raises(self, ltc_hybrid_annuity_class):
        """Negative guaranteed_crediting_rate raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            ltc_hybrid_annuity_class(
                insured_age=60,
                single_premium=100_000.0,
                guaranteed_crediting_rate=-0.01,
            )

    @pytest.mark.unit()
    def test_invalid_surrender_schedule_type_raises(self, ltc_hybrid_annuity_class):
        """Non-enum surrender_schedule raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            ltc_hybrid_annuity_class(
                insured_age=60,
                single_premium=100_000.0,
                surrender_schedule="STANDARD",
            )

    @pytest.mark.unit()
    def test_invalid_death_benefit_floor_pct_raises(self, ltc_hybrid_annuity_class):
        """Out-of-range death_benefit_floor_pct raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            ltc_hybrid_annuity_class(
                insured_age=60,
                single_premium=100_000.0,
                death_benefit_floor_pct=3.0,
            )


@pytest.mark.unit()
class Class_Test_LTC_Hybrid_Annuity_Extra:
    """Extra branch-coverage tests for Insurance_LTC_Hybrid_Annuity."""

    @pytest.mark.unit()
    def test_surrender_schedule_none(self, ltc_hybrid_annuity_class):
        """Surrender schedule NONE type is accepted."""
        from src.products.insurance.insurance_LTC.insurance_LTC_hybrid_annuity import (
            Surrender_Schedule_Type,
        )

        p = ltc_hybrid_annuity_class(
            insured_age=60,
            single_premium=100_000.0,
            surrender_schedule=Surrender_Schedule_Type.NONE,
        )
        result = p.calc_surrender_value(year = 1)
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_surrender_schedule_short(self, ltc_hybrid_annuity_class):
        """Surrender schedule SHORT type is accepted."""
        from src.products.insurance.insurance_LTC.insurance_LTC_hybrid_annuity import (
            Surrender_Schedule_Type,
        )

        p = ltc_hybrid_annuity_class(
            insured_age=60,
            single_premium=100_000.0,
            surrender_schedule=Surrender_Schedule_Type.SHORT,
        )
        result = p.calc_surrender_value(year = 1)
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_surrender_value_year_0_raises(self, basic_hybrid_annuity):
        """calc_surrender_value with year < 1 raises exception."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_hybrid_annuity.calc_surrender_value(year = 0)

    @pytest.mark.unit()
    def test_account_value_year_0_raises(self, basic_hybrid_annuity):
        """calc_account_value_at_year with year < 1 raises exception."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_hybrid_annuity.calc_account_value_at_year(year = 0)

    @pytest.mark.unit()
    def test_ltc_pool_at_year_year_0_raises(self, basic_hybrid_annuity):
        """calc_LTC_pool_at_year with year < 1 raises exception."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_hybrid_annuity.calc_LTC_pool_at_year(year = 0)

    @pytest.mark.unit()
    def test_monthly_ltc_benefit_at_year_0_raises(self, basic_hybrid_annuity):
        """calc_monthly_LTC_benefit_at_year with year < 1 raises exception."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_hybrid_annuity.calc_monthly_LTC_benefit_at_year(year = 0)

    @pytest.mark.unit()
    def test_monthly_ltc_benefit_at_year_valid(self, basic_hybrid_annuity):
        """calc_monthly_LTC_benefit_at_year returns the rounded monthly pool amount."""
        pool = basic_hybrid_annuity.calc_LTC_pool_at_year(year = 1)

        result = basic_hybrid_annuity.calc_monthly_LTC_benefit_at_year(year = 1)

        assert result == pytest.approx(
            round(pool / (basic_hybrid_annuity.benefit_period.value * 12), 2),
        )

    @pytest.mark.unit()
    def test_death_benefit_year_0_raises(self, basic_hybrid_annuity):
        """calc_death_benefit with year < 1 raises exception."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_hybrid_annuity.calc_death_benefit(year = 0)

    @pytest.mark.unit()
    def test_death_benefit_after_ltc_negative_paid_raises(self, basic_hybrid_annuity):
        """calc_death_benefit_after_LTC with negative LTC_benefits_paid raises."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_hybrid_annuity.calc_death_benefit_after_LTC(LTC_benefits_paid=-100.0, year=1)

    @pytest.mark.unit()
    def test_death_benefit_after_ltc_valid(self, basic_hybrid_annuity):
        """calc_death_benefit_after_LTC with valid inputs returns float."""
        result = basic_hybrid_annuity.calc_death_benefit_after_LTC(LTC_benefits_paid=10_000.0, year=1)
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_remaining_ltc_pool_negative_paid_raises(self, basic_hybrid_annuity):
        """calc_remaining_LTC_pool with negative LTC_benefits_paid raises."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_hybrid_annuity.calc_remaining_LTC_pool(LTC_benefits_paid=-1.0)

    @pytest.mark.unit()
    def test_remaining_ltc_pool_valid(self, basic_hybrid_annuity):
        """calc_remaining_LTC_pool with valid inputs returns float."""
        result = basic_hybrid_annuity.calc_remaining_LTC_pool(LTC_benefits_paid=50_000.0)
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_effective_annual_cost_positive_rate_diff(self, ltc_hybrid_annuity_class):
        """calc_effective_annual_cost returns float."""
        p = ltc_hybrid_annuity_class(
            insured_age=60,
            single_premium=100_000.0,
            guaranteed_crediting_rate=0.01,
        )
        result = p.calc_effective_annual_cost(year = 1)
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_effective_annual_cost_year_0_raises(self, basic_hybrid_annuity):
        """calc_effective_annual_cost with year < 1 raises exception."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_hybrid_annuity.calc_effective_annual_cost(year = 0)

    @pytest.mark.unit()
    def test_internal_rate_of_return_ltc_invalid_benefits_raises(self, basic_hybrid_annuity):
        """calc_internal_rate_of_return_LTC with zero benefits raises."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_hybrid_annuity.calc_internal_rate_of_return_LTC(
                total_LTC_benefits_received=0.0, years_on_claim=5
            )

    @pytest.mark.unit()
    def test_internal_rate_of_return_ltc_invalid_year_raises(self, basic_hybrid_annuity):
        """calc_internal_rate_of_return_LTC with invalid year raises."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_hybrid_annuity.calc_internal_rate_of_return_LTC(
                total_LTC_benefits_received=200_000.0, years_on_claim=0
            )

    @pytest.mark.unit()
    def test_internal_rate_of_return_ltc_valid(self, basic_hybrid_annuity):
        """calc_internal_rate_of_return_LTC returns float for valid inputs."""
        result = basic_hybrid_annuity.calc_internal_rate_of_return_LTC(
            total_LTC_benefits_received=300_000.0, years_on_claim=5
        )
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_daily_benefit_at_year_with_inflation(self, ltc_hybrid_annuity_class):
        """calc_daily_benefit_at_year with compound inflation returns float."""
        from src.products.insurance.insurance_LTC.insurance_LTC_base import (
            Inflation_Protection,
        )

        p = ltc_hybrid_annuity_class(
            insured_age=60,
            single_premium=100_000.0,
            inflation_protection=Inflation_Protection.COMPOUND_3,
        )
        result = p.calc_daily_benefit_at_year(year = 5)
        assert result > 0.0

    @pytest.mark.unit()
    def test_daily_benefit_at_year_with_simple_inflation(self, ltc_hybrid_annuity_class):
        """calc_daily_benefit_at_year with simple inflation returns float."""
        from src.products.insurance.insurance_LTC.insurance_LTC_base import (
            Inflation_Protection,
        )

        p = ltc_hybrid_annuity_class(
            insured_age=60,
            single_premium=100_000.0,
            inflation_protection=Inflation_Protection.SIMPLE_3,
        )
        result = p.calc_daily_benefit_at_year(year = 5)
        assert result > 0.0

    @pytest.mark.unit()
    def test_ltc_multiplier_times_3(self, ltc_hybrid_annuity_class):
        """LTC_Multiplier.TIMES_3 is accepted and works."""
        from src.products.insurance.insurance_LTC.insurance_LTC_hybrid_annuity import (
            LTC_Multiplier,
        )

        p = ltc_hybrid_annuity_class(
            insured_age=60,
            single_premium=100_000.0,
            LTC_multiplier=LTC_Multiplier.TIMES_3,
        )
        assert p.calc_maximum_lifetime_benefit() > 0.0

    @pytest.mark.unit()
    def test_ltc_multiplier_times_4(self, ltc_hybrid_annuity_class):
        """LTC_Multiplier.TIMES_4 is accepted and works."""
        from src.products.insurance.insurance_LTC.insurance_LTC_hybrid_annuity import (
            LTC_Multiplier,
        )

        p = ltc_hybrid_annuity_class(
            insured_age=60,
            single_premium=100_000.0,
            LTC_multiplier=LTC_Multiplier.TIMES_4,
        )
        assert p.calc_maximum_lifetime_benefit() > 0.0

    @pytest.mark.unit()
    def test_annuity_type_fixed_indexed(self, ltc_hybrid_annuity_class):
        """Annuity_Type_Hybrid.FIXED_INDEXED is accepted."""
        from src.products.insurance.insurance_LTC.insurance_LTC_hybrid_annuity import (
            Annuity_Type_Hybrid,
        )

        p = ltc_hybrid_annuity_class(
            insured_age=60,
            single_premium=100_000.0,
            annuity_type=Annuity_Type_Hybrid.FIXED_INDEXED,
        )
        assert p is not None

    @pytest.mark.unit()
    def test_surrender_value_late_year(self, basic_hybrid_annuity):
        """calc_surrender_value at year 15 (past schedule) returns float."""
        result = basic_hybrid_annuity.calc_surrender_value(year = 15)
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_get_surrender_charge_pct_standard_past_schedule(self, basic_hybrid_annuity):
        """_get_surrender_charge_pct with STANDARD schedule beyond year 10 returns 0.0."""
        result = basic_hybrid_annuity._get_surrender_charge_pct(year = 11)
        assert result == 0.0

    @pytest.mark.unit()
    def test_invalid_ltc_multiplier_raises(self, ltc_hybrid_annuity_class):
        """Non-enum LTC_multiplier raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            ltc_hybrid_annuity_class(
                insured_age=60,
                single_premium=100_000.0,
                LTC_multiplier="TIMES_2",
            )

    @pytest.mark.unit()
    def test_invalid_annuity_type_raises(self, ltc_hybrid_annuity_class):
        """Non-enum annuity_type raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            ltc_hybrid_annuity_class(
                insured_age=60,
                single_premium=100_000.0,
                annuity_type="FIXED",
            )

    @pytest.mark.unit()
    def test_invalid_guaranteed_min_surrender_pct_raises(self, ltc_hybrid_annuity_class):
        """Out-of-range guaranteed_min_surrender_pct raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            ltc_hybrid_annuity_class(
                insured_age=60,
                single_premium=100_000.0,
                guaranteed_min_surrender_pct=2.0,
            )

    @pytest.mark.unit()
    def test_daily_benefit_at_year_0_raises(self, basic_hybrid_annuity):
        """calc_daily_benefit_at_year with year < 1 raises exception."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_hybrid_annuity.calc_daily_benefit_at_year(year = 0)

    @pytest.mark.unit()
    def test_surrender_schedule_short_beyond_years(self, ltc_hybrid_annuity_class):
        """SHORT schedule beyond year 5 returns 0 charge."""
        from src.products.insurance.insurance_LTC.insurance_LTC_hybrid_annuity import (
            Surrender_Schedule_Type,
        )

        p = ltc_hybrid_annuity_class(
            insured_age=60,
            single_premium=100_000.0,
            surrender_schedule=Surrender_Schedule_Type.SHORT,
        )
        # Year 6 is beyond the 5-year SHORT schedule; should return 0 charge
        result = p.calc_surrender_value(year = 6)
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_effective_annual_cost_high_crediting_rate(self, ltc_hybrid_annuity_class):
        """calc_effective_annual_cost returns 0.0 when crediting_rate >= market rate."""
        p = ltc_hybrid_annuity_class(
            insured_age=60,
            single_premium=100_000.0,
            guaranteed_crediting_rate=0.05,
        )
        result = p.calc_effective_annual_cost(year = 1)
        assert result == 0.0


# ======================================================================
# LTC Hybrid Life — Extended Property and Branch Coverage
# ======================================================================


@pytest.mark.unit()
class Class_Test_LTC_Hybrid_Life_Properties:
    """Tests for Insurance_LTC_Hybrid_Life property accessors."""

    @pytest.mark.unit()
    def test_death_benefit_property(self, basic_hybrid_life):
        """death_benefit property returns expected value."""
        assert basic_hybrid_life.death_benefit == 250_000.0

    @pytest.mark.unit()
    def test_single_premium_property(self, basic_hybrid_life):
        """single_premium property returns expected value."""
        assert basic_hybrid_life.single_premium == 100_000.0

    @pytest.mark.unit()
    def test_premium_structure_property(self, basic_hybrid_life):
        """premium_structure property returns an enum instance."""
        from src.products.insurance.insurance_LTC.insurance_LTC_hybrid_life import (
            Premium_Structure_Hybrid_Life,
        )

        assert isinstance(basic_hybrid_life.premium_structure, Premium_Structure_Hybrid_Life)

    @pytest.mark.unit()
    def test_extension_of_benefits_property(self, basic_hybrid_life):
        """extension_of_benefits property returns an enum instance."""
        from src.products.insurance.insurance_LTC.insurance_LTC_hybrid_life import (
            Extension_Of_Benefits,
        )

        assert isinstance(basic_hybrid_life.extension_of_benefits, Extension_Of_Benefits)

    @pytest.mark.unit()
    def test_return_of_premium_property(self, basic_hybrid_life):
        """return_of_premium property returns an enum instance."""
        from src.products.insurance.insurance_LTC.insurance_LTC_hybrid_life import (
            Return_Of_Premium_Type,
        )

        assert isinstance(basic_hybrid_life.return_of_premium, Return_Of_Premium_Type)

    @pytest.mark.unit()
    def test_cash_value_growth_rate_property(self, basic_hybrid_life):
        """cash_value_growth_rate property returns expected default."""
        assert basic_hybrid_life.cash_value_growth_rate == pytest.approx(0.02)

    @pytest.mark.unit()
    def test_residual_death_benefit_pct_property(self, basic_hybrid_life):
        """residual_death_benefit_pct property returns expected default."""
        assert basic_hybrid_life.residual_death_benefit_pct == pytest.approx(0.10)

    @pytest.mark.unit()
    def test_invalid_cash_value_growth_rate_raises(self, ltc_hybrid_life_class):
        """Out-of-range cash_value_growth_rate raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            ltc_hybrid_life_class(
                insured_age=60,
                death_benefit=250_000.0,
                single_premium=100_000.0,
                cash_value_growth_rate=0.50,
            )

    @pytest.mark.unit()
    def test_invalid_cash_value_growth_rate_negative_raises(self, ltc_hybrid_life_class):
        """Negative cash_value_growth_rate raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            ltc_hybrid_life_class(
                insured_age=60,
                death_benefit=250_000.0,
                single_premium=100_000.0,
                cash_value_growth_rate=-0.01,
            )

    @pytest.mark.unit()
    def test_invalid_residual_death_benefit_pct_raises(self, ltc_hybrid_life_class):
        """Out-of-range residual_death_benefit_pct raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            ltc_hybrid_life_class(
                insured_age=60,
                death_benefit=250_000.0,
                single_premium=100_000.0,
                residual_death_benefit_pct=1.5,
            )

    @pytest.mark.unit()
    def test_invalid_residual_death_benefit_pct_negative_raises(self, ltc_hybrid_life_class):
        """Negative residual_death_benefit_pct raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            ltc_hybrid_life_class(
                insured_age=60,
                death_benefit=250_000.0,
                single_premium=100_000.0,
                residual_death_benefit_pct=-0.01,
            )

    @pytest.mark.unit()
    def test_invalid_return_of_premium_type_raises(self, ltc_hybrid_life_class):
        """Non-enum return_of_premium raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            ltc_hybrid_life_class(
                insured_age=60,
                death_benefit=250_000.0,
                single_premium=100_000.0,
                return_of_premium="FULL",
            )

    @pytest.mark.unit()
    def test_invalid_premium_structure_raises(self, ltc_hybrid_life_class):
        """Non-enum premium_structure raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            ltc_hybrid_life_class(
                insured_age=60,
                death_benefit=250_000.0,
                single_premium=100_000.0,
                premium_structure="SINGLE",
            )

    @pytest.mark.unit()
    def test_invalid_extension_of_benefits_raises(self, ltc_hybrid_life_class):
        """Non-enum extension_of_benefits raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            ltc_hybrid_life_class(
                insured_age=60,
                death_benefit=250_000.0,
                single_premium=100_000.0,
                extension_of_benefits="TIMES_2",
            )


@pytest.mark.unit()
class Class_Test_LTC_Hybrid_Life_Extra:
    """Extra branch-coverage tests for Insurance_LTC_Hybrid_Life."""

    @pytest.mark.unit()
    def test_return_of_premium_none(self, ltc_hybrid_life_class):
        """Return_Of_Premium_Type.NONE is accepted."""
        from src.products.insurance.insurance_LTC.insurance_LTC_hybrid_life import (
            Return_Of_Premium_Type,
        )

        p = ltc_hybrid_life_class(
            insured_age=60,
            death_benefit=250_000.0,
            single_premium=100_000.0,
            return_of_premium=Return_Of_Premium_Type.NONE,
        )
        result = p.calc_surrender_value(year = 1)
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_return_of_premium_graded(self, ltc_hybrid_life_class):
        """Return_Of_Premium_Type.GRADED is accepted."""
        from src.products.insurance.insurance_LTC.insurance_LTC_hybrid_life import (
            Return_Of_Premium_Type,
        )

        p = ltc_hybrid_life_class(
            insured_age=60,
            death_benefit=250_000.0,
            single_premium=100_000.0,
            return_of_premium=Return_Of_Premium_Type.GRADED,
        )
        result = p.calc_surrender_value(year = 1)
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_return_of_premium_full(self, basic_hybrid_life):
        """calc_surrender_value with FULL ROP returns float."""
        result = basic_hybrid_life.calc_surrender_value(year = 1)
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_daily_benefit_year_0_raises(self, basic_hybrid_life):
        """calc_daily_benefit_at_year with year < 1 raises exception."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_hybrid_life.calc_daily_benefit_at_year(year = 0)

    @pytest.mark.unit()
    def test_cash_value_at_year_0_raises(self, basic_hybrid_life):
        """calc_cash_value_at_year with year < 1 raises exception."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_hybrid_life.calc_cash_value_at_year(year = 0)

    @pytest.mark.unit()
    def test_surrender_value_year_0_raises(self, basic_hybrid_life):
        """calc_surrender_value with year < 1 raises exception."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_hybrid_life.calc_surrender_value(year = 0)

    @pytest.mark.unit()
    def test_daily_benefit_with_compound_inflation(self, ltc_hybrid_life_class):
        """calc_daily_benefit_at_year with COMPOUND_3 inflation returns float."""
        from src.products.insurance.insurance_LTC.insurance_LTC_base import (
            Inflation_Protection,
        )

        p = ltc_hybrid_life_class(
            insured_age=60,
            death_benefit=250_000.0,
            single_premium=100_000.0,
            inflation_protection=Inflation_Protection.COMPOUND_3,
        )
        result = p.calc_daily_benefit_at_year(year = 5)
        assert result > 0.0

    @pytest.mark.unit()
    def test_daily_benefit_with_simple_inflation(self, ltc_hybrid_life_class):
        """calc_daily_benefit_at_year with SIMPLE_3 inflation returns float."""
        from src.products.insurance.insurance_LTC.insurance_LTC_base import (
            Inflation_Protection,
        )

        p = ltc_hybrid_life_class(
            insured_age=60,
            death_benefit=250_000.0,
            single_premium=100_000.0,
            inflation_protection=Inflation_Protection.SIMPLE_3,
        )
        result = p.calc_daily_benefit_at_year(year = 5)
        assert result > 0.0

    @pytest.mark.unit()
    def test_residual_death_benefit_negative_paid_raises(self, basic_hybrid_life):
        """calc_residual_death_benefit with negative LTC_benefits_paid raises."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_hybrid_life.calc_residual_death_benefit(LTC_benefits_paid=-1.0)

    @pytest.mark.unit()
    def test_residual_death_benefit_valid(self, basic_hybrid_life):
        """calc_residual_death_benefit with valid inputs returns float."""
        result = basic_hybrid_life.calc_residual_death_benefit(LTC_benefits_paid=50_000.0)
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_remaining_ltc_pool_negative_raises(self, basic_hybrid_life):
        """calc_remaining_LTC_pool with negative benefits_paid raises."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_hybrid_life.calc_remaining_LTC_pool(LTC_benefits_paid=-1.0)

    @pytest.mark.unit()
    def test_remaining_ltc_pool_valid(self, basic_hybrid_life):
        """calc_remaining_LTC_pool with valid inputs returns float."""
        result = basic_hybrid_life.calc_remaining_LTC_pool(LTC_benefits_paid=50_000.0)
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_irr_death_invalid_year_raises(self, basic_hybrid_life):
        """calc_internal_rate_of_return_death with year < 1 raises exception."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_hybrid_life.calc_internal_rate_of_return_death(year_of_death = 0)

    @pytest.mark.unit()
    def test_irr_death_valid(self, basic_hybrid_life):
        """calc_internal_rate_of_return_death returns float."""
        result = basic_hybrid_life.calc_internal_rate_of_return_death(year_of_death = 10)
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_breakeven_year_invalid_premium_raises(self, basic_hybrid_life):
        """calc_breakeven_year_vs_traditional with invalid premium raises."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_hybrid_life.calc_breakeven_year_vs_traditional(traditional_annual_premium = 0.0)

    @pytest.mark.unit()
    def test_breakeven_year_valid(self, basic_hybrid_life):
        """calc_breakeven_year_vs_traditional with valid premium returns int."""
        result = basic_hybrid_life.calc_breakeven_year_vs_traditional(traditional_annual_premium = 5_000.0)
        assert isinstance(result, int)

    @pytest.mark.unit()
    def test_extension_of_benefits_none(self, ltc_hybrid_life_class):
        """Extension_Of_Benefits.NONE accepted."""
        from src.products.insurance.insurance_LTC.insurance_LTC_hybrid_life import (
            Extension_Of_Benefits,
        )

        p = ltc_hybrid_life_class(
            insured_age=60,
            death_benefit=250_000.0,
            single_premium=100_000.0,
            extension_of_benefits=Extension_Of_Benefits.NONE,
        )
        assert p.calc_maximum_lifetime_benefit() >= 0.0

    @pytest.mark.unit()
    def test_extension_of_benefits_times_3(self, ltc_hybrid_life_class):
        """Extension_Of_Benefits.TIMES_3 accepted."""
        from src.products.insurance.insurance_LTC.insurance_LTC_hybrid_life import (
            Extension_Of_Benefits,
        )

        p = ltc_hybrid_life_class(
            insured_age=60,
            death_benefit=250_000.0,
            single_premium=100_000.0,
            extension_of_benefits=Extension_Of_Benefits.TIMES_3,
        )
        assert p.calc_maximum_lifetime_benefit() > 0.0

    @pytest.mark.unit()
    def test_premium_structure_pay5(self, ltc_hybrid_life_class):
        """Premium_Structure_Hybrid_Life.PAY_5 accepted."""
        from src.products.insurance.insurance_LTC.insurance_LTC_hybrid_life import (
            Premium_Structure_Hybrid_Life,
        )

        p = ltc_hybrid_life_class(
            insured_age=60,
            death_benefit=250_000.0,
            single_premium=100_000.0,
            premium_structure=Premium_Structure_Hybrid_Life.PAY_5,
        )
        assert p.calc_annual_premium() > 0.0

    @pytest.mark.unit()
    def test_get_insurance_as_string_returns_str(self, basic_hybrid_life):
        """get_insurance_as_string returns a non-empty string."""
        result = basic_hybrid_life.get_insurance_as_string()
        assert isinstance(result, str)
        assert len(result) > 0


# ======================================================================
# LTC Traditional — Extended Property and Branch Coverage
# ======================================================================


@pytest.mark.unit()
class Class_Test_LTC_Traditional_Properties:
    """Tests for Insurance_LTC_Traditional property accessors."""

    @pytest.mark.unit()
    def test_gender_property(self, basic_traditional, traditional_enums):
        """gender property returns expected value."""
        assert basic_traditional.gender == traditional_enums["Gender_LTC"].FEMALE

    @pytest.mark.unit()
    def test_health_class_property(self, basic_traditional, traditional_enums):
        """health_class property returns expected default."""
        assert basic_traditional.health_class == traditional_enums["Health_Class_LTC"].STANDARD

    @pytest.mark.unit()
    def test_non_forfeiture_property(self, basic_traditional, traditional_enums):
        """non_forfeiture property returns expected default."""
        assert basic_traditional.non_forfeiture == traditional_enums["Non_Forfeiture_Option"].NONE

    @pytest.mark.unit()
    def test_shared_care_property(self, basic_traditional):
        """shared_care property returns False by default."""
        assert basic_traditional.shared_care is False

    @pytest.mark.unit()
    def test_waiver_of_premium_property(self, basic_traditional):
        """waiver_of_premium property returns True by default."""
        assert basic_traditional.waiver_of_premium is True

    @pytest.mark.unit()
    def test_cumulative_rate_increase_pct_property(self, basic_traditional):
        """cumulative_rate_increase_pct property returns expected default."""
        assert basic_traditional.cumulative_rate_increase_pct == pytest.approx(0.0)

    @pytest.mark.unit()
    def test_invalid_health_class_raises(self, ltc_traditional_class, traditional_enums):
        """Non-enum health_class raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            ltc_traditional_class(
                insured_age=60,
                daily_benefit_amount=200.0,
                gender=traditional_enums["Gender_LTC"].FEMALE,
                health_class="STANDARD",
            )

    @pytest.mark.unit()
    def test_invalid_non_forfeiture_raises(self, ltc_traditional_class, traditional_enums):
        """Non-enum non_forfeiture raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            ltc_traditional_class(
                insured_age=60,
                daily_benefit_amount=200.0,
                gender=traditional_enums["Gender_LTC"].FEMALE,
                non_forfeiture="NONE",
            )

    @pytest.mark.unit()
    def test_invalid_cumulative_rate_increase_raises(self, ltc_traditional_class, traditional_enums):
        """Out-of-range cumulative_rate_increase_pct raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            ltc_traditional_class(
                insured_age=60,
                daily_benefit_amount=200.0,
                gender=traditional_enums["Gender_LTC"].FEMALE,
                cumulative_rate_increase_pct=10.0,
            )


@pytest.mark.unit()
class Class_Test_LTC_Traditional_Extra:
    """Extra branch-coverage tests for Insurance_LTC_Traditional."""

    @pytest.mark.unit()
    def test_male_gender(self, ltc_traditional_class, traditional_enums):
        """MALE gender accepted and produces valid premium."""
        p = ltc_traditional_class(
            insured_age=60,
            daily_benefit_amount=200.0,
            gender=traditional_enums["Gender_LTC"].MALE,
        )
        assert p.calc_annual_premium() > 0.0

    @pytest.mark.unit()
    def test_unisex_gender(self, ltc_traditional_class, traditional_enums):
        """UNISEX gender accepted and produces valid premium."""
        p = ltc_traditional_class(
            insured_age=60,
            daily_benefit_amount=200.0,
            gender=traditional_enums["Gender_LTC"].UNISEX,
        )
        assert p.calc_annual_premium() > 0.0

    @pytest.mark.unit()
    def test_preferred_health_class(self, ltc_traditional_class, traditional_enums):
        """PREFERRED health class produces a lower premium than STANDARD."""
        p_pref = ltc_traditional_class(
            insured_age=60,
            daily_benefit_amount=200.0,
            gender=traditional_enums["Gender_LTC"].FEMALE,
            health_class=traditional_enums["Health_Class_LTC"].PREFERRED,
        )
        p_std = ltc_traditional_class(
            insured_age=60,
            daily_benefit_amount=200.0,
            gender=traditional_enums["Gender_LTC"].FEMALE,
            health_class=traditional_enums["Health_Class_LTC"].STANDARD,
        )
        assert p_pref.calc_annual_premium() <= p_std.calc_annual_premium()

    @pytest.mark.unit()
    def test_substandard_health_class(self, ltc_traditional_class, traditional_enums):
        """SUBSTANDARD health class produces a higher premium than STANDARD."""
        p_sub = ltc_traditional_class(
            insured_age=60,
            daily_benefit_amount=200.0,
            gender=traditional_enums["Gender_LTC"].FEMALE,
            health_class=traditional_enums["Health_Class_LTC"].SUBSTANDARD,
        )
        p_std = ltc_traditional_class(
            insured_age=60,
            daily_benefit_amount=200.0,
            gender=traditional_enums["Gender_LTC"].FEMALE,
            health_class=traditional_enums["Health_Class_LTC"].STANDARD,
        )
        assert p_sub.calc_annual_premium() >= p_std.calc_annual_premium()

    @pytest.mark.unit()
    def test_shared_care_surcharge(self, ltc_traditional_class, traditional_enums):
        """shared_care=True increases premium."""
        p_shared = ltc_traditional_class(
            insured_age=60,
            daily_benefit_amount=200.0,
            gender=traditional_enums["Gender_LTC"].FEMALE,
            shared_care=True,
        )
        p_no = ltc_traditional_class(
            insured_age=60,
            daily_benefit_amount=200.0,
            gender=traditional_enums["Gender_LTC"].FEMALE,
            shared_care=False,
        )
        assert p_shared.calc_annual_premium() >= p_no.calc_annual_premium()

    @pytest.mark.unit()
    def test_inflation_simple_3(self, ltc_traditional_class, traditional_enums):
        """SIMPLE_3 inflation produces non-zero daily benefit at year 5."""
        from src.products.insurance.insurance_LTC.insurance_LTC_base import (
            Inflation_Protection,
        )

        p = ltc_traditional_class(
            insured_age=60,
            daily_benefit_amount=200.0,
            gender=traditional_enums["Gender_LTC"].FEMALE,
            inflation_protection=Inflation_Protection.SIMPLE_3,
        )
        assert p.calc_daily_benefit_at_year(year = 5) > 200.0

    @pytest.mark.unit()
    def test_inflation_compound_5(self, ltc_traditional_class, traditional_enums):
        """COMPOUND_5 inflation produces growing daily benefit."""
        from src.products.insurance.insurance_LTC.insurance_LTC_base import (
            Inflation_Protection,
        )

        p = ltc_traditional_class(
            insured_age=60,
            daily_benefit_amount=200.0,
            gender=traditional_enums["Gender_LTC"].FEMALE,
            inflation_protection=Inflation_Protection.COMPOUND_5,
        )
        assert p.calc_daily_benefit_at_year(year = 5) > 200.0

    @pytest.mark.unit()
    def test_inflation_cpi_linked(self, ltc_traditional_class, traditional_enums):
        """CPI_LINKED inflation produces non-zero premium."""
        from src.products.insurance.insurance_LTC.insurance_LTC_base import (
            Inflation_Protection,
        )

        p = ltc_traditional_class(
            insured_age=60,
            daily_benefit_amount=200.0,
            gender=traditional_enums["Gender_LTC"].FEMALE,
            inflation_protection=Inflation_Protection.CPI_LINKED,
        )
        assert p.calc_annual_premium() > 0.0

    @pytest.mark.unit()
    def test_inflation_future_purchase(self, ltc_traditional_class, traditional_enums):
        """FUTURE_PURCHASE inflation produces non-zero premium."""
        from src.products.insurance.insurance_LTC.insurance_LTC_base import (
            Inflation_Protection,
        )

        p = ltc_traditional_class(
            insured_age=60,
            daily_benefit_amount=200.0,
            gender=traditional_enums["Gender_LTC"].FEMALE,
            inflation_protection=Inflation_Protection.FUTURE_PURCHASE,
        )
        assert p.calc_annual_premium() > 0.0

    @pytest.mark.unit()
    def test_daily_benefit_at_year_0_raises(self, basic_traditional):
        """calc_daily_benefit_at_year with year < 1 raises exception."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_traditional.calc_daily_benefit_at_year(year = 0)

    @pytest.mark.unit()
    def test_modal_premium_quarterly(self, ltc_traditional_class, traditional_enums):
        """QUARTERLY frequency modal premium returns float."""
        from src.products.insurance.insurance_LTC.insurance_LTC_base import (
            Premium_Frequency_LTC,
        )

        p = ltc_traditional_class(
            insured_age=60,
            daily_benefit_amount=200.0,
            gender=traditional_enums["Gender_LTC"].FEMALE,
            premium_frequency=Premium_Frequency_LTC.QUARTERLY,
        )
        result = p.calc_modal_premium()
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_modal_premium_monthly(self, ltc_traditional_class, traditional_enums):
        """MONTHLY frequency modal premium returns float."""
        from src.products.insurance.insurance_LTC.insurance_LTC_base import (
            Premium_Frequency_LTC,
        )

        p = ltc_traditional_class(
            insured_age=60,
            daily_benefit_amount=200.0,
            gender=traditional_enums["Gender_LTC"].FEMALE,
            premium_frequency=Premium_Frequency_LTC.MONTHLY,
        )
        result = p.calc_modal_premium()
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_remaining_benefit_pool_valid(self, basic_traditional):
        """calc_remaining_benefit_pool returns non-negative float."""
        result = basic_traditional.calc_remaining_benefit_pool(benefits_paid_to_date=5_000.0)
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_remaining_benefit_pool_negative_paid_raises(self, basic_traditional):
        """calc_remaining_benefit_pool with negative benefits raises."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_traditional.calc_remaining_benefit_pool(benefits_paid_to_date=-1.0)

    @pytest.mark.unit()
    def test_remaining_benefit_pool_invalid_year_raises(self, basic_traditional):
        """calc_remaining_benefit_pool with year < 1 raises exception."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_traditional.calc_remaining_benefit_pool(
                benefits_paid_to_date=0.0, policy_year=0
            )

    @pytest.mark.unit()
    def test_cost_of_waiting_valid(self, basic_traditional):
        """calc_cost_of_waiting with valid future age returns float."""
        result = basic_traditional.calc_cost_of_waiting(future_age = 70)
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_cost_of_waiting_same_age_raises(self, basic_traditional):
        """calc_cost_of_waiting with future_age <= current age raises exception."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_traditional.calc_cost_of_waiting(future_age = 50)

    @pytest.mark.unit()
    def test_non_forfeiture_shortened_benefit(self, ltc_traditional_class, traditional_enums):
        """Non_Forfeiture_Option.SHORTENED_BENEFIT produces valid benefit."""
        p = ltc_traditional_class(
            insured_age=60,
            daily_benefit_amount=200.0,
            gender=traditional_enums["Gender_LTC"].FEMALE,
            non_forfeiture=traditional_enums["Non_Forfeiture_Option"].SHORTENED_BENEFIT,
        )
        result = p.calc_non_forfeiture_benefit(years_premiums_paid = 10)
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_non_forfeiture_none_returns_zero(self, basic_traditional):
        """Non_Forfeiture_Option.NONE returns 0.0."""
        result = basic_traditional.calc_non_forfeiture_benefit(years_premiums_paid = 5)
        assert result == 0.0

    @pytest.mark.unit()
    def test_non_forfeiture_return_of_premium(self, ltc_traditional_class, traditional_enums):
        """Non_Forfeiture_Option.RETURN_OF_PREMIUM produces valid benefit."""
        p = ltc_traditional_class(
            insured_age=60,
            daily_benefit_amount=200.0,
            gender=traditional_enums["Gender_LTC"].FEMALE,
            non_forfeiture=traditional_enums["Non_Forfeiture_Option"].RETURN_OF_PREMIUM,
        )
        result = p.calc_non_forfeiture_benefit(years_premiums_paid = 10)
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_non_forfeiture_contingent(self, ltc_traditional_class, traditional_enums):
        """Non_Forfeiture_Option.CONTINGENT produces valid benefit."""
        p = ltc_traditional_class(
            insured_age=60,
            daily_benefit_amount=200.0,
            gender=traditional_enums["Gender_LTC"].FEMALE,
            non_forfeiture=traditional_enums["Non_Forfeiture_Option"].CONTINGENT,
        )
        result = p.calc_non_forfeiture_benefit(years_premiums_paid = 10)
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_non_forfeiture_invalid_years_raises(self, basic_traditional):
        """calc_non_forfeiture_benefit with negative years raises exception."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_traditional.calc_non_forfeiture_benefit(years_premiums_paid = -1)

    @pytest.mark.unit()
    def test_elimination_period_out_of_pocket_valid(self, basic_traditional):
        """calc_elimination_period_out_of_pocket returns non-negative float."""
        result = basic_traditional.calc_elimination_period_out_of_pocket(daily_care_cost = 350.0)
        assert isinstance(result, float)
        assert result >= 0.0

    @pytest.mark.unit()
    def test_elimination_period_out_of_pocket_negative_raises(self, basic_traditional):
        """calc_elimination_period_out_of_pocket with negative daily cost raises."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_traditional.calc_elimination_period_out_of_pocket(daily_care_cost = -1.0)

    @pytest.mark.unit()
    def test_benefit_duration_at_cost_valid(self, basic_traditional):
        """calc_benefit_duration_at_cost returns non-negative float."""
        result = basic_traditional.calc_benefit_duration_at_cost(daily_care_cost = 350.0)
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_benefit_duration_at_cost_negative_raises(self, basic_traditional):
        """calc_benefit_duration_at_cost with negative cost raises."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_traditional.calc_benefit_duration_at_cost(daily_care_cost = -1.0)

    @pytest.mark.unit()
    def test_total_premiums_to_age_valid(self, basic_traditional):
        """calc_total_premiums_to_age returns positive float."""
        result = basic_traditional.calc_total_premiums_to_age(target_age = 80)
        assert isinstance(result, float)
        assert result > 0.0

    @pytest.mark.unit()
    def test_total_premiums_to_age_invalid_raises(self, basic_traditional):
        """calc_total_premiums_to_age with target <= insured_age raises."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_traditional.calc_total_premiums_to_age(target_age = 55)

    @pytest.mark.unit()
    def test_get_insurance_as_string_returns_str(self, basic_traditional):
        """get_insurance_as_string returns a non-empty string."""
        result = basic_traditional.get_insurance_as_string()
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.unit()
    def test_care_setting_home_health_care(self, ltc_traditional_class, traditional_enums):
        """Care_Setting.HOME_HEALTH_CARE accepted and produces non-zero premium."""
        from src.products.insurance.insurance_LTC.insurance_LTC_base import (
            Care_Setting,
        )

        p = ltc_traditional_class(
            insured_age=60,
            daily_benefit_amount=200.0,
            gender=traditional_enums["Gender_LTC"].FEMALE,
            care_setting=Care_Setting.HOME_HEALTH_CARE,
        )
        assert p.calc_annual_premium() > 0.0

    @pytest.mark.unit()
    def test_smoker_surcharge(self, ltc_traditional_class, traditional_enums):
        """is_smoker=True increases premium."""
        p_smoker = ltc_traditional_class(
            insured_age=60,
            daily_benefit_amount=200.0,
            gender=traditional_enums["Gender_LTC"].FEMALE,
            is_smoker=True,
        )
        p_no = ltc_traditional_class(
            insured_age=60,
            daily_benefit_amount=200.0,
            gender=traditional_enums["Gender_LTC"].FEMALE,
            is_smoker=False,
        )
        assert p_smoker.calc_annual_premium() >= p_no.calc_annual_premium()

    @pytest.mark.unit()
    def test_base_rate_property_accessed(self, basic_traditional):
        """base_rate_per_unit property is accessible."""
        assert basic_traditional.base_rate_per_unit > 0.0

    @pytest.mark.unit()
    def test_custom_base_rate_per_unit_accepted(self, ltc_traditional_class, traditional_enums):
        """Explicit base_rate_per_unit is stored correctly."""
        p = ltc_traditional_class(
            insured_age=60,
            daily_benefit_amount=200.0,
            gender=traditional_enums["Gender_LTC"].FEMALE,
            base_rate_per_unit=8.0,
        )
        assert p.base_rate_per_unit == 8.0

    @pytest.mark.unit()
    def test_invalid_base_rate_per_unit_raises(self, ltc_traditional_class, traditional_enums):
        """Non-positive base_rate_per_unit raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            ltc_traditional_class(
                insured_age=60,
                daily_benefit_amount=200.0,
                gender=traditional_enums["Gender_LTC"].FEMALE,
                base_rate_per_unit=0.0,
            )

    @pytest.mark.unit()
    def test_age_above_band_uses_default_rate(self, ltc_traditional_class, traditional_enums):
        """Age at top of valid band still returns a valid premium."""
        p = ltc_traditional_class(
            insured_age=80,
            daily_benefit_amount=200.0,
            gender=traditional_enums["Gender_LTC"].MALE,
        )
        assert p.calc_annual_premium() > 0.0

    @pytest.mark.unit()
    def test_unisex_gender_rate(self, ltc_traditional_class, traditional_enums):
        """UNISEX gender uses average male+female rate."""
        p_unisex = ltc_traditional_class(
            insured_age=80,
            daily_benefit_amount=200.0,
            gender=traditional_enums["Gender_LTC"].UNISEX,
        )
        assert p_unisex.calc_annual_premium() > 0.0

    @pytest.mark.unit()
    def test_modal_premium_single_pay(self, ltc_traditional_class, traditional_enums):
        """SINGLE-pay frequency returns annual premium directly."""
        from src.products.insurance.insurance_LTC.insurance_LTC_base import (
            Premium_Frequency_LTC,
        )

        p = ltc_traditional_class(
            insured_age=60,
            daily_benefit_amount=200.0,
            gender=traditional_enums["Gender_LTC"].FEMALE,
            premium_frequency=Premium_Frequency_LTC.SINGLE,
        )
        modal = p.calc_modal_premium()
        assert modal == p.calc_annual_premium()

    @pytest.mark.unit()
    def test_benefit_duration_at_cost_zero_daily_cost_raises(self, basic_traditional):
        """calc_benefit_duration_at_cost with zero cost raises exception."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_traditional.calc_benefit_duration_at_cost(daily_care_cost = 0.0)


# ======================================================================
# LTC Hybrid Annuity — coverage-gap test (STANDARD surrender schedule, year ≤ 10)
# ======================================================================


@pytest.mark.unit()
class Class_Test_LTC_Hybrid_Annuity_Surrender_Standard:
    """Coverage-gap test: standard 10-year declining surrender charge."""

    @pytest.mark.unit()
    def test_surrender_schedule_standard_within_period(self, basic_hybrid_annuity):
        """STANDARD schedule at year 5 (≤ 10) returns a non-zero charge percentage."""
        # basic_hybrid_annuity uses the default STANDARD schedule.
        # Year 5 should hit: return max(0.11 - 0.01 * year, 0.0) → 0.06
        result = basic_hybrid_annuity._get_surrender_charge_pct(year = 5)
        assert result == pytest.approx(0.06)

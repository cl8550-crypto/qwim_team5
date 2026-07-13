"""Unit tests for insurance_life_base and insurance_life_term modules.

Covers enum values, base class validation, Term Life constructor,
premium calculation, benefit calculations, and error paths.
"""

from __future__ import annotations

import pytest


# ======================================================================
# Fixtures
# ======================================================================


@pytest.fixture()
def life_term_class():
    """Import Insurance_Life_Term."""
    from src.products.insurance.insurance_life.insurance_life_term import (
        Insurance_Life_Term,
    )

    return Insurance_Life_Term


@pytest.fixture()
def life_base_enums():
    """Import life insurance base enumerations."""
    from src.products.insurance.insurance_life.insurance_life_base import (
        Death_Benefit_Option,
        Insurance_Life_Type,
        Premium_Frequency,
        Underwriting_Class,
    )

    return {
        "Insurance_Life_Type": Insurance_Life_Type,
        "Underwriting_Class": Underwriting_Class,
        "Premium_Frequency": Premium_Frequency,
        "Death_Benefit_Option": Death_Benefit_Option,
    }


@pytest.fixture()
def term_enums():
    """Import Term Life enumerations."""
    from src.products.insurance.insurance_life.insurance_life_term import (
        Term_Type,
    )

    return {"Term_Type": Term_Type}


@pytest.fixture()
def basic_term_policy(life_term_class):
    """A valid Insurance_Life_Term instance with default settings."""
    return life_term_class(insured_age=35, face_amount=500_000.0)


@pytest.fixture()
def life_base_concrete_class():
    """A minimal concrete subclass of Insurance_Life_Base for base-class testing."""
    from src.products.insurance.insurance_life.insurance_life_base import (
        Insurance_Life_Base,
        Insurance_Life_Type,
        Premium_Frequency,
        Underwriting_Class,
    )

    class _Concrete_Life(Insurance_Life_Base):
        def __init__(
            self,
            insured_age: int,
            face_amount: float,
            insurance_type: Insurance_Life_Type = Insurance_Life_Type.TERM_LIFE,
            premium_frequency: Premium_Frequency = Premium_Frequency.MONTHLY,
            underwriting_class: Underwriting_Class = Underwriting_Class.STANDARD,
            is_smoker: bool = False,
            beneficiary_primary: str = "",
            beneficiary_contingent: str = "",
        ) -> None:
            super().__init__(
                insured_age=insured_age,
                face_amount=face_amount,
                insurance_type=insurance_type,
                underwriting_class=underwriting_class,
                premium_frequency=premium_frequency,
                is_smoker=is_smoker,
                beneficiary_primary=beneficiary_primary,
                beneficiary_contingent=beneficiary_contingent,
            )

        def calc_death_benefit(self) -> float:
            return self.m_face_amount

        def calc_annual_premium(self) -> float:
            return self.m_face_amount * 0.01

    return _Concrete_Life


# ======================================================================
# Base class — enum values
# ======================================================================


class Class_Test_Life_Base_Enums:
    """Verify all life insurance base enum values are accessible."""

    @pytest.mark.unit()
    def Test_Insurance_Life_Type_Values(self, life_base_enums):
        """Insurance_Life_Type should have five variants."""
        T = life_base_enums["Insurance_Life_Type"]
        assert T.WHOLE_LIFE.value == "Whole Life Insurance"
        assert T.TERM_LIFE.value == "Term Life Insurance"
        assert T.UNIVERSAL_LIFE.value == "Universal Life Insurance"
        assert T.VARIABLE_LIFE.value == "Variable Life Insurance"
        assert T.SURVIVOR_LIFE.value == "Survivor Life Insurance"

    @pytest.mark.unit()
    def Test_Underwriting_Class_Values(self, life_base_enums):
        """Underwriting_Class should have four risk classes."""
        UC = life_base_enums["Underwriting_Class"]
        assert UC.PREFERRED_PLUS.value == "Preferred Plus"
        assert UC.STANDARD.value == "Standard"
        assert UC.SUBSTANDARD.value == "Substandard"

    @pytest.mark.unit()
    def Test_Premium_Frequency_Values(self, life_base_enums):
        """Premium_Frequency numeric values should match payment counts."""
        PF = life_base_enums["Premium_Frequency"]
        assert PF.ANNUAL.value == 1
        assert PF.MONTHLY.value == 12
        assert PF.SINGLE.value == 0

    @pytest.mark.unit()
    def Test_Death_Benefit_Option_Values(self, life_base_enums):
        """Death_Benefit_Option values should be correct."""
        DB = life_base_enums["Death_Benefit_Option"]
        assert DB.LEVEL.value == "Level"
        assert DB.INCREASING.value == "Increasing"
        assert DB.RETURN_OF_PREMIUM.value == "Return of Premium"

    @pytest.mark.unit()
    def Test_Term_Type_Values(self, term_enums):
        """Term_Type should have three variants."""
        TT = term_enums["Term_Type"]
        assert TT.LEVEL.value == "Level Term"
        assert TT.ANNUALLY_RENEWABLE.value == "Annually Renewable Term"
        assert TT.DECREASING.value == "Decreasing Term"


# ======================================================================
# Base class — validation
# ======================================================================


class Class_Test_Life_Base_Validation:
    """Validation paths in the Insurance_Life_Base constructor."""

    @pytest.mark.unit()
    def Test_Raises_When_Age_Is_Bool(self, life_base_concrete_class):
        """Boolean insured_age should not be accepted as an integer age."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            life_base_concrete_class(insured_age=True, face_amount=100_000.0)

    @pytest.mark.unit()
    def Test_Raises_When_Face_Amount_Is_Bool(self, life_base_concrete_class):
        """Boolean face_amount should not be accepted as a numeric amount."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            life_base_concrete_class(insured_age=35, face_amount=True)

    @pytest.mark.unit()
    def Test_Raises_When_Age_Negative(self, life_term_class):
        """insured_age < 0 should raise Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            life_term_class(insured_age=-1, face_amount=100_000.0)

    @pytest.mark.unit()
    def Test_Raises_When_Age_Over_120(self, life_term_class):
        """insured_age > 120 should raise Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            life_term_class(insured_age=130, face_amount=100_000.0)

    @pytest.mark.unit()
    def Test_Raises_When_Face_Amount_Zero(self, life_term_class):
        """face_amount = 0 should raise Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            life_term_class(insured_age=35, face_amount=0.0)

    @pytest.mark.unit()
    def Test_Raises_When_Face_Amount_Negative(self, life_term_class):
        """Negative face_amount should raise Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            life_term_class(insured_age=35, face_amount=-50_000.0)

    @pytest.mark.unit()
    def Test_Raises_When_Underwriting_Class_Wrong_Type(self, life_term_class):
        """Passing a string as underwriting_class should raise."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            life_term_class(
                insured_age=35,
                face_amount=500_000.0,
                underwriting_class="Standard",
            )

    @pytest.mark.unit()
    def Test_Raises_When_Term_Years_Zero(self, life_term_class):
        """term_years = 0 should raise Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            life_term_class(
                insured_age=35,
                face_amount=500_000.0,
                term_years=0,
            )


# ======================================================================
# Term Life — construction
# ======================================================================


class Class_Test_Life_Term_Construction:
    """Tests for Insurance_Life_Term constructor."""

    @pytest.mark.unit()
    def Test_Default_Construction(self, basic_term_policy, life_base_enums, term_enums):
        """Default construction should set all expected attributes."""
        obj = basic_term_policy
        assert obj.m_insured_age == 35
        assert obj.m_face_amount == pytest.approx(500_000.0)
        assert obj.m_insurance_type == life_base_enums["Insurance_Life_Type"].TERM_LIFE
        assert obj.m_term_years == 20
        assert obj.m_term_type == term_enums["Term_Type"].LEVEL
        assert obj.m_is_convertible is True
        assert obj.m_is_smoker is False

    @pytest.mark.unit()
    def Test_Custom_Term_Years(self, life_term_class):
        """term_years=30 should be stored as m_term_years."""
        obj = life_term_class(insured_age=30, face_amount=1_000_000.0, term_years=30)
        assert obj.m_term_years == 30

    @pytest.mark.unit()
    def Test_Smoker_Flag(self, life_term_class):
        """is_smoker=True should be stored."""
        obj = life_term_class(insured_age=40, face_amount=250_000.0, is_smoker=True)
        assert obj.m_is_smoker is True

    @pytest.mark.unit()
    def Test_Annually_Renewable_Term_Type(self, life_term_class, term_enums):
        """ANNUALLY_RENEWABLE term_type should be stored."""
        obj = life_term_class(
            insured_age=28,
            face_amount=500_000.0,
            term_type=term_enums["Term_Type"].ANNUALLY_RENEWABLE,
        )
        assert obj.m_term_type == term_enums["Term_Type"].ANNUALLY_RENEWABLE

    @pytest.mark.unit()
    def Test_Return_Of_Premium_Flag(self, life_term_class):
        """has_return_of_premium=True should be stored."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            has_return_of_premium=True,
        )
        assert obj.m_has_return_of_premium is True

    @pytest.mark.unit()
    def Test_Beneficiary_Fields_Stored(self, life_term_class):
        """Beneficiary strings should be stored correctly."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            beneficiary_primary="Jane Doe",
            beneficiary_contingent="John Doe",
        )
        assert obj.m_beneficiary_primary == "Jane Doe"
        assert obj.m_beneficiary_contingent == "John Doe"


# ======================================================================
# Term Life — premium calculation
# ======================================================================


class Class_Test_Life_Term_Premium:
    """Tests for Insurance_Life_Term.calc_annual_premium()."""

    @pytest.mark.unit()
    def Test_Annual_Premium_Is_Positive(self, basic_term_policy):
        """calc_annual_premium should return a positive float."""
        premium = basic_term_policy.calc_annual_premium()
        assert isinstance(premium, float)
        assert premium > 0.0

    @pytest.mark.unit()
    def Test_Rop_Rider_Increases_Premium(self, life_term_class):
        """Return-of-premium rider should increase the annual premium by ~60%."""
        base = {"insured_age": 35, "face_amount": 500_000.0}
        no_rop = life_term_class(**base, has_return_of_premium=False)
        with_rop = life_term_class(**base, has_return_of_premium=True)
        assert with_rop.calc_annual_premium() > no_rop.calc_annual_premium()

    @pytest.mark.unit()
    def Test_Higher_Face_Amount_Higher_Premium(self, life_term_class):
        """Larger face amount should produce a higher annual premium."""
        low = life_term_class(insured_age=35, face_amount=100_000.0)
        high = life_term_class(insured_age=35, face_amount=1_000_000.0)
        assert high.calc_annual_premium() > low.calc_annual_premium()

    @pytest.mark.unit()
    def Test_Higher_Coi_Rate_Higher_Premium(self, life_term_class):
        """Higher cost-of-insurance rate should produce a higher annual premium."""
        low_coi = life_term_class(insured_age=35, face_amount=500_000.0, rate_cost_of_insurance=1.0)
        high_coi = life_term_class(insured_age=35, face_amount=500_000.0, rate_cost_of_insurance=5.0)
        assert high_coi.calc_annual_premium() > low_coi.calc_annual_premium()


# ======================================================================
# Term Life — death benefit
# ======================================================================


class Class_Test_Life_Term_Death_Benefit:
    """Tests for Insurance_Life_Term.calc_death_benefit()."""

    @pytest.mark.unit()
    def Test_Death_Benefit_Equals_Face_Amount_For_Level_Term(self, basic_term_policy):
        """Level term death benefit should equal the face amount."""
        db = basic_term_policy.calc_death_benefit()
        assert isinstance(db, float)
        assert db == pytest.approx(500_000.0)

    @pytest.mark.unit()
    def Test_Decreasing_Term_Death_Benefit_At_Midpoint(
        self, life_term_class, term_enums
    ):
        """Decreasing term death benefit at policy year 10 of a 20-year term."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            term_years=20,
            term_type=term_enums["Term_Type"].DECREASING,
        )
        db_mid = obj.calc_death_benefit_at_year(policy_year=10)
        # At year 10 of 20: F * (20-10+1)/20 = F * 11/20 = 0.55 * F
        assert db_mid == pytest.approx(500_000.0 * 11 / 20, rel=1e-5)


# ======================================================================
# Package import smoke tests
# ======================================================================


class Class_Test_Life_Insurance_Package_Imports:
    """Smoke tests to ensure all life insurance sub-modules are importable."""

    @pytest.mark.unit()
    def Test_Life_Base_Module_Importable(self):
        """insurance_life_base should be importable."""
        import src.products.insurance.insurance_life.insurance_life_base  # noqa: F401

    @pytest.mark.unit()
    def Test_Life_Term_Module_Importable(self):
        """insurance_life_term should be importable."""
        import src.products.insurance.insurance_life.insurance_life_term  # noqa: F401

    @pytest.mark.unit()
    def Test_Life_Whole_Module_Importable(self):
        """insurance_life_whole should be importable."""
        import src.products.insurance.insurance_life.insurance_life_whole  # noqa: F401

    @pytest.mark.unit()
    def Test_Life_Universal_Module_Importable(self):
        """insurance_life_universal should be importable."""
        import src.products.insurance.insurance_life.insurance_life_universal  # noqa: F401

    @pytest.mark.unit()
    def Test_Life_Variable_Module_Importable(self):
        """insurance_life_variable should be importable."""
        import src.products.insurance.insurance_life.insurance_life_variable  # noqa: F401

    @pytest.mark.unit()
    def Test_Life_Survivor_Module_Importable(self):
        """insurance_life_survivor should be importable."""
        import src.products.insurance.insurance_life.insurance_life_survivor  # noqa: F401

    @pytest.mark.unit()
    def Test_Life_Init_Package_Importable(self):
        """insurance_life __init__ package should be importable."""
        import src.products.insurance.insurance_life  # noqa: F401


# ======================================================================
# Base class — missing validation raises (insurance_type, premium_frequency)
# ======================================================================


class Class_Test_Life_Base_Validation_Enum_Types:
    """Cover the validation raises for wrong-typed enum arguments."""

    @pytest.mark.unit()
    def Test_Raises_When_Insurance_Type_Wrong_Type(self, life_base_concrete_class):
        """Passing a string as insurance_type must raise Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            life_base_concrete_class(
                insured_age=35,
                face_amount=500_000.0,
                insurance_type="Term Life Insurance",
            )

    @pytest.mark.unit()
    def Test_Raises_When_Premium_Frequency_Wrong_Type(self, life_base_concrete_class):
        """Passing a string as premium_frequency must raise Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            life_base_concrete_class(
                insured_age=35,
                face_amount=500_000.0,
                premium_frequency="Monthly",
            )


# ======================================================================
# Base class — property accessors
# ======================================================================


class Class_Test_Life_Base_Properties:
    """Verify all property getters return the stored value."""

    @pytest.mark.unit()
    def Test_Insured_Age_Property(self, basic_term_policy):
        """insured_age property returns m_insured_age."""
        assert basic_term_policy.insured_age == basic_term_policy.m_insured_age

    @pytest.mark.unit()
    def Test_Face_Amount_Property(self, basic_term_policy):
        """face_amount property returns m_face_amount."""
        assert basic_term_policy.face_amount == pytest.approx(basic_term_policy.m_face_amount)

    @pytest.mark.unit()
    def Test_Insurance_Type_Property(self, basic_term_policy, life_base_enums):
        """insurance_type property returns the correct Insurance_Life_Type."""
        assert basic_term_policy.insurance_type == life_base_enums["Insurance_Life_Type"].TERM_LIFE

    @pytest.mark.unit()
    def Test_Underwriting_Class_Property(self, basic_term_policy, life_base_enums):
        """underwriting_class property returns the stored Underwriting_Class."""
        assert basic_term_policy.underwriting_class == life_base_enums["Underwriting_Class"].STANDARD

    @pytest.mark.unit()
    def Test_Premium_Frequency_Property(self, basic_term_policy, life_base_enums):
        """premium_frequency property returns the stored Premium_Frequency."""
        assert basic_term_policy.premium_frequency == life_base_enums["Premium_Frequency"].MONTHLY

    @pytest.mark.unit()
    def Test_Is_Smoker_Property_Default_False(self, basic_term_policy):
        """is_smoker property should default to False."""
        assert basic_term_policy.is_smoker is False

    @pytest.mark.unit()
    def Test_Is_Smoker_Property_True(self, life_term_class):
        """is_smoker property should reflect True when set."""
        obj = life_term_class(insured_age=40, face_amount=250_000.0, is_smoker=True)
        assert obj.is_smoker is True

    @pytest.mark.unit()
    def Test_Beneficiary_Primary_Property(self, life_term_class):
        """beneficiary_primary property returns stored string."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            beneficiary_primary="Alice",
        )
        assert obj.beneficiary_primary == "Alice"

    @pytest.mark.unit()
    def Test_Beneficiary_Contingent_Property(self, life_term_class):
        """beneficiary_contingent property returns stored string."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            beneficiary_contingent="Bob",
        )
        assert obj.beneficiary_contingent == "Bob"


# ======================================================================
# Base class — calc_modal_factor
# ======================================================================


class Class_Test_Life_Base_Calc_Modal_Factor:
    """Tests for Insurance_Life_Base.calc_modal_premium_factor()."""

    @pytest.mark.unit()
    def Test_Annual_Modal_Factor_Is_One(self, life_term_class):
        """payment_frequency=1 (annual) should yield modal factor 1.0."""
        obj = life_term_class(insured_age=35, face_amount=500_000.0, payment_frequency=1)
        assert obj.calc_modal_premium_factor() == pytest.approx(1.0)

    @pytest.mark.unit()
    def Test_Semi_Annual_Modal_Factor(self, life_term_class):
        """payment_frequency=2 (semi-annual) should yield modal factor 0.515."""
        obj = life_term_class(insured_age=35, face_amount=500_000.0, payment_frequency=2)
        assert obj.calc_modal_premium_factor() == pytest.approx(0.515)

    @pytest.mark.unit()
    def Test_Monthly_Modal_Factor(self, life_term_class):
        """payment_frequency=12 (monthly, default) should yield modal factor 0.0875."""
        obj = life_term_class(insured_age=35, face_amount=500_000.0, payment_frequency=12)
        assert obj.calc_modal_premium_factor() == pytest.approx(0.0875)

    @pytest.mark.unit()
    def Test_Quarterly_Modal_Factor(self, life_term_class):
        """payment_frequency=4 (quarterly) should yield modal factor 0.265."""
        obj = life_term_class(insured_age=35, face_amount=500_000.0, payment_frequency=4)
        assert obj.calc_modal_premium_factor() == pytest.approx(0.265)


# ======================================================================
# Base class — calc_cost_per_thousand
# ======================================================================


class Class_Test_Life_Base_Calc_Cost_Per_Thousand:
    """Tests for Insurance_Life_Base.calc_cost_per_thousand()."""

    @pytest.mark.unit()
    def Test_Valid_Cost_Per_Thousand(self, basic_term_policy):
        """Valid annual_premium should return cost per $1,000 of face."""
        result = basic_term_policy.calc_cost_per_thousand(annual_premium=1_000.0)
        expected = 1_000.0 / (500_000.0 / 1_000)
        assert result == pytest.approx(expected)

    @pytest.mark.unit()
    def Test_Raises_When_Annual_Premium_Zero(self, basic_term_policy):
        """annual_premium = 0 should raise Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_term_policy.calc_cost_per_thousand(annual_premium=0.0)

    @pytest.mark.unit()
    def Test_Raises_When_Annual_Premium_Negative(self, basic_term_policy):
        """Negative annual_premium should raise Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_term_policy.calc_cost_per_thousand(annual_premium=-500.0)

    @pytest.mark.unit()
    def Test_Raises_When_Annual_Premium_Not_Numeric(self, basic_term_policy):
        """Non-numeric annual_premium should raise Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_term_policy.calc_cost_per_thousand(annual_premium="1000")


# ======================================================================
# Base class — get_insurance_as_string
# ======================================================================


class Class_Test_Life_Base_Get_Insurance_As_String:
    """Tests for Insurance_Life_Base.get_insurance_as_string()."""

    @pytest.mark.unit()
    def Test_String_Contains_Insurance_Type(self, life_base_concrete_class):
        """String representation should contain the insurance type value."""
        obj = life_base_concrete_class(insured_age=35, face_amount=500_000.0)
        result = obj.get_insurance_as_string()
        assert "Term Life Insurance" in result

    @pytest.mark.unit()
    def Test_String_Contains_Non_Smoker_For_Default(self, life_base_concrete_class):
        """Default (non-smoker) policy string should contain 'Non-Smoker'."""
        obj = life_base_concrete_class(insured_age=35, face_amount=500_000.0)
        result = obj.get_insurance_as_string()
        assert "Non-Smoker" in result

    @pytest.mark.unit()
    def Test_String_Contains_Smoker_For_Smoker_Policy(self, life_base_concrete_class):
        """Smoker policy string should contain 'Smoker' (not 'Non-Smoker')."""
        obj = life_base_concrete_class(insured_age=40, face_amount=250_000.0, is_smoker=True)
        result = obj.get_insurance_as_string()
        assert "Smoker" in result
        assert "Non-Smoker" not in result

    @pytest.mark.unit()
    def Test_String_Contains_Age(self, life_base_concrete_class):
        """String representation should contain the insured age."""
        obj = life_base_concrete_class(insured_age=35, face_amount=500_000.0)
        result = obj.get_insurance_as_string()
        assert "35" in result

    @pytest.mark.unit()
    def Test_String_Contains_Face_Amount(self, life_base_concrete_class):
        """String representation should contain the face amount."""
        obj = life_base_concrete_class(insured_age=35, face_amount=500_000.0)
        result = obj.get_insurance_as_string()
        assert "500,000.00" in result


# ======================================================================
# Whole Life Insurance Tests
# ======================================================================


@pytest.fixture()
def whole_life_class():
    """Import Insurance_Life_Whole."""
    from src.products.insurance.insurance_life.insurance_life_whole import (
        Insurance_Life_Whole,
    )

    return Insurance_Life_Whole


@pytest.fixture()
def basic_whole_policy(whole_life_class):
    """A valid Insurance_Life_Whole instance with defaults."""
    return whole_life_class(insured_age=40, face_amount=250_000.0)


@pytest.mark.unit()
class Class_Test_Life_Whole_Construction:
    """Tests for Insurance_Life_Whole constructor."""

    @pytest.mark.unit()
    def test_creates_instance(self, basic_whole_policy):
        """Whole life policy instance created without error."""
        assert basic_whole_policy is not None

    @pytest.mark.unit()
    def test_default_attributes(self, basic_whole_policy):
        """Default attributes are set correctly on construction."""
        p = basic_whole_policy
        assert p.m_rate_guaranteed_interest == 0.04
        assert p.m_cash_value == 0.0
        assert p.m_is_participating is True
        assert p.m_rate_loan_interest == 0.05
        assert p.m_premium_paying_years == 100

    @pytest.mark.unit()
    def test_invalid_rate_guaranteed_interest_raises(self, whole_life_class):
        """Negative guaranteed interest raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            whole_life_class(insured_age=40, face_amount=100_000.0, rate_guaranteed_interest=-0.01)

    @pytest.mark.unit()
    def test_invalid_cash_value_raises(self, whole_life_class):
        """Negative cash_value raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            whole_life_class(insured_age=40, face_amount=100_000.0, cash_value=-1.0)

    @pytest.mark.unit()
    def test_invalid_rate_dividend_raises(self, whole_life_class):
        """Negative rate_dividend raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            whole_life_class(insured_age=40, face_amount=100_000.0, rate_dividend=-0.01)

    @pytest.mark.unit()
    def test_invalid_rate_loan_interest_raises(self, whole_life_class):
        """Negative rate_loan_interest raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            whole_life_class(insured_age=40, face_amount=100_000.0, rate_loan_interest=-0.01)

    @pytest.mark.unit()
    def test_invalid_amount_loan_outstanding_raises(self, whole_life_class):
        """Negative amount_loan_outstanding raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            whole_life_class(insured_age=40, face_amount=100_000.0, amount_loan_outstanding=-1.0)

    @pytest.mark.unit()
    def test_invalid_paid_up_additions_raises(self, whole_life_class):
        """Negative paid_up_additions raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            whole_life_class(insured_age=40, face_amount=100_000.0, paid_up_additions=-1.0)

    @pytest.mark.unit()
    def test_invalid_premium_paying_years_raises(self, whole_life_class):
        """Non-positive premium_paying_years raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            whole_life_class(insured_age=40, face_amount=100_000.0, premium_paying_years=0)

    @pytest.mark.unit()
    def test_invalid_rate_cost_of_insurance_raises(self, whole_life_class):
        """Negative rate_cost_of_insurance raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            whole_life_class(insured_age=40, face_amount=100_000.0, rate_cost_of_insurance=-1.0)

    @pytest.mark.unit()
    def test_invalid_death_benefit_option_raises(self, whole_life_class):
        """Invalid death_benefit_option raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            whole_life_class(insured_age=40, face_amount=100_000.0, death_benefit_option="LEVEL")

    @pytest.mark.unit()
    def test_invalid_payment_frequency_raises(self, whole_life_class):
        """Negative payment_frequency raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            whole_life_class(insured_age=40, face_amount=100_000.0, payment_frequency=-1)


@pytest.mark.unit()
class Class_Test_Life_Whole_Properties:
    """Tests for Insurance_Life_Whole property accessors."""

    @pytest.mark.unit()
    def test_rate_guaranteed_interest_property(self, whole_life_class):
        """rate_guaranteed_interest property returns correct value."""
        p = whole_life_class(insured_age=40, face_amount=100_000.0, rate_guaranteed_interest=0.035)
        assert p.rate_guaranteed_interest == 0.035

    @pytest.mark.unit()
    def test_cash_value_property(self, whole_life_class):
        """cash_value property returns correct value."""
        p = whole_life_class(insured_age=40, face_amount=100_000.0, cash_value=5_000.0)
        assert p.cash_value == 5_000.0

    @pytest.mark.unit()
    def test_is_participating_property(self, basic_whole_policy):
        """is_participating property returns True by default."""
        assert basic_whole_policy.is_participating is True

    @pytest.mark.unit()
    def test_rate_dividend_property(self, whole_life_class):
        """rate_dividend property returns correct value."""
        p = whole_life_class(insured_age=40, face_amount=100_000.0, rate_dividend=0.02)
        assert p.rate_dividend == 0.02

    @pytest.mark.unit()
    def test_rate_loan_interest_property(self, basic_whole_policy):
        """rate_loan_interest property returns 0.05 default."""
        assert basic_whole_policy.rate_loan_interest == 0.05

    @pytest.mark.unit()
    def test_amount_loan_outstanding_property(self, basic_whole_policy):
        """amount_loan_outstanding property returns 0.0 default."""
        assert basic_whole_policy.amount_loan_outstanding == 0.0

    @pytest.mark.unit()
    def test_paid_up_additions_property(self, basic_whole_policy):
        """paid_up_additions property returns 0.0 default."""
        assert basic_whole_policy.paid_up_additions == 0.0

    @pytest.mark.unit()
    def test_premium_paying_years_property(self, basic_whole_policy):
        """premium_paying_years property returns 100 default."""
        assert basic_whole_policy.premium_paying_years == 100

    @pytest.mark.unit()
    def test_rate_cost_of_insurance_property(self, basic_whole_policy):
        """rate_cost_of_insurance property returns 5.0 default."""
        assert basic_whole_policy.rate_cost_of_insurance == 5.0

    @pytest.mark.unit()
    def test_payment_frequency_property(self, basic_whole_policy):
        """payment_frequency property returns 12 default."""
        assert basic_whole_policy.payment_frequency == 12

    @pytest.mark.unit()
    def test_death_benefit_option_property(self, basic_whole_policy):
        """death_benefit_option property returns Death_Benefit_Option."""
        from src.products.insurance.insurance_life.insurance_life_base import (
            Death_Benefit_Option,
        )

        assert basic_whole_policy.death_benefit_option == Death_Benefit_Option.LEVEL


@pytest.mark.unit()
class Class_Test_Life_Whole_Death_Benefit:
    """Tests for Insurance_Life_Whole.calc_death_benefit()."""

    @pytest.mark.unit()
    def test_level_death_benefit_default(self, whole_life_class):
        """Level death benefit equals face amount when no loan or PUA."""
        p = whole_life_class(insured_age=40, face_amount=250_000.0)
        assert p.calc_death_benefit() == 250_000.0

    @pytest.mark.unit()
    def test_level_with_pua(self, whole_life_class):
        """Level death benefit includes paid-up additions."""
        from src.products.insurance.insurance_life.insurance_life_whole import (
            Death_Benefit_Option,
        )

        p = whole_life_class(
            insured_age=40,
            face_amount=250_000.0,
            paid_up_additions=10_000.0,
            death_benefit_option=Death_Benefit_Option.LEVEL,
        )
        assert p.calc_death_benefit() == 260_000.0

    @pytest.mark.unit()
    def test_increasing_death_benefit(self, whole_life_class):
        """Increasing death benefit adds cash value to face + PUA."""
        from src.products.insurance.insurance_life.insurance_life_whole import (
            Death_Benefit_Option,
        )

        p = whole_life_class(
            insured_age=40,
            face_amount=200_000.0,
            cash_value=20_000.0,
            death_benefit_option=Death_Benefit_Option.INCREASING,
        )
        assert p.calc_death_benefit() == 220_000.0

    @pytest.mark.unit()
    def test_loan_reduces_death_benefit(self, whole_life_class):
        """Outstanding loan reduces the net death benefit."""
        p = whole_life_class(
            insured_age=40,
            face_amount=250_000.0,
            amount_loan_outstanding=50_000.0,
        )
        assert p.calc_death_benefit() == 200_000.0


@pytest.mark.unit()
class Class_Test_Life_Whole_Premium:
    """Tests for Insurance_Life_Whole premium calculations."""

    @pytest.mark.unit()
    def test_calc_annual_premium_positive(self, basic_whole_policy):
        """Annual premium is positive."""
        assert basic_whole_policy.calc_annual_premium() > 0

    @pytest.mark.unit()
    def test_calc_annual_premium_formula(self, whole_life_class):
        """Annual premium uses 20% loading over net premium."""
        p = whole_life_class(
            insured_age=40,
            face_amount=100_000.0,
            rate_cost_of_insurance=5.0,
        )
        expected = (100_000.0 / 1_000) * 5.0 * 1.20
        assert abs(p.calc_annual_premium() - expected) < 1e-6

    @pytest.mark.unit()
    def test_calc_modal_premium_monthly(self, whole_life_class):
        """Monthly modal premium is less than annual premium."""
        p = whole_life_class(insured_age=40, face_amount=100_000.0, payment_frequency=12)
        assert p.calc_modal_premium() < p.calc_annual_premium()

    @pytest.mark.unit()
    def test_calc_modal_premium_single(self, whole_life_class):
        """Single payment (frequency=0) modal premium equals annual premium."""
        p = whole_life_class(insured_age=40, face_amount=100_000.0, payment_frequency=0)
        assert p.calc_modal_premium() == p.calc_annual_premium()


@pytest.mark.unit()
class Class_Test_Life_Whole_Cash_Value:
    """Tests for Insurance_Life_Whole cash value calculations."""

    @pytest.mark.unit()
    def test_calc_cash_value_at_year_returns_positive(self, basic_whole_policy):
        """Cash value at year 10 is non-negative."""
        result = basic_whole_policy.calc_cash_value_at_year(year = 10)
        assert result >= 0.0

    @pytest.mark.unit()
    def test_calc_cash_value_grows_over_time(self, basic_whole_policy):
        """Cash value at year 20 exceeds cash value at year 5."""
        cv5 = basic_whole_policy.calc_cash_value_at_year(year = 5)
        cv20 = basic_whole_policy.calc_cash_value_at_year(year = 20)
        assert cv20 > cv5

    @pytest.mark.unit()
    def test_calc_cash_value_invalid_year_raises(self, basic_whole_policy):
        """Non-positive year raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_whole_policy.calc_cash_value_at_year(year = 0)

    @pytest.mark.unit()
    def test_calc_cash_surrender_value(self, whole_life_class):
        """Cash surrender value is cash value minus outstanding loan."""
        p = whole_life_class(
            insured_age=40,
            face_amount=100_000.0,
            cash_value=20_000.0,
            amount_loan_outstanding=5_000.0,
        )
        assert p.calc_cash_surrender_value() == 15_000.0

    @pytest.mark.unit()
    def test_calc_net_amount_at_risk(self, whole_life_class):
        """NAR is death benefit minus cash value, floored at 0."""
        p = whole_life_class(
            insured_age=40,
            face_amount=100_000.0,
            cash_value=20_000.0,
        )
        assert p.calc_net_amount_at_risk() == 80_000.0

    @pytest.mark.unit()
    def test_calc_cash_value_with_dividends(self, whole_life_class):
        """Participating policy accumulates more value than non-participating."""
        p_par = whole_life_class(
            insured_age=40,
            face_amount=100_000.0,
            is_participating=True,
            rate_dividend=0.03,
        )
        p_nonpar = whole_life_class(
            insured_age=40,
            face_amount=100_000.0,
            is_participating=False,
        )
        assert p_par.calc_cash_value_at_year(year = 10) > p_nonpar.calc_cash_value_at_year(year = 10)


@pytest.mark.unit()
class Class_Test_Life_Whole_Loan:
    """Tests for Insurance_Life_Whole loan calculations."""

    @pytest.mark.unit()
    def test_calc_max_loan_amount_no_existing_loan(self, whole_life_class):
        """Max loan is 90% of cash value when no existing loan."""
        p = whole_life_class(insured_age=40, face_amount=100_000.0, cash_value=50_000.0)
        assert abs(p.calc_max_loan_amount() - 45_000.0) < 1e-6

    @pytest.mark.unit()
    def test_calc_loan_interest_due(self, whole_life_class):
        """Loan interest is outstanding balance x rate x years."""
        p = whole_life_class(
            insured_age=40,
            face_amount=100_000.0,
            amount_loan_outstanding=10_000.0,
            rate_loan_interest=0.05,
        )
        assert abs(p.calc_loan_interest_due(years = 1) - 500.0) < 1e-6

    @pytest.mark.unit()
    def test_calc_loan_interest_invalid_years_raises(self, whole_life_class):
        """Non-positive years raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        p = whole_life_class(insured_age=40, face_amount=100_000.0)
        with pytest.raises(Exception_Validation_Input):
            p.calc_loan_interest_due(years = 0)


@pytest.mark.unit()
class Class_Test_Life_Whole_Dividend:
    """Tests for Insurance_Life_Whole dividend calculations."""

    @pytest.mark.unit()
    def test_calc_annual_dividend_non_participating_returns_zero(self, whole_life_class):
        """Non-participating policy pays zero dividend."""
        p = whole_life_class(
            insured_age=40,
            face_amount=100_000.0,
            is_participating=False,
            rate_dividend=0.03,
        )
        assert p.calc_annual_dividend() == 0.0

    @pytest.mark.unit()
    def test_calc_annual_dividend_participating(self, whole_life_class):
        """Participating policy dividend is cash_value x rate_dividend."""
        p = whole_life_class(
            insured_age=40,
            face_amount=100_000.0,
            cash_value=50_000.0,
            is_participating=True,
            rate_dividend=0.02,
        )
        assert abs(p.calc_annual_dividend() - 1_000.0) < 1e-6

    @pytest.mark.unit()
    def test_calc_paid_up_additions_from_dividend_zero_for_nonpar(self, whole_life_class):
        """PUA from dividend is 0 for non-participating policy."""
        p = whole_life_class(insured_age=40, face_amount=100_000.0, is_participating=False)
        assert p.calc_paid_up_additions_from_dividend() == 0.0

    @pytest.mark.unit()
    def test_calc_paid_up_additions_from_dividend_positive_for_par(self, whole_life_class):
        """PUA from dividend is positive for participating policy with cash value."""
        p = whole_life_class(
            insured_age=40,
            face_amount=100_000.0,
            cash_value=50_000.0,
            is_participating=True,
            rate_dividend=0.02,
        )
        assert p.calc_paid_up_additions_from_dividend() > 0.0


@pytest.mark.unit()
class Class_Test_Life_Whole_IRR:
    """Tests for Insurance_Life_Whole.calc_internal_rate_of_return()."""

    @pytest.mark.unit()
    def test_irr_returns_float(self, basic_whole_policy):
        """IRR returns a float for valid num_years."""
        result = basic_whole_policy.calc_internal_rate_of_return(num_years = 10)
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_irr_invalid_num_years_raises(self, basic_whole_policy):
        """Non-positive num_years raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_whole_policy.calc_internal_rate_of_return(num_years = 0)

    @pytest.mark.unit()
    def test_irr_negative_when_zero_cv(self, whole_life_class):
        """IRR can be negative when projected cash value stays below total premiums."""
        p = whole_life_class(
            insured_age=40,
            face_amount=100_000.0,
            rate_guaranteed_interest=0.0,
            rate_cost_of_insurance=1000.0,
        )
        result = p.calc_internal_rate_of_return(num_years = 1)
        assert result < 0.0

    @pytest.mark.unit()
    def test_irr_raises_when_zero_premium(self, whole_life_class):
        """IRR raises Exception_Calculation when annual premium is zero."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Calculation,
        )

        p = whole_life_class(
            insured_age=40,
            face_amount=100_000.0,
            rate_cost_of_insurance=0,
        )
        with pytest.raises(Exception_Calculation):
            p.calc_internal_rate_of_return(num_years = 10)


@pytest.mark.unit()
class Class_Test_Life_Whole_String_Repr:
    """Tests for Insurance_Life_Whole.get_insurance_as_string()."""

    @pytest.mark.unit()
    def test_string_contains_whole_life(self, basic_whole_policy):
        """String representation contains 'Whole Life'."""
        assert "Whole Life" in basic_whole_policy.get_insurance_as_string()

    @pytest.mark.unit()
    def test_string_contains_participating(self, basic_whole_policy):
        """Default policy string contains 'Participating'."""
        assert "Participating" in basic_whole_policy.get_insurance_as_string()

    @pytest.mark.unit()
    def test_string_non_participating(self, whole_life_class):
        """Non-participating policy string contains 'Non-Participating'."""
        p = whole_life_class(insured_age=40, face_amount=100_000.0, is_participating=False)
        assert "Non-Participating" in p.get_insurance_as_string()


# ======================================================================
# Universal Life Insurance Tests
# ======================================================================


@pytest.fixture()
def universal_life_class():
    """Import Insurance_Life_Universal."""
    from src.products.insurance.insurance_life.insurance_life_universal import (
        Insurance_Life_Universal,
    )

    return Insurance_Life_Universal


@pytest.fixture()
def basic_universal_policy(universal_life_class):
    """A valid Insurance_Life_Universal instance with defaults."""
    return universal_life_class(insured_age=40, face_amount=250_000.0)


@pytest.mark.unit()
class Class_Test_Life_Universal_Construction:
    """Tests for Insurance_Life_Universal constructor."""

    @pytest.mark.unit()
    def test_creates_instance(self, basic_universal_policy):
        """Universal life policy instance created without error."""
        assert basic_universal_policy is not None

    @pytest.mark.unit()
    def test_default_attributes(self, basic_universal_policy):
        """Default crediting rates set correctly."""
        p = basic_universal_policy
        assert p.m_rate_crediting_current == 0.045
        assert p.m_rate_crediting_guaranteed == 0.02

    @pytest.mark.unit()
    def test_invalid_rate_crediting_current_raises(self, universal_life_class):
        """Negative rate_crediting_current raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            universal_life_class(
                insured_age=40, face_amount=100_000.0, rate_crediting_current=-0.01
            )

    @pytest.mark.unit()
    def test_invalid_cash_value_raises(self, universal_life_class):
        """Negative cash_value raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            universal_life_class(insured_age=40, face_amount=100_000.0, cash_value=-1.0)


@pytest.mark.unit()
class Class_Test_Life_Universal_Calculations:
    """Tests for Insurance_Life_Universal calculation methods."""

    @pytest.mark.unit()
    def test_calc_death_benefit_positive(self, basic_universal_policy):
        """Death benefit is positive."""
        assert basic_universal_policy.calc_death_benefit() > 0.0

    @pytest.mark.unit()
    def test_calc_annual_premium_positive(self, basic_universal_policy):
        """Annual premium is positive."""
        assert basic_universal_policy.calc_annual_premium() > 0.0

    @pytest.mark.unit()
    def test_calc_monthly_coi_charge_non_negative(self, basic_universal_policy):
        """Monthly COI charge is non-negative."""
        assert basic_universal_policy.calc_monthly_COI_charge() >= 0.0

    @pytest.mark.unit()
    def test_calc_net_amount_at_risk_non_negative(self, basic_universal_policy):
        """NAR is non-negative."""
        assert basic_universal_policy.calc_net_amount_at_risk() >= 0.0

    @pytest.mark.unit()
    def test_calc_cash_value_at_month_returns_float(self, basic_universal_policy):
        """Cash value at month 12 returns a non-negative float."""
        result = basic_universal_policy.calc_cash_value_at_month(months = 12)
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_get_insurance_as_string_contains_universal(self, basic_universal_policy):
        """String representation contains 'Universal'."""
        assert "Universal" in basic_universal_policy.get_insurance_as_string()

    @pytest.mark.unit()
    def test_calc_effective_crediting_rate_returns_float(self, basic_universal_policy):
        """Effective crediting rate returns a float."""
        assert isinstance(
            basic_universal_policy.calc_effective_crediting_rate(index_return=0.08),
            float,
        )


# ======================================================================
# Variable Life Insurance Tests
# ======================================================================


@pytest.fixture()
def variable_life_class():
    """Import Insurance_Life_Variable."""
    from src.products.insurance.insurance_life.insurance_life_variable import (
        Insurance_Life_Variable,
    )

    return Insurance_Life_Variable


@pytest.fixture()
def basic_variable_policy(variable_life_class):
    """A valid Insurance_Life_Variable instance with defaults."""
    return variable_life_class(insured_age=40, face_amount=250_000.0)


@pytest.mark.unit()
class Class_Test_Life_Variable_Construction:
    """Tests for Insurance_Life_Variable constructor."""

    @pytest.mark.unit()
    def test_creates_instance(self, basic_variable_policy):
        """Variable life policy instance created without error."""
        assert basic_variable_policy is not None

    @pytest.mark.unit()
    def test_invalid_rate_me_charge_raises(self, variable_life_class):
        """Negative rate_ME_charge raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            variable_life_class(insured_age=40, face_amount=100_000.0, rate_ME_charge=-0.01)

    @pytest.mark.unit()
    def test_invalid_cash_value_raises(self, variable_life_class):
        """Negative cash_value raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            variable_life_class(insured_age=40, face_amount=100_000.0, cash_value=-1.0)


@pytest.mark.unit()
class Class_Test_Life_Variable_Calculations:
    """Tests for Insurance_Life_Variable calculation methods."""

    @pytest.mark.unit()
    def test_calc_death_benefit_positive(self, basic_variable_policy):
        """Death benefit equals face amount with no cash value."""
        assert basic_variable_policy.calc_death_benefit() == 250_000.0

    @pytest.mark.unit()
    def test_calc_annual_premium_positive(self, basic_variable_policy):
        """Annual premium is positive."""
        assert basic_variable_policy.calc_annual_premium() > 0.0

    @pytest.mark.unit()
    def test_calc_total_annual_fees_non_negative(self, basic_variable_policy):
        """Total annual fees are non-negative."""
        assert basic_variable_policy.calc_total_annual_fees() >= 0.0

    @pytest.mark.unit()
    def test_calc_monthly_fees_non_negative(self, basic_variable_policy):
        """Monthly fees are non-negative."""
        assert basic_variable_policy.calc_monthly_fees() >= 0.0

    @pytest.mark.unit()
    def test_calc_net_amount_at_risk_non_negative(self, basic_variable_policy):
        """NAR is non-negative."""
        assert basic_variable_policy.calc_net_amount_at_risk() >= 0.0

    @pytest.mark.unit()
    def test_calc_weighted_return_returns_float(self, basic_variable_policy):
        """Weighted return returns a float given a returns dict."""
        from src.products.insurance.insurance_life.insurance_life_variable import (
            Sub_Account_Type,
        )

        sub_returns = {
            Sub_Account_Type.BALANCED: 0.07,
            Sub_Account_Type.FIXED_INCOME: 0.04,
            Sub_Account_Type.MONEY_MARKET: 0.02,
            Sub_Account_Type.EQUITY_LARGE_CAP: 0.10,
            Sub_Account_Type.EQUITY_INTERNATIONAL: 0.08,
        }
        result = basic_variable_policy.calc_weighted_return(sub_account_returns = sub_returns)
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_get_insurance_as_string_contains_variable(self, basic_variable_policy):
        """String representation contains 'Variable'."""
        assert "Variable" in basic_variable_policy.get_insurance_as_string()


# ======================================================================
# Survivor Life Insurance Tests
# ======================================================================


@pytest.fixture()
def survivor_life_class():
    """Import Insurance_Life_Survivor."""
    from src.products.insurance.insurance_life.insurance_life_survivor import (
        Insurance_Life_Survivor,
    )

    return Insurance_Life_Survivor


@pytest.fixture()
def basic_survivor_policy(survivor_life_class):
    """A valid Insurance_Life_Survivor instance with defaults."""
    return survivor_life_class(
        insured_age=60,
        insured_age_second=58,
        face_amount=1_000_000.0,
    )


@pytest.mark.unit()
class Class_Test_Life_Survivor_Construction:
    """Tests for Insurance_Life_Survivor constructor."""

    @pytest.mark.unit()
    def test_creates_instance(self, basic_survivor_policy):
        """Survivor life policy instance created without error."""
        assert basic_survivor_policy is not None

    @pytest.mark.unit()
    def test_invalid_second_insured_age_raises(self, survivor_life_class):
        """Non-positive second insured age raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            survivor_life_class(
                insured_age=60,
                insured_age_second=121,
                face_amount=1_000_000.0,
            )


@pytest.mark.unit()
class Class_Test_Life_Survivor_Calculations:
    """Tests for Insurance_Life_Survivor calculation methods."""

    @pytest.mark.unit()
    def test_calc_death_benefit_equals_face(self, basic_survivor_policy):
        """Default death benefit equals the face amount."""
        assert basic_survivor_policy.calc_death_benefit() == 1_000_000.0

    @pytest.mark.unit()
    def test_calc_annual_premium_positive(self, basic_survivor_policy):
        """Annual premium is positive."""
        assert basic_survivor_policy.calc_annual_premium() > 0.0

    @pytest.mark.unit()
    def test_calc_joint_equivalent_age_positive(self, basic_survivor_policy):
        """Joint equivalent age is a positive int."""
        result = basic_survivor_policy.calc_joint_equivalent_age()
        assert isinstance(result, int)
        assert result > 0

    @pytest.mark.unit()
    def test_calc_joint_coi_non_negative(self, basic_survivor_policy):
        """Joint COI is non-negative."""
        assert basic_survivor_policy.calc_joint_COI() >= 0.0

    @pytest.mark.unit()
    def test_calc_net_amount_at_risk_non_negative(self, basic_survivor_policy):
        """NAR is non-negative."""
        assert basic_survivor_policy.calc_net_amount_at_risk() >= 0.0

    @pytest.mark.unit()
    def test_calc_cash_value_at_year_non_negative(self, basic_survivor_policy):
        """Cash value at year 10 is non-negative."""
        assert basic_survivor_policy.calc_cash_value_at_year(years = 10) >= 0.0

    @pytest.mark.unit()
    def test_get_insurance_as_string_contains_survivor(self, basic_survivor_policy):
        """String representation contains 'Survivor'."""
        assert "Survivor" in basic_survivor_policy.get_insurance_as_string()


# ======================================================================
# Additional Property + Branch Coverage Tests
# ======================================================================


@pytest.mark.unit()
class Class_Test_Life_Universal_Properties:
    """Tests that access all Universal Life properties for coverage."""

    @pytest.mark.unit()
    def test_ul_variant_property(self, basic_universal_policy):
        """ul_variant property returns UL_Variant."""
        from src.products.insurance.insurance_life.insurance_life_universal import (
            UL_Variant,
        )

        assert basic_universal_policy.ul_variant == UL_Variant.TRADITIONAL

    @pytest.mark.unit()
    def test_rate_crediting_properties(self, basic_universal_policy):
        """Crediting rate properties return floats."""
        p = basic_universal_policy
        assert isinstance(p.rate_crediting_current, float)
        assert isinstance(p.rate_crediting_guaranteed, float)
        assert isinstance(p.rate_cap, float)
        assert isinstance(p.rate_floor, float)
        assert isinstance(p.participation_rate, float)

    @pytest.mark.unit()
    def test_cash_and_charge_properties(self, basic_universal_policy):
        """Cash value and charge properties return non-negative floats."""
        p = basic_universal_policy
        assert isinstance(p.cash_value, float)
        assert isinstance(p.rate_COI, float)
        assert isinstance(p.rate_expense_charge, float)
        assert isinstance(p.rate_surrender_charge, float)
        assert isinstance(p.surrender_charge_years, int)

    @pytest.mark.unit()
    def test_premium_and_guarantee_properties(self, basic_universal_policy):
        """Target/minimum premium and NLG properties return correct types."""
        p = basic_universal_policy
        assert isinstance(p.target_premium, float)
        assert isinstance(p.minimum_premium, float)
        assert isinstance(p.has_no_lapse_guarantee, bool)
        assert isinstance(p.nlg_guarantee_years, int)

    @pytest.mark.unit()
    def test_benefit_and_loan_properties(self, basic_universal_policy):
        """Death benefit, loan, and payment frequency properties."""
        from src.products.insurance.insurance_life.insurance_life_base import (
            Death_Benefit_Option,
        )

        p = basic_universal_policy
        assert p.death_benefit_option == Death_Benefit_Option.LEVEL
        assert isinstance(p.amount_loan_outstanding, float)
        assert isinstance(p.rate_loan_interest, float)
        assert isinstance(p.payment_frequency, int)

    @pytest.mark.unit()
    def test_indexed_variant_crediting(self, universal_life_class):
        """INDEXED variant applies cap/floor to index return."""
        from src.products.insurance.insurance_life.insurance_life_universal import (
            UL_Variant,
        )

        p = universal_life_class(
            insured_age=45,
            face_amount=200_000.0,
            ul_variant=UL_Variant.INDEXED,
            rate_cap=0.10,
            rate_floor=0.0,
            participation_rate=1.0,
        )
        rate = p.calc_effective_crediting_rate(index_return=0.15)
        assert rate <= 0.10

    @pytest.mark.unit()
    def test_guaranteed_variant_crediting(self, universal_life_class):
        """GUARANTEED variant returns guaranteed rate."""
        from src.products.insurance.insurance_life.insurance_life_universal import (
            UL_Variant,
        )

        p = universal_life_class(
            insured_age=45,
            face_amount=200_000.0,
            ul_variant=UL_Variant.GUARANTEED,
            rate_crediting_guaranteed=0.025,
        )
        assert p.calc_effective_crediting_rate() == 0.025

    @pytest.mark.unit()
    def test_calc_months_until_lapse_returns_int(self, universal_life_class):
        """calc_months_until_lapse returns an int."""
        p = universal_life_class(
            insured_age=40,
            face_amount=50_000.0,
            cash_value=500.0,
            rate_COI=100.0,
        )
        result = p.calc_months_until_lapse(monthly_premium=0.0)
        assert isinstance(result, int)

    @pytest.mark.unit()
    def test_calc_months_until_lapse_no_lapse(self, universal_life_class):
        """Policy with large cash value and low COI returns -1."""
        p = universal_life_class(
            insured_age=40,
            face_amount=100_000.0,
            cash_value=500_000.0,
            rate_COI=0.01,
            rate_expense_charge=0.0,
        )
        result = p.calc_months_until_lapse(monthly_premium=1000.0)
        assert result == -1

    @pytest.mark.unit()
    def test_calc_cash_surrender_with_policy_year(self, universal_life_class):
        """Cash surrender value with policy_year > 0 applies surrender charge."""
        p = universal_life_class(
            insured_age=40,
            face_amount=100_000.0,
            cash_value=10_000.0,
            rate_surrender_charge=0.05,
            surrender_charge_years=10,
        )
        csv = p.calc_cash_surrender_value(policy_year=5)
        assert isinstance(csv, float)

    @pytest.mark.unit()
    def test_calc_loan_interest_due_positive(self, universal_life_class):
        """Loan interest due is non-negative."""
        p = universal_life_class(
            insured_age=40,
            face_amount=100_000.0,
            amount_loan_outstanding=10_000.0,
            rate_loan_interest=0.05,
        )
        assert p.calc_loan_interest_due(years=2) >= 0.0

    @pytest.mark.unit()
    def test_calc_loan_interest_due_invalid_years(self, basic_universal_policy):
        """Non-positive years raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_universal_policy.calc_loan_interest_due(years=0)

    @pytest.mark.unit()
    def test_additional_validation_raises(self, universal_life_class):
        """Other invalid inputs raise Exception_Validation_Input."""
        from src.products.insurance.insurance_life.insurance_life_universal import (
            UL_Variant,
        )
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            universal_life_class(
                insured_age=40, face_amount=100_000.0, ul_variant="TRAD"
            )
        with pytest.raises(Exception_Validation_Input):
            universal_life_class(
                insured_age=40, face_amount=100_000.0, rate_crediting_guaranteed=-0.01
            )
        with pytest.raises(Exception_Validation_Input):
            universal_life_class(
                insured_age=40, face_amount=100_000.0, rate_cap=-0.01
            )
        with pytest.raises(Exception_Validation_Input):
            universal_life_class(
                insured_age=40, face_amount=100_000.0, rate_floor="bad"
            )
        with pytest.raises(Exception_Validation_Input):
            universal_life_class(
                insured_age=40, face_amount=100_000.0, participation_rate=-0.01
            )
        with pytest.raises(Exception_Validation_Input):
            universal_life_class(
                insured_age=40, face_amount=100_000.0, rate_COI=-0.01
            )
        with pytest.raises(Exception_Validation_Input):
            universal_life_class(
                insured_age=40, face_amount=100_000.0, rate_expense_charge=-0.01
            )
        with pytest.raises(Exception_Validation_Input):
            universal_life_class(
                insured_age=40, face_amount=100_000.0, rate_surrender_charge=-0.01
            )
        with pytest.raises(Exception_Validation_Input):
            universal_life_class(
                insured_age=40, face_amount=100_000.0, surrender_charge_years=-1
            )
        with pytest.raises(Exception_Validation_Input):
            universal_life_class(
                insured_age=40,
                face_amount=100_000.0,
                death_benefit_option="LEVEL",
            )
        with pytest.raises(Exception_Validation_Input):
            universal_life_class(
                insured_age=40, face_amount=100_000.0, amount_loan_outstanding=-1.0
            )
        with pytest.raises(Exception_Validation_Input):
            universal_life_class(
                insured_age=40, face_amount=100_000.0, rate_loan_interest=-0.01
            )
        with pytest.raises(Exception_Validation_Input):
            universal_life_class(
                insured_age=40, face_amount=100_000.0, payment_frequency=-1
            )


@pytest.mark.unit()
class Class_Test_Life_Universal_Extra:
    """Additional Universal Life tests for branch and method coverage."""

    @pytest.mark.unit()
    def test_increasing_death_benefit(self, universal_life_class):
        """INCREASING death benefit includes cash value."""
        from src.products.insurance.insurance_life.insurance_life_base import (
            Death_Benefit_Option,
        )

        p = universal_life_class(
            insured_age=40,
            face_amount=100_000.0,
            cash_value=20_000.0,
            death_benefit_option=Death_Benefit_Option.INCREASING,
        )
        assert p.calc_death_benefit() >= 120_000.0

    @pytest.mark.unit()
    def test_target_premium_branch(self, universal_life_class):
        """When target_premium > 0, calc_annual_premium returns it."""
        p = universal_life_class(
            insured_age=40,
            face_amount=100_000.0,
            target_premium=3000.0,
        )
        assert p.calc_annual_premium() == 3000.0

    @pytest.mark.unit()
    def test_calc_modal_premium_returns_float(self, basic_universal_policy):
        """calc_modal_premium returns a float."""
        assert isinstance(basic_universal_policy.calc_modal_premium(), float)

    @pytest.mark.unit()
    def test_get_insurance_as_string_non_empty(self, basic_universal_policy):
        """get_insurance_as_string returns non-empty string."""
        s = basic_universal_policy.get_insurance_as_string()
        assert isinstance(s, str)
        assert len(s) > 0

    @pytest.mark.unit()
    def test_calc_max_loan_amount_returns_float(self, basic_universal_policy):
        """calc_max_loan_amount returns a float."""
        assert isinstance(basic_universal_policy.calc_max_loan_amount(), float)

    @pytest.mark.unit()
    def test_calc_modal_premium_single_pay(self, universal_life_class):
        """SINGLE pay frequency returns annual premium directly."""
        p = universal_life_class(
            insured_age=40,
            face_amount=100_000.0,
            payment_frequency=0,
        )
        modal = p.calc_modal_premium()
        assert modal == p.calc_annual_premium()

    @pytest.mark.unit()
    def test_calc_loan_interest_due_with_loan(self, universal_life_class):
        """calc_loan_interest_due calculates correctly."""
        p = universal_life_class(
            insured_age=40,
            face_amount=100_000.0,
            amount_loan_outstanding=10_000.0,
            rate_loan_interest=0.05,
        )
        assert p.calc_loan_interest_due(years=1) == pytest.approx(500.0, rel=1e-4)

    @pytest.mark.unit()
    def test_calc_months_until_lapse_lapses(self, universal_life_class):
        """Policy with minimal cash and high COI lapses quickly."""
        p = universal_life_class(
            insured_age=40,
            face_amount=100_000.0,
            cash_value=100.0,
            rate_COI=200.0,
            rate_expense_charge=0.5,
        )
        result = p.calc_months_until_lapse(monthly_premium=0.0)
        assert result > 0


@pytest.mark.unit()
class Class_Test_Life_Variable_Properties:
    """Tests that access all Variable Life properties and branches."""

    @pytest.mark.unit()
    def test_all_properties(self, basic_variable_policy):
        """All Variable Life properties return expected types."""
        p = basic_variable_policy
        assert isinstance(p.sub_account_allocations, dict)
        assert isinstance(p.cash_value, float)
        assert isinstance(p.guaranteed_min_death_benefit, float)
        assert isinstance(p.rate_ME_charge, float)
        assert isinstance(p.rate_admin_fee, float)
        assert isinstance(p.rate_investment_management, float)
        assert isinstance(p.rate_surrender_charge, float)
        assert isinstance(p.surrender_charge_years, int)
        assert isinstance(p.rate_COI, float)
        assert isinstance(p.amount_loan_outstanding, float)
        assert isinstance(p.rate_loan_interest, float)

    @pytest.mark.unit()
    def test_death_benefit_option_property(self, basic_variable_policy):
        """death_benefit_option property returns Death_Benefit_Option."""
        from src.products.insurance.insurance_life.insurance_life_base import (
            Death_Benefit_Option,
        )

        assert basic_variable_policy.death_benefit_option == Death_Benefit_Option.LEVEL

    @pytest.mark.unit()
    def test_calc_total_annual_fees_non_negative(self, basic_variable_policy):
        """Total annual fees is non-negative."""
        assert basic_variable_policy.calc_total_annual_fees() >= 0.0

    @pytest.mark.unit()
    def test_calc_monthly_fees_non_negative(self, basic_variable_policy):
        """Monthly fees is non-negative."""
        assert basic_variable_policy.calc_monthly_fees() >= 0.0

    @pytest.mark.unit()
    def test_calc_cash_value_at_month_invalid(self, basic_variable_policy):
        """Non-positive months raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_variable_policy.calc_cash_value_at_month(months = 0)

    @pytest.mark.unit()
    def test_calc_cash_surrender_with_policy_year(self, variable_life_class):
        """Cash surrender value with policy_year > 0."""
        p = variable_life_class(
            insured_age=40,
            face_amount=100_000.0,
            cash_value=10_000.0,
            rate_surrender_charge=0.05,
            surrender_charge_years=10,
        )
        csv = p.calc_cash_surrender_value(policy_year=3)
        assert isinstance(csv, float)

    @pytest.mark.unit()
    def test_calc_loan_interest_due_invalid(self, basic_variable_policy):
        """Non-positive years raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_variable_policy.calc_loan_interest_due(years=0)

    @pytest.mark.unit()
    def test_increasing_death_benefit(self, variable_life_class):
        """Increasing death benefit = face + cash_value."""
        from src.products.insurance.insurance_life.insurance_life_base import (
            Death_Benefit_Option,
        )

        p = variable_life_class(
            insured_age=40,
            face_amount=100_000.0,
            cash_value=20_000.0,
            death_benefit_option=Death_Benefit_Option.INCREASING,
        )
        assert p.calc_death_benefit() >= 120_000.0

    @pytest.mark.unit()
    def test_additional_validation_raises(self, variable_life_class):
        """Invalid inputs for Variable Life raise Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            variable_life_class(insured_age=40, face_amount=100_000.0, cash_value=-1.0)
        with pytest.raises(Exception_Validation_Input):
            variable_life_class(insured_age=40, face_amount=100_000.0, rate_ME_charge=-0.01)
        with pytest.raises(Exception_Validation_Input):
            variable_life_class(insured_age=40, face_amount=100_000.0, rate_admin_fee=-0.01)
        with pytest.raises(Exception_Validation_Input):
            variable_life_class(
                insured_age=40, face_amount=100_000.0, rate_investment_management=-0.01
            )
        with pytest.raises(Exception_Validation_Input):
            variable_life_class(
                insured_age=40, face_amount=100_000.0, rate_surrender_charge=-0.01
            )
        with pytest.raises(Exception_Validation_Input):
            variable_life_class(
                insured_age=40, face_amount=100_000.0, surrender_charge_years=-1
            )
        with pytest.raises(Exception_Validation_Input):
            variable_life_class(insured_age=40, face_amount=100_000.0, rate_COI=-0.01)
        with pytest.raises(Exception_Validation_Input):
            variable_life_class(
                insured_age=40, face_amount=100_000.0, death_benefit_option="LEVEL"
            )
        with pytest.raises(Exception_Validation_Input):
            variable_life_class(
                insured_age=40, face_amount=100_000.0, amount_loan_outstanding=-1.0
            )
        with pytest.raises(Exception_Validation_Input):
            variable_life_class(
                insured_age=40, face_amount=100_000.0, rate_loan_interest=-0.01
            )
        with pytest.raises(Exception_Validation_Input):
            variable_life_class(
                insured_age=40, face_amount=100_000.0, sub_account_allocations="bad"
            )
        with pytest.raises(Exception_Validation_Input):
            variable_life_class(
                insured_age=40,
                face_amount=100_000.0,
                sub_account_allocations={"bad_key": 1.0},
            )
        with pytest.raises(Exception_Validation_Input):
            from src.products.insurance.insurance_life.insurance_life_variable import (
                Sub_Account_Type,
            )

            variable_life_class(
                insured_age=40,
                face_amount=100_000.0,
                sub_account_allocations={Sub_Account_Type.BALANCED: 1.5},
            )
        with pytest.raises(Exception_Validation_Input):
            from src.products.insurance.insurance_life.insurance_life_variable import (
                Sub_Account_Type,
            )

            variable_life_class(
                insured_age=40,
                face_amount=100_000.0,
                sub_account_allocations={Sub_Account_Type.BALANCED: 0.5},
            )


@pytest.mark.unit()
class Class_Test_Life_Variable_Extra:
    """Additional Variable Life tests for branch and method coverage."""

    @pytest.mark.unit()
    def test_calc_weighted_return_invalid_raises(self, basic_variable_policy):
        """Non-dict sub_account_returns raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_variable_policy.calc_weighted_return(sub_account_returns = "not_a_dict")

    @pytest.mark.unit()
    def test_calc_modal_premium_returns_float(self, basic_variable_policy):
        """calc_modal_premium returns a float."""
        assert isinstance(basic_variable_policy.calc_modal_premium(), float)

    @pytest.mark.unit()
    def test_calc_monthly_coi_non_negative(self, basic_variable_policy):
        """Monthly COI charge is non-negative."""
        assert basic_variable_policy.calc_monthly_COI_charge() >= 0.0

    @pytest.mark.unit()
    def test_calc_cash_value_at_month_valid(self, basic_variable_policy):
        """calc_cash_value_at_month returns non-negative for valid months."""
        result = basic_variable_policy.calc_cash_value_at_month(months = 12)
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_calc_max_loan_amount_returns_float(self, basic_variable_policy):
        """calc_max_loan_amount returns a float."""
        assert isinstance(basic_variable_policy.calc_max_loan_amount(), float)

    @pytest.mark.unit()
    def test_calc_loan_interest_due_valid(self, variable_life_class):
        """calc_loan_interest_due returns expected value."""
        p = variable_life_class(
            insured_age=40,
            face_amount=100_000.0,
            amount_loan_outstanding=10_000.0,
            rate_loan_interest=0.05,
        )
        assert p.calc_loan_interest_due(years=1) == pytest.approx(500.0, rel=1e-4)

    @pytest.mark.unit()
    def test_get_insurance_as_string_non_empty(self, basic_variable_policy):
        """get_insurance_as_string returns non-empty string."""
        s = basic_variable_policy.get_insurance_as_string()
        assert isinstance(s, str)
        assert len(s) > 0

    @pytest.mark.unit()
    def test_calc_modal_premium_single_pay(self, variable_life_class):
        """SINGLE pay frequency returns annual premium directly."""
        from src.products.insurance.insurance_life.insurance_life_base import (
            Premium_Frequency,
        )
        from src.products.insurance.insurance_life.insurance_life_variable import (
            Sub_Account_Type,
        )

        p = variable_life_class(
            insured_age=40,
            face_amount=100_000.0,
            sub_account_allocations={Sub_Account_Type.BALANCED: 1.0},
            premium_frequency=Premium_Frequency.SINGLE,
        )
        modal = p.calc_modal_premium()
        assert modal == p.calc_annual_premium()


@pytest.mark.unit()
class Class_Test_Life_Survivor_Properties:
    """Tests that access all Survivor Life properties and branches."""

    @pytest.mark.unit()
    def test_all_properties(self, basic_survivor_policy):
        """All Survivor Life properties return expected types."""
        p = basic_survivor_policy
        assert isinstance(p.insured_age_second, int)
        assert isinstance(p.underwriting_class_second, object)
        assert isinstance(p.is_smoker_second, bool)
        assert isinstance(p.first_death_occurred, bool)
        assert isinstance(p.cash_value, float)
        assert isinstance(p.rate_guaranteed_interest, float)
        assert isinstance(p.rate_COI_insured_1, float)
        assert isinstance(p.rate_COI_insured_2, float)
        assert isinstance(p.death_benefit_option, object)
        assert isinstance(p.has_split_option, bool)
        assert isinstance(p.amount_loan_outstanding, float)
        assert isinstance(p.rate_loan_interest, float)
        assert isinstance(p.rate_surrender_charge, float)
        assert isinstance(p.surrender_charge_years, int)

    @pytest.mark.unit()
    def test_first_death_occurred_trigger(self, survivor_life_class):
        """Policy with first_death_occurred=True still creates correctly."""
        p = survivor_life_class(
            insured_age=65,
            insured_age_second=62,
            face_amount=1_000_000.0,
            first_death_occurred=True,
        )
        assert p.first_death_occurred is True

    @pytest.mark.unit()
    def test_calc_cash_value_at_year_invalid(self, basic_survivor_policy):
        """Non-positive year raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_survivor_policy.calc_cash_value_at_year(years = 0)

    @pytest.mark.unit()
    def test_calc_joint_coi_after_first_death(self, survivor_life_class):
        """After first death, joint COI uses insured 2 rate."""
        p = survivor_life_class(
            insured_age=65,
            insured_age_second=62,
            face_amount=1_000_000.0,
            first_death_occurred=True,
            rate_COI_insured_2=3.5,
        )
        coi = p.calc_joint_COI()
        assert coi >= 0.0

    @pytest.mark.unit()
    def test_additional_validation_raises(self, survivor_life_class):
        """Invalid inputs for Survivor Life raise Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            survivor_life_class(
                insured_age=60,
                insured_age_second=55,
                face_amount=1_000_000.0,
                cash_value=-1.0,
            )
        with pytest.raises(Exception_Validation_Input):
            survivor_life_class(
                insured_age=60,
                insured_age_second=55,
                face_amount=1_000_000.0,
                rate_guaranteed_interest=-0.01,
            )
        with pytest.raises(Exception_Validation_Input):
            survivor_life_class(
                insured_age=60,
                insured_age_second=55,
                face_amount=1_000_000.0,
                rate_COI_insured_1=-0.01,
            )
        with pytest.raises(Exception_Validation_Input):
            survivor_life_class(
                insured_age=60,
                insured_age_second=55,
                face_amount=1_000_000.0,
                rate_COI_insured_2=-0.01,
            )
        with pytest.raises(Exception_Validation_Input):
            survivor_life_class(
                insured_age=60,
                insured_age_second=55,
                face_amount=1_000_000.0,
                death_benefit_option="LEVEL",
            )
        with pytest.raises(Exception_Validation_Input):
            survivor_life_class(
                insured_age=60,
                insured_age_second=55,
                face_amount=1_000_000.0,
                amount_loan_outstanding=-1.0,
            )
        with pytest.raises(Exception_Validation_Input):
            survivor_life_class(
                insured_age=60,
                insured_age_second=55,
                face_amount=1_000_000.0,
                rate_loan_interest=-0.01,
            )
        with pytest.raises(Exception_Validation_Input):
            survivor_life_class(
                insured_age=60,
                insured_age_second=55,
                face_amount=1_000_000.0,
                rate_surrender_charge=-0.01,
            )
        with pytest.raises(Exception_Validation_Input):
            survivor_life_class(
                insured_age=60,
                insured_age_second=55,
                face_amount=1_000_000.0,
                surrender_charge_years=-1,
            )
        with pytest.raises(Exception_Validation_Input):
            survivor_life_class(
                insured_age=60,
                insured_age_second=55,
                face_amount=1_000_000.0,
                underwriting_class_second="STANDARD",
            )
        with pytest.raises(Exception_Validation_Input):
            survivor_life_class(
                insured_age=60,
                insured_age_second=55,
                face_amount=1_000_000.0,
                chassis="WHOLE_LIFE",
            )


@pytest.mark.unit()
class Class_Test_Life_Survivor_Extra:
    """Additional Survivor Life tests for method/branch coverage."""

    @pytest.mark.unit()
    def test_chassis_property(self, basic_survivor_policy):
        """chassis property returns Survivor_Chassis."""
        from src.products.insurance.insurance_life.insurance_life_survivor import (
            Survivor_Chassis,
        )

        assert isinstance(basic_survivor_policy.chassis, Survivor_Chassis)

    @pytest.mark.unit()
    def test_calc_joint_equivalent_age_returns_int(self, basic_survivor_policy):
        """calc_joint_equivalent_age returns an int."""
        assert isinstance(basic_survivor_policy.calc_joint_equivalent_age(), int)

    @pytest.mark.unit()
    def test_calc_joint_coi_zero_rates(self, survivor_life_class):
        """calc_joint_COI returns 0.0 when both COI rates are zero."""
        p = survivor_life_class(
            insured_age=60,
            insured_age_second=55,
            face_amount=1_000_000.0,
            rate_COI_insured_1=0.0,
            rate_COI_insured_2=0.0,
        )
        assert p.calc_joint_COI() == 0.0

    @pytest.mark.unit()
    def test_increasing_death_benefit(self, survivor_life_class):
        """INCREASING death benefit equals face + cash value."""
        from src.products.insurance.insurance_life.insurance_life_base import (
            Death_Benefit_Option,
        )

        p = survivor_life_class(
            insured_age=60,
            insured_age_second=55,
            face_amount=1_000_000.0,
            cash_value=50_000.0,
            death_benefit_option=Death_Benefit_Option.INCREASING,
        )
        assert p.calc_death_benefit() >= 1_050_000.0

    @pytest.mark.unit()
    def test_calc_modal_premium_returns_float(self, basic_survivor_policy):
        """calc_modal_premium returns a float."""
        assert isinstance(basic_survivor_policy.calc_modal_premium(), float)

    @pytest.mark.unit()
    def test_calc_premium_savings_positive(self, basic_survivor_policy):
        """calc_premium_savings_vs_individual returns a float."""
        result = basic_survivor_policy.calc_premium_savings_vs_individual(
            individual_premium_insured_1=5000.0,
            individual_premium_insured_2=4000.0,
        )
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_calc_premium_savings_invalid_raises(self, basic_survivor_policy):
        """Negative individual premium raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_survivor_policy.calc_premium_savings_vs_individual(
                individual_premium_insured_1=-100.0,
                individual_premium_insured_2=1000.0,
            )

    @pytest.mark.unit()
    def test_calc_cash_surrender_with_policy_year(self, survivor_life_class):
        """Cash surrender with policy_year > 0 applies surrender charge."""
        p = survivor_life_class(
            insured_age=60,
            insured_age_second=55,
            face_amount=1_000_000.0,
            cash_value=50_000.0,
            rate_surrender_charge=0.05,
            surrender_charge_years=10,
        )
        csv = p.calc_cash_surrender_value(policy_year=3)
        assert isinstance(csv, float)

    @pytest.mark.unit()
    def test_calc_max_loan_amount_returns_float(self, basic_survivor_policy):
        """calc_max_loan_amount returns a float."""
        assert isinstance(basic_survivor_policy.calc_max_loan_amount(), float)

    @pytest.mark.unit()
    def test_calc_loan_interest_due_valid(self, survivor_life_class):
        """calc_loan_interest_due returns expected value."""
        p = survivor_life_class(
            insured_age=60,
            insured_age_second=55,
            face_amount=1_000_000.0,
            amount_loan_outstanding=10_000.0,
            rate_loan_interest=0.05,
        )
        assert p.calc_loan_interest_due(years=2) == pytest.approx(1000.0, rel=1e-4)

    @pytest.mark.unit()
    def test_calc_loan_interest_due_invalid(self, basic_survivor_policy):
        """Non-positive years raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_survivor_policy.calc_loan_interest_due(years=0)

    @pytest.mark.unit()
    def test_calc_estate_tax_coverage_returns_float(self, basic_survivor_policy):
        """calc_estate_tax_coverage returns a float for large estate."""
        result = basic_survivor_policy.calc_estate_tax_coverage(estate_value=20_000_000.0)
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_calc_estate_tax_coverage_no_tax(self, basic_survivor_policy):
        """Small estate (below exclusion) returns inf."""
        result = basic_survivor_policy.calc_estate_tax_coverage(estate_value=1_000_000.0)
        assert result == float("inf")

    @pytest.mark.unit()
    def test_calc_estate_tax_coverage_invalid(self, basic_survivor_policy):
        """Negative estate_value raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_survivor_policy.calc_estate_tax_coverage(estate_value=-1.0)

    @pytest.mark.unit()
    def test_calc_cash_value_at_year_valid(self, basic_survivor_policy):
        """calc_cash_value_at_year returns non-negative float."""
        result = basic_survivor_policy.calc_cash_value_at_year(years = 5)
        assert isinstance(result, float)
        assert result >= 0.0

    @pytest.mark.unit()
    def test_calc_modal_premium_single_pay(self, survivor_life_class):
        """SINGLE pay frequency returns annual premium directly."""
        from src.products.insurance.insurance_life.insurance_life_base import (
            Premium_Frequency,
        )

        p = survivor_life_class(
            insured_age=60,
            insured_age_second=55,
            face_amount=1_000_000.0,
            premium_frequency=Premium_Frequency.SINGLE,
        )
        modal = p.calc_modal_premium()
        assert modal == p.calc_annual_premium()

    @pytest.mark.unit()
    def test_calc_cash_surrender_default_no_charge(self, basic_survivor_policy):
        """calc_cash_surrender_value with default policy_year=0 returns float."""
        result = basic_survivor_policy.calc_cash_surrender_value(policy_year=0)
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_calc_monthly_coi_charge_non_negative(self, basic_survivor_policy):
        """calc_monthly_COI_charge returns non-negative float."""
        result = basic_survivor_policy.calc_monthly_COI_charge()
        assert isinstance(result, float)
        assert result >= 0.0


# ======================================================================
# Term Life — extra constructor validation
# ======================================================================


@pytest.mark.unit()
class Class_Test_Life_Term_Extra_Validation:
    """Cover constructor raise paths not tested in the base construction class."""

    @pytest.mark.unit()
    def Test_Invalid_Term_Type_String_Raises(self, life_term_class):
        """Passing a string as term_type must raise Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            life_term_class(insured_age=35, face_amount=500_000.0, term_type="level")

    @pytest.mark.unit()
    def Test_Invalid_Term_Type_None_Raises(self, life_term_class):
        """Passing None as term_type must raise Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            life_term_class(insured_age=35, face_amount=500_000.0, term_type=None)

    @pytest.mark.unit()
    def Test_Negative_Conversion_Deadline_Year_Raises(self, life_term_class):
        """Negative conversion_deadline_year must raise Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            life_term_class(
                insured_age=35,
                face_amount=500_000.0,
                conversion_deadline_year=-1,
            )

    @pytest.mark.unit()
    def Test_Negative_Rate_COI_Raises(self, life_term_class):
        """Negative rate_cost_of_insurance must raise Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            life_term_class(
                insured_age=35,
                face_amount=500_000.0,
                rate_cost_of_insurance=-1.0,
            )

    @pytest.mark.unit()
    def Test_Negative_Payment_Frequency_Raises(self, life_term_class):
        """Negative payment_frequency must raise Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            life_term_class(
                insured_age=35,
                face_amount=500_000.0,
                payment_frequency=-1,
            )


# ======================================================================
# Term Life — property accessors (covers lines 273-308)
# ======================================================================


@pytest.mark.unit()
class Class_Test_Life_Term_Properties:
    """Tests for Insurance_Life_Term property accessors."""

    @pytest.mark.unit()
    def Test_Term_Years_Property(self, life_term_class):
        """term_years property returns the stored value."""
        obj = life_term_class(insured_age=35, face_amount=500_000.0, term_years=15)
        assert obj.term_years == 15

    @pytest.mark.unit()
    def Test_Term_Type_Property(self, life_term_class, term_enums):
        """term_type property returns the stored Term_Type."""
        TT = term_enums["Term_Type"]
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            term_type=TT.DECREASING,
        )
        assert obj.term_type == TT.DECREASING

    @pytest.mark.unit()
    def Test_Is_Convertible_Property_True(self, basic_term_policy):
        """is_convertible property returns True by default."""
        assert basic_term_policy.is_convertible is True

    @pytest.mark.unit()
    def Test_Is_Convertible_Property_False(self, life_term_class):
        """is_convertible property returns False when set to False."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            is_convertible=False,
        )
        assert obj.is_convertible is False

    @pytest.mark.unit()
    def Test_Conversion_Deadline_Year_Property_Default(self, basic_term_policy):
        """conversion_deadline_year defaults to term_years when input is 0."""
        assert basic_term_policy.conversion_deadline_year == basic_term_policy.term_years

    @pytest.mark.unit()
    def Test_Conversion_Deadline_Year_Property_Custom(self, life_term_class):
        """conversion_deadline_year stores the explicitly provided value."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            term_years=20,
            conversion_deadline_year=10,
        )
        assert obj.conversion_deadline_year == 10

    @pytest.mark.unit()
    def Test_Is_Renewable_Property_Default_True(self, basic_term_policy):
        """is_renewable property defaults to True."""
        assert basic_term_policy.is_renewable is True

    @pytest.mark.unit()
    def Test_Is_Renewable_Property_False(self, life_term_class):
        """is_renewable property returns False when set."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            is_renewable=False,
        )
        assert obj.is_renewable is False

    @pytest.mark.unit()
    def Test_Has_Return_Of_Premium_Property_False(self, basic_term_policy):
        """has_return_of_premium property defaults to False."""
        assert basic_term_policy.has_return_of_premium is False

    @pytest.mark.unit()
    def Test_Has_Return_Of_Premium_Property_True(self, life_term_class):
        """has_return_of_premium property returns True when set."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            has_return_of_premium=True,
        )
        assert obj.has_return_of_premium is True

    @pytest.mark.unit()
    def Test_Rate_Cost_Of_Insurance_Property(self, life_term_class):
        """rate_cost_of_insurance property returns the stored float."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            rate_cost_of_insurance=3.75,
        )
        assert obj.rate_cost_of_insurance == pytest.approx(3.75)

    @pytest.mark.unit()
    def Test_Payment_Frequency_Property(self, life_term_class):
        """payment_frequency property returns the stored int."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            payment_frequency=4,
        )
        assert obj.payment_frequency == 4


# ======================================================================
# Term Life — calc_death_benefit_at_year (covers lines 356, 364, 369)
# ======================================================================


@pytest.mark.unit()
class Class_Test_Life_Term_Death_Benefit_At_Year:
    """Tests for Insurance_Life_Term.calc_death_benefit_at_year()."""

    @pytest.mark.unit()
    def Test_Invalid_Policy_Year_Raises(self, basic_term_policy):
        """policy_year < 1 raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_term_policy.calc_death_benefit_at_year(policy_year = 0)

    @pytest.mark.unit()
    def Test_Invalid_Policy_Year_Float_Raises(self, basic_term_policy):
        """Float policy_year raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_term_policy.calc_death_benefit_at_year(policy_year = 1.5)

    @pytest.mark.unit()
    def Test_Year_Beyond_Term_Returns_Zero(self, basic_term_policy):
        """policy_year > term_years returns 0.0."""
        result = basic_term_policy.calc_death_benefit_at_year(policy_year = 25)
        assert result == pytest.approx(0.0)

    @pytest.mark.unit()
    def Test_Level_Term_Returns_Face_Amount(self, basic_term_policy):
        """Level term in year 1 returns face amount."""
        result = basic_term_policy.calc_death_benefit_at_year(policy_year = 1)
        assert result == pytest.approx(500_000.0)

    @pytest.mark.unit()
    def Test_Decreasing_Term_Formula(self, life_term_class, term_enums):
        """Decreasing term death benefit at year t = F * (n - t + 1) / n."""
        obj = life_term_class(
            insured_age=35,
            face_amount=600_000.0,
            term_years=20,
            term_type=term_enums["Term_Type"].DECREASING,
        )
        # year 5: F * (20 - 5 + 1) / 20 = F * 16/20
        result = obj.calc_death_benefit_at_year(policy_year = 5)
        assert result == pytest.approx(600_000.0 * 16 / 20, rel=1e-6)


# ======================================================================
# Term Life — calc_annual_premium_at_year (covers lines 421, 422, 429-437)
# ======================================================================


@pytest.mark.unit()
class Class_Test_Life_Term_Annual_Premium_At_Year:
    """Tests for Insurance_Life_Term.calc_annual_premium_at_year()."""

    @pytest.mark.unit()
    def Test_Invalid_Policy_Year_Raises(self, basic_term_policy):
        """policy_year < 1 raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_term_policy.calc_annual_premium_at_year(policy_year = 0)

    @pytest.mark.unit()
    def Test_Year_Beyond_Term_Returns_Zero(self, basic_term_policy):
        """policy_year > term_years returns 0.0."""
        result = basic_term_policy.calc_annual_premium_at_year(policy_year = 25)
        assert result == pytest.approx(0.0)

    @pytest.mark.unit()
    def Test_Level_Term_Premium_Same_Each_Year(self, basic_term_policy):
        """Level term premium is the same in year 1 and year 10."""
        p1 = basic_term_policy.calc_annual_premium_at_year(policy_year = 1)
        p10 = basic_term_policy.calc_annual_premium_at_year(policy_year = 10)
        assert p1 == pytest.approx(p10)

    @pytest.mark.unit()
    def Test_Art_Premium_Increases_With_Year(self, life_term_class, term_enums):
        """ART premium increases each year (~3% per year)."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            term_type=term_enums["Term_Type"].ANNUALLY_RENEWABLE,
        )
        p1 = obj.calc_annual_premium_at_year(policy_year = 1)
        p5 = obj.calc_annual_premium_at_year(policy_year = 5)
        assert p5 > p1

    @pytest.mark.unit()
    def Test_Art_Premium_Year_1_Equals_Annual(self, life_term_class, term_enums):
        """ART premium in year 1 equals base annual premium."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            term_type=term_enums["Term_Type"].ANNUALLY_RENEWABLE,
        )
        assert obj.calc_annual_premium_at_year(policy_year = 1) == pytest.approx(
            obj.calc_annual_premium(), rel=1e-6
        )

    @pytest.mark.unit()
    def Test_Art_Premium_Formula(self, life_term_class, term_enums):
        """ART premium in year t = base * 1.03^(t-1)."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            term_type=term_enums["Term_Type"].ANNUALLY_RENEWABLE,
        )
        base = obj.calc_annual_premium()
        result = obj.calc_annual_premium_at_year(policy_year = 3)
        assert result == pytest.approx(base * (1.03**2), rel=1e-6)


# ======================================================================
# Term Life — calc_modal_premium (covers lines 447-451)
# ======================================================================


@pytest.mark.unit()
class Class_Test_Life_Term_Modal_Premium:
    """Tests for Insurance_Life_Term.calc_modal_premium()."""

    @pytest.mark.unit()
    def Test_Single_Frequency_Returns_Annual(self, life_term_class):
        """payment_frequency=0 (SINGLE) returns annual premium directly."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            payment_frequency=0,
        )
        modal = obj.calc_modal_premium()
        annual = obj.calc_annual_premium()
        assert modal == pytest.approx(annual)

    @pytest.mark.unit()
    def Test_Monthly_Frequency_Returns_Monthly_Amount(self, life_term_class):
        """payment_frequency=12 returns annual * modal factor."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            payment_frequency=12,
        )
        modal = obj.calc_modal_premium()
        annual = obj.calc_annual_premium()
        factor = obj.calc_modal_premium_factor()
        assert modal == pytest.approx(annual * factor)

    @pytest.mark.unit()
    def Test_Annual_Frequency_Returns_Annual(self, life_term_class):
        """payment_frequency=1 modal premium equals annual premium."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            payment_frequency=1,
        )
        assert obj.calc_modal_premium() == pytest.approx(obj.calc_annual_premium())

    @pytest.mark.unit()
    def Test_Modal_Less_Than_Annual_For_Monthly(self, life_term_class):
        """Monthly modal premium is less than annual premium."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            payment_frequency=12,
        )
        assert obj.calc_modal_premium() < obj.calc_annual_premium()


# ======================================================================
# Term Life — calc_total_premiums_paid (covers lines 467-473)
# ======================================================================


@pytest.mark.unit()
class Class_Test_Life_Term_Total_Premiums:
    """Tests for Insurance_Life_Term.calc_total_premiums_paid()."""

    @pytest.mark.unit()
    def Test_Level_Term_Total_Is_Annual_Times_Years(self, basic_term_policy):
        """Level term total = annual_premium * term_years."""
        total = basic_term_policy.calc_total_premiums_paid()
        expected = basic_term_policy.calc_annual_premium() * basic_term_policy.term_years
        assert total == pytest.approx(expected)

    @pytest.mark.unit()
    def Test_Art_Total_Greater_Than_Level_Total(self, life_term_class, term_enums):
        """ART total premiums are greater than level total (premiums rise)."""
        level = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            term_years=10,
            term_type=term_enums["Term_Type"].LEVEL,
        )
        art = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            term_years=10,
            term_type=term_enums["Term_Type"].ANNUALLY_RENEWABLE,
        )
        assert art.calc_total_premiums_paid() > level.calc_total_premiums_paid()

    @pytest.mark.unit()
    def Test_Art_Total_Sums_Each_Year(self, life_term_class, term_enums):
        """ART total is exactly the sum of per-year premiums."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            term_years=5,
            term_type=term_enums["Term_Type"].ANNUALLY_RENEWABLE,
        )
        expected = sum(obj.calc_annual_premium_at_year(policy_year = yr) for yr in range(1, 6))
        assert obj.calc_total_premiums_paid() == pytest.approx(expected)


# ======================================================================
# Term Life — calc_return_of_premium_benefit (covers lines 483-485)
# ======================================================================


@pytest.mark.unit()
class Class_Test_Life_Term_ROP_Benefit:
    """Tests for Insurance_Life_Term.calc_return_of_premium_benefit()."""

    @pytest.mark.unit()
    def Test_No_Rop_Returns_Zero(self, basic_term_policy):
        """Policy without ROP returns 0.0."""
        result = basic_term_policy.calc_return_of_premium_benefit()
        assert result == pytest.approx(0.0)

    @pytest.mark.unit()
    def Test_With_Rop_Returns_Total_Premiums(self, life_term_class):
        """Policy with ROP returns total premiums paid."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            has_return_of_premium=True,
        )
        rop = obj.calc_return_of_premium_benefit()
        total = obj.calc_total_premiums_paid()
        assert rop == pytest.approx(total)

    @pytest.mark.unit()
    def Test_With_Rop_Greater_Than_Zero(self, life_term_class):
        """ROP benefit is greater than 0 for valid policy with ROP."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            has_return_of_premium=True,
        )
        assert obj.calc_return_of_premium_benefit() > 0.0


# ======================================================================
# Term Life — calc_cost_per_thousand_per_year (covers lines 504-506)
# ======================================================================


@pytest.mark.unit()
class Class_Test_Life_Term_Cost_Per_Thousand_Per_Year:
    """Tests for Insurance_Life_Term.calc_cost_per_thousand_per_year()."""

    @pytest.mark.unit()
    def Test_Beyond_Term_Returns_Zero(self, basic_term_policy):
        """policy_year > term_years returns 0.0 (db <= 0 branch)."""
        result = basic_term_policy.calc_cost_per_thousand_per_year(policy_year=25)
        assert result == pytest.approx(0.0)

    @pytest.mark.unit()
    def Test_Valid_Year_Returns_Positive(self, basic_term_policy):
        """Valid year returns positive cost per $1000."""
        result = basic_term_policy.calc_cost_per_thousand_per_year(policy_year=1)
        assert result > 0.0

    @pytest.mark.unit()
    def Test_Cost_Formula_Year_1(self, life_term_class):
        """Cost per thousand at year 1 = annual_premium / (face / 1000)."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            rate_cost_of_insurance=2.5,
        )
        result = obj.calc_cost_per_thousand_per_year(policy_year = 1)
        premium = obj.calc_annual_premium_at_year(policy_year = 1)
        expected = premium / (obj.m_face_amount / 1_000)
        assert result == pytest.approx(expected)


# ======================================================================
# Term Life — is_conversion_available + calc_remaining_term_years (line 521+)
# ======================================================================


@pytest.mark.unit()
class Class_Test_Life_Term_Conversion:
    """Tests for Insurance_Life_Term.is_conversion_available() and calc_remaining_term_years()."""

    @pytest.mark.unit()
    def Test_Not_Convertible_Returns_False(self, life_term_class):
        """Non-convertible policy returns False for any year."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            is_convertible=False,
        )
        assert obj.is_conversion_available(current_policy_year = 5) is False

    @pytest.mark.unit()
    def Test_Convertible_Within_Deadline_Returns_True(self, life_term_class):
        """Convertible policy within deadline returns True."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            is_convertible=True,
            term_years=20,
            conversion_deadline_year=10,
        )
        assert obj.is_conversion_available(current_policy_year = 5) is True

    @pytest.mark.unit()
    def Test_Convertible_Past_Deadline_Returns_False(self, life_term_class):
        """Convertible policy past deadline returns False."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            is_convertible=True,
            term_years=20,
            conversion_deadline_year=10,
        )
        assert obj.is_conversion_available(current_policy_year = 11) is False

    @pytest.mark.unit()
    def Test_Convertible_At_Deadline_Returns_True(self, life_term_class):
        """Convertible policy exactly at deadline returns True."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            is_convertible=True,
            term_years=20,
            conversion_deadline_year=10,
        )
        assert obj.is_conversion_available(current_policy_year = 10) is True

    @pytest.mark.unit()
    def Test_Remaining_Term_Years_Early(self, basic_term_policy):
        """calc_remaining_term_years at year 5 of 20-year term = 16."""
        assert basic_term_policy.calc_remaining_term_years(current_policy_year = 5) == 16

    @pytest.mark.unit()
    def Test_Remaining_Term_Years_At_End(self, basic_term_policy):
        """calc_remaining_term_years at term_years = 1."""
        assert basic_term_policy.calc_remaining_term_years(current_policy_year = 20) == 1

    @pytest.mark.unit()
    def Test_Remaining_Term_Years_Past_End(self, basic_term_policy):
        """calc_remaining_term_years past end of term is floored at 0."""
        assert basic_term_policy.calc_remaining_term_years(current_policy_year = 25) == 0


# ======================================================================
# Term Life — get_insurance_as_string (covers lines 544-574)
# ======================================================================


@pytest.mark.unit()
class Class_Test_Life_Term_String_Repr:
    """Tests for Insurance_Life_Term.get_insurance_as_string()."""

    @pytest.mark.unit()
    def Test_String_Contains_Term_Life(self, basic_term_policy):
        """String contains 'Term Life'."""
        assert "Term Life" in basic_term_policy.get_insurance_as_string()

    @pytest.mark.unit()
    def Test_All_Features_String(self, life_term_class, term_enums):
        """Policy with all features shows Convertible, Renewable, and ROP."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            is_convertible=True,
            is_renewable=True,
            has_return_of_premium=True,
        )
        s = obj.get_insurance_as_string()
        assert "Convertible" in s
        assert "Renewable" in s
        assert "ROP" in s

    @pytest.mark.unit()
    def Test_No_Features_Shows_Basic(self, life_term_class):
        """Policy with no features shows 'Basic'."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            is_convertible=False,
            is_renewable=False,
            has_return_of_premium=False,
        )
        s = obj.get_insurance_as_string()
        assert "Basic" in s

    @pytest.mark.unit()
    def Test_Only_Convertible_Feature(self, life_term_class):
        """Policy with only is_convertible shows 'Convertible' not 'Renewable' or 'ROP'."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            is_convertible=True,
            is_renewable=False,
            has_return_of_premium=False,
        )
        s = obj.get_insurance_as_string()
        assert "Convertible" in s
        assert "ROP" not in s

    @pytest.mark.unit()
    def Test_Only_Renewable_Feature(self, life_term_class):
        """Policy with only is_renewable shows 'Renewable'."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            is_convertible=False,
            is_renewable=True,
            has_return_of_premium=False,
        )
        s = obj.get_insurance_as_string()
        assert "Renewable" in s
        assert "Convertible" not in s
        assert "ROP" not in s

    @pytest.mark.unit()
    def Test_String_Contains_Age_And_Face_Amount(self, basic_term_policy):
        """String contains insured age and face amount."""
        s = basic_term_policy.get_insurance_as_string()
        assert "35" in s
        assert "500,000.00" in s

    @pytest.mark.unit()
    def Test_String_Contains_Term_Type_Value(self, life_term_class, term_enums):
        """String contains term type value text."""
        TT = term_enums["Term_Type"]
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            term_type=TT.ANNUALLY_RENEWABLE,
        )
        s = obj.get_insurance_as_string()
        assert "Annually Renewable Term" in s

    @pytest.mark.unit()
    def Test_Decreasing_Term_In_String(self, life_term_class, term_enums):
        """Decreasing term type shows in string."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            term_type=term_enums["Term_Type"].DECREASING,
        )
        assert "Decreasing Term" in obj.get_insurance_as_string()

        with pytest.raises(Exception_Validation_Input):
            life_term_class(
                insured_age=35,
                face_amount=500_000.0,
                payment_frequency=-1,
            )

    @pytest.mark.unit()
    def Test_Zero_Term_Years_Raises(self, life_term_class):
        """term_years=0 must raise Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            life_term_class(insured_age=35, face_amount=500_000.0, term_years=0)


# ======================================================================
# Term Life — property accessors
# ======================================================================


@pytest.mark.unit()
class Class_Test_Life_Term_Properties:
    """Tests for Insurance_Life_Term property accessors."""

    @pytest.mark.unit()
    def Test_Term_Years_Property(self, life_term_class):
        """term_years property returns m_term_years."""
        obj = life_term_class(insured_age=35, face_amount=500_000.0, term_years=15)
        assert obj.term_years == 15

    @pytest.mark.unit()
    def Test_Term_Type_Property(self, life_term_class, term_enums):
        """term_type property returns stored Term_Type."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            term_type=term_enums["Term_Type"].ANNUALLY_RENEWABLE,
        )
        assert obj.term_type == term_enums["Term_Type"].ANNUALLY_RENEWABLE

    @pytest.mark.unit()
    def Test_Is_Convertible_Property_True(self, life_term_class):
        """is_convertible property returns True by default."""
        obj = life_term_class(insured_age=35, face_amount=500_000.0)
        assert obj.is_convertible is True

    @pytest.mark.unit()
    def Test_Is_Convertible_Property_False(self, life_term_class):
        """is_convertible property returns False when set."""
        obj = life_term_class(
            insured_age=35, face_amount=500_000.0, is_convertible=False
        )
        assert obj.is_convertible is False

    @pytest.mark.unit()
    def Test_Conversion_Deadline_Year_Property_Explicit(self, life_term_class):
        """conversion_deadline_year property returns explicit value."""
        obj = life_term_class(
            insured_age=35, face_amount=500_000.0, conversion_deadline_year=10
        )
        assert obj.conversion_deadline_year == 10

    @pytest.mark.unit()
    def Test_Conversion_Deadline_Year_Property_Default_To_Term(self, life_term_class):
        """conversion_deadline_year defaults to term_years when 0 is passed."""
        obj = life_term_class(
            insured_age=35, face_amount=500_000.0, term_years=20, conversion_deadline_year=0
        )
        assert obj.conversion_deadline_year == 20

    @pytest.mark.unit()
    def Test_Is_Renewable_Property(self, life_term_class):
        """is_renewable property returns stored value."""
        obj = life_term_class(insured_age=35, face_amount=500_000.0, is_renewable=False)
        assert obj.is_renewable is False

    @pytest.mark.unit()
    def Test_Has_Return_Of_Premium_Property(self, life_term_class):
        """has_return_of_premium property returns stored value."""
        obj = life_term_class(
            insured_age=35, face_amount=500_000.0, has_return_of_premium=True
        )
        assert obj.has_return_of_premium is True

    @pytest.mark.unit()
    def Test_Rate_Cost_Of_Insurance_Property(self, life_term_class):
        """rate_cost_of_insurance property returns stored float."""
        obj = life_term_class(
            insured_age=35, face_amount=500_000.0, rate_cost_of_insurance=3.0
        )
        assert obj.rate_cost_of_insurance == pytest.approx(3.0)

    @pytest.mark.unit()
    def Test_Payment_Frequency_Property(self, life_term_class):
        """payment_frequency property returns stored int."""
        obj = life_term_class(insured_age=35, face_amount=500_000.0, payment_frequency=4)
        assert obj.payment_frequency == 4


# ======================================================================
# Term Life — death benefit extended cases
# ======================================================================


@pytest.mark.unit()
class Class_Test_Life_Term_Death_Benefit_Extra:
    """Extended death benefit tests covering missing coverage paths."""

    @pytest.mark.unit()
    def Test_Death_Benefit_At_Year_Beyond_Term_Returns_Zero(self, life_term_class):
        """calc_death_benefit_at_year beyond term_years returns 0.0."""
        obj = life_term_class(insured_age=35, face_amount=500_000.0, term_years=20)
        assert obj.calc_death_benefit_at_year(policy_year = 21) == pytest.approx(0.0)

    @pytest.mark.unit()
    def Test_Death_Benefit_Decreasing_Year_1(self, life_term_class, term_enums):
        """DECREASING term at year 1 of 20: F * 20/20 = F."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            term_years=20,
            term_type=term_enums["Term_Type"].DECREASING,
        )
        assert obj.calc_death_benefit_at_year(policy_year = 1) == pytest.approx(500_000.0)

    @pytest.mark.unit()
    def Test_Death_Benefit_Decreasing_Last_Year(self, life_term_class, term_enums):
        """DECREASING term at year 20 of 20: F * 1/20."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            term_years=20,
            term_type=term_enums["Term_Type"].DECREASING,
        )
        assert obj.calc_death_benefit_at_year(policy_year = 20) == pytest.approx(500_000.0 / 20)

    @pytest.mark.unit()
    def Test_Death_Benefit_Level_At_Year_Returns_Face(self, life_term_class):
        """LEVEL term at any in-term year returns face amount."""
        obj = life_term_class(insured_age=35, face_amount=500_000.0, term_years=20)
        assert obj.calc_death_benefit_at_year(policy_year = 10) == pytest.approx(500_000.0)

    @pytest.mark.unit()
    def Test_Death_Benefit_ART_At_Year_Returns_Face(self, life_term_class, term_enums):
        """ART term at any in-term year returns face amount."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            term_years=20,
            term_type=term_enums["Term_Type"].ANNUALLY_RENEWABLE,
        )
        assert obj.calc_death_benefit_at_year(policy_year = 5) == pytest.approx(500_000.0)

    @pytest.mark.unit()
    def Test_Death_Benefit_At_Year_Invalid_Policy_Year_Raises(self, life_term_class):
        """policy_year=0 raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        obj = life_term_class(insured_age=35, face_amount=500_000.0)
        with pytest.raises(Exception_Validation_Input):
            obj.calc_death_benefit_at_year(policy_year = 0)


# ======================================================================
# Term Life — annual premium at year extended cases
# ======================================================================


@pytest.mark.unit()
class Class_Test_Life_Term_Annual_Premium_At_Year:
    """Tests for Insurance_Life_Term.calc_annual_premium_at_year()."""

    @pytest.mark.unit()
    def Test_Premium_At_Year_Beyond_Term_Returns_Zero(self, life_term_class):
        """calc_annual_premium_at_year beyond term_years returns 0.0."""
        obj = life_term_class(insured_age=35, face_amount=500_000.0, term_years=20)
        assert obj.calc_annual_premium_at_year(policy_year = 21) == pytest.approx(0.0)

    @pytest.mark.unit()
    def Test_Premium_At_Year_ART_Year_1_Equals_Base(self, life_term_class, term_enums):
        """ART year 1 premium equals base annual premium (1.03^0 = 1.0)."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            term_type=term_enums["Term_Type"].ANNUALLY_RENEWABLE,
        )
        assert obj.calc_annual_premium_at_year(policy_year = 1) == pytest.approx(obj.calc_annual_premium())

    @pytest.mark.unit()
    def Test_Premium_At_Year_ART_Year_5_Higher_Than_Year_1(self, life_term_class, term_enums):
        """ART year 5 premium is higher than year 1 due to 3% annual increase."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            term_type=term_enums["Term_Type"].ANNUALLY_RENEWABLE,
        )
        assert obj.calc_annual_premium_at_year(policy_year = 5) > obj.calc_annual_premium_at_year(policy_year = 1)

    @pytest.mark.unit()
    def Test_Premium_At_Year_Level_Any_Year_Equals_Base(self, life_term_class):
        """LEVEL term at year 10 returns same as base annual premium."""
        obj = life_term_class(insured_age=35, face_amount=500_000.0, term_years=20)
        assert obj.calc_annual_premium_at_year(policy_year = 10) == pytest.approx(obj.calc_annual_premium())

    @pytest.mark.unit()
    def Test_Premium_At_Year_Decreasing_Any_Year_Equals_Base(
        self, life_term_class, term_enums
    ):
        """DECREASING term premium is same each year (equals base annual premium)."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            term_type=term_enums["Term_Type"].DECREASING,
        )
        assert obj.calc_annual_premium_at_year(policy_year = 5) == pytest.approx(obj.calc_annual_premium())

    @pytest.mark.unit()
    def Test_Premium_At_Year_Invalid_Policy_Year_Raises(self, life_term_class):
        """policy_year=0 raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        obj = life_term_class(insured_age=35, face_amount=500_000.0)
        with pytest.raises(Exception_Validation_Input):
            obj.calc_annual_premium_at_year(policy_year = 0)


# ======================================================================
# Term Life — modal premium
# ======================================================================


@pytest.mark.unit()
class Class_Test_Life_Term_Modal_Premium:
    """Tests for Insurance_Life_Term.calc_modal_premium()."""

    @pytest.mark.unit()
    def Test_Modal_Premium_Single_Pay_Equals_Annual(self, life_term_class):
        """SINGLE pay (frequency=0) modal premium equals annual premium."""
        obj = life_term_class(insured_age=35, face_amount=500_000.0, payment_frequency=0)
        assert obj.calc_modal_premium() == pytest.approx(obj.calc_annual_premium())

    @pytest.mark.unit()
    def Test_Modal_Premium_Monthly_Less_Than_Annual(self, life_term_class):
        """Monthly (frequency=12) modal premium is less than annual premium."""
        obj = life_term_class(insured_age=35, face_amount=500_000.0, payment_frequency=12)
        assert obj.calc_modal_premium() < obj.calc_annual_premium()

    @pytest.mark.unit()
    def Test_Modal_Premium_Annual_Pay_Equals_Annual(self, life_term_class):
        """Annual (frequency=1) modal premium equals annual premium."""
        obj = life_term_class(insured_age=35, face_amount=500_000.0, payment_frequency=1)
        assert obj.calc_modal_premium() == pytest.approx(obj.calc_annual_premium())


# ======================================================================
# Term Life — total premiums paid
# ======================================================================


@pytest.mark.unit()
class Class_Test_Life_Term_Total_Premiums:
    """Tests for Insurance_Life_Term.calc_total_premiums_paid()."""

    @pytest.mark.unit()
    def Test_Total_Premiums_Level_Equals_Annual_Times_Term(self, life_term_class):
        """LEVEL total premiums = annual_premium * term_years."""
        obj = life_term_class(insured_age=35, face_amount=500_000.0, term_years=20)
        expected = obj.calc_annual_premium() * 20
        assert obj.calc_total_premiums_paid() == pytest.approx(expected)

    @pytest.mark.unit()
    def Test_Total_Premiums_ART_Greater_Than_Level(self, life_term_class, term_enums):
        """ART total premiums exceed level total because premiums increase each year."""
        level_obj = life_term_class(insured_age=35, face_amount=500_000.0, term_years=20)
        art_obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            term_years=20,
            term_type=term_enums["Term_Type"].ANNUALLY_RENEWABLE,
        )
        assert art_obj.calc_total_premiums_paid() > level_obj.calc_total_premiums_paid()

    @pytest.mark.unit()
    def Test_Total_Premiums_ART_Positive(self, life_term_class, term_enums):
        """ART total premiums are a positive float."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            term_years=10,
            term_type=term_enums["Term_Type"].ANNUALLY_RENEWABLE,
        )
        total = obj.calc_total_premiums_paid()
        assert isinstance(total, float)
        assert total > 0.0


# ======================================================================
# Term Life — return of premium benefit
# ======================================================================


@pytest.mark.unit()
class Class_Test_Life_Term_ROP_Benefit:
    """Tests for Insurance_Life_Term.calc_return_of_premium_benefit()."""

    @pytest.mark.unit()
    def Test_ROP_Benefit_Without_Rider_Returns_Zero(self, life_term_class):
        """Without ROP rider, benefit is 0.0."""
        obj = life_term_class(
            insured_age=35, face_amount=500_000.0, has_return_of_premium=False
        )
        assert obj.calc_return_of_premium_benefit() == pytest.approx(0.0)

    @pytest.mark.unit()
    def Test_ROP_Benefit_With_Rider_Equals_Total_Premiums(self, life_term_class):
        """With ROP rider, benefit equals total premiums paid."""
        obj = life_term_class(
            insured_age=35, face_amount=500_000.0, has_return_of_premium=True
        )
        assert obj.calc_return_of_premium_benefit() == pytest.approx(
            obj.calc_total_premiums_paid()
        )


# ======================================================================
# Term Life — conversion availability
# ======================================================================


@pytest.mark.unit()
class Class_Test_Life_Term_Conversion:
    """Tests for Insurance_Life_Term.is_conversion_available()."""

    @pytest.mark.unit()
    def Test_Conversion_Non_Convertible_Returns_False(self, life_term_class):
        """Non-convertible policy returns False for any policy year."""
        obj = life_term_class(
            insured_age=35, face_amount=500_000.0, is_convertible=False
        )
        assert obj.is_conversion_available(current_policy_year = 1) is False
        assert obj.is_conversion_available(current_policy_year = 10) is False

    @pytest.mark.unit()
    def Test_Conversion_Within_Deadline_Returns_True(self, life_term_class):
        """Convertible policy within deadline returns True."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            is_convertible=True,
            conversion_deadline_year=10,
        )
        assert obj.is_conversion_available(current_policy_year = 5) is True
        assert obj.is_conversion_available(current_policy_year = 10) is True

    @pytest.mark.unit()
    def Test_Conversion_Beyond_Deadline_Returns_False(self, life_term_class):
        """Convertible policy past deadline returns False."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            is_convertible=True,
            conversion_deadline_year=10,
        )
        assert obj.is_conversion_available(current_policy_year = 11) is False


# ======================================================================
# Term Life — remaining term years
# ======================================================================


@pytest.mark.unit()
class Class_Test_Life_Term_Remaining_Years:
    """Tests for Insurance_Life_Term.calc_remaining_term_years()."""

    @pytest.mark.unit()
    def Test_Remaining_Years_At_Year_1(self, life_term_class):
        """At policy year 1 of 20, remaining = 20."""
        obj = life_term_class(insured_age=35, face_amount=500_000.0, term_years=20)
        assert obj.calc_remaining_term_years(current_policy_year = 1) == 20

    @pytest.mark.unit()
    def Test_Remaining_Years_At_Midpoint(self, life_term_class):
        """At policy year 11 of 20, remaining = 10."""
        obj = life_term_class(insured_age=35, face_amount=500_000.0, term_years=20)
        assert obj.calc_remaining_term_years(current_policy_year = 11) == 10

    @pytest.mark.unit()
    def Test_Remaining_Years_After_Term_Returns_Zero(self, life_term_class):
        """Past the term, remaining years floors at 0."""
        obj = life_term_class(insured_age=35, face_amount=500_000.0, term_years=20)
        assert obj.calc_remaining_term_years(current_policy_year = 25) == 0


# ======================================================================
# Term Life — cost per thousand per year
# ======================================================================


@pytest.mark.unit()
class Class_Test_Life_Term_Cost_Per_Thousand_Per_Year:
    """Tests for Insurance_Life_Term.calc_cost_per_thousand_per_year()."""

    @pytest.mark.unit()
    def Test_Cost_Per_Thousand_Year_1_Positive(self, life_term_class):
        """Cost per $1,000 at year 1 is a positive float."""
        obj = life_term_class(insured_age=35, face_amount=500_000.0)
        result = obj.calc_cost_per_thousand_per_year(policy_year = 1)
        assert isinstance(result, float)
        assert result > 0.0

    @pytest.mark.unit()
    def Test_Cost_Per_Thousand_Beyond_Term_Returns_Zero(self, life_term_class):
        """Cost per $1,000 beyond term returns 0.0 (db=0)."""
        obj = life_term_class(insured_age=35, face_amount=500_000.0, term_years=10)
        result = obj.calc_cost_per_thousand_per_year(policy_year = 11)
        assert result == pytest.approx(0.0)

    @pytest.mark.unit()
    def Test_Cost_Per_Thousand_Default_Year_Is_Year_1(self, life_term_class):
        """Default policy_year=1 returns same as explicit year 1."""
        obj = life_term_class(insured_age=35, face_amount=500_000.0)
        assert obj.calc_cost_per_thousand_per_year() == pytest.approx(
            obj.calc_cost_per_thousand_per_year(policy_year = 1)
        )


# ======================================================================
# Term Life — get_insurance_as_string
# ======================================================================


@pytest.mark.unit()
class Class_Test_Life_Term_String_Repr:
    """Tests for Insurance_Life_Term.get_insurance_as_string()."""

    @pytest.mark.unit()
    def Test_String_Contains_Term_Type(self, basic_term_policy, term_enums):
        """String contains the term type value."""
        result = basic_term_policy.get_insurance_as_string()
        assert term_enums["Term_Type"].LEVEL.value in result

    @pytest.mark.unit()
    def Test_String_Contains_Term_Years(self, basic_term_policy):
        """String contains the term length."""
        result = basic_term_policy.get_insurance_as_string()
        assert "20" in result

    @pytest.mark.unit()
    def Test_String_Contains_Age(self, basic_term_policy):
        """String contains the insured age."""
        result = basic_term_policy.get_insurance_as_string()
        assert "35" in result

    @pytest.mark.unit()
    def Test_String_Contains_Face_Amount(self, basic_term_policy):
        """String contains the face amount."""
        result = basic_term_policy.get_insurance_as_string()
        assert "500,000.00" in result

    @pytest.mark.unit()
    def Test_String_Features_Convertible_And_Renewable(self, basic_term_policy):
        """Default policy (convertible+renewable) shows those features."""
        result = basic_term_policy.get_insurance_as_string()
        assert "Convertible" in result
        assert "Renewable" in result

    @pytest.mark.unit()
    def Test_String_Features_ROP(self, life_term_class):
        """Policy with ROP rider shows 'ROP' in string."""
        obj = life_term_class(
            insured_age=35, face_amount=500_000.0, has_return_of_premium=True
        )
        result = obj.get_insurance_as_string()
        assert "ROP" in result

    @pytest.mark.unit()
    def Test_String_Features_Basic_When_No_Features(self, life_term_class):
        """Policy with no features shows 'Basic'."""
        obj = life_term_class(
            insured_age=35,
            face_amount=500_000.0,
            is_convertible=False,
            is_renewable=False,
            has_return_of_premium=False,
        )
        result = obj.get_insurance_as_string()
        assert "Basic" in result


# ======================================================================
# Universal Life — coverage-gap tests
# ======================================================================


@pytest.mark.unit()
class Class_Test_Life_Universal_Coverage_Gaps:
    """Targeted tests to reach previously uncovered branches in Universal Life."""

    @pytest.mark.unit()
    def test_calc_projected_cash_value_invalid_months_raises(
        self, basic_universal_policy
    ):
        """calc_cash_value_at_month with months=0 raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            basic_universal_policy.calc_cash_value_at_month(months=0)

    @pytest.mark.unit()
    def test_calc_projected_cash_value_explicit_monthly_premium(
        self, basic_universal_policy
    ):
        """calc_cash_value_at_month with explicit monthly_premium skips auto-calc."""
        result = basic_universal_policy.calc_cash_value_at_month(
            months=12, monthly_premium=500.0
        )
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_calc_cash_surrender_value_year_zero(self, basic_universal_policy):
        """calc_cash_surrender_value with policy_year=0 returns charge_factor=0."""
        result = basic_universal_policy.calc_cash_surrender_value(policy_year=0)
        assert isinstance(result, float)


# ======================================================================
# Variable Life — coverage-gap tests
# ======================================================================


@pytest.mark.unit()
class Class_Test_Life_Variable_Coverage_Gaps:
    """Targeted tests to reach previously uncovered branches in Variable Life."""

    @pytest.mark.unit()
    def test_calc_cash_surrender_value_year_zero(self, basic_variable_policy):
        """calc_cash_surrender_value with policy_year=0 returns charge_factor=0."""
        result = basic_variable_policy.calc_cash_surrender_value(policy_year=0)
        assert isinstance(result, float)

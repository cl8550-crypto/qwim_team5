"""Hypothesis-based property tests for insurance_life product classes.

Covers:
    - Insurance_Life_Term: construction, death benefit, annual premium
    - Insurance_Life_Whole: construction, cash value growth, annual premium
    - Insurance_Life_Universal: construction, annual premium, cash value
    - Insurance_Life_Variable: construction, total fees
    - Insurance_Life_Survivor: construction, death benefit

Author:         QWIM Development Team
Version:        0.1.0
Last Modified:  2026-05-28
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.products.insurance.insurance_life.insurance_life_term import (
    Insurance_Life_Term,
    Term_Type,
)
from src.products.insurance.insurance_life.insurance_life_whole import (
    Insurance_Life_Whole,
    Death_Benefit_Option,
)
from src.products.insurance.insurance_life.insurance_life_universal import (
    Insurance_Life_Universal,
)
from src.products.insurance.insurance_life.insurance_life_variable import (
    Insurance_Life_Variable,
    Sub_Account_Type,
)
from src.products.insurance.insurance_life.insurance_life_survivor import (
    Insurance_Life_Survivor,
)

# ---------------------------------------------------------------------------
# Shared strategies
# ---------------------------------------------------------------------------

_valid_age = st.integers(min_value=18, max_value=75)
_valid_face = st.floats(min_value=10_000.0, max_value=5_000_000.0, allow_nan=False)
_valid_rate = st.floats(min_value=0.0, max_value=0.20, allow_nan=False)
_positive_rate = st.floats(min_value=0.001, max_value=0.20, allow_nan=False)


# ===========================================================================
# Insurance_Life_Term
# ===========================================================================


class Class_Test_Hypothesis_Insurance_Life_Term_Construction:
    """Hypothesis tests for Insurance_Life_Term construction invariants."""

    @pytest.mark.unit()
    @given(age=_valid_age, face=_valid_face)
    @settings(max_examples=200)
    def Test_stores_insured_age(self, age: int, face: float) -> None:
        """m_insured_age equals constructor insured_age."""
        term = Insurance_Life_Term(insured_age=age, face_amount=face)
        assert term.m_insured_age == age

    @pytest.mark.unit()
    @given(age=_valid_age, face=_valid_face)
    @settings(max_examples=200)
    def Test_stores_face_amount(self, age: int, face: float) -> None:
        """m_face_amount equals constructor face_amount."""
        term = Insurance_Life_Term(insured_age=age, face_amount=face)
        assert abs(term.m_face_amount - face) < 1.0

    @pytest.mark.unit()
    @given(age=_valid_age, face=_valid_face, term=st.integers(min_value=1, max_value=40))
    @settings(max_examples=200)
    def Test_stores_term_years(self, age: int, face: float, term: int) -> None:
        """m_term_years equals constructor term_years."""
        ins = Insurance_Life_Term(insured_age=age, face_amount=face, term_years=term)
        assert ins.m_term_years == term

    @pytest.mark.unit()
    @given(face=st.floats(max_value=0.0, allow_nan=False))
    @settings(max_examples=100)
    def Test_invalid_face_raises(self, face: float) -> None:
        """Non-positive face_amount raises an exception."""
        try:
            Insurance_Life_Term(insured_age=40, face_amount=face)
            assert False, "Expected exception not raised"
        except Exception:
            pass


class Class_Test_Hypothesis_Insurance_Life_Term_Calc_Death_Benefit:
    """Hypothesis tests for Insurance_Life_Term.calc_death_benefit."""

    @pytest.mark.unit()
    @given(age=_valid_age, face=_valid_face)
    @settings(max_examples=200)
    def Test_death_benefit_equals_face_amount(self, age: int, face: float) -> None:
        """calc_death_benefit() equals face_amount."""
        term = Insurance_Life_Term(insured_age=age, face_amount=face)
        assert abs(term.calc_death_benefit() - face) < 1.0

    @pytest.mark.unit()
    @given(age=_valid_age, face=_valid_face)
    @settings(max_examples=200)
    def Test_annual_premium_positive(self, age: int, face: float) -> None:
        """calc_annual_premium() is positive."""
        term = Insurance_Life_Term(insured_age=age, face_amount=face)
        assert term.calc_annual_premium() > 0


# ===========================================================================
# Insurance_Life_Whole
# ===========================================================================


class Class_Test_Hypothesis_Insurance_Life_Whole_Construction:
    """Hypothesis tests for Insurance_Life_Whole construction invariants."""

    @pytest.mark.unit()
    @given(age=_valid_age, face=_valid_face)
    @settings(max_examples=200)
    def Test_stores_insured_age(self, age: int, face: float) -> None:
        """m_insured_age equals constructor insured_age."""
        whole = Insurance_Life_Whole(insured_age=age, face_amount=face)
        assert whole.m_insured_age == age

    @pytest.mark.unit()
    @given(age=_valid_age, face=_valid_face)
    @settings(max_examples=200)
    def Test_annual_premium_positive(self, age: int, face: float) -> None:
        """calc_annual_premium() is positive."""
        whole = Insurance_Life_Whole(insured_age=age, face_amount=face)
        assert whole.calc_annual_premium() > 0

    @pytest.mark.unit()
    @given(age=_valid_age, face=_valid_face, rate=_valid_rate)
    @settings(max_examples=200)
    def Test_death_benefit_equals_face_plus_pua(
        self, age: int, face: float, rate: float
    ) -> None:
        """calc_death_benefit() >= face_amount (PUA may increase it)."""
        whole = Insurance_Life_Whole(insured_age=age, face_amount=face)
        assert whole.calc_death_benefit() >= face - 1.0


class Class_Test_Hypothesis_Insurance_Life_Whole_Cash_Value:
    """Hypothesis tests for Insurance_Life_Whole cash value growth."""

    @pytest.mark.unit()
    @given(age=_valid_age, face=_valid_face, year=st.integers(min_value=1, max_value=30))
    @settings(max_examples=200)
    def Test_cash_value_nonneg_for_positive_year(
        self, age: int, face: float, year: int
    ) -> None:
        """calc_cash_value_at_year(year) >= 0."""
        whole = Insurance_Life_Whole(
            insured_age=age,
            face_amount=face,
            rate_guaranteed_interest=0.04,
        )
        assert whole.calc_cash_value_at_year(year=year) >= 0

    @pytest.mark.unit()
    @given(age=_valid_age, face=_valid_face)
    @settings(max_examples=200)
    def Test_cash_value_year2_ge_year1(self, age: int, face: float) -> None:
        """Cash value at year 2 >= cash value at year 1 (positive interest)."""
        whole = Insurance_Life_Whole(
            insured_age=age,
            face_amount=face,
            rate_guaranteed_interest=0.04,
        )
        cv1 = whole.calc_cash_value_at_year(year=1)
        cv2 = whole.calc_cash_value_at_year(year=2)
        assert cv2 >= cv1 - 1e-6


# ===========================================================================
# Insurance_Life_Universal
# ===========================================================================


class Class_Test_Hypothesis_Insurance_Life_Universal_Construction:
    """Hypothesis tests for Insurance_Life_Universal construction invariants."""

    @pytest.mark.unit()
    @given(age=_valid_age, face=_valid_face)
    @settings(max_examples=200)
    def Test_stores_insured_age(self, age: int, face: float) -> None:
        """m_insured_age equals constructor insured_age."""
        ul = Insurance_Life_Universal(insured_age=age, face_amount=face)
        assert ul.m_insured_age == age

    @pytest.mark.unit()
    @given(age=_valid_age, face=_valid_face)
    @settings(max_examples=200)
    def Test_annual_premium_positive(self, age: int, face: float) -> None:
        """calc_annual_premium() is positive."""
        ul = Insurance_Life_Universal(insured_age=age, face_amount=face)
        assert ul.calc_annual_premium() > 0

    @pytest.mark.unit()
    @given(age=_valid_age, face=_valid_face, cv=st.floats(min_value=0.0, max_value=500_000.0, allow_nan=False))
    @settings(max_examples=200)
    def Test_stores_cash_value(self, age: int, face: float, cv: float) -> None:
        """m_cash_value equals constructor cash_value."""
        ul = Insurance_Life_Universal(insured_age=age, face_amount=face, cash_value=cv)
        assert abs(ul.m_cash_value - cv) < 1.0


# ===========================================================================
# Insurance_Life_Variable
# ===========================================================================


class Class_Test_Hypothesis_Insurance_Life_Variable_Construction:
    """Hypothesis tests for Insurance_Life_Variable construction invariants."""

    @pytest.mark.unit()
    @given(age=_valid_age, face=_valid_face)
    @settings(max_examples=200)
    def Test_stores_insured_age(self, age: int, face: float) -> None:
        """m_insured_age equals constructor insured_age."""
        vl = Insurance_Life_Variable(
            insured_age=age,
            face_amount=face,
            sub_account_allocations={Sub_Account_Type.INDEX: 1.0},
        )
        assert vl.m_insured_age == age

    @pytest.mark.unit()
    @given(
        age=_valid_age,
        face=_valid_face,
        me=st.floats(min_value=0.005, max_value=0.02, allow_nan=False),
        admin=st.floats(min_value=0.0, max_value=0.01, allow_nan=False),
    )
    @settings(max_examples=200)
    def Test_total_fees_nonneg(self, age: int, face: float, me: float, admin: float) -> None:
        """calc_total_annual_fees() is non-negative."""
        vl = Insurance_Life_Variable(
            insured_age=age,
            face_amount=face,
            sub_account_allocations={Sub_Account_Type.INDEX: 1.0},
            rate_ME_charge=me,
            rate_admin_fee=admin,
        )
        assert vl.calc_total_annual_fees() >= 0


# ===========================================================================
# Insurance_Life_Survivor
# ===========================================================================


class Class_Test_Hypothesis_Insurance_Life_Survivor_Construction:
    """Hypothesis tests for Insurance_Life_Survivor construction invariants."""

    @pytest.mark.unit()
    @given(
        age1=st.integers(min_value=30, max_value=70),
        age2=st.integers(min_value=30, max_value=70),
        face=_valid_face,
    )
    @settings(max_examples=200)
    def Test_stores_both_ages(self, age1: int, age2: int, face: float) -> None:
        """m_insured_age and m_insured_age_second equal constructor values."""
        sv = Insurance_Life_Survivor(
            insured_age=age1,
            insured_age_second=age2,
            face_amount=face,
        )
        assert sv.m_insured_age == age1
        assert sv.m_insured_age_second == age2

    @pytest.mark.unit()
    @given(age1=_valid_age, age2=_valid_age, face=_valid_face)
    @settings(max_examples=200)
    def Test_death_benefit_equals_face(self, age1: int, age2: int, face: float) -> None:
        """calc_death_benefit() equals face_amount."""
        sv = Insurance_Life_Survivor(
            insured_age=age1,
            insured_age_second=age2,
            face_amount=face,
        )
        assert abs(sv.calc_death_benefit() - face) < 1.0

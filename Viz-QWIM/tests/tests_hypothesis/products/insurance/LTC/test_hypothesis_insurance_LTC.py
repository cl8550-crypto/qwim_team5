"""Hypothesis-based property tests for insurance_LTC product classes.

Covers:
    - Insurance_LTC_Traditional: construction, annual premium, max lifetime benefit
    - Insurance_LTC_Hybrid_Annuity: construction, annual premium, benefit leverage
    - Insurance_LTC_Hybrid_Life: construction, annual premium, benefit leverage

Author:         QWIM Development Team
Version:        0.1.0
Last Modified:  2026-05-28
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.products.insurance.insurance_LTC.insurance_LTC_traditional import (
    Insurance_LTC_Traditional,
    Gender_LTC,
    Health_Class_LTC,
)
from src.products.insurance.insurance_LTC.insurance_LTC_hybrid_annuity import (
    Insurance_LTC_Hybrid_Annuity,
    LTC_Multiplier,
)
from src.products.insurance.insurance_LTC.insurance_LTC_hybrid_life import (
    Insurance_LTC_Hybrid_Life,
)

# ---------------------------------------------------------------------------
# Shared strategies
# ---------------------------------------------------------------------------

_valid_age = st.integers(min_value=40, max_value=75)
_valid_daily_benefit = st.floats(min_value=50.0, max_value=1000.0, allow_nan=False)
_valid_premium = st.floats(min_value=25_000.0, max_value=500_000.0, allow_nan=False)
_valid_death_benefit = st.floats(min_value=50_000.0, max_value=2_000_000.0, allow_nan=False)
_gender = st.sampled_from([Gender_LTC.MALE, Gender_LTC.FEMALE])


# ===========================================================================
# Insurance_LTC_Traditional
# ===========================================================================


class Class_Test_Hypothesis_Insurance_LTC_Traditional_Construction:
    """Hypothesis tests for Insurance_LTC_Traditional construction invariants."""

    @pytest.mark.unit()
    @given(age=_valid_age, daily=_valid_daily_benefit, gender=_gender)
    @settings(max_examples=200)
    def Test_stores_insured_age(self, age: int, daily: float, gender: Gender_LTC) -> None:
        """m_insured_age equals constructor insured_age."""
        trad = Insurance_LTC_Traditional(
            insured_age=age,
            daily_benefit_amount=daily,
            gender=gender,
        )
        assert trad.m_insured_age == age

    @pytest.mark.unit()
    @given(age=_valid_age, daily=_valid_daily_benefit, gender=_gender)
    @settings(max_examples=200)
    def Test_stores_daily_benefit(self, age: int, daily: float, gender: Gender_LTC) -> None:
        """m_daily_benefit_amount equals constructor daily_benefit_amount."""
        trad = Insurance_LTC_Traditional(
            insured_age=age,
            daily_benefit_amount=daily,
            gender=gender,
        )
        assert abs(trad.m_daily_benefit_amount - daily) < 1e-6

    @pytest.mark.unit()
    @given(age=_valid_age, daily=_valid_daily_benefit, gender=_gender)
    @settings(max_examples=200)
    def Test_annual_premium_positive(self, age: int, daily: float, gender: Gender_LTC) -> None:
        """calc_annual_premium() is positive."""
        trad = Insurance_LTC_Traditional(
            insured_age=age,
            daily_benefit_amount=daily,
            gender=gender,
        )
        assert trad.calc_annual_premium() > 0


class Class_Test_Hypothesis_Insurance_LTC_Traditional_Calc_Benefit:
    """Hypothesis tests for Insurance_LTC_Traditional benefit calculations."""

    @pytest.mark.unit()
    @given(age=_valid_age, daily=_valid_daily_benefit, gender=_gender)
    @settings(max_examples=200)
    def Test_max_lifetime_benefit_positive(
        self, age: int, daily: float, gender: Gender_LTC
    ) -> None:
        """calc_maximum_lifetime_benefit() is positive."""
        trad = Insurance_LTC_Traditional(
            insured_age=age,
            daily_benefit_amount=daily,
            gender=gender,
        )
        assert trad.calc_maximum_lifetime_benefit() > 0

    @pytest.mark.unit()
    @given(age=_valid_age, daily=_valid_daily_benefit, gender=_gender)
    @settings(max_examples=200)
    def Test_monthly_benefit_equals_daily_times_30(
        self, age: int, daily: float, gender: Gender_LTC
    ) -> None:
        """calc_monthly_benefit_amount() equals daily * 30."""
        trad = Insurance_LTC_Traditional(
            insured_age=age,
            daily_benefit_amount=daily,
            gender=gender,
        )
        assert abs(trad.calc_monthly_benefit_amount() - daily * 30) < 1e-6

    @pytest.mark.unit()
    @given(age=_valid_age, daily=_valid_daily_benefit, gender=_gender, year=st.integers(min_value=1, max_value=20))
    @settings(max_examples=200)
    def Test_daily_benefit_at_year_ge_initial(
        self, age: int, daily: float, gender: Gender_LTC, year: int
    ) -> None:
        """calc_daily_benefit_at_year(year) >= daily_benefit_amount (inflation increases it)."""
        trad = Insurance_LTC_Traditional(
            insured_age=age,
            daily_benefit_amount=daily,
            gender=gender,
        )
        assert trad.calc_daily_benefit_at_year(year=year) >= daily - 1e-6


# ===========================================================================
# Insurance_LTC_Hybrid_Annuity
# ===========================================================================


class Class_Test_Hypothesis_Insurance_LTC_Hybrid_Annuity_Construction:
    """Hypothesis tests for Insurance_LTC_Hybrid_Annuity construction invariants."""

    @pytest.mark.unit()
    @given(age=_valid_age, premium=_valid_premium)
    @settings(max_examples=200)
    def Test_stores_insured_age(self, age: int, premium: float) -> None:
        """m_insured_age equals constructor insured_age."""
        ha = Insurance_LTC_Hybrid_Annuity(
            insured_age=age,
            single_premium=premium,
        )
        assert ha.m_insured_age == age

    @pytest.mark.unit()
    @given(age=_valid_age, premium=_valid_premium)
    @settings(max_examples=200)
    def Test_annual_premium_equals_single_premium(self, age: int, premium: float) -> None:
        """calc_annual_premium() equals single_premium (single-pay product)."""
        ha = Insurance_LTC_Hybrid_Annuity(
            insured_age=age,
            single_premium=premium,
        )
        assert abs(ha.calc_annual_premium() - premium) < 1.0

    @pytest.mark.unit()
    @given(age=_valid_age, premium=_valid_premium, multiplier=st.sampled_from(list(LTC_Multiplier)))
    @settings(max_examples=200)
    def Test_max_lifetime_benefit_ge_premium(
        self, age: int, premium: float, multiplier: LTC_Multiplier
    ) -> None:
        """calc_maximum_lifetime_benefit() >= single_premium when LTC_multiplier > 1."""
        ha = Insurance_LTC_Hybrid_Annuity(
            insured_age=age,
            single_premium=premium,
            LTC_multiplier=multiplier,
        )
        assert ha.calc_maximum_lifetime_benefit() >= premium - 1e-6

    @pytest.mark.unit()
    @given(age=_valid_age, premium=_valid_premium)
    @settings(max_examples=200)
    def Test_benefit_leverage_ratio_positive(self, age: int, premium: float) -> None:
        """calc_benefit_leverage_ratio() is positive."""
        ha = Insurance_LTC_Hybrid_Annuity(
            insured_age=age,
            single_premium=premium,
        )
        assert ha.calc_benefit_leverage_ratio() > 0


# ===========================================================================
# Insurance_LTC_Hybrid_Life
# ===========================================================================


class Class_Test_Hypothesis_Insurance_LTC_Hybrid_Life_Construction:
    """Hypothesis tests for Insurance_LTC_Hybrid_Life construction invariants."""

    @pytest.mark.unit()
    @given(age=_valid_age, db=_valid_death_benefit, premium=_valid_premium)
    @settings(max_examples=200)
    def Test_stores_insured_age(self, age: int, db: float, premium: float) -> None:
        """m_insured_age equals constructor insured_age."""
        hl = Insurance_LTC_Hybrid_Life(
            insured_age=age,
            death_benefit=db,
            single_premium=premium,
        )
        assert hl.m_insured_age == age

    @pytest.mark.unit()
    @given(age=_valid_age, db=_valid_death_benefit, premium=_valid_premium)
    @settings(max_examples=200)
    def Test_annual_premium_equals_single_premium(
        self, age: int, db: float, premium: float
    ) -> None:
        """calc_annual_premium() equals single_premium."""
        hl = Insurance_LTC_Hybrid_Life(
            insured_age=age,
            death_benefit=db,
            single_premium=premium,
        )
        assert abs(hl.calc_annual_premium() - premium) < 1.0

    @pytest.mark.unit()
    @given(age=_valid_age, db=_valid_death_benefit, premium=_valid_premium)
    @settings(max_examples=200)
    def Test_benefit_leverage_ratio_positive(
        self, age: int, db: float, premium: float
    ) -> None:
        """calc_benefit_leverage_ratio() is positive."""
        hl = Insurance_LTC_Hybrid_Life(
            insured_age=age,
            death_benefit=db,
            single_premium=premium,
        )
        assert hl.calc_benefit_leverage_ratio() > 0

    @pytest.mark.unit()
    @given(age=_valid_age, db=_valid_death_benefit, premium=_valid_premium)
    @settings(max_examples=200)
    def Test_max_lifetime_benefit_positive(
        self, age: int, db: float, premium: float
    ) -> None:
        """calc_maximum_lifetime_benefit() is positive."""
        hl = Insurance_LTC_Hybrid_Life(
            insured_age=age,
            death_benefit=db,
            single_premium=premium,
        )
        assert hl.calc_maximum_lifetime_benefit() > 0

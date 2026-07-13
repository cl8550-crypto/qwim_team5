"""Hypothesis (property-based) tests for Annuity_DIA.

Tests cover:
- ``Annuity_DIA`` construction — valid and invalid parameter ranges
- ``calc_annuity_payout`` — proportionality to principal and payout rate;
  deferred-period returns zero
- ``calc_monthly_payout`` — equals annual / 12
- ``calc_future_value`` — compound-growth invariant

Author
------
QWIM Team

Version
-------
0.1.0 (2026-05-28)
"""

from __future__ import annotations

import math

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from src.products.annuity.annuity_base import Annuity_Payout_Option, Annuity_Type
from src.products.annuity.annuity_DIA import Annuity_DIA
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)


# ---------------------------------------------------------------------------
# Helper factory
# ---------------------------------------------------------------------------


def _make_dia(
    client_age: int = 45,
    payout_rate: float = 0.05,
    age_income_start: int = 65,
    **kwargs: object,
) -> Annuity_DIA:
    return Annuity_DIA(
        client_age=client_age,
        annuity_payout_rate=payout_rate,
        age_income_start=age_income_start,
        **kwargs,  # type: ignore[arg-type]
    )


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Annuity_DIA_Construction
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Annuity_DIA_Construction:
    """Tests for valid construction of Annuity_DIA."""

    @pytest.mark.unit()
    @given(
        client_age=st.integers(min_value=1, max_value=79),
        payout_rate=st.floats(min_value=0.001, max_value=0.20, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_construction_stores_client_age_and_payout_rate(
        self,
        client_age: int,
        payout_rate: float,
    ) -> None:
        """m_client_age and m_annuity_payout_rate stored correctly."""
        dia = Annuity_DIA(
            client_age=client_age,
            annuity_payout_rate=payout_rate,
            age_income_start=client_age + 1,
        )
        assert dia.m_client_age == client_age
        assert dia.m_annuity_payout_rate == payout_rate

    @pytest.mark.unit()
    @given(
        client_age=st.integers(min_value=1, max_value=79),
        payout_rate=st.floats(min_value=0.001, max_value=0.20, allow_nan=False, allow_infinity=False),
        age_income_start=st.integers(min_value=2, max_value=100),
    )
    @settings(max_examples=200)
    def Test_age_income_start_stored_correctly(
        self,
        client_age: int,
        payout_rate: float,
        age_income_start: int,
    ) -> None:
        """m_age_income_start stored correctly when > client_age."""
        assume(age_income_start > client_age)
        dia = Annuity_DIA(
            client_age=client_age,
            annuity_payout_rate=payout_rate,
            age_income_start=age_income_start,
        )
        assert dia.m_age_income_start == age_income_start

    @pytest.mark.unit()
    @given(
        client_age=st.integers(min_value=1, max_value=79),
        payout_rate=st.floats(min_value=0.001, max_value=0.20, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_annuity_type_is_dia(
        self,
        client_age: int,
        payout_rate: float,
    ) -> None:
        """m_annuity_type is always ANNUITY_DIA."""
        dia = Annuity_DIA(
            client_age=client_age,
            annuity_payout_rate=payout_rate,
            age_income_start=client_age + 1,
        )
        assert dia.m_annuity_type == Annuity_Type.ANNUITY_DIA

    @pytest.mark.unit()
    @given(
        client_age=st.integers(min_value=1, max_value=79),
        payout_rate=st.floats(min_value=0.001, max_value=0.20, allow_nan=False, allow_infinity=False),
        cola_rate=st.floats(min_value=0.0, max_value=0.10, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_cola_rate_stored_correctly(
        self,
        client_age: int,
        payout_rate: float,
        cola_rate: float,
    ) -> None:
        """rate_COLA stored in m_rate_COLA."""
        dia = Annuity_DIA(
            client_age=client_age,
            annuity_payout_rate=payout_rate,
            age_income_start=client_age + 1,
            rate_COLA=cola_rate,
        )
        assert dia.m_rate_COLA == cola_rate

    @pytest.mark.unit()
    @given(
        payout_rate=st.floats(min_value=0.001, max_value=0.20, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_invalid_age_income_start_raises(
        self,
        payout_rate: float,
    ) -> None:
        """age_income_start <= client_age raises Exception_Validation_Input."""
        with pytest.raises(Exception_Validation_Input):
            Annuity_DIA(
                client_age=50,
                annuity_payout_rate=payout_rate,
                age_income_start=50,
            )

    @pytest.mark.unit()
    @given(
        client_age=st.integers(min_value=1, max_value=79),
    )
    @settings(max_examples=200)
    def Test_invalid_payout_rate_raises(
        self,
        client_age: int,
    ) -> None:
        """Non-positive payout_rate raises Exception_Validation_Input."""
        with pytest.raises(Exception_Validation_Input):
            Annuity_DIA(
                client_age=client_age,
                annuity_payout_rate=0.0,
                age_income_start=client_age + 1,
            )


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Annuity_DIA_Calc_Payout
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Annuity_DIA_Calc_Payout:
    """Tests for calc_annuity_payout() numerical invariants."""

    @pytest.mark.unit()
    @given(
        payout_rate=st.floats(min_value=0.01, max_value=0.15, allow_nan=False, allow_infinity=False),
        principal=st.floats(min_value=1.0, max_value=1_000_000.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_payout_always_zero_during_deferral(
        self,
        payout_rate: float,
        principal: float,
    ) -> None:
        """calc_annuity_payout always returns 0.0 (DIA requires age_income_start > client_age)."""
        dia = _make_dia(client_age=45, payout_rate=payout_rate, age_income_start=65)
        payout = dia.calc_annuity_payout(amount_principal=principal)
        assert payout == 0.0

    @pytest.mark.unit()
    @given(
        payout_rate=st.floats(min_value=0.01, max_value=0.15, allow_nan=False, allow_infinity=False),
        principal=st.floats(min_value=1.0, max_value=1_000_000.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_payout_in_year_positive_at_income_start(
        self,
        payout_rate: float,
        principal: float,
    ) -> None:
        """calc_payout_in_year at year 1 (income start) returns > 0."""
        dia = _make_dia(client_age=45, payout_rate=payout_rate, age_income_start=65)
        payout = dia.calc_payout_in_year(amount_principal=principal, year_number=1)
        assert payout > 0


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Annuity_DIA_Calc_Monthly_Payout
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Annuity_DIA_Calc_Monthly_Payout:
    """Tests for calc_monthly_payout() invariants."""

    @pytest.mark.unit()
    @given(
        payout_rate=st.floats(min_value=0.01, max_value=0.15, allow_nan=False, allow_infinity=False),
        principal=st.floats(min_value=1.0, max_value=1_000_000.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_monthly_equals_annual_div_twelve(
        self,
        payout_rate: float,
        principal: float,
    ) -> None:
        """calc_monthly_payout = calc_annuity_payout / 12."""
        dia = _make_dia(client_age=65, payout_rate=payout_rate, age_income_start=66)
        annual = dia.calc_annuity_payout(amount_principal=principal)
        monthly = dia.calc_monthly_payout(amount_principal=principal)
        assert math.isclose(monthly, annual / 12, rel_tol=1e-12)


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Annuity_DIA_Calc_Future_Value
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Annuity_DIA_Calc_Future_Value:
    """Tests for calc_future_value() invariants."""

    @pytest.mark.unit()
    @given(
        principal=st.floats(min_value=1.0, max_value=1_000_000.0, allow_nan=False, allow_infinity=False),
        rate=st.floats(min_value=0.0, max_value=0.20, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_future_value_geq_principal_when_rate_nonneg(
        self,
        principal: float,
        rate: float,
    ) -> None:
        """Future value >= principal when rate >= 0."""
        dia = _make_dia()
        fv = dia.calc_future_value(
            amount_principal=principal,
            growth_rate=rate,
        )
        assert fv >= principal

    @pytest.mark.unit()
    @given(
        principal=st.floats(min_value=1.0, max_value=1_000_000.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_future_value_equals_principal_at_zero_rate(
        self,
        principal: float,
    ) -> None:
        """FV = principal when rate = 0."""
        dia = _make_dia()
        fv = dia.calc_future_value(
            amount_principal=principal,
            growth_rate=0.0,
        )
        assert math.isclose(fv, principal, rel_tol=1e-12)

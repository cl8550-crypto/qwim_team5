"""Hypothesis (property-based) tests for Annuity_FIA.

Tests cover:
- ``Annuity_FIA`` construction — valid parameter storage
- ``calc_credited_rate`` — floor invariant; cap invariant; non-negativity
- ``calc_annuity_payout`` — deferred-period returns zero; proportional to
  principal (via benefit base × payout_rate)
- ``calc_monthly_payout`` — equals annual / 12

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

from src.products.annuity.annuity_base import Annuity_Type
from src.products.annuity.annuity_FIA import Annuity_FIA
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)


# ---------------------------------------------------------------------------
# Helper factory
# ---------------------------------------------------------------------------


def _make_fia(
    client_age: int = 45,
    payout_rate: float = 0.05,
    age_income_start: int = 65,
    age_max_ratchet: int = 70,
    rate_rollup_benefit: float = 0.05,
    floor_rate: float = 0.0,
    cap_rate: float = 0.07,
    participation_rate: float = 1.0,
    **kwargs: object,
) -> Annuity_FIA:
    return Annuity_FIA(
        client_age=client_age,
        annuity_payout_rate=payout_rate,
        age_income_start=age_income_start,
        age_max_ratchet=age_max_ratchet,
        rate_rollup_benefit=rate_rollup_benefit,
        floor_rate=floor_rate,
        cap_rate=cap_rate,
        participation_rate=participation_rate,
        **kwargs,  # type: ignore[arg-type]
    )


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Annuity_FIA_Construction
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Annuity_FIA_Construction:
    """Tests for valid construction of Annuity_FIA."""

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
        fia = Annuity_FIA(
            client_age=client_age,
            annuity_payout_rate=payout_rate,
            age_income_start=client_age + 1,
            age_max_ratchet=client_age + 5,
            rate_rollup_benefit=0.05,
        )
        assert fia.m_client_age == client_age
        assert fia.m_annuity_payout_rate == payout_rate

    @pytest.mark.unit()
    @given(
        client_age=st.integers(min_value=1, max_value=79),
        payout_rate=st.floats(min_value=0.001, max_value=0.20, allow_nan=False, allow_infinity=False),
        cap_rate=st.floats(min_value=0.01, max_value=0.30, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_cap_rate_stored_correctly(
        self,
        client_age: int,
        payout_rate: float,
        cap_rate: float,
    ) -> None:
        """m_cap_rate is stored correctly."""
        fia = Annuity_FIA(
            client_age=client_age,
            annuity_payout_rate=payout_rate,
            age_income_start=client_age + 1,
            age_max_ratchet=client_age + 5,
            rate_rollup_benefit=0.05,
            cap_rate=cap_rate,
        )
        assert fia.m_cap_rate == cap_rate

    @pytest.mark.unit()
    @given(
        client_age=st.integers(min_value=1, max_value=79),
        payout_rate=st.floats(min_value=0.001, max_value=0.20, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_annuity_type_is_fia(
        self,
        client_age: int,
        payout_rate: float,
    ) -> None:
        """m_annuity_type is always ANNUITY_FIA."""
        fia = Annuity_FIA(
            client_age=client_age,
            annuity_payout_rate=payout_rate,
            age_income_start=client_age + 1,
            age_max_ratchet=client_age + 5,
            rate_rollup_benefit=0.05,
        )
        assert fia.m_annuity_type == Annuity_Type.ANNUITY_FIA

    @pytest.mark.unit()
    @given(
        payout_rate=st.floats(min_value=0.001, max_value=0.20, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_invalid_client_age_raises(
        self,
        payout_rate: float,
    ) -> None:
        """Non-positive client_age raises Exception_Validation_Input."""
        with pytest.raises(Exception_Validation_Input):
            Annuity_FIA(
                client_age=0,
                annuity_payout_rate=payout_rate,
                age_income_start=65,
                age_max_ratchet=70,
                rate_rollup_benefit=0.05,
            )


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Annuity_FIA_Credited_Rate
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Annuity_FIA_Credited_Rate:
    """Tests for calc_credited_rate() numerical invariants."""

    @pytest.mark.unit()
    @given(
        index_return=st.floats(min_value=-0.50, max_value=0.50, allow_nan=False, allow_infinity=False),
        floor_rate=st.floats(min_value=0.0, max_value=0.05, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_credited_rate_geq_floor(
        self,
        index_return: float,
        floor_rate: float,
    ) -> None:
        """calc_credited_rate() is always >= floor_rate."""
        fia = _make_fia(floor_rate=floor_rate)
        rate = fia.calc_credited_rate(index_return=index_return)
        assert rate >= floor_rate - 1e-12

    @pytest.mark.unit()
    @given(
        index_return=st.floats(min_value=0.0, max_value=0.50, allow_nan=False, allow_infinity=False),
        cap_rate=st.floats(min_value=0.01, max_value=0.30, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_credited_rate_leq_cap(
        self,
        index_return: float,
        cap_rate: float,
    ) -> None:
        """calc_credited_rate() is always <= cap_rate for positive returns."""
        fia = _make_fia(cap_rate=cap_rate)
        rate = fia.calc_credited_rate(index_return=index_return)
        assert rate <= cap_rate + 1e-12

    @pytest.mark.unit()
    @given(
        index_return=st.floats(min_value=-0.50, max_value=0.50, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_credited_rate_nonneg_with_zero_floor(
        self,
        index_return: float,
    ) -> None:
        """With floor_rate=0, credited_rate >= 0 for any index_return."""
        fia = _make_fia(floor_rate=0.0)
        rate = fia.calc_credited_rate(index_return=index_return)
        assert rate >= -1e-12


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Annuity_FIA_Calc_Payout
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Annuity_FIA_Calc_Payout:
    """Tests for calc_annuity_payout() numerical invariants."""

    @pytest.mark.unit()
    @given(
        payout_rate=st.floats(min_value=0.01, max_value=0.15, allow_nan=False, allow_infinity=False),
        principal=st.floats(min_value=1.0, max_value=1_000_000.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_payout_zero_during_deferral(
        self,
        payout_rate: float,
        principal: float,
    ) -> None:
        """calc_annuity_payout returns 0.0 when client_age < age_income_start."""
        fia = _make_fia(client_age=45, payout_rate=payout_rate, age_income_start=65)
        payout = fia.calc_annuity_payout(amount_principal=principal)
        assert payout == 0.0

    @pytest.mark.unit()
    @given(
        payout_rate=st.floats(min_value=0.01, max_value=0.15, allow_nan=False, allow_infinity=False),
        principal=st.floats(min_value=1.0, max_value=1_000_000.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_payout_positive_at_income_start_age(
        self,
        payout_rate: float,
        principal: float,
    ) -> None:
        """calc_annuity_payout > 0 when m_client_age >= age_income_start."""
        fia = _make_fia(client_age=64, payout_rate=payout_rate, age_income_start=65)
        fia.m_client_age = 65
        payout = fia.calc_annuity_payout(amount_principal=principal)
        assert payout > 0

    @pytest.mark.unit()
    @given(
        payout_rate=st.floats(min_value=0.01, max_value=0.15, allow_nan=False, allow_infinity=False),
        principal_a=st.floats(min_value=1.0, max_value=500_000.0, allow_nan=False, allow_infinity=False),
        principal_b=st.floats(min_value=1.0, max_value=500_000.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_payout_proportional_to_principal(
        self,
        payout_rate: float,
        principal_a: float,
        principal_b: float,
    ) -> None:
        """Payout scales linearly with principal: P(a)/P(b) = a/b."""
        assume(principal_b > 0.01)
        fia = _make_fia(client_age=64, payout_rate=payout_rate, age_income_start=65)
        fia.m_client_age = 65
        payout_a = fia.calc_annuity_payout(amount_principal=principal_a)
        payout_b = fia.calc_annuity_payout(amount_principal=principal_b)
        assume(payout_b > 0.0)
        assert math.isclose(payout_a / payout_b, principal_a / principal_b, rel_tol=1e-9)


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Annuity_FIA_Calc_Monthly_Payout
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Annuity_FIA_Calc_Monthly_Payout:
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
        fia = _make_fia(client_age=64, payout_rate=payout_rate, age_income_start=65)
        fia.m_client_age = 65
        annual = fia.calc_annuity_payout(amount_principal=principal)
        monthly = fia.calc_monthly_payout(amount_principal=principal)
        assert math.isclose(monthly, annual / 12, rel_tol=1e-12)

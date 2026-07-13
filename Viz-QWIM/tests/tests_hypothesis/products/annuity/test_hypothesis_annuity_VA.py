"""Hypothesis (property-based) tests for Annuity_VA.

Tests cover:
- ``Annuity_VA`` construction — valid parameter storage
- ``calc_total_annual_charges`` — sum of ME + admin + rider charges
- ``calc_annuity_payout`` — deferred-period returns zero; proportional to
  principal; positive at income start age
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
from src.products.annuity.annuity_VA import Annuity_VA
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)


# ---------------------------------------------------------------------------
# Helper factory
# ---------------------------------------------------------------------------


def _make_va(
    client_age: int = 45,
    payout_rate: float = 0.05,
    age_income_start: int = 65,
    age_max_ratchet: int = 70,
    rate_rollup_benefit: float = 0.05,
    rate_ME_charge: float = 0.0125,
    rate_admin_fee: float = 0.0015,
    rate_rider_charge: float = 0.0100,
    **kwargs: object,
) -> Annuity_VA:
    return Annuity_VA(
        client_age=client_age,
        annuity_payout_rate=payout_rate,
        age_income_start=age_income_start,
        age_max_ratchet=age_max_ratchet,
        rate_rollup_benefit=rate_rollup_benefit,
        rate_ME_charge=rate_ME_charge,
        rate_admin_fee=rate_admin_fee,
        rate_rider_charge=rate_rider_charge,
        **kwargs,  # type: ignore[arg-type]
    )


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Annuity_VA_Construction
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Annuity_VA_Construction:
    """Tests for valid construction of Annuity_VA."""

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
        va = Annuity_VA(
            client_age=client_age,
            annuity_payout_rate=payout_rate,
            age_income_start=client_age + 1,
            age_max_ratchet=client_age + 5,
            rate_rollup_benefit=0.05,
        )
        assert va.m_client_age == client_age
        assert va.m_annuity_payout_rate == payout_rate

    @pytest.mark.unit()
    @given(
        client_age=st.integers(min_value=1, max_value=79),
        payout_rate=st.floats(min_value=0.001, max_value=0.20, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_annuity_type_is_va(
        self,
        client_age: int,
        payout_rate: float,
    ) -> None:
        """m_annuity_type is always ANNUITY_VA."""
        va = Annuity_VA(
            client_age=client_age,
            annuity_payout_rate=payout_rate,
            age_income_start=client_age + 1,
            age_max_ratchet=client_age + 5,
            rate_rollup_benefit=0.05,
        )
        assert va.m_annuity_type == Annuity_Type.ANNUITY_VA

    @pytest.mark.unit()
    @given(
        client_age=st.integers(min_value=1, max_value=79),
        payout_rate=st.floats(min_value=0.001, max_value=0.20, allow_nan=False, allow_infinity=False),
        has_gmdb=st.booleans(),
        has_glwb=st.booleans(),
    )
    @settings(max_examples=200)
    def Test_has_gmdb_and_glwb_stored_correctly(
        self,
        client_age: int,
        payout_rate: float,
        has_gmdb: bool,
        has_glwb: bool,
    ) -> None:
        """m_has_GMDB and m_has_GLWB stored correctly."""
        va = Annuity_VA(
            client_age=client_age,
            annuity_payout_rate=payout_rate,
            age_income_start=client_age + 1,
            age_max_ratchet=client_age + 5,
            rate_rollup_benefit=0.05,
            has_GMDB=has_gmdb,
            has_GLWB=has_glwb,
        )
        assert va.m_has_GMDB == has_gmdb
        assert va.m_has_GLWB == has_glwb

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
            Annuity_VA(
                client_age=0,
                annuity_payout_rate=payout_rate,
                age_income_start=65,
                age_max_ratchet=70,
                rate_rollup_benefit=0.05,
            )


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Annuity_VA_Annual_Charges
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Annuity_VA_Annual_Charges:
    """Tests for calc_total_annual_charges() invariants."""

    @pytest.mark.unit()
    @given(
        me_charge=st.floats(min_value=0.0, max_value=0.05, allow_nan=False, allow_infinity=False),
        admin_fee=st.floats(min_value=0.0, max_value=0.05, allow_nan=False, allow_infinity=False),
        rider_charge=st.floats(min_value=0.0, max_value=0.05, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_total_charges_sum_equals_components(
        self,
        me_charge: float,
        admin_fee: float,
        rider_charge: float,
    ) -> None:
        """calc_total_annual_charges() = ME + admin + rider."""
        va = _make_va(
            rate_ME_charge=me_charge,
            rate_admin_fee=admin_fee,
            rate_rider_charge=rider_charge,
        )
        total = va.calc_total_annual_charges()
        assert math.isclose(total, me_charge + admin_fee + rider_charge, rel_tol=1e-12)

    @pytest.mark.unit()
    @given(
        me_charge=st.floats(min_value=0.0, max_value=0.05, allow_nan=False, allow_infinity=False),
        admin_fee=st.floats(min_value=0.0, max_value=0.05, allow_nan=False, allow_infinity=False),
        rider_charge=st.floats(min_value=0.0, max_value=0.05, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_total_charges_nonneg(
        self,
        me_charge: float,
        admin_fee: float,
        rider_charge: float,
    ) -> None:
        """calc_total_annual_charges() >= 0 for non-negative inputs."""
        va = _make_va(
            rate_ME_charge=me_charge,
            rate_admin_fee=admin_fee,
            rate_rider_charge=rider_charge,
        )
        assert va.calc_total_annual_charges() >= 0


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Annuity_VA_Calc_Payout
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Annuity_VA_Calc_Payout:
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
        va = _make_va(client_age=45, payout_rate=payout_rate, age_income_start=65)
        payout = va.calc_annuity_payout(amount_principal=principal)
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
        va = _make_va(client_age=64, payout_rate=payout_rate, age_income_start=65)
        va.m_client_age = 65
        payout = va.calc_annuity_payout(amount_principal=principal)
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
        va = _make_va(client_age=64, payout_rate=payout_rate, age_income_start=65)
        va.m_client_age = 65
        payout_a = va.calc_annuity_payout(amount_principal=principal_a)
        payout_b = va.calc_annuity_payout(amount_principal=principal_b)
        assume(payout_b > 0.0)
        assert math.isclose(payout_a / payout_b, principal_a / principal_b, rel_tol=1e-9)


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Annuity_VA_Calc_Monthly_Payout
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Annuity_VA_Calc_Monthly_Payout:
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
        va = _make_va(client_age=64, payout_rate=payout_rate, age_income_start=65)
        va.m_client_age = 65
        annual = va.calc_annuity_payout(amount_principal=principal)
        monthly = va.calc_monthly_payout(amount_principal=principal)
        assert math.isclose(monthly, annual / 12, rel_tol=1e-12)

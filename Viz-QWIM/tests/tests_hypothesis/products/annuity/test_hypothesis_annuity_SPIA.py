"""Hypothesis (property-based) tests for Annuity_SPIA and related types.

Tests cover:
- ``Withdrawal_Rates`` struct construction and field access
- ``Annuity_Payout_Option`` and ``Annuity_Type`` enum invariants
- ``Annuity_SPIA`` construction — valid and invalid parameter ranges
- ``calc_annuity_payout`` — proportionality to principal and payout rate
- COLA property stored correctly
"""

from __future__ import annotations

import math

import pytest

from hypothesis import assume, given, settings
from hypothesis import strategies as st

from src.products.annuity.annuity_base import (
    Annuity_Payout_Option,
    Annuity_Type,
    Withdrawal_Rates,
)
from src.products.annuity.annuity_SPIA import Annuity_SPIA


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Withdrawal_Rates
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Withdrawal_Rates:
    """Tests for the Withdrawal_Rates struct."""

    @pytest.mark.unit()
    @given(
        nominal_wr=st.floats(min_value=0.0, max_value=0.20, allow_nan=False, allow_infinity=False),
        real_wr=st.floats(min_value=-0.05, max_value=0.20, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_fields_stored_correctly(
        self,
        nominal_wr: float,
        real_wr: float,
    ) -> None:
        """Withdrawal_Rates stores nominal_WR and real_WR exactly."""
        wr = Withdrawal_Rates(nominal_WR=nominal_wr, real_WR=real_wr)
        assert wr.nominal_WR == nominal_wr
        assert wr.real_WR == real_wr

    @pytest.mark.unit()
    @given(
        nominal_wr=st.floats(min_value=0.03, max_value=0.10, allow_nan=False, allow_infinity=False),
        inflation_rate=st.floats(min_value=0.0, max_value=0.10, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_real_wr_below_nominal_when_inflation_positive(
        self,
        nominal_wr: float,
        inflation_rate: float,
    ) -> None:
        """real_WR = nominal_WR - inflation_rate ≤ nominal_WR when inflation ≥ 0."""
        real_wr = nominal_wr - inflation_rate
        wr = Withdrawal_Rates(nominal_WR=nominal_wr, real_WR=real_wr)
        assert wr.real_WR <= wr.nominal_WR


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Annuity_Type_And_Payout_Option_Enums
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Annuity_Type_And_Payout_Option_Enums:
    """Tests for Annuity_Type and Annuity_Payout_Option enums."""

    @pytest.mark.unit()
    @given(
        idx_type=st.sampled_from(list(Annuity_Type)),
    )
    @settings(max_examples=200)
    def Test_annuity_type_has_non_empty_value(
        self,
        idx_type: Annuity_Type,
    ) -> None:
        """Every Annuity_Type member has a non-empty string value."""
        assert isinstance(idx_type.value, str)
        assert len(idx_type.value) > 0

    @pytest.mark.unit()
    @given(
        idx_option=st.sampled_from(list(Annuity_Payout_Option)),
    )
    @settings(max_examples=200)
    def Test_payout_option_has_non_empty_value(
        self,
        idx_option: Annuity_Payout_Option,
    ) -> None:
        """Every Annuity_Payout_Option member has a non-empty string value."""
        assert isinstance(idx_option.value, str)
        assert len(idx_option.value) > 0

    @pytest.mark.unit()
    def Test_spia_type_exists_in_annuity_type(self) -> None:
        """Annuity_Type.ANNUITY_SPIA is present."""
        assert Annuity_Type.ANNUITY_SPIA in list(Annuity_Type)

    @pytest.mark.unit()
    def Test_life_only_option_exists(self) -> None:
        """Annuity_Payout_Option.LIFE_ONLY is present."""
        assert Annuity_Payout_Option.LIFE_ONLY in list(Annuity_Payout_Option)


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Annuity_SPIA_Construction
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Annuity_SPIA_Construction:
    """Tests for valid construction of Annuity_SPIA."""

    @pytest.mark.unit()
    @given(
        client_age=st.integers(min_value=1, max_value=100),
        payout_rate=st.floats(min_value=0.001, max_value=0.20, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_life_only_construction_stores_attributes(
        self,
        client_age: int,
        payout_rate: float,
    ) -> None:
        """LIFE_ONLY SPIA stores client_age and payout_rate correctly."""
        spia = Annuity_SPIA(
            client_age=client_age,
            annuity_payout_rate=payout_rate,
            payout_option=Annuity_Payout_Option.LIFE_ONLY,
        )
        assert spia.m_client_age == client_age
        assert spia.m_annuity_payout_rate == payout_rate

    @pytest.mark.unit()
    @given(
        client_age=st.integers(min_value=1, max_value=100),
        payout_rate=st.floats(min_value=0.001, max_value=0.20, allow_nan=False, allow_infinity=False),
        guarantee_years=st.integers(min_value=1, max_value=30),
    )
    @settings(max_examples=200)
    def Test_period_certain_stores_guarantee_years(
        self,
        client_age: int,
        payout_rate: float,
        guarantee_years: int,
    ) -> None:
        """PERIOD_CERTAIN SPIA stores guarantee_period_years correctly."""
        spia = Annuity_SPIA(
            client_age=client_age,
            annuity_payout_rate=payout_rate,
            payout_option=Annuity_Payout_Option.PERIOD_CERTAIN,
            guarantee_period_years=guarantee_years,
        )
        assert spia.m_guarantee_period_years == guarantee_years

    @pytest.mark.unit()
    @given(
        client_age=st.integers(min_value=1, max_value=100),
        payout_rate=st.floats(min_value=0.001, max_value=0.20, allow_nan=False, allow_infinity=False),
        rate_cola=st.floats(min_value=0.0, max_value=0.10, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_cola_stored_correctly(
        self,
        client_age: int,
        payout_rate: float,
        rate_cola: float,
    ) -> None:
        """rate_COLA is stored exactly in m_rate_COLA."""
        spia = Annuity_SPIA(
            client_age=client_age,
            annuity_payout_rate=payout_rate,
            rate_COLA=rate_cola,
        )
        assert spia.m_rate_COLA == rate_cola

    @pytest.mark.unit()
    @given(
        client_age=st.integers(min_value=1, max_value=100),
        payout_rate=st.floats(min_value=0.001, max_value=0.20, allow_nan=False, allow_infinity=False),
        survivor_pct=st.floats(min_value=0.01, max_value=1.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_joint_survivor_pct_stored_correctly(
        self,
        client_age: int,
        payout_rate: float,
        survivor_pct: float,
    ) -> None:
        """joint_survivor_pct is stored in m_joint_survivor_pct."""
        spia = Annuity_SPIA(
            client_age=client_age,
            annuity_payout_rate=payout_rate,
            joint_survivor_pct=survivor_pct,
        )
        assert spia.m_joint_survivor_pct == survivor_pct

    @pytest.mark.unit()
    @given(
        client_age=st.integers(min_value=1, max_value=100),
        payout_rate=st.floats(min_value=0.001, max_value=0.20, allow_nan=False, allow_infinity=False),
        payment_frequency=st.integers(min_value=1, max_value=12),
    )
    @settings(max_examples=200)
    def Test_payment_frequency_stored_correctly(
        self,
        client_age: int,
        payout_rate: float,
        payment_frequency: int,
    ) -> None:
        """payment_frequency is stored in m_payment_frequency."""
        spia = Annuity_SPIA(
            client_age=client_age,
            annuity_payout_rate=payout_rate,
            payment_frequency=payment_frequency,
        )
        assert spia.m_payment_frequency == payment_frequency

    @pytest.mark.unit()
    @given(
        client_age=st.integers(min_value=1, max_value=100),
        payout_rate=st.floats(min_value=0.001, max_value=0.20, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_annuity_type_is_spia(
        self,
        client_age: int,
        payout_rate: float,
    ) -> None:
        """m_annuity_type is always ANNUITY_SPIA for SPIA objects."""
        spia = Annuity_SPIA(
            client_age=client_age,
            annuity_payout_rate=payout_rate,
        )
        assert spia.m_annuity_type == Annuity_Type.ANNUITY_SPIA

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
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Validation_Input
        with pytest.raises(Exception_Validation_Input):
            Annuity_SPIA(client_age=0, annuity_payout_rate=payout_rate)

    @pytest.mark.unit()
    @given(
        client_age=st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=200)
    def Test_invalid_payout_rate_raises(
        self,
        client_age: int,
    ) -> None:
        """Non-positive payout_rate raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Validation_Input
        with pytest.raises(Exception_Validation_Input):
            Annuity_SPIA(client_age=client_age, annuity_payout_rate=0.0)


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Annuity_SPIA_Calc_Payout
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Annuity_SPIA_Calc_Payout:
    """Tests for calc_annuity_payout() numerical invariants."""

    @pytest.mark.unit()
    @given(
        client_age=st.integers(min_value=55, max_value=80),
        payout_rate=st.floats(min_value=0.03, max_value=0.10, allow_nan=False, allow_infinity=False),
        principal=st.floats(min_value=1.0, max_value=1_000_000.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_payout_equals_principal_times_rate(
        self,
        client_age: int,
        payout_rate: float,
        principal: float,
    ) -> None:
        """Base payout = principal × payout_rate (no COLA, no inflation)."""
        spia = Annuity_SPIA(
            client_age=client_age,
            annuity_payout_rate=payout_rate,
        )
        payout = spia.calc_annuity_payout(amount_principal=principal)
        expected = principal * payout_rate
        assert math.isclose(payout, expected, rel_tol=1e-9)

    @pytest.mark.unit()
    @given(
        client_age=st.integers(min_value=55, max_value=80),
        payout_rate=st.floats(min_value=0.03, max_value=0.10, allow_nan=False, allow_infinity=False),
        principal_a=st.floats(min_value=1.0, max_value=500_000.0, allow_nan=False, allow_infinity=False),
        principal_b=st.floats(min_value=1.0, max_value=500_000.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_payout_proportional_to_principal(
        self,
        client_age: int,
        payout_rate: float,
        principal_a: float,
        principal_b: float,
    ) -> None:
        """Payout scales linearly with principal: P(a)/P(b) = a/b."""
        assume(principal_b > 0.01)
        spia = Annuity_SPIA(
            client_age=client_age,
            annuity_payout_rate=payout_rate,
        )
        payout_a = spia.calc_annuity_payout(amount_principal=principal_a)
        payout_b = spia.calc_annuity_payout(amount_principal=principal_b)
        assert math.isclose(payout_a / payout_b, principal_a / principal_b, rel_tol=1e-9)

    @pytest.mark.unit()
    @given(
        client_age=st.integers(min_value=55, max_value=80),
        payout_rate=st.floats(min_value=0.03, max_value=0.10, allow_nan=False, allow_infinity=False),
        principal=st.floats(min_value=1.0, max_value=1_000_000.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_payout_is_positive(
        self,
        client_age: int,
        payout_rate: float,
        principal: float,
    ) -> None:
        """calc_annuity_payout() always returns a positive value."""
        spia = Annuity_SPIA(
            client_age=client_age,
            annuity_payout_rate=payout_rate,
        )
        payout = spia.calc_annuity_payout(amount_principal=principal)
        assert payout > 0

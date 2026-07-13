"""Hypothesis (property-based) tests for Annuity_RILA.

Tests cover:
- ``Annuity_RILA`` construction — valid parameter storage; invalid raises
- ``calc_downside_return`` — always <= 0 for negative index_return
- ``calc_credited_rate`` — cap invariant; floor protection; buffer protection
- ``calc_annualised_credited_rate`` — compound-rate identity
- ``calc_account_values_multi_term`` — length; first value equals principal
- ``calc_annuity_payout`` / ``calc_monthly_payout`` — deferral and active-age invariants
- ``calc_withdrawal_rates`` — active-age withdrawal-rate invariants without inflation
- ``calc_worst_case_account_value`` / ``calc_best_case_account_value``

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

from hypothesis import (
    given,
    settings,
    strategies as st,
)

from src.products.annuity.annuity_base import Annuity_Type
from src.products.annuity.annuity_RILA import (
    Annuity_RILA,
    Crediting_Strategy,
    Protection_Type,
)
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)


# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------


def _make_buffer_rila(
    client_age: int = 45,
    payout_rate: float = 0.05,
    age_income_start: int = 66,
    buffer_rate: float = 0.10,
    cap_rate: float = 0.15,
    term_years: int = 6,
    **kwargs: object,
) -> Annuity_RILA:
    return Annuity_RILA(
        client_age=client_age,
        annuity_payout_rate=payout_rate,
        age_income_start=age_income_start,
        protection_type=Protection_Type.BUFFER,
        buffer_rate=buffer_rate,
        cap_rate=cap_rate,
        crediting_strategy=Crediting_Strategy.CAP,
        term_years=term_years,
        **kwargs,  # type: ignore[arg-type]
    )


def _make_floor_rila(
    client_age: int = 45,
    payout_rate: float = 0.05,
    age_income_start: int = 66,
    floor_rate: float = -0.10,
    cap_rate: float = 0.15,
    term_years: int = 6,
    **kwargs: object,
) -> Annuity_RILA:
    return Annuity_RILA(
        client_age=client_age,
        annuity_payout_rate=payout_rate,
        age_income_start=age_income_start,
        protection_type=Protection_Type.FLOOR,
        floor_rate=floor_rate,
        cap_rate=cap_rate,
        crediting_strategy=Crediting_Strategy.CAP,
        term_years=term_years,
        **kwargs,  # type: ignore[arg-type]
    )


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Annuity_RILA_Construction
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Annuity_RILA_Construction:
    """Tests for valid construction of Annuity_RILA."""

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
        rila = Annuity_RILA(
            client_age=client_age,
            annuity_payout_rate=payout_rate,
            age_income_start=client_age + 1,
        )
        assert rila.m_client_age == client_age
        assert rila.m_annuity_payout_rate == payout_rate

    @pytest.mark.unit()
    @given(
        client_age=st.integers(min_value=1, max_value=79),
        payout_rate=st.floats(min_value=0.001, max_value=0.20, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_annuity_type_is_rila(
        self,
        client_age: int,
        payout_rate: float,
    ) -> None:
        """m_annuity_type is always ANNUITY_RILA."""
        rila = Annuity_RILA(
            client_age=client_age,
            annuity_payout_rate=payout_rate,
            age_income_start=client_age + 1,
        )
        assert rila.m_annuity_type == Annuity_Type.ANNUITY_RILA

    @pytest.mark.unit()
    @given(
        client_age=st.integers(min_value=1, max_value=79),
        payout_rate=st.floats(min_value=0.001, max_value=0.20, allow_nan=False, allow_infinity=False),
        buffer_rate=st.floats(min_value=0.0, max_value=0.30, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_buffer_rate_stored_correctly(
        self,
        client_age: int,
        payout_rate: float,
        buffer_rate: float,
    ) -> None:
        """m_buffer_rate stored correctly for BUFFER protection type."""
        rila = Annuity_RILA(
            client_age=client_age,
            annuity_payout_rate=payout_rate,
            age_income_start=client_age + 1,
            protection_type=Protection_Type.BUFFER,
            buffer_rate=buffer_rate,
        )
        assert rila.m_buffer_rate == buffer_rate

    @pytest.mark.unit()
    @given(
        client_age=st.integers(min_value=1, max_value=79),
        payout_rate=st.floats(min_value=0.001, max_value=0.20, allow_nan=False, allow_infinity=False),
        cap_rate=st.floats(min_value=0.01, max_value=0.50, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_cap_rate_stored_correctly(
        self,
        client_age: int,
        payout_rate: float,
        cap_rate: float,
    ) -> None:
        """m_cap_rate stored correctly."""
        rila = Annuity_RILA(
            client_age=client_age,
            annuity_payout_rate=payout_rate,
            age_income_start=client_age + 1,
            cap_rate=cap_rate,
        )
        assert rila.m_cap_rate == cap_rate

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
            Annuity_RILA(
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
            Annuity_RILA(
                client_age=client_age,
                annuity_payout_rate=0.0,
                age_income_start=client_age + 1,
            )


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Annuity_RILA_Downside_Return
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Annuity_RILA_Downside_Return:
    """Tests for calc_downside_return() invariants."""

    @pytest.mark.unit()
    @given(
        index_return=st.floats(min_value=-0.99, max_value=-0.001, allow_nan=False, allow_infinity=False),
        buffer_rate=st.floats(min_value=0.0, max_value=0.40, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_downside_return_nonpos_for_negative_index(
        self,
        index_return: float,
        buffer_rate: float,
    ) -> None:
        """calc_downside_return <= 0 for any negative index return."""
        rila = _make_buffer_rila(buffer_rate=buffer_rate)
        downside = rila.calc_downside_return(index_return=index_return)
        assert downside <= 1e-12

    @pytest.mark.unit()
    @given(
        index_return=st.floats(min_value=-0.99, max_value=-0.001, allow_nan=False, allow_infinity=False),
        buffer_rate=st.floats(min_value=0.001, max_value=0.40, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_buffer_absorbs_small_losses(
        self,
        index_return: float,
        buffer_rate: float,
    ) -> None:
        """Losses within buffer return 0.0; losses beyond buffer return index_return + buffer."""
        rila = _make_buffer_rila(buffer_rate=buffer_rate)
        downside = rila.calc_downside_return(index_return=index_return)
        if index_return >= -buffer_rate:
            assert math.isclose(downside, 0.0, abs_tol=1e-12)
        else:
            assert math.isclose(downside, index_return + buffer_rate, rel_tol=1e-9)

    @pytest.mark.unit()
    @given(
        index_return=st.floats(min_value=-0.99, max_value=-0.001, allow_nan=False, allow_infinity=False),
        floor_rate=st.floats(min_value=-0.40, max_value=-0.001, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_floor_protection_caps_loss(
        self,
        index_return: float,
        floor_rate: float,
    ) -> None:
        """Floor protection: downside = max(index_return, floor_rate)."""
        rila = _make_floor_rila(floor_rate=floor_rate)
        downside = rila.calc_downside_return(index_return=index_return)
        assert downside >= floor_rate - 1e-12


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Annuity_RILA_Credited_Rate
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Annuity_RILA_Credited_Rate:
    """Tests for calc_credited_rate() invariants."""

    @pytest.mark.unit()
    @given(
        index_return=st.floats(min_value=0.0, max_value=0.50, allow_nan=False, allow_infinity=False),
        cap_rate=st.floats(min_value=0.01, max_value=0.50, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_credited_rate_leq_cap_for_positive_returns(
        self,
        index_return: float,
        cap_rate: float,
    ) -> None:
        """calc_credited_rate() <= cap_rate for positive index returns."""
        rila = _make_buffer_rila(cap_rate=cap_rate)
        rate = rila.calc_credited_rate(index_return=index_return)
        assert rate <= cap_rate + 1e-12

    @pytest.mark.unit()
    @given(
        index_return=st.floats(min_value=-0.99, max_value=-0.001, allow_nan=False, allow_infinity=False),
        floor_rate=st.floats(min_value=-0.40, max_value=-0.001, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_floor_rila_credited_rate_geq_floor(
        self,
        index_return: float,
        floor_rate: float,
    ) -> None:
        """Floor RILA: calc_credited_rate() >= floor_rate for negative index returns."""
        rila = _make_floor_rila(floor_rate=floor_rate)
        rate = rila.calc_credited_rate(index_return=index_return)
        assert rate >= floor_rate - 1e-12

    @pytest.mark.unit()
    @given(
        index_return=st.floats(min_value=0.0, max_value=0.50, allow_nan=False, allow_infinity=False),
        trigger_rate=st.floats(min_value=0.001, max_value=0.20, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_performance_trigger_credits_fixed_rate(
        self,
        index_return: float,
        trigger_rate: float,
    ) -> None:
        """Performance trigger credits exactly trigger_rate when index_return >= 0."""
        rila = Annuity_RILA(
            client_age=45,
            annuity_payout_rate=0.05,
            age_income_start=66,
            crediting_strategy=Crediting_Strategy.PERFORMANCE_TRIGGER,
            performance_trigger_rate=trigger_rate,
        )
        rate = rila.calc_credited_rate(index_return=index_return)
        assert math.isclose(rate, trigger_rate, rel_tol=1e-12)


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Annuity_RILA_Annualised_Rate
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Annuity_RILA_Annualised_Rate:
    """Tests for calc_annualised_credited_rate() invariants."""

    @pytest.mark.unit()
    @given(
        index_return=st.floats(min_value=0.0, max_value=0.50, allow_nan=False, allow_infinity=False),
        term_years=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=200)
    def Test_annualised_rate_identity_for_one_year(
        self,
        index_return: float,
        term_years: int,
    ) -> None:
        """annualised_rate satisfies (1+r)^T - 1 == term_credited_rate."""
        rila = _make_buffer_rila(term_years=term_years)
        credited = rila.calc_credited_rate(index_return=index_return)
        annualised = rila.calc_annualised_credited_rate(index_return=index_return)
        # Reconstruct: (1 + annualised)^term_years ≈ 1 + credited
        reconstructed = (1.0 + annualised) ** term_years - 1.0
        assert math.isclose(reconstructed, credited, rel_tol=1e-6, abs_tol=1e-12)

    @pytest.mark.unit()
    @given(
        index_return=st.floats(min_value=0.0, max_value=0.50, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_annualised_rate_equals_credited_for_one_year_term(
        self,
        index_return: float,
    ) -> None:
        """For term_years=1, annualised rate = credited rate."""
        rila = _make_buffer_rila(term_years=1)
        credited = rila.calc_credited_rate(index_return=index_return)
        annualised = rila.calc_annualised_credited_rate(index_return=index_return)
        assert math.isclose(annualised, credited, rel_tol=1e-12, abs_tol=1e-15)


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Annuity_RILA_Multi_Term
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Annuity_RILA_Multi_Term:
    """Tests for calc_account_values_multi_term() invariants."""

    @pytest.mark.unit()
    @given(
        principal=st.floats(min_value=1.0, max_value=1_000_000.0, allow_nan=False, allow_infinity=False),
        returns=st.lists(
            st.floats(min_value=-0.40, max_value=0.40, allow_nan=False, allow_infinity=False),
            min_size=1,
            max_size=10,
        ),
    )
    @settings(max_examples=200)
    def Test_multi_term_length_is_returns_plus_one(
        self,
        principal: float,
        returns: list[float],
    ) -> None:
        """Result has len(term_returns) + 1 elements."""
        rila = _make_buffer_rila()
        values = rila.calc_account_values_multi_term(
            amount_principal=principal,
            term_index_returns=returns,
        )
        assert len(values) == len(returns) + 1

    @pytest.mark.unit()
    @given(
        principal=st.floats(min_value=1.0, max_value=1_000_000.0, allow_nan=False, allow_infinity=False),
        returns=st.lists(
            st.floats(min_value=-0.40, max_value=0.40, allow_nan=False, allow_infinity=False),
            min_size=1,
            max_size=10,
        ),
    )
    @settings(max_examples=200)
    def Test_multi_term_first_value_equals_principal(
        self,
        principal: float,
        returns: list[float],
    ) -> None:
        """First element of result equals amount_principal."""
        rila = _make_buffer_rila()
        values = rila.calc_account_values_multi_term(
            amount_principal=principal,
            term_index_returns=returns,
        )
        assert math.isclose(values[0], principal, rel_tol=1e-12)


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Annuity_RILA_Worst_Best_Case
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Annuity_RILA_Payout_Withdrawal:
    """Tests for payout, monthly payout, and withdrawal-rate invariants."""

    @pytest.mark.unit()
    @given(
        principal=st.floats(min_value=1.0, max_value=1_000_000.0, allow_nan=False, allow_infinity=False),
        payout_rate=st.floats(min_value=0.001, max_value=0.20, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_payout_and_monthly_payout_are_zero_during_deferral(
        self,
        principal: float,
        payout_rate: float,
    ) -> None:
        """During deferral, both annual and monthly payout remain 0.0."""
        rila = _make_buffer_rila(client_age=45, age_income_start=66, payout_rate=payout_rate)
        annual = rila.calc_annuity_payout(amount_principal = principal)
        monthly = rila.calc_monthly_payout(amount_principal = principal)
        assert math.isclose(annual, 0.0, abs_tol=1e-12)
        assert math.isclose(monthly, 0.0, abs_tol=1e-12)

    @pytest.mark.unit()
    @given(
        principal=st.floats(min_value=1.0, max_value=1_000_000.0, allow_nan=False, allow_infinity=False),
        payout_rate=st.floats(min_value=0.001, max_value=0.20, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_active_monthly_payout_matches_annual_payout(
        self,
        principal: float,
        payout_rate: float,
    ) -> None:
        """Past income start, annual payout scales with principal and monthly is annual/12."""
        rila = _make_buffer_rila(client_age=64, age_income_start=65, payout_rate=payout_rate)
        rila.m_client_age = 66
        annual = rila.calc_annuity_payout(amount_principal = principal)
        monthly = rila.calc_monthly_payout(amount_principal = principal)
        assert math.isclose(annual, principal * payout_rate, rel_tol=1e-9)
        assert math.isclose(monthly, annual / 12.0, rel_tol=1e-9)

    @pytest.mark.unit()
    @given(
        principal=st.floats(min_value=1.0, max_value=1_000_000.0, allow_nan=False, allow_infinity=False),
        payout_rate=st.floats(min_value=0.001, max_value=0.20, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_active_withdrawal_rates_match_contract_payout_rate_without_inflation(
        self,
        principal: float,
        payout_rate: float,
    ) -> None:
        """Without inflation, active-age nominal and real WR match the contract payout rate."""
        rila = _make_buffer_rila(client_age=64, age_income_start=65, payout_rate=payout_rate)
        rila.m_client_age = 66
        withdrawal_rates = rila.calc_withdrawal_rates(amount_principal = principal)
        assert math.isclose(withdrawal_rates.nominal_WR, payout_rate, rel_tol=1e-9)
        assert math.isclose(withdrawal_rates.real_WR, withdrawal_rates.nominal_WR, rel_tol=1e-9)


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Annuity_RILA_Worst_Best_Case
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Annuity_RILA_Worst_Best_Case:
    """Tests for calc_worst_case_account_value / calc_best_case_account_value."""

    @pytest.mark.unit()
    @given(
        principal=st.floats(min_value=1.0, max_value=1_000_000.0, allow_nan=False, allow_infinity=False),
        num_terms=st.integers(min_value=1, max_value=5),
    )
    @settings(max_examples=200)
    def Test_worst_case_leq_principal(
        self,
        principal: float,
        num_terms: int,
    ) -> None:
        """calc_worst_case_account_value <= principal (losses or breakeven)."""
        rila = _make_buffer_rila()
        worst = rila.calc_worst_case_account_value(
            amount_principal=principal,
            num_terms=num_terms,
        )
        assert worst <= principal + 1e-6

    @pytest.mark.unit()
    @given(
        principal=st.floats(min_value=1.0, max_value=1_000_000.0, allow_nan=False, allow_infinity=False),
        num_terms=st.integers(min_value=1, max_value=5),
        cap_rate=st.floats(min_value=0.01, max_value=0.50, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_best_case_geq_principal(
        self,
        principal: float,
        num_terms: int,
        cap_rate: float,
    ) -> None:
        """calc_best_case_account_value >= principal when cap_rate > 0."""
        rila = _make_buffer_rila(cap_rate=cap_rate)
        best = rila.calc_best_case_account_value(
            amount_principal=principal,
            num_terms=num_terms,
        )
        assert best >= principal - 1e-6

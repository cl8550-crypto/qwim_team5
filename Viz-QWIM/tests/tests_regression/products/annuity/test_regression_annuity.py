"""Regression tests for annuity product calculation outputs.

These tests verify that key numerical outputs (annual payout, monthly payout,
withdrawal rates) do not change unexpectedly across refactors.

Test Strategy
-------------
1. A single deterministic instance of each annuity type is constructed with
   fixed parameters.
2. Key methods are called with fixed ``amount_principal = 100_000.0``.
3. Results are stored as Parquet baselines in
    ``tests/_baselines/products/annuity/``.
4. On subsequent runs the computed value is compared against the baseline.

Baseline Regeneration
---------------------
Set the environment variable ``REGENERATE_BASELINES=1`` before running pytest
to overwrite baselines with fresh values::

    REGENERATE_BASELINES=1 python -m pytest tests/tests_regression/products/annuity/ -q

Commit both code changes and updated baselines together.
"""

from __future__ import annotations

import os

import polars as pl
import pytest

from src.products.annuity.annuity_DIA import Annuity_DIA
from src.products.annuity.annuity_FIA import Annuity_FIA
from src.products.annuity.annuity_RILA import (
    Annuity_RILA,
    Crediting_Strategy,
    Protection_Type,
)
from src.products.annuity.annuity_SPIA import Annuity_SPIA
from src.products.annuity.annuity_VA import Annuity_VA

from tests.tests_regression.products.annuity.conftest import load_baseline, save_baseline


_REGENERATE = os.environ.get("REGENERATE_BASELINES", "0") == "1"
_PRINCIPAL = 100_000.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _compare_or_regenerate(filename: str, current: pl.DataFrame) -> None:
    """Either save baseline (regenerate mode) or compare against it."""
    if _REGENERATE:
        save_baseline(filename, current)
        return
    baseline = load_baseline(filename)
    assert current.shape == baseline.shape, (
        f"Shape mismatch for {filename}: {current.shape} vs {baseline.shape}"
    )
    for col in baseline.columns:
        assert current[col].to_list() == pytest.approx(
            baseline[col].to_list(), rel=1e-6,
        ), f"Column '{col}' mismatch in {filename}"


def _make_income_active_rila() -> Annuity_RILA:
    """Construct a deterministic RILA and advance it past income start."""
    rila = Annuity_RILA(
        client_age=64,
        annuity_payout_rate=0.05,
        age_income_start=65,
        protection_type=Protection_Type.BUFFER,
        buffer_rate=0.10,
        cap_rate=0.15,
    )
    rila.m_client_age = 66
    return rila



# ---------------------------------------------------------------------------
# SPIA regression
# ---------------------------------------------------------------------------


class Class_Test_Regression_Annuity_SPIA:
    """Regression tests for Annuity_SPIA calculations."""

    @pytest.mark.regression()
    def Test_annual_payout_unchanged(self) -> None:
        """calc_annuity_payout at fixed parameters matches baseline."""
        spia = Annuity_SPIA(client_age=65, annuity_payout_rate=0.05)
        payout = spia.calc_annuity_payout(amount_principal=_PRINCIPAL)
        df = pl.DataFrame({"annual_payout": [payout]})
        _compare_or_regenerate("spia_annual_payout.parquet", df)

    @pytest.mark.regression()
    def Test_monthly_payout_unchanged(self) -> None:
        """calc_monthly_payout at fixed parameters matches baseline."""
        spia = Annuity_SPIA(client_age=65, annuity_payout_rate=0.05)
        monthly = spia.calc_monthly_payout(amount_principal=_PRINCIPAL)
        df = pl.DataFrame({"monthly_payout": [monthly]})
        _compare_or_regenerate("spia_monthly_payout.parquet", df)

    @pytest.mark.regression()
    def Test_withdrawal_rates_unchanged(self) -> None:
        """calc_withdrawal_rates at fixed parameters matches baseline."""
        spia = Annuity_SPIA(client_age=65, annuity_payout_rate=0.05)
        wr = spia.calc_withdrawal_rates(amount_principal=_PRINCIPAL)
        df = pl.DataFrame({
            "nominal_WR": [wr.nominal_WR],
            "real_WR": [wr.real_WR],
        })
        _compare_or_regenerate("spia_withdrawal_rates.parquet", df)


# ---------------------------------------------------------------------------
# DIA regression
# ---------------------------------------------------------------------------


class Class_Test_Regression_Annuity_DIA:
    """Regression tests for Annuity_DIA calculations."""

    @pytest.mark.regression()
    def Test_annual_payout_during_deferral_unchanged(self) -> None:
        """calc_annuity_payout returns 0.0 during deferral (regression)."""
        dia = Annuity_DIA(
            client_age=45,
            annuity_payout_rate=0.05,
            age_income_start=65,
        )
        payout = dia.calc_annuity_payout(amount_principal=_PRINCIPAL)
        df = pl.DataFrame({"annual_payout": [payout]})
        _compare_or_regenerate("dia_annual_payout_deferral.parquet", df)

    @pytest.mark.regression()
    def Test_payout_in_year_one_unchanged(self) -> None:
        """calc_payout_in_year(year_number=1) matches baseline."""
        dia = Annuity_DIA(
            client_age=45,
            annuity_payout_rate=0.05,
            age_income_start=65,
        )
        payout = dia.calc_payout_in_year(amount_principal=_PRINCIPAL, year_number=1)
        df = pl.DataFrame({"payout_year_1": [payout]})
        _compare_or_regenerate("dia_payout_year_1.parquet", df)

    @pytest.mark.regression()
    def Test_future_value_unchanged(self) -> None:
        """calc_future_value at 4% growth matches baseline."""
        dia = Annuity_DIA(
            client_age=45,
            annuity_payout_rate=0.05,
            age_income_start=65,
        )
        fv = dia.calc_future_value(amount_principal=_PRINCIPAL, growth_rate=0.04)
        df = pl.DataFrame({"future_value": [fv]})
        _compare_or_regenerate("dia_future_value.parquet", df)


# ---------------------------------------------------------------------------
# FIA regression
# ---------------------------------------------------------------------------


class Class_Test_Regression_Annuity_FIA:
    """Regression tests for Annuity_FIA calculations."""

    @pytest.mark.regression()
    def Test_credited_rate_unchanged(self) -> None:
        """calc_credited_rate at index_return=0.08 matches baseline."""
        fia = Annuity_FIA(
            client_age=50,
            annuity_payout_rate=0.05,
            age_income_start=65,
            age_max_ratchet=80,
            rate_rollup_benefit=0.05,
            cap_rate=0.07,
            participation_rate=1.0,
            floor_rate=0.0,
        )
        rate = fia.calc_credited_rate(index_return=0.08)
        df = pl.DataFrame({"credited_rate": [rate]})
        _compare_or_regenerate("fia_credited_rate.parquet", df)

    @pytest.mark.regression()
    def Test_annual_payout_during_deferral_unchanged(self) -> None:
        """calc_annuity_payout returns 0.0 during deferral (regression)."""
        fia = Annuity_FIA(
            client_age=50,
            annuity_payout_rate=0.05,
            age_income_start=65,
            age_max_ratchet=80,
            rate_rollup_benefit=0.05,
        )
        payout = fia.calc_annuity_payout(amount_principal=_PRINCIPAL)
        df = pl.DataFrame({"annual_payout": [payout]})
        _compare_or_regenerate("fia_annual_payout_deferral.parquet", df)

    @pytest.mark.regression()
    def Test_annual_payout_at_income_start_unchanged(self) -> None:
        """calc_annuity_payout with m_client_age overridden to income start matches baseline."""
        fia = Annuity_FIA(
            client_age=64,
            annuity_payout_rate=0.05,
            age_income_start=65,
            age_max_ratchet=80,
            rate_rollup_benefit=0.05,
        )
        fia.m_client_age = 65
        payout = fia.calc_annuity_payout(amount_principal=_PRINCIPAL)
        df = pl.DataFrame({"annual_payout": [payout]})
        _compare_or_regenerate("fia_annual_payout_income_start.parquet", df)

    @pytest.mark.regression()
    def Test_benefit_base_with_rollup_unchanged(self) -> None:
        """calc_benefit_base_with_rollup at fixed parameters matches baseline."""
        fia = Annuity_FIA(
            client_age=50,
            annuity_payout_rate=0.05,
            age_income_start=65,
            age_max_ratchet=80,
            rate_rollup_benefit=0.05,
        )
        base = fia.calc_benefit_base_with_rollup(amount_principal=_PRINCIPAL)
        df = pl.DataFrame({"benefit_base": [base]})
        _compare_or_regenerate("fia_benefit_base_rollup.parquet", df)


# ---------------------------------------------------------------------------
# VA regression
# ---------------------------------------------------------------------------


class Class_Test_Regression_Annuity_VA:
    """Regression tests for Annuity_VA calculations."""

    @pytest.mark.regression()
    def Test_total_annual_charges_unchanged(self) -> None:
        """calc_total_annual_charges() at fixed parameters matches baseline."""
        va = Annuity_VA(
            client_age=50,
            annuity_payout_rate=0.05,
            age_income_start=65,
            age_max_ratchet=80,
            rate_rollup_benefit=0.05,
            rate_ME_charge=0.0125,
            rate_admin_fee=0.0015,
            rate_rider_charge=0.0100,
        )
        total_charges = va.calc_total_annual_charges()
        df = pl.DataFrame({"total_annual_charges": [total_charges]})
        _compare_or_regenerate("va_total_annual_charges.parquet", df)

    @pytest.mark.regression()
    def Test_annual_payout_during_deferral_unchanged(self) -> None:
        """calc_annuity_payout returns 0.0 during deferral (regression)."""
        va = Annuity_VA(
            client_age=50,
            annuity_payout_rate=0.05,
            age_income_start=65,
            age_max_ratchet=80,
            rate_rollup_benefit=0.05,
        )
        payout = va.calc_annuity_payout(amount_principal=_PRINCIPAL)
        df = pl.DataFrame({"annual_payout": [payout]})
        _compare_or_regenerate("va_annual_payout_deferral.parquet", df)

    @pytest.mark.regression()
    def Test_annual_payout_at_income_start_unchanged(self) -> None:
        """calc_annuity_payout with m_client_age overridden to income start matches baseline."""
        va = Annuity_VA(
            client_age=64,
            annuity_payout_rate=0.05,
            age_income_start=65,
            age_max_ratchet=80,
            rate_rollup_benefit=0.05,
        )
        va.m_client_age = 65
        payout = va.calc_annuity_payout(amount_principal=_PRINCIPAL)
        df = pl.DataFrame({"annual_payout": [payout]})
        _compare_or_regenerate("va_annual_payout_income_start.parquet", df)

    @pytest.mark.regression()
    def Test_benefit_base_with_rollup_unchanged(self) -> None:
        """calc_benefit_base_with_rollup at fixed parameters matches baseline."""
        va = Annuity_VA(
            client_age=50,
            annuity_payout_rate=0.05,
            age_income_start=65,
            age_max_ratchet=80,
            rate_rollup_benefit=0.05,
        )
        base = va.calc_benefit_base_with_rollup(amount_principal=_PRINCIPAL)
        df = pl.DataFrame({"benefit_base": [base]})
        _compare_or_regenerate("va_benefit_base_rollup.parquet", df)


# ---------------------------------------------------------------------------
# RILA regression
# ---------------------------------------------------------------------------


class Class_Test_Regression_Annuity_RILA:
    """Regression tests for Annuity_RILA calculations."""

    @pytest.mark.regression()
    def Test_downside_return_buffer_unchanged(self) -> None:
        """calc_downside_return with buffer at -0.15 index return matches baseline."""
        rila = Annuity_RILA(
            client_age=45,
            annuity_payout_rate=0.05,
            age_income_start=65,
            protection_type=Protection_Type.BUFFER,
            buffer_rate=0.10,
            cap_rate=0.15,
        )
        downside = rila.calc_downside_return(index_return=-0.15)
        df = pl.DataFrame({"downside_return": [downside]})
        _compare_or_regenerate("rila_downside_return_buffer.parquet", df)

    @pytest.mark.regression()
    def Test_credited_rate_cap_unchanged(self) -> None:
        """calc_credited_rate with cap strategy at index_return=0.20 matches baseline."""
        rila = Annuity_RILA(
            client_age=45,
            annuity_payout_rate=0.05,
            age_income_start=65,
            crediting_strategy=Crediting_Strategy.CAP,
            cap_rate=0.15,
        )
        rate = rila.calc_credited_rate(index_return=0.20)
        df = pl.DataFrame({"credited_rate": [rate]})
        _compare_or_regenerate("rila_credited_rate_cap.parquet", df)

    @pytest.mark.regression()
    def Test_account_values_multi_term_unchanged(self) -> None:
        """calc_account_values_multi_term at fixed returns matches baseline."""
        rila = Annuity_RILA(
            client_age=45,
            annuity_payout_rate=0.05,
            age_income_start=65,
            protection_type=Protection_Type.BUFFER,
            buffer_rate=0.10,
            cap_rate=0.15,
        )
        returns = [0.08, -0.05, 0.12, -0.20, 0.06]
        values = rila.calc_account_values_multi_term(
            amount_principal=_PRINCIPAL,
            term_index_returns=returns,
        )
        df = pl.DataFrame({"account_value": values})
        _compare_or_regenerate("rila_account_values_multi_term.parquet", df)

    @pytest.mark.regression()
    def Test_annual_payout_income_start_unchanged(self) -> None:
        """calc_annuity_payout past income start matches baseline."""
        rila = _make_income_active_rila()
        payout = rila.calc_annuity_payout(amount_principal=_PRINCIPAL)
        df = pl.DataFrame({"annual_payout": [payout]})
        _compare_or_regenerate("rila_annual_payout_income_start.parquet", df)

    @pytest.mark.regression()
    def Test_monthly_payout_income_start_unchanged(self) -> None:
        """calc_monthly_payout past income start matches baseline."""
        rila = _make_income_active_rila()
        monthly = rila.calc_monthly_payout(amount_principal=_PRINCIPAL)
        df = pl.DataFrame({"monthly_payout": [monthly]})
        _compare_or_regenerate("rila_monthly_payout_income_start.parquet", df)

    @pytest.mark.regression()
    def Test_withdrawal_rates_income_start_unchanged(self) -> None:
        """calc_withdrawal_rates past income start matches baseline."""
        rila = _make_income_active_rila()
        withdrawal_rates = rila.calc_withdrawal_rates(amount_principal=_PRINCIPAL)
        df = pl.DataFrame({
            "nominal_WR": [withdrawal_rates.nominal_WR],
            "real_WR": [withdrawal_rates.real_WR],
        })
        _compare_or_regenerate("rila_withdrawal_rates_income_start.parquet", df)

    @pytest.mark.regression()
    def Test_worst_case_account_value_unchanged(self) -> None:
        """calc_worst_case_account_value with 3 terms matches baseline."""
        rila = Annuity_RILA(
            client_age=45,
            annuity_payout_rate=0.05,
            age_income_start=65,
            protection_type=Protection_Type.BUFFER,
            buffer_rate=0.10,
            cap_rate=0.15,
        )
        worst = rila.calc_worst_case_account_value(amount_principal=_PRINCIPAL, num_terms=3)
        df = pl.DataFrame({"worst_case_value": [worst]})
        _compare_or_regenerate("rila_worst_case_account_value.parquet", df)

    @pytest.mark.regression()
    def Test_best_case_account_value_unchanged(self) -> None:
        """calc_best_case_account_value with 3 terms matches baseline."""
        rila = Annuity_RILA(
            client_age=45,
            annuity_payout_rate=0.05,
            age_income_start=65,
            protection_type=Protection_Type.BUFFER,
            buffer_rate=0.10,
            cap_rate=0.15,
        )
        best = rila.calc_best_case_account_value(amount_principal=_PRINCIPAL, num_terms=3)
        df = pl.DataFrame({"best_case_value": [best]})
        _compare_or_regenerate("rila_best_case_account_value.parquet", df)

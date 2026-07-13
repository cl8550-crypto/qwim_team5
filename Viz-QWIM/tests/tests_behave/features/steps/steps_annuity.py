"""Behave step definitions for products.annuity.

Tests cover:
    - Annuity_SPIA: construction, payout, monthly payout, withdrawal rates
    - Annuity_DIA: construction, deferral payout, payout-in-year, future value
    - Annuity_FIA: construction, credited rate, deferral payout, benefit base
    - Annuity_VA: construction, total charges, deferral payout, benefit base
    - Annuity_RILA: construction, downside return, credited rate, multi-term, payout, withdrawal rates, worst/best-case outcomes

Author:         QWIM Development Team
Version:        0.1.0
Last Modified:  2026-05-30
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from behave import given, then, when

# ---------------------------------------------------------------------------
# Project root on sys.path — step files live 4 levels below root:
#   tests/tests_behave/features/steps/<this file>
# ---------------------------------------------------------------------------
_PROJECT_ROOT: Path = Path(__file__).resolve().parents[4]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Module-level import guard
# ---------------------------------------------------------------------------
MODULE_IMPORT_AVAILABLE: bool = True
_import_error_message: str = ""

try:
    from src.products.annuity.annuity_SPIA import Annuity_SPIA
    from src.products.annuity.annuity_DIA import Annuity_DIA
    from src.products.annuity.annuity_FIA import Annuity_FIA
    from src.products.annuity.annuity_VA import Annuity_VA
    from src.products.annuity.annuity_RILA import (
        Annuity_RILA,
        Crediting_Strategy,
        Protection_Type,
    )
except ImportError as _exc:
    MODULE_IMPORT_AVAILABLE = False
    _import_error_message = str(_exc)


def _require_imports() -> None:
    """Raise RuntimeError when required imports are unavailable."""
    if not MODULE_IMPORT_AVAILABLE:
        raise RuntimeError(
            f"products.annuity not importable: {_import_error_message}"
        )


# ===========================================================================
# SPIA — construction
# ===========================================================================


@when(u"I construct an Annuity_SPIA with client_age {age:d} and payout_rate {rate:f}")
def step_construct_spia(context, age: int, rate: float) -> None:
    """Construct Annuity_SPIA and store on context."""
    _require_imports()
    context.spia = Annuity_SPIA(client_age=age, annuity_payout_rate=rate)


@when(u"I attempt to construct an Annuity_SPIA with payout_rate {rate:f}")
def step_attempt_construct_spia_invalid(context, rate: float) -> None:
    """Attempt invalid SPIA construction and capture exception."""
    _require_imports()
    context.raised_exception = None
    try:
        Annuity_SPIA(client_age=65, annuity_payout_rate=rate)
    except Exception as exc:
        context.raised_exception = exc


@then(u"the SPIA client_age should be {age:d}")
def step_spia_client_age(context, age: int) -> None:
    """Assert SPIA m_client_age equals expected age."""
    assert context.spia.m_client_age == age


@then(u"the SPIA payout_rate should be {rate:f}")
def step_spia_payout_rate(context, rate: float) -> None:
    """Assert SPIA m_annuity_payout_rate equals expected rate."""
    assert abs(context.spia.m_annuity_payout_rate - rate) < 1e-9


# ===========================================================================
# SPIA — payout calculations
# ===========================================================================


@when(u"I calculate the SPIA annual payout with principal {principal:f}")
def step_calc_spia_annual_payout(context, principal: float) -> None:
    """Compute SPIA annual payout and store on context."""
    _require_imports()
    context.annual_payout = context.spia.calc_annuity_payout(amount_principal=principal)


@when(u"I calculate the SPIA monthly payout with principal {principal:f}")
def step_calc_spia_monthly_payout(context, principal: float) -> None:
    """Compute SPIA monthly payout and store on context."""
    _require_imports()
    context.monthly_payout = context.spia.calc_monthly_payout(amount_principal=principal)


@when(u"I calculate the SPIA withdrawal rates with principal {principal:f}")
def step_calc_spia_withdrawal_rates(context, principal: float) -> None:
    """Compute SPIA withdrawal rates and store on context."""
    _require_imports()
    context.wr = context.spia.calc_withdrawal_rates(amount_principal=principal)


@then(u"the nominal withdrawal rate should be positive")
def step_nominal_wr_positive(context) -> None:
    """Assert nominal withdrawal rate is positive."""
    assert context.wr.nominal_WR > 0


# ===========================================================================
# DIA — construction
# ===========================================================================


@when(
    u"I construct an Annuity_DIA with client_age {age:d}, "
    u"age_income_start {income_start:d}, and payout_rate {rate:f}"
)
def step_construct_dia(context, age: int, income_start: int, rate: float) -> None:
    """Construct Annuity_DIA and store on context."""
    _require_imports()
    context.dia = Annuity_DIA(
        client_age=age,
        annuity_payout_rate=rate,
        age_income_start=income_start,
    )


@when(
    u"I attempt to construct an Annuity_DIA with client_age {age:d} "
    u"and age_income_start {income_start:d}"
)
def step_attempt_construct_dia_invalid(context, age: int, income_start: int) -> None:
    """Attempt invalid DIA construction and capture exception."""
    _require_imports()
    context.raised_exception = None
    try:
        Annuity_DIA(
            client_age=age,
            annuity_payout_rate=0.05,
            age_income_start=income_start,
        )
    except Exception as exc:
        context.raised_exception = exc


@then(u"the DIA client_age should be {age:d}")
def step_dia_client_age(context, age: int) -> None:
    """Assert DIA m_client_age equals expected age."""
    assert context.dia.m_client_age == age


@then(u"the DIA age_income_start should be {age:d}")
def step_dia_age_income_start(context, age: int) -> None:
    """Assert DIA m_age_income_start equals expected age."""
    assert context.dia.m_age_income_start == age


# ===========================================================================
# DIA — payout calculations
# ===========================================================================


@when(u"I calculate the DIA annual payout with principal {principal:f}")
def step_calc_dia_annual_payout(context, principal: float) -> None:
    """Compute DIA annual payout and store on context."""
    _require_imports()
    context.annual_payout = context.dia.calc_annuity_payout(amount_principal=principal)


@when(u"I calculate the DIA payout in year {year:d} with principal {principal:f}")
def step_calc_dia_payout_in_year(context, year: int, principal: float) -> None:
    """Compute DIA payout in given year and store on context."""
    _require_imports()
    context.payout = context.dia.calc_payout_in_year(
        amount_principal=principal, year_number=year
    )


@when(
    u"I calculate the DIA future value with principal {principal:f} "
    u"and growth_rate {rate:f}"
)
def step_calc_dia_future_value(context, principal: float, rate: float) -> None:
    """Compute DIA future value and store on context."""
    _require_imports()
    context.future_value = context.dia.calc_future_value(
        amount_principal=principal, growth_rate=rate
    )


@then(u"the payout should be positive")
def step_payout_positive(context) -> None:
    """Assert payout is positive."""
    assert context.payout > 0


@then(u"the future value should be {value:f}")
def step_future_value_equals(context, value: float) -> None:
    """Assert future value equals expected value."""
    assert abs(context.future_value - value) < 1e-6


@then(u"the future value should be greater than {value:f}")
def step_future_value_greater_than(context, value: float) -> None:
    """Assert future value is greater than expected."""
    assert context.future_value > value


# ===========================================================================
# FIA — construction
# ===========================================================================


@when(
    u"I construct an Annuity_FIA with client_age {age:d}, "
    u"age_income_start {income_start:d}, and payout_rate {rate:f}"
)
def step_construct_fia(context, age: int, income_start: int, rate: float) -> None:
    """Construct Annuity_FIA and store on context."""
    _require_imports()
    context.fia = Annuity_FIA(
        client_age=age,
        annuity_payout_rate=rate,
        age_income_start=income_start,
        age_max_ratchet=80,
        rate_rollup_benefit=0.05,
        cap_rate=0.07,
        participation_rate=1.0,
        floor_rate=0.0,
    )


@when(
    u"I attempt to construct an Annuity_FIA with client_age {age:d} "
    u"and age_income_start {income_start:d}"
)
def step_attempt_construct_fia_invalid(context, age: int, income_start: int) -> None:
    """Attempt invalid FIA construction and capture exception."""
    _require_imports()
    context.raised_exception = None
    try:
        Annuity_FIA(
            client_age=age,
            annuity_payout_rate=0.05,
            age_income_start=income_start,
            age_max_ratchet=80,
            rate_rollup_benefit=0.05,
        )
    except Exception as exc:
        context.raised_exception = exc


@then(u"the FIA client_age should be {age:d}")
def step_fia_client_age(context, age: int) -> None:
    """Assert FIA m_client_age equals expected age."""
    assert context.fia.m_client_age == age


@then(u"the FIA cap_rate should be {rate:f}")
def step_fia_cap_rate(context, rate: float) -> None:
    """Assert FIA m_cap_rate equals expected rate."""
    assert abs(context.fia.m_cap_rate - rate) < 1e-9


# ===========================================================================
# FIA — credited rate
# ===========================================================================


@when(u"I calculate the FIA credited rate with index_return {ret:f}")
def step_calc_fia_credited_rate(context, ret: float) -> None:
    """Compute FIA credited rate and store on context."""
    _require_imports()
    context.credited_rate = context.fia.calc_credited_rate(index_return=ret)


@then(u"the credited rate should be at most {rate:f}")
def step_credited_rate_at_most(context, rate: float) -> None:
    """Assert credited rate is at most expected value."""
    assert context.credited_rate <= rate + 1e-9


@then(u"the credited rate should be at least {rate:f}")
def step_credited_rate_at_least(context, rate: float) -> None:
    """Assert credited rate is at least expected value."""
    assert context.credited_rate >= rate - 1e-9


# ===========================================================================
# FIA — payout / benefit base
# ===========================================================================


@when(u"I calculate the FIA annual payout with principal {principal:f}")
def step_calc_fia_annual_payout(context, principal: float) -> None:
    """Compute FIA annual payout and store on context."""
    _require_imports()
    context.annual_payout = context.fia.calc_annuity_payout(amount_principal=principal)


@when(u"I calculate the FIA benefit base with principal {principal:f}")
def step_calc_fia_benefit_base(context, principal: float) -> None:
    """Compute FIA benefit base with rollup and store on context."""
    _require_imports()
    context.benefit_base = context.fia.calc_benefit_base_with_rollup(
        amount_principal=principal
    )


# ===========================================================================
# VA — construction
# ===========================================================================


@when(
    u"I construct an Annuity_VA with client_age {age:d}, "
    u"age_income_start {income_start:d}, and payout_rate {rate:f}"
)
def step_construct_va(context, age: int, income_start: int, rate: float) -> None:
    """Construct Annuity_VA and store on context."""
    _require_imports()
    context.va = Annuity_VA(
        client_age=age,
        annuity_payout_rate=rate,
        age_income_start=income_start,
        age_max_ratchet=80,
        rate_rollup_benefit=0.05,
        rate_ME_charge=0.0125,
        rate_admin_fee=0.0015,
        rate_rider_charge=0.0100,
    )


@when(
    u"I attempt to construct an Annuity_VA with client_age {age:d} "
    u"and age_income_start {income_start:d}"
)
def step_attempt_construct_va_invalid(context, age: int, income_start: int) -> None:
    """Attempt invalid VA construction and capture exception."""
    _require_imports()
    context.raised_exception = None
    try:
        Annuity_VA(
            client_age=age,
            annuity_payout_rate=0.05,
            age_income_start=income_start,
            age_max_ratchet=80,
            rate_rollup_benefit=0.05,
        )
    except Exception as exc:
        context.raised_exception = exc


@then(u"the VA client_age should be {age:d}")
def step_va_client_age(context, age: int) -> None:
    """Assert VA m_client_age equals expected age."""
    assert context.va.m_client_age == age


@then(u"the VA has_GMDB should be {value}")
def step_va_has_gmdb(context, value: str) -> None:
    """Assert VA m_has_GMDB matches expected bool string."""
    expected = value.strip() == "True"
    assert context.va.m_has_GMDB == expected


# ===========================================================================
# VA — charges / payout / benefit base
# ===========================================================================


@when(u"I calculate the VA total annual charges")
def step_calc_va_total_charges(context) -> None:
    """Compute VA total annual charges and store on context."""
    _require_imports()
    context.total_charges = context.va.calc_total_annual_charges()


@then(u"the total annual charges should be {expected:f}")
def step_total_charges_equals(context, expected: float) -> None:
    """Assert total annual charges equal expected value."""
    assert abs(context.total_charges - expected) < 1e-9


@when(u"I calculate the VA annual payout with principal {principal:f}")
def step_calc_va_annual_payout(context, principal: float) -> None:
    """Compute VA annual payout and store on context."""
    _require_imports()
    context.annual_payout = context.va.calc_annuity_payout(amount_principal=principal)


@when(u"I calculate the VA benefit base with principal {principal:f}")
def step_calc_va_benefit_base(context, principal: float) -> None:
    """Compute VA benefit base with rollup and store on context."""
    _require_imports()
    context.benefit_base = context.va.calc_benefit_base_with_rollup(
        amount_principal=principal
    )


# ===========================================================================
# RILA — construction
# ===========================================================================


@when(
    u"I construct an Annuity_RILA with client_age {age:d}, "
    u"age_income_start {income_start:d}, and payout_rate {rate:f}"
)
def step_construct_rila(context, age: int, income_start: int, rate: float) -> None:
    """Construct Annuity_RILA and store on context."""
    _require_imports()
    context.rila = Annuity_RILA(
        client_age=age,
        annuity_payout_rate=rate,
        age_income_start=income_start,
        protection_type=Protection_Type.BUFFER,
        buffer_rate=0.10,
        cap_rate=0.15,
    )


@when(
    u"I attempt to construct an Annuity_RILA with client_age {age:d} "
    u"and age_income_start {income_start:d}"
)
def step_attempt_construct_rila_invalid(context, age: int, income_start: int) -> None:
    """Attempt invalid RILA construction and capture exception."""
    _require_imports()
    context.raised_exception = None
    try:
        Annuity_RILA(
            client_age=age,
            annuity_payout_rate=0.05,
            age_income_start=income_start,
        )
    except Exception as exc:
        context.raised_exception = exc


@then(u"the RILA client_age should be {age:d}")
def step_rila_client_age(context, age: int) -> None:
    """Assert RILA m_client_age equals expected age."""
    assert context.rila.m_client_age == age


@then(u"the RILA buffer_rate should be {rate:f}")
def step_rila_buffer_rate(context, rate: float) -> None:
    """Assert RILA m_buffer_rate equals expected rate."""
    assert abs(context.rila.m_buffer_rate - rate) < 1e-9


@when(u"I advance the RILA client_age to {age:d}")
def step_advance_rila_client_age(context, age: int) -> None:
    """Advance the constructed RILA to a later client age."""
    _require_imports()
    context.rila.m_client_age = age


# ===========================================================================
# RILA — downside return
# ===========================================================================


@when(u"I calculate the RILA downside return with index_return {ret:f}")
def step_calc_rila_downside_return(context, ret: float) -> None:
    """Compute RILA downside return and store on context."""
    _require_imports()
    context.downside_return = context.rila.calc_downside_return(index_return=ret)


@then(u"the downside return should be {value:f}")
def step_downside_return_equals(context, value: float) -> None:
    """Assert downside return equals expected value."""
    assert abs(context.downside_return - value) < 1e-9


# ===========================================================================
# RILA — credited rate
# ===========================================================================


@when(u"I calculate the RILA credited rate with index_return {ret:f}")
def step_calc_rila_credited_rate(context, ret: float) -> None:
    """Compute RILA credited rate and store on context."""
    _require_imports()
    context.credited_rate = context.rila.calc_credited_rate(index_return=ret)


# ===========================================================================
# RILA — multi-term
# ===========================================================================


@when(u"I calculate the RILA annual payout with principal {principal:f}")
def step_calc_rila_annual_payout(context, principal: float) -> None:
    """Compute RILA annual payout and store on context."""
    _require_imports()
    context.annual_payout = context.rila.calc_annuity_payout(amount_principal=principal)


@when(u"I calculate the RILA withdrawal rates with principal {principal:f}")
def step_calc_rila_withdrawal_rates(context, principal: float) -> None:
    """Compute RILA withdrawal rates and store on context."""
    _require_imports()
    context.wr = context.rila.calc_withdrawal_rates(amount_principal=principal)


@when(
    u"I calculate the RILA worst-case account value with principal {principal:f} "
    u"and num_terms {num_terms:d}"
)
def step_calc_rila_worst_case_account_value(
    context,
    principal: float,
    num_terms: int,
) -> None:
    """Compute RILA worst-case account value and store on context."""
    _require_imports()
    context.worst_case_account_value = context.rila.calc_worst_case_account_value(
        amount_principal=principal,
        num_terms=num_terms,
    )


@when(
    u"I calculate the RILA best-case account value with principal {principal:f} "
    u"and num_terms {num_terms:d}"
)
def step_calc_rila_best_case_account_value(
    context,
    principal: float,
    num_terms: int,
) -> None:
    """Compute RILA best-case account value and store on context."""
    _require_imports()
    context.best_case_account_value = context.rila.calc_best_case_account_value(
        amount_principal=principal,
        num_terms=num_terms,
    )


@when(
    u"I calculate the RILA account values multi-term with principal {principal:f}"
)
def step_calc_rila_multi_term(context, principal: float) -> None:
    """Compute RILA multi-term account values and store on context."""
    _require_imports()
    context.account_values = context.rila.calc_account_values_multi_term(
        amount_principal=principal,
        term_index_returns=[0.08, -0.05, 0.12],
    )


@then(u"the first account value should be {value:f}")
def step_first_account_value_equals(context, value: float) -> None:
    """Assert first account value equals expected value."""
    assert abs(context.account_values[0] - value) < 1e-6


# ===========================================================================
# Shared steps
# ===========================================================================


@then(u"an exception should be raised")
def step_exception_raised(context) -> None:
    """Assert that an exception was captured."""
    assert context.raised_exception is not None


@then(u"the annual payout should be {value:f}")
def step_annual_payout_equals(context, value: float) -> None:
    """Assert annual payout equals expected value."""
    assert abs(context.annual_payout - value) < 1e-6


@then(u"the monthly payout should be {value:f}")
def step_monthly_payout_equals(context, value: float) -> None:
    """Assert monthly payout equals expected value."""
    assert abs(context.monthly_payout - value) < 1e-6


@then(u"the benefit base should be at least {value:f}")
def step_benefit_base_at_least(context, value: float) -> None:
    """Assert benefit base is at least expected value."""
    assert context.benefit_base >= value - 1e-9


@then(u"the worst-case account value should be {value:f}")
def step_worst_case_account_value_equals(context, value: float) -> None:
    """Assert worst-case account value equals expected value."""
    assert abs(context.worst_case_account_value - value) < 1e-6


@then(u"the best-case account value should be {value:f}")
def step_best_case_account_value_equals(context, value: float) -> None:
    """Assert best-case account value equals expected value."""
    assert abs(context.best_case_account_value - value) < 1e-6

"""
Robot Framework keyword library for products.annuity.
======================================================

Keywords cover:
    - Annuity_SPIA: construction, payout, monthly payout, withdrawal rates
    - Annuity_DIA: construction, deferral payout, payout-in-year, future value
    - Annuity_FIA: construction, credited rate, payout, benefit base
    - Annuity_VA: construction, total charges, payout, benefit base
    - Annuity_RILA: construction, downside return, credited rate, multi-term, payout, withdrawal rates, worst/best-case outcomes

Author:         QWIM Development Team
Version:        0.1.0
Last Modified:  2026-05-30
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Project root on sys.path
# parents: [0]=annuity, [1]=products, [2]=tests_robot_framework, [3]=tests, [4]=root
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Conditional imports (Robot Framework replaces sys.stderr with StringIO)
# ---------------------------------------------------------------------------
MODULE_IMPORT_AVAILABLE: bool = True
_import_error_message: str = ""

_original_stderr = sys.stderr
if not hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(io.BytesIO())

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
except Exception as _exc:  # noqa: BLE001
    MODULE_IMPORT_AVAILABLE = False
    _import_error_message = str(_exc)
finally:
    sys.stderr = _original_stderr


def _require_imports() -> None:
    """Raise RuntimeError when required imports are unavailable."""
    if not MODULE_IMPORT_AVAILABLE:
        raise RuntimeError(
            f"Required imports not available: {_import_error_message}"
        )


# ===========================================================================
# SPIA keywords
# ===========================================================================


def construct_spia(client_age: int, payout_rate: float) -> Annuity_SPIA:
    """Construct and return an Annuity_SPIA instance."""
    _require_imports()
    return Annuity_SPIA(client_age=int(client_age), annuity_payout_rate=float(payout_rate))


def get_spia_annual_payout(spia: Annuity_SPIA, principal: float) -> float:
    """Return annual payout for the given SPIA and principal."""
    _require_imports()
    return spia.calc_annuity_payout(amount_principal=float(principal))


def get_spia_monthly_payout(spia: Annuity_SPIA, principal: float) -> float:
    """Return monthly payout for the given SPIA and principal."""
    _require_imports()
    return spia.calc_monthly_payout(amount_principal=float(principal))


def get_spia_nominal_wr(spia: Annuity_SPIA, principal: float) -> float:
    """Return nominal withdrawal rate for the given SPIA and principal."""
    _require_imports()
    wr = spia.calc_withdrawal_rates(amount_principal=float(principal))
    return wr.nominal_WR


def verify_spia_client_age(spia: Annuity_SPIA, expected_age: int) -> None:
    """Assert that SPIA m_client_age equals expected_age."""
    assert int(spia.m_client_age) == int(expected_age), (
        f"Expected client_age={expected_age}, got {spia.m_client_age}"
    )


def verify_value_equals(actual: float, expected: float, tol: float = 1e-6) -> None:
    """Assert that actual is within tol of expected."""
    assert abs(float(actual) - float(expected)) <= float(tol), (
        f"Expected {expected} but got {actual} (tol={tol})"
    )


def verify_value_positive(value: float) -> None:
    """Assert that value is positive."""
    assert float(value) > 0, f"Expected positive value, got {value}"


# ===========================================================================
# DIA keywords
# ===========================================================================


def construct_dia(
    client_age: int,
    age_income_start: int,
    payout_rate: float,
) -> Annuity_DIA:
    """Construct and return an Annuity_DIA instance."""
    _require_imports()
    return Annuity_DIA(
        client_age=int(client_age),
        annuity_payout_rate=float(payout_rate),
        age_income_start=int(age_income_start),
    )


def get_dia_annual_payout(dia: Annuity_DIA, principal: float) -> float:
    """Return annual payout for the given DIA and principal."""
    _require_imports()
    return dia.calc_annuity_payout(amount_principal=float(principal))


def get_dia_payout_in_year(dia: Annuity_DIA, principal: float, year_number: int) -> float:
    """Return payout in a specific year for the given DIA."""
    _require_imports()
    return dia.calc_payout_in_year(
        amount_principal=float(principal), year_number=int(year_number)
    )


def get_dia_future_value(dia: Annuity_DIA, principal: float, growth_rate: float) -> float:
    """Return future value for the given DIA."""
    _require_imports()
    return dia.calc_future_value(
        amount_principal=float(principal), growth_rate=float(growth_rate)
    )


def verify_value_greater_than(actual: float, threshold: float) -> None:
    """Assert that actual is greater than threshold."""
    assert float(actual) > float(threshold), (
        f"Expected value > {threshold}, got {actual}"
    )


# ===========================================================================
# FIA keywords
# ===========================================================================


def construct_fia(
    client_age: int,
    age_income_start: int,
    payout_rate: float,
    cap_rate: float = 0.07,
) -> Annuity_FIA:
    """Construct and return an Annuity_FIA instance."""
    _require_imports()
    return Annuity_FIA(
        client_age=int(client_age),
        annuity_payout_rate=float(payout_rate),
        age_income_start=int(age_income_start),
        age_max_ratchet=80,
        rate_rollup_benefit=0.05,
        cap_rate=float(cap_rate),
        participation_rate=1.0,
        floor_rate=0.0,
    )


def get_fia_credited_rate(fia: Annuity_FIA, index_return: float) -> float:
    """Return credited rate for the given FIA and index return."""
    _require_imports()
    return fia.calc_credited_rate(index_return=float(index_return))


def get_fia_annual_payout(fia: Annuity_FIA, principal: float) -> float:
    """Return annual payout for the given FIA and principal."""
    _require_imports()
    return fia.calc_annuity_payout(amount_principal=float(principal))


def get_fia_benefit_base(fia: Annuity_FIA, principal: float) -> float:
    """Return benefit base with rollup for the given FIA."""
    _require_imports()
    return fia.calc_benefit_base_with_rollup(amount_principal=float(principal))


def verify_value_at_most(actual: float, maximum: float, tol: float = 1e-9) -> None:
    """Assert that actual is at most maximum (within tolerance)."""
    assert float(actual) <= float(maximum) + float(tol), (
        f"Expected value <= {maximum}, got {actual}"
    )


def verify_value_at_least(actual: float, minimum: float, tol: float = 1e-9) -> None:
    """Assert that actual is at least minimum (within tolerance)."""
    assert float(actual) >= float(minimum) - float(tol), (
        f"Expected value >= {minimum}, got {actual}"
    )


# ===========================================================================
# VA keywords
# ===========================================================================


def construct_va(
    client_age: int,
    age_income_start: int,
    payout_rate: float,
    rate_ME_charge: float = 0.0125,
    rate_admin_fee: float = 0.0015,
    rate_rider_charge: float = 0.0100,
) -> Annuity_VA:
    """Construct and return an Annuity_VA instance."""
    _require_imports()
    return Annuity_VA(
        client_age=int(client_age),
        annuity_payout_rate=float(payout_rate),
        age_income_start=int(age_income_start),
        age_max_ratchet=80,
        rate_rollup_benefit=0.05,
        rate_ME_charge=float(rate_ME_charge),
        rate_admin_fee=float(rate_admin_fee),
        rate_rider_charge=float(rate_rider_charge),
    )


def get_va_total_annual_charges(va: Annuity_VA) -> float:
    """Return total annual charges for the given VA."""
    _require_imports()
    return va.calc_total_annual_charges()


def get_va_annual_payout(va: Annuity_VA, principal: float) -> float:
    """Return annual payout for the given VA and principal."""
    _require_imports()
    return va.calc_annuity_payout(amount_principal=float(principal))


def get_va_benefit_base(va: Annuity_VA, principal: float) -> float:
    """Return benefit base with rollup for the given VA."""
    _require_imports()
    return va.calc_benefit_base_with_rollup(amount_principal=float(principal))


# ===========================================================================
# RILA keywords
# ===========================================================================


def construct_rila(
    client_age: int,
    age_income_start: int,
    payout_rate: float,
    buffer_rate: float = 0.10,
    cap_rate: float = 0.15,
) -> Annuity_RILA:
    """Construct and return an Annuity_RILA instance."""
    _require_imports()
    return Annuity_RILA(
        client_age=int(client_age),
        annuity_payout_rate=float(payout_rate),
        age_income_start=int(age_income_start),
        protection_type=Protection_Type.BUFFER,
        buffer_rate=float(buffer_rate),
        cap_rate=float(cap_rate),
    )


def advance_rila_client_age(rila: Annuity_RILA, client_age: int) -> None:
    """Advance an existing RILA to a later client age."""
    _require_imports()
    rila.m_client_age = int(client_age)


def get_rila_downside_return(rila: Annuity_RILA, index_return: float) -> float:
    """Return downside return for the given RILA and index return."""
    _require_imports()
    return rila.calc_downside_return(index_return=float(index_return))


def get_rila_credited_rate(rila: Annuity_RILA, index_return: float) -> float:
    """Return credited rate for the given RILA and index return."""
    _require_imports()
    return rila.calc_credited_rate(index_return=float(index_return))


def get_rila_annual_payout(rila: Annuity_RILA, principal: float) -> float:
    """Return annual payout for the given RILA and principal."""
    _require_imports()
    return rila.calc_annuity_payout(amount_principal=float(principal))


def get_rila_nominal_wr(rila: Annuity_RILA, principal: float) -> float:
    """Return nominal withdrawal rate for the given RILA and principal."""
    _require_imports()
    withdrawal_rates = rila.calc_withdrawal_rates(amount_principal=float(principal))
    return withdrawal_rates.nominal_WR


def get_rila_worst_case_account_value(
    rila: Annuity_RILA,
    principal: float,
    num_terms: int,
) -> float:
    """Return worst-case account value for the given RILA."""
    _require_imports()
    return rila.calc_worst_case_account_value(
        amount_principal=float(principal),
        num_terms=int(num_terms),
    )


def get_rila_best_case_account_value(
    rila: Annuity_RILA,
    principal: float,
    num_terms: int,
) -> float:
    """Return best-case account value for the given RILA."""
    _require_imports()
    return rila.calc_best_case_account_value(
        amount_principal=float(principal),
        num_terms=int(num_terms),
    )


def get_rila_first_account_value(
    rila: Annuity_RILA,
    principal: float,
    returns: list[float] | None = None,
) -> float:
    """Return first element of multi-term account values."""
    _require_imports()
    if returns is None:
        returns = [0.08, -0.05, 0.12]
    values = rila.calc_account_values_multi_term(
        amount_principal=float(principal), term_index_returns=returns
    )
    return values[0]

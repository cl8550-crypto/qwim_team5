"""Robot Framework keyword library for insurance product tests.

Covers:
    - Insurance_Life_Term
    - Insurance_Life_Whole
    - Insurance_Life_Survivor
    - Insurance_LTC_Traditional
    - Insurance_LTC_Hybrid_Annuity
    - Insurance_LTC_Hybrid_Life

Author:         QWIM Development Team
Version:        0.1.0
Last Modified:  2026-05-28
"""

from __future__ import annotations

import sys
from pathlib import Path

# Resolve project root: insurance → products → tests_robot_framework → tests → root
_PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Suppress stderr noise from RF import machinery
import io as _io
import contextlib as _cl

_buf = _io.StringIO()
with _cl.redirect_stderr(_buf):
    from src.products.insurance.insurance_life.insurance_life_term import (
        Insurance_Life_Term,
    )
    from src.products.insurance.insurance_life.insurance_life_whole import (
        Insurance_Life_Whole,
    )
    from src.products.insurance.insurance_life.insurance_life_survivor import (
        Insurance_Life_Survivor,
    )
    from src.products.insurance.insurance_LTC.insurance_LTC_traditional import (
        Insurance_LTC_Traditional,
        Gender_LTC,
    )
    from src.products.insurance.insurance_LTC.insurance_LTC_hybrid_annuity import (
        Insurance_LTC_Hybrid_Annuity,
    )
    from src.products.insurance.insurance_LTC.insurance_LTC_hybrid_life import (
        Insurance_LTC_Hybrid_Life,
    )


# ---------------------------------------------------------------------------
# Generic verification helpers
# ---------------------------------------------------------------------------


def verify_value_equals(actual, expected, tol: float = 1e-6) -> None:
    """Raise AssertionError if |actual - expected| > tol."""
    a, e = float(actual), float(expected)
    assert abs(a - e) <= tol, f"Expected {e}, got {a}"


def verify_value_positive(value) -> None:
    """Raise AssertionError if value is not positive."""
    assert float(value) > 0, f"Expected positive, got {value}"


def verify_value_non_negative(value) -> None:
    """Raise AssertionError if value is negative."""
    assert float(value) >= 0, f"Expected non-negative, got {value}"


def verify_value_at_least(value, lower) -> None:
    """Raise AssertionError if value < lower."""
    assert float(value) >= float(lower) - 1e-6, f"Expected >= {lower}, got {value}"


# ===========================================================================
# Insurance_Life_Term keywords
# ===========================================================================


def construct_life_term(insured_age: int, face_amount: float) -> Insurance_Life_Term:
    """Construct and return an Insurance_Life_Term object."""
    return Insurance_Life_Term(insured_age=int(insured_age), face_amount=float(face_amount))


def get_term_life_death_benefit(obj: Insurance_Life_Term) -> float:
    """Return calc_death_benefit() result."""
    return obj.calc_death_benefit()


def get_term_life_annual_premium(obj: Insurance_Life_Term) -> float:
    """Return calc_annual_premium() result."""
    return obj.calc_annual_premium()


# ===========================================================================
# Insurance_Life_Whole keywords
# ===========================================================================


def construct_life_whole(insured_age: int, face_amount: float) -> Insurance_Life_Whole:
    """Construct and return an Insurance_Life_Whole object."""
    return Insurance_Life_Whole(insured_age=int(insured_age), face_amount=float(face_amount))


def get_whole_life_annual_premium(obj: Insurance_Life_Whole) -> float:
    """Return calc_annual_premium() result."""
    return obj.calc_annual_premium()


def get_whole_life_cash_value_at_year(obj: Insurance_Life_Whole, year: int) -> float:
    """Return calc_cash_value_at_year(year) result."""
    return obj.calc_cash_value_at_year(year=int(year))


# ===========================================================================
# Insurance_Life_Survivor keywords
# ===========================================================================


def construct_life_survivor(
    insured_age: int, insured_age_second: int, face_amount: float
) -> Insurance_Life_Survivor:
    """Construct and return an Insurance_Life_Survivor object."""
    return Insurance_Life_Survivor(
        insured_age=int(insured_age),
        insured_age_second=int(insured_age_second),
        face_amount=float(face_amount),
    )


def get_survivor_life_death_benefit(obj: Insurance_Life_Survivor) -> float:
    """Return calc_death_benefit() result."""
    return obj.calc_death_benefit()


def get_survivor_life_annual_premium(obj: Insurance_Life_Survivor) -> float:
    """Return calc_annual_premium() result."""
    return obj.calc_annual_premium()


# ===========================================================================
# Insurance_LTC_Traditional keywords
# ===========================================================================


def construct_ltc_traditional_female(
    insured_age: int, daily_benefit_amount: float
) -> Insurance_LTC_Traditional:
    """Construct Insurance_LTC_Traditional (female)."""
    return Insurance_LTC_Traditional(
        insured_age=int(insured_age),
        daily_benefit_amount=float(daily_benefit_amount),
        gender=Gender_LTC.FEMALE,
    )


def get_ltc_traditional_annual_premium(obj: Insurance_LTC_Traditional) -> float:
    """Return calc_annual_premium() result."""
    return obj.calc_annual_premium()


def get_ltc_traditional_monthly_benefit(obj: Insurance_LTC_Traditional) -> float:
    """Return calc_monthly_benefit_amount() result."""
    return obj.calc_monthly_benefit_amount()


def get_ltc_traditional_daily_benefit_at_year(
    obj: Insurance_LTC_Traditional, year: int
) -> float:
    """Return calc_daily_benefit_at_year(year) result."""
    return obj.calc_daily_benefit_at_year(year=int(year))


# ===========================================================================
# Insurance_LTC_Hybrid_Annuity keywords
# ===========================================================================


def construct_ltc_hybrid_annuity(
    insured_age: int, single_premium: float
) -> Insurance_LTC_Hybrid_Annuity:
    """Construct Insurance_LTC_Hybrid_Annuity."""
    return Insurance_LTC_Hybrid_Annuity(
        insured_age=int(insured_age),
        single_premium=float(single_premium),
    )


def get_ltc_hybrid_annuity_annual_premium(obj: Insurance_LTC_Hybrid_Annuity) -> float:
    """Return calc_annual_premium() result."""
    return obj.calc_annual_premium()


def get_ltc_hybrid_annuity_leverage_ratio(obj: Insurance_LTC_Hybrid_Annuity) -> float:
    """Return calc_benefit_leverage_ratio() result."""
    return obj.calc_benefit_leverage_ratio()


def get_ltc_hybrid_annuity_max_lifetime_benefit(
    obj: Insurance_LTC_Hybrid_Annuity,
) -> float:
    """Return calc_maximum_lifetime_benefit() result."""
    return obj.calc_maximum_lifetime_benefit()


# ===========================================================================
# Insurance_LTC_Hybrid_Life keywords
# ===========================================================================


def construct_ltc_hybrid_life(
    insured_age: int, death_benefit: float, single_premium: float
) -> Insurance_LTC_Hybrid_Life:
    """Construct Insurance_LTC_Hybrid_Life."""
    return Insurance_LTC_Hybrid_Life(
        insured_age=int(insured_age),
        death_benefit=float(death_benefit),
        single_premium=float(single_premium),
    )


def get_ltc_hybrid_life_annual_premium(obj: Insurance_LTC_Hybrid_Life) -> float:
    """Return calc_annual_premium() result."""
    return obj.calc_annual_premium()


def get_ltc_hybrid_life_leverage_ratio(obj: Insurance_LTC_Hybrid_Life) -> float:
    """Return calc_benefit_leverage_ratio() result."""
    return obj.calc_benefit_leverage_ratio()


def get_ltc_hybrid_life_max_lifetime_benefit(obj: Insurance_LTC_Hybrid_Life) -> float:
    """Return calc_maximum_lifetime_benefit() result."""
    return obj.calc_maximum_lifetime_benefit()

"""Behave step definitions for insurance product features.

Covers:
    - Insurance_Life_Term
    - Insurance_Life_Whole
    - Insurance_Life_Universal
    - Insurance_Life_Variable
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

from behave import given, then, when


def _require_imports(context) -> None:
    """Lazy-import insurance modules, caching them on context."""
    if getattr(context, "_insurance_imported", False):
        return

    project_root = Path(__file__).resolve().parents[4]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from src.products.insurance.insurance_life.insurance_life_term import (
        Insurance_Life_Term,
    )
    from src.products.insurance.insurance_life.insurance_life_whole import (
        Insurance_Life_Whole,
    )
    from src.products.insurance.insurance_life.insurance_life_universal import (
        Insurance_Life_Universal,
    )
    from src.products.insurance.insurance_life.insurance_life_variable import (
        Insurance_Life_Variable,
        Sub_Account_Type,
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

    context._Insurance_Life_Term = Insurance_Life_Term
    context._Insurance_Life_Whole = Insurance_Life_Whole
    context._Insurance_Life_Universal = Insurance_Life_Universal
    context._Insurance_Life_Variable = Insurance_Life_Variable
    context._Sub_Account_Type = Sub_Account_Type
    context._Insurance_Life_Survivor = Insurance_Life_Survivor
    context._Insurance_LTC_Traditional = Insurance_LTC_Traditional
    context._Gender_LTC = Gender_LTC
    context._Insurance_LTC_Hybrid_Annuity = Insurance_LTC_Hybrid_Annuity
    context._Insurance_LTC_Hybrid_Life = Insurance_LTC_Hybrid_Life
    context._insurance_imported = True


# ---------------------------------------------------------------------------
# Shared "result is" steps
# ---------------------------------------------------------------------------


@then("the result is positive")
def step_result_is_positive(context) -> None:
    assert context.result > 0, f"Expected positive, got {context.result}"


@then("the result is non-negative")
def step_result_is_non_negative(context) -> None:
    assert context.result >= 0, f"Expected non-negative, got {context.result}"


@then("the result equals {expected:f}")
def step_result_equals(context, expected: float) -> None:
    assert abs(context.result - expected) < 1e-6, (
        f"Expected {expected}, got {context.result}"
    )


@then("the result is at least {lower:f}")
def step_result_is_at_least(context, lower: float) -> None:
    assert context.result >= lower - 1e-6, (
        f"Expected >= {lower}, got {context.result}"
    )


# ===========================================================================
# Insurance_Life_Term steps
# ===========================================================================


@given(
    "I construct an Insurance_Life_Term with insured_age {age:d} and face_amount {face:d}"
)
def step_construct_life_term(context, age: int, face: int) -> None:
    _require_imports(context)
    context.life_term = context._Insurance_Life_Term(
        insured_age=age,
        face_amount=float(face),
    )


@then("the term life insured_age is {age:d}")
def step_term_life_insured_age(context, age: int) -> None:
    assert context.life_term.m_insured_age == age


@then("the term life face_amount is {face:f}")
def step_term_life_face_amount(context, face: float) -> None:
    assert abs(context.life_term.m_face_amount - face) < 1e-6


@when("I calculate the term life death benefit")
def step_calc_term_death_benefit(context) -> None:
    context.result = context.life_term.calc_death_benefit()


@when("I calculate the term life annual premium")
def step_calc_term_annual_premium(context) -> None:
    context.result = context.life_term.calc_annual_premium()


# ===========================================================================
# Insurance_Life_Whole steps
# ===========================================================================


@given(
    "I construct an Insurance_Life_Whole with insured_age {age:d} and face_amount {face:d}"
)
def step_construct_life_whole(context, age: int, face: int) -> None:
    _require_imports(context)
    context.life_whole = context._Insurance_Life_Whole(
        insured_age=age,
        face_amount=float(face),
    )


@then("the whole life insured_age is {age:d}")
def step_whole_life_insured_age(context, age: int) -> None:
    assert context.life_whole.m_insured_age == age


@then("the whole life face_amount is {face:f}")
def step_whole_life_face_amount(context, face: float) -> None:
    assert abs(context.life_whole.m_face_amount - face) < 1e-6


@when("I calculate the whole life annual premium")
def step_calc_whole_annual_premium(context) -> None:
    context.result = context.life_whole.calc_annual_premium()


@when("I calculate the whole life cash value at year {year:d}")
def step_calc_whole_cash_value(context, year: int) -> None:
    context.result = context.life_whole.calc_cash_value_at_year(year=year)
    # store indexed for growth comparison
    if not hasattr(context, "_whole_cv"):
        context._whole_cv = {}
    context._whole_cv[year] = context.result


@then("the second result is greater than or equal to the first")
def step_second_ge_first_cv(context) -> None:
    cv = context._whole_cv
    years = sorted(cv.keys())
    assert cv[years[1]] >= cv[years[0]] - 1e-9, (
        f"Expected cv[{years[1]}] >= cv[{years[0]}] but {cv[years[1]]} < {cv[years[0]]}"
    )


# ===========================================================================
# Insurance_Life_Universal steps
# ===========================================================================


@given(
    "I construct an Insurance_Life_Universal with insured_age {age:d} and face_amount {face:d}"
)
def step_construct_life_universal(context, age: int, face: int) -> None:
    _require_imports(context)
    context.life_universal = context._Insurance_Life_Universal(
        insured_age=age,
        face_amount=float(face),
    )


@then("the universal life insured_age is {age:d}")
def step_universal_life_insured_age(context, age: int) -> None:
    assert context.life_universal.m_insured_age == age


@then("the universal life face_amount is {face:f}")
def step_universal_life_face_amount(context, face: float) -> None:
    assert abs(context.life_universal.m_face_amount - face) < 1e-6


@when("I calculate the universal life annual premium")
def step_calc_universal_annual_premium(context) -> None:
    context.result = context.life_universal.calc_annual_premium()


# ===========================================================================
# Insurance_Life_Variable steps
# ===========================================================================


@given(
    "I construct an Insurance_Life_Variable with insured_age {age:d} and face_amount {face:d}"
)
def step_construct_life_variable(context, age: int, face: int) -> None:
    _require_imports(context)
    allocations = {context._Sub_Account_Type.INDEX: 1.0}
    context.life_variable = context._Insurance_Life_Variable(
        insured_age=age,
        face_amount=float(face),
        sub_account_allocations=allocations,
    )


@then("the variable life insured_age is {age:d}")
def step_variable_life_insured_age(context, age: int) -> None:
    assert context.life_variable.m_insured_age == age


@then("the variable life face_amount is {face:f}")
def step_variable_life_face_amount(context, face: float) -> None:
    assert abs(context.life_variable.m_face_amount - face) < 1e-6


@when("I calculate the variable life total annual fees")
def step_calc_variable_total_fees(context) -> None:
    context.result = context.life_variable.calc_total_annual_fees()


@when("I calculate the variable life monthly fees")
def step_calc_variable_monthly_fees(context) -> None:
    context.result = context.life_variable.calc_monthly_fees()


# ===========================================================================
# Insurance_Life_Survivor steps
# ===========================================================================


@given(
    "I construct an Insurance_Life_Survivor with insured_age {age1:d} insured_age_second {age2:d} and face_amount {face:d}"
)
def step_construct_life_survivor(context, age1: int, age2: int, face: int) -> None:
    _require_imports(context)
    context.life_survivor = context._Insurance_Life_Survivor(
        insured_age=age1,
        insured_age_second=age2,
        face_amount=float(face),
    )


@then("the survivor life insured_age is {age:d}")
def step_survivor_life_insured_age(context, age: int) -> None:
    assert context.life_survivor.m_insured_age == age


@then("the survivor life face_amount is {face:f}")
def step_survivor_life_face_amount(context, face: float) -> None:
    assert abs(context.life_survivor.m_face_amount - face) < 1e-6


@when("I calculate the survivor life death benefit")
def step_calc_survivor_death_benefit(context) -> None:
    context.result = context.life_survivor.calc_death_benefit()


@when("I calculate the survivor life annual premium")
def step_calc_survivor_annual_premium(context) -> None:
    context.result = context.life_survivor.calc_annual_premium()


# ===========================================================================
# Insurance_LTC_Traditional steps
# ===========================================================================


@given(
    "I construct an Insurance_LTC_Traditional with insured_age {age:d} daily_benefit {daily:f} and gender {gender_str}"
)
def step_construct_ltc_traditional(
    context, age: int, daily: float, gender_str: str
) -> None:
    _require_imports(context)
    gender = (
        context._Gender_LTC.FEMALE
        if gender_str.upper() == "FEMALE"
        else context._Gender_LTC.MALE
    )
    context.ltc_traditional = context._Insurance_LTC_Traditional(
        insured_age=age,
        daily_benefit_amount=daily,
        gender=gender,
    )


@then("the LTC traditional insured_age is {age:d}")
def step_ltc_traditional_insured_age(context, age: int) -> None:
    assert context.ltc_traditional.m_insured_age == age


@then("the LTC traditional daily_benefit_amount is {daily:f}")
def step_ltc_traditional_daily_benefit(context, daily: float) -> None:
    assert abs(context.ltc_traditional.m_daily_benefit_amount - daily) < 1e-6


@when("I calculate the LTC traditional annual premium")
def step_calc_ltc_trad_annual_premium(context) -> None:
    context.result = context.ltc_traditional.calc_annual_premium()


@when("I calculate the LTC traditional monthly benefit amount")
def step_calc_ltc_trad_monthly_benefit(context) -> None:
    context.result = context.ltc_traditional.calc_monthly_benefit_amount()


@when("I calculate the LTC traditional daily benefit at year {year:d}")
def step_calc_ltc_trad_daily_at_year(context, year: int) -> None:
    context.result = context.ltc_traditional.calc_daily_benefit_at_year(year=year)


# ===========================================================================
# Insurance_LTC_Hybrid_Annuity steps
# ===========================================================================


@given(
    "I construct an Insurance_LTC_Hybrid_Annuity with insured_age {age:d} and single_premium {premium:f}"
)
def step_construct_ltc_hybrid_annuity(context, age: int, premium: float) -> None:
    _require_imports(context)
    context.ltc_hybrid_annuity = context._Insurance_LTC_Hybrid_Annuity(
        insured_age=age,
        single_premium=premium,
    )


@then("the LTC hybrid annuity insured_age is {age:d}")
def step_ltc_hybrid_annuity_insured_age(context, age: int) -> None:
    assert context.ltc_hybrid_annuity.m_insured_age == age


@when("I calculate the LTC hybrid annuity annual premium")
def step_calc_ltc_ha_annual_premium(context) -> None:
    context.result = context.ltc_hybrid_annuity.calc_annual_premium()


@when("I calculate the LTC hybrid annuity benefit leverage ratio")
def step_calc_ltc_ha_leverage(context) -> None:
    context.result = context.ltc_hybrid_annuity.calc_benefit_leverage_ratio()


@when("I calculate the LTC hybrid annuity maximum lifetime benefit")
def step_calc_ltc_ha_max_benefit(context) -> None:
    context.result = context.ltc_hybrid_annuity.calc_maximum_lifetime_benefit()


# ===========================================================================
# Insurance_LTC_Hybrid_Life steps
# ===========================================================================


@given(
    "I construct an Insurance_LTC_Hybrid_Life with insured_age {age:d} death_benefit {db:f} and single_premium {premium:f}"
)
def step_construct_ltc_hybrid_life(context, age: int, db: float, premium: float) -> None:
    _require_imports(context)
    context.ltc_hybrid_life = context._Insurance_LTC_Hybrid_Life(
        insured_age=age,
        death_benefit=db,
        single_premium=premium,
    )


@then("the LTC hybrid life insured_age is {age:d}")
def step_ltc_hybrid_life_insured_age(context, age: int) -> None:
    assert context.ltc_hybrid_life.m_insured_age == age


@when("I calculate the LTC hybrid life annual premium")
def step_calc_ltc_hl_annual_premium(context) -> None:
    context.result = context.ltc_hybrid_life.calc_annual_premium()


@when("I calculate the LTC hybrid life benefit leverage ratio")
def step_calc_ltc_hl_leverage(context) -> None:
    context.result = context.ltc_hybrid_life.calc_benefit_leverage_ratio()


@when("I calculate the LTC hybrid life maximum lifetime benefit")
def step_calc_ltc_hl_max_benefit(context) -> None:
    context.result = context.ltc_hybrid_life.calc_maximum_lifetime_benefit()

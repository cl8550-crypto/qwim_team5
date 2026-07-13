"""Regression tests for insurance product classes.

Baselines stored at:
    tests/tests_regression/_baselines/products/insurance/

Run with REGENERATE_BASELINES=1 to create/update baselines.

Author:         QWIM Development Team
Version:        0.1.0
Last Modified:  2026-05-28
"""

from __future__ import annotations

import os

import polars as pl
import pytest

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
    LTC_Multiplier,
)
from src.products.insurance.insurance_LTC.insurance_LTC_hybrid_life import (
    Insurance_LTC_Hybrid_Life,
)

from tests.tests_regression.products.insurance.conftest import load_baseline, save_baseline


REGENERATE_BASELINES = os.environ.get("REGENERATE_BASELINES", "0") == "1"


def _compare_or_regenerate(filename: str, current_df: pl.DataFrame) -> None:
    """Save baseline (regenerate mode) or compare against stored baseline."""
    if REGENERATE_BASELINES:
        save_baseline(filename, current_df)
        return
    baseline_df = load_baseline(filename)
    for col in baseline_df.columns:
        assert current_df[col].to_list() == pytest.approx(
            baseline_df[col].to_list(), rel=1e-6
        ), f"Column '{col}' differs from baseline in {filename}"


# ===========================================================================
# Insurance_Life_Term
# ===========================================================================


class Class_Test_Regression_Insurance_Life_Term:
    """Regression tests for Insurance_Life_Term."""

    @pytest.mark.regression()
    def Test_calc_death_benefit_regression(self) -> None:
        """calc_death_benefit() matches baseline."""
        results = []
        for age in [30, 40, 50]:
            for face in [250_000, 500_000]:
                obj = Insurance_Life_Term(insured_age=age, face_amount=float(face))
                results.append(
                    {
                        "insured_age": age,
                        "face_amount": float(face),
                        "death_benefit": obj.calc_death_benefit(),
                    }
                )
        df = pl.DataFrame(results)
        _compare_or_regenerate("life_term_death_benefit.parquet", df)

    @pytest.mark.regression()
    def Test_calc_annual_premium_regression(self) -> None:
        """calc_annual_premium() matches baseline."""
        results = []
        for age in [25, 35, 45, 55]:
            obj = Insurance_Life_Term(insured_age=age, face_amount=500_000.0)
            results.append(
                {
                    "insured_age": age,
                    "annual_premium": obj.calc_annual_premium(),
                }
            )
        df = pl.DataFrame(results)
        _compare_or_regenerate("life_term_annual_premium.parquet", df)


# ===========================================================================
# Insurance_Life_Whole
# ===========================================================================


class Class_Test_Regression_Insurance_Life_Whole:
    """Regression tests for Insurance_Life_Whole."""

    @pytest.mark.regression()
    def Test_calc_annual_premium_regression(self) -> None:
        """calc_annual_premium() matches baseline."""
        results = []
        for age in [30, 40, 50]:
            for face in [100_000, 250_000, 500_000]:
                obj = Insurance_Life_Whole(insured_age=age, face_amount=float(face))
                results.append(
                    {
                        "insured_age": age,
                        "face_amount": float(face),
                        "annual_premium": obj.calc_annual_premium(),
                    }
                )
        df = pl.DataFrame(results)
        _compare_or_regenerate("life_whole_annual_premium.parquet", df)

    @pytest.mark.regression()
    def Test_calc_cash_value_at_year_regression(self) -> None:
        """calc_cash_value_at_year() matches baseline for years 5, 10, 20."""
        results = []
        obj = Insurance_Life_Whole(insured_age=40, face_amount=100_000.0)
        for year in [5, 10, 20]:
            results.append(
                {
                    "year": year,
                    "cash_value": obj.calc_cash_value_at_year(year=year),
                }
            )
        df = pl.DataFrame(results)
        _compare_or_regenerate("life_whole_cash_value.parquet", df)


# ===========================================================================
# Insurance_Life_Universal
# ===========================================================================


class Class_Test_Regression_Insurance_Life_Universal:
    """Regression tests for Insurance_Life_Universal."""

    @pytest.mark.regression()
    def Test_calc_annual_premium_regression(self) -> None:
        """calc_annual_premium() matches baseline."""
        results = []
        for age in [35, 45, 55]:
            for face in [250_000, 500_000]:
                obj = Insurance_Life_Universal(insured_age=age, face_amount=float(face))
                results.append(
                    {
                        "insured_age": age,
                        "face_amount": float(face),
                        "annual_premium": obj.calc_annual_premium(),
                    }
                )
        df = pl.DataFrame(results)
        _compare_or_regenerate("life_universal_annual_premium.parquet", df)


# ===========================================================================
# Insurance_Life_Variable
# ===========================================================================


class Class_Test_Regression_Insurance_Life_Variable:
    """Regression tests for Insurance_Life_Variable."""

    @pytest.mark.regression()
    def Test_calc_total_annual_fees_regression(self) -> None:
        """calc_total_annual_fees() matches baseline."""
        results = []
        allocations = {Sub_Account_Type.INDEX: 1.0}
        for age in [30, 45, 60]:
            for face in [250_000, 500_000]:
                obj = Insurance_Life_Variable(
                    insured_age=age,
                    face_amount=float(face),
                    sub_account_allocations=allocations,
                )
                results.append(
                    {
                        "insured_age": age,
                        "face_amount": float(face),
                        "total_annual_fees": obj.calc_total_annual_fees(),
                    }
                )
        df = pl.DataFrame(results)
        _compare_or_regenerate("life_variable_total_fees.parquet", df)


# ===========================================================================
# Insurance_Life_Survivor
# ===========================================================================


class Class_Test_Regression_Insurance_Life_Survivor:
    """Regression tests for Insurance_Life_Survivor."""

    @pytest.mark.regression()
    def Test_calc_death_benefit_regression(self) -> None:
        """calc_death_benefit() matches baseline."""
        results = []
        for age1, age2 in [(50, 48), (55, 53), (60, 58)]:
            for face in [500_000, 1_000_000]:
                obj = Insurance_Life_Survivor(
                    insured_age=age1,
                    insured_age_second=age2,
                    face_amount=float(face),
                )
                results.append(
                    {
                        "insured_age": age1,
                        "insured_age_second": age2,
                        "face_amount": float(face),
                        "death_benefit": obj.calc_death_benefit(),
                    }
                )
        df = pl.DataFrame(results)
        _compare_or_regenerate("life_survivor_death_benefit.parquet", df)

    @pytest.mark.regression()
    def Test_calc_annual_premium_regression(self) -> None:
        """calc_annual_premium() matches baseline."""
        results = []
        for age1, age2 in [(50, 48), (55, 53)]:
            obj = Insurance_Life_Survivor(
                insured_age=age1,
                insured_age_second=age2,
                face_amount=1_000_000.0,
            )
            results.append(
                {
                    "insured_age": age1,
                    "insured_age_second": age2,
                    "annual_premium": obj.calc_annual_premium(),
                }
            )
        df = pl.DataFrame(results)
        _compare_or_regenerate("life_survivor_annual_premium.parquet", df)


# ===========================================================================
# Insurance_LTC_Traditional
# ===========================================================================


class Class_Test_Regression_Insurance_LTC_Traditional:
    """Regression tests for Insurance_LTC_Traditional."""

    @pytest.mark.regression()
    def Test_calc_annual_premium_regression(self) -> None:
        """calc_annual_premium() matches baseline."""
        results = []
        for age in [50, 60, 65]:
            for gender in [Gender_LTC.MALE, Gender_LTC.FEMALE]:
                obj = Insurance_LTC_Traditional(
                    insured_age=age,
                    daily_benefit_amount=200.0,
                    gender=gender,
                )
                results.append(
                    {
                        "insured_age": age,
                        "gender": gender.name,
                        "annual_premium": obj.calc_annual_premium(),
                    }
                )
        df = pl.DataFrame(results)
        _compare_or_regenerate("LTC_traditional_annual_premium.parquet", df)

    @pytest.mark.regression()
    def Test_calc_daily_benefit_at_year_regression(self) -> None:
        """calc_daily_benefit_at_year() matches baseline for years 1, 5, 10."""
        results = []
        obj = Insurance_LTC_Traditional(
            insured_age=55,
            daily_benefit_amount=200.0,
            gender=Gender_LTC.FEMALE,
        )
        for year in [1, 5, 10]:
            results.append(
                {
                    "year": year,
                    "daily_benefit": obj.calc_daily_benefit_at_year(year=year),
                }
            )
        df = pl.DataFrame(results)
        _compare_or_regenerate("LTC_traditional_daily_benefit.parquet", df)


# ===========================================================================
# Insurance_LTC_Hybrid_Annuity
# ===========================================================================


class Class_Test_Regression_Insurance_LTC_Hybrid_Annuity:
    """Regression tests for Insurance_LTC_Hybrid_Annuity."""

    @pytest.mark.regression()
    def Test_calc_maximum_lifetime_benefit_regression(self) -> None:
        """calc_maximum_lifetime_benefit() matches baseline."""
        results = []
        for age in [55, 65]:
            for premium in [100_000.0, 200_000.0]:
                for multiplier in [LTC_Multiplier.TIMES_2, LTC_Multiplier.TIMES_3]:
                    obj = Insurance_LTC_Hybrid_Annuity(
                        insured_age=age,
                        single_premium=premium,
                        LTC_multiplier=multiplier,
                    )
                    results.append(
                        {
                            "insured_age": age,
                            "single_premium": premium,
                            "multiplier": multiplier.name,
                            "max_lifetime_benefit": obj.calc_maximum_lifetime_benefit(),
                        }
                    )
        df = pl.DataFrame(results)
        _compare_or_regenerate("LTC_hybrid_annuity_max_benefit.parquet", df)

    @pytest.mark.regression()
    def Test_calc_benefit_leverage_ratio_regression(self) -> None:
        """calc_benefit_leverage_ratio() matches baseline."""
        results = []
        for age in [55, 65]:
            obj = Insurance_LTC_Hybrid_Annuity(
                insured_age=age,
                single_premium=100_000.0,
            )
            results.append(
                {
                    "insured_age": age,
                    "leverage_ratio": obj.calc_benefit_leverage_ratio(),
                }
            )
        df = pl.DataFrame(results)
        _compare_or_regenerate("LTC_hybrid_annuity_leverage.parquet", df)


# ===========================================================================
# Insurance_LTC_Hybrid_Life
# ===========================================================================


class Class_Test_Regression_Insurance_LTC_Hybrid_Life:
    """Regression tests for Insurance_LTC_Hybrid_Life."""

    @pytest.mark.regression()
    def Test_calc_maximum_lifetime_benefit_regression(self) -> None:
        """calc_maximum_lifetime_benefit() matches baseline."""
        results = []
        for age in [55, 65]:
            for db in [500_000.0, 1_000_000.0]:
                obj = Insurance_LTC_Hybrid_Life(
                    insured_age=age,
                    death_benefit=db,
                    single_premium=100_000.0,
                )
                results.append(
                    {
                        "insured_age": age,
                        "death_benefit": db,
                        "max_lifetime_benefit": obj.calc_maximum_lifetime_benefit(),
                    }
                )
        df = pl.DataFrame(results)
        _compare_or_regenerate("LTC_hybrid_life_max_benefit.parquet", df)

    @pytest.mark.regression()
    def Test_calc_benefit_leverage_ratio_regression(self) -> None:
        """calc_benefit_leverage_ratio() matches baseline."""
        results = []
        for age in [55, 65]:
            obj = Insurance_LTC_Hybrid_Life(
                insured_age=age,
                death_benefit=500_000.0,
                single_premium=100_000.0,
            )
            results.append(
                {
                    "insured_age": age,
                    "leverage_ratio": obj.calc_benefit_leverage_ratio(),
                }
            )
        df = pl.DataFrame(results)
        _compare_or_regenerate("LTC_hybrid_life_leverage.parquet", df)

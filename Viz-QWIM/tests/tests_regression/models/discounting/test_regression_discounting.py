"""Regression tests for :mod:`src.models.discounting`.

Tests verify that the numerical outputs of
``Discounting_Model_Constant`` are stable across code changes by
comparing against committed Parquet baselines.

Regenerate baselines
--------------------
    REGENERATE_BASELINES=1 pytest tests/tests_regression/models/discounting/ -v

Run comparison
--------------
    pytest tests/tests_regression/models/discounting/ -v -m regression
"""

from __future__ import annotations

import datetime
import os
from pathlib import Path

import polars as pl
import pytest

from src.models.discounting.model_discounting_constant import (
    Discounting_Model_Constant,
)
from src.utils.dates_times_utils.daycount import Daycount_Convention

from .conftest import (
    CASH_FLOWS,
    DISCOUNT_RATE_HIGH,
    DISCOUNT_RATE_LOW,
    DISCOUNT_RATE_MID,
    END_DATES_STR,
    VALUATION_DATE_STR,
    load_baseline,
    save_baseline,
)

_REGENERATE: bool = os.environ.get("REGENERATE_BASELINES", "0") == "1"

_START_DATE = datetime.date.fromisoformat(VALUATION_DATE_STR)
_END_DATES = [datetime.date.fromisoformat(d) for d in END_DATES_STR]

_CONVENTIONS = [
    Daycount_Convention.ACTUAL_ACTUAL,
    Daycount_Convention.ACTUAL_360,
    Daycount_Convention.ACTUAL_365,
    Daycount_Convention.THIRTY_360,
]


def _build_discount_factor_table(rate: float) -> pl.DataFrame:
    """Build a DataFrame of discount factors for fixed parameters.

    Parameters
    ----------
    rate : float
        Discount rate to use.

    Returns
    -------
    pl.DataFrame
        Columns: rate, end_date, convention, discount_factor.
    """
    model = Discounting_Model_Constant(discount_rate=rate)
    rows: list[dict] = []
    for end_date in _END_DATES:
        for conv in _CONVENTIONS:
            df_val = model.calc_discount_factor(
                end_date=end_date,
                start_date=_START_DATE,
                daycount_convention=conv,
            )
            rows.append(
                {
                    "rate": rate,
                    "end_date": end_date.isoformat(),
                    "convention": conv.name,
                    "discount_factor": df_val,
                }
            )
    return pl.DataFrame(rows)


def _build_pv_table(rate: float) -> pl.DataFrame:
    """Build a DataFrame of present values for fixed cash-flow stream.

    Parameters
    ----------
    rate : float
        Discount rate to use.

    Returns
    -------
    pl.DataFrame
        Columns: rate, end_date, cash_flow, present_value.
    """
    model = Discounting_Model_Constant(discount_rate=rate)
    rows: list[dict] = []
    for end_date, cf in zip(_END_DATES, CASH_FLOWS):
        pv = model.calc_present_value(
            cash_flow=cf,
            end_date=end_date,
            start_date=_START_DATE,
        )
        rows.append(
            {
                "rate": rate,
                "end_date": end_date.isoformat(),
                "cash_flow": cf,
                "present_value": pv,
            }
        )
    return pl.DataFrame(rows)


# ---------------------------------------------------------------------------
# Discount factor regression — 3 rates
# ---------------------------------------------------------------------------


class Class_Test_Regression_Discounting_Constant_Discount_Factor:
    """Regression suite: discount factors for three rate scenarios."""

    @pytest.mark.regression()
    def Test_low_rate_discount_factors(self) -> None:
        """Discount factors at 3 % match baseline."""
        baseline_file = "discount_factor_low_rate.parquet"
        actual = _build_discount_factor_table(DISCOUNT_RATE_LOW)
        if _REGENERATE:
            save_baseline(baseline_file, actual)
            return
        expected = load_baseline(baseline_file)
        assert actual.shape == expected.shape
        assert actual["discount_factor"].to_list() == pytest.approx(
            expected["discount_factor"].to_list(), rel=1e-9
        )

    @pytest.mark.regression()
    def Test_mid_rate_discount_factors(self) -> None:
        """Discount factors at 5 % match baseline."""
        baseline_file = "discount_factor_mid_rate.parquet"
        actual = _build_discount_factor_table(DISCOUNT_RATE_MID)
        if _REGENERATE:
            save_baseline(baseline_file, actual)
            return
        expected = load_baseline(baseline_file)
        assert actual.shape == expected.shape
        assert actual["discount_factor"].to_list() == pytest.approx(
            expected["discount_factor"].to_list(), rel=1e-9
        )

    @pytest.mark.regression()
    def Test_high_rate_discount_factors(self) -> None:
        """Discount factors at 10 % match baseline."""
        baseline_file = "discount_factor_high_rate.parquet"
        actual = _build_discount_factor_table(DISCOUNT_RATE_HIGH)
        if _REGENERATE:
            save_baseline(baseline_file, actual)
            return
        expected = load_baseline(baseline_file)
        assert actual.shape == expected.shape
        assert actual["discount_factor"].to_list() == pytest.approx(
            expected["discount_factor"].to_list(), rel=1e-9
        )


# ---------------------------------------------------------------------------
# Present value regression — 3 rates
# ---------------------------------------------------------------------------


class Class_Test_Regression_Discounting_Constant_Present_Value:
    """Regression suite: present values for three rate scenarios."""

    @pytest.mark.regression()
    def Test_low_rate_present_values(self) -> None:
        """Present values at 3 % match baseline."""
        baseline_file = "present_value_low_rate.parquet"
        actual = _build_pv_table(DISCOUNT_RATE_LOW)
        if _REGENERATE:
            save_baseline(baseline_file, actual)
            return
        expected = load_baseline(baseline_file)
        assert actual["present_value"].to_list() == pytest.approx(
            expected["present_value"].to_list(), rel=1e-9
        )

    @pytest.mark.regression()
    def Test_mid_rate_present_values(self) -> None:
        """Present values at 5 % match baseline."""
        baseline_file = "present_value_mid_rate.parquet"
        actual = _build_pv_table(DISCOUNT_RATE_MID)
        if _REGENERATE:
            save_baseline(baseline_file, actual)
            return
        expected = load_baseline(baseline_file)
        assert actual["present_value"].to_list() == pytest.approx(
            expected["present_value"].to_list(), rel=1e-9
        )

    @pytest.mark.regression()
    def Test_high_rate_present_values(self) -> None:
        """Present values at 10 % match baseline."""
        baseline_file = "present_value_high_rate.parquet"
        actual = _build_pv_table(DISCOUNT_RATE_HIGH)
        if _REGENERATE:
            save_baseline(baseline_file, actual)
            return
        expected = load_baseline(baseline_file)
        assert actual["present_value"].to_list() == pytest.approx(
            expected["present_value"].to_list(), rel=1e-9
        )

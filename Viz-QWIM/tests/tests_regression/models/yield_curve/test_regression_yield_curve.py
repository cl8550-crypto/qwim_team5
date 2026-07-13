"""Regression tests for yield_curve models.

Each test loads a stored Parquet baseline and asserts that the current
implementation reproduces it exactly.  Set the environment variable
``REGENERATE_BASELINES=1`` to overwrite the baselines (run once after
intentional behaviour changes).

Usage
-----
    # Generate baselines:
    REGENERATE_BASELINES=1 pytest tests/tests_regression/models/yield_curve/ -q

    # Assert no regression:
    pytest tests/tests_regression/models/yield_curve/ -q -m regression
"""

from __future__ import annotations

import os

import polars as pl
import pytest

from .conftest import (
    MATURITIES_PREDICT,
    load_baseline,
    save_baseline,
)


REGENERATE = os.getenv("REGENERATE_BASELINES", "0") == "1"


# ---------------------------------------------------------------------------
# Comparison helper
# ---------------------------------------------------------------------------


def _assert_frames_approx_equal(actual: pl.DataFrame, baseline: pl.DataFrame) -> None:
    """Assert two DataFrames are equal within floating-point tolerance."""
    assert set(actual.columns) == set(baseline.columns), (
        f"Column mismatch: {actual.columns} != {baseline.columns}"
    )
    for col in actual.columns:
        if actual[col].dtype in (pl.Float32, pl.Float64):
            for a, b in zip(actual[col].to_list(), baseline[col].to_list()):
                assert abs(a - b) < 1e-9, (
                    f"Column '{col}' mismatch: {a} != {b}"
                )
        else:
            assert actual[col].to_list() == baseline[col].to_list(), (
                f"Column '{col}' mismatch"
            )


# ===========================================================================
# Constant model — predict
# ===========================================================================


class Class_Test_Regression_Constant_Model_Predict:
    """Regression tests for Yield_Curve_Model_Constant.predict."""

    @pytest.mark.regression()
    def Test_Predict_Fitted_To_Market_Data(
        self, constant_model_fitted
    ) -> None:
        """predict() output matches baseline for market-fitted constant model."""
        df = constant_model_fitted.predict(maturities=MATURITIES_PREDICT)

        if REGENERATE:
            save_baseline(df, "constant_predict_fitted.parquet")
            return

        baseline = load_baseline("constant_predict_fitted.parquet")
        _assert_frames_approx_equal(df, baseline)

    @pytest.mark.regression()
    def Test_Predict_Hardcoded_Rate(
        self, constant_model_hardcoded
    ) -> None:
        """predict() output matches baseline for hard-coded flat rate."""
        df = constant_model_hardcoded.predict(maturities=MATURITIES_PREDICT)

        if REGENERATE:
            save_baseline(df, "constant_predict_hardcoded.parquet")
            return

        baseline = load_baseline("constant_predict_hardcoded.parquet")
        _assert_frames_approx_equal(df, baseline)


# ===========================================================================
# Constant model — par yield and forward rate
# ===========================================================================


class Class_Test_Regression_Constant_Par_Forward:
    """Regression tests for get_par_yield and get_forward_rate (constant model)."""

    @pytest.mark.regression()
    def Test_Par_Yields_At_Standard_Maturities(
        self, constant_model_fitted
    ) -> None:
        """get_par_yield snapshot matches baseline for constant model."""
        par_yields = [
            constant_model_fitted.get_par_yield(maturity = tau) for tau in MATURITIES_PREDICT
        ]
        df = pl.DataFrame(
            {"Maturity": MATURITIES_PREDICT, "Par_Yield": par_yields}
        )

        if REGENERATE:
            save_baseline(df, "constant_par_yield.parquet")
            return

        baseline = load_baseline("constant_par_yield.parquet")
        _assert_frames_approx_equal(df, baseline)

    @pytest.mark.regression()
    def Test_Forward_Rates_At_Standard_Maturities(
        self, constant_model_fitted
    ) -> None:
        """get_forward_rate snapshot matches baseline for constant model."""
        fwd_rates = [
            constant_model_fitted.get_forward_rate(maturity = tau) for tau in MATURITIES_PREDICT
        ]
        df = pl.DataFrame(
            {"Maturity": MATURITIES_PREDICT, "Forward_Rate": fwd_rates}
        )

        if REGENERATE:
            save_baseline(df, "constant_forward_rate.parquet")
            return

        baseline = load_baseline("constant_forward_rate.parquet")
        _assert_frames_approx_equal(df, baseline)


# ===========================================================================
# Standard (Nelson-Siegel) model — predict
# ===========================================================================


class Class_Test_Regression_Standard_Model_Predict:
    """Regression tests for Yield_Curve_Model_Standard.predict."""

    @pytest.mark.regression()
    def Test_Predict_Yields_And_Forward_Rates(
        self, standard_model_fitted
    ) -> None:
        """predict() output matches baseline for NS model fitted to market data."""
        df = standard_model_fitted.predict(maturities=MATURITIES_PREDICT)

        if REGENERATE:
            save_baseline(df, "standard_predict.parquet")
            return

        baseline = load_baseline("standard_predict.parquet")
        _assert_frames_approx_equal(df, baseline)


# ===========================================================================
# Standard (Nelson-Siegel) model — par yield and forward rate
# ===========================================================================


class Class_Test_Regression_Standard_Par_Forward:
    """Regression tests for NS model get_par_yield and get_forward_rate."""

    @pytest.mark.regression()
    def Test_Par_Yields_At_Standard_Maturities(
        self, standard_model_fitted
    ) -> None:
        """get_par_yield snapshot matches baseline for NS model."""
        par_yields = [
            standard_model_fitted.get_par_yield(maturity = tau) for tau in MATURITIES_PREDICT
        ]
        df = pl.DataFrame(
            {"Maturity": MATURITIES_PREDICT, "Par_Yield": par_yields}
        )

        if REGENERATE:
            save_baseline(df, "standard_par_yield.parquet")
            return

        baseline = load_baseline("standard_par_yield.parquet")
        _assert_frames_approx_equal(df, baseline)

    @pytest.mark.regression()
    def Test_Forward_Rates_At_Standard_Maturities(
        self, standard_model_fitted
    ) -> None:
        """get_forward_rate snapshot matches baseline for NS model."""
        fwd_rates = [
            standard_model_fitted.get_forward_rate(maturity = tau) for tau in MATURITIES_PREDICT
        ]
        df = pl.DataFrame(
            {"Maturity": MATURITIES_PREDICT, "Forward_Rate": fwd_rates}
        )

        if REGENERATE:
            save_baseline(df, "standard_forward_rate.parquet")
            return

        baseline = load_baseline("standard_forward_rate.parquet")
        _assert_frames_approx_equal(df, baseline)

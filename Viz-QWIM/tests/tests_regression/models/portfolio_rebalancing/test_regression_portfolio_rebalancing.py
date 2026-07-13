"""Regression tests for :mod:`src.models.portfolio_rebalancing`.

Tests verify that the numerical outputs of
``Portfolio_Rebalancing_Standard.rebalance`` and
``get_summary_statistics`` are stable across code changes by comparing
against committed Parquet baselines.

Regenerate baselines
--------------------
    REGENERATE_BASELINES=1 pytest tests/tests_regression/models/portfolio_rebalancing/ -v

Run comparison
--------------
    pytest tests/tests_regression/models/portfolio_rebalancing/ -v -m regression
"""

from __future__ import annotations

import os

import numpy as np
import polars as pl
import pytest

from src.models.portfolio_rebalancing.portfolio_rebalancing_standard import (
    Portfolio_Rebalancing_Standard,
)

from .conftest import (
    COST_BPS,
    CURRENT_AT_TARGET,
    CURRENT_DRIFTED,
    NAMES_3,
    PORTFOLIO_VALUE,
    TARGET_60_30_10,
    TARGET_EQUAL,
    load_baseline,
    save_baseline,
)


_REGENERATE: bool = os.environ.get("REGENERATE_BASELINES", "0") == "1"


# ---------------------------------------------------------------------------
# Helpers for asserting DataFrames match baselines
# ---------------------------------------------------------------------------


def _assert_frames_approx_equal(actual: pl.DataFrame, baseline: pl.DataFrame) -> None:
    """Assert two DataFrames are equal within floating-point tolerance."""
    assert set(actual.columns) == set(baseline.columns), (
        f"Column mismatch: {actual.columns} vs {baseline.columns}"
    )
    for col in actual.columns:
        if actual[col].dtype == pl.String:
            assert actual[col].to_list() == baseline[col].to_list(), (
                f"Column '{col}' mismatch"
            )
        else:
            act_list = actual[col].to_list()
            bas_list = baseline[col].to_list()
            for i, (a, b) in enumerate(zip(act_list, bas_list, strict=False)):
                assert abs(a - b) < 1e-9, (
                    f"Column '{col}' row {i}: actual={a} vs baseline={b}"
                )


# ===========================================================================
# Regression tests — equal-weight target
# ===========================================================================


@pytest.mark.regression()
class Class_Test_Regression_Rebalance_Equal_Target:
    """Regression tests for rebalance with equal-weight target (1/3 each)."""

    @pytest.mark.regression()
    def Test_Rebalance_Drifted_Equal(self, strategy_equal: Portfolio_Rebalancing_Standard) -> None:
        """Rebalancing drifted weights with equal target stays stable."""
        actual = strategy_equal.rebalance(current_weights = CURRENT_DRIFTED, portfolio_value=PORTFOLIO_VALUE)

        if _REGENERATE:
            save_baseline(actual, "rebalance_drifted_equal.parquet")
            return

        baseline = load_baseline("rebalance_drifted_equal.parquet")
        _assert_frames_approx_equal(actual, baseline)

    @pytest.mark.regression()
    def Test_Rebalance_At_Target_Equal(self, strategy_equal: Portfolio_Rebalancing_Standard) -> None:
        """Rebalancing at-target weights produces zero trades (stable)."""
        actual = strategy_equal.rebalance(current_weights = CURRENT_AT_TARGET, portfolio_value=PORTFOLIO_VALUE)

        if _REGENERATE:
            save_baseline(actual, "rebalance_at_target_equal.parquet")
            return

        baseline = load_baseline("rebalance_at_target_equal.parquet")
        _assert_frames_approx_equal(actual, baseline)


# ===========================================================================
# Regression tests — 60/30/10 target
# ===========================================================================


@pytest.mark.regression()
class Class_Test_Regression_Rebalance_60_30_10:
    """Regression tests for rebalance with 60/30/10 target."""

    @pytest.mark.regression()
    def Test_Rebalance_Drifted_60_30_10(
        self, strategy_60_30_10: Portfolio_Rebalancing_Standard
    ) -> None:
        """Rebalancing drifted weights with 60/30/10 target stays stable."""
        # Drift: Equities at 0.50 (under-weight), Bonds at 0.40 (over), Cash at 0.10
        current = np.array([0.50, 0.40, 0.10])
        actual = strategy_60_30_10.rebalance(current_weights = current, portfolio_value=PORTFOLIO_VALUE)

        if _REGENERATE:
            save_baseline(actual, "rebalance_drifted_60_30_10.parquet")
            return

        baseline = load_baseline("rebalance_drifted_60_30_10.parquet")
        _assert_frames_approx_equal(actual, baseline)

    @pytest.mark.regression()
    def Test_Rebalance_At_Target_60_30_10(
        self, strategy_60_30_10: Portfolio_Rebalancing_Standard
    ) -> None:
        """Rebalancing at-target weights (60/30/10) produces zero trades."""
        actual = strategy_60_30_10.rebalance(current_weights = TARGET_60_30_10.copy(), portfolio_value=PORTFOLIO_VALUE)

        if _REGENERATE:
            save_baseline(actual, "rebalance_at_target_60_30_10.parquet")
            return

        baseline = load_baseline("rebalance_at_target_60_30_10.parquet")
        _assert_frames_approx_equal(actual, baseline)


# ===========================================================================
# Regression tests — summary statistics
# ===========================================================================


@pytest.mark.regression()
class Class_Test_Regression_Summary_Statistics:
    """Regression tests for get_summary_statistics output."""

    @pytest.mark.regression()
    def Test_Summary_Drifted_Equal(self, strategy_equal: Portfolio_Rebalancing_Standard) -> None:
        """Summary statistics for drifted equal-weight rebalance stay stable."""
        rebalance_result = strategy_equal.rebalance(
            current_weights = CURRENT_DRIFTED, portfolio_value=PORTFOLIO_VALUE
        )
        actual = strategy_equal.get_summary_statistics(rebalancing_result = rebalance_result)

        if _REGENERATE:
            save_baseline(actual, "summary_drifted_equal.parquet")
            return

        baseline = load_baseline("summary_drifted_equal.parquet")
        _assert_frames_approx_equal(actual, baseline)

    @pytest.mark.regression()
    def Test_Summary_At_Target_Equal(self, strategy_equal: Portfolio_Rebalancing_Standard) -> None:
        """Summary statistics for at-target equal rebalance show zero turnover."""
        rebalance_result = strategy_equal.rebalance(
            current_weights = CURRENT_AT_TARGET, portfolio_value=PORTFOLIO_VALUE
        )
        actual = strategy_equal.get_summary_statistics(rebalancing_result = rebalance_result)

        if _REGENERATE:
            save_baseline(actual, "summary_at_target_equal.parquet")
            return

        baseline = load_baseline("summary_at_target_equal.parquet")
        _assert_frames_approx_equal(actual, baseline)

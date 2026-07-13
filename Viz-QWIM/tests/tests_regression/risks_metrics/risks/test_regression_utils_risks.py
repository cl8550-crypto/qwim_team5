"""Regression tests for Risk_Measure_Type category classmethods.

These tests verify that the membership of each risk measure category does
not change unexpectedly across code changes or refactors.

Test Strategy
-------------
Each test:
1. Loads a pre-computed Parquet baseline from ``_baselines/risks_metrics/risks/``.
2. Calls the corresponding classmethod on ``Risk_Measure_Type``.
3. Compares every member name and value against the stored baseline.

Baseline Regeneration
---------------------
If category membership is intentionally changed, see conftest.py for the
regeneration command, then commit code + updated Parquet files together.
"""

from __future__ import annotations

import polars as pl
import pytest

from src.risks_metrics.risks.utils_risks import Risk_Measure_Type
from tests.tests_regression.risks_metrics.risks.conftest import load_baseline


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _assert_category_matches_baseline(
    current_members: list[Risk_Measure_Type],
    baseline_filename: str,
    label: str = "",
) -> None:
    """Compare current category members against the stored Parquet baseline.

    Parameters
    ----------
    current_members:
        Members returned by the category classmethod.
    baseline_filename:
        Filename (not path) of the Parquet baseline.
    label:
        Label used in error messages.

    Raises
    ------
    AssertionError
        If the member list differs from the baseline in size or content.
    """
    baseline = load_baseline(baseline_filename)
    current_df = pl.DataFrame(
        {
            "member_name": [m.name for m in current_members],
            "member_value": [m.value for m in current_members],
        }
    )
    assert current_df.shape == baseline.shape, (
        f"Shape mismatch {label}: current={current_df.shape}, "
        f"baseline={baseline.shape}"
    )
    assert current_df["member_name"].to_list() == baseline["member_name"].to_list(), (
        f"member_name mismatch {label}"
    )
    assert current_df["member_value"].to_list() == baseline["member_value"].to_list(), (
        f"member_value mismatch {label}"
    )


# ---------------------------------------------------------------------------
# Regression tests — one per category classmethod
# ---------------------------------------------------------------------------


class Class_Test_Regression_Risk_Measure_Type_Categories:
    """Regression tests verifying Risk_Measure_Type category membership stability."""

    @pytest.mark.regression()
    def Test_variance_based_category_unchanged(self) -> None:
        """Variance-based category matches stored baseline."""
        _assert_category_matches_baseline(
            Risk_Measure_Type.get_variance_based_measures(),
            "category_variance_based.parquet",
            label="variance_based",
        )

    @pytest.mark.regression()
    def Test_var_family_category_unchanged(self) -> None:
        """VaR-family category matches stored baseline."""
        _assert_category_matches_baseline(
            Risk_Measure_Type.get_var_family_measures(),
            "category_var_family.parquet",
            label="var_family",
        )

    @pytest.mark.regression()
    def Test_drawdown_category_unchanged(self) -> None:
        """Drawdown category matches stored baseline."""
        _assert_category_matches_baseline(
            Risk_Measure_Type.get_drawdown_measures(),
            "category_drawdown.parquet",
            label="drawdown",
        )

    @pytest.mark.regression()
    def Test_higher_moment_category_unchanged(self) -> None:
        """Higher-moment category matches stored baseline."""
        _assert_category_matches_baseline(
            Risk_Measure_Type.get_higher_moment_measures(),
            "category_higher_moment.parquet",
            label="higher_moment",
        )

    @pytest.mark.regression()
    def Test_coherent_category_unchanged(self) -> None:
        """Coherent category matches stored baseline."""
        _assert_category_matches_baseline(
            Risk_Measure_Type.get_coherent_measures(),
            "category_coherent.parquet",
            label="coherent",
        )

    @pytest.mark.regression()
    def Test_convex_category_unchanged(self) -> None:
        """Convex category matches stored baseline."""
        _assert_category_matches_baseline(
            Risk_Measure_Type.get_convex_measures(),
            "category_convex.parquet",
            label="convex",
        )

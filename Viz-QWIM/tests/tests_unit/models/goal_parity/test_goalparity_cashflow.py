"""Unit tests for CashFlowEstimator (Step 2, Roadmap Sec 3.2)."""

from __future__ import annotations

import pytest

from src.models.goal_parity import CashFlowEstimator
from src.models.goal_parity._goalparity_data import AssetStats


def _asset(a: float = 0.06, income_fraction: float = 0.5) -> AssetStats:
    return AssetStats(
        ticker="TEST", name="Test Asset", asset_class="sectors",
        a=a, sigma=0.15, gamma=0.0, income_fraction=income_fraction,
    )


class Test_EPV_Convention:
    def test_epv_equals_rc_plus_rn(self) -> None:
        profile = CashFlowEstimator().profile(_asset(), T=10)
        assert profile.epv == pytest.approx(profile.epv_rc + profile.epv_rn)

    def test_total_epv_matches_one_plus_aT(self) -> None:
        """EPV/I = 1 + a*T regardless of the RC/RN split (Sec 3.2)."""
        profile = CashFlowEstimator().profile(_asset(a=0.06), T=10)
        assert profile.epv == pytest.approx(1 + 0.06 * 10)

    def test_income_fraction_drives_split(self) -> None:
        profile = CashFlowEstimator().profile(_asset(a=0.08, income_fraction=0.75), T=5)
        assert profile.a_rn == pytest.approx(0.06)
        assert profile.a_rc == pytest.approx(0.02)
        assert profile.epv_rn == pytest.approx(0.30)

    def test_negative_carry_epv_floored_positive(self) -> None:
        """VIXY-style assets must not produce negative EPV (Step 4 corruption)."""
        profile = CashFlowEstimator().profile(_asset(a=-0.55, income_fraction=0.0), T=25)
        assert profile.epv == pytest.approx(0.01)

    def test_rejects_nonpositive_horizon(self) -> None:
        with pytest.raises(ValueError):
            CashFlowEstimator().profile(_asset(), T=0)


class Test_WAM:
    def test_pure_zero_coupon_wam_is_T(self) -> None:
        profile = CashFlowEstimator().profile(_asset(a=0.05, income_fraction=0.0), T=8)
        assert profile.wam == pytest.approx(8)

    def test_income_shortens_wam(self) -> None:
        no_income = CashFlowEstimator().profile(_asset(income_fraction=0.0), T=10)
        with_income = CashFlowEstimator().profile(_asset(income_fraction=0.9), T=10)
        assert with_income.wam < no_income.wam

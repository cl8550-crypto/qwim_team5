"""Unit tests for VolatilityAdjuster (Step 3, Roadmap Sec 3.3)."""

from __future__ import annotations

import pytest

from src.models.goal_parity import VolatilityAdjuster
from src.models.goal_parity._goalparity_data import AssetStats


def _asset(sigma: float = 0.20, gamma: float = 0.0) -> AssetStats:
    return AssetStats(
        ticker="TEST", name="Test", asset_class="sectors",
        a=0.05, sigma=sigma, gamma=gamma, income_fraction=0.25,
    )


class Test_Skew_Adjustment:
    def test_zero_skew_leaves_vols_unchanged(self) -> None:
        adjusted = VolatilityAdjuster(kappa=2.0).adjust(_asset(gamma=0.0))
        assert adjusted.sigma_d == pytest.approx(0.20)
        assert adjusted.sigma_l == pytest.approx(0.20)

    def test_negative_skew_raises_defaultility_lowers_liquitility(self) -> None:
        adjusted = VolatilityAdjuster(kappa=2.0).adjust(_asset(gamma=-1.0))
        assert adjusted.sigma_d > 0.20
        assert adjusted.sigma_l < 0.20

    def test_positive_skew_is_symmetric_opposite(self) -> None:
        adjusted = VolatilityAdjuster(kappa=2.0).adjust(_asset(gamma=+1.0))
        assert adjusted.sigma_l > 0.20
        assert adjusted.sigma_d < 0.20
        # sigma_d * sigma_l == sigma^2 (the exp adjustments are reciprocal)
        assert adjusted.sigma_d * adjusted.sigma_l == pytest.approx(0.20**2)

    def test_extreme_skew_is_capped(self) -> None:
        adjusted = VolatilityAdjuster(kappa=0.5).adjust(_asset(gamma=-50.0))
        assert adjusted.sigma_d == pytest.approx(0.20 * 4.4817, abs=0.01)  # capped at e^1.5

    def test_rejects_nonpositive_kappa(self) -> None:
        with pytest.raises(ValueError):
            VolatilityAdjuster(kappa=0.0)

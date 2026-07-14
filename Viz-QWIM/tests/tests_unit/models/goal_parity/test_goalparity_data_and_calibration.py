"""Unit tests for the data layer, asset map, and calibration utilities."""

from __future__ import annotations

import numpy as np
import pytest

from src.models.goal_parity import AssetUniverse, CalibrationSuite, GoalDecomposer
from src.models.goal_parity._goalparity_asset_map import asset_map_coordinates
from src.models.goal_parity._goalparity_data import find_cleaned_data_dir


class Test_Asset_Universe:
    """Integration-light checks against the real cleaned_data folder."""

    @pytest.fixture(scope="class")
    def universe(self) -> AssetUniverse:
        try:
            return AssetUniverse.load()
        except FileNotFoundError:
            pytest.skip("cleaned_data folder not present in this checkout")

    def test_loads_all_investable_assets(self, universe: AssetUniverse) -> None:
        assert len(universe.tickers) >= 15
        assert "BIL" in universe.tickers
        assert "VIX" not in universe.tickers  # index is context, not investable

    def test_stats_are_finite_and_annualized(self, universe: AssetUniverse) -> None:
        for stats in universe.all_stats():
            assert np.isfinite(stats.a) and np.isfinite(stats.sigma) and np.isfinite(stats.gamma)
            assert 0.0 < stats.sigma < 2.0

    def test_risk_free_rate_plausible(self, universe: AssetUniverse) -> None:
        assert -0.02 < universe.risk_free_rate() < 0.15

    def test_common_start_date_is_latest_inception(self, universe: AssetUniverse) -> None:
        start = universe.common_start_date()
        assert all(frame["Date"].min() <= start for frame in universe.frames.values())

    def test_aligned_returns_share_dates(self, universe: AssetUniverse) -> None:
        aligned = universe.aligned_returns(["BIL", "AGG"])
        assert aligned.columns == ["Date", "BIL", "AGG"]
        assert aligned.height > 100

    def test_cash_tickers_are_rates_class(self, universe: AssetUniverse) -> None:
        assert set(universe.cash_tickers()) == {"BIL", "SHV"}

    def test_find_cleaned_data_dir_resolves(self) -> None:
        assert find_cleaned_data_dir().name == "cleaned_data"


class Test_Asset_Map:
    def test_cash_plots_at_origin(self) -> None:
        shares = GoalDecomposer().decompose(
            "CASH", epv=1.0, sigma_d=0.001, sigma_l=0.001, T=20, tau_years=0.5, b=0.85
        )
        assert asset_map_coordinates(shares) == pytest.approx((0.0, 0.0), abs=0.02)

    def test_coordinates_bounded(self) -> None:
        shares = GoalDecomposer().decompose(
            "EQTY", epv=2.0, sigma_d=0.3, sigma_l=0.3, T=25, tau_years=0.5, b=0.9
        )
        x, y = asset_map_coordinates(shares)
        assert 0.0 <= x <= 1.0 and 0.0 <= y <= 1.0


class Test_Calibration:
    def test_gaussian_tail_fraction_small(self) -> None:
        rng = np.random.default_rng(5)
        fraction = CalibrationSuite.tail_variance_fraction(rng.normal(0, 0.01, 5000))
        assert 0.0 < fraction < 0.35

    def test_fit_kappa_floors_at_one(self) -> None:
        rng = np.random.default_rng(5)
        heavy = rng.standard_t(df=2, size=5000) * 0.01
        assert CalibrationSuite.fit_kappa(heavy) >= 1.0

    def test_default_recovered_at_quarter_tail(self) -> None:
        # tail fraction 0.25 -> kappa = 2.0 (module default)
        class _Fake(CalibrationSuite):
            @staticmethod
            def tail_variance_fraction(returns, z=2.0):
                return 0.25

        assert _Fake.fit_kappa(np.zeros(100)) == pytest.approx(2.0)

    def test_walk_forward_produces_folds(self) -> None:
        data = np.arange(100.0)
        folds = CalibrationSuite.walk_forward(data, lambda tr, te: float(te.mean()), n_folds=4)
        assert len(folds) == 4
        assert folds[0].train.size < folds[-1].train.size

    def test_walk_forward_rejects_tiny_samples(self) -> None:
        with pytest.raises(ValueError):
            CalibrationSuite.walk_forward(np.arange(5.0), lambda tr, te: 0.0, n_folds=4)

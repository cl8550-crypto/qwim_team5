"""Unit tests for the walk-forward backtest (run_walk_forward).

Uses a small synthetic AssetUniverse (deterministic rng) so results are
independent of the repo's market data, mirroring the other model tests.
"""

from __future__ import annotations

import datetime

import numpy as np
import polars as pl
import pytest

from src.models.goal_parity import InvestorProfile, run_walk_forward
from src.models.goal_parity._goalparity_backtest import (
    TRADING_DAYS_PER_MONTH,
    _benchmark_weights,
    _performance_summary,
    _simple_daily_returns,
)
from src.models.goal_parity._goalparity_data import AssetUniverse


N_DAYS = 5 * 252  # five years of synthetic daily data

_ASSET_SPECS: list[tuple[str, str, float, float]] = [
    # ticker, class, daily mean, daily vol
    ("EQTY", "sectors", 0.0004, 0.010),
    ("EQT2", "sectors", 0.0003, 0.012),
    ("BOND", "bonds", 0.0001, 0.003),
    ("BIL", "rates", 0.00008, 0.0005),
]


@pytest.fixture(scope="module")
def universe() -> AssetUniverse:
    rng = np.random.default_rng(7)
    dates = pl.date_range(
        datetime.date(2019, 1, 1),
        datetime.date(2019, 1, 1) + datetime.timedelta(days=int(N_DAYS * 1.6)),
        interval="1d",
        eager=True,
    ).head(N_DAYS)
    u = AssetUniverse(data_dir=None)  # type: ignore[arg-type]
    for ticker, asset_class, mu, sigma in _ASSET_SPECS:
        returns = rng.normal(mu, sigma, N_DAYS)
        u.frames[ticker] = pl.DataFrame({"Date": dates, "Log_Return": returns})
        u.names[ticker] = ticker
        u.classes[ticker] = asset_class
    return u


@pytest.fixture(scope="module")
def profile() -> InvestorProfile:
    return InvestorProfile(T=25, tau_months=6, risk_profile="Moderate")


@pytest.fixture(scope="module")
def result(universe: AssetUniverse, profile: InvestorProfile):
    return run_walk_forward(universe, profile, train_years=2.0, test_months=6, step_months=6)


class Test_Walk_Forward_Structure:
    def test_nav_curves_align_with_dates(self, result) -> None:
        assert len(result.dates) == len(result.portfolio_nav) == len(result.benchmark_nav)
        assert len(result.dates) > 0

    def test_nav_starts_near_one(self, result) -> None:
        # First NAV point is 1 * exp(first day's return), so close to 1.
        assert result.portfolio_nav[0] == pytest.approx(1.0, abs=0.05)

    def test_expected_fold_count(self, result) -> None:
        train_days = 2 * 252
        step_days = 6 * TRADING_DAYS_PER_MONTH
        expected = len(range(train_days, N_DAYS, step_days))
        assert len(result.folds) == expected

    def test_no_look_ahead_in_folds(self, result) -> None:
        for fold in result.folds:
            assert fold.train_end < fold.test_start
            assert fold.train_start <= fold.train_end

    def test_fold_weights_on_simplex(self, result) -> None:
        for fold in result.folds:
            weights = np.array(list(fold.weights.values()))
            assert weights.sum() == pytest.approx(1.0, abs=1e-6)
            assert (weights >= -1e-9).all()

    def test_summary_has_both_strategies(self, result) -> None:
        for name in ("Goal Parity", "Benchmark"):
            stats = result.summary[name]
            assert set(stats) == {
                "total_return",
                "annualized_return",
                "annualized_volatility",
                "sharpe_ratio",
                "max_drawdown",
            }
            assert stats["max_drawdown"] <= 0.0


class Test_Input_Guardrails:
    def test_too_short_training_window_rejected(self, universe, profile) -> None:
        with pytest.raises(ValueError, match="at least 1 year"):
            run_walk_forward(universe, profile, train_years=0.5)

    def test_insufficient_data_rejected(self, universe, profile) -> None:
        with pytest.raises(ValueError, match="Not enough data"):
            run_walk_forward(
                universe,
                profile,
                train_years=2.0,
                end_date=datetime.date(2019, 6, 1),
            )

    def test_short_train_window_warns(self, universe, profile) -> None:
        result = run_walk_forward(universe, profile, train_years=1.0, step_months=6)
        assert any("short" in w for w in result.warnings)

    def test_step_defaults_to_profile_tau(self, universe, profile) -> None:
        explicit = run_walk_forward(universe, profile, train_years=2.0, step_months=6)
        defaulted = run_walk_forward(universe, profile, train_years=2.0, step_months=None)
        assert len(defaulted.folds) == len(explicit.folds)


class Test_Benchmark:
    def test_sixty_forty_weights(self, universe) -> None:
        weights, description = _benchmark_weights(universe, ["EQTY", "EQT2", "BOND", "BIL"])
        assert weights.sum() == pytest.approx(1.0)
        assert weights[0] == weights[1] == pytest.approx(0.30)
        assert weights[2] == pytest.approx(0.40)
        assert weights[3] == 0.0
        assert "60%" in description

    def test_fallback_without_bonds_uses_rates(self, universe) -> None:
        weights, _ = _benchmark_weights(universe, ["EQTY", "BIL"])
        assert weights[0] == pytest.approx(0.60)
        assert weights[1] == pytest.approx(0.40)

    def test_fallback_single_sleeve(self, universe) -> None:
        weights, description = _benchmark_weights(universe, ["EQTY", "EQT2"])
        assert weights.sum() == pytest.approx(1.0)
        assert "one benchmark sleeve" in description


class Test_Return_Math:
    def test_simple_daily_returns_single_asset_identity(self) -> None:
        log_returns = np.array([[0.01], [-0.02], [0.005]])
        weights = np.array([1.0])
        out = _simple_daily_returns(log_returns, weights)
        assert np.allclose(out, log_returns.ravel())

    def test_performance_summary_flat_series(self) -> None:
        daily = np.full(252, 0.0001)
        nav = np.exp(np.cumsum(daily))
        stats = _performance_summary(daily, nav)
        assert stats["annualized_return"] == pytest.approx(np.expm1(0.0001 * 252))
        assert stats["max_drawdown"] == pytest.approx(0.0)

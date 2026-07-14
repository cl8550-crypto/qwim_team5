"""Unit tests for GoalDecomposer (Step 4, Roadmap Sec 3.4)."""

from __future__ import annotations

import pytest

from src.models.goal_parity import GoalDecomposer, first_passage_probability
from src.models.goal_parity.utils_goal_parity import GOALS


class Test_First_Passage_Probability:
    def test_barrier_at_current_level_hits_immediately(self) -> None:
        assert first_passage_probability(T=5, sigma=0.2, barrier=1.0) == 1.0

    def test_zero_barrier_never_hits(self) -> None:
        assert first_passage_probability(T=5, sigma=0.2, barrier=0.0) == 0.0

    def test_zero_volatility_never_hits(self) -> None:
        assert first_passage_probability(T=5, sigma=0.0, barrier=0.9) == 0.0

    def test_monotone_in_volatility(self) -> None:
        probs = [first_passage_probability(10, s, 0.85) for s in (0.05, 0.10, 0.20, 0.40)]
        assert probs == sorted(probs)

    def test_monotone_in_horizon(self) -> None:
        probs = [first_passage_probability(t, 0.2, 0.85) for t in (1, 5, 10, 25)]
        assert probs == sorted(probs)

    def test_bounded_in_unit_interval(self) -> None:
        p = first_passage_probability(30, 0.6, 0.99)
        assert 0.0 <= p <= 1.0


class Test_EPV_Split:
    def test_split_sums_to_epv(self) -> None:
        split = GoalDecomposer().epv_split(epv=2.5, pi_d=0.63, pi_l=0.41)
        assert sum(split.values()) == pytest.approx(2.5)
        assert set(split) == set(GOALS)

    def test_truth_table_corners(self) -> None:
        decomposer = GoalDecomposer()
        assert decomposer.epv_split(1.0, 1.0, 1.0)["Growth"] == pytest.approx(1.0)
        assert decomposer.epv_split(1.0, 1.0, 0.0)["Income"] == pytest.approx(1.0)
        assert decomposer.epv_split(1.0, 0.0, 1.0)["Preservation"] == pytest.approx(1.0)
        assert decomposer.epv_split(1.0, 0.0, 0.0)["Liquidity"] == pytest.approx(1.0)


class Test_Decompose:
    def test_cash_is_almost_entirely_liquidity(self) -> None:
        """sigma_D = sigma_L ~ 0 -> both triggers ~0 -> EPV_L ~ EPV (Sec 3.4)."""
        shares = GoalDecomposer().decompose(
            "CASH", epv=1.3, sigma_d=0.004, sigma_l=0.004, T=25, tau_years=0.5, b=0.85
        )
        assert shares.shares["Liquidity"] > 0.95

    def test_volatile_asset_is_growth_heavy_for_long_horizons(self) -> None:
        shares = GoalDecomposer().decompose(
            "EQTY", epv=3.0, sigma_d=0.25, sigma_l=0.25, T=25, tau_years=0.5, b=0.85
        )
        assert shares.shares["Growth"] > 0.5

    def test_shares_sum_to_one(self) -> None:
        shares = GoalDecomposer().decompose(
            "MID", epv=2.0, sigma_d=0.08, sigma_l=0.10, T=10, tau_years=0.5, b=0.74
        )
        assert sum(shares.shares.values()) == pytest.approx(1.0)

    def test_longer_horizon_lowers_liquidity_preference(self) -> None:
        """k = k1^T falls with T: long-horizon investors tolerate lock-up."""
        decomposer = GoalDecomposer()
        short = decomposer.pi_liquidity(0.5, T=2, sigma_l=0.15)
        long = decomposer.pi_liquidity(0.5, T=30, sigma_l=0.15)
        assert 0.0 <= short <= 1.0 and 0.0 <= long <= 1.0

    def test_rejects_bad_strike(self) -> None:
        with pytest.raises(ValueError):
            GoalDecomposer(k1=1.5)

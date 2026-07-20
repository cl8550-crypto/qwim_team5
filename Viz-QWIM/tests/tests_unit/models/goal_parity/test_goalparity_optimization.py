"""Unit tests for StrategicOptimizer (Step 5, Golts & Jones 2023 p.10-12).

Uses a small synthetic universe with archetypal goal profiles so results are
deterministic and independent of market data.
"""

from __future__ import annotations

import numpy as np
import pytest

from src.models.goal_parity import StrategicOptimizer, tilted_theta
from src.models.goal_parity.utils_goal_parity import GOALS, THETA_BALANCED


TICKERS = ["CASH", "BOND", "TIPS", "EQTY"]
EXP_RETURNS = np.array([0.02, 0.04, 0.03, 0.09])
SHARES = {
    "CASH": {"Liquidity": 0.95, "Income": 0.03, "Preservation": 0.01, "Growth": 0.01},
    "BOND": {"Liquidity": 0.30, "Income": 0.55, "Preservation": 0.10, "Growth": 0.05},
    "TIPS": {"Liquidity": 0.10, "Income": 0.25, "Preservation": 0.55, "Growth": 0.10},
    "EQTY": {"Liquidity": 0.02, "Income": 0.08, "Preservation": 0.10, "Growth": 0.80},
}


class Test_Balanced:
    def test_weights_valid_simplex(self) -> None:
        result = StrategicOptimizer().solve_balanced(TICKERS, EXP_RETURNS, SHARES)
        assert result.success
        assert result.weights.sum() == pytest.approx(1.0)
        assert (result.weights >= -1e-9).all()

    def test_goal_powers_near_25_each(self) -> None:
        result = StrategicOptimizer().solve_balanced(TICKERS, EXP_RETURNS, SHARES)
        for goal in GOALS:
            assert result.goal_powers[goal] == pytest.approx(0.25, abs=0.05)

    def test_custom_theta_respected(self) -> None:
        theta = {"Liquidity": 0.40, "Income": 0.30, "Preservation": 0.15, "Growth": 0.15}
        result = StrategicOptimizer().solve_balanced(TICKERS, EXP_RETURNS, SHARES, theta=theta)
        assert result.goal_powers["Liquidity"] > result.goal_powers["Growth"]

    def test_w_max_cap_enforced(self) -> None:
        result = StrategicOptimizer(w_max=0.30).solve_balanced(TICKERS, EXP_RETURNS, SHARES)
        assert (result.weights <= 0.30 + 1e-8).all()


class Test_Tilted_Theta:
    """Golts & Jones (2023) p.12: the tilt is a goal-target vector, not a
    separate constrained objective."""

    def test_maximal_tilt_is_100_0_0_0(self) -> None:
        theta = tilted_theta("Growth", tilt_strength=1.0)
        assert theta == {"Liquidity": 0.0, "Income": 0.0, "Preservation": 0.0, "Growth": 1.0}

    def test_zero_strength_recovers_balanced(self) -> None:
        assert tilted_theta("Growth", tilt_strength=0.0) == THETA_BALANCED

    def test_moderate_tilt_is_between_balanced_and_maximal(self) -> None:
        """p.12: "a more moderate tilt (such as 50% growth) ... in between"."""
        theta = tilted_theta("Growth", tilt_strength=0.5)
        assert 0.25 < theta["Growth"] < 1.0
        assert 0.0 < theta["Liquidity"] < 0.25

    def test_rejects_unknown_goal(self) -> None:
        with pytest.raises(ValueError):
            tilted_theta("Revenue")

    def test_rejects_out_of_range_strength(self) -> None:
        with pytest.raises(ValueError):
            tilted_theta("Growth", tilt_strength=1.5)


class Test_Tilted:
    def test_tilt_raises_target_goal_power(self) -> None:
        optimizer = StrategicOptimizer()
        balanced = optimizer.solve_balanced(TICKERS, EXP_RETURNS, SHARES)
        tilted = optimizer.solve_tilted(TICKERS, EXP_RETURNS, SHARES, "Growth")
        assert tilted.success
        assert tilted.goal_powers["Growth"] > balanced.goal_powers["Growth"]

    def test_maximal_tilt_uses_100_percent_target(self) -> None:
        """Solving with the maximal tilt is equivalent to solve_balanced(theta=maximal)."""
        optimizer = StrategicOptimizer()
        via_tilted = optimizer.solve_tilted(TICKERS, EXP_RETURNS, SHARES, "Income")
        via_balanced = optimizer.solve_balanced(
            TICKERS, EXP_RETURNS, SHARES, theta=tilted_theta("Income", 1.0)
        )
        assert via_tilted.weights == pytest.approx(via_balanced.weights)

    def test_partial_tilt_lands_between_balanced_and_maximal(self) -> None:
        optimizer = StrategicOptimizer()
        balanced = optimizer.solve_balanced(TICKERS, EXP_RETURNS, SHARES)
        half = optimizer.solve_tilted(TICKERS, EXP_RETURNS, SHARES, "Growth", tilt_strength=0.5)
        full = optimizer.solve_tilted(TICKERS, EXP_RETURNS, SHARES, "Growth", tilt_strength=1.0)
        assert balanced.goal_powers["Growth"] <= half.goal_powers["Growth"] <= full.goal_powers["Growth"] + 1e-9

    def test_always_feasible_even_for_scarce_goal(self) -> None:
        """A soft quadratic penalty (not hard floors) can never be infeasible."""
        result = StrategicOptimizer().solve_tilted(TICKERS, EXP_RETURNS, SHARES, "Preservation")
        assert result.success

    def test_rejects_unknown_goal(self) -> None:
        with pytest.raises(ValueError):
            StrategicOptimizer().solve_tilted(TICKERS, EXP_RETURNS, SHARES, "Revenue")


class Test_Validation:
    def test_rejects_bad_constants(self) -> None:
        with pytest.raises(ValueError):
            StrategicOptimizer(c=0.0)
        with pytest.raises(ValueError):
            StrategicOptimizer(w_max=1.5)

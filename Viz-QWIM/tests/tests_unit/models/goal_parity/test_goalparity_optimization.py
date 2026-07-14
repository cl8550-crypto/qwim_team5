"""Unit tests for StrategicOptimizer (Step 5, Roadmap Sec 3.5).

Uses a small synthetic universe with archetypal goal profiles so results are
deterministic and independent of market data.
"""

from __future__ import annotations

import numpy as np
import pytest

from src.models.goal_parity import StrategicOptimizer
from src.models.goal_parity.utils_goal_parity import GOALS


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


class Test_Tilted:
    def test_tilt_raises_target_goal_power(self) -> None:
        optimizer = StrategicOptimizer()
        balanced = optimizer.solve_balanced(TICKERS, EXP_RETURNS, SHARES)
        tilted = optimizer.solve_tilted(TICKERS, EXP_RETURNS, SHARES, "Growth")
        assert tilted.success
        assert tilted.goal_powers["Growth"] > balanced.goal_powers["Growth"]

    def test_floors_hold_for_other_goals(self) -> None:
        result = StrategicOptimizer().solve_tilted(
            TICKERS, EXP_RETURNS, SHARES, "Growth",
            floors={"Liquidity": 0.10, "Income": 0.10, "Preservation": 0.05},
        )
        assert result.success
        assert result.goal_powers["Liquidity"] >= 0.10 - 1e-6
        assert result.goal_powers["Income"] >= 0.10 - 1e-6

    def test_infeasible_floor_capped_to_capacity(self) -> None:
        """A floor above the goal's achievable capacity must not break the solve."""
        result = StrategicOptimizer().solve_tilted(
            TICKERS, EXP_RETURNS, SHARES, "Growth", floors={"Preservation": 0.90}
        )
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

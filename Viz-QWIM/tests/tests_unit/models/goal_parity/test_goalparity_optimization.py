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

    def test_rejects_bad_capped_weight(self) -> None:
        with pytest.raises(ValueError):
            StrategicOptimizer(capped_weight_for_low_return=-0.1)
        with pytest.raises(ValueError):
            StrategicOptimizer(w_max=0.35, capped_weight_for_low_return=0.5)


# A VIXY-like asset: near-pure Growth classification (both option triggers
# fire near-certainty) but a structurally negative expected return from
# decay -- the exact pathology this cap was built to prevent.
_DECAY_TICKERS = [*TICKERS, "DECAY"]
_DECAY_EXP_RETURNS = np.append(EXP_RETURNS, -0.50)
_DECAY_SHARES = {
    **SHARES,
    "DECAY": {"Liquidity": 0.00, "Income": 0.01, "Preservation": 0.01, "Growth": 0.98},
}


class Test_Low_Return_Weight_Cap:
    def test_maximal_tilt_caps_negative_return_asset(self) -> None:
        optimizer = StrategicOptimizer()  # default cap: 2%
        tilted = optimizer.solve_tilted(_DECAY_TICKERS, _DECAY_EXP_RETURNS, _DECAY_SHARES, "Growth")
        decay_weight = tilted.weights[_DECAY_TICKERS.index("DECAY")]
        assert decay_weight <= optimizer.capped_weight_for_low_return + 1e-8

    def test_capped_tilt_still_achieves_elevated_growth_power_and_positive_return(self) -> None:
        optimizer = StrategicOptimizer()
        balanced = optimizer.solve_balanced(_DECAY_TICKERS, _DECAY_EXP_RETURNS, _DECAY_SHARES)
        tilted = optimizer.solve_tilted(_DECAY_TICKERS, _DECAY_EXP_RETURNS, _DECAY_SHARES, "Growth")
        # In this 5-asset toy universe only EQTY (capped at w_max=0.35) can
        # carry the tilt once DECAY is capped, so Growth power is well above
        # the Balanced baseline but nowhere near the paper's own "maximal"
        # illustration -- the real 18-asset universe has more headroom.
        assert tilted.goal_powers["Growth"] > balanced.goal_powers["Growth"]
        assert tilted.expected_return > 0.0  # capping DECAY should not tank the return

    def test_positive_return_asset_with_same_goal_profile_is_not_capped(self) -> None:
        """Only the negative-return asset should be capped; EQTY (also
        Growth-heavy but a genuine +9% expected return) must not be."""
        optimizer = StrategicOptimizer()
        tilted = optimizer.solve_tilted(_DECAY_TICKERS, _DECAY_EXP_RETURNS, _DECAY_SHARES, "Growth")
        eqty_weight = tilted.weights[_DECAY_TICKERS.index("EQTY")]
        assert eqty_weight > optimizer.capped_weight_for_low_return

    def test_custom_cap_is_respected(self) -> None:
        optimizer = StrategicOptimizer(capped_weight_for_low_return=0.10)
        tilted = optimizer.solve_tilted(_DECAY_TICKERS, _DECAY_EXP_RETURNS, _DECAY_SHARES, "Growth")
        decay_weight = tilted.weights[_DECAY_TICKERS.index("DECAY")]
        assert decay_weight <= 0.10 + 1e-8

    def test_disabling_cap_via_low_threshold_restores_old_behavior(self) -> None:
        """A very negative threshold means no asset is ever capped, matching
        pre-fix behavior (regression guard for the opt-out path)."""
        optimizer = StrategicOptimizer(min_expected_return_for_full_weight=-999.0)
        tilted = optimizer.solve_tilted(_DECAY_TICKERS, _DECAY_EXP_RETURNS, _DECAY_SHARES, "Growth")
        decay_weight = tilted.weights[_DECAY_TICKERS.index("DECAY")]
        assert decay_weight > optimizer.capped_weight_for_low_return

    def test_balanced_mode_unaffected_when_decay_asset_not_preferred(self) -> None:
        """Confirms the cap is non-binding (does not distort results) in
        Balanced mode, where the decay asset was never going to be chosen
        anyway -- matches the real 18-asset universe's observed behavior."""
        optimizer = StrategicOptimizer()
        uncapped = StrategicOptimizer(min_expected_return_for_full_weight=-999.0)
        balanced_capped = optimizer.solve_balanced(_DECAY_TICKERS, _DECAY_EXP_RETURNS, _DECAY_SHARES)
        balanced_uncapped = uncapped.solve_balanced(_DECAY_TICKERS, _DECAY_EXP_RETURNS, _DECAY_SHARES)
        assert balanced_capped.weights == pytest.approx(balanced_uncapped.weights, abs=1e-6)

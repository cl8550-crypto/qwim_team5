"""Unit tests for SignalPriorityRebalancer (Step 6, Roadmap Sec 3.6, 4.2)."""

from __future__ import annotations

import numpy as np
import pytest

from src.models.goal_parity import SignalPriorityRebalancer
from src.models.goal_parity.utils_goal_parity import THETA_BALANCED


TICKERS = ["CASH", "BOND", "TIPS", "EQTY"]
SHARES = {
    "CASH": {"Liquidity": 0.95, "Income": 0.03, "Preservation": 0.01, "Growth": 0.01},
    "BOND": {"Liquidity": 0.30, "Income": 0.55, "Preservation": 0.10, "Growth": 0.05},
    "TIPS": {"Liquidity": 0.10, "Income": 0.25, "Preservation": 0.55, "Growth": 0.10},
    "EQTY": {"Liquidity": 0.02, "Income": 0.08, "Preservation": 0.10, "Growth": 0.80},
}
BALANCED_W = np.array([0.25, 0.25, 0.25, 0.25])


class Test_No_Trade_Path:
    def test_within_eps_no_trade(self) -> None:
        rebalancer = SignalPriorityRebalancer(eps=0.5)
        result = rebalancer.rebalance(TICKERS, BALANCED_W, SHARES, THETA_BALANCED)
        assert not result.traded
        assert result.turnover == 0.0
        assert np.allclose(result.weights, BALANCED_W)

    def test_goal_powers_sum_to_one(self) -> None:
        rebalancer = SignalPriorityRebalancer()
        share_matrix = np.array(
            [[SHARES[t][g] for g in ("Liquidity", "Income", "Preservation", "Growth")] for t in TICKERS]
        )
        powers = rebalancer.goal_powers(BALANCED_W, share_matrix)
        assert sum(powers.values()) == pytest.approx(1.0)


class Test_Trading_Path:
    def test_extreme_drift_triggers_trades_toward_target(self) -> None:
        drifted = np.array([0.01, 0.01, 0.01, 0.97])  # all-in equities
        rebalancer = SignalPriorityRebalancer(eps=0.02, turnover_budget=0.50)
        result = rebalancer.rebalance(TICKERS, drifted, SHARES, THETA_BALANCED)
        assert result.traded
        gap_before = max(abs(THETA_BALANCED[g] - v) for g, v in result.goal_powers_before.items())
        gap_after = max(abs(THETA_BALANCED[g] - v) for g, v in result.goal_powers_after.items())
        assert gap_after < gap_before
        assert all(t.sell == "EQTY" or t.buy != "EQTY" for t in result.trades)

    def test_turnover_budget_respected(self) -> None:
        drifted = np.array([0.01, 0.01, 0.01, 0.97])
        rebalancer = SignalPriorityRebalancer(turnover_budget=0.10, trade_size=0.01)
        result = rebalancer.rebalance(TICKERS, drifted, SHARES, THETA_BALANCED)
        assert result.turnover <= 0.10 + 1e-9

    def test_weights_stay_on_simplex(self) -> None:
        drifted = np.array([0.05, 0.05, 0.05, 0.85])
        result = SignalPriorityRebalancer().rebalance(TICKERS, drifted, SHARES, THETA_BALANCED)
        assert result.weights.sum() == pytest.approx(1.0)
        assert (result.weights >= -1e-9).all()

    def test_cash_floor_respected(self) -> None:
        start = np.array([0.05, 0.35, 0.30, 0.30])
        rebalancer = SignalPriorityRebalancer(cash_min=0.05, turnover_budget=0.50)
        result = rebalancer.rebalance(
            TICKERS, start, SHARES, THETA_BALANCED, cash_tickers=["CASH"]
        )
        cash_weight = result.weights[TICKERS.index("CASH")]
        assert cash_weight >= 0.05 - 1e-9

    def test_high_cost_threshold_blocks_marginal_trades(self) -> None:
        mildly_drifted = np.array([0.22, 0.28, 0.22, 0.28])
        strict = SignalPriorityRebalancer(eps=0.0, eta_cost_benefit=1e9)
        result = strict.rebalance(TICKERS, mildly_drifted, SHARES, THETA_BALANCED)
        assert not result.traded

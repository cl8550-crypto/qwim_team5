"""StrategicOptimizer: Step 5 — strategic portfolio optimization (Roadmap Sec 3.5).

Goal Parity Balanced (paper's objective, transcribed in the Roadmap):

    max_w  a·w  -  (1/2c) * sum_k (P_k(w) - theta_k)^2  -  (1/2kappa) * w·w
    s.t.   sum(w) = 1,  0 <= w_i <= w_max

where P_k(w) = sum_i w_i * s_{k,i} are portfolio goal powers built from the
per-asset goal shares s (Step 4). Solved with SciPy SLSQP (the Roadmap's
lighter recommended alternative to cvxpy).

Goal Tilted (Roadmap's constrained variant, flagged [verify] against
Golts & Jones 2023): maximize the tilted goal's power (plus the return and
diversification terms) subject to hard floors on the other three goals.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize

from src.models.goal_parity.utils_goal_parity import GOALS, THETA_BALANCED


@dataclass(frozen=True)
class OptimizationResult:
    tickers: list[str]
    weights: np.ndarray
    goal_powers: dict[str, float]
    expected_return: float
    mode: str
    success: bool
    message: str


def _goal_share_matrix(goal_shares_by_ticker: dict[str, dict[str, float]], tickers: list[str]) -> np.ndarray:
    """(n_assets x 4) matrix S with S[i, k] = asset i's share of goal k."""
    return np.array([[goal_shares_by_ticker[t][g] for g in GOALS] for t in tickers])


class StrategicOptimizer:
    """Implements Sec 3.5 over Step 4 goal shares and Step 2 expected returns."""

    def __init__(
        self,
        c: float = 0.005,
        kappa_diversification: float = 10.0,
        w_max: float = 0.35,
    ) -> None:
        if c <= 0 or kappa_diversification <= 0:
            raise ValueError("tuning constants c and kappa must be positive")
        if not 0 < w_max <= 1:
            raise ValueError(f"w_max must be in (0, 1], got {w_max}")
        self.c = c
        self.kappa_diversification = kappa_diversification
        self.w_max = w_max

    # ------------------------------------------------------------------
    def _solve(
        self,
        tickers: list[str],
        exp_returns: np.ndarray,
        share_matrix: np.ndarray,
        objective,
        constraints: list[dict],
        mode: str,
    ) -> OptimizationResult:
        n = len(tickers)
        w0 = np.full(n, 1.0 / n)
        bounds = [(0.0, self.w_max)] * n
        base_constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}, *constraints]
        result = minimize(
            objective,
            w0,
            method="SLSQP",
            bounds=bounds,
            constraints=base_constraints,
            options={"maxiter": 500, "ftol": 1e-10},
        )
        weights = np.clip(result.x, 0.0, self.w_max)
        weights = weights / weights.sum()
        powers = share_matrix.T @ weights
        return OptimizationResult(
            tickers=tickers,
            weights=weights,
            goal_powers=dict(zip(GOALS, powers.tolist())),
            expected_return=float(exp_returns @ weights),
            mode=mode,
            success=bool(result.success),
            message=str(result.message),
        )

    # ------------------------------------------------------------------
    def solve_balanced(
        self,
        tickers: list[str],
        exp_returns: np.ndarray,
        goal_shares_by_ticker: dict[str, dict[str, float]],
        theta: dict[str, float] | None = None,
    ) -> OptimizationResult:
        """Goal Parity Balanced: theta = 25% each unless overridden (Sec 3.5)."""
        theta_vec = np.array([(theta or THETA_BALANCED)[g] for g in GOALS])
        S = _goal_share_matrix(goal_shares_by_ticker, tickers)

        def objective(w: np.ndarray) -> float:
            powers = S.T @ w
            tracking = np.sum((powers - theta_vec) ** 2)
            return -(
                exp_returns @ w
                - tracking / (2.0 * self.c)
                - (w @ w) / (2.0 * self.kappa_diversification)
            )

        return self._solve(tickers, exp_returns, S, objective, [], mode="balanced")

    # ------------------------------------------------------------------
    def solve_tilted(
        self,
        tickers: list[str],
        exp_returns: np.ndarray,
        goal_shares_by_ticker: dict[str, dict[str, float]],
        tilt_goal: str,
        floors: dict[str, float] | None = None,
    ) -> OptimizationResult:
        """Goal Tilted: maximize the prioritized goal with floors on the rest.

        [Verify against PDF once Golts & Jones (2023) is available]: whether
        their "Goal Tilted" uses exactly this floor-constraint formulation.
        """
        if tilt_goal not in GOALS:
            raise ValueError(f"tilt_goal must be one of {GOALS}, got {tilt_goal!r}")
        S = _goal_share_matrix(goal_shares_by_ticker, tickers)
        tilt_idx = GOALS.index(tilt_goal)
        default_floor = 0.10
        # Feasibility-aware floors: a goal's maximum achievable portfolio power
        # under the w_max cap is the greedy fill of the highest-share assets;
        # cap each requested floor at 80% of that so scarce goals (often
        # Preservation for tight loss barriers) cannot make the QP infeasible.
        floor_map: dict[str, float] = {}
        for g in GOALS:
            if g == tilt_goal:
                continue
            col = np.sort(S[:, GOALS.index(g)])[::-1]
            capacity, remaining = 0.0, 1.0
            for share in col:
                take = min(self.w_max, remaining)
                capacity += share * take
                remaining -= take
                if remaining <= 0:
                    break
            requested = (floors or {}).get(g, default_floor)
            floor_map[g] = min(requested, 0.8 * capacity)

        constraints = [
            {
                "type": "ineq",
                "fun": (lambda w, k=GOALS.index(g), f=f: float(S[:, k] @ w - f)),
            }
            for g, f in floor_map.items()
        ]

        def objective(w: np.ndarray) -> float:
            return -(
                S[:, tilt_idx] @ w
                + 0.1 * (exp_returns @ w)
                - (w @ w) / (2.0 * self.kappa_diversification)
            )

        return self._solve(
            tickers, exp_returns, S, objective, constraints, mode=f"tilted:{tilt_goal}"
        )

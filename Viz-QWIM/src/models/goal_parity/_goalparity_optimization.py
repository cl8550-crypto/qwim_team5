"""StrategicOptimizer: Step 5 — strategic portfolio optimization (Roadmap Sec 3.5).

Goal Parity Balanced (Golts & Jones 2023, schematic objective on p.10-11):

    max_w  a·w  -  (1/2c) * sum_k (P_k(w) - theta_k)^2  -  (1/2kappa) * w·w
    s.t.   sum(w) = 1,  0 <= w_i <= w_max

where P_k(w) = sum_i w_i * s_{k,i} are portfolio goal powers built from the
per-asset goal shares s (Step 4), and D(Port vs Goals) = sum_k (P_k-theta_k)^2
is the paper's "deviation from goal targets" term. Solved with SciPy SLSQP
(the Roadmap's lighter recommended alternative to cvxpy).

Goal Tilted (confirmed against Golts & Jones 2023, p.12 "Goal-Tilted
Portfolios"): NOT a separately-constrained objective. It is the exact same
objective above, with the goal-target vector theta upweighted toward one
goal instead of 25% each -- e.g. a full Growth tilt sets
theta = (Liquidity=0, Income=0, Preservation=0, Growth=100%). The paper's own
"maximal" tilts use 100%/0% targets; it also notes an investor may choose "a
more moderate tilt (such as 50% growth)," interpolating between Balanced and
the full tilt -- implemented here as ``tilt_strength`` in [0, 1].

Low-return eligibility cap: at theta -> 0%/100% (a maximal tilt), the
quadratic tracking penalty's coefficient 1/(2c) is ~100x the return term's
linear coefficient, so the optimizer effectively maximizes goal-share
*classification* almost irrespective of a·w. In a universe containing a
structurally negative-carry instrument that happens to score at the extreme
corner of the tilted goal (e.g. VIX futures scoring near-pure Growth via
Pi_default*Pi_liquidity~1, despite realized returns around -80%/year from
futures-roll decay), this can concentrate a large weight in an asset that
actively destroys the tilted portfolio's expected return. Rather than
special-case Growth or exclude assets from the universe outright, any
asset whose expected return falls below ``min_expected_return_for_full_weight``
has its own weight bound tightened to ``capped_weight_for_low_return``
(default 2%) instead of ``w_max`` -- letting the optimizer still use it in
small size (e.g. for genuine diversification/hedging value) without letting
goal-classification alone justify a large allocation to a money-losing
asset. This does not change Balanced-mode results in the team's own
18-asset universe (no asset there is both goal-scarce and negative-return
enough to bind), only the maximal-tilt pathology it was built to fix.
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


def tilted_theta(tilt_goal: str, tilt_strength: float = 1.0) -> dict[str, float]:
    """Goal-target vector for a Goal Tilted portfolio (Golts & Jones 2023, p.12).

    tilt_strength=1.0 reproduces the paper's "maximal" tilt exactly (100% on
    tilt_goal, 0% on the rest); tilt_strength=0.0 recovers Goal Parity
    Balanced (25% each). Intermediate values interpolate linearly, matching
    the paper's note that a "more moderate tilt (such as 50% growth)" falls
    "in between the Goal Parity Balanced, and the full 100%-tilt portfolios."
    """
    if tilt_goal not in GOALS:
        raise ValueError(f"tilt_goal must be one of {GOALS}, got {tilt_goal!r}")
    if not 0.0 <= tilt_strength <= 1.0:
        raise ValueError(f"tilt_strength must be in [0, 1], got {tilt_strength}")
    maximal = {g: (1.0 if g == tilt_goal else 0.0) for g in GOALS}
    return {
        g: (1.0 - tilt_strength) * THETA_BALANCED[g] + tilt_strength * maximal[g] for g in GOALS
    }


class StrategicOptimizer:
    """Implements p.10-12 over Step 4 goal shares and Step 2 expected returns."""

    def __init__(
        self,
        c: float = 0.005,
        kappa_diversification: float = 10.0,
        w_max: float = 0.35,
        min_expected_return_for_full_weight: float = 0.0,
        capped_weight_for_low_return: float = 0.02,
    ) -> None:
        if c <= 0 or kappa_diversification <= 0:
            raise ValueError("tuning constants c and kappa must be positive")
        if not 0 < w_max <= 1:
            raise ValueError(f"w_max must be in (0, 1], got {w_max}")
        if not 0 <= capped_weight_for_low_return <= w_max:
            raise ValueError(
                f"capped_weight_for_low_return must be in [0, w_max={w_max}], "
                f"got {capped_weight_for_low_return}",
            )
        self.c = c
        self.kappa_diversification = kappa_diversification
        self.w_max = w_max
        self.min_expected_return_for_full_weight = min_expected_return_for_full_weight
        self.capped_weight_for_low_return = capped_weight_for_low_return

    # ------------------------------------------------------------------
    def _solve_for_theta(
        self,
        tickers: list[str],
        exp_returns: np.ndarray,
        goal_shares_by_ticker: dict[str, dict[str, float]],
        theta: dict[str, float],
        mode: str,
    ) -> OptimizationResult:
        """Core solve: max a.w - D(Port vs Goals)/2c - w.w/2kappa, s.t. sum(w)=1."""
        S = _goal_share_matrix(goal_shares_by_ticker, tickers)
        theta_vec = np.array([theta[g] for g in GOALS])
        n = len(tickers)

        def objective(w: np.ndarray) -> float:
            powers = S.T @ w
            tracking = np.sum((powers - theta_vec) ** 2)
            return -(
                exp_returns @ w
                - tracking / (2.0 * self.c)
                - (w @ w) / (2.0 * self.kappa_diversification)
            )

        w0 = np.full(n, 1.0 / n)
        upper_bounds = np.where(
            exp_returns < self.min_expected_return_for_full_weight,
            self.capped_weight_for_low_return,
            self.w_max,
        )
        # w0 must itself respect the tightened bounds, or SLSQP starts infeasible.
        w0 = np.minimum(w0, upper_bounds)
        w0 = w0 / w0.sum()
        bounds = [(0.0, float(ub)) for ub in upper_bounds]
        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
        result = minimize(
            objective,
            w0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 500, "ftol": 1e-10},
        )
        weights = np.clip(result.x, 0.0, upper_bounds)
        weights = weights / weights.sum()
        powers = S.T @ weights
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
        """Goal Parity Balanced: theta = 25% each unless overridden (p.11)."""
        return self._solve_for_theta(
            tickers, exp_returns, goal_shares_by_ticker, theta or THETA_BALANCED, mode="balanced"
        )

    # ------------------------------------------------------------------
    def solve_tilted(
        self,
        tickers: list[str],
        exp_returns: np.ndarray,
        goal_shares_by_ticker: dict[str, dict[str, float]],
        tilt_goal: str,
        tilt_strength: float = 1.0,
    ) -> OptimizationResult:
        """Goal Tilted (Golts & Jones 2023, p.12): same objective as Balanced,
        with theta upweighted toward tilt_goal instead of 25% each."""
        theta = tilted_theta(tilt_goal, tilt_strength)
        return self._solve_for_theta(
            tickers,
            exp_returns,
            goal_shares_by_ticker,
            theta,
            mode=f"tilted:{tilt_goal}@{tilt_strength:.0%}",
        )

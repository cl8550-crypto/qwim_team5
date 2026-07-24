"""CalibrationSuite: Golts & Jones (2023) Appendix A gamma0 calibration, plus
a generic walk-forward evaluation harness for the remaining tuning constants.

gamma0 = gamma_tail * rho^3 is the paper's fitted tail-scaling constant
(Appendix A); the paper reports using a single gamma0 = 1.6 fitted across
their whole asset universe rather than per-asset. fit_gamma0_for_universe
mirrors that: pool every selected asset's daily returns and fit one shared
constant, which is what the dashboard pipeline now uses in place of the
hardcoded default (see _tab_goal_parity_pipeline.calibrated_volatility_adjuster).

Grid searches for the remaining tuning constants (c, kappa_diversification,
rebalancing eps/eta) are not yet wired into the dashboard -- walk_forward is
provided as the harness for that future work, deliberately left as a
documented gap rather than guessed at (see Sec 5 of the Technical Roadmap).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np


@dataclass(frozen=True)
class WalkForwardFold:
    train: np.ndarray
    test: np.ndarray
    score: float


class CalibrationSuite:
    """Sec 5 calibration procedures over daily log-return arrays."""

    @staticmethod
    def tail_variance_fraction(returns: np.ndarray, z: float = 2.0) -> float:
        """Fraction of total variance contributed by |r - mean| > z*sigma tail
        observations (the paper suggests this is often >~25%)."""
        r = np.asarray(returns, dtype=float)
        r = r[np.isfinite(r)]
        if r.size < 20:
            return 0.25
        demeaned = r - r.mean()
        variance = float(np.sum(demeaned**2))
        if variance <= 0:
            return 0.25
        tail_mask = np.abs(demeaned) > z * r.std(ddof=1)
        return float(np.sum(demeaned[tail_mask] ** 2) / variance)

    @classmethod
    def fit_gamma0(cls, returns: np.ndarray, z: float = 2.0) -> float:
        """gamma0 = 1 / (2 * tail fraction), floored at 1.0 (Appendix A).

        A 25% tail fraction recovers the paper's own gamma0 = 1.6 (approx.,
        since 1/(2*0.3125) = 1.6); lighter/heavier tails than that shift
        gamma0 down/up accordingly (fatter tails -> more skew sensitivity).
        """
        fraction = max(1e-3, cls.tail_variance_fraction(returns, z=z))
        return max(1.0, 1.0 / (2.0 * fraction))

    @classmethod
    def fit_gamma0_for_universe(
        cls, returns_by_ticker: dict[str, np.ndarray], z: float = 2.0) -> float:
        """Pool every asset's returns and fit one shared gamma0 (Appendix A:
        the paper fits a single gamma0 across its whole universe, not one
        per asset).

        Each series is standardized (its own mean subtracted, divided by its
        own std) before pooling. Without this, an asset with much larger
        absolute volatility than the rest of the universe (e.g. VIX futures
        at ~65% annualized vol vs. T-bills at ~0.5%) dominates the pooled
        variance and the fitted gamma0 collapses to its floor regardless of
        the other assets' actual tail behavior -- standardizing first means
        every asset contributes to the *shape* (tail-heaviness) measurement
        in proportion to its own distribution, not its absolute scale.
        """
        standardized: list[np.ndarray] = []
        for r in returns_by_ticker.values():
            arr = np.asarray(r, dtype=float)
            arr = arr[np.isfinite(arr)]
            if arr.size < 20:
                continue
            std = arr.std(ddof=1)
            if std > 0:
                standardized.append((arr - arr.mean()) / std)
        if not standardized:
            return 1.0
        pooled = np.concatenate(standardized)
        return cls.fit_gamma0(pooled, z=z)

    # ------------------------------------------------------------------
    @staticmethod
    def walk_forward(
        data: np.ndarray,
        evaluate: Callable[[np.ndarray, np.ndarray], float],
        n_folds: int = 4,
    ) -> list[WalkForwardFold]:
        """Rolling-window calibration: train on a trailing window, score the
        following block (Sec 5 validation protocol). ``evaluate(train, test)``
        returns the fold's out-of-sample score (e.g. goal-power tracking error)."""
        d = np.asarray(data)
        if n_folds < 1 or d.shape[0] < (n_folds + 1) * 2:
            raise ValueError("not enough observations for the requested folds")
        block = d.shape[0] // (n_folds + 1)
        folds: list[WalkForwardFold] = []
        for k in range(1, n_folds + 1):
            train = d[: k * block]
            test = d[k * block : (k + 1) * block]
            folds.append(WalkForwardFold(train=train, test=test, score=float(evaluate(train, test))))
        return folds

"""CalibrationSuite: Roadmap Sec 5 — calibration utilities.

Implements the tail-scaling constant fit for kappa (Sec 3.3) and a simple
walk-forward evaluation harness. Grid searches for (c, kappa_div, eps, eta)
are exposed as a generic walk-forward runner so they can be layered on later
without changing the pipeline modules.
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
    def fit_kappa(cls, returns: np.ndarray, z: float = 2.0) -> float:
        """kappa = 1 / (2 * tail fraction), floored at 1.0 (Sec 3.3, Sec 5).

        A 25% tail fraction recovers the module default kappa = 2.0.
        """
        fraction = max(1e-3, cls.tail_variance_fraction(returns, z=z))
        return max(1.0, 1.0 / (2.0 * fraction))

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

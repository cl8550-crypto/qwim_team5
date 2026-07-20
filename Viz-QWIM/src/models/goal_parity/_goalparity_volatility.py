"""VolatilityAdjuster: Step 3 — skewness-adjusted volatilities (Roadmap Sec 3.3).

Confirmed against Golts & Jones (2023), Appendix A ("Skewness and Horizon-Driven
Liquidity Preference"):
    sigma_D = sigma * exp(-gamma / (2*gamma0))   ("defaultility")
    sigma_L = sigma * exp(+gamma / (2*gamma0))   ("liquitility")
Negatively skewed assets get sigma_D adjusted up and sigma_L down; positively
skewed assets the opposite. gamma0 = gamma_tail * rho^3 is a fitted constant
related to the fat-tailed nature of returns; the paper uses gamma0 = 1.6
throughout (rho^2 >= ~25% tail-variance fraction is typical for fat-tailed
financial returns). CalibrationSuite.fit_kappa offers a data-driven alternative
to this fixed constant.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from src.models.goal_parity._goalparity_data import AssetStats


#: Golts & Jones (2023), Appendix A: "We use gamma0 = 1.6 in this article."
DEFAULT_GAMMA0: float = 1.6

#: Cap on |gamma/(2*gamma0)| so extreme sample skewness cannot explode vols.
_MAX_EXPONENT: float = 1.5


@dataclass(frozen=True)
class AdjustedVolatility:
    ticker: str
    sigma: float
    gamma: float
    sigma_d: float  # "defaultility" — feeds pi_default (Sec 3.4)
    sigma_l: float  # "liquitility" — feeds pi_liquidity (Sec 3.4)


class VolatilityAdjuster:
    """Implements Appendix A for AssetStats produced by the data layer."""

    def __init__(self, gamma0: float = DEFAULT_GAMMA0) -> None:
        if gamma0 <= 0:
            raise ValueError(f"gamma0 must be positive, got {gamma0}")
        self.gamma0 = gamma0

    def adjust(self, asset: AssetStats) -> AdjustedVolatility:
        exponent = asset.gamma / (2.0 * self.gamma0)
        exponent = max(-_MAX_EXPONENT, min(_MAX_EXPONENT, exponent))
        return AdjustedVolatility(
            ticker=asset.ticker,
            sigma=asset.sigma,
            gamma=asset.gamma,
            sigma_d=asset.sigma * math.exp(-exponent),
            sigma_l=asset.sigma * math.exp(+exponent),
        )

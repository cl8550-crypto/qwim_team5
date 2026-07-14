"""VolatilityAdjuster: Step 3 — skewness-adjusted volatilities (Roadmap Sec 3.3).

Appendix B normalization of Cron & Golts (2022):
    sigma_L = sigma * exp(+gamma / (2*kappa))   ("liquitility")
    sigma_D = sigma * exp(-gamma / (2*kappa))   ("defaultility")
Negatively skewed assets get sigma_D adjusted up and sigma_L down; positively
skewed assets the opposite. kappa is the fitted tail-scaling constant
(calibrated in _goalparity_calibration; see also configs/goal_parity_config.yaml).

[Verify against PDF]: the Appendix B derivation extracted with corrupted
symbols in the source; this module implements the clean final normalization
the Roadmap records.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from src.models.goal_parity._goalparity_data import AssetStats


#: Default tail-scaling constant; paper notes heavy-tail variance fractions
#: are often >~25%, giving kappa = 1/(2*0.25) = 2.0 (see CalibrationSuite).
DEFAULT_KAPPA: float = 2.0

#: Cap on |gamma/(2*kappa)| so extreme sample skewness cannot explode vols.
_MAX_EXPONENT: float = 1.5


@dataclass(frozen=True)
class AdjustedVolatility:
    ticker: str
    sigma: float
    gamma: float
    sigma_d: float  # "defaultility" — feeds pi_default (Sec 3.4)
    sigma_l: float  # "liquitility" — feeds pi_liquidity (Sec 3.4)


class VolatilityAdjuster:
    """Implements Sec 3.3 for AssetStats produced by the data layer."""

    def __init__(self, kappa: float = DEFAULT_KAPPA) -> None:
        if kappa <= 0:
            raise ValueError(f"kappa must be positive, got {kappa}")
        self.kappa = kappa

    def adjust(self, asset: AssetStats) -> AdjustedVolatility:
        exponent = asset.gamma / (2.0 * self.kappa)
        exponent = max(-_MAX_EXPONENT, min(_MAX_EXPONENT, exponent))
        return AdjustedVolatility(
            ticker=asset.ticker,
            sigma=asset.sigma,
            gamma=asset.gamma,
            sigma_d=asset.sigma * math.exp(-exponent),
            sigma_l=asset.sigma * math.exp(+exponent),
        )

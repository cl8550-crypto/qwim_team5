"""CashFlowEstimator: Step 2 — EPV and the RC/RN split (Roadmap Sec 3.2).

Uses the paper's arithmetic-return convention:
    EPV(RC_t, T)/I = 1 + a_RC * T      EPV(RN_t, T)/I = a_RN * T
where a_RC / a_RN are the annualized returns from "return OF capital" (final
sale/maturity) and "return ON capital" (coupons, dividends, carry). Because
the cleaned prices are total-return adjusted, the split uses the per-asset
income fraction from the data layer rather than separate cash-flow series.
WAM places the RC leg at T and spreads the RN leg evenly (mean time T/2).
"""

from __future__ import annotations

from dataclasses import dataclass

from src.models.goal_parity._goalparity_data import AssetStats


@dataclass(frozen=True)
class CashFlowProfile:
    """Sec 3.2 outputs for one asset at horizon T (per $1 invested)."""

    ticker: str
    a_rc: float  # annualized return-of-capital component
    a_rn: float  # annualized return-on-capital component
    epv_rc: float  # 1 + a_RC * T
    epv_rn: float  # a_RN * T
    wam: float  # expected weighted-average maturity

    @property
    def epv(self) -> float:
        """EPV(CF_t, T) = EPV(RC_t, T) + EPV(RN_t, T) (Sec 3.2)."""
        return self.epv_rc + self.epv_rn


class CashFlowEstimator:
    """Implements Sec 3.2 for AssetStats produced by the data layer."""

    def profile(self, asset: AssetStats, T: float) -> CashFlowProfile:
        if T <= 0:
            raise ValueError(f"Horizon T must be positive, got {T}")
        a_rn = asset.income_fraction * asset.a
        a_rc = asset.a - a_rn
        epv_rc = 1.0 + a_rc * T
        epv_rn = a_rn * T
        # The paper's linear convention EPV/I = 1 + a*T can go negative for
        # strongly negative-carry assets (e.g. VIXY) at long horizons; floor
        # the RC leg so total EPV stays (barely) positive rather than letting
        # a nonsensical negative EPV corrupt the Step 4 goal split.
        epv_rc = max(epv_rc, 0.01 - epv_rn)
        epv = epv_rc + epv_rn
        # RC recovered at T; RN spread evenly over (0, T] -> mean time T/2.
        wam = (epv_rc * T + epv_rn * (T / 2.0)) / epv if epv > 0 else T
        return CashFlowProfile(
            ticker=asset.ticker, a_rc=a_rc, a_rn=a_rn, epv_rc=epv_rc, epv_rn=epv_rn, wam=wam
        )

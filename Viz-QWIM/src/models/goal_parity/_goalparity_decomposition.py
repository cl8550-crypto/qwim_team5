"""GoalDecomposer: Step 4 — option-based 4x4 EPV split (Roadmap Sec 3.4).

Both option "prices" are implemented as first-passage (barrier-hit)
probabilities of a driftless geometric Brownian motion, which lie in [0, 1]
and act as the paper's two independent triggers:

    pi_default(T, sigma_D, b)      — probability of breaching the investor's
                                     "substantial loss" barrier b within T
                                     (Golts & Kritzman 2010, formula 3)
    pi_liquidity(tau, T, sigma_L)  — horizon-driven liquidity preference
                                     (Roadmap Sec 3.4 / Appendix B variant):
                                     first-passage against the compounding
                                     strike k = k1^T, so short-horizon
                                     investors demand near-full liquidity and
                                     long-horizon investors tolerate locking
                                     up roughly half the portfolio
                                     (Golts & Kritzman 2010, formula 5)

The 2x2 truth-table split (the literal origin of the "4x4" name):
    EPV_G = pi_d *    pi_l  * EPV      EPV_I = pi_d * (1-pi_l) * EPV
    EPV_P = (1-pi_d)* pi_l  * EPV      EPV_L = (1-pi_d)*(1-pi_l)* EPV
which sums back to EPV by construction.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from scipy.stats import norm

from src.models.goal_parity.utils_goal_parity import DEFAULT_LIQUIDITY_STRIKE_K1, GOALS


def first_passage_probability(T: float, sigma: float, barrier: float) -> float:
    """P(min over [0,T] of a driftless GBM falls to ``barrier``), barrier in (0,1].

    Standard reflection formula with log-space drift mu = -sigma^2/2:
        P = Phi((ln b - mu T)/(sigma sqrt(T))) + b^(2 mu / sigma^2) *
            Phi((ln b + mu T)/(sigma sqrt(T)))
    """
    if barrier >= 1.0:
        return 1.0
    if barrier <= 0.0 or T <= 0.0 or sigma <= 0.0:
        return 0.0
    log_b = math.log(barrier)
    mu = -0.5 * sigma * sigma
    denom = sigma * math.sqrt(T)
    term1 = norm.cdf((log_b - mu * T) / denom)
    term2 = math.exp(2.0 * mu * log_b / (sigma * sigma)) * norm.cdf((log_b + mu * T) / denom)
    return float(min(1.0, max(0.0, term1 + term2)))


@dataclass(frozen=True)
class GoalShares:
    """Per-asset goal decomposition: EPV levels and normalized shares."""

    ticker: str
    pi_default: float
    pi_liquidity: float
    epv: float
    epv_by_goal: dict[str, float]

    @property
    def shares(self) -> dict[str, float]:
        """Goal shares s_k = EPV_k / EPV, summing to 1 (Sec 3.6 goal power input)."""
        total = sum(self.epv_by_goal.values())
        if total <= 0:
            return {goal: 0.25 for goal in GOALS}
        return {goal: value / total for goal, value in self.epv_by_goal.items()}


class GoalDecomposer:
    """Implements Sec 3.4 given the Step 2/Step 3 outputs."""

    def __init__(self, k1: float = DEFAULT_LIQUIDITY_STRIKE_K1) -> None:
        if not 0.0 < k1 <= 1.0:
            raise ValueError(f"liquidity strike k1 must be in (0, 1], got {k1}")
        self.k1 = k1

    def pi_default(self, T: float, sigma_d: float, b: float) -> float:
        """First-passage probability of the loss barrier b over horizon T."""
        return first_passage_probability(T, sigma_d, b)

    def pi_liquidity(self, tau_years: float, T: float, sigma_l: float) -> float:
        """Horizon-driven liquidity option (Roadmap Sec 3.4 Appendix B variant).

        The one-year strike k1 compounds to k = k1^T over the horizon
        (k ~ 0.985 at T=1 down to ~0.55 at T=40), and the option is priced as
        the first-passage probability of that strike under sigma_L. tau is
        retained in the signature for the cliquet variant (a) but does not
        enter this pricing (the tau -> 0 limit the Roadmap records); tau
        drives Step 6 rebalancing frequency instead.
        """
        del tau_years
        if T <= 0.0 or sigma_l <= 0.0:
            return 0.0
        horizon_strike = self.k1**T
        return first_passage_probability(T, sigma_l, horizon_strike)

    def epv_split(self, epv: float, pi_d: float, pi_l: float) -> dict[str, float]:
        """2x2 truth-table split of EPV into the four goals (sums to EPV)."""
        return {
            "Liquidity": (1.0 - pi_d) * (1.0 - pi_l) * epv,
            "Income": pi_d * (1.0 - pi_l) * epv,
            "Preservation": (1.0 - pi_d) * pi_l * epv,
            "Growth": pi_d * pi_l * epv,
        }

    def decompose(
        self,
        ticker: str,
        epv: float,
        sigma_d: float,
        sigma_l: float,
        T: float,
        tau_years: float,
        b: float,
    ) -> GoalShares:
        pi_d = self.pi_default(T, sigma_d, b)
        pi_l = self.pi_liquidity(tau_years, T, sigma_l)
        return GoalShares(
            ticker=ticker,
            pi_default=pi_d,
            pi_liquidity=pi_l,
            epv=epv,
            epv_by_goal=self.epv_split(epv, pi_d, pi_l),
        )

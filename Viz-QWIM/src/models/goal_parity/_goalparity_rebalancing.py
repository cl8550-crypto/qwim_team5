"""SignalPriorityRebalancer: Step 6 — tactical rebalancing (Roadmap Sec 3.6, 4.2).

Project design choice (per advisor guidance, documented in the Proposal's
Step 6 note): instead of the source paper's quadratic tactical program, use a
signal-priority (impact-ranked, greedy) trade-selection heuristic following
Arnott, Li & Linnainmaa (2024), "Smart Rebalancing":

    1. compute portfolio goal powers P_k(w) = sum_i w_i s_{k,i}
    2. goal gaps delta_k = theta_k - P_k(w)
    3. candidate trades = (sell i, buy j) pairs of size ``trade_size``
    4. score_j = reduction in sum_k |delta_k| per unit transaction cost
    5. execute greedily while score > eta, turnover budget remains, and the
       cash floor (w_cash >= cash_min) stays satisfied
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from src.models.goal_parity.utils_goal_parity import GOALS


@dataclass(frozen=True)
class Trade:
    sell: str
    buy: str
    size: float
    score: float


@dataclass
class RebalanceResult:
    tickers: list[str]
    weights: np.ndarray
    traded: bool
    trades: list[Trade] = field(default_factory=list)
    turnover: float = 0.0
    goal_powers_before: dict[str, float] = field(default_factory=dict)
    goal_powers_after: dict[str, float] = field(default_factory=dict)


class SignalPriorityRebalancer:
    """Implements the Sec 4.2 signal-priority loop."""

    def __init__(
        self,
        eps: float = 0.02,
        eta_cost_benefit: float = 100.0,
        cash_min: float = 0.0,
        turnover_budget: float = 0.20,
        trade_size: float = 0.01,
        unit_cost: float = 0.0005,
    ) -> None:
        # eta_cost_benefit is in "gap reduction per unit of round-trip cost";
        # 100 means a trade must close at least 100x its transaction cost in
        # goal gap to execute (a 1% trade at 5 bps/side must close >= 0.001).
        self.eps = eps
        self.eta_cost_benefit = eta_cost_benefit
        self.cash_min = cash_min
        self.turnover_budget = turnover_budget
        self.trade_size = trade_size
        self.unit_cost = unit_cost

    # ------------------------------------------------------------------
    @staticmethod
    def goal_powers(weights: np.ndarray, share_matrix: np.ndarray) -> dict[str, float]:
        """P_k(w) = sum_i w_i * s_{k,i} (Sec 3.6); sums to 1 across goals."""
        return dict(zip(GOALS, (share_matrix.T @ weights).tolist()))

    @staticmethod
    def _gap_metric(weights: np.ndarray, share_matrix: np.ndarray, theta: np.ndarray) -> float:
        return float(np.sum(np.abs(theta - share_matrix.T @ weights)))

    def _cash_share(self, weights: np.ndarray, cash_indices: list[int]) -> float:
        return float(np.sum(weights[cash_indices])) if cash_indices else 1.0

    # ------------------------------------------------------------------
    def rebalance(
        self,
        tickers: list[str],
        weights_current: np.ndarray,
        goal_shares_by_ticker: dict[str, dict[str, float]],
        theta: dict[str, float],
        cash_tickers: list[str] | None = None,
    ) -> RebalanceResult:
        share_matrix = np.array([[goal_shares_by_ticker[t][g] for g in GOALS] for t in tickers])
        theta_vec = np.array([theta[g] for g in GOALS])
        cash_indices = [tickers.index(t) for t in (cash_tickers or []) if t in tickers]

        weights = weights_current.astype(float).copy()
        powers_before = self.goal_powers(weights, share_matrix)
        gaps = theta_vec - share_matrix.T @ weights

        cash_ok = self._cash_share(weights, cash_indices) >= self.cash_min
        if float(np.max(np.abs(gaps))) <= self.eps and cash_ok:
            return RebalanceResult(
                tickers=tickers,
                weights=weights,
                traded=False,
                goal_powers_before=powers_before,
                goal_powers_after=powers_before,
            )

        trades: list[Trade] = []
        turnover = 0.0
        n = len(tickers)
        step = self.trade_size

        while turnover + step <= self.turnover_budget:
            base_metric = self._gap_metric(weights, share_matrix, theta_vec)
            best: tuple[float, int, int] | None = None
            for i in range(n):  # sell i
                if weights[i] < step:
                    continue
                for j in range(n):  # buy j
                    if i == j:
                        continue
                    candidate = weights.copy()
                    candidate[i] -= step
                    candidate[j] += step
                    if self._cash_share(candidate, cash_indices) < self.cash_min:
                        continue
                    improvement = base_metric - self._gap_metric(candidate, share_matrix, theta_vec)
                    score = improvement / (2.0 * self.unit_cost * step)
                    if best is None or score > best[0]:
                        best = (score, i, j)
            if best is None or best[0] <= self.eta_cost_benefit:
                break
            score, i, j = best
            weights[i] -= step
            weights[j] += step
            turnover += step
            trades.append(Trade(sell=tickers[i], buy=tickers[j], size=step, score=score))

        return RebalanceResult(
            tickers=tickers,
            weights=weights,
            traded=bool(trades),
            trades=trades,
            turnover=turnover,
            goal_powers_before=powers_before,
            goal_powers_after=self.goal_powers(weights, share_matrix),
        )

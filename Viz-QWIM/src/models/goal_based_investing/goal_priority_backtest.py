"""Client-cash-flow evaluation of non-postponable and postponable spending.

This small reporting utility applies realised portfolio returns to a retirement
account.  Essential spending is non-postponable (NP): it is paid whenever
wealth is available and any unpaid balance is recorded as an essential
shortfall.  Important and aspirational spending are postponable (P): their
monthly amount may remain outstanding for at most ``postponement_months``.
The oldest outstanding P amount is paid first when assets permit it.

It is deliberately separate from the return-only portfolio backtest.  Return
metrics answer how an allocation performed; this module answers how the same
allocation funded a specified client's priorities.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


PRIORITIES = ("essential", "important", "aspirational")


@dataclass(frozen=True, slots=True)
class Goal_Priority_Backtest:  # noqa: N801
    """Realised wealth path and payment outcomes for one portfolio policy."""

    monthly_wealth: pd.Series
    essential_paid: float
    essential_shortfall: float
    important_paid: float
    important_expired: float
    important_postponed: float
    aspirational_paid: float
    aspirational_expired: float
    aspirational_postponed: float

    @property
    def final_wealth(self) -> float:
        """Return the ending account value after all realised cash flows."""
        return float(self.monthly_wealth.iloc[-1])

    @property
    def net_wealth_returns(self) -> pd.Series:
        """Monthly change in account wealth after all client cash flows."""
        return self.monthly_wealth.pct_change().dropna()


def backtest_goal_priority_cashflows(
    monthly_returns: pd.Series,
    *,
    initial_wealth: float,
    annual_essential: float,
    annual_important: float,
    annual_aspirational: float,
    annual_guaranteed_income: float,
    postponement_months: int = 12,
) -> Goal_Priority_Backtest:
    """Apply monthly NP/P retirement cash flows to one realised return path.

    Guaranteed income and each spending tier are spread evenly across months.
    An unpaid P payment expires after the stated postponement window; this is
    a transparent annual-expense approximation rather than an assertion that
    discretionary consumption can be deferred indefinitely.
    """
    values = monthly_returns.astype(float).dropna()
    if values.empty or not np.isfinite(values.to_numpy()).all() or (values <= -1).any():
        raise ValueError("monthly_returns must be finite, non-empty and greater than -100%")
    numeric_values = {
        "initial_wealth": initial_wealth,
        "annual_essential": annual_essential,
        "annual_important": annual_important,
        "annual_aspirational": annual_aspirational,
        "annual_guaranteed_income": annual_guaranteed_income,
    }
    if any(not np.isfinite(value) or value < 0 for value in numeric_values.values()):
        raise ValueError("wealth, income and spending inputs must be finite and non-negative")
    if not isinstance(postponement_months, int) or postponement_months < 1:
        raise ValueError("postponement_months must be a positive integer")

    wealth = float(initial_wealth)
    monthly_income = annual_guaranteed_income / 12.0
    monthly_spending = {
        "essential": annual_essential / 12.0,
        "important": annual_important / 12.0,
        "aspirational": annual_aspirational / 12.0,
    }
    pending = {priority: [] for priority in ("important", "aspirational")}
    paid = dict.fromkeys(PRIORITIES, 0.0)
    expired = {"important": 0.0, "aspirational": 0.0}
    wealth_path: list[float] = []

    for month, realised_return in enumerate(values, start=1):
        wealth = max(0.0, wealth * (1.0 + realised_return) + monthly_income)
        essential_due = monthly_spending["essential"]
        essential_payment = min(wealth, essential_due)
        wealth -= essential_payment
        paid["essential"] += essential_payment
        essential_shortfall = essential_due - essential_payment
        if month == 1:
            total_essential_shortfall = essential_shortfall
        else:
            total_essential_shortfall += essential_shortfall

        for priority in ("important", "aspirational"):
            pending[priority].append([month, monthly_spending[priority]])
            while pending[priority] and wealth > 0:
                _, outstanding = pending[priority][0]
                payment = min(wealth, outstanding)
                wealth -= payment
                paid[priority] += payment
                pending[priority][0][1] -= payment
                if pending[priority][0][1] <= 1e-10:
                    pending[priority].pop(0)
                else:
                    break
            while pending[priority] and month - pending[priority][0][0] + 1 >= postponement_months:
                _, outstanding = pending[priority].pop(0)
                expired[priority] += outstanding
        wealth_path.append(wealth)

    return Goal_Priority_Backtest(
        monthly_wealth=pd.Series(wealth_path, index=values.index, name="net_wealth"),
        essential_paid=paid["essential"],
        essential_shortfall=total_essential_shortfall,
        important_paid=paid["important"],
        important_expired=expired["important"],
        important_postponed=sum(item[1] for item in pending["important"]),
        aspirational_paid=paid["aspirational"],
        aspirational_expired=expired["aspirational"],
        aspirational_postponed=sum(item[1] for item in pending["aspirational"]),
    )


def payment_rate(*, paid: float, expired: float, postponed: float = 0.0) -> float:
    """Return the fraction of scheduled P spending that was eventually paid."""
    total = paid + expired + postponed
    return 1.0 if total == 0 else paid / total

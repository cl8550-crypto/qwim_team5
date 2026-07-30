"""Performance and risk metrics for the MSGP plan and its benchmarks.

Two distinct notions of "return" matter here and are kept separate
throughout this module:

- **Cashflow-adjusted investment return**: the return earned purely on
  invested capital, stripping out the effect of external contributions and
  goal withdrawals (a simple single-period Dietz-style adjustment,
  ``r_t = (wealth_t - cashflow_t) / wealth_{t-1} - 1``). This is what should
  feed Sharpe/Sortino/volatility/tracking-error, since those measures are
  meaningless if a large withdrawal is misread as a loss.
- **Wealth level**: used directly for drawdown and terminal wealth
  distribution statistics, since a goal withdrawal reducing wealth is a
  real, intended feature of the plan, not something to net out.

All ratio-based statistics take ``periods_per_year`` explicitly rather than
assuming daily/monthly data, since MSGP stages are frequently multi-year.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .goals import Goal
from .stochastic_optimizer import MSGPResult


def cashflow_adjusted_returns(
    wealth: np.ndarray, contributions: np.ndarray, consumption: np.ndarray
) -> np.ndarray:
    """Per-stage investment returns, stripped of external cashflow effects.

    Parameters
    ----------
    wealth : np.ndarray
        Wealth at each stage, length ``n_stages + 1``.
    contributions : np.ndarray
        Contribution inflow at each stage, same length (index 0 unused).
    consumption : np.ndarray
        Withdrawal outflow at each stage, same length (index 0 unused).

    Returns
    -------
    np.ndarray
        Length ``n_stages``, one adjusted return per stage transition.
    """
    n_stages = len(wealth) - 1
    net_cashflow = contributions[1 : n_stages + 1] - consumption[1 : n_stages + 1]
    prev_wealth = wealth[:n_stages]
    returns = np.where(
        prev_wealth > 0,
        (wealth[1 : n_stages + 1] - net_cashflow) / prev_wealth - 1.0,
        0.0,
    )
    return returns


def annualized_return(returns: np.ndarray, periods_per_year: float) -> float:
    """Geometric (compound) annualized return from a per-stage return series."""
    if len(returns) == 0:
        return 0.0
    total_growth = np.prod(1.0 + returns)
    n_years = len(returns) / periods_per_year
    if n_years <= 0 or total_growth <= 0:
        return float("nan")
    return float(total_growth ** (1.0 / n_years) - 1.0)


def annualized_volatility(returns: np.ndarray, periods_per_year: float) -> float:
    """Annualized standard deviation of per-stage returns."""
    if len(returns) < 2:
        return 0.0
    return float(np.std(returns, ddof=1) * np.sqrt(periods_per_year))


def sharpe_ratio(returns: np.ndarray, risk_free_rate: float, periods_per_year: float) -> float:
    """Annualized Sharpe ratio: excess return over volatility.

    Parameters
    ----------
    returns : np.ndarray
        Per-stage cashflow-adjusted returns.
    risk_free_rate : float
        Annualized risk-free rate.
    periods_per_year : float
        Stage frequency.
    """
    ann_return = annualized_return(returns, periods_per_year)
    ann_vol = annualized_volatility(returns, periods_per_year)
    if ann_vol == 0:
        return float("nan")
    return (ann_return - risk_free_rate) / ann_vol


def sortino_ratio(
    returns: np.ndarray,
    risk_free_rate: float,
    periods_per_year: float,
    target_return: float = 0.0,
) -> float:
    """Annualized Sortino ratio: excess return over downside deviation.

    Downside deviation only penalizes returns below ``target_return``
    (annualized, converted to a per-period threshold), following Sortino &
    van der Meer (1991) -- distinguishing "bad" (downside) volatility from
    "good" (upside) volatility, unlike the symmetric Sharpe ratio.
    """
    per_period_target = target_return / periods_per_year
    downside = np.minimum(returns - per_period_target, 0.0)
    downside_dev = np.sqrt(np.mean(downside**2)) * np.sqrt(periods_per_year)
    ann_return = annualized_return(returns, periods_per_year)
    if downside_dev == 0:
        return float("nan")
    return (ann_return - risk_free_rate) / downside_dev


def max_drawdown(wealth: np.ndarray) -> float:
    """Maximum peak-to-trough decline in wealth, as a positive fraction.

    Uses raw wealth levels (not cashflow-adjusted returns) since a
    withdrawal-driven decline is a real drawdown from the investor's
    perspective, but note that MSGP's *planned* goal withdrawals will show
    up here too -- inspect alongside the consumption series when
    interpreting this number for a goals-based plan.
    """
    running_max = np.maximum.accumulate(wealth)
    drawdowns = np.where(running_max > 0, (wealth - running_max) / running_max, 0.0)
    return float(-drawdowns.min())


def tracking_error(returns: np.ndarray, benchmark_returns: np.ndarray, periods_per_year: float) -> float:
    """Annualized standard deviation of the return differential vs. a benchmark."""
    diff = returns - benchmark_returns
    if len(diff) < 2:
        return 0.0
    return float(np.std(diff, ddof=1) * np.sqrt(periods_per_year))


def average_turnover(turnover: np.ndarray) -> float:
    """Mean per-stage gross turnover (see constraints.turnover_constraint for units)."""
    nonzero = turnover[turnover != 0]
    return float(np.mean(turnover)) if len(turnover) else 0.0


def total_transaction_costs(transaction_costs: np.ndarray) -> float:
    """Cumulative monetary transaction costs paid over the backtest."""
    return float(np.sum(transaction_costs))


@dataclass
class TerminalWealthStats:
    """Summary statistics of a terminal wealth distribution."""

    mean: float
    median: float
    std: float
    p10: float
    p25: float
    p75: float
    p90: float


def terminal_wealth_stats(wealth_values: np.ndarray, probabilities: np.ndarray) -> TerminalWealthStats:
    """Probability-weighted summary statistics of terminal wealth.

    Parameters
    ----------
    wealth_values : np.ndarray
        Terminal wealth at each leaf/scenario.
    probabilities : np.ndarray
        Corresponding probabilities, summing to 1.

    Returns
    -------
    TerminalWealthStats
    """
    order = np.argsort(wealth_values)
    values_sorted = wealth_values[order]
    probs_sorted = probabilities[order]
    cum_probs = np.cumsum(probs_sorted)

    def weighted_percentile(q: float) -> float:
        idx = np.searchsorted(cum_probs, q)
        idx = min(idx, len(values_sorted) - 1)
        return float(values_sorted[idx])

    mean = float(np.average(wealth_values, weights=probabilities))
    variance = float(np.average((wealth_values - mean) ** 2, weights=probabilities))
    return TerminalWealthStats(
        mean=mean,
        median=weighted_percentile(0.5),
        std=float(np.sqrt(variance)),
        p10=weighted_percentile(0.10),
        p25=weighted_percentile(0.25),
        p75=weighted_percentile(0.75),
        p90=weighted_percentile(0.90),
    )


def goal_success_probability(result: MSGPResult, goal: Goal) -> float:
    """Probability-weighted fraction of scenarios in which a goal is fully met.

    Computed directly from the solved scenario tree: for each node at the
    goal's horizon stage, checks whether the *incremental* consumption
    attributable to this goal's priority level equals its full (inflation-
    adjusted) target, then sums node probabilities where that holds.

    Parameters
    ----------
    result : MSGPResult
        Solved MSGP result (must include a step at ``goal.priority``).
    goal : Goal
        The goal to evaluate.

    Returns
    -------
    float
        Probability in ``[0, 1]``.
    """
    if goal.priority not in result.steps:
        raise ValueError(f"No solved step at priority {goal.priority} for goal '{goal.name}'.")

    from .stochastic_optimizer import _cumulative_inflation_factor

    step = result.steps[goal.priority]
    prior_priorities = [p for p in result.steps if p < goal.priority]
    prev_step = result.steps[max(prior_priorities)] if prior_priorities else None

    total_prob = 0.0
    achieved_prob = 0.0
    for nid in result.tree.nodes_at_stage(goal.horizon_stage):
        prob = result.tree.nodes[nid].probability
        total_prob += prob
        c_now = step.consumption.get(nid, 0.0)
        c_prev = prev_step.consumption.get(nid, 0.0) if prev_step else 0.0
        inflation_factor = _cumulative_inflation_factor(result.tree, nid)
        target = inflation_factor * goal.target_wealth
        # Relative tolerance: an LP solver's absolute precision degrades with
        # the magnitude of the values involved (typically ~1e-6 to 1e-4
        # *relative* error, not absolute). At million-dollar terminal wealth
        # scales, a fixed absolute epsilon like 1e-6 misclassifies fully
        # achieved goals as failures over a few cents of solver noise.
        tolerance = max(1e-6, 1e-6 * abs(target))
        achieved = (c_now - c_prev) >= target - tolerance
        if achieved:
            achieved_prob += prob
    return achieved_prob / total_prob if total_prob > 0 else float("nan")


@dataclass
class PerformanceReport:
    """Bundle of all headline performance metrics for a single wealth path."""

    annual_return: float
    volatility: float
    sharpe: float
    sortino: float
    max_drawdown: float
    tracking_error: float | None
    avg_turnover: float
    total_transaction_costs: float


def build_performance_report(
    wealth: np.ndarray,
    contributions: np.ndarray,
    consumption: np.ndarray,
    turnover: np.ndarray,
    transaction_costs: np.ndarray,
    periods_per_year: float,
    risk_free_rate: float = 0.0,
    benchmark_wealth: np.ndarray | None = None,
    benchmark_contributions: np.ndarray | None = None,
    benchmark_consumption: np.ndarray | None = None,
) -> PerformanceReport:
    """Compute the full standard performance report for a wealth path.

    Parameters
    ----------
    wealth, contributions, consumption, turnover, transaction_costs : np.ndarray
        See :class:`portfolio_simulator.WealthPath` fields of the same names.
    periods_per_year : float
        Stage frequency for annualization.
    risk_free_rate : float
        Annualized risk-free rate for Sharpe/Sortino.
    benchmark_wealth, benchmark_contributions, benchmark_consumption : np.ndarray, optional
        Same-shaped arrays for a benchmark, enabling tracking error.

    Returns
    -------
    PerformanceReport
    """
    returns = cashflow_adjusted_returns(wealth, contributions, consumption)

    te = None
    if benchmark_wealth is not None:
        bench_returns = cashflow_adjusted_returns(
            benchmark_wealth, benchmark_contributions, benchmark_consumption
        )
        te = tracking_error(returns, bench_returns, periods_per_year)

    return PerformanceReport(
        annual_return=annualized_return(returns, periods_per_year),
        volatility=annualized_volatility(returns, periods_per_year),
        sharpe=sharpe_ratio(returns, risk_free_rate, periods_per_year),
        sortino=sortino_ratio(returns, risk_free_rate, periods_per_year),
        max_drawdown=max_drawdown(wealth),
        tracking_error=te,
        avg_turnover=average_turnover(turnover),
        total_transaction_costs=total_transaction_costs(transaction_costs),
    )

"""Offline walk-forward evaluation of the six-ETF GBI CVaR policies.

This is a research/reporting utility, not Dashboard logic.  At each quarterly
rebalance it uses only the preceding trailing window to refit the five CVaR
policies, applies the selected weights to the next realised months, and
deducts a one-way trading cost from actual portfolio wealth.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from .portfolio_performance import calculate_portfolio_performance
from .risk_portfolio_policy import DEFAULT_RISK_PROFILE_BANDS, build_cvar_policies


if TYPE_CHECKING:
    from collections.abc import Mapping


SIX_ETF_ASSETS = ("BIL", "XLK", "XLP", "AGG", "TIP", "GLD")
EQUITY_ASSETS = ("XLK", "XLP")
# Frozen before comparing the two lookback windows.  They avoid a trivial
# all-cash or single-ETF solution while retaining the existing GBI universe.
DEFAULT_SIX_ETF_CAPS: Mapping[str, float] = {
    "BIL": 0.40,
    "XLK": 0.35,
    "XLP": 0.50,
    "AGG": 0.35,
    "TIP": 0.25,
    "GLD": 0.15,
}
MODERATE_BENCHMARK_WEIGHTS: Mapping[str, float] = {
    "BIL": 0.15,
    "XLK": 0.25,
    "XLP": 0.25,
    "AGG": 0.25,
    "TIP": 0.05,
    "GLD": 0.05,
}


@dataclass(frozen=True, slots=True)
class Rolling_Policy_Backtest:  # noqa: N801
    """One risk-profile's realised return path and rebalance metadata."""

    profile: str
    monthly_returns: pd.Series
    rebalance_count: int
    total_turnover: float
    total_transaction_cost: float
    target_weights: pd.DataFrame


def backtest_rolling_cvar_policies(
    monthly_asset_returns: pd.DataFrame,
    *,
    lookback_months: int,
    rebalance_months: int = 3,
    transaction_cost_rate: float = 0.001,
    asset_caps: Mapping[str, float] = DEFAULT_SIX_ETF_CAPS,
) -> dict[str, Rolling_Policy_Backtest]:
    """Run a no-look-ahead rolling-CVaR backtest for the five GBI profiles.

    The first ``lookback_months`` observations are estimation only.  The
    remaining realised months are out-of-sample.  Weights are refitted at the
    start of every rebalance block, held while they drift, then returned to
    the next target weights.  Transaction cost is charged on one-way turnover
    ``0.5 * sum(abs(target - drifted))``.
    """
    if lookback_months < 12:
        raise ValueError("lookback_months must be at least 12")
    if rebalance_months < 1:
        raise ValueError("rebalance_months must be positive")
    if not 0 <= transaction_cost_rate < 1:
        raise ValueError("transaction_cost_rate must lie in [0, 1)")
    missing_assets = set(SIX_ETF_ASSETS).difference(monthly_asset_returns.columns)
    if missing_assets:
        raise ValueError(
            f"monthly_asset_returns is missing required assets: {sorted(missing_assets)}",
        )
    returns = monthly_asset_returns.loc[:, SIX_ETF_ASSETS].astype(float).dropna()
    if len(returns) <= lookback_months:
        raise ValueError("monthly_asset_returns must contain observations beyond lookback_months")
    if not np.isfinite(returns.to_numpy()).all() or (returns.to_numpy() <= -1).any():
        raise ValueError("monthly_asset_returns must be finite and greater than -100%")
    if set(asset_caps) != set(SIX_ETF_ASSETS) or any(
        not 0 <= cap <= 1 for cap in asset_caps.values()
    ):
        raise ValueError("asset_caps must provide a [0, 1] cap for each six-ETF asset")

    states = {
        band.profile: {
            "weights": np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
            "returns": [],
            "dates": [],
            "turnover": 0.0,
            "cost": 0.0,
            "rebalances": 0,
            "target_dates": [],
            "target_weights": [],
        }
        for band in DEFAULT_RISK_PROFILE_BANDS
    }
    for start in range(lookback_months, len(returns), rebalance_months):
        fitted = build_cvar_policies(
            returns.iloc[start - lookback_months : start],
            equity_assets=EQUITY_ASSETS,
            max_weight=asset_caps,
        )
        stop = min(start + rebalance_months, len(returns))
        for profile, policy in fitted.items():
            state = states[profile]
            target = np.array([policy.weights[asset] for asset in SIX_ETF_ASSETS])
            turnover = 0.5 * float(np.abs(target - state["weights"]).sum())
            cost = transaction_cost_rate * turnover
            state["turnover"] += turnover
            state["cost"] += cost
            state["rebalances"] += 1
            state["target_dates"].append(returns.index[start])
            state["target_weights"].append(target)
            state["weights"] = target
            for date, asset_return in returns.iloc[start:stop].iterrows():
                gross_return = float(np.dot(state["weights"], asset_return.to_numpy(dtype=float)))
                net_return = (
                    (1.0 - cost) * (1.0 + gross_return) - 1.0
                    if date == returns.index[start]
                    else gross_return
                )
                state["returns"].append(net_return)
                state["dates"].append(date)
                state["weights"] = (
                    state["weights"]
                    * (1.0 + asset_return.to_numpy(dtype=float))
                    / (1.0 + gross_return)
                )

    return {
        profile: Rolling_Policy_Backtest(
            profile=profile,
            monthly_returns=pd.Series(
                state["returns"],
                index=pd.Index(state["dates"], name=returns.index.name),
                name=profile,
            ),
            rebalance_count=state["rebalances"],
            total_turnover=float(state["turnover"]),
            total_transaction_cost=float(state["cost"]),
            target_weights=pd.DataFrame(
                state["target_weights"],
                index=pd.Index(state["target_dates"], name=returns.index.name),
                columns=SIX_ETF_ASSETS,
            ),
        )
        for profile, state in states.items()
    }


def backtest_fixed_cvar_policies(
    monthly_asset_returns: pd.DataFrame,
    *,
    lookback_months: int,
    rebalance_months: int = 3,
    transaction_cost_rate: float = 0.001,
    asset_caps: Mapping[str, float] = DEFAULT_SIX_ETF_CAPS,
) -> dict[str, Rolling_Policy_Backtest]:
    """Evaluate frozen initial CVaR policies on the same out-of-sample months.

    This is the fixed-policy comparator for the rolling policy.  It calibrates
    weights once using the initial trailing window, then rebalances to those
    unchanged weights quarterly while applying identical transaction costs.
    """
    rolling = backtest_rolling_cvar_policies(
        monthly_asset_returns,
        lookback_months=lookback_months,
        rebalance_months=rebalance_months,
        transaction_cost_rate=transaction_cost_rate,
        asset_caps=asset_caps,
    )
    returns = monthly_asset_returns.loc[:, SIX_ETF_ASSETS].astype(float).dropna()
    frozen = build_cvar_policies(
        returns.iloc[:lookback_months],
        equity_assets=EQUITY_ASSETS,
        max_weight=asset_caps,
    )
    results: dict[str, Rolling_Policy_Backtest] = {}
    for profile in rolling:
        target = np.array([frozen[profile].weights[asset] for asset in SIX_ETF_ASSETS])
        weights = np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        path, dates, target_dates, target_history = [], [], [], []
        turnover_total = cost_total = 0.0
        for start in range(lookback_months, len(returns), rebalance_months):
            turnover = 0.5 * float(np.abs(target - weights).sum())
            cost = transaction_cost_rate * turnover
            turnover_total += turnover
            cost_total += cost
            target_dates.append(returns.index[start])
            target_history.append(target.copy())
            weights = target.copy()
            stop = min(start + rebalance_months, len(returns))
            for position, (date, asset_return) in enumerate(returns.iloc[start:stop].iterrows()):
                gross_return = float(np.dot(weights, asset_return.to_numpy(dtype=float)))
                path.append(
                    (1.0 - cost) * (1.0 + gross_return) - 1.0 if position == 0 else gross_return,
                )
                dates.append(date)
                weights = (
                    weights * (1.0 + asset_return.to_numpy(dtype=float)) / (1.0 + gross_return)
                )
        results[profile] = Rolling_Policy_Backtest(
            profile=profile,
            monthly_returns=pd.Series(
                path, index=pd.Index(dates, name=returns.index.name), name=profile,
            ),
            rebalance_count=len(target_dates),
            total_turnover=turnover_total,
            total_transaction_cost=cost_total,
            target_weights=pd.DataFrame(
                target_history,
                index=pd.Index(target_dates, name=returns.index.name),
                columns=SIX_ETF_ASSETS,
            ),
        )
    return results


def backtest_fixed_weight_benchmark(
    monthly_asset_returns: pd.DataFrame,
    *,
    weights_by_asset: Mapping[str, float],
    lookback_months: int,
    rebalance_months: int = 3,
    transaction_cost_rate: float = 0.001,
    name: str = "Benchmark",
) -> Rolling_Policy_Backtest:
    """Evaluate a fixed-weight benchmark over the rolling policy's OOS months."""
    if set(weights_by_asset) != set(SIX_ETF_ASSETS):
        raise ValueError("weights_by_asset must cover each six-ETF asset exactly once")
    target = np.array([float(weights_by_asset[asset]) for asset in SIX_ETF_ASSETS])
    if (target < 0).any() or not np.isclose(target.sum(), 1.0):
        raise ValueError("weights_by_asset must be long-only and sum to one")
    returns = monthly_asset_returns.loc[:, SIX_ETF_ASSETS].astype(float).dropna()
    if len(returns) <= lookback_months:
        raise ValueError("monthly_asset_returns must contain observations beyond lookback_months")
    current_weights = np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    path, dates, target_dates, target_history = [], [], [], []
    turnover_total = cost_total = 0.0
    for start in range(lookback_months, len(returns), rebalance_months):
        turnover = 0.5 * float(np.abs(target - current_weights).sum())
        cost = transaction_cost_rate * turnover
        turnover_total += turnover
        cost_total += cost
        target_dates.append(returns.index[start])
        target_history.append(target.copy())
        current_weights = target.copy()
        stop = min(start + rebalance_months, len(returns))
        for position, (date, asset_return) in enumerate(returns.iloc[start:stop].iterrows()):
            gross_return = float(np.dot(current_weights, asset_return.to_numpy(dtype=float)))
            path.append((1.0 - cost) * (1.0 + gross_return) - 1.0 if position == 0 else gross_return)
            dates.append(date)
            current_weights = current_weights * (1.0 + asset_return.to_numpy(dtype=float)) / (1.0 + gross_return)
    return Rolling_Policy_Backtest(
        profile=name,
        monthly_returns=pd.Series(path, index=pd.Index(dates, name=returns.index.name), name=name),
        rebalance_count=len(target_dates),
        total_turnover=turnover_total,
        total_transaction_cost=cost_total,
        target_weights=pd.DataFrame(
            target_history,
            index=pd.Index(target_dates, name=returns.index.name),
            columns=SIX_ETF_ASSETS,
        ),
    )


def rolling_backtest_performance_table(
    results: Mapping[str, Rolling_Policy_Backtest],
) -> pd.DataFrame:
    """Format rolling-policy results using the same columns as the static table."""
    rows = [
        calculate_portfolio_performance(
            pd.DataFrame({"portfolio": result.monthly_returns}),
            weights={"portfolio": 1.0},
            profile=profile,
        )
        for profile, result in results.items()
    ]
    return pd.DataFrame(
        {
            "Risk profile": [row.profile for row in rows],
            "Annualized return": [row.annualized_return for row in rows],
            "Annualized volatility": [row.annualized_volatility for row in rows],
            "Sharpe ratio": [row.sharpe_ratio for row in rows],
            "Maximum drawdown": [row.maximum_drawdown for row in rows],
            "Historical ES (95%)": [row.expected_shortfall_95 for row in rows],
            "Monthly observations": [row.observations for row in rows],
        },
    )

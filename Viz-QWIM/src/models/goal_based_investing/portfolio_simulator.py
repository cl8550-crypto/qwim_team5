"""Out-of-sample simulation: walk-forward MSGP backtest and static benchmarks.

Kim et al. (2019) only report *in-sample* statistics computed directly on
the scenario tree (their Figures 2-7). That is a legitimate way to describe
what the optimizer believes about its own plan, but it cannot detect
overfitting to the bootstrapped tree, and it gives no head-to-head
comparison against realized market history. This module adds a genuine
**walk-forward backtest**: at each rebalance date, re-estimate the return
model from only the trailing data available at that time, rebuild a fresh
scenario tree, re-solve the MSGP for the remaining horizon, apply the
resulting stage-0 (i.e., "now") trade, and then step forward using the
*actual* realized historical return -- never information from the future.
This is the standard walk-forward protocol used to evaluate systematic
strategies out of sample (see e.g. Bailey & Lopez de Prado 2014 on backtest
overfitting) and is a substantive improvement in realism over the paper's
in-sample-only demonstration.

Benchmarks
----------
Static, periodically-rebalanced weight portfolios simulated on the same
realized return path and the same contribution/consumption cash flows:
100% S&P 500, 60/40 (stocks/bonds), and equal-weight across the full asset
universe.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .covariance import CovarianceConfig, ewma_shrinkage_covariance
from .expected_returns import BlackLittermanViews, estimate_expected_returns
from .goals import GoalSet
from .scenario_generation import BootstrapConfig, generate_bootstrap_stage_paths
from .scenario_tree import build_scenario_tree
from .stochastic_optimizer import MSGPConfig, MSGPOptimizer


@dataclass
class WealthPath:
    """A realized wealth trajectory plus the trades/consumption that produced it.

    Attributes
    ----------
    dates : list
        Rebalance dates (or stage indices if no calendar dates available).
    wealth : np.ndarray
        Wealth immediately after each rebalance/consumption event, length
        ``n_stages + 1`` (index 0 = stage-0 initial wealth).
    weights : np.ndarray
        Shape ``(n_stages + 1, n_assets)``, post-rebalance weights at each
        stage.
    consumption : np.ndarray
        Consumption withdrawn at each stage, length ``n_stages + 1`` (index
        0 always 0.0).
    turnover : np.ndarray
        Gross turnover (see :func:`constraints.turnover_constraint`) realized
        at each stage.
    transaction_costs : np.ndarray
        Monetary transaction costs paid at each stage.
    """

    dates: list
    wealth: np.ndarray
    weights: np.ndarray
    consumption: np.ndarray
    turnover: np.ndarray
    transaction_costs: np.ndarray


def simulate_fixed_weight_benchmark(
    realized_returns: np.ndarray,
    target_weights: np.ndarray,
    initial_wealth: float,
    contribution_schedule: np.ndarray,
    consumption_schedule: np.ndarray | None = None,
    txn_cost: float = 0.0,
) -> WealthPath:
    """Simulate a periodically-rebalanced fixed-weight benchmark portfolio.

    Parameters
    ----------
    realized_returns : np.ndarray
        Shape ``(n_stages, n_assets)`` actual (not bootstrapped) per-stage
        returns realized over the backtest.
    target_weights : np.ndarray
        Shape ``(n_assets,)``, rebalanced back to this target every stage.
    initial_wealth : float
        Stage-0 wealth.
    contribution_schedule : np.ndarray
        Length ``n_stages + 1`` additional investment per stage (index 0 unused).
    consumption_schedule : np.ndarray, optional
        Length ``n_stages + 1`` planned withdrawals per stage; if omitted, no
        withdrawals (pure accumulation benchmark).
    txn_cost : float
        Proportional cost applied to the full rebalance trade each stage.

    Returns
    -------
    WealthPath
    """
    n_stages, n_assets = realized_returns.shape
    consumption_schedule = (
        consumption_schedule if consumption_schedule is not None else np.zeros(n_stages + 1)
    )

    wealth = np.zeros(n_stages + 1)
    weights = np.zeros((n_stages + 1, n_assets))
    turnover = np.zeros(n_stages + 1)
    txn_costs = np.zeros(n_stages + 1)

    wealth[0] = initial_wealth
    weights[0] = target_weights
    prev_alloc = target_weights * initial_wealth

    for t in range(1, n_stages + 1):
        arrival = prev_alloc * (1.0 + realized_returns[t - 1])
        arrival_total = arrival.sum()
        net_cash = contribution_schedule[t] - consumption_schedule[t]
        gross_total = arrival_total + net_cash
        target_alloc = target_weights * gross_total

        trade = target_alloc - arrival
        gross_turnover = np.abs(trade).sum()  # buys + sells implied by the rebalance
        cost = txn_cost * gross_turnover
        final_total = gross_total - cost
        final_alloc = target_weights * final_total

        wealth[t] = final_total
        weights[t] = target_weights
        turnover[t] = gross_turnover / arrival_total if arrival_total > 0 else 0.0
        txn_costs[t] = cost
        prev_alloc = final_alloc

    return WealthPath(
        dates=list(range(n_stages + 1)),
        wealth=wealth,
        weights=weights,
        consumption=consumption_schedule.copy(),
        turnover=turnover,
        transaction_costs=txn_costs,
    )


@dataclass
class WalkForwardConfig:
    """Configuration for the rolling MSGP walk-forward backtest.

    Parameters
    ----------
    lookback_periods : int
        Number of trailing base-frequency periods used to (re-)estimate
        covariance/expected returns and bootstrap paths at each rebalance.
    stage_lengths : list[int]
        Base periods per remaining stage, same convention as
        :func:`scenario_generation.compound_to_stage_returns`.
    branching : list[int]
        Scenario-tree branching factors per remaining stage.
    n_bootstrap_paths : int
        Bootstrap paths drawn at each re-optimization.
    expected_return_method : str
        Passed to :func:`expected_returns.estimate_expected_returns`.
    market_weights : np.ndarray | None
        Benchmark weights for CAPM/Black-Litterman.
    risk_free_rate : float
        Annual risk-free rate.
    bl_views : BlackLittermanViews | None
        Optional investor views for Black-Litterman.
    covariance_config : CovarianceConfig
        EWMA + shrinkage settings.
    bootstrap_config : BootstrapConfig
        Stationary bootstrap settings.
    msgp_config_template : MSGPConfig
        Template config (max_weight, turnover_limit, txn costs, discount
        rate, portfolio_cvar); ``stage_years`` is overwritten per re-solve.
    random_state : int | None
        Seed for reproducibility across re-optimizations.
    """

    lookback_periods: int
    stage_lengths: list[int]
    branching: list[int]
    n_bootstrap_paths: int
    expected_return_method: str
    msgp_config_template: MSGPConfig
    market_weights: np.ndarray | None = None
    risk_free_rate: float = 0.0
    bl_views: BlackLittermanViews | None = None
    covariance_config: CovarianceConfig = field(default_factory=CovarianceConfig)
    bootstrap_config: BootstrapConfig = field(default_factory=BootstrapConfig)
    random_state: int | None = None


def walk_forward_backtest(
    full_history: pd.DataFrame,
    backtest_start_idx: int,
    goal_set: GoalSet,
    config: WalkForwardConfig,
) -> WealthPath:
    """Rolling re-optimization backtest of the MSGP strategy.

    At each stage boundary within the backtest window, only data strictly
    before that point is used to re-estimate the return model, rebuild the
    scenario tree, and re-solve the MSGP for the *remaining* goal horizon.
    The resulting stage-0 (i.e. "now") trade is applied, then the realized
    historical return for that period advances the actual wealth -- so no
    future information leaks into any decision.

    Parameters
    ----------
    full_history : pd.DataFrame
        Full periodic-return history, index chronological, spanning both the
        estimation lookback and the entire backtest window.
    backtest_start_idx : int
        Row index in ``full_history`` at which the backtest (stage 0 of the
        investor's plan) begins.
    goal_set : GoalSet
        Investor's prioritized goals, defined relative to the backtest's own
        stage indexing (stage 0 = ``backtest_start_idx``).
    config : WalkForwardConfig
        Backtest configuration.

    Returns
    -------
    WealthPath
    """
    n_stages = len(config.stage_lengths)
    n_assets = full_history.shape[1]
    asset_names = list(full_history.columns)

    wealth = np.zeros(n_stages + 1)
    weights = np.zeros((n_stages + 1, n_assets))
    consumption = np.zeros(n_stages + 1)
    turnover = np.zeros(n_stages + 1)
    txn_costs = np.zeros(n_stages + 1)

    wealth[0] = goal_set.initial_wealth()
    current_alloc = np.zeros(n_assets)
    current_alloc[0] = wealth[0]  # start fully in cash, per the paper's convention
    weights[0] = current_alloc / wealth[0] if wealth[0] > 0 else current_alloc

    cursor = backtest_start_idx
    for t in range(n_stages):
        lookback = full_history.iloc[max(0, cursor - config.lookback_periods) : cursor]
        cov_ann, _ = ewma_shrinkage_covariance(lookback, config.covariance_config)
        mu_ann = estimate_expected_returns(
            config.expected_return_method,
            lookback,
            cov_ann,
            market_weights=config.market_weights,
            risk_free_rate=config.risk_free_rate,
            bl_views=config.bl_views,
        )

        remaining_stage_lengths = config.stage_lengths[t:]
        remaining_branching = config.branching[t:]
        paths = generate_bootstrap_stage_paths(
            lookback,
            remaining_stage_lengths,
            config.n_bootstrap_paths,
            config=config.bootstrap_config,
            target_mean=mu_ann,
            target_cov=cov_ann,
        )
        tree = build_scenario_tree(
            paths, remaining_branching, asset_names, random_state=config.random_state
        )

        remaining_goals = _shift_goals(goal_set, shift=t, current_wealth=current_alloc.sum())
        stage_years = list(range(len(remaining_stage_lengths) + 1))
        cfg = _clone_msgp_config(config.msgp_config_template, stage_years=stage_years)
        optimizer = MSGPOptimizer(tree, remaining_goals, cfg)
        result = optimizer.solve()

        root_x = result.final.x[0]

        realized_return = full_history.iloc[cursor : cursor + remaining_stage_lengths[0]].to_numpy()
        stage_realized_return = np.prod(1.0 + realized_return, axis=0) - 1.0

        pre_trade_value = current_alloc.sum()
        post_trade_alloc = root_x.copy()  # planned post-trade allocation at stage 0 of this re-solve
        # Scale plan to actual pre-trade wealth (tree used bootstrapped, not realized, path).
        planned_total = post_trade_alloc.sum()
        if planned_total > 0:
            post_trade_alloc = post_trade_alloc / planned_total * pre_trade_value

        traded = np.abs(post_trade_alloc - current_alloc).sum()
        turnover[t + 1] = traded / pre_trade_value if pre_trade_value > 0 else 0.0
        cost = config.msgp_config_template.txn_cost_buy * traded * 0.5 + (
            config.msgp_config_template.txn_cost_sell * traded * 0.5
        )
        txn_costs[t + 1] = cost
        post_trade_alloc_after_cost = post_trade_alloc * (1 - cost / planned_total if planned_total > 0 else 1.0)

        grown = post_trade_alloc_after_cost * (1.0 + stage_realized_return)
        contribution_at_stage1 = float(
            remaining_goals.investment_schedule(len(remaining_stage_lengths))[1]
        )
        goal_at_stage = _goal_amount_at_stage(remaining_goals, stage=1)
        total_after_growth = grown.sum() + contribution_at_stage1
        withdrawal = min(goal_at_stage, max(total_after_growth, 0.0))
        net_total = total_after_growth - withdrawal
        if grown.sum() > 0:
            current_alloc = grown * (net_total / grown.sum())
        else:
            current_alloc = np.zeros(n_assets)
            current_alloc[0] = net_total
        wealth[t + 1] = current_alloc.sum()
        weights[t + 1] = current_alloc / wealth[t + 1] if wealth[t + 1] > 0 else current_alloc
        consumption[t + 1] = withdrawal

        cursor += remaining_stage_lengths[0]

    return WealthPath(
        dates=list(range(n_stages + 1)),
        wealth=wealth,
        weights=weights,
        consumption=consumption,
        turnover=turnover,
        transaction_costs=txn_costs,
    )


def _shift_goals(goal_set: GoalSet, shift: int, current_wealth: float = 0.0) -> GoalSet:
    """Return a GoalSet with horizons shifted back by ``shift`` stages, dropping the past.

    The actual current portfolio value (``current_wealth``) is assigned to
    whichever goal is highest priority among the survivors, since the
    optimizer's stage-0 cash balance must reflect real wealth at the
    rebalance date, not the original plan's stage-0 wealth.
    """
    from .goals import Goal

    new_goals = []
    for g in goal_set.goals:
        new_horizon = g.horizon_stage - shift
        if new_horizon < 0:
            continue
        new_sched = {
            s - shift: v for s, v in g.contribution_schedule.items() if s - shift >= 1
        }
        new_goals.append(
            Goal(
                name=g.name,
                target_wealth=g.target_wealth,
                horizon_stage=new_horizon,
                priority=g.priority,
                probability_of_success=g.probability_of_success,
                current_wealth=0.0,
                contribution_schedule=new_sched,
                cvar_alpha=g.cvar_alpha,
                cvar_shortfall_ratio=g.cvar_shortfall_ratio,
            )
        )
    if not new_goals:
        raise ValueError("All goals exhausted before end of backtest horizon.")

    best_priority = min(g.priority for g in new_goals)
    first_idx = next(i for i, g in enumerate(new_goals) if g.priority == best_priority)
    new_goals[first_idx] = Goal(
        name=new_goals[first_idx].name,
        target_wealth=new_goals[first_idx].target_wealth,
        horizon_stage=new_goals[first_idx].horizon_stage,
        priority=new_goals[first_idx].priority,
        probability_of_success=new_goals[first_idx].probability_of_success,
        current_wealth=current_wealth,
        contribution_schedule=new_goals[first_idx].contribution_schedule,
        cvar_alpha=new_goals[first_idx].cvar_alpha,
        cvar_shortfall_ratio=new_goals[first_idx].cvar_shortfall_ratio,
    )
    return GoalSet(new_goals)


def _goal_amount_at_stage(goal_set: GoalSet, stage: int) -> float:
    total = 0.0
    for g in goal_set.goals:
        if g.horizon_stage == stage:
            total += g.target_wealth
    return total


def _clone_msgp_config(template: MSGPConfig, stage_years: list) -> MSGPConfig:
    return MSGPConfig(
        stage_years=stage_years,
        discount_rate=template.discount_rate,
        max_weight=template.max_weight,
        turnover_limit=template.turnover_limit,
        txn_cost_buy=template.txn_cost_buy,
        txn_cost_sell=template.txn_cost_sell,
        portfolio_cvar={k: v for k, v in template.portfolio_cvar.items() if k < len(stage_years)},
        solver=template.solver,
    )

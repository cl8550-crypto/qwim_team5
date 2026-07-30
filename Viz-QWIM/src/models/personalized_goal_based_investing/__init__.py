
"""Personalized goal-based investing via multi-stage stochastic goal programming.

Implements and extends Kim, Kwon, Lee, Kim & Lin (2019), "Personalized
goal-based investing via multi-stage stochastic goal programming",
Quantitative Finance 20(3), 515-526, with historical-bootstrap scenario
generation, EWMA+shrinkage covariance, Black-Litterman expected returns, and
CVaR-based downside protection.
"""

from .constraints import (
    cvar_goal_shortfall_constraints,
    cvar_portfolio_return_constraints,
    goal_bound_constraints,
    max_weight_constraints,
    nonnegativity_constraints,
    rebalance_flow_constraints,
    stage0_allocation_constraints,
    turnover_constraint,
)
from .covariance import (
    CovarianceConfig,
    constant_correlation_target,
    ewma_covariance,
    ewma_shrinkage_covariance,
    ledoit_wolf_shrinkage_intensity,
)
from .expected_returns import (
    BlackLittermanViews,
    black_litterman_posterior,
    capm_implied_returns,
    estimate_expected_returns,
    historical_mean_returns,
)
from .goals import Goal, GoalSet
from .performance import (
    PerformanceReport,
    TerminalWealthStats,
    average_turnover,
    build_performance_report,
    cashflow_adjusted_returns,
    goal_success_probability,
    max_drawdown,
    sharpe_ratio,
    sortino_ratio,
    terminal_wealth_stats,
    total_transaction_costs,
    tracking_error,
)
from .portfolio_simulator import (
    WalkForwardConfig,
    WealthPath,
    simulate_fixed_weight_benchmark,
    walk_forward_backtest,
)
from .scenario_generation import (
    BootstrapConfig,
    compound_to_stage_returns,
    generate_bootstrap_stage_paths,
    generate_bootstrap_stage_paths_with_inflation,
    stationary_bootstrap_path,
)
from .scenario_tree import ScenarioNode, ScenarioTree, build_scenario_tree
from .stochastic_optimizer import (
    MSGPConfig,
    MSGPOptimizer,
    MSGPResult,
    MSGPStepResult,
)
from .visualization import (
    plot_allocation_over_time,
    plot_efficient_frontier,
    plot_goal_probabilities,
    plot_scenario_tree,
    plot_terminal_wealth_distribution,
)

__all__ = [
    "Goal",
    "GoalSet",
    "BootstrapConfig",
    "stationary_bootstrap_path",
    "compound_to_stage_returns",
    "generate_bootstrap_stage_paths",
    "generate_bootstrap_stage_paths_with_inflation",
    "CovarianceConfig",
    "ewma_covariance",
    "constant_correlation_target",
    "ledoit_wolf_shrinkage_intensity",
    "ewma_shrinkage_covariance",
    "BlackLittermanViews",
    "capm_implied_returns",
    "black_litterman_posterior",
    "historical_mean_returns",
    "estimate_expected_returns",
    "ScenarioNode",
    "ScenarioTree",
    "build_scenario_tree",
    "stage0_allocation_constraints",
    "rebalance_flow_constraints",
    "nonnegativity_constraints",
    "max_weight_constraints",
    "turnover_constraint",
    "goal_bound_constraints",
    "cvar_goal_shortfall_constraints",
    "cvar_portfolio_return_constraints",
    "MSGPConfig",
    "MSGPOptimizer",
    "MSGPResult",
    "MSGPStepResult",
    "WalkForwardConfig",
    "WealthPath",
    "simulate_fixed_weight_benchmark",
    "walk_forward_backtest",
    "PerformanceReport",
    "TerminalWealthStats",
    "average_turnover",
    "build_performance_report",
    "cashflow_adjusted_returns",
    "goal_success_probability",
    "max_drawdown",
    "sharpe_ratio",
    "sortino_ratio",
    "terminal_wealth_stats",
    "total_transaction_costs",
    "tracking_error",
    "plot_allocation_over_time",
    "plot_efficient_frontier",
    "plot_goal_probabilities",
    "plot_scenario_tree",
    "plot_terminal_wealth_distribution",
]

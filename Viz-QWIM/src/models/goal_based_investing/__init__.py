"""Goal-based investing baseline model for the QWIM planning pipeline."""

from __future__ import annotations

from src.models.goal_based_investing.client_financial_plan import (
    Client_Financial_Plan,
    Income_Source_Specification,
    build_client_financial_plan,
    build_portfolio_specification_from_plan,
)
from src.models.goal_based_investing.model_goal_based_investing_baseline import (
    Goal_Assessment,
    Goal_Based_Investing_Baseline,
)
from src.models.goal_based_investing.model_goal_postponement import (
    Goal_Specification,
    Portfolio_Specification,
    Priority_Spending_Specification,
    Scenario_Node,
    Scenario_Tree,
    build_goal_postponement_model,
    fixed_date_comparator,
)
from src.models.goal_based_investing.portfolio_performance import (
    Portfolio_Performance,
    build_policy_performance_table,
    calculate_portfolio_performance,
    performance_comparison_to_latex,
    performance_table_to_latex,
    write_performance_latex_table,
)
from src.models.goal_based_investing.risk_portfolio_policy import (
    DEFAULT_RISK_PROFILE_BANDS,
    Predefined_Portfolio_Policy,
    Risk_Profile_Band,
    build_cvar_policies,
    load_predefined_cvar_policies,
    normalize_risk_profile,
)
from src.models.goal_based_investing.rolling_policy_backtest import (
    Rolling_Policy_Backtest,
    backtest_fixed_cvar_policies,
    backtest_fixed_weight_benchmark,
    backtest_rolling_cvar_policies,
    rolling_backtest_performance_table,
)


__all__ = [
    "DEFAULT_RISK_PROFILE_BANDS",
    "Client_Financial_Plan",
    "Goal_Assessment",
    "Goal_Based_Investing_Baseline",
    "Goal_Specification",
    "Income_Source_Specification",
    "Portfolio_Performance",
    "Portfolio_Specification",
    "Predefined_Portfolio_Policy",
    "Priority_Spending_Specification",
    "Risk_Profile_Band",
    "Rolling_Policy_Backtest",
    "Scenario_Node",
    "Scenario_Tree",
    "backtest_fixed_cvar_policies",
    "backtest_fixed_weight_benchmark",
    "backtest_rolling_cvar_policies",
    "build_client_financial_plan",
    "build_cvar_policies",
    "build_goal_postponement_model",
    "build_policy_performance_table",
    "build_portfolio_specification_from_plan",
    "calculate_portfolio_performance",
    "fixed_date_comparator",
    "load_predefined_cvar_policies",
    "normalize_risk_profile",
    "performance_comparison_to_latex",
    "performance_table_to_latex",
    "rolling_backtest_performance_table",
    "write_performance_latex_table",
]

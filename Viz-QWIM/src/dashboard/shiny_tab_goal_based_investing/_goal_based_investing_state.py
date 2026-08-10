"""Shared state and pure calculation helpers for Goal-Based Investing."""

from __future__ import annotations

from typing import Any

import numpy as np

from shiny import reactive

from src.models.goal_based_investing import (
    Goal_Based_Investing_Baseline,
    build_goal_postponement_model,
    build_portfolio_specification_from_plan,
)
from src.models.goal_based_investing.goal_priority_backtest import (
    backtest_goal_priority_cashflows,
    payment_rate,
)
from src.models.goal_based_investing.scenario_tree_goal_based_investing import (
    historical_bootstrap_tree,
)


GOAL_PROFILE_STATE_KEY = "Goal_Based_Investing_Profile"
GOAL_ASSESSMENT_STATE_KEY = "Goal_Based_Investing_Assessment"
GOAL_ASSESSMENT_ERROR_KEY = "Goal_Based_Investing_Assessment_Error"
GOAL_FINANCIAL_PLAN_STATE_KEY = "Goal_Based_Investing_Financial_Plan"
GOAL_MULTISTAGE_PREVIEW_STATE_KEY = "Goal_Based_Investing_Multistage_Preview"


def get_goal_based_investing_state(*, reactives_shiny: dict[str, Any]) -> dict[str, Any]:
    """Return the session-scoped reactive values used by both GBI subtabs."""
    inner_variables = reactives_shiny["Inner_Variables_Shiny"]
    state_keys = (
        GOAL_PROFILE_STATE_KEY,
        GOAL_ASSESSMENT_STATE_KEY,
        GOAL_ASSESSMENT_ERROR_KEY,
        GOAL_FINANCIAL_PLAN_STATE_KEY,
        GOAL_MULTISTAGE_PREVIEW_STATE_KEY,
    )
    for state_key in state_keys:
        if state_key not in inner_variables:
            inner_variables[state_key] = reactive.Value(None)
    return {
        "Profile": inner_variables[GOAL_PROFILE_STATE_KEY],
        "Assessment": inner_variables[GOAL_ASSESSMENT_STATE_KEY],
        "Error": inner_variables[GOAL_ASSESSMENT_ERROR_KEY],
        "Financial_Plan": inner_variables[GOAL_FINANCIAL_PLAN_STATE_KEY],
        "Multistage_Preview": inner_variables[GOAL_MULTISTAGE_PREVIEW_STATE_KEY],
    }


def build_goal_assessment_state(
    *,
    profile: dict[str, Any],
    portfolio_monthly_returns: np.ndarray | None = None,
) -> dict[str, Any]:
    """Calculate a deterministic or risk-policy scenario goal assessment."""
    annual_return_decimal = float(profile["Annual_Return_Percent"]) / 100.0
    goal_model = Goal_Based_Investing_Baseline(
        goal_name=str(profile["Goal_Name"]),
        target_amount=float(profile["Target_Amount"]),
        current_amount=float(profile["Current_Amount"]),
        years_to_goal=int(profile["Years_To_Goal"]),
        annual_contribution=float(profile["Annual_Contribution"]),
    )
    terminal_values: np.ndarray | None = None
    if portfolio_monthly_returns is None:
        assessment = goal_model.assess(annual_return=annual_return_decimal)
    else:
        monthly_returns = np.asarray(portfolio_monthly_returns, dtype=float)
        if monthly_returns.ndim != 1 or monthly_returns.size < 2 or not np.isfinite(monthly_returns).all():
            raise ValueError("portfolio_monthly_returns must be a finite one-dimensional series")
        if (monthly_returns <= -1.0).any():
            raise ValueError("portfolio_monthly_returns cannot contain a loss of 100% or more")
        annual_return_decimal = (1.0 + float(monthly_returns.mean())) ** 12 - 1.0
        terminal_values = _bootstrap_terminal_values(
            goal_model=goal_model,
            monthly_returns=monthly_returns,
        )
        assessment = goal_model.assess_terminal_values(terminal_values)
    annual_progress = [
        goal_model.current_amount
        if years_elapsed == 0
        else Goal_Based_Investing_Baseline(
            goal_name=goal_model.goal_name,
            target_amount=goal_model.target_amount,
            current_amount=goal_model.current_amount,
            years_to_goal=years_elapsed,
            annual_contribution=goal_model.annual_contribution,
        ).project_amount(annual_return=annual_return_decimal)
        for years_elapsed in range(goal_model.years_to_goal + 1)
    ]
    return {
        "Assessment": assessment,
        "Annual_Progress": annual_progress,
        "Years": list(range(goal_model.years_to_goal + 1)),
        "Terminal_Values": terminal_values,
    }


def _bootstrap_terminal_values(
    *,
    goal_model: Goal_Based_Investing_Baseline,
    monthly_returns: np.ndarray,
    scenario_count: int = 2_000,
    seed: int = 17,
) -> np.ndarray:
    """Create deterministic historical-bootstrap terminal values for one policy."""
    months = 12 * goal_model.years_to_goal
    values = np.full(scenario_count, goal_model.current_amount, dtype=float)
    if months == 0:
        return values
    sampled_returns = np.random.default_rng(seed).choice(
        monthly_returns,
        size=(scenario_count, months),
        replace=True,
    )
    monthly_contribution = goal_model.annual_contribution / 12.0
    for month in range(months):
        values = values * (1.0 + sampled_returns[:, month]) + monthly_contribution
    return values


def build_multistage_preview_state(
    *,
    financial_plan: Any,
    policy: Any,
    asset_returns: Any,
    return_periods: int = 3,
    branches: int = 2,
) -> dict[str, Any]:
    """Solve a deliberately small, no-discrete-goal MSMIP dashboard preview.

    The preview uses the client-selected policy's assets and risk band, staged
    client cash flows, and a historical-bootstrap tree.  P/NP discrete goals
    are deliberately omitted in Version 1, so this is an allocation and
    recurring-spending feasibility preview rather than a full goal-postponement
    screen.
    """
    import pyomo.environ as pyo

    portfolio = build_portfolio_specification_from_plan(
        financial_plan=financial_plan,
        policy=policy,
    )
    tree = historical_bootstrap_tree(
        asset_returns,
        assets=portfolio.assets,
        return_periods=return_periods,
        branches=branches,
        seed=29,
    )
    model = build_goal_postponement_model(tree, portfolio, ())
    result = pyo.SolverFactory("appsi_highs").solve(model)
    if not pyo.check_optimal_termination(result):
        raise ValueError(f"Multistage preview did not solve optimally: {result.solver.termination_condition}")
    leaves = tuple(node for node in tree.nodes if node.stage == return_periods + 1)
    root = tree.root.identifier
    root_total = sum(pyo.value(model.holdings[root, asset]) for asset in portfolio.assets)
    root_weights = {
        asset: pyo.value(model.holdings[root, asset]) / root_total
        for asset in portfolio.assets
        if pyo.value(model.holdings[root, asset]) > 1e-8
    }
    expected_terminal_wealth = sum(
        node.probability * sum(pyo.value(model.holdings[node.identifier, asset]) for asset in portfolio.assets)
        for node in leaves
    )
    expected_shortfall = {
        priority: sum(
            node.probability * pyo.value(model.spending_shortfall[node.identifier, priority])
            for node in tree.nodes
            if node.parent is not None
        )
        for priority in model.spending_priorities
    }
    return {
        "Return_Periods": return_periods,
        "Branches": branches,
        "Scenario_Nodes": len(tree.nodes),
        "Root_Weights": root_weights,
        "Expected_Terminal_Wealth": expected_terminal_wealth,
        "Expected_Priority_Shortfall": expected_shortfall,
    }


def build_goal_profile_from_client_data(
    *,
    manual_profile: dict[str, Any],
    personal_info: dict[str, Any],
    assets: dict[str, Any],
    goals: dict[str, Any],
    income: dict[str, Any],
) -> dict[str, Any]:
    """Apply only client fields with an unambiguous baseline-model mapping.

    Assets become the plan's current amount and current/retirement ages define
    the horizon.  The current Clients-tab goal and income fields describe
    annual retirement cash flows, not a one-time target or annual savings; we
    retain them as transparent plan context until the multistage model consumes
    them as goals and staged income.
    """
    profile = dict(manual_profile)
    profile["Current_Amount"] = _financial_total(assets)
    profile["Years_To_Goal"] = max(
        0,
        int(personal_info.get("age_retirement", 65)) - int(personal_info.get("age_current", 35)),
    )
    profile["Input_Source"] = "Clients Dashboard"
    profile["Client_Name"] = str(personal_info.get("name") or "Primary Client")
    profile["Risk_Profile"] = str(personal_info.get("tolerance_risk") or "Moderate")
    profile["Annual_Goal_Needs"] = _financial_total(goals)
    profile["Annual_Guaranteed_Income"] = _financial_total(income)
    profile["Annual_Retirement_Gap"] = max(
        0.0,
        profile["Annual_Goal_Needs"] - profile["Annual_Guaranteed_Income"],
    )
    profile["Annual_Goal_Priorities"] = {
        priority: max(0.0, float(goals.get(priority, 0.0)))
        for priority in ("essential", "important", "aspirational")
    }
    return profile


def build_goal_priority_cashflow_state(*, profile: dict[str, Any]) -> dict[str, Any]:
    """Evaluate priority spending against the selected policy's realised path."""
    portfolio_returns = profile.get("Portfolio_Monthly_Returns")
    if portfolio_returns is None:
        raise ValueError("A selected policy return path is required for cash-flow analysis")

    priorities = profile["Annual_Goal_Priorities"]
    result = backtest_goal_priority_cashflows(
        portfolio_returns,
        initial_wealth=float(profile["Confirmed_Plan_Assets"]),
        annual_essential=float(priorities["essential"]),
        annual_important=float(priorities["important"]),
        annual_aspirational=float(priorities["aspirational"]),
        annual_guaranteed_income=float(profile["Annual_Guaranteed_Income"]),
    )
    payment_rates = {
        "Essential": payment_rate(
            paid=result.essential_paid,
            expired=result.essential_shortfall,
        ),
        "Important": payment_rate(
            paid=result.important_paid,
            expired=result.important_expired,
            postponed=result.important_postponed,
        ),
        "Aspirational": payment_rate(
            paid=result.aspirational_paid,
            expired=result.aspirational_expired,
            postponed=result.aspirational_postponed,
        ),
    }
    return {
        "Result": result,
        "Payment_Rates": payment_rates,
        "Annual_Priorities": priorities,
    }


def _financial_total(values: dict[str, Any]) -> float:
    """Sum finite, non-negative dashboard amounts without trusting a total field."""
    total = 0.0
    for value in values.values():
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if number >= 0:
            total += number
    return total


def format_currency(*, amount: float) -> str:
    """Format a dollar amount for dashboard display."""
    return f"${amount:,.0f}"

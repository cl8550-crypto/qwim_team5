"""Shared state and pure calculation helpers for Goal-Based Investing."""

from __future__ import annotations

from typing import Any

from shiny import reactive

from src.models.goal_based_investing import Goal_Based_Investing_Baseline


GOAL_PROFILE_STATE_KEY = "Goal_Based_Investing_Profile"
GOAL_ASSESSMENT_STATE_KEY = "Goal_Based_Investing_Assessment"
GOAL_ASSESSMENT_ERROR_KEY = "Goal_Based_Investing_Assessment_Error"


def get_goal_based_investing_state(*, reactives_shiny: dict[str, Any]) -> dict[str, Any]:
    """Return the session-scoped reactive values used by both GBI subtabs."""
    inner_variables = reactives_shiny["Inner_Variables_Shiny"]
    state_keys = (
        GOAL_PROFILE_STATE_KEY,
        GOAL_ASSESSMENT_STATE_KEY,
        GOAL_ASSESSMENT_ERROR_KEY,
    )
    for state_key in state_keys:
        if state_key not in inner_variables:
            inner_variables[state_key] = reactive.Value(None)
    return {
        "Profile": inner_variables[GOAL_PROFILE_STATE_KEY],
        "Assessment": inner_variables[GOAL_ASSESSMENT_STATE_KEY],
        "Error": inner_variables[GOAL_ASSESSMENT_ERROR_KEY],
    }


def build_goal_assessment_state(*, profile: dict[str, Any]) -> dict[str, Any]:
    """Calculate one deterministic goal assessment and annual progress series."""
    annual_return_decimal = float(profile["Annual_Return_Percent"]) / 100.0
    goal_model = Goal_Based_Investing_Baseline(
        goal_name=str(profile["Goal_Name"]),
        target_amount=float(profile["Target_Amount"]),
        current_amount=float(profile["Current_Amount"]),
        years_to_goal=int(profile["Years_To_Goal"]),
        annual_contribution=float(profile["Annual_Contribution"]),
    )
    assessment = goal_model.assess(annual_return=annual_return_decimal)
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
    }


def format_currency(*, amount: float) -> str:
    """Format a dollar amount for dashboard display."""
    return f"${amount:,.0f}"

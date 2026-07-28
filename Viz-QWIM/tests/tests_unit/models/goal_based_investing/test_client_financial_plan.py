"""Tests for the Clients-to-goal-model financial-plan adapter."""

from __future__ import annotations

from src.models.goal_based_investing import (
    Income_Source_Specification,
    build_client_financial_plan,
    build_portfolio_specification_from_plan,
    load_predefined_cvar_policies,
)


def test_adapter_creates_contributions_then_retirement_income_and_spending() -> None:
    plan = build_client_financial_plan(
        risk_profile="Moderate",
        confirmed_plan_assets=300_000,
        current_age=60,
        retirement_age=65,
        income_start_age=65,
        annual_contribution=15_000,
        annual_goals={"essential": 50_000, "important": 8_000, "aspirational": 2_000},
        annual_income={"social_security": 30_000, "pension": 10_000, "annuity_existing": 0, "other": 0},
        horizon_periods=8,
    )
    assert plan.initial_wealth == 300_000
    assert plan.retirement_stage == 7
    assert plan.contribution_by_stage == {2: 15_000, 3: 15_000, 4: 15_000, 5: 15_000, 6: 15_000}
    assert plan.income_by_stage == {7: 40_000, 8: 40_000, 9: 40_000}
    assert plan.spending_by_stage == {7: 60_000, 8: 60_000, 9: 60_000}
    assert plan.spending_by_priority_stage["essential"] == {7: 50_000, 8: 50_000, 9: 50_000}
    assert plan.annual_retirement_gap == 20_000
    assert plan.income_by_source_stage["social_security"] == {7: 30_000, 8: 30_000, 9: 30_000}


def test_adapter_supports_periods_shorter_than_retirement_horizon() -> None:
    plan = build_client_financial_plan(
        risk_profile="Conservative",
        confirmed_plan_assets=100,
        current_age=40,
        retirement_age=65,
        income_start_age=65,
        annual_contribution=12,
        annual_goals={"essential": 0, "important": 0, "aspirational": 0},
        annual_income={"social_security": 0, "pension": 0, "annuity_existing": 0, "other": 0},
        horizon_periods=3,
    )
    assert plan.retirement_stage == 4
    assert plan.contribution_by_stage == {2: 12, 3: 12}
    assert plan.income_by_stage == {4: 0}
    assert plan.spending_by_stage == {4: 0}


def test_adapter_supports_source_specific_start_end_and_growth() -> None:
    plan = build_client_financial_plan(
        risk_profile="Moderate",
        confirmed_plan_assets=300_000,
        current_age=60,
        retirement_age=65,
        income_start_age=65,
        annual_contribution=0,
        annual_goals={"essential": 50_000, "important": 0, "aspirational": 0},
        annual_income={"social_security": 24_000, "pension": 12_000, "annuity_existing": 0, "other": 0},
        income_sources={
            "social_security": Income_Source_Specification(24_000, start_age=67, annual_growth_rate=0.02),
            "pension": Income_Source_Specification(12_000, start_age=65, end_age=66),
            "annuity_existing": Income_Source_Specification(0, start_age=65),
            "other": Income_Source_Specification(0, start_age=65),
        },
        horizon_periods=9,
    )

    assert plan.income_by_source_stage["pension"] == {7: 12_000, 8: 12_000}
    assert plan.income_by_source_stage["social_security"][9] == 24_000
    assert plan.income_by_source_stage["social_security"][10] == 24_480
    assert plan.income_by_stage[7] == 12_000
    assert plan.income_by_stage[9] == 24_000
    assert plan.annual_guaranteed_income == 12_000


def test_financial_plan_and_selected_risk_policy_build_msmip_portfolio_inputs() -> None:
    plan = build_client_financial_plan(
        risk_profile="Moderate",
        confirmed_plan_assets=300_000,
        current_age=60,
        retirement_age=65,
        income_start_age=65,
        annual_contribution=15_000,
        annual_goals={"essential": 50_000, "important": 8_000, "aspirational": 2_000},
        annual_income={"social_security": 30_000, "pension": 10_000, "annuity_existing": 0, "other": 0},
        horizon_periods=8,
    )
    policy = load_predefined_cvar_policies()["Moderate"]

    portfolio = build_portfolio_specification_from_plan(financial_plan=plan, policy=policy)

    assert portfolio.initial_wealth == 300_000
    assert portfolio.risky_assets == ("XLK", "XLP")
    assert portfolio.minimum_risky_weight == 0.40
    assert portfolio.maximum_risky_weight == 0.55
    assert portfolio.priority_spending[0].priority == "essential"
    assert portfolio.priority_spending[0].shortfall_penalty > portfolio.priority_spending[-1].shortfall_penalty

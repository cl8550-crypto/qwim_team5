"""Regression checks for the small-tree goal-postponement reference model."""

from __future__ import annotations

import pyomo.environ as pyo

from src.models.goal_based_investing import (
    Goal_Specification,
    Portfolio_Specification,
    Priority_Spending_Specification,
    Scenario_Node,
    Scenario_Tree,
    build_goal_postponement_model,
    fixed_date_comparator,
)


ASSETS = ("BIL", "XLK")


def _tree() -> Scenario_Tree:
    return Scenario_Tree((
        Scenario_Node("root", 1, None, 1.0, {}),
        Scenario_Node("up", 2, "root", 0.5, {"BIL": 1.0, "XLK": 1.1}),
        Scenario_Node("down", 2, "root", 0.5, {"BIL": 1.0, "XLK": 0.9}),
        Scenario_Node("up_up", 3, "up", 0.25, {"BIL": 1.0, "XLK": 1.1}),
        Scenario_Node("up_down", 3, "up", 0.25, {"BIL": 1.0, "XLK": 0.9}),
        Scenario_Node("down_up", 3, "down", 0.25, {"BIL": 1.0, "XLK": 1.1}),
        Scenario_Node("down_down", 3, "down", 0.25, {"BIL": 1.0, "XLK": 0.9}),
    ))


def _portfolio() -> Portfolio_Specification:
    return Portfolio_Specification(
        assets=ASSETS,
        cash_asset="BIL",
        initial_wealth=100.0,
        transaction_cost={"XLK": 0.0},
        max_weight={"XLK": 1.0},
        income_by_stage={},
    )


def test_tree_rejects_duplicate_siblings() -> None:
    duplicate_tree = Scenario_Tree((
        Scenario_Node("root", 1, None, 1.0, {}),
        Scenario_Node("a", 2, "root", 0.5, {"BIL": 1.0, "XLK": 1.0}),
        Scenario_Node("b", 2, "root", 0.5, {"BIL": 1.0, "XLK": 1.0}),
    ))
    try:
        duplicate_tree.validate(assets=ASSETS, branches=2)
    except ValueError as as_error:
        assert "duplicate siblings" in str(as_error)
    else:  # pragma: no cover - keeps assertion meaningful if validation regresses
        raise AssertionError("duplicate siblings must be rejected")


def test_postponement_is_no_worse_than_earliest_fixed_goal() -> None:
    goals = (Goal_Specification("purchase", 95.0, 100.0, (2, 3), postponable=True),)
    model = build_goal_postponement_model(_tree(), _portfolio(), goals)
    fixed_model = build_goal_postponement_model(
        _tree(), _portfolio(), fixed_date_comparator(goals, date="earliest"))
    solver = pyo.SolverFactory("appsi_highs")
    solver.solve(model)
    solver.solve(fixed_model)
    assert pyo.value(model.expected_utility) >= pyo.value(fixed_model.expected_utility) - 1e-9


def test_goal_completion_is_cumulative_on_each_path() -> None:
    goals = (Goal_Specification("purchase", 30.0, 100.0, (2, 3), postponable=True),)
    model = build_goal_postponement_model(_tree(), _portfolio(), goals)
    pyo.SolverFactory("appsi_highs").solve(model)
    for path in (("up", "up_up"), ("up", "up_down"), ("down", "down_up"), ("down", "down_down")):
        assert sum(round(pyo.value(model.fulfil[node, "purchase"])) for node in path) <= 1


def test_staged_contributions_income_and_spending_flow_through_cash_balance() -> None:
    portfolio = Portfolio_Specification(
        assets=ASSETS,
        cash_asset="BIL",
        initial_wealth=100.0,
        transaction_cost={"XLK": 0.0},
        max_weight={"XLK": 0.0},
        income_by_stage={2: 10.0},
        contribution_by_stage={2: 5.0},
        spending_by_stage={2: 7.0},
    )
    model = build_goal_postponement_model(_tree(), portfolio, ())
    pyo.SolverFactory("appsi_highs").solve(model)
    assert pyo.value(model.holdings["up", "BIL"]) == 108.0


def test_risk_profile_band_constrains_risky_weight_at_every_node() -> None:
    portfolio = Portfolio_Specification(
        assets=ASSETS,
        cash_asset="BIL",
        initial_wealth=100.0,
        transaction_cost={"XLK": 0.0},
        max_weight={"XLK": 1.0},
        income_by_stage={},
        risky_assets=("XLK",),
        minimum_risky_weight=0.20,
        maximum_risky_weight=0.40,
    )
    model = build_goal_postponement_model(_tree(), portfolio, ())
    pyo.SolverFactory("appsi_highs").solve(model)
    for node in ("root", "up", "down", "up_up", "up_down", "down_up", "down_down"):
        total = sum(pyo.value(model.holdings[node, asset]) for asset in ASSETS)
        risky_weight = pyo.value(model.holdings[node, "XLK"]) / total
        assert 0.20 - 1e-9 <= risky_weight <= 0.40 + 1e-9


def test_essential_recurring_spending_is_protected_before_aspirational_spending() -> None:
    portfolio = Portfolio_Specification(
        assets=ASSETS,
        cash_asset="BIL",
        initial_wealth=100.0,
        transaction_cost={"XLK": 0.0},
        max_weight={"XLK": 0.0},
        income_by_stage={},
        priority_spending=(
            Priority_Spending_Specification("essential", {2: 100.0}, shortfall_penalty=1_000.0),
            Priority_Spending_Specification("aspirational", {2: 100.0}, shortfall_penalty=10.0),
        ),
    )
    model = build_goal_postponement_model(_tree(), portfolio, ())
    pyo.SolverFactory("appsi_highs").solve(model)
    for node in ("up", "down"):
        assert pyo.value(model.spending_shortfall[node, "essential"]) == 0.0
        assert pyo.value(model.spending_shortfall[node, "aspirational"]) == 100.0

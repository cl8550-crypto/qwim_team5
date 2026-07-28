"""Exact small-tree MSMIP for goal-based investing with postponement.

This is the QWIM research implementation of Bae et al. (2024). A decision
belongs to a scenario-tree node, hence it uses only that node's return history.
The formulation is intentionally for small exact trees, providing a reference
implementation before scenario reduction or SDDiP is introduced.
"""

from __future__ import annotations

import math

from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Scenario_Node:  # noqa: N801
    """One scenario-tree node; all returns are positive gross returns."""

    identifier: str
    stage: int
    parent: str | None
    probability: float
    gross_returns: Mapping[str, float]


@dataclass(frozen=True, slots=True)
class Scenario_Tree:  # noqa: N801
    """A rooted non-recombining tree; root is deterministic paper stage 1."""

    nodes: tuple[Scenario_Node, ...]

    @property
    def root(self) -> Scenario_Node:
        roots = [node for node in self.nodes if node.parent is None]
        if len(roots) != 1:
            raise ValueError("Scenario tree must contain exactly one root")
        return roots[0]

    def validate(self, *, assets: tuple[str, ...], branches: int | None = None) -> None:
        root = self.root
        if root.stage != 1 or not math.isclose(root.probability, 1.0):
            raise ValueError("Root must be deterministic, probability-one paper stage 1")
        by_id = {node.identifier: node for node in self.nodes}
        if len(by_id) != len(self.nodes):
            raise ValueError("Scenario-node identifiers must be unique")
        children: dict[str, list[Scenario_Node]] = {}
        for node in self.nodes:
            if node.parent is None:
                continue
            parent = by_id.get(node.parent)
            if parent is None or node.stage != parent.stage + 1:
                raise ValueError(f"{node.identifier}: invalid parent or stage")
            if set(node.gross_returns) != set(assets) or any(value <= 0 for value in node.gross_returns.values()):
                raise ValueError(f"{node.identifier}: returns must be positive and cover all assets")
            children.setdefault(node.parent, []).append(node)
        for parent, siblings in children.items():
            if branches is not None and len(siblings) != branches:
                raise ValueError(f"{parent}: expected {branches} children")
            if not math.isclose(sum(node.probability for node in siblings), by_id[parent].probability, abs_tol=1e-10):
                raise ValueError(f"{parent}: child probabilities must sum to parent probability")
            signatures = [tuple(node.gross_returns[asset] for asset in assets) for node in siblings]
            if len(signatures) != len(set(signatures)):
                raise ValueError(f"{parent}: duplicate siblings are indistinguishable information sets")


@dataclass(frozen=True, slots=True)
class Goal_Specification:  # noqa: N801
    """An all-or-nothing goal with separately stored reference and allowed dates."""

    name: str
    base_cost: float
    base_utility: float
    attainable_stages: tuple[int, ...]
    postponable: bool = False
    inflation: float = 0.0
    time_preference: float = 0.0
    reference_stage: int | None = None

    def __post_init__(self) -> None:
        stages = self.attainable_stages
        if not self.name or not stages or tuple(sorted(set(stages))) != stages or stages[0] < 2:
            raise ValueError("attainable_stages must be sorted, unique, nonempty stages >= 2")
        if self.base_cost < 0 or self.base_utility < 0 or self.inflation < 0 or self.time_preference < 0:
            raise ValueError(f"{self.name}: cost, utility, inflation and time preference must be non-negative")
        reference = stages[0] if self.reference_stage is None else self.reference_stage
        if not isinstance(reference, int) or reference < 2 or reference > stages[0]:
            raise ValueError(f"{self.name}: reference stage must be no later than the first allowed stage")
        object.__setattr__(self, "reference_stage", reference)
        if self.postponable:
            if len(stages) < 2 or stages != tuple(range(stages[0], stages[-1] + 1)):
                raise ValueError(f"{self.name}: postponable goals require a consecutive window")
        elif len(stages) != 1:
            raise ValueError(f"{self.name}: non-postponable goals require one stage")

    def cost_at(self, stage: int) -> float:
        return self.base_cost * (1.0 + self.inflation) ** (stage - self.reference_stage)

    def utility_at(self, stage: int) -> float:
        return self.base_utility * (1.0 + self.time_preference) ** -(stage - self.reference_stage)


@dataclass(frozen=True, slots=True)
class Priority_Spending_Specification:  # noqa: N801
    """Recurring spending that may be short, with an explicit priority penalty."""

    priority: str
    amount_by_stage: Mapping[int, float]
    shortfall_penalty: float

    def __post_init__(self) -> None:
        if not self.priority.strip():
            raise ValueError("priority must not be empty")
        if not math.isfinite(self.shortfall_penalty) or self.shortfall_penalty <= 0:
            raise ValueError("shortfall_penalty must be finite and positive")
        if any(stage < 2 or not math.isfinite(amount) or amount < 0 for stage, amount in self.amount_by_stage.items()):
            raise ValueError("amount_by_stage requires non-negative spending at stages >= 2")


@dataclass(frozen=True, slots=True)
class Portfolio_Specification:  # noqa: N801
    """Investment inputs. Assets must list the selected cash proxy first."""

    assets: tuple[str, ...]
    cash_asset: str
    initial_wealth: float
    transaction_cost: Mapping[str, float]
    max_weight: Mapping[str, float]
    income_by_stage: Mapping[int, float]
    contribution_by_stage: Mapping[int, float] = field(default_factory=dict)
    spending_by_stage: Mapping[int, float] = field(default_factory=dict)
    risky_assets: tuple[str, ...] = ()
    minimum_risky_weight: float = 0.0
    maximum_risky_weight: float = 1.0
    priority_spending: tuple[Priority_Spending_Specification, ...] = ()

    def __post_init__(self) -> None:
        if not self.assets or self.assets[0] != self.cash_asset or len(set(self.assets)) != len(self.assets):
            raise ValueError("assets must be unique and start with cash_asset")
        if not math.isfinite(self.initial_wealth) or self.initial_wealth <= 0:
            raise ValueError("initial_wealth must be finite and positive")
        for asset in self.assets[1:]:
            cost, cap = self.transaction_cost.get(asset), self.max_weight.get(asset)
            if cost is None or cap is None or not 0 <= cost < 1 or not 0 <= cap <= 1:
                raise ValueError(f"{asset}: require transaction cost and cap in [0, 1]")
        for name, schedule in {
            "income_by_stage": self.income_by_stage,
            "contribution_by_stage": self.contribution_by_stage,
            "spending_by_stage": self.spending_by_stage,
        }.items():
            if any(stage < 2 or not math.isfinite(amount) or amount < 0 for stage, amount in schedule.items()):
                raise ValueError(f"{name} requires non-negative cash flows at stages >= 2")
        if len(set(self.risky_assets)) != len(self.risky_assets) or any(asset not in self.assets[1:] for asset in self.risky_assets):
            raise ValueError("risky_assets must be unique investable assets and cannot contain cash")
        if not 0 <= self.minimum_risky_weight <= self.maximum_risky_weight <= 1:
            raise ValueError("risky weights must satisfy 0 <= minimum <= maximum <= 1")
        if not self.risky_assets and (self.minimum_risky_weight != 0 or self.maximum_risky_weight != 1):
            raise ValueError("risky_assets is required when setting a non-default risky-weight band")
        if self.spending_by_stage and self.priority_spending:
            raise ValueError("use either spending_by_stage or priority_spending, not both")
        if len({item.priority for item in self.priority_spending}) != len(self.priority_spending):
            raise ValueError("priority_spending priorities must be unique")


def build_goal_postponement_model(tree: Scenario_Tree, portfolio: Portfolio_Specification, goals: tuple[Goal_Specification, ...]):
    """Build the deterministic-equivalent Pyomo MSMIP from Bae et al. (2024).

    It maximises expected time-adjusted goal utility. Terminal wealth remains
    an output rather than an objective component, matching the paper baseline.
    """
    try:
        import pyomo.environ as pyo
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise ModuleNotFoundError("Pyomo is required for the multistage goal model") from exc
    tree.validate(assets=portfolio.assets)
    goal_by_name = {goal.name: goal for goal in goals}
    if len(goal_by_name) != len(goals):
        raise ValueError("Goal names must be unique")
    if any(goal.attainable_stages[-1] > max(node.stage for node in tree.nodes) for goal in goals):
        raise ValueError("Each goal must lie within the scenario-tree horizon")
    cash, *risky = portfolio.assets
    by_id = {node.identifier: node for node in tree.nodes}
    root = tree.root.identifier
    decisions = tuple(node.identifier for node in tree.nodes if node.parent is not None)
    parent = {node: by_id[node].parent for node in decisions}
    stage = {node: by_id[node].stage for node in decisions}

    model = pyo.ConcreteModel("QWIM_goal_postponement")
    model.nodes = pyo.Set(initialize=tuple(by_id))
    model.decision_nodes = pyo.Set(initialize=decisions)
    model.assets = pyo.Set(initialize=portfolio.assets)
    model.risky_assets = pyo.Set(initialize=risky)
    model.goals = pyo.Set(initialize=tuple(goal_by_name))
    priority_spending = {item.priority: item for item in portfolio.priority_spending}
    model.spending_priorities = pyo.Set(initialize=tuple(priority_spending))
    model.holdings = pyo.Var(model.nodes, model.assets, domain=pyo.NonNegativeReals)
    model.initial_buy = pyo.Var(model.risky_assets, domain=pyo.NonNegativeReals)
    model.buy = pyo.Var(model.decision_nodes, model.risky_assets, domain=pyo.NonNegativeReals)
    model.sell = pyo.Var(model.decision_nodes, model.risky_assets, domain=pyo.NonNegativeReals)
    model.fulfil = pyo.Var(model.decision_nodes, model.goals, domain=pyo.Binary)
    model.completed = pyo.Var(model.decision_nodes, model.goals, domain=pyo.Binary)
    model.spending_shortfall = pyo.Var(model.decision_nodes, model.spending_priorities, domain=pyo.NonNegativeReals)
    model.root_cash = pyo.Constraint(expr=model.holdings[root, cash] == portfolio.initial_wealth - sum((1 + portfolio.transaction_cost[asset]) * model.initial_buy[asset] for asset in risky))
    model.root_risky = pyo.Constraint(model.risky_assets, rule=lambda m, asset: m.holdings[root, asset] == m.initial_buy[asset])
    model.root_cap = pyo.Constraint(model.risky_assets, rule=lambda m, asset: m.holdings[root, asset] <= portfolio.max_weight[asset] * sum(m.holdings[root, current] for current in m.assets))
    if portfolio.risky_assets:
        model.root_risky_weight_upper = pyo.Constraint(
            expr=sum(model.holdings[root, asset] for asset in portfolio.risky_assets)
            <= portfolio.maximum_risky_weight * sum(model.holdings[root, asset] for asset in portfolio.assets),
        )
        model.root_risky_weight_lower = pyo.Constraint(
            expr=sum(model.holdings[root, asset] for asset in portfolio.risky_assets)
            >= portfolio.minimum_risky_weight * sum(model.holdings[root, asset] for asset in portfolio.assets),
        )
    def cash_balance(m, node):
        current = by_id[node]
        purchases = sum((1 + portfolio.transaction_cost[asset]) * m.buy[node, asset] for asset in risky)
        sales = sum((1 - portfolio.transaction_cost[asset]) * m.sell[node, asset] for asset in risky)
        spending = sum(goal_by_name[goal].cost_at(stage[node]) * m.fulfil[node, goal] for goal in m.goals)
        recurring_spending = portfolio.spending_by_stage.get(stage[node], 0.0) + sum(
            priority_spending[priority].amount_by_stage.get(stage[node], 0.0) - m.spending_shortfall[node, priority]
            for priority in m.spending_priorities
        )
        contributions = portfolio.contribution_by_stage.get(stage[node], 0.0)
        income = portfolio.income_by_stage.get(stage[node], 0.0)
        return m.holdings[node, cash] == current.gross_returns[cash] * m.holdings[parent[node], cash] + income + contributions - recurring_spending - purchases + sales - spending
    model.cash_balance = pyo.Constraint(model.decision_nodes, rule=cash_balance)
    model.spending_shortfall_limit = pyo.Constraint(
        model.decision_nodes,
        model.spending_priorities,
        rule=lambda m, node, priority: m.spending_shortfall[node, priority]
        <= priority_spending[priority].amount_by_stage.get(stage[node], 0.0),
    )
    model.risky_balance = pyo.Constraint(model.decision_nodes, model.risky_assets, rule=lambda m, node, asset: m.holdings[node, asset] == by_id[node].gross_returns[asset] * m.holdings[parent[node], asset] + m.buy[node, asset] - m.sell[node, asset])
    model.allocation_cap = pyo.Constraint(model.decision_nodes, model.risky_assets, rule=lambda m, node, asset: m.holdings[node, asset] <= portfolio.max_weight[asset] * sum(m.holdings[node, current] for current in m.assets))
    if portfolio.risky_assets:
        model.risky_weight_upper = pyo.Constraint(
            model.decision_nodes,
            rule=lambda m, node: sum(m.holdings[node, asset] for asset in portfolio.risky_assets)
            <= portfolio.maximum_risky_weight * sum(m.holdings[node, asset] for asset in m.assets),
        )
        model.risky_weight_lower = pyo.Constraint(
            model.decision_nodes,
            rule=lambda m, node: sum(m.holdings[node, asset] for asset in portfolio.risky_assets)
            >= portfolio.minimum_risky_weight * sum(m.holdings[node, asset] for asset in m.assets),
        )
    model.eligibility = pyo.Constraint(model.decision_nodes, model.goals, rule=lambda m, node, goal: m.fulfil[node, goal] == 0 if stage[node] not in goal_by_name[goal].attainable_stages else pyo.Constraint.Skip)
    model.cumulative_completion = pyo.Constraint(model.decision_nodes, model.goals, rule=lambda m, node, goal: m.completed[node, goal] == (0 if parent[node] == root else m.completed[parent[node], goal]) + m.fulfil[node, goal])
    model.expected_utility = pyo.Objective(
        expr=sum(
            by_id[node].probability
            * (
                sum(goal_by_name[goal].utility_at(stage[node]) * model.fulfil[node, goal] for goal in model.goals)
                - sum(priority_spending[priority].shortfall_penalty * model.spending_shortfall[node, priority] for priority in model.spending_priorities)
            )
            for node in decisions
        ),
        sense=pyo.maximize,
    )
    return model


def fixed_date_comparator(goals: tuple[Goal_Specification, ...], *, date: str = "earliest") -> tuple[Goal_Specification, ...]:
    """Restrict P-goals to one date while preserving their original reference date."""
    if date not in {"earliest", "latest"}:
        raise ValueError("date must be 'earliest' or 'latest'")
    return tuple(Goal_Specification(goal.name, goal.base_cost, goal.base_utility, (goal.attainable_stages[0 if date == "earliest" else -1],), False, goal.inflation, goal.time_preference, goal.reference_stage) for goal in goals)

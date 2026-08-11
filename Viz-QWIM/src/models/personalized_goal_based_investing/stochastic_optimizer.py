"""Multi-stage stochastic goal programming (MSGP) optimizer.

Goal programming (Section 2.2, Figure 1) is implemented as a
loop over priority levels: level ``p`` solves a linear program keeping every
previous level's consumption as a hard lower bound, so strictly higher
priority goals can never be traded off against lower ones.

"""

from __future__ import annotations

from dataclasses import dataclass, field

import cvxpy as cp
import numpy as np

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
from .goals import GoalSet
from .scenario_tree import ScenarioTree


@dataclass
class MSGPConfig:
    """Tunable knobs for the MSGP solve, all optional beyond the base model.

    Parameters
    ----------
    stage_years : list[float]
        Cumulative elapsed years at each stage, length ``n_stages + 1``,
        ``stage_years[0] == 0``. Used for discounting.
    discount_rate : float
        Annual discount rate for the objective's present-value weighting
        (paper's ``d_{t,s}``, taken deterministic -- see module docstring).
    max_weight : float | np.ndarray | None
        Per-asset maximum allocation fraction (Table 1 Panel D uses 0.45).
    turnover_limit : float | None
        Max one-way turnover as a fraction of pre-trade wealth, per
        rebalance. ``None`` disables the constraint.
    txn_cost_buy, txn_cost_sell : float
        Proportional transaction costs (eq 31-32). Zero by default.
    portfolio_cvar : dict[int, tuple[float, float]]
        Stage -> ``(alpha, max_expected_loss_ratio)`` investment-risk CVaR
        constraints (eq 27-30), applied to every node at that stage that has
        children.
    solver : str
        cvxpy solver name. ``"CLARABEL"`` and ``"HIGHS"`` both handle this
        LP well; HIGHS is typically fastest for large sparse LPs.
    """

    stage_years: list[float]
    discount_rate: float = 0.0
    max_weight: float | np.ndarray | None = None
    turnover_limit: float | None = None
    txn_cost_buy: float = 0.0
    txn_cost_sell: float = 0.0
    portfolio_cvar: dict[int, tuple[float, float]] = field(default_factory=dict)
    solver: str = "CLARABEL"


@dataclass
class MSGPStepResult:
    """Solution of a single priority-level LP."""

    priority: int
    objective_value: float
    x: dict[int, np.ndarray]  # node_id -> final holdings (post-rebalance)
    buy: dict[int, np.ndarray]
    sell: dict[int, np.ndarray]
    consumption: dict[int, float]  # node_id -> c^p_{t,s} (0.0 for stage 0)
    solver_status: str

@dataclass
class EfficientFrontierContext:
    expected_returns: np.ndarray
    covariance: np.ndarray
    assets: list[str]

@dataclass
class MSGPResult:
    tree: ScenarioTree
    goal_set: GoalSet
    steps: dict[int, MSGPStepResult]
    efficient_frontier_context: EfficientFrontierContext | None = None

    @property
    def final(self) -> MSGPStepResult:
        """The last (lowest-priority, most complete) step's solution -- the recommended plan."""
        last_p = max(self.steps.keys())
        return self.steps[last_p]

    def weights_by_stage(self) -> dict[int, dict[int, np.ndarray]]:
        """Portfolio weights (fractions of wealth) per node, keyed by stage then node id."""
        out: dict[int, dict[int, np.ndarray]] = {}
        for nid, x in self.final.x.items():
            stage = self.tree.nodes[nid].stage
            total = x.sum()
            out.setdefault(stage, {})[nid] = x / total if total > 0 else x
        return out

    def terminal_wealth_distribution(self) -> tuple[np.ndarray, np.ndarray]:
        """Leaf terminal wealth values and their probabilities.

        Returns
        -------
        tuple[np.ndarray, np.ndarray]
            ``(wealth_values, probabilities)``, aligned arrays over all leaf
            nodes of the tree.
        """
        leaves = self.tree.leaves()
        wealth = np.array([self.final.x[nid].sum() for nid in leaves])
        probs = np.array([self.tree.nodes[nid].probability for nid in leaves])
        return wealth, probs


def _cumulative_inflation_factor(tree: ScenarioTree, node_id: int) -> float:
    """Product of ``(1 + inflation_rate)`` along the path from root to ``node_id``."""
    factor = 1.0
    for nid in tree.path_to_root(node_id)[1:]:  # skip root (no inflation applied)
        factor *= 1.0 + tree.nodes[nid].inflation_rate
    return factor


def _discount_factor(stage: int, stage_years: list[float], discount_rate: float) -> float:
    if discount_rate == 0.0:
        return 1.0
    return 1.0 / (1.0 + discount_rate) ** stage_years[stage]


class MSGPOptimizer:
    """Solves the multi-stage stochastic goal program on a scenario tree.

    Parameters
    ----------
    tree : ScenarioTree
        Node-indexed scenario tree from :func:`scenario_tree.build_scenario_tree`.
    goal_set : GoalSet
        Prioritized investor goals.
    config : MSGPConfig
        Solver and constraint configuration.
    """

    def __init__(self, tree: ScenarioTree, goal_set: GoalSet, config: MSGPConfig):
        self.tree = tree
        self.goal_set = goal_set
        self.config = config
        self.n_assets = len(tree.asset_names)
        self.investment_schedule = goal_set.investment_schedule(tree.n_stages)

        if len(config.stage_years) != tree.n_stages + 1:
            raise ValueError(
                f"stage_years must have length {tree.n_stages + 1}, got {len(config.stage_years)}."
            )

    def solve(self) -> MSGPResult:
        """Run the full sequential goal-programming procedure over all priority levels.

        Returns
        -------
        MSGPResult
        """
        goal_targets = self.goal_set.goal_targets_by_level(self.tree.n_stages)
        cvar_specs = self.goal_set.cvar_specs_by_level()

        all_nodes_ge1 = [
            nid for nid in self.tree.nodes if self.tree.nodes[nid].stage >= 1
        ]
        c_prev: dict[int, float] = {nid: 0.0 for nid in all_nodes_ge1}

        steps: dict[int, MSGPStepResult] = {}
        for p in self.goal_set.priority_levels:
            step = self._solve_priority_level(
                priority=p,
                goal_target=goal_targets[p],
                cvar_spec=cvar_specs.get(p, []),
                c_prev=c_prev,
            )
            steps[p] = step
            c_prev = dict(step.consumption)

        return MSGPResult(tree=self.tree, goal_set=self.goal_set, steps=steps)

    def _solve_priority_level(
        self,
        priority: int,
        goal_target: np.ndarray,
        cvar_spec: list[tuple[int, float, float]],
        c_prev: dict[int, float],
    ) -> MSGPStepResult:
        tree = self.tree
        cfg = self.config
        n_assets = self.n_assets

        x: dict[int, cp.Variable] = {}
        buy: dict[int, cp.Variable] = {}
        sell: dict[int, cp.Variable] = {}
        c: dict[int, cp.Variable] = {}
        constraints: list[cp.Constraint] = []

        # --- Stage 0 (root): allocation only, no consumption. ---
        root_id = tree.root_id
        x[root_id] = cp.Variable(n_assets, nonneg=True)
        buy[root_id] = cp.Variable(n_assets, nonneg=True)
        sell_cash0 = cp.Variable(nonneg=True)
        sell[root_id] = None  # stage 0 has no generalized sell vector

        constraints += stage0_allocation_constraints(
            x0=x[root_id],
            buy0=buy[root_id],
            sell_cash0=sell_cash0,
            initial_cash=self.goal_set.initial_wealth(),
            n_assets=n_assets,
        )
        if cfg.max_weight is not None:
            constraints += max_weight_constraints(x[root_id], cfg.max_weight)

        # --- Stages 1..T: allocation + consumption. ---
        for stage in range(1, tree.n_stages + 1):
            for nid in tree.nodes_at_stage(stage):
                node = tree.nodes[nid]
                parent_id = node.parent_id
                x_arrival = cp.multiply(1.0 + node.asset_return, x[parent_id])

                x[nid] = cp.Variable(n_assets, nonneg=True)
                buy[nid] = cp.Variable(n_assets, nonneg=True)
                sell[nid] = cp.Variable(n_assets, nonneg=True)
                c[nid] = cp.Variable(nonneg=True)

                contribution = float(self.investment_schedule[stage])
                constraints += rebalance_flow_constraints(
                    x_final=x[nid],
                    x_arrival=x_arrival,
                    buy=buy[nid],
                    sell=sell[nid],
                    contribution=contribution,
                    consumption=c[nid],
                    txn_cost_buy=cfg.txn_cost_buy,
                    txn_cost_sell=cfg.txn_cost_sell,
                )
                if cfg.max_weight is not None:
                    constraints += max_weight_constraints(x[nid], cfg.max_weight)
                if cfg.turnover_limit is not None:
                    reference_value = cp.sum(x_arrival)
                    constraints += turnover_constraint(
                        buy[nid], sell[nid], reference_value, cfg.turnover_limit
                    )

                inflation_factor = _cumulative_inflation_factor(tree, nid)
                inflated_goal = inflation_factor * float(goal_target[stage])
                constraints += goal_bound_constraints(
                    c=c[nid], c_prev=c_prev[nid], inflated_goal=inflated_goal
                )

        # --- Optional CVaR goal-shortfall protection (eq 25-26). ---
        for horizon_stage, alpha, shortfall_ratio in cvar_spec:
            stage_nodes = tree.nodes_at_stage(horizon_stage)
            if not stage_nodes:
                continue
            zeta = cp.Variable()
            loss = cp.Variable(len(stage_nodes), nonneg=True)
            node_probs = {nid: tree.nodes[nid].probability for nid in stage_nodes}
            inflated_goal_by_node = {
                nid: _cumulative_inflation_factor(tree, nid) * float(goal_target[horizon_stage])
                for nid in stage_nodes
            }
            consumption_map = {nid: c[nid] for nid in stage_nodes}
            c_prev_map = {nid: c_prev[nid] for nid in stage_nodes}
            constraints += cvar_goal_shortfall_constraints(
                zeta=zeta,
                loss=loss,
                consumption=consumption_map,
                c_prev=c_prev_map,
                node_probabilities=node_probs,
                inflated_goal=inflated_goal_by_node,
                alpha=alpha,
                shortfall_ratio=shortfall_ratio,
            )

        # --- Optional CVaR investment-risk protection (eq 27-30). ---
        for stage, (alpha, max_loss_ratio) in cfg.portfolio_cvar.items():
            nodes_at_stage = [nid for nid in ([root_id] if stage == 0 else tree.nodes_at_stage(stage))]
            for nid in nodes_at_stage:
                node = tree.nodes[nid]
                if not node.children_ids:
                    continue
                child_returns = np.array(
                    [tree.nodes[cid].asset_return for cid in node.children_ids]
                )
                parent_prob = node.probability
                child_probs = np.array(
                    [tree.nodes[cid].probability / parent_prob for cid in node.children_ids]
                )
                zeta_r = cp.Variable()
                loss_r = cp.Variable(len(node.children_ids), nonneg=True)
                constraints += cvar_portfolio_return_constraints(
                    zeta=zeta_r,
                    loss=loss_r,
                    x_node=x[nid],
                    child_returns=child_returns,
                    child_probabilities=child_probs,
                    alpha=alpha,
                    max_expected_loss_ratio=max_loss_ratio,
                )

        # --- Objective: maximize expected present value of consumption (eq 1/13). ---
        obj_terms = []
        for stage in range(1, tree.n_stages + 1):
            d_t = _discount_factor(stage, cfg.stage_years, cfg.discount_rate)
            for nid in tree.nodes_at_stage(stage):
                obj_terms.append(d_t * tree.nodes[nid].probability * c[nid])
        objective = cp.Maximize(cp.sum(cp.hstack(obj_terms)) if obj_terms else 0)

        problem = cp.Problem(objective, constraints)
        problem.solve(solver=cfg.solver)

        if problem.status not in ("optimal", "optimal_inaccurate"):
            raise RuntimeError(
                f"MSGP priority level {priority} solve failed with status '{problem.status}'."
            )

        x_val = {nid: np.asarray(var.value).clip(min=0) for nid, var in x.items()}
        buy_val = {nid: np.asarray(var.value).clip(min=0) for nid, var in buy.items()}
        sell_val = {
            nid: (np.asarray(var.value).clip(min=0) if var is not None else np.zeros(n_assets))
            for nid, var in sell.items()
        }
        consumption_val = {nid: float(var.value) for nid, var in c.items()}

        return MSGPStepResult(
            priority=priority,
            objective_value=float(problem.value),
            x=x_val,
            buy=buy_val,
            sell=sell_val,
            consumption=consumption_val,
            solver_status=problem.status,
        )

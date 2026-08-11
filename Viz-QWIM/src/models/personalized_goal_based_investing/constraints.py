"""Composable cvxpy constraint builders for the MSGP optimization.

Each function returns a list of ``cvxpy`` constraints for one node (or one
node's outgoing edges) of the scenario tree, so :mod:`stochastic_optimizer`
can assemble the full problem by looping over nodes and concatenating
constraint lists. Equation numbers referenced in docstrings are from Kim et
al. (2019).

All constraints here are linear (or, for CVaR, linear after the standard
Rockafellar-Uryasev / Krokhmal-Palmquist-Uryasev reformulation), preserving
the paper's claim that the model remains a linear program regardless of
which optional constraints are attached.
"""

from __future__ import annotations

import cvxpy as cp
import numpy as np


def stage0_allocation_constraints(
    x0: cp.Variable,
    buy0: cp.Variable,
    sell_cash0: cp.Variable,
    initial_cash: float,
    n_assets: int,
) -> list[cp.Constraint]:
    """Stage-0 allocation constraints (paper equations 16-18, generalized eq 4-6).

    Investor starts fully in cash (asset index 0). Cash funds purchases of
    all other assets; no selling of non-cash assets is possible at stage 0
    since none are yet held.

    Parameters
    ----------
    x0 : cp.Variable
        Final stage-0 holdings, shape ``(n_assets,)``.
    buy0 : cp.Variable
        Stage-0 purchase amounts, shape ``(n_assets,)`` (index 0 unused/zero).
    sell_cash0 : cp.Variable
        Scalar: amount of cash liquidated to fund purchases.
    initial_cash : float
        Total stage-0 wealth, all held in cash (``x_{1,0}^{\\rightarrow}``).
    n_assets : int
        Number of assets (cash = index 0).

    Returns
    -------
    list[cp.Constraint]
    """
    cons = [
        x0[0] == initial_cash - sell_cash0,
        x0[1:] == buy0[1:],
        sell_cash0 == cp.sum(buy0[1:]),
        buy0[0] == 0,
    ]
    return cons


def rebalance_flow_constraints(
    x_final: cp.Variable,
    x_arrival: cp.Expression,
    buy: cp.Variable,
    sell: cp.Variable,
    contribution: float,
    consumption: cp.Variable,
    txn_cost_buy: float = 0.0,
    txn_cost_sell: float = 0.0,
) -> list[cp.Constraint]:
    """Post-arrival rebalancing constraints for stage ``t > 0`` (eq 19-20, 31-32).

    Parameters
    ----------
    x_final : cp.Variable
        Final holdings at this node after this stage's trading, ``(n_assets,)``.
    x_arrival : cp.Expression
        Holdings *before* trading, i.e. the parent's holdings grown by this
        node's realized returns: ``(1 + r) * x_parent``.
    buy, sell : cp.Variable
        Purchase / sale amounts at this node, ``(n_assets,)``.
    contribution : float
        Additional investment ``I_t`` available at this stage.
    consumption : cp.Variable
        Scalar consumption ``c^p_{t,s}`` drawn at this node.
    txn_cost_buy, txn_cost_sell : float
        Proportional transaction costs ``delta+``, ``delta-`` (eq 31-32).
        Zero reduces exactly to the paper's frictionless eq 7-8.

    Returns
    -------
    list[cp.Constraint]
    """
    cons = [
        x_final == x_arrival + buy - sell,
        (1 - txn_cost_sell) * cp.sum(sell) - (1 + txn_cost_buy) * cp.sum(buy)
        == contribution - consumption,
    ]
    return cons


def nonnegativity_constraints(*variables: cp.Variable) -> list[cp.Constraint]:
    """Explicit non-negativity (eq 12/24); redundant if variables were declared nonneg."""
    return [v >= 0 for v in variables]


def max_weight_constraints(
    x_final: cp.Variable, max_weight: np.ndarray | float
) -> list[cp.Constraint]:
    """Per-asset maximum allocation as a fraction of total node wealth.

    Linearized as ``x_i <= max_weight_i * sum(x)`` (both sides linear in the
    decision vector, no division needed). Matches the paper's Table 1 Panel D
    (e.g. 45% cap per asset class).

    Parameters
    ----------
    x_final : cp.Variable
        Holdings vector at a node, ``(n_assets,)``.
    max_weight : np.ndarray | float
        Per-asset cap in ``[0, 1]``, scalar (applied to all) or vector.

    Returns
    -------
    list[cp.Constraint]
    """
    total = cp.sum(x_final)
    if np.isscalar(max_weight):
        return [x_final <= max_weight * total]
    max_weight = np.asarray(max_weight, dtype=float)
    return [x_final[i] <= max_weight[i] * total for i in range(len(max_weight))]


def turnover_constraint(
    buy: cp.Variable, sell: cp.Variable, reference_value: cp.Expression, max_turnover: float
) -> list[cp.Constraint]:
    """Cap gross (two-way) turnover as a fraction of node wealth.

    ``sum(buy) + sum(sell) <= max_turnover * reference_value``. Note this is
    *gross* turnover: fully liquidating and reinvesting the entire portfolio
    costs a value of 2.0 under this metric (1.0 of sells + 1.0 of buys), not
    1.0. Typical values therefore range 0 (no trading) to 2 (unrestricted
    full reallocation); values below ~1.0 forbid a complete portfolio
    overhaul in a single rebalance and can interact with tight CVaR
    downside-protection constraints that require decisive reallocation --
    if a solve becomes infeasible after adding a turnover cap, relaxing this
    limit is the first thing to check.
    """
    return [cp.sum(buy) + cp.sum(sell) <= max_turnover * reference_value]


def goal_bound_constraints(
    c: cp.Variable, c_prev: float | cp.Expression, inflated_goal: float
) -> list[cp.Constraint]:
    """Strict priority goal bounds (paper eq 14-15 / 2-3).

    ``c_prev <= c <= c_prev + inflated_goal``: consumption at this priority
    step can never fall below what previous (higher-priority) steps already
    guaranteed, and extra consumption beyond the current goal's inflated
    target adds no further utility at this step.
    """
    return [c >= c_prev, c <= c_prev + inflated_goal]


def cvar_goal_shortfall_constraints(
    zeta: cp.Variable,
    loss: cp.Variable,
    consumption: dict[int, cp.Variable],
    c_prev: dict[int, float],
    node_probabilities: dict[int, float],
    inflated_goal: dict[int, float],
    alpha: float,
    shortfall_ratio: float,
) -> list[cp.Constraint]:
    """CVaR downside protection on goal shortfall (eq 25-26).

    Constrains the average under-achievement of a goal in the worst
    ``(1-alpha)`` fraction of stage-``t`` scenarios to be within
    ``shortfall_ratio`` of the (inflation-adjusted) goal.

    Parameters
    ----------
    zeta : cp.Variable
        Scalar VaR auxiliary variable for this stage/goal.
    loss : cp.Variable
        Vector auxiliary variable, one entry per node, ordered to match
        ``consumption``'s keys. Pass a ``cp.Variable(len(consumption))``.
    consumption : dict[int, cp.Variable]
        Node id -> this step's consumption variable ``c^p_{t,s}``.
    c_prev : dict[int, float]
        Node id -> previous step's consumption level ``c^{p-1}_{t,s}``.
    node_probabilities : dict[int, float]
        Node id -> probability, renormalized to sum to 1 across this stage.
    inflated_goal : dict[int, float]
        Node id -> inflation-adjusted goal amount using that node's own
        (scenario-specific) cumulative inflation path -- more accurate than
        a single representative value when inflation is stochastic.
    alpha : float
        CVaR quantile level (e.g. 0.90).
    shortfall_ratio : float
        ``rho`` in equation (25).

    Returns
    -------
    list[cp.Constraint]
    """
    node_ids = list(consumption.keys())
    total_prob = sum(node_probabilities[n] for n in node_ids)
    probs = np.array([node_probabilities[n] / total_prob for n in node_ids])
    avg_goal = float(np.mean([inflated_goal[n] for n in node_ids]))

    cons = []
    for idx, nid in enumerate(node_ids):
        shortfall = inflated_goal[nid] - (consumption[nid] - c_prev[nid])
        cons.append(loss[idx] >= shortfall - zeta)
        cons.append(loss[idx] >= 0)
    cvar_expr = zeta + (1.0 / (1.0 - alpha)) * cp.sum(cp.multiply(probs, loss))
    cons.append(cvar_expr <= shortfall_ratio * avg_goal)
    return cons


def cvar_portfolio_return_constraints(
    zeta: cp.Variable,
    loss: cp.Variable,
    x_node: cp.Variable,
    child_returns: np.ndarray,
    child_probabilities: np.ndarray,
    alpha: float,
    max_expected_loss_ratio: float,
) -> list[cp.Constraint]:
    """CVaR downside protection on one-period portfolio return (eq 29-30).

    Constrains the average loss (negative return, in monetary units) across
    the worst ``(1-alpha)`` fraction of a node's children to be within
    ``max_expected_loss_ratio`` of the node's total wealth.

    Parameters
    ----------
    zeta : cp.Variable
        Scalar VaR auxiliary variable for this node.
    loss : cp.Variable
        Vector auxiliary variable, one entry per child, ``(n_children,)``.
    x_node : cp.Variable
        This node's final holdings (post-rebalance), ``(n_assets,)``.
    child_returns : np.ndarray
        Shape ``(n_children, n_assets)``, each child's realized return
        vector for the transition out of this node.
    child_probabilities : np.ndarray
        Conditional probabilities of each child given this node, summing to 1.
    alpha : float
        CVaR quantile level.
    max_expected_loss_ratio : float
        ``rho`` in equation (27); can be negative to require a positive
        worst-case average return.

    Returns
    -------
    list[cp.Constraint]
    """
    total_value = cp.sum(x_node)
    n_children = child_returns.shape[0]
    cons = []
    for k in range(n_children):
        node_loss = -(child_returns[k] @ x_node)
        cons.append(loss[k] >= node_loss - zeta)
        cons.append(loss[k] >= 0)
    cvar_expr = zeta + (1.0 / (1.0 - alpha)) * cp.sum(cp.multiply(child_probabilities, loss))
    cons.append(cvar_expr <= max_expected_loss_ratio * total_value)
    return cons

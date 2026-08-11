# """Plotly visualizations for the goal-based investing dashboard tab.

# All functions return a ``plotly.graph_objects.Figure``, matching the rest of
# the QWIM dashboard's plotting stack (see ``main_App.py``'s About modal,
# which lists Plotly as the visualization library), so these compose directly
# with ``shinywidgets.render_widget`` in a Shiny tab module.
# """

# from __future__ import annotations

# import cvxpy as cp
# import numpy as np
# import plotly.graph_objects as go

# from .goals import Goal, GoalSet
# from .performance import goal_success_probability, terminal_wealth_stats
# from .scenario_tree import ScenarioTree
# from .stochastic_optimizer import MSGPResult


# def plot_efficient_frontier(
#     mu: np.ndarray,
#     cov: np.ndarray,
#     asset_names: list[str],
#     max_weight: float | np.ndarray | None = None,
#     n_points: int = 40,
#     highlight_weights: np.ndarray | None = None,
#     highlight_label: str = "MSGP stage-0 allocation",
# ) -> go.Figure:
#     """Long-only, no-leverage mean-variance efficient frontier.

#     Solves, for a sweep of target returns, ``min w'Sigma w`` subject to
#     ``w'mu >= target``, ``sum(w) = 1``, ``w >= 0`` (and the same optional
#     ``max_weight`` cap used in the MSGP optimizer, for an apples-to-apples
#     comparison). Infeasible target returns (outside the achievable range
#     given the long-only/max-weight constraints) are silently skipped.

#     Parameters
#     ----------
#     mu : np.ndarray
#         Annualized expected returns, ``(n_assets,)``.
#     cov : np.ndarray
#         Annualized covariance, ``(n_assets, n_assets)``.
#     asset_names : list[str]
#         Asset labels for hover text.
#     max_weight : float | np.ndarray, optional
#         Same per-asset cap convention as :mod:`constraints`.
#     n_points : int
#         Number of frontier points to attempt.
#     highlight_weights : np.ndarray, optional
#         A specific portfolio (e.g. the MSGP stage-0 solution) to overlay as
#         a marker for context.
#     highlight_label : str
#         Legend label for the highlighted portfolio.

#     Returns
#     -------
#     go.Figure
#     """
#     n_assets = len(mu)
#     targets = np.linspace(mu.min(), mu.max(), n_points)

#     risks, rets, weights_list = [], [], []
#     for target in targets:
#         w = cp.Variable(n_assets, nonneg=True)
#         constraints_ = [cp.sum(w) == 1, w @ mu >= target]
#         if max_weight is not None:
#             if np.isscalar(max_weight):
#                 constraints_.append(w <= max_weight)
#             else:
#                 constraints_.append(w <= np.asarray(max_weight))
#         prob = cp.Problem(cp.Minimize(cp.quad_form(w, cov)), constraints_)
#         try:
#             prob.solve(solver="CLARABEL")
#         except cp.error.SolverError:
#             continue
#         if prob.status not in ("optimal", "optimal_inaccurate") or w.value is None:
#             continue
#         risks.append(float(np.sqrt(w.value @ cov @ w.value)))
#         rets.append(float(w.value @ mu))
#         weights_list.append(w.value.copy())

#     fig = go.Figure()
#     hover_text = [
#         "<br>".join(f"{name}: {wt:.1%}" for name, wt in zip(asset_names, w))
#         for w in weights_list
#     ]
#     fig.add_trace(
#         go.Scatter(
#             x=risks,
#             y=rets,
#             mode="lines+markers",
#             name="Efficient frontier",
#             text=hover_text,
#             hovertemplate="Risk: %{x:.2%}<br>Return: %{y:.2%}<br>%{text}<extra></extra>",
#         )
#     )

#     if highlight_weights is not None:
#         hw = np.asarray(highlight_weights)
#         hw_risk = float(np.sqrt(hw @ cov @ hw))
#         hw_ret = float(hw @ mu)
#         fig.add_trace(
#             go.Scatter(
#                 x=[hw_risk],
#                 y=[hw_ret],
#                 mode="markers",
#                 marker=dict(size=14, symbol="star", color="firebrick"),
#                 name=highlight_label,
#             )
#         )

#     fig.update_layout(
#         title="Efficient Frontier (long-only, no leverage)",
#         xaxis_title="Annualized volatility",
#         yaxis_title="Annualized expected return",
#         xaxis_tickformat=".1%",
#         yaxis_tickformat=".1%",
#         template="plotly_white",
#     )
#     return fig


# def plot_scenario_tree(tree: ScenarioTree, color_by: str = "probability") -> go.Figure:
#     """Diagram of the scenario tree structure.

#     Nodes are laid out with stage on the x-axis and a deterministic vertical
#     offset within each stage; edges connect parent to child. Node color
#     encodes either cumulative probability or (if available) total wealth --
#     controlled by ``color_by``.

#     Parameters
#     ----------
#     tree : ScenarioTree
#         The tree to visualize.
#     color_by : {"probability"}
#         Coloring scheme (currently only probability is supported; kept as a
#         parameter for forward compatibility with wealth-colored trees).

#     Returns
#     -------
#     go.Figure
#     """
#     positions: dict[int, tuple[float, float]] = {}
#     for stage in range(tree.n_stages + 1):
#         node_ids = tree.nodes_at_stage(stage)
#         n = len(node_ids)
#         for i, nid in enumerate(node_ids):
#             y = (i - (n - 1) / 2.0) if n > 1 else 0.0
#             positions[nid] = (float(stage), float(y))

#     edge_x, edge_y = [], []
#     for nid, node in tree.nodes.items():
#         if node.parent_id is None:
#             continue
#         x0, y0 = positions[node.parent_id]
#         x1, y1 = positions[nid]
#         edge_x += [x0, x1, None]
#         edge_y += [y0, y1, None]

#     node_x = [positions[nid][0] for nid in tree.nodes]
#     node_y = [positions[nid][1] for nid in tree.nodes]
#     node_color = [tree.nodes[nid].probability for nid in tree.nodes]
#     node_text = [
#         f"stage {tree.nodes[nid].stage}<br>P = {tree.nodes[nid].probability:.4f}"
#         for nid in tree.nodes
#     ]

#     fig = go.Figure()
#     fig.add_trace(
#         go.Scatter(x=edge_x, y=edge_y, mode="lines", line=dict(color="lightgray", width=1), hoverinfo="skip")
#     )
#     fig.add_trace(
#         go.Scatter(
#             x=node_x,
#             y=node_y,
#             mode="markers",
#             marker=dict(size=10, color=node_color, colorscale="Blues", showscale=True, colorbar=dict(title="Probability")),
#             text=node_text,
#             hovertemplate="%{text}<extra></extra>",
#         )
#     )
#     fig.update_layout(
#         title="Scenario Tree",
#         xaxis_title="Stage",
#         yaxis=dict(showticklabels=False),
#         template="plotly_white",
#         showlegend=False,
#     )
#     return fig


# def plot_allocation_over_time(result: MSGPResult) -> go.Figure:
#     """Stacked-area chart of probability-weighted average allocation by stage.

#     At each stage, averages post-rebalance weights across all nodes,
#     weighted by node probability -- matching the presentation style of the
#     paper's Figure 3.

#     Parameters
#     ----------
#     result : MSGPResult
#         A solved MSGP result (uses ``result.final``, the last priority
#         step's solution).

#     Returns
#     -------
#     go.Figure
#     """
#     tree = result.tree
#     asset_names = tree.asset_names
#     n_assets = len(asset_names)
#     stages = list(range(tree.n_stages + 1))

#     avg_weights = np.zeros((len(stages), n_assets))
#     for s_idx, stage in enumerate(stages):
#         total_prob = 0.0
#         weighted_sum = np.zeros(n_assets)
#         for nid in tree.nodes_at_stage(stage):
#             prob = tree.nodes[nid].probability
#             x = result.final.x[nid]
#             total = x.sum()
#             w = x / total if total > 0 else x
#             weighted_sum += prob * w
#             total_prob += prob
#         avg_weights[s_idx] = weighted_sum / total_prob if total_prob > 0 else weighted_sum

#     fig = go.Figure()
#     for i, name in enumerate(asset_names):
#         fig.add_trace(
#             go.Scatter(
#                 x=stages,
#                 y=avg_weights[:, i],
#                 mode="lines",
#                 stackgroup="one",
#                 name=name,
#                 hovertemplate=f"{name}: " + "%{y:.1%}<extra></extra>",
#             )
#         )
#     fig.update_layout(
#         title="Average Allocation by Stage (probability-weighted)",
#         xaxis_title="Stage",
#         yaxis_title="Portfolio weight",
#         yaxis_tickformat=".0%",
#         template="plotly_white",
#     )
#     return fig


# def plot_goal_probabilities(result: MSGPResult, goal_set: GoalSet) -> go.Figure:
#     """Bar chart of achievement probability for each goal, in priority order.

#     Mirrors the paper's Figure 5 (incremental goal achievement): shows how
#     each successively lower-priority goal's success probability compares,
#     given that higher-priority goals were never sacrificed for it.

#     Parameters
#     ----------
#     result : MSGPResult
#         Solved MSGP result covering all of ``goal_set``'s priority levels.
#     goal_set : GoalSet
#         The goals to report on.

#     Returns
#     -------
#     go.Figure
#     """
#     labels, probs = [], []
#     for p in goal_set.priority_levels:
#         for goal in goal_set.goals_at_level(p):
#             labels.append(f"P{p}: {goal.name}\n(stage {goal.horizon_stage})")
#             probs.append(goal_success_probability(result, goal))

#     fig = go.Figure(
#         go.Bar(
#             x=labels,
#             y=probs,
#             text=[f"{p:.0%}" for p in probs],
#             textposition="outside",
#             marker_color="steelblue",
#         )
#     )
#     fig.update_layout(
#         title="Goal Achievement Probability (by priority)",
#         yaxis_title="Probability of full achievement",
#         yaxis_tickformat=".0%",
#         yaxis_range=[0, 1.1],
#         template="plotly_white",
#     )
#     return fig


# def plot_terminal_wealth_distribution(result: MSGPResult, n_bins: int = 30) -> go.Figure:
#     """Probability-weighted histogram (fan-style summary) of terminal wealth.

#     Parameters
#     ----------
#     result : MSGPResult
#         Solved MSGP result.
#     n_bins : int
#         Number of histogram bins.

#     Returns
#     -------
#     go.Figure
#     """
#     wealth, probs = result.terminal_wealth_distribution()
#     stats = terminal_wealth_stats(wealth, probs)

#     fig = go.Figure()
#     fig.add_trace(
#         go.Histogram(
#             x=wealth,
#             y=probs,
#             histfunc="sum",
#             nbinsx=n_bins,
#             marker_color="seagreen",
#             name="Terminal wealth",
#         )
#     )
#     for stat_name, value, dash in [
#         ("Median", stats.median, "dash"),
#         ("P10", stats.p10, "dot"),
#         ("P90", stats.p90, "dot"),
#     ]:
#         fig.add_vline(
#             x=value,
#             line_dash=dash,
#             annotation_text=f"{stat_name}: {value:,.0f}",
#             annotation_position="top",
#         )

#     fig.update_layout(
#         title="Terminal Wealth Distribution",
#         xaxis_title="Terminal wealth",
#         yaxis_title="Probability mass",
#         template="plotly_white",
#     )
#     return fig

"""Plotly visualizations for the goal-based investing dashboard tab.

All functions return a ``plotly.graph_objects.Figure``, matching the rest of
the QWIM dashboard's plotting stack (see ``main_App.py``'s About modal,
which lists Plotly as the visualization library), so these compose directly
with ``shinywidgets.render_widget`` in a Shiny tab module.
"""

from __future__ import annotations

import cvxpy as cp
import numpy as np
import plotly.graph_objects as go

from .goals import Goal, GoalSet
from .performance import goal_success_probability, terminal_wealth_stats
from .scenario_tree import ScenarioTree
from .stochastic_optimizer import MSGPResult


def plot_efficient_frontier(
    mu: np.ndarray,
    cov: np.ndarray,
    asset_names: list[str],
    max_weight: float | np.ndarray | None = None,
    n_points: int = 40,
    highlight_weights: np.ndarray | None = None,
    highlight_label: str = "MSGP stage-0 allocation",
) -> go.Figure:
    """Long-only, no-leverage mean-variance efficient frontier.

    Solves, for a sweep of target returns, ``min w'Sigma w`` subject to
    ``w'mu >= target``, ``sum(w) = 1``, ``w >= 0`` (and the same optional
    ``max_weight`` cap used in the MSGP optimizer, for an apples-to-apples
    comparison). Infeasible target returns (outside the achievable range
    given the long-only/max-weight constraints) are silently skipped.

    Parameters
    ----------
    mu : np.ndarray
        Annualized expected returns, ``(n_assets,)``.
    cov : np.ndarray
        Annualized covariance, ``(n_assets, n_assets)``.
    asset_names : list[str]
        Asset labels for hover text.
    max_weight : float | np.ndarray, optional
        Same per-asset cap convention as :mod:`constraints`.
    n_points : int
        Number of frontier points to attempt.
    highlight_weights : np.ndarray, optional
        A specific portfolio (e.g. the MSGP stage-0 solution) to overlay as
        a marker for context.
    highlight_label : str
        Legend label for the highlighted portfolio.

    Returns
    -------
    go.Figure
    """
    n_assets = len(mu)
    targets = np.linspace(mu.min(), mu.max(), n_points)

    risks, rets, weights_list = [], [], []
    for target in targets:
        w = cp.Variable(n_assets, nonneg=True)
        constraints_ = [cp.sum(w) == 1, w @ mu >= target]
        if max_weight is not None:
            if np.isscalar(max_weight):
                constraints_.append(w <= max_weight)
            else:
                constraints_.append(w <= np.asarray(max_weight))
        prob = cp.Problem(cp.Minimize(cp.quad_form(w, cov)), constraints_)
        try:
            prob.solve(solver="CLARABEL")
        except cp.error.SolverError:
            continue
        if prob.status not in ("optimal", "optimal_inaccurate") or w.value is None:
            continue
        risks.append(float(np.sqrt(w.value @ cov @ w.value)))
        rets.append(float(w.value @ mu))
        weights_list.append(w.value.copy())

    fig = go.Figure()
    hover_text = [
        "<br>".join(f"{name}: {wt:.1%}" for name, wt in zip(asset_names, w))
        for w in weights_list
    ]
    fig.add_trace(
        go.Scatter(
            x=risks,
            y=rets,
            mode="lines+markers",
            name="Efficient frontier",
            text=hover_text,
            hovertemplate="Risk: %{x:.2%}<br>Return: %{y:.2%}<br>%{text}<extra></extra>",
        )
    )

    if highlight_weights is not None:
        hw = np.asarray(highlight_weights)
        hw_risk = float(np.sqrt(hw @ cov @ hw))
        hw_ret = float(hw @ mu)
        fig.add_trace(
            go.Scatter(
                x=[hw_risk],
                y=[hw_ret],
                mode="markers",
                marker=dict(size=14, symbol="star", color="firebrick"),
                name=highlight_label,
            )
        )

    fig.update_layout(
        title="Efficient Frontier (long-only, no leverage)",
        xaxis_title="Annualized volatility",
        yaxis_title="Annualized expected return",
        xaxis_tickformat=".1%",
        yaxis_tickformat=".1%",
        template="plotly_white",
    )
    return fig


def plot_scenario_tree(tree: ScenarioTree, color_by: str = "probability") -> go.Figure:
    """Diagram of the scenario tree structure.

    Nodes are laid out with stage on the x-axis and a deterministic vertical
    offset within each stage; edges connect parent to child. Node color
    encodes either cumulative probability or (if available) total wealth --
    controlled by ``color_by``.

    Parameters
    ----------
    tree : ScenarioTree
        The tree to visualize.
    color_by : {"probability"}
        Coloring scheme (currently only probability is supported; kept as a
        parameter for forward compatibility with wealth-colored trees).

    Returns
    -------
    go.Figure
    """
    positions: dict[int, tuple[float, float]] = {}
    for stage in range(tree.n_stages + 1):
        node_ids = tree.nodes_at_stage(stage)
        n = len(node_ids)
        for i, nid in enumerate(node_ids):
            y = (i - (n - 1) / 2.0) if n > 1 else 0.0
            positions[nid] = (float(stage), float(y))

    edge_x, edge_y = [], []
    for nid, node in tree.nodes.items():
        if node.parent_id is None:
            continue
        x0, y0 = positions[node.parent_id]
        x1, y1 = positions[nid]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    node_x = [positions[nid][0] for nid in tree.nodes]
    node_y = [positions[nid][1] for nid in tree.nodes]
    node_color = [tree.nodes[nid].probability for nid in tree.nodes]
    node_text = [
        f"stage {tree.nodes[nid].stage}<br>P = {tree.nodes[nid].probability:.4f}"
        for nid in tree.nodes
    ]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=edge_x, y=edge_y, mode="lines", line=dict(color="lightgray", width=1), hoverinfo="skip")
    )
    fig.add_trace(
        go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers",
            marker=dict(size=10, color=node_color, colorscale="Blues", showscale=True, colorbar=dict(title="Probability")),
            text=node_text,
            hovertemplate="%{text}<extra></extra>",
        )
    )
    fig.update_layout(
        title="Scenario Tree",
        xaxis_title="Stage",
        yaxis=dict(showticklabels=False),
        template="plotly_white",
        showlegend=False,
    )
    return fig


def plot_allocation_over_time(result: MSGPResult) -> go.Figure:
    """Stacked-area chart of probability-weighted average allocation by stage.

    At each stage, averages post-rebalance weights across all nodes,
    weighted by node probability -- matching the presentation style of the
    paper's Figure 3.

    Parameters
    ----------
    result : MSGPResult
        A solved MSGP result (uses ``result.final``, the last priority
        step's solution).

    Returns
    -------
    go.Figure
    """
    tree = result.tree
    asset_names = tree.asset_names
    n_assets = len(asset_names)
    stages = list(range(tree.n_stages + 1))

    avg_weights = np.zeros((len(stages), n_assets))
    for s_idx, stage in enumerate(stages):
        total_prob = 0.0
        weighted_sum = np.zeros(n_assets)
        for nid in tree.nodes_at_stage(stage):
            prob = tree.nodes[nid].probability
            x = result.final.x[nid]
            total = x.sum()
            w = x / total if total > 0 else x
            weighted_sum += prob * w
            total_prob += prob
        avg_weights[s_idx] = weighted_sum / total_prob if total_prob > 0 else weighted_sum

    fig = go.Figure()
    for i, name in enumerate(asset_names):
        display_name = name.replace("Sector_", "").replace("_", " ")
        fig.add_trace(
            go.Scatter(
                x=stages,
                y=avg_weights[:, i],
                mode="lines",
                stackgroup="one",
                name=display_name,
                hovertemplate=f"{display_name}: " + "%{y:.1%}<extra></extra>",
            )
        )
    fig.update_layout(
        title="Average Allocation by Stage (probability-weighted)",
        xaxis_title="Stage",
        yaxis_title="Portfolio weight",
        yaxis_tickformat=".0%",
        template="plotly_white",
    )
    return fig


def plot_goal_probabilities(result: MSGPResult, goal_set: GoalSet) -> go.Figure:
    """Bar chart of achievement probability for each goal, in priority order.

    Mirrors the paper's Figure 5 (incremental goal achievement): shows how
    each successively lower-priority goal's success probability compares,
    given that higher-priority goals were never sacrificed for it.

    Parameters
    ----------
    result : MSGPResult
        Solved MSGP result covering all of ``goal_set``'s priority levels.
    goal_set : GoalSet
        The goals to report on.

    Returns
    -------
    go.Figure
    """
    labels, probs = [], []
    for p in goal_set.priority_levels:
        for goal in goal_set.goals_at_level(p):
            labels.append(f"P{p}: {goal.name}\n(stage {goal.horizon_stage})")
            probs.append(goal_success_probability(result, goal))

    fig = go.Figure(
        go.Bar(
            x=labels,
            y=probs,
            text=[f"{p:.0%}" for p in probs],
            textposition="outside",
            marker_color="steelblue",
        )
    )
    fig.update_layout(
        title="Goal Achievement Probability (by priority)",
        yaxis_title="Probability of full achievement",
        yaxis_tickformat=".0%",
        yaxis_range=[0, 1.1],
        template="plotly_white",
    )
    return fig


def plot_terminal_wealth_distribution(result: MSGPResult, n_bins: int = 30) -> go.Figure:
    """Probability-weighted histogram (fan-style summary) of terminal wealth.

    Parameters
    ----------
    result : MSGPResult
        Solved MSGP result.
    n_bins : int
        Number of histogram bins.

    Returns
    -------
    go.Figure
    """
    wealth, probs = result.terminal_wealth_distribution()
    stats = terminal_wealth_stats(wealth, probs)

    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=wealth,
            y=probs,
            histfunc="sum",
            nbinsx=n_bins,
            marker_color="seagreen",
            name="Terminal wealth",
        )
    )
    for stat_name, value, dash in [
        ("Median", stats.median, "dash"),
        ("P10", stats.p10, "dot"),
        ("P90", stats.p90, "dot"),
    ]:
        fig.add_vline(
            x=value,
            line_dash=dash,
            annotation_text=f"{stat_name}: {value:,.0f}",
            annotation_position="top",
        )

    fig.update_layout(
        title="Terminal Wealth Distribution",
        xaxis_title="Terminal wealth",
        yaxis_title="Probability mass",
        template="plotly_white",
    )
    return fig
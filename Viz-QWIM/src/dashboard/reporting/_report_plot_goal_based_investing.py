"""Goal-based investing plot builders and exporters for the client PDF report.

Mirrors ``_report_plot_allocation.py``'s structure exactly: ``build_plotnine_*``
functions return a ``plotnine.ggplot`` or ``None``; ``export_plot_*`` functions
pull data from ``reactives_shiny``, build the chart, and save it as SVG via
the shared ``_save_plot`` helper from ``_report_plot_returns``.

The live dashboard tab (``tab_goals.py``) renders interactive Plotly figures
via ``goal_based_investing.visualization``; Typst cannot embed those (no JS
runtime), so this module is a **separate, static-chart implementation**
covering the same three results with plotnine instead. Keep both in sync by
hand if the underlying MSGPResult fields change shape.

Public API re-exported via ``report_plot_export``:
- ``build_plotnine_goal_based_investing_allocation``
- ``build_plotnine_goal_based_investing_goal_probabilities``
- ``build_plotnine_goal_based_investing_wealth_distribution``
- ``export_plot_goal_based_investing_allocation``
- ``export_plot_goal_based_investing_goal_probabilities``
- ``export_plot_goal_based_investing_wealth_distribution``
"""

from __future__ import annotations

from typing import Any

import pandas as pd  # pandas-boundary: plotnine requires pandas DataFrame input.

from plotnine import (
    aes,
    element_text,
    geom_area,
    geom_col,
    geom_histogram,
    geom_vline,
    ggplot,
    labs,
    theme,
)

from ._report_plot_returns import (
    _PALETTE,
    _QWIM_THEME,
    _get_inner_variables,
    _safe_reactive_get,
    _save_plot,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name = __name__)

#: Key under reactives_shiny["Inner_Variables_Shiny"] where tab_goals.py
#: mirrors the currently-selected goal_based_investing.MSGPResult, matching
#: the same runtime-mutation pattern subtab_goals.py uses for
#: User_Inputs_Shiny (see that module's observer_update_shared_reactives_shiny_goals).
GOAL_BASED_INVESTING_RESULT_KEY = "Goal_Based_Investing_Selected_Result"


# =========================================================================
# PLOTNINE BUILDER FUNCTIONS
# =========================================================================


def build_plotnine_goal_based_investing_allocation(*, result: Any) -> Any:
    """Build a stacked-area chart of average allocation by stage.

    Parameters
    ----------
    result : goal_based_investing.MSGPResult | None
        A solved MSGP result.

    Returns
    -------
    plotnine.ggplot | None
    """
    try:
        if result is None:
            return None

        tree = result.tree
        asset_names = tree.asset_names
        stages = list(range(tree.n_stages + 1))

        rows = []
        for stage in stages:
            total_prob = 0.0
            weighted = {name: 0.0 for name in asset_names}
            for nid in tree.nodes_at_stage(stage):
                prob = tree.nodes[nid].probability
                x = result.final.x[nid]
                total = x.sum()
                w = x / total if total > 0 else x
                for i, name in enumerate(asset_names):
                    weighted[name] += prob * w[i]
                total_prob += prob
            for name in asset_names:
                value = weighted[name] / total_prob if total_prob > 0 else weighted[name]
                rows.append({"stage": stage, "asset": name, "weight": value})

        if not rows:
            return None
        df = pd.DataFrame(rows)

        num_assets = len(asset_names)
        colors = (_PALETTE * ((num_assets // len(_PALETTE)) + 1))[:num_assets]

        return (
            ggplot(df, aes(x="stage", y="weight", fill="asset"))
            + geom_area(position="stack", alpha=0.85)
            + labs(
                title="Goal-Based Investing: Average Allocation by Stage",
                x="Stage",
                y="Weight",
                fill="Asset",
            )
            + _QWIM_THEME
        )
    except Exception as exc:  # noqa: BLE001  # pragma: no cover - report boundary tolerates heterogeneous plotting failures.
        _logger.warning("build_plotnine_goal_based_investing_allocation: %s", exc)
        return None


def build_plotnine_goal_based_investing_goal_probabilities(*, result: Any) -> Any:
    """Build a bar chart of achievement probability per goal, in priority order.

    Parameters
    ----------
    result : goal_based_investing.MSGPResult | None
        A solved MSGP result.

    Returns
    -------
    plotnine.ggplot | None
    """
    try:
        if result is None:
            return None
        from src.models.personalized_goal_based_investing.performance import goal_success_probability

        rows = []
        for p in result.goal_set.priority_levels:
            for goal in result.goal_set.goals_at_level(p):
                prob = goal_success_probability(result, goal)
                rows.append(
                    {
                        "goal": f"P{p}: {goal.name}",
                        "probability": prob,
                    }
                )
        if not rows:
            return None
        df = pd.DataFrame(rows)
        # Preserve priority order on the x-axis rather than plotnine's default
        # alphabetical sort of the categorical column.
        df["goal"] = pd.Categorical(df["goal"], categories=df["goal"].tolist(), ordered=True)

        return (
            ggplot(df, aes(x="goal", y="probability"))
            + geom_col(fill="#1d4ed8", alpha=0.85)
            + labs(
                title="Goal Achievement Probability (by priority)",
                x="Goal",
                y="Probability of full achievement",
            )
            + _QWIM_THEME
            + theme(axis_text_x=element_text(angle=30, hjust=1))
        )
    except Exception as exc:  # noqa: BLE001  # pragma: no cover - report boundary tolerates heterogeneous plotting failures.
        _logger.warning("build_plotnine_goal_based_investing_goal_probabilities: %s", exc)
        return None


def build_plotnine_goal_based_investing_wealth_distribution(*, result: Any) -> Any:
    """Build a probability-weighted histogram of terminal wealth.

    Parameters
    ----------
    result : goal_based_investing.MSGPResult | None
        A solved MSGP result.

    Returns
    -------
    plotnine.ggplot | None
    """
    try:
        if result is None:
            return None
        wealth, probs = result.terminal_wealth_distribution()
        if len(wealth) == 0:
            return None

        df = pd.DataFrame({"wealth": wealth, "probability": probs})
        median_wealth = float((df.sort_values("wealth")["wealth"]).median())

        return (
            ggplot(df, aes(x="wealth", weight="probability"))
            + geom_histogram(bins=30, fill="#0f766e", alpha=0.85)
            + geom_vline(xintercept=median_wealth, linetype="dashed", color="#b45309", size=0.7)
            + labs(
                title="Terminal Wealth Distribution",
                x="Terminal wealth",
                y="Probability mass",
            )
            + _QWIM_THEME
        )
    except Exception as exc:  # noqa: BLE001  # pragma: no cover - report boundary tolerates heterogeneous plotting failures.
        _logger.warning("build_plotnine_goal_based_investing_wealth_distribution: %s", exc)
        return None


# =========================================================================
# EXPORT FUNCTIONS
# =========================================================================


def _get_selected_goal_based_investing_result(*, reactives_shiny: dict | None) -> Any:
    """Fetch the currently-selected MSGPResult mirrored by tab_goals.py, or None."""
    inner = _get_inner_variables(reactives_shiny = reactives_shiny)
    return _safe_reactive_get(reactive_value = inner.get(GOAL_BASED_INVESTING_RESULT_KEY))


def export_plot_goal_based_investing_allocation(*, reactives_shiny: dict | None) -> Any:
    """Render the goal-based investing allocation-by-stage chart as SVG."""
    result = _get_selected_goal_based_investing_result(reactives_shiny = reactives_shiny)
    p = build_plotnine_goal_based_investing_allocation(result = result)
    if p is None:
        return None
    return _save_plot(plot = p, filename = "chart_goal_based_investing_allocation_by_stage.svg")


def export_plot_goal_based_investing_goal_probabilities(*, reactives_shiny: dict | None) -> Any:
    """Render the goal achievement probability chart as SVG."""
    result = _get_selected_goal_based_investing_result(reactives_shiny = reactives_shiny)
    p = build_plotnine_goal_based_investing_goal_probabilities(result = result)
    if p is None:
        return None
    return _save_plot(plot = p, filename = "chart_goal_based_investing_goal_probabilities.svg")


def export_plot_goal_based_investing_wealth_distribution(*, reactives_shiny: dict | None) -> Any:
    """Render the terminal wealth distribution chart as SVG."""
    result = _get_selected_goal_based_investing_result(reactives_shiny = reactives_shiny)
    p = build_plotnine_goal_based_investing_wealth_distribution(result = result)
    if p is None:
        return None
    return _save_plot(
        plot = p, filename = "chart_goal_based_investing_wealth_distribution.svg"
    )

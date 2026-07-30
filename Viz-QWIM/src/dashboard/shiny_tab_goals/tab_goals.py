"""Goal-Based Investing Tab Module.

Read-only dashboard tab presenting precomputed multi-stage stochastic goal
programming (MSGP) plans -- see ``src/models/personalized_goal_based_investing`` for the
optimizer itself. This tab does **not** solve anything live in the Shiny
session; it selects and renders a plan that was solved offline.

Integration contract
---------------------
This tab expects ``data_inputs`` to contain a key
``"personalized_goal_based_investing_Results"`` mapping a client/plan label (str) to an
already-solved ``personalized_goal_based_investing.MSGPResult`` object, e.g.:

```python
import pickle
from personalized_goal_based_investing import MSGPResult

data_inputs["personalized_goal_based_investing_Results"] = {
    "Jane Doe - Retirement Plan": pickled_result_1,
    "John Smith - Retirement Plan": pickled_result_2,
}
```

``MSGPResult`` is picklable (it only holds numpy arrays, the
``ScenarioTree``, and the ``GoalSet`` -- no live ``cvxpy`` variables survive
``MSGPOptimizer.solve()``), so the natural offline workflow is: run
``MSGPOptimizer(...).solve()`` in a batch/notebook job per client, pickle the
``MSGPResult``, and load the pickles into this dict at dashboard startup
inside ``get_data_inputs()``. Optionally, a matching
``"personalized_goal_based_investing_Benchmarks"`` key can map the same labels to a dict
of benchmark ``WealthPath`` objects (e.g. ``{"60/40": wealth_path, ...}``)
from ``portfolio_simulator.simulate_fixed_weight_benchmark`` for the
tracking-error KPI; this is optional and the tab degrades gracefully without
it.

If ``"personalized_goal_based_investing_Results"`` is missing or empty, the tab renders a
placeholder message instead of erroring, so the dashboard still boots before
any client plans have been computed.
"""

from __future__ import annotations

import typing

from typing import Any

from shiny import module, reactive, render, ui
from shinywidgets import output_widget, render_widget

from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

#: Module-level logger instance
_logger = get_logger(name=__name__)

RESULTS_KEY = "personalized_goal_based_investing_Results"
BENCHMARKS_KEY = "personalized_goal_based_investing_Benchmarks"


# =============================================================================
# UI Components
# =============================================================================


@module.ui
def tab_goals_ui(*, data_utils: dict, data_inputs: dict) -> Any:  # pragma: no cover
    """Create the UI for the Goal-Based Investing tab.

    Builds a client/plan selector plus four read-only result panels
    (Overview, Allocation, Goal Achievement, Wealth Distribution). All panel
    content is rendered server-side from whichever precomputed
    ``MSGPResult`` the user selects -- no inputs here trigger a solve.

    Parameters
    ----------
    data_utils : dict
        Shared dashboard utility/configuration dict (unused directly here,
        accepted for signature consistency with other tabs).
    data_inputs : dict
        Must contain ``RESULTS_KEY`` (see module docstring) for the selector
        to be populated; an empty/missing key still renders a valid (if
        empty) UI.

    Returns
    -------
    Any
        A Shiny ``navset_tab`` matching the layout convention used by
        ``tab_portfolios_ui`` / ``tab_clients_ui``.
    """
    results = data_inputs.get(RESULTS_KEY, {})
    plan_choices = list(results.keys())

    selector = ui.input_select(
        "input_ID_goals_plan_select",
        "Client / Goal Plan",
        choices=plan_choices,
        selected=plan_choices[0] if plan_choices else None,
    )

    if not plan_choices:
        empty_state = ui.card(
            ui.card_header("No goal-based plans available"),
            ui.p(
                "No precomputed goal-based investing results were found. "
                "Solve an MSGPResult offline (see this module's docstring) "
                "and register it under data_inputs['personalized_goal_based_investing_Results']."
            ),
        )
        return ui.div(selector, empty_state)

    tab_panels = [
        ui.nav_panel("Overview", _overview_panel_ui()),
        ui.nav_panel("Allocation", _allocation_panel_ui()),
        ui.nav_panel("Goal Achievement", _goal_achievement_panel_ui()),
        ui.nav_panel("Wealth Distribution", _wealth_distribution_panel_ui()),
    ]

    return ui.div(
        selector,
        ui.navset_tab(*tab_panels, id="ID_tab_goals_tabs_all"),
    )


def _overview_panel_ui() -> Any:
    """KPI summary cards plus the raw goal table for the selected plan."""
    return ui.div(
        ui.layout_columns(
            ui.value_box("Terminal Wealth (mean)", ui.output_text("output_ID_kpi_mean_wealth")),
            ui.value_box("Terminal Wealth (median)", ui.output_text("output_ID_kpi_median_wealth")),
            ui.value_box("Top-Priority Goal Success", ui.output_text("output_ID_kpi_top_goal_prob")),
            ui.value_box("Solver Status", ui.output_text("output_ID_kpi_solver_status")),
            col_widths=[3, 3, 3, 3],
        ),
        ui.card(
            ui.card_header("Goals (priority order)"),
            ui.output_table("output_ID_goal_table"),
        ),
    )


def _allocation_panel_ui() -> Any:
    """Average allocation over time and the plan's efficient frontier."""
    return ui.div(
        ui.card(ui.card_header("Average Allocation by Stage"), output_widget("output_ID_allocation_plot")),
        ui.card(
            ui.card_header("Efficient Frontier (context, not a live optimizer)"),
            ui.p(
                "Requires per-stage expected returns/covariance to be stored "
                "alongside the result; see this tab's server code if this panel "
                "is blank.",
                class_="text-muted small",
            ),
            output_widget("output_ID_frontier_plot"),
        ),
    )


def _goal_achievement_panel_ui() -> Any:
    return ui.card(
        ui.card_header("Goal Achievement Probability"),
        output_widget("output_ID_goal_prob_plot"),
    )


def _wealth_distribution_panel_ui() -> Any:
    return ui.div(
        ui.card(ui.card_header("Terminal Wealth Distribution"), output_widget("output_ID_wealth_dist_plot")),
        ui.card(ui.card_header("Scenario Tree"), output_widget("output_ID_scenario_tree_plot")),
    )


# =============================================================================
# Server Logic
# =============================================================================


@module.server
def tab_goals_server(  # pragma: no cover
    input: typing.Any,
    output: typing.Any,
    session: typing.Any,
    data_utils: dict,
    data_inputs: dict,
    reactives_shiny: dict,
) -> dict | None:
    """Server logic for the Goal-Based Investing tab.

    Every render function below is a pure read of the currently selected
    ``MSGPResult`` -- there is no optimizer call anywhere in this function.
    If a future version needs an interactive "edit and re-solve" mode, that
    is a materially different (and heavier) server and should be a separate
    tab or an explicit opt-in panel, not bolted onto this one.

    Parameters
    ----------
    input, output, session : Any
        Standard Shiny module server arguments.
    data_utils : dict
        Shared dashboard configuration (unused here).
    data_inputs : dict
        Must contain ``RESULTS_KEY``; see module docstring for the contract.
    reactives_shiny : dict
        Shared cross-tab reactive state (unused here; accepted for signature
        consistency with other tabs).

    Returns
    -------
    dict | None
        Empty dict (no child sub-servers to expose), for signature
        consistency with the dict-returning pattern used elsewhere.
    """
    results: dict[str, Any] = data_inputs.get(RESULTS_KEY, {})
    benchmarks: dict[str, dict[str, Any]] = data_inputs.get(BENCHMARKS_KEY, {})

    if not results:
        _logger.warning("No goal-based investing results registered; tab_goals server has nothing to render.")
        return {}

    @reactive.calc
    def selected_result():
        label = input.input_ID_goals_plan_select()
        if label not in results:
            _logger.error("Selected plan '%s' not found in registered results.", label)
            return None
        return results[label]

    @reactive.effect
    def observer_mirror_selected_result_to_reactives_shiny() -> None:
        """Mirror the selected plan into shared reactive state for the report pipeline.

        The client-report exporters (report_plot_export /
        _report_plot_personalized_goal_based_investing.py) read this exact key --
        reactives_shiny["Inner_Variables_Shiny"]["personalized_goal_based_investing_Selected_Result"]
        -- via the same _get_inner_variables()/_safe_reactive_get() pattern
        used for every other tab's report data. Without this, "Generate PDF
        Report" would have no way to find which plan is currently selected.
        """
        if not reactives_shiny or not isinstance(reactives_shiny, dict):
            return
        inner = reactives_shiny.get("Inner_Variables_Shiny")
        if inner is None or not isinstance(inner, dict):
            return

        from src.dashboard.reporting._report_plot_goal_based_investing import (
            personalized_goal_based_investing_RESULT_KEY,
        )

        current = selected_result()
        existing_rv = inner.get(personalized_goal_based_investing_RESULT_KEY)
        if existing_rv is not None and hasattr(existing_rv, "set"):
            existing_rv.set(current)
        else:
            inner[personalized_goal_based_investing_RESULT_KEY] = reactive.Value(current)

    # --- Overview KPIs ---

    @render.text
    def output_ID_kpi_mean_wealth():
        result = selected_result()
        if result is None:
            return "n/a"
        from src.models.personalized_goal_based_investing.performance import terminal_wealth_stats

        wealth, probs = result.terminal_wealth_distribution()
        stats = terminal_wealth_stats(wealth, probs)
        return f"${stats.mean:,.0f}"

    @render.text
    def output_ID_kpi_median_wealth():
        result = selected_result()
        if result is None:
            return "n/a"
        from src.models.personalized_goal_based_investing.performance import terminal_wealth_stats

        wealth, probs = result.terminal_wealth_distribution()
        stats = terminal_wealth_stats(wealth, probs)
        return f"${stats.median:,.0f}"

    @render.text
    def output_ID_kpi_top_goal_prob():
        result = selected_result()
        if result is None:
            return "n/a"
        from src.models.personalized_goal_based_investing.performance import goal_success_probability

        top_priority = min(result.goal_set.priority_levels)
        top_goal = result.goal_set.goals_at_level(top_priority)[0]
        try:
            prob = goal_success_probability(result, top_goal)
        except ValueError:
            return "n/a"
        return f"{prob:.0%}"

    @render.text
    def output_ID_kpi_solver_status():
        result = selected_result()
        if result is None:
            return "n/a"
        return result.final.solver_status

    @render.table
    def output_ID_goal_table():
        result = selected_result()
        if result is None:
            return None
        import pandas as pd

        rows = []
        for p in result.goal_set.priority_levels:
            for g in result.goal_set.goals_at_level(p):
                rows.append(
                    {
                        "Priority": g.priority,
                        "Goal": g.name,
                        "Stage": g.horizon_stage,
                        "Target": f"${g.target_wealth:,.0f}",
                    }
                )
        return pd.DataFrame(rows)

    # --- Allocation panel ---

    @render_widget
    def output_ID_allocation_plot():
        result = selected_result()
        if result is None:
            return None
        from src.models.personalized_goal_based_investing.visualization import plot_allocation_over_time

        return plot_allocation_over_time(result)

    @render_widget
    def output_ID_frontier_plot():
        result = selected_result()
        if result is None:
            return None
        mu = getattr(result, "stage0_expected_returns", None)
        cov = getattr(result, "stage0_covariance", None)
        if mu is None or cov is None:
            return None  # graceful: frontier needs mu/cov, not always attached to a result
        from src.models.personalized_goal_based_investing.visualization import plot_efficient_frontier

        stage0_x = result.final.x[result.tree.root_id]
        return plot_efficient_frontier(
            mu, cov, result.tree.asset_names, highlight_weights=stage0_x / stage0_x.sum()
        )

    # --- Goal achievement panel ---

    @render_widget
    def output_ID_goal_prob_plot():
        result = selected_result()
        if result is None:
            return None
        from src.models.personalized_goal_based_investing.visualization import plot_goal_probabilities

        return plot_goal_probabilities(result, result.goal_set)

    # --- Wealth distribution panel ---

    @render_widget
    def output_ID_wealth_dist_plot():
        result = selected_result()
        if result is None:
            return None
        from src.models.personalized_goal_based_investing.visualization import plot_terminal_wealth_distribution

        return plot_terminal_wealth_distribution(result)

    @render_widget
    def output_ID_scenario_tree_plot():
        result = selected_result()
        if result is None:
            return None
        from src.models.personalized_goal_based_investing.visualization import plot_scenario_tree

        return plot_scenario_tree(result.tree)

    return {}
# """Goal-Based Investing Tab Module.

# Read-only dashboard tab presenting precomputed multi-stage stochastic goal
# programming (MSGP) plans -- see ``src/models/personalized_goal_based_investing`` for the
# optimizer itself. This tab does **not** solve anything live in the Shiny
# session; it selects and renders a plan that was solved offline.

# Integration contract
# ---------------------
# This tab expects ``data_inputs`` to contain a key
# ``"personalized_goal_based_investing_Results"`` mapping a client/plan label (str) to an
# already-solved ``personalized_goal_based_investing.MSGPResult`` object, e.g.:

# ```python
# import pickle
# from personalized_goal_based_investing import MSGPResult

# data_inputs["personalized_goal_based_investing_Results"] = {
#     "Jane Doe - Retirement Plan": pickled_result_1,
#     "John Smith - Retirement Plan": pickled_result_2,
# }
# ```

# ``MSGPResult`` is picklable (it only holds numpy arrays, the
# ``ScenarioTree``, and the ``GoalSet`` -- no live ``cvxpy`` variables survive
# ``MSGPOptimizer.solve()``), so the natural offline workflow is: run
# ``MSGPOptimizer(...).solve()`` in a batch/notebook job per client, pickle the
# ``MSGPResult``, and load the pickles into this dict at dashboard startup
# inside ``get_data_inputs()``. Optionally, a matching
# ``"personalized_goal_based_investing_Benchmarks"`` key can map the same labels to a dict
# of benchmark ``WealthPath`` objects (e.g. ``{"60/40": wealth_path, ...}``)
# from ``portfolio_simulator.simulate_fixed_weight_benchmark`` for the
# tracking-error KPI; this is optional and the tab degrades gracefully without
# it.

# If ``"personalized_goal_based_investing_Results"`` is missing or empty, the tab renders a
# placeholder message instead of erroring, so the dashboard still boots before
# any client plans have been computed.
# """

# from __future__ import annotations

# import typing

# from typing import Any

# from shiny import module, reactive, render, ui
# from shinywidgets import output_widget, render_widget

# from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

# #: Module-level logger instance
# _logger = get_logger(name=__name__)

# RESULTS_KEY = "personalized_goal_based_investing_Results"
# BENCHMARKS_KEY = "personalized_goal_based_investing_Benchmarks"


# # =============================================================================
# # UI Components
# # =============================================================================


# @module.ui
# def tab_goals_ui(*, data_utils: dict, data_inputs: dict) -> Any:  # pragma: no cover
#     """Create the UI for the Goal-Based Investing tab.

#     Builds a client/plan selector plus four read-only result panels
#     (Overview, Allocation, Goal Achievement, Wealth Distribution). All panel
#     content is rendered server-side from whichever precomputed
#     ``MSGPResult`` the user selects -- no inputs here trigger a solve.

#     Parameters
#     ----------
#     data_utils : dict
#         Shared dashboard utility/configuration dict (unused directly here,
#         accepted for signature consistency with other tabs).
#     data_inputs : dict
#         Must contain ``RESULTS_KEY`` (see module docstring) for the selector
#         to be populated; an empty/missing key still renders a valid (if
#         empty) UI.

#     Returns
#     -------
#     Any
#         A Shiny ``navset_tab`` matching the layout convention used by
#         ``tab_portfolios_ui`` / ``tab_clients_ui``.
#     """
#     results = data_inputs.get(RESULTS_KEY, {})
#     plan_choices = list(results.keys())

#     selector = ui.input_select(
#         "input_ID_goals_plan_select",
#         "Client / Goal Plan",
#         choices=plan_choices,
#         selected=plan_choices[0] if plan_choices else None,
#     )

#     if not plan_choices:
#         empty_state = ui.card(
#             ui.card_header("No goal-based plans available"),
#             ui.p(
#                 "No precomputed goal-based investing results were found. "
#                 "Solve an MSGPResult offline (see this module's docstring) "
#                 "and register it under data_inputs['personalized_goal_based_investing_Results']."
#             ),
#         )
#         return ui.div(selector, empty_state)

#     tab_panels = [
#         ui.nav_panel("Overview", _overview_panel_ui()),
#         ui.nav_panel("Allocation", _allocation_panel_ui()),
#         ui.nav_panel("Goal Achievement", _goal_achievement_panel_ui()),
#         ui.nav_panel("Wealth Distribution", _wealth_distribution_panel_ui()),
#     ]

#     return ui.div(
#         selector,
#         ui.navset_tab(*tab_panels, id="ID_tab_goals_tabs_all"),
#     )


# def _overview_panel_ui() -> Any:
#     """KPI summary cards plus the raw goal table for the selected plan."""
#     return ui.div(
#         ui.layout_columns(
#             ui.value_box("Terminal Wealth (mean)", ui.output_text("output_ID_kpi_mean_wealth")),
#             ui.value_box("Terminal Wealth (median)", ui.output_text("output_ID_kpi_median_wealth")),
#             ui.value_box("Top-Priority Goal Success", ui.output_text("output_ID_kpi_top_goal_prob")),
#             ui.value_box("Solver Status", ui.output_text("output_ID_kpi_solver_status")),
#             col_widths=[3, 3, 3, 3],
#         ),
#         ui.card(
#             ui.card_header("Goals (priority order)"),
#             ui.output_table("output_ID_goal_table"),
#         ),
#     )


# def _allocation_panel_ui() -> Any:
#     """Average allocation over time and the plan's efficient frontier."""
#     return ui.div(
#         ui.card(ui.card_header("Average Allocation by Stage"), output_widget("output_ID_allocation_plot")),
#         ui.card(
#             ui.card_header("Efficient Frontier (context, not a live optimizer)"),
#             ui.p(
#                 "Requires per-stage expected returns/covariance to be stored "
#                 "alongside the result; see this tab's server code if this panel "
#                 "is blank.",
#                 class_="text-muted small",
#             ),
#             output_widget("output_ID_frontier_plot"),
#         ),
#     )


# def _goal_achievement_panel_ui() -> Any:
#     return ui.card(
#         ui.card_header("Goal Achievement Probability"),
#         output_widget("output_ID_goal_prob_plot"),
#     )


# def _wealth_distribution_panel_ui() -> Any:
#     return ui.div(
#         ui.card(ui.card_header("Terminal Wealth Distribution"), output_widget("output_ID_wealth_dist_plot")),
#         ui.card(ui.card_header("Scenario Tree"), output_widget("output_ID_scenario_tree_plot")),
#     )


# # =============================================================================
# # Server Logic
# # =============================================================================


# @module.server
# def tab_goals_server(  # pragma: no cover
#     input: typing.Any,
#     output: typing.Any,
#     session: typing.Any,
#     data_utils: dict,
#     data_inputs: dict,
#     reactives_shiny: dict,
# ) -> dict | None:
#     """Server logic for the Goal-Based Investing tab.

#     Every render function below is a pure read of the currently selected
#     ``MSGPResult`` -- there is no optimizer call anywhere in this function.
#     If a future version needs an interactive "edit and re-solve" mode, that
#     is a materially different (and heavier) server and should be a separate
#     tab or an explicit opt-in panel, not bolted onto this one.

#     Parameters
#     ----------
#     input, output, session : Any
#         Standard Shiny module server arguments.
#     data_utils : dict
#         Shared dashboard configuration (unused here).
#     data_inputs : dict
#         Must contain ``RESULTS_KEY``; see module docstring for the contract.
#     reactives_shiny : dict
#         Shared cross-tab reactive state (unused here; accepted for signature
#         consistency with other tabs).

#     Returns
#     -------
#     dict | None
#         Empty dict (no child sub-servers to expose), for signature
#         consistency with the dict-returning pattern used elsewhere.
#     """
#     results: dict[str, Any] = data_inputs.get(RESULTS_KEY, {})
#     benchmarks: dict[str, dict[str, Any]] = data_inputs.get(BENCHMARKS_KEY, {})

#     if not results:
#         _logger.warning("No goal-based investing results registered; tab_goals server has nothing to render.")
#         return {}

#     @reactive.calc
#     def selected_result():
#         label = input.input_ID_goals_plan_select()
#         if label not in results:
#             _logger.error("Selected plan '%s' not found in registered results.", label)
#             return None
#         return results[label]

#     @reactive.effect
#     def observer_mirror_selected_result_to_reactives_shiny() -> None:
#         """Mirror the selected plan into shared reactive state for the report pipeline.

#         The client-report exporters (report_plot_export /
#         _report_plot_personalized_goal_based_investing.py) read this exact key --
#         reactives_shiny["Inner_Variables_Shiny"]["personalized_goal_based_investing_Selected_Result"]
#         -- via the same _get_inner_variables()/_safe_reactive_get() pattern
#         used for every other tab's report data. Without this, "Generate PDF
#         Report" would have no way to find which plan is currently selected.
#         """
#         if not reactives_shiny or not isinstance(reactives_shiny, dict):
#             return
#         inner = reactives_shiny.get("Inner_Variables_Shiny")
#         if inner is None or not isinstance(inner, dict):
#             return

#         from src.dashboard.reporting._report_plot_goal_based_investing import (
#             personalized_goal_based_investing_RESULT_KEY,
#         )

#         current = selected_result()
#         existing_rv = inner.get(personalized_goal_based_investing_RESULT_KEY)
#         if existing_rv is not None and hasattr(existing_rv, "set"):
#             existing_rv.set(current)
#         else:
#             inner[personalized_goal_based_investing_RESULT_KEY] = reactive.Value(current)

#     # --- Overview KPIs ---

#     @render.text
#     def output_ID_kpi_mean_wealth():
#         result = selected_result()
#         if result is None:
#             return "n/a"
#         from src.models.personalized_goal_based_investing.performance import terminal_wealth_stats

#         wealth, probs = result.terminal_wealth_distribution()
#         stats = terminal_wealth_stats(wealth, probs)
#         return f"${stats.mean:,.0f}"

#     @render.text
#     def output_ID_kpi_median_wealth():
#         result = selected_result()
#         if result is None:
#             return "n/a"
#         from src.models.personalized_goal_based_investing.performance import terminal_wealth_stats

#         wealth, probs = result.terminal_wealth_distribution()
#         stats = terminal_wealth_stats(wealth, probs)
#         return f"${stats.median:,.0f}"

#     @render.text
#     def output_ID_kpi_top_goal_prob():
#         result = selected_result()
#         if result is None:
#             return "n/a"
#         from src.models.personalized_goal_based_investing.performance import goal_success_probability

#         top_priority = min(result.goal_set.priority_levels)
#         top_goal = result.goal_set.goals_at_level(top_priority)[0]
#         try:
#             prob = goal_success_probability(result, top_goal)
#         except ValueError:
#             return "n/a"
#         return f"{prob:.0%}"

#     @render.text
#     def output_ID_kpi_solver_status():
#         result = selected_result()
#         if result is None:
#             return "n/a"
#         return result.final.solver_status

#     @render.table
#     def output_ID_goal_table():
#         result = selected_result()
#         if result is None:
#             return None
#         import pandas as pd

#         rows = []
#         for p in result.goal_set.priority_levels:
#             for g in result.goal_set.goals_at_level(p):
#                 rows.append(
#                     {
#                         "Priority": g.priority,
#                         "Goal": g.name,
#                         "Stage": g.horizon_stage,
#                         "Target": f"${g.target_wealth:,.0f}",
#                     }
#                 )
#         return pd.DataFrame(rows)

#     # --- Allocation panel ---

#     @render_widget
#     def output_ID_allocation_plot():
#         result = selected_result()
#         if result is None:
#             return None
#         from src.models.personalized_goal_based_investing.visualization import plot_allocation_over_time

#         return plot_allocation_over_time(result)

#     @render_widget
#     def output_ID_frontier_plot():
#         result = selected_result()
#         if result is None:
#             return None
#         mu = getattr(result, "stage0_expected_returns", None)
#         cov = getattr(result, "stage0_covariance", None)
#         if mu is None or cov is None:
#             return None  # graceful: frontier needs mu/cov, not always attached to a result
#         from src.models.personalized_goal_based_investing.visualization import plot_efficient_frontier

#         stage0_x = result.final.x[result.tree.root_id]
#         return plot_efficient_frontier(
#             mu, cov, result.tree.asset_names, highlight_weights=stage0_x / stage0_x.sum()
#         )

#     # --- Goal achievement panel ---

#     @render_widget
#     def output_ID_goal_prob_plot():
#         result = selected_result()
#         if result is None:
#             return None
#         from src.models.personalized_goal_based_investing.visualization import plot_goal_probabilities

#         return plot_goal_probabilities(result, result.goal_set)

#     # --- Wealth distribution panel ---

#     @render_widget
#     def output_ID_wealth_dist_plot():
#         result = selected_result()
#         if result is None:
#             return None
#         from src.models.personalized_goal_based_investing.visualization import plot_terminal_wealth_distribution

#         return plot_terminal_wealth_distribution(result)

#     @render_widget
#     def output_ID_scenario_tree_plot():
#         result = selected_result()
#         if result is None:
#             return None
#         from src.models.personalized_goal_based_investing.visualization import plot_scenario_tree

#         return plot_scenario_tree(result.tree)

#     return {}

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

#: Solver statuses that mean the plan is fully usable, mapped to plain-language status.
_FRIENDLY_SOLVER_STATUS = {
    "optimal": "On track",
    "optimal_inaccurate": "On track",
}


def _friendly_solver_status(raw_status: str) -> str:
    """Translate a cvxpy/solver status string into a plain-language plan status.

    Anything not recognized as a clean "optimal" solve is surfaced as
    "Needs review" rather than an unexplained solver code, since a normal
    investor has no way to act on e.g. "infeasible" or "unbounded".
    """
    return _FRIENDLY_SOLVER_STATUS.get(str(raw_status).strip().lower(), "Needs review")


def _format_wealth_short(amount: float) -> str:
    """Format a dollar amount as a compact string, e.g. 2988252 -> '$2.99M'."""
    sign = "-" if amount < 0 else ""
    amount = abs(amount)
    if amount >= 1_000_000_000:
        return f"{sign}${amount / 1_000_000_000:.2f}B"
    if amount >= 1_000_000:
        return f"{sign}${amount / 1_000_000:.2f}M"
    if amount >= 1_000:
        return f"{sign}${amount / 1_000:.0f}K"
    return f"{sign}${amount:,.0f}"


# =============================================================================
# UI Components
# =============================================================================


@module.ui
def tab_goals_ui(*, data_utils: dict, data_inputs: dict) -> Any:  # pragma: no cover
    """Create the UI for the Goal-Based Investing tab.

    Builds a client/plan selector plus five read-only result panels, ordered
    outcome-first rather than mechanics-first: My Plan (the money story),
    My Goals, My Investment, What Could Happen, and Details (advanced /
    technical material). All panel content is rendered server-side from
    whichever precomputed ``MSGPResult`` the user selects -- no inputs here
    trigger a solve.

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

    # Outcome first, mechanics second: the person should see what their plan
    # is expected to produce before they see how the optimizer produced it.
    tab_panels = [
        ui.nav_panel("My Plan", _my_plan_panel_ui()),
        ui.nav_panel("My Goals", _my_goals_panel_ui()),
        ui.nav_panel("My Investment", _my_investment_panel_ui()),
        ui.nav_panel("What Could Happen", _what_could_happen_panel_ui()),
        ui.nav_panel("Details", _details_panel_ui()),
    ]

    return ui.div(
        selector,
        ui.navset_tab(*tab_panels, id="ID_tab_goals_tabs_all"),
    )


def _how_calculated_details(text: str) -> Any:
    """A collapsed '<details>' block that hides technical explanation by default."""
    return ui.tags.details(
        ui.tags.summary("How is this calculated?", style="cursor:pointer; color:#6c757d;", class_="small"),
        ui.p(text, class_="text-muted small mt-2 mb-0"),
        class_="mt-2",
    )


def _kpi_card(
    *, title: str, output_id: str, tooltip_text: str, subtitle_output_id: str | None = None
) -> Any:
    """A KPI value box whose title carries a hover tooltip explaining the technical term."""
    header = ui.tooltip(
        ui.span(
            title,
            " ",
            ui.tags.i(class_="bi bi-info-circle text-muted"),
            style="cursor:help;",
        ),
        tooltip_text,
    )
    extra = (ui.p(ui.output_text(subtitle_output_id), class_="text-muted small mb-0"),) if subtitle_output_id else ()
    return ui.value_box(header, ui.output_text(output_id), *extra)


def _my_plan_panel_ui() -> Any:
    """The 'money story': the plan's expected outcome, told in plain language first."""
    return ui.div(
        ui.card(
            ui.div(
                ui.p("Estimated wealth at the end of your plan", class_="text-muted mb-1"),
                ui.h2(ui.output_text("output_ID_kpi_headline_wealth"), class_="display-5 fw-bold mb-1"),
                ui.p("Based on thousands of possible market scenarios.", class_="text-muted mb-0"),
                _how_calculated_details(
                    "We run your plan through thousands of simulated market scenarios and "
                    "average the projected wealth across all of them. Analysts call this the "
                    "mean terminal wealth."
                ),
                class_="text-center py-4",
            ),
        ),
        ui.layout_columns(
            _kpi_card(
                title="Expected wealth",
                output_id="output_ID_kpi_mean_wealth",
                tooltip_text=(
                    "The average amount of money you could have at the end of your plan, "
                    "across all simulated market scenarios. Also called terminal wealth (mean)."
                ),
            ),
            _kpi_card(
                title="Typical outcome",
                output_id="output_ID_kpi_median_wealth",
                tooltip_text=(
                    "The middle result across every simulated scenario -- half of outcomes "
                    "were higher, half were lower. Also called terminal wealth (median)."
                ),
            ),
            _kpi_card(
                title="Top goal probability",
                output_id="output_ID_kpi_top_goal_prob",
                tooltip_text="The chance your highest-priority goal is fully funded, based on the simulated scenarios.",
                subtitle_output_id="output_ID_kpi_top_goal_name",
            ),
            _kpi_card(
                title="Plan status",
                output_id="output_ID_kpi_solver_status",
                tooltip_text="Whether your plan was successfully calculated and its recommendations are current.",
            ),
            col_widths=[3, 3, 3, 3],
        ),
        ui.card(
            ui.card_header("Your goals, in priority order"),
            ui.output_table("output_ID_goal_table"),
        ),
    )


def _my_goals_panel_ui() -> Any:
    """How likely each goal is to be met -- the 'why' behind the plan."""
    return ui.card(
        ui.card_header("Chance of reaching each goal"),
        ui.p(
            "For each goal, the odds it gets fully funded across the simulated scenarios.",
            class_="text-muted small",
        ),
        output_widget("output_ID_goal_prob_plot"),
    )


def _my_investment_panel_ui() -> Any:
    """How the money is invested to pursue those goals."""
    return ui.card(
        ui.card_header("How your investments shift over time"),
        ui.p(
            "The recommended mix of investments at each stage of your plan.",
            class_="text-muted small",
        ),
        output_widget("output_ID_allocation_plot"),
    )


def _what_could_happen_panel_ui() -> Any:
    """The range of outcomes the plan could produce -- uncertainty made visible."""
    return ui.card(
        ui.card_header("Range of possible outcomes"),
        ui.p(
            "Each simulated scenario produces a different result. This shows the full "
            "spread of projected wealth at the end of your plan, not just the average.",
            class_="text-muted small",
        ),
        output_widget("output_ID_wealth_dist_plot"),
    )


def _details_panel_ui() -> Any:
    """Technical / advanced material: efficient frontier and the underlying scenario tree."""
    return ui.div(
        ui.card(
            ui.card_header("Efficient frontier (context, not a live optimizer)"),
            ui.p(
                "Requires per-stage expected returns/covariance to be stored "
                "alongside the result; see this tab's server code if this panel "
                "is blank.",
                class_="text-muted small",
            ),
            output_widget("output_ID_frontier_plot"),
        ),
        ui.card(
            ui.card_header("Scenario tree"),
            ui.p(
                "The underlying set of simulated market paths your plan was optimized against.",
                class_="text-muted small",
            ),
            output_widget("output_ID_scenario_tree_plot"),
        ),
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

    # --- My Plan KPIs ---

    @render.text
    def output_ID_kpi_headline_wealth():
        """Big headline number on the 'My Plan' tab: expected wealth, compactly formatted."""
        result = selected_result()
        if result is None:
            return "n/a"
        from src.models.personalized_goal_based_investing.performance import terminal_wealth_stats

        wealth, probs = result.terminal_wealth_distribution()
        stats = terminal_wealth_stats(wealth, probs)
        return _format_wealth_short(stats.mean)

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
    def output_ID_kpi_top_goal_name():
        """Subtitle under 'Top goal probability' naming which goal it refers to."""
        result = selected_result()
        if result is None:
            return ""
        top_priority = min(result.goal_set.priority_levels)
        top_goal = result.goal_set.goals_at_level(top_priority)[0]
        return top_goal.name

    @render.text
    def output_ID_kpi_solver_status():
        result = selected_result()
        if result is None:
            return "n/a"
        return _friendly_solver_status(result.final.solver_status)

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
        df = pd.DataFrame(rows, columns=["Priority", "Goal", "Stage", "Target"])
        # Hide the default RangeIndex -- otherwise it renders as an extra
        # unlabeled leading column and shifts every header one column out
        # of alignment with its data (Target ends up looking empty).
        return df.style.hide(axis="index")

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

        frontier = getattr(result, "efficient_frontier_context", None)
        if frontier is None:
            return None

        from src.models.personalized_goal_based_investing.visualization import (
            plot_efficient_frontier,
        )

        stage0_x = result.final.x[result.tree.root_id]

        return plot_efficient_frontier(
            frontier.expected_returns,
            frontier.covariance,
            frontier.assets,
            highlight_weights=stage0_x / stage0_x.sum(),
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
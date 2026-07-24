"""Goal Parity subtab: Strategic Optimization (Step 5, Roadmap Sec 3.5).

Solves Goal Parity Balanced (θ = 25% each) or a Goal Tilted variant for the
profile and universe chosen in the other subtabs. The server returns a
reactive OptimizationResult for the rebalancing subtab.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
from shiny import module, reactive, render, ui
from shinywidgets import output_widget, render_widget

from src.dashboard.shiny_tab_goal_parity._tab_goal_parity_pipeline import (
    run_strategic,
    scarce_goals,
)
from src.models.goal_parity.utils_goal_parity import GOALS, THETA_BALANCED
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name=__name__)


@module.ui
def subtab_goal_parity_optimization_ui(
    *, data_utils: dict[str, Any], data_inputs: dict[str, Any]
) -> Any:  # pragma: no cover
    del data_utils, data_inputs
    return ui.div(
        ui.h3("Strategic Optimization (Step 5)"),
        ui.markdown(
            "max_w a·w − (1/2c)·Σ(P_k(w)−θ_k)² − (1/2κ)·w·w subject to Σw=1 "
            "(SLSQP). *Balanced* targets all four goal powers at 25% each. "
            "*Tilted* solves the identical objective with the target vector "
            "upweighted toward the tilted goal, per Golts & Jones (2023) p.12 "
            "— not a separately constrained maximization. *Tilt strength* "
            "interpolates the target between Balanced (0%, all goals at 25%) "
            "and a maximal tilt (100%, the tilted goal at 100% and the rest "
            "at 0%). "
            "Assets with a structurally negative expected return have their "
            "own weight bound capped, so goal classification alone cannot "
            "justify a large allocation to a money-losing position."
        ),
        ui.layout_sidebar(
            ui.sidebar(
                ui.input_radio_buttons(
                    "input_mode",
                    "Mode",
                    choices={"balanced": "Goal Parity Balanced", "tilted": "Goal Tilted"},
                    selected="balanced",
                ),
                ui.panel_conditional(
                    "input.input_mode === 'tilted'",
                    ui.input_select(
                        "input_tilt_goal", "Tilted goal", choices=list(GOALS), selected="Growth"
                    ),
                    ui.input_slider(
                        "input_tilt_strength",
                        "Tilt strength",
                        min=0, max=100, value=100, step=5, post="%",
                    ),
                ),
                width=300,
            ),
            ui.output_text("output_optimization_summary"),
            ui.output_ui("output_scarcity_warning"),
            output_widget("output_goal_power_plot"),
            output_widget("output_weights_plot"),
        ),
    )


@module.server
def subtab_goal_parity_optimization_server(  # pragma: no cover
    input: Any,
    output: Any,
    session: Any,
    *,
    data_utils: dict,
    data_inputs: dict,
    reactives_shiny: dict,
    pipeline,
):
    del output, session, data_utils, data_inputs, reactives_shiny

    @reactive.calc
    def strategic():
        return run_strategic(
            pipeline(),
            mode=input.input_mode(),
            tilt_goal=input.input_tilt_goal(),
            tilt_strength=input.input_tilt_strength() / 100.0,
        )

    @render.text
    def output_optimization_summary() -> str:
        result = strategic()
        status = "converged" if result.success else "did not fully converge"
        return (
            f"Mode: {result.mode} — solver {status}. "
            f"Expected portfolio return a·w = {result.expected_return:+.2%} per year."
        )

    @render.ui
    def output_scarcity_warning():
        scarce = scarce_goals(pipeline())
        if not scarce:
            return None
        goals_text = " and ".join(scarce) if len(scarce) <= 2 else ", ".join(scarce)
        verb = "has" if len(scarce) == 1 else "have"
        noun = "this goal" if len(scarce) == 1 else "these goals"
        return ui.div(
            ui.markdown(
                f"**Note:** {goals_text} {verb} limited support in the current "
                "investment universe — no single asset (and so no achievable "
                f"portfolio) scores highly on {noun}, regardless of tilt. A "
                "low power here reflects a data limitation, not an optimizer "
                "failure."
            ),
            class_="alert alert-warning",
        )

    @render_widget
    def output_goal_power_plot():
        result = strategic()
        frame = pd.DataFrame(
            {
                "Goal": [*GOALS, *GOALS],
                "Power": [*(result.goal_powers[g] for g in GOALS), *(THETA_BALANCED[g] for g in GOALS)],
                "Series": ["Achieved"] * 4 + ["Balanced target (25%)"] * 4,
            }
        )
        figure = px.bar(
            frame, x="Goal", y="Power", color="Series", barmode="group",
            title="Portfolio goal powers vs. targets",
        )
        figure.update_layout(height=380, yaxis_tickformat=".0%")
        return figure

    @render_widget
    def output_weights_plot():
        result = strategic()
        frame = (
            pd.DataFrame({"Ticker": result.tickers, "Weight": result.weights})
            .query("Weight > 0.005")
            .sort_values("Weight", ascending=True)
        )
        figure = px.bar(
            frame, x="Weight", y="Ticker", orientation="h",
            title="Strategic weights w (positions > 0.5%)",
        )
        figure.update_layout(height=420, xaxis_tickformat=".0%")
        return figure

    return strategic

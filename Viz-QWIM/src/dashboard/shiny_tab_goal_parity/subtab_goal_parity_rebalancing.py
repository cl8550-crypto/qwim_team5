"""Goal Parity subtab: Tactical Rebalancing (Step 6, Roadmap Sec 3.6, 4.2).

Signal-priority (impact-ranked, greedy) rebalancing per Arnott, Li &
Linnainmaa (2024): drift the strategic weights with a seeded shock, then
re-align toward the strategic portfolio's achieved goal powers, executing
only trades whose goal-gap reduction clears the cost-benefit threshold.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
from shiny import module, reactive, render, ui
from shinywidgets import output_widget, render_widget

from src.dashboard.shiny_tab_goal_parity._tab_goal_parity_pipeline import run_rebalance_demo
from src.models.goal_parity.utils_goal_parity import GOALS
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name=__name__)


@module.ui
def subtab_goal_parity_rebalancing_ui(
    *, data_utils: dict[str, Any], data_inputs: dict[str, Any]
) -> Any:  # pragma: no cover
    del data_utils, data_inputs
    return ui.div(
        ui.h3("Tactical Rebalancing (Step 6 — Signal Priority)"),
        ui.markdown(
            "Candidate (sell, buy) trades are ranked by goal-gap reduction per "
            "unit transaction cost and executed greedily while the score clears "
            "the threshold η, subject to the cash floor and turnover budget."
        ),
        ui.layout_sidebar(
            ui.sidebar(
                ui.input_slider(
                    "input_drift_scale", "Simulated market drift (σ of weight shock)",
                    min=0.0, max=0.6, value=0.25, step=0.05,
                ),
                ui.input_numeric("input_drift_seed", "Drift scenario seed", value=5, min=0),
                width=320,
            ),
            ui.output_text("output_rebalance_summary"),
            output_widget("output_rebalance_powers_plot"),
            ui.output_table("output_trades_table"),
        ),
    )


@module.server
def subtab_goal_parity_rebalancing_server(  # pragma: no cover
    input: Any,
    output: Any,
    session: Any,
    *,
    data_utils: dict,
    data_inputs: dict,
    reactives_shiny: dict,
    pipeline,
    strategic,
):
    del output, session, data_utils, data_inputs, reactives_shiny

    @reactive.calc
    def rebalance():
        return run_rebalance_demo(
            pipeline(),
            strategic(),
            drift_scale=float(input.input_drift_scale() or 0.25),
            seed=int(input.input_drift_seed() or 5),
        )

    @render.text
    def output_rebalance_summary() -> str:
        result = rebalance()
        if not result.traded:
            return (
                "No trades executed: goal-power drift is within the ε threshold "
                "(and the cash floor holds), so trading is not worth its cost."
            )
        return (
            f"Executed {len(result.trades)} trades, one-way turnover "
            f"{result.turnover:.1%}, re-aligning goal powers toward the "
            "strategic portfolio."
        )

    @render_widget
    def output_rebalance_powers_plot():
        result = rebalance()
        target = strategic().goal_powers
        frame = pd.DataFrame(
            {
                "Goal": [*GOALS, *GOALS, *GOALS],
                "Power": [
                    *(result.goal_powers_before[g] for g in GOALS),
                    *(result.goal_powers_after[g] for g in GOALS),
                    *(target[g] for g in GOALS),
                ],
                "Series": ["Drifted"] * 4 + ["After rebalance"] * 4 + ["Strategic target"] * 4,
            }
        )
        figure = px.bar(
            frame, x="Goal", y="Power", color="Series", barmode="group",
            title="Goal powers: drifted → rebalanced → strategic target",
        )
        figure.update_layout(height=380, yaxis_tickformat=".0%")
        return figure

    @render.table
    def output_trades_table() -> pd.DataFrame:
        result = rebalance()
        if not result.trades:
            return pd.DataFrame({"Trades": ["(none executed)"]})
        return pd.DataFrame(
            {
                "#": range(1, len(result.trades) + 1),
                "Sell": [t.sell for t in result.trades],
                "Buy": [t.buy for t in result.trades],
                "Size": [f"{t.size:.1%}" for t in result.trades],
                "Impact score": [f"{t.score:,.0f}" for t in result.trades],
            }
        )

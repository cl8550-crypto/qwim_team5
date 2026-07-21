"""Goal Parity subtab: 4x4 Asset-Goal Map (Steps 2-4, Roadmap Sec 3.2-3.4, 3.7).

Lets the user select the asset universe (checkboxes, per the advisor's
guidance that universe selection happens at dashboard level) and shows each
asset's option triggers, goal shares, and position on the 2D asset map.
The server returns a reactive list of selected tickers for downstream subtabs.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
from shiny import module, reactive, render, ui
from shinywidgets import output_widget, render_widget

from src.dashboard.shiny_tab_goal_parity._tab_goal_parity_pipeline import (
    available_assets,
    calibrated_volatility_adjuster,
    decompose_universe,
)
from src.models.goal_parity.utils_goal_parity import GOALS
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name=__name__)


@module.ui
def subtab_goal_parity_asset_map_ui(
    *, data_utils: dict[str, Any], data_inputs: dict[str, Any]
) -> Any:  # pragma: no cover
    del data_utils, data_inputs
    assets = available_assets()
    return ui.div(
        ui.h3("4×4 Asset-Goal Map (Steps 2–4)"),
        ui.markdown(
            "Each asset's EPV is split into the four goals by two option "
            "triggers: π_default (first-passage of the investor's loss barrier "
            "b under σ_D) and π_liquidity (first-passage of the compounding "
            "liquidity strike k₁^T under σ_L). Growth = both trigger; "
            "Liquidity = neither."
        ),
        ui.output_text("output_calibration_note"),
        ui.layout_sidebar(
            ui.sidebar(
                ui.input_checkbox_group(
                    "input_asset_selection",
                    "Asset universe",
                    choices=assets,
                    selected=list(assets),
                ),
                width=380,
            ),
            output_widget("output_asset_map_plot"),
            ui.output_table("output_decomposition_table"),
        ),
    )


@module.server
def subtab_goal_parity_asset_map_server(  # pragma: no cover
    input: Any,
    output: Any,
    session: Any,
    *,
    data_utils: dict,
    data_inputs: dict,
    reactives_shiny: dict,
    profile,
):
    del output, session, data_utils, data_inputs, reactives_shiny

    @reactive.calc
    def selected_tickers() -> list[str]:
        selection = list(input.input_asset_selection() or [])
        return selection or list(available_assets())

    @reactive.calc
    def pipeline():
        return decompose_universe(profile(), selected_tickers())

    @render.text
    def output_calibration_note() -> str:
        gamma0 = calibrated_volatility_adjuster().gamma0
        return (
            f"Skew-sensitivity constant gamma0 = {gamma0:.2f}, calibrated from this "
            "universe's own daily-return history (Appendix A), vs. the paper's own "
            "monthly-data default of 1.6."
        )

    @render_widget
    def output_asset_map_plot():
        frame = pd.DataFrame(pipeline().rows)
        figure = px.scatter(
            frame,
            x="map_x",
            y="map_y",
            text="Ticker",
            color="Class",
            hover_data={goal: ":.2f" for goal in GOALS},
            labels={
                "map_x": "Liquitility (pi_liquidity)",
                "map_y": "Defaultility (pi_default)",
            },
            title="Asset map — corners: Liquidity (0,0), Income (1,0), Preservation (0,1), Growth (1,1)",
            range_x=[-0.05, 1.05],
            range_y=[-0.05, 1.05],
        )
        figure.update_traces(textposition="top center")
        figure.update_layout(height=520)
        return figure

    @render.table
    def output_decomposition_table() -> pd.DataFrame:
        frame = pd.DataFrame(pipeline().rows)
        display = frame[
            ["Ticker", "Class", "a", "sigma", "gamma", "pi_default", "pi_liquidity", *GOALS]
        ].copy()
        for column in display.columns[2:]:
            display[column] = display[column].map(lambda v: f"{v:.3f}")
        return display

    return selected_tickers

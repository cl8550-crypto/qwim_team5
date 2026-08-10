"""Goal Parity Tab Module.

Integrates the Goal Parity model (Cron & Golts 2022; Golts & Jones 2023) as
its own dashboard tab with a static landing page plus one subtab per
pipeline stage:

0. Overview & Guide — why Goal Parity vs. a conventional benchmark, and a
   step-by-step usage guide (static, no server)
1. Investor Profile — Step 1 (reads the Clients tab's tolerance_risk and
   age_current/age_retirement fields; manual override available)
2. 4x4 Asset Map — Steps 2-4 (EPV, skew-adjusted vols, option-based split)
3. Strategic Optimization — Step 5 (Goal Parity Balanced / Tilted)
4. Tactical Rebalancing — Step 6 (signal-priority trades)
5. Historical Backtest — walk-forward train/test/step evaluation with all
   model inputs re-estimated per fold from training data only

The subtab servers are chained through returned reactives: profile ->
(selected tickers, Steps 2-4 pipeline) -> strategic result -> rebalancing.
The pipeline is computed once in the Asset Map subtab and shared downstream,
rather than recomputed independently in each subtab.
"""

from __future__ import annotations

import typing
from typing import Any

from shiny import module, ui

from src.dashboard.shiny_tab_goal_parity.subtab_goal_parity_guide import (
    subtab_goal_parity_guide_server,
    subtab_goal_parity_guide_ui,
)
from src.dashboard.shiny_tab_goal_parity.subtab_goal_parity_backtest import (
    subtab_goal_parity_backtest_server,
    subtab_goal_parity_backtest_ui,
)
from src.dashboard.shiny_tab_goal_parity.subtab_goal_parity_asset_map import (
    subtab_goal_parity_asset_map_server,
    subtab_goal_parity_asset_map_ui,
)
from src.dashboard.shiny_tab_goal_parity.subtab_goal_parity_optimization import (
    subtab_goal_parity_optimization_server,
    subtab_goal_parity_optimization_ui,
)
from src.dashboard.shiny_tab_goal_parity.subtab_goal_parity_profile import (
    subtab_goal_parity_profile_server,
    subtab_goal_parity_profile_ui,
)
from src.dashboard.shiny_tab_goal_parity.subtab_goal_parity_rebalancing import (
    subtab_goal_parity_rebalancing_server,
    subtab_goal_parity_rebalancing_ui,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name=__name__)


@module.ui
def tab_goal_parity_ui(*, data_utils: dict, data_inputs: dict) -> Any:  # pragma: no cover
    """Navigation tab set with one subtab per Goal Parity pipeline stage."""
    tab_panels = [
        ui.nav_panel(
            "Overview & Guide",
            subtab_goal_parity_guide_ui(  # type: ignore[call-arg]
                id="ID_tab_goal_parity_subtab_guide",  # pyright: ignore[reportCallIssue]
                data_utils=data_utils,
                data_inputs=data_inputs,
            ),
        ),
        ui.nav_panel(
            "Investor Profile",
            subtab_goal_parity_profile_ui(  # type: ignore[call-arg]
                id="ID_tab_goal_parity_subtab_profile",  # pyright: ignore[reportCallIssue]
                data_utils=data_utils,
                data_inputs=data_inputs,
            ),
        ),
        ui.nav_panel(
            "4×4 Asset Map",
            subtab_goal_parity_asset_map_ui(  # type: ignore[call-arg]
                id="ID_tab_goal_parity_subtab_asset_map",  # pyright: ignore[reportCallIssue]
                data_utils=data_utils,
                data_inputs=data_inputs,
            ),
        ),
        ui.nav_panel(
            "Strategic Optimization",
            subtab_goal_parity_optimization_ui(  # type: ignore[call-arg]
                id="ID_tab_goal_parity_subtab_optimization",  # pyright: ignore[reportCallIssue]
                data_utils=data_utils,
                data_inputs=data_inputs,
            ),
        ),
        ui.nav_panel(
            "Tactical Rebalancing",
            subtab_goal_parity_rebalancing_ui(  # type: ignore[call-arg]
                id="ID_tab_goal_parity_subtab_rebalancing",  # pyright: ignore[reportCallIssue]
                data_utils=data_utils,
                data_inputs=data_inputs,
            ),
        ),
        ui.nav_panel(
            "Historical Backtest",
            subtab_goal_parity_backtest_ui(  # type: ignore[call-arg]
                id="ID_tab_goal_parity_subtab_backtest",  # pyright: ignore[reportCallIssue]
                data_utils=data_utils,
                data_inputs=data_inputs,
            ),
        ),
    ]
    return ui.navset_tab(*tab_panels, id="ID_tab_goal_parity_tabs_all")


@module.server
def tab_goal_parity_server(  # pragma: no cover
    input: typing.Any,
    output: typing.Any,
    session: typing.Any,
    data_utils: dict,
    data_inputs: dict,
    reactives_shiny: dict,
) -> dict | None:
    """Coordinates the subtab servers, chaining their reactives."""
    subtab_goal_parity_guide_server(  # type: ignore[call-arg]
        id="ID_tab_goal_parity_subtab_guide",  # pyright: ignore[reportCallIssue]
        data_utils=data_utils,
        data_inputs=data_inputs,
        reactives_shiny=reactives_shiny,
    )
    profile = subtab_goal_parity_profile_server(  # type: ignore[call-arg]
        id="ID_tab_goal_parity_subtab_profile",  # pyright: ignore[reportCallIssue]
        data_utils=data_utils,
        data_inputs=data_inputs,
        reactives_shiny=reactives_shiny,
    )
    selected_tickers, pipeline = subtab_goal_parity_asset_map_server(  # type: ignore[call-arg]
        id="ID_tab_goal_parity_subtab_asset_map",  # pyright: ignore[reportCallIssue]
        data_utils=data_utils,
        data_inputs=data_inputs,
        reactives_shiny=reactives_shiny,
        profile=profile,
    )
    strategic = subtab_goal_parity_optimization_server(  # type: ignore[call-arg]
        id="ID_tab_goal_parity_subtab_optimization",  # pyright: ignore[reportCallIssue]
        data_utils=data_utils,
        data_inputs=data_inputs,
        reactives_shiny=reactives_shiny,
        pipeline=pipeline,
    )
    subtab_goal_parity_rebalancing_server(  # type: ignore[call-arg]
        id="ID_tab_goal_parity_subtab_rebalancing",  # pyright: ignore[reportCallIssue]
        data_utils=data_utils,
        data_inputs=data_inputs,
        reactives_shiny=reactives_shiny,
        pipeline=pipeline,
        strategic=strategic,
    )
    subtab_goal_parity_backtest_server(  # type: ignore[call-arg]
        id="ID_tab_goal_parity_subtab_backtest",  # pyright: ignore[reportCallIssue]
        data_utils=data_utils,
        data_inputs=data_inputs,
        reactives_shiny=reactives_shiny,
        profile=profile,
        selected_tickers=selected_tickers,
    )
    return {
        "Profile_Server": profile,
        "Selected_Tickers": selected_tickers,
        "Pipeline_Server": pipeline,
        "Strategic_Server": strategic,
    }

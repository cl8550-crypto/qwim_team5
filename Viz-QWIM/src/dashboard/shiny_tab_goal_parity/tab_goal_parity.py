"""Goal Parity Tab Module.

Integrates the Goal Parity model (Cron & Golts 2022; Golts & Jones 2023) as
its own dashboard tab with one subtab per pipeline stage:

1. Investor Profile — Step 1 (reads the Clients tab's tolerance_risk and
   age_current/age_retirement fields; manual override available)
2. 4x4 Asset Map — Steps 2-4 (EPV, skew-adjusted vols, option-based split)
3. Strategic Optimization — Step 5 (Goal Parity Balanced / Tilted)
4. Tactical Rebalancing — Step 6 (signal-priority trades)

The subtab servers are chained through returned reactives: profile ->
selected tickers -> strategic result -> rebalancing.
"""

from __future__ import annotations

import typing
from typing import Any

from shiny import module, ui

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
    """Coordinates the four subtab servers, chaining their reactives."""
    profile = subtab_goal_parity_profile_server(  # type: ignore[call-arg]
        id="ID_tab_goal_parity_subtab_profile",  # pyright: ignore[reportCallIssue]
        data_utils=data_utils,
        data_inputs=data_inputs,
        reactives_shiny=reactives_shiny,
    )
    selected_tickers = subtab_goal_parity_asset_map_server(  # type: ignore[call-arg]
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
        profile=profile,
        selected_tickers=selected_tickers,
    )
    subtab_goal_parity_rebalancing_server(  # type: ignore[call-arg]
        id="ID_tab_goal_parity_subtab_rebalancing",  # pyright: ignore[reportCallIssue]
        data_utils=data_utils,
        data_inputs=data_inputs,
        reactives_shiny=reactives_shiny,
        profile=profile,
        selected_tickers=selected_tickers,
        strategic=strategic,
    )
    return {
        "Profile_Server": profile,
        "Selected_Tickers": selected_tickers,
        "Strategic_Server": strategic,
    }

"""Covariance dashboard tab."""

from __future__ import annotations

import typing

from typing import Any

from shiny import module, ui

from .subtab_covariance_analysis import (
    subtab_covariance_analysis_server,
    subtab_covariance_analysis_ui,
)


@module.ui
def tab_covariance_ui(
    *,
    data_utils: dict[str, Any],
    data_inputs: dict[str, Any],
) -> Any:
    """Create the covariance model tab."""

    return ui.navset_tab(
        ui.nav_panel(
            "Estimator Analysis",
            subtab_covariance_analysis_ui(
                id="ID_tab_covariance_subtab_analysis",
                data_utils=data_utils,
                data_inputs=data_inputs,
            ),
        ),
        id="ID_tab_covariance_tabs_all",
    )


@module.server
def tab_covariance_server(
    input: typing.Any,
    output: typing.Any,
    session: typing.Any,
    data_utils: dict[str, Any],
    data_inputs: dict[str, Any],
    reactives_shiny: dict[str, Any],
) -> dict[str, Any]:
    """Run covariance-tab server logic."""

    analysis_server = subtab_covariance_analysis_server(
        id="ID_tab_covariance_subtab_analysis",
        data_utils=data_utils,
        data_inputs=data_inputs,
        reactives_shiny=reactives_shiny,
    )

    return {"Covariance_Analysis_Server": analysis_server}


Tab_Covariance = tab_covariance_ui
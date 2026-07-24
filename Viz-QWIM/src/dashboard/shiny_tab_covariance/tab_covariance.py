"""Covariance dashboard tab.

The covariance workflow is divided into three client-facing subtabs:

1. Overview — executive recommendation and analysis summary.
2. Estimator Comparison — detailed rankings and performance metrics.
3. Diagnostics — rolling behavior and covariance-matrix reliability checks.

The covariance backtest is initiated in the Overview subtab and its reactive
results are shared with the Comparison and Diagnostics subtabs.
"""

from __future__ import annotations

import typing

from typing import Any

from shiny import module, ui

from .subtab_covariance_comparison import (
    subtab_covariance_comparison_server,
    subtab_covariance_comparison_ui,
)
from .subtab_covariance_diagnostics import (
    subtab_covariance_diagnostics_server,
    subtab_covariance_diagnostics_ui,
)
from .subtab_covariance_overview import (
    subtab_covariance_overview_server,
    subtab_covariance_overview_ui,
)


@module.ui
def tab_covariance_ui(
    *,
    data_utils: dict[str, Any],
    data_inputs: dict[str, Any],
) -> Any:
    """Create the three-subtab covariance workflow."""

    tab_panels = [
        ui.nav_panel(
            "Overview",
            subtab_covariance_overview_ui(
                id="ID_tab_covariance_subtab_overview",
                data_utils=data_utils,
                data_inputs=data_inputs,
            ),
        ),
        ui.nav_panel(
            "Estimator Comparison",
            subtab_covariance_comparison_ui(
                id="ID_tab_covariance_subtab_comparison",
                data_utils=data_utils,
                data_inputs=data_inputs,
            ),
        ),
        ui.nav_panel(
            "Diagnostics",
            subtab_covariance_diagnostics_ui(
                id="ID_tab_covariance_subtab_diagnostics",
                data_utils=data_utils,
                data_inputs=data_inputs,
            ),
        ),
    ]

    return ui.navset_tab(
        *tab_panels,
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
    """Coordinate the covariance subtabs and shared results."""

    overview = subtab_covariance_overview_server(
        id="ID_tab_covariance_subtab_overview",
        data_utils=data_utils,
        data_inputs=data_inputs,
        reactives_shiny=reactives_shiny,
    )

    comparison = subtab_covariance_comparison_server(
        id="ID_tab_covariance_subtab_comparison",
        data_utils=data_utils,
        data_inputs=data_inputs,
        reactives_shiny=reactives_shiny,
        overview=overview,
    )

    diagnostics = subtab_covariance_diagnostics_server(
        id="ID_tab_covariance_subtab_diagnostics",
        data_utils=data_utils,
        data_inputs=data_inputs,
        reactives_shiny=reactives_shiny,
        overview=overview,
    )

    return {
        "Overview_Server": overview,
        "Comparison_Server": comparison,
        "Diagnostics_Server": diagnostics,
    }


Tab_Covariance = tab_covariance_ui
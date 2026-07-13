"""Setup Tab Module.

Provides dashboard configuration and setup functionality, including computation
settings and advisor information management.

Tab Structure
-------------
- **Computation** — lets users select the computation engine (joblib, asyncio,
  standard, etc.) and developer / debug options (Logger Display, Execution
  Thread Mode, Profiler) for each computation-heavy subtab.
- **Advisor** — captures advisor name, credentials, title, team, firm, email,
  address, and phone number.  Auto-populates from the uploaded Inputs Worksheet
  PDF when triggered by the Clients › Outline subtab.
"""

from __future__ import annotations

import typing

from typing import Any

from shiny import module, ui

from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

from .subtab_advisor_info import subtab_advisor_info_server, subtab_advisor_info_ui
from .subtab_computation import subtab_computation_server, subtab_computation_ui


_logger = get_logger(name = __name__)


@module.ui
def tab_setup_ui(  # pragma: no cover
    *, data_utils: dict[str, Any], data_inputs: dict[str, Any]) -> Any:
    """Create the Setup tab user interface.

    Parameters
    ----------
    data_utils : dict
        Shared dashboard utility functions.
    data_inputs : dict
        Default input values and configuration.

    Returns
    -------
    ui.navset_tab
        Navigation tab set for the Setup tab.
    """
    tab_panels_setup = [
        ui.nav_panel(
            "Computation",
            subtab_computation_ui(  # type: ignore[call-arg]
                id="ID_tab_setup_subtab_computation",  # pyright: ignore[reportCallIssue]  # pyrefly: ignore[unexpected-keyword,bad-argument-count]
                data_utils=data_utils,
                data_inputs=data_inputs,
            ),
        ),
        ui.nav_panel(
            "Advisor",
            subtab_advisor_info_ui(  # type: ignore[call-arg]
                id="ID_tab_setup_subtab_advisor_info",  # pyright: ignore[reportCallIssue]  # pyrefly: ignore[unexpected-keyword,bad-argument-count]
                data_utils=data_utils,
                data_inputs=data_inputs,
            ),
        ),
    ]

    return ui.navset_tab(
        *tab_panels_setup,
        id="ID_tab_setup_tabs_all",
    )


@module.server
def tab_setup_server(  # pragma: no cover
    input: typing.Any,
    output: typing.Any,
    session: typing.Any,
    data_utils: dict[str, Any],
    data_inputs: dict[str, Any],
    reactives_shiny: dict[str, Any],
) -> dict | None:
    """Server logic for the Setup tab.

    Parameters
    ----------
    input, output, session
        Standard Shiny server objects.
    data_utils : dict
        Shared dashboard utility functions.
    data_inputs : dict
        Default input values and configuration.
    reactives_shiny : dict
        Shared reactive state dictionary.

    Returns
    -------
    dict
        Dictionary of initialised server instances.
    """
    _logger.info(
        "SERVER_INIT: Setup tab server",
        extra={"event_type": "server_init", "tab": "setup"},
    )

    setup_computation_server_instance = subtab_computation_server(  # type: ignore[call-arg]
        id="ID_tab_setup_subtab_computation",  # pyright: ignore[reportCallIssue]  # pyrefly: ignore[unexpected-keyword,bad-argument-count]
        data_utils=data_utils,
        data_inputs=data_inputs,
        reactives_shiny=reactives_shiny,
    )

    setup_advisor_info_server_instance = subtab_advisor_info_server(  # type: ignore[call-arg]
        id="ID_tab_setup_subtab_advisor_info",  # pyright: ignore[reportCallIssue]  # pyrefly: ignore[unexpected-keyword,bad-argument-count]
        data_utils=data_utils,
        data_inputs=data_inputs,
        reactives_shiny=reactives_shiny,
    )

    return {
        "setup_Computation_Server": setup_computation_server_instance,
        "setup_Advisor_Info_Server": setup_advisor_info_server_instance,
    }

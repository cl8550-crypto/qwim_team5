"""Goal Profile subtab for Goal-Based Investing."""

from __future__ import annotations

from typing import Any

from shiny import module, ui


@module.ui
def subtab_goal_based_investing_profile_ui(
    *,
    data_utils: dict[str, Any],
    data_inputs: dict[str, Any],
) -> Any:  # pragma: no cover
    """Create the placeholder for goal inputs.

    User input controls will be added here in the next implementation step.
    """
    del data_utils, data_inputs
    return ui.page_fluid(
        ui.h3("Goal Profile"),
        ui.p("Goal inputs will be configured here."),
    )


@module.server
def subtab_goal_based_investing_profile_server(
    input: Any,
    output: Any,
    session: Any,
    data_utils: dict[str, Any],
    data_inputs: dict[str, Any],
    reactives_shiny: dict[str, Any],
) -> None:  # pragma: no cover
    """Reserve server scope for goal-input validation and shared state."""
    del input, output, session, data_utils, data_inputs, reactives_shiny


Subtab_Goal_Based_Investing_Profile = subtab_goal_based_investing_profile_ui
